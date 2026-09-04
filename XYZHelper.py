import clr
import time
# import oneTimeScan as ots

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.Benchtop.StepperMotorCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import *
from System import Decimal

class KinesisXYZHelper:
    def __init__(self):
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


if __name__ == '__main__':
    # meets gantry at 0,0,12.95
    K = KinesisXYZHelper()
    K.connectAll()
    K.planeScanNoMeasure(xStart=5,yStart=5,zStart=12.95,xyPitch=10,xStep=2,yStep=2)
    # time.sleep(3)
    K.closeAll()
