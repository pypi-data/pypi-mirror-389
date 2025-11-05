from ..base import VisionCameraBase
import ctypes
import sys
import time
import numpy
from PIL import Image
import matplotlib.pyplot as plt
from .LJ_X8000A_PyLib_1_3_0_3 import LJXAwrap


class Keyence3dLineScan(VisionCameraBase):
    def __init__(self, deviceId=0,
                 ip_addr='192.168.0.1',
                 ProgramNo=0,
                 wPortNo=24691,
                 HighSpeedPortNo=24692,
                 ysize=1
                 ):

        super(Keyence3dLineScan, self).__init__()
        self.image_available = False  # Flag to conrirm the completion of image acquisition.
        self.ysize_acquired = 0  # Number of Y lines of acquired image.
        self.z_val = []  # The buffer for height image.
        self.lumi_val = []  # The buffer for luminance image.
        self.deviceId = deviceId
        self.ip_addr = ip_addr  # ip address
        self.wPortNo = wPortNo  # Port No.
        self.HighSpeedPortNo = HighSpeedPortNo  # Port No. for high-speed
        self.ProgramNo = ProgramNo  # proagram No.
        self.ysize = ysize  # Number of Y lines.
        self.use_external_batchStart = False  # 'True' if you start batch externally.
        self.ethernetConfig = None
        self.profinfo = None
        res = self._connect()  # connect camera

    def _connect(self):
        try:
            ip_list = [int(x) for x in self.ip_addr.split('.')]
            self.ethernetConfig = LJXAwrap.LJX8IF_ETHERNET_CONFIG()
            for i in range(len(ip_list)):
                self.ethernetConfig.abyIpAddress[i] = ip_list[i]  # 192
            self.ethernetConfig.wPortNo = self.wPortNo  # Port No.
            self.__ethernetOpen()
            self.__set_programNo(self.ProgramNo)
            self.__initHighSpeedCommunication()
            self.__preStartHighSpeedCommunication()
            self.__startHighSpeedCommunication()
            self.__allocateMemory()
            self.__startMeasure()
            return 1
        except Exception as e:
            return 0

    def capture(self, timeout=-1):  # -1 代表永不超时
        # wait for the image acquisition complete
        start_time = time.time()
        while True:
            if self.image_available:
                break
            if timeout == -1:
                time.sleep(0.01)
                continue
            elif time.time() - start_time > timeout:
                break
        if self.image_available is not True:
            print("\nFailed to acquire image (timeout)")
            print("\nTerminated normally.")
            return None, None

        ZUnit = ctypes.c_ushort()
        LJXAwrap.LJX8IF_GetZUnitSimpleArray(self.deviceId, ZUnit)
        self.ZUnit = ZUnit
        self.image_available = False

        # todo 待测试是否要停止测量、清理缓存
        # self.__stopMeasure()
        # res = LJXAwrap.LJX8IF_ClearMemory(self.deviceId)
        # print('清理缓存',res)

        height_image = self._process__data(self.z_val)
        lumi_image = self._process__data(self.lumi_val)

        return height_image, lumi_image

    def _process__data(self, vals):
        """处理高度数据的优化版本"""
        # 方案1：如果数据源允许，直接生成 numpy 数组
        if hasattr(self.z_val, '__array__'):  # 检查是否已经是类数组对象
            image = numpy.asarray(vals, dtype=numpy.int32)
        else:
            image = numpy.fromiter(vals, dtype=numpy.int32,
                                   count=self.xsize * self.ysize)
        return image.reshape(self.ysize, self.xsize)

    def reconnect(self):
        self.stop()
        self.close()
        self._connect()

    def stop(self):
        res = LJXAwrap.LJX8IF_StopHighSpeedDataCommunication(self.deviceId)
        print("LJXAwrap.LJX8IF_StoptHighSpeedDataCommunication:", hex(res))
        # Finalize
        res = LJXAwrap.LJX8IF_FinalizeHighSpeedDataCommunication(self.deviceId)
        print("LJXAwrap.LJX8IF_FinalizeHighSpeedDataCommunication:", hex(res))

    def close(self):
        # Close
        res = LJXAwrap.LJX8IF_CommunicationClose(self.deviceId)
        print("LJXAwrap.LJX8IF_CommunicationClose:", hex(res))

    def get_infos(self):
        controllerSerial = ctypes.create_string_buffer(16)  # 获取序列号
        headSerial = ctypes.create_string_buffer(16)
        res = LJXAwrap.LJX8IF_GetSerialNumber(self.deviceId,
                                              controllerSerial, headSerial)
        print("LJXAwrap.LJX8IF_GetSerialNumber:", hex(res),
              "<controllerSerial>=", controllerSerial.value,
              "<headSerial>=", headSerial.value)
        print("---------------------------------------------------------")
        headmodel = ctypes.create_string_buffer(32)
        res = LJXAwrap.LJX8IF_GetHeadModel(self.deviceId, headmodel)
        print("LJXAwrap.LJX8IF_GetHeadModel:", hex(res),
              "<headmodel>=", headmodel.value)
        print("---------------------------------------------------------")
        sensorT = ctypes.c_short()
        processorT = ctypes.c_short()
        caseT = ctypes.c_short()
        res = LJXAwrap.LJX8IF_GetHeadTemperature(self.deviceId,
                                                 sensorT, processorT, caseT)
        print("LJXAwrap.LJX8IF_GetHeadTemperature:", hex(res),
              "<SensorT, ProcessorT, CaseT [degree Celsius]>=",
              sensorT.value / 100.0, processorT.value / 100.0, caseT.value / 100.0)
        print("----")

    def get_status(self):
        try:
            attentionStatus = ctypes.c_ushort()
            res = LJXAwrap.LJX8IF_GetAttentionStatus(self.deviceId, attentionStatus)
            # print("LJXAwrap.LJX8IF_GetAttentionStatus:", hex(res),
            #       "<AttentionStatus>=", bin(attentionStatus.value))
            # print("----")
            if res == 0:
                return 1
            else:
                return 0
        except:
            return 0

    def __set_programNo(self, ProgramNo):
        res = LJXAwrap.LJX8IF_ChangeActiveProgram(self.deviceId, ProgramNo)
        print("LJXAwrap.LJX8IF_ChangeActiveProgram:", hex(res),
              "<ProgramNo_set>=", ProgramNo)
        # Get active program No.
        programNo_get = ctypes.c_ubyte()
        res = LJXAwrap.LJX8IF_GetActiveProgram(self.deviceId, programNo_get)
        print("LJXAwrap.LJX8IF_GetActiveProgram:", hex(res),
              "<ProgramNo_get>=", programNo_get.value)
        print("----")

    def __ethernetOpen(self):
        res = LJXAwrap.LJX8IF_EthernetOpen(0, self.ethernetConfig)
        if res != 0:
            print("Failed to connect contoller.")
            print("Exit the program.")
            sys.exit()

    def __initHighSpeedCommunication(self):
        self.my_callback_s_a = LJXAwrap.LJX8IF_CALLBACK_SIMPLE_ARRAY(self.__callback_func)
        res = LJXAwrap.LJX8IF_InitializeHighSpeedDataCommunicationSimpleArray(
            self.deviceId,
            self.ethernetConfig,
            self.HighSpeedPortNo,
            self.my_callback_s_a,
            self.ysize,
            0)
        if res != 0:
            print("\nExit the program.InitializeHighSpeedDataCommunicationSimpleArray:error")
            sys.exit()

    def __callback_func(self, p_header,
                        p_height,
                        p_lumi,
                        luminance_enable,
                        xpointnum,
                        profnum,
                        notify, user):

        if (notify == 0) or (notify == 0x10000):
            if profnum != 0:
                if self.image_available is False:
                    for i in range(xpointnum * profnum):
                        self.z_val[i] = p_height[i]
                        if luminance_enable == 1:
                            self.lumi_val[i] = p_lumi[i]  # queue
                    self.ysize_acquired = profnum
                    self.image_available = True
        return

    def __preStartHighSpeedCommunication(self):
        req = LJXAwrap.LJX8IF_HIGH_SPEED_PRE_START_REQ()
        req.bySendPosition = 2
        self.profinfo = LJXAwrap.LJX8IF_PROFILE_INFO()

        res = LJXAwrap.LJX8IF_PreStartHighSpeedDataCommunication(
            self.deviceId,
            req,
            self.profinfo)
        if res != 0:
            print("\nExit the program:PreStartHighSpeedDataCommunication error")
            sys.exit()

    def __startHighSpeedCommunication(self):
        # Start Hi-Speed Communication
        self.image_available = False
        res = LJXAwrap.LJX8IF_StartHighSpeedDataCommunication(self.deviceId)
        if res != 0:
            print("\nExit the program: StartHighSpeedDataCommunication error")
            sys.exit()

    def __allocateMemory(self):
        # allocate the memory
        self.xsize = self.profinfo.wProfileDataCount
        self.z_val = [0] * self.xsize * self.ysize
        self.lumi_val = [0] * self.xsize * self.ysize

    def __startMeasure(self):
        if self.use_external_batchStart is False:
            LJXAwrap.LJX8IF_StartMeasure(self.deviceId)

    def __stopMeasure(self):
        res = LJXAwrap.LJX8IF_StopMeasure(self.deviceId)
        print('停止测量', res)
        self.use_external_batchStart = True

    def display(self, z_val, lumi_val):
        fig = plt.figure(figsize=(4.0, 6.0))
        plt.subplots_adjust(hspace=0.5)

        # Height image display
        ax1 = fig.add_subplot(3, 1, 1)
        img1 = Image.new('I', (self.xsize, self.ysize))
        img1.putdata(list(map(int, z_val)))
        im_list1 = numpy.asarray(img1)

        ax1.imshow(im_list1,
                   cmap='gray',
                   vmin=0,
                   vmax=65535,
                   interpolation='none')

        plt.title("Height Image")

        # Luminance image display
        ax2 = fig.add_subplot(3, 1, 2)
        img2 = Image.new('I', (self.xsize, self.ysize))
        img2.putdata(list(map(int, lumi_val)))
        im_list2 = numpy.asarray(img2)

        ax2.imshow(im_list2,
                   cmap='gray',
                   vmin=0,
                   vmax=1024,
                   interpolation='none')

        plt.title("Luminance Image")

        # Height profile display
        ax3 = fig.add_subplot(3, 1, 3)
        sl = int(self.xsize * self.ysize_acquired / 2)  # the horizontal center profile

        x_val_mm = [0.0] * self.xsize
        z_val_mm = [0.0] * self.xsize
        for i in range(self.xsize):
            # Conver X data to the actual length in millimeters
            x_val_mm[i] = (self.profinfo.lXStart + self.profinfo.lXPitch * i) / 100.0  # um
            x_val_mm[i] /= 1000.0  # mm

            # Conver Z data to the actual length in millimeters
            if z_val[sl + i] == 0:  # invalid value
                z_val_mm[i] = numpy.nan
            else:
                # 'Simple array data' is offset to be unsigned 16-bit data.
                # Decode by subtracting 32768 to get a signed value.
                z_val_mm[i] = int(z_val[sl + i]) - 32768  # decode
                z_val_mm[i] *= self.ZUnit.value / 100.0  # um
                z_val_mm[i] /= 1000.0  # mm

        plotz_min = numpy.nanmin(z_val_mm)
        if numpy.isnan(plotz_min):
            plotz_min = -1.0
        else:
            plotz_min -= 1.0

        plotz_max = numpy.nanmax(z_val_mm)
        if numpy.isnan(plotz_max):
            plotz_max = 1.0
        else:
            plotz_max += 1.0

        plt.ylim(plotz_min, plotz_max)
        ax3.plot(x_val_mm, z_val_mm)

        plt.title("Height Profile")
        # Show all plot
        print("\nPress 'q' key to exit the program...")
        plt.show()
        plt.close('all')


if __name__ == '__main__':

    # 相机类
    camera = Keyence3dLineScan(deviceId=0, ProgramNo=0, ip_addr='192.168.0.1', wPortNo=24691, HighSpeedPortNo=24692,
                               ysize=500)
    while 1:
        # 采集图像
        p1, p2 = camera.capture(-1)
        camera.display(p1, p2)
        # im_list1 = np.array(p1, dtype=np.int32).reshape(camera.ysize, camera.xsize)
        # im_list2 = np.array(p2, dtype=np.int32).reshape(camera.ysize, camera.xsize)
        # print(im_list1)
        # print(im_list2)
        # cv2.imwrite('1.tif', im_list1)
        # cv2.imwrite('2.tif', im_list2)
        time.sleep(0.05)
        break
