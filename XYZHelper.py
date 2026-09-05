import clr
import time
from datetime import datetime

from decimal import Decimal

from HardnessPIDController import HardnessPIDController 

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.Benchtop.StepperMotorCLI.dll")

from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import *
from System import Decimal


class KinesisXYZHelper:
    def __init__(self):
        self.pidController = HardnessPIDController()
        self.serial_no = "70400554" #found on the benchtop
        DeviceManagerCLI.BuildDeviceList()
        self.connected = False

    def connectAll(self):
        self.device = self.init_benchtopStepper(self.serial_no)
        self.connected = True

    def closeAll(self):
        for channel in [self.device_x, self.device_y, self.device_z]:
            channel.StopPolling()
        self.device.Disconnect()
        self.connected = False

    def init_benchtopStepper(self,serial_no):
        DeviceManagerCLI.BuildDeviceList()
        device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial_no)
        device.Connect(serial_no)
        time.sleep(.25)

        self.device_x = device.GetChannel(1)
        self.device_y = device.GetChannel(2)
        self.device_z = device.GetChannel(3)

        for channel in [self.device_x, self.device_y, self.device_z]:

            # Ensure that the device settings have been initialized.
            if not channel.IsSettingsInitialized():
                channel.WaitForSettingsInitialized(10000)  # 10 second timeout.
                assert channel.IsSettingsInitialized() is True

            # Start polling loop and enable device.
            channel.StartPolling(250)  # 250ms polling rate.
            time.sleep(0.25)
            channel.EnableDevice()
            time.sleep(0.25)  # Wait for device to enable.

            # Load any configuration settings needed by the controller/stage.
            motor_config = channel.LoadMotorConfiguration(channel.DeviceID)

        # Get Device Information and display description.
        device_info = device.GetDeviceInfo()
        print(device_info.Description)

        return device

    def voxelFTIR(self,xStart,yStart,zStart,xyPitch,zPitch,xStep,yStep,zStep):
        for x_ind in range(xStep):
            self.device_x.MoveTo(Decimal(xStart + x_ind * xyPitch), 60000)
            for y_ind in range(yStep):
                self.device_y.MoveTo(Decimal(yStart + y_ind * xyPitch), 60000)
                for z_ind in range(zStep):
                    self.device_z.MoveTo(Decimal(zStart+z_ind*zPitch), 60000)

    def planeScan(self,xStart,yStart,zStart,xyPitch,xStep,yStep):
        self.device_z.MoveTo(Decimal(zStart), 60000)
        for x_ind in range(xStep):
            self.device_x.MoveTo(Decimal(xStart + x_ind * xyPitch), 60000)
            for y_ind in range(yStep):
                self.device_y.MoveTo(Decimal(yStart + y_ind * xyPitch), 60000)
                # ots.ftirScan(x=x_ind,y=y_ind,z = 0)

        self.device_z.MoveTo(Decimal(12.95), 60000)
        self.device_y.MoveTo(Decimal(0), 60000)
        self.device_x.MoveTo(Decimal(0), 60000)

    def planeScanNoMeasure(self,xStart,yStart,zStart,xyPitch,xStep,yStep):
        self.device_z.MoveTo(Decimal(zStart), 60000)
        for x_ind in range(xStep):
            self.device_x.MoveTo(Decimal(xStart + x_ind * xyPitch), 60000)
            for y_ind in range(yStep):
                self.device_y.MoveTo(Decimal(yStart + y_ind * xyPitch), 60000)

        self.device_z.MoveTo(Decimal(12.95), 60000)
        self.device_y.MoveTo(Decimal(0), 60000)
        self.device_x.MoveTo(Decimal(0), 60000)

    def PID(self, target=100, Kp=0.01, Ki=0.0, Kd=0.0, tolerance=0.5,
            max_step=0.02, min_step=0.002, contact_threshold=2.0,
            z_min=None, z_max=None, max_iterations=2000, log_path=None):

        integral = 0
        previous_error = 0
        previous_time = time.time()
        load_history = []  # for smoothing

        self.pidController.open()
        log_file = open(log_path, "w") if log_path else None
        if log_file:
            log_file.write("time,load,error,output,position\n")

        try:
            for i in range(max_iterations):
                raw_load = self.pidController.get_weight()

                if raw_load is None:
                    print("No reading from load cell...")
                    time.sleep(0.1)
                    continue

                # simple smoothing to fight sensor noise (helps the D term a lot)
                load_history.append(raw_load)
                if len(load_history) > 5:
                    load_history.pop(0)
                load = sum(load_history) / len(load_history)

                error = target - load

                if abs(error) <= tolerance:
                    print(f"Target reached: {load:.3f}")
                    break

                current_time = time.time()
                dt = max(current_time - previous_time, 0.001)

                # anti-windup: only integrate if we're not saturated
                unclamped_output = Kp * error + Ki * integral + Kd * ((error - previous_error) / dt)
                if abs(unclamped_output) < max_step:
                    integral += error * dt

                derivative = (error - previous_error) / dt
                output = Kp * error + Ki * integral + Kd * derivative

                # shrink allowed step once we're near/in contact
                step_limit = max_step if load < contact_threshold else min_step
                output = max(min(output, step_limit), -step_limit)

                current_position = float(str(self.device_z.Position))
                new_position = current_position + output

                # safety bounds so the loop can't drive into a hard limit
                if z_min is not None:
                    new_position = max(new_position, z_min)
                if z_max is not None:
                    new_position = min(new_position, z_max)

                self.device_z.MoveTo(Decimal(new_position), 60000)

                print(f"Load: {load:.3f} | Target: {target:.3f} | Error: {error:.3f} | "
                    f"Step: {output:.5f} | Pos: {new_position:.4f}")

                if log_file:
                    log_file.write(f"{current_time},{load},{error},{output},{new_position}\n")

                previous_error = error
                previous_time = current_time

                time.sleep(0.1)  # matches your 250ms polling headroom better than 0.2
            else:
                print("PID timed out without reaching target")

        finally:
            self.pidController.close()
            if log_file:
                log_file.close()

    def moveMotor(self,motor,amount):

        if motor == "x":
            device = self.device_x

        elif motor == "y":
            device = self.device_y

        elif motor == "z":
            device = self.device_z

        else:
            print("Motor must be x, y, or z")
            return

        current_position = float(str(device.Position))

        new_position = current_position + amount

        device.MoveTo(
            Decimal(new_position),
            60000
        )

        print(
            "Motor: {} | Start: {} | Move: {} | New Position: {}".format(
                motor,
                current_position,
                amount,
                new_position
            )
        )


if __name__ == '__main__':
    # meets gantry at 0,0,12.95
    K = KinesisXYZHelper()
    K.connectAll()

    # K.moveMotor('z', .75)

    # K.planeScanNoMeasure(
    #     xStart=5,
    #     yStart=5,
    #     zStart=12.95,
    #     xyPitch=10,
    #     xStep=2,
    #     yStep=2
    # )

    # PID until load reaches 100
    K.PID(
        target=100,
        Kp=0.01,
        Ki=0.0,
        Kd=0.0,
        tolerance=0.5
    )
    K.moveMotor('z', -.75)

    K.closeAll()
