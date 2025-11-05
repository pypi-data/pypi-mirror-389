# -- coding: utf-8 --

import time


# sys.path.append("../MVSDK")
# from IMVFGApi import *

def displayDeviceInfo(interfaceList, deviceInfoList):
    print("Idx  Type   Vendor              Model           S/N                 DeviceUserID    IP Address")
    print("------------------------------------------------------------------------------------------------")
    for index in range(0, interfaceList.nInterfaceNum):
        interfaceInfo = interfaceList.pInterfaceInfoList[index]
        strType = ""
        strVendorName = interfaceInfo.vendorName.decode("ascii")
        strModeName = interfaceInfo.modelName.decode("ascii")
        serialNumber = interfaceInfo.serialNumber.decode("ascii")
        interfaceName = interfaceInfo.interfaceName.decode("ascii")
        if interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeGigEInterface:
            strType = "Gige Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeU3vInterface:
            strType = "U3V Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeCLInterface:
            strType = "CL Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeCXPInterface:
            strType = "CXP Card"
        print("[%d]  %s   %s    %s        %s            %s " % (
            index + 1, strType, strVendorName, strModeName, serialNumber, interfaceName))

        for i in range(0, deviceInfoList.nDevNum):
            pDeviceInfo = deviceInfoList.pDeviceInfoList[i]
            if pDeviceInfo.FGInterfaceInfo.interfaceKey == interfaceInfo.interfaceKey:
                strType = ""
                strIpAdress = ""
                strVendorName = pDeviceInfo.vendorName.decode("ascii")
                strModeName = pDeviceInfo.modelName.decode("ascii")
                strSerialNumber = pDeviceInfo.serialNumber.decode("ascii")
                strCameraname = pDeviceInfo.cameraName.decode("ascii")
                if pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_GIGE_DEVICE:
                    strType = "Gige"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_U3V_DEVICE:
                    strType = "U3V"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_CL_DEVICE:
                    strType = "CL"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_CXP_DEVICE:
                    strType = "CXP"
                print("  |-%d  %s   %s    %s      %s     %s           %s" % (
                    int(i) + 1, strType, strVendorName, strModeName, strSerialNumber, strCameraname, strIpAdress))

    return


def selectSaveFormat(inputstr):
    # print("--------------------------------------------")
    # print("0.Save to BMP")
    # print("1.Save to Jpeg")
    # print("2.Save to Png")
    # print("3.Save to Tif")
    # print("--------------------------------------------")
    if int(inputstr) == 0:
        # print("select ", IMV_FG_ESaveType.typeImageBmp)
        return IMV_FG_ESaveType.typeImageBmp
    elif int(inputstr) == 1:
        # print("select typeImageJpeg", IMV_FG_ESaveType.typeImageJpeg)
        return IMV_FG_ESaveType.typeImageJpeg
    elif int(inputstr) == 2:
        # print("select typeImagePng", IMV_FG_ESaveType.typeImagePng)
        return IMV_FG_ESaveType.typeImagePng
    elif int(inputstr) == 3:
        # print("select typeImageTif", IMV_FG_ESaveType.typeImageTif)
        return IMV_FG_ESaveType.typeImageTif
    else:
        # print("select typeImageBmp", IMV_FG_ESaveType.typeImageBmp)
        return IMV_FG_ESaveType.typeImageBmp


import traceback
from utils.custom_print import *
import cv2
import numpy as np


def displayDeviceInfo(interfaceList, deviceInfoList):
    print("Idx  Type   Vendor              Model           S/N                 DeviceUserID    IP Address")
    print("------------------------------------------------------------------------------------------------")
    for index in range(0, interfaceList.nInterfaceNum):
        interfaceInfo = interfaceList.pInterfaceInfoList[index]
        strType = ""
        strVendorName = interfaceInfo.vendorName.decode("ascii")
        strModeName = interfaceInfo.modelName.decode("ascii")
        serialNumber = interfaceInfo.serialNumber.decode("ascii")
        interfaceName = interfaceInfo.interfaceName.decode("ascii")
        if interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeGigEInterface:
            strType = "Gige Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeU3vInterface:
            strType = "U3V Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeCLInterface:
            strType = "CL Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeCXPInterface:
            strType = "CXP Card"
        print("[%d]  %s   %s    %s        %s            %s " % (
            index + 1, strType, strVendorName, strModeName, serialNumber, interfaceName))

        for i in range(0, deviceInfoList.nDevNum):
            pDeviceInfo = deviceInfoList.pDeviceInfoList[i]
            if pDeviceInfo.FGInterfaceInfo.interfaceKey == interfaceInfo.interfaceKey:
                strType = ""
                strIpAdress = ""
                strVendorName = pDeviceInfo.vendorName.decode("ascii")
                strModeName = pDeviceInfo.modelName.decode("ascii")
                strSerialNumber = pDeviceInfo.serialNumber.decode("ascii")
                strCameraname = pDeviceInfo.cameraName.decode("ascii")
                if pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_GIGE_DEVICE:
                    strType = "Gige"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_U3V_DEVICE:
                    strType = "U3V"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_CL_DEVICE:
                    strType = "CL"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_CXP_DEVICE:
                    strType = "CXP"
                print("  |-%d  %s   %s    %s      %s     %s           %s" % (
                    int(i) + 1, strType, strVendorName, strModeName, strSerialNumber, strCameraname, strIpAdress))
    return


class CamComm(object):

    def __init__(self, camId=0):
        self.mvsdk = None
        self.card = None
        self.connect_handler = {
            0: self.fakecam_connect,
            # 1: self.mvs_connect,
            # 2: self.hk2d_connect,
            3: self.huaray2dcard_connect,
            4: self.opt2d_connect,
        }
        self.camId = camId
        self.cam_sn = config['cameras']['camsns'][camId]
        self.card_sn = config['cameras']['cardsns'][camId]
        self.cfg_file = config['cameras']['configuration'][camId]

    def init_cam(self, cam_mode):
        '''
        初始化相机
        '''
        self.cam_mode = cam_mode
        self.connect_handler.get(cam_mode, self.unknown_cammode)()

    def captrue(self, exposetime=-1):
        '''
        调用相机拍照
        :param exposetime:曝光时间
        '''
        if self.mvsdk == None:
            printerror('mvsdk is None!')
            return

        ret = None
        # 0:Fake PLC; 1：PLC TCP； 2： PLC RS485
        if self.cam_mode == 0:
            ret = self.fake_capture(exposetime)
        elif self.cam_mode == 1:
            ret = self.mvs_capture(exposetime)  # address, count, slave address
        elif self.cam_mode == 2:
            ret = self.hk_capture(exposetime)  # address, count, slave address
        elif self.cam_mode == 3:
            ret = self.huaray_capture(exposetime)  # address, count, slave address
        else:
            printerror('Unknown cam mode!')
        return ret

    def unknown_cammode(self):
        printerror('Unknown cam mode!')

    def fakecam_connect(self):
        self.mvsdk = 0
        printdebug('Start!')

    def huaray2dcard_connect(self):
        print("SDK Version:", MvCamera.IMV_FG_GetVersion().decode("ascii"))
        card = Capture()
        cam = MvCamera()
        print("Enum capture board interface info.")
        # 枚举采集卡设备
        interfaceList = IMV_FG_INTERFACE_INFO_LIST()
        interfaceTp = IMV_FG_EInterfaceType.typeCLInterface | IMV_FG_EInterfaceType.typeCXPInterface
        nRet = card.IMV_FG_EnumInterface(interfaceTp, interfaceList)
        if (IMV_FG_OK != nRet):
            print("Enumeration devices failed! errorCode:", nRet)
            sys.exit()
        if (interfaceList.nInterfaceNum == 0):
            print("No board device find. board list size:", interfaceList.nInterfaceNum)
            sys.exit()
        print("Enum camera device.")
        # 枚举相机设备
        nInterfacetype = IMV_FG_EInterfaceType.typeCLInterface | IMV_FG_EInterfaceType.typeCXPInterface
        deviceList = IMV_FG_DEVICE_INFO_LIST()
        nRet = card.IMV_FG_EnumDevices(nInterfacetype, deviceList)
        if IMV_FG_OK != nRet:
            print("Enumeration devices failed! ErrorCode", nRet)
            sys.exit()
        if deviceList.nDevNum == 0:
            print("find no device!")
            sys.exit()
        # 打印相机基本信息（序号,类型,制造商信息,型号,序列号,用户自定义ID)
        displayDeviceInfo(interfaceList, deviceList)
        cardid, camid = self.getcardcamindex(interfaceList, deviceList)
        # 打开采集卡
        nRet = card.IMV_FG_OpenInterface(cardid)
        if (IMV_FG_OK != nRet):
            print("Open capture board device failed! errorCode:", nRet)
            sys.exit()
        # 打开相机
        nRet = cam.IMV_FG_OpenDevice(IMV_FG_ECreateHandleMode.IMV_FG_MODE_BY_INDEX,
                                     byref(c_void_p(camid)))
        if IMV_FG_OK != nRet:
            print("Open devHandle failed! ErrorCode", nRet)
            sys.exit()
        # 加载相机属性配置文件
        errorList = IMV_FG_ErrorList()
        memset(byref(errorList), 0, sizeof(IMV_FG_ErrorList))
        nRet = cam.IMV_FG_LoadDeviceCfg(self.cfg_file, errorList)
        if IMV_FG_OK != nRet:
            print("Load camera configuration fail! ErrorCode", nRet)
            sys.exit()
        for errorIndex in range(0, errorList.nParamCnt):
            print("Error paramName ", errorList.paramNameList[errorIndex].str)
        # 开始拉流
        nRet = card.IMV_FG_StartGrabbing()
        if IMV_FG_OK != nRet:
            print("Start grabbing failed! ErrorCode", nRet)
            sys.exit()
        print('相机启动成功，采集卡成功:', self.cam_sn, self.card_sn)
        self.card = card
        self.mvsdk = cam
        #####################################################################################################

    def getcardcamindex(self, interfaceList, deviceInfoList):

        card_index = -1
        cam_index = -1
        for index in range(0, interfaceList.nInterfaceNum):
            interfaceInfo = interfaceList.pInterfaceInfoList[index]
            serialNumber = interfaceInfo.serialNumber.decode("ascii")
            if serialNumber == self.card_sn:
                card_index = index
                break

        for i in range(0, deviceInfoList.nDevNum):
            pDeviceInfo = deviceInfoList.pDeviceInfoList[i]
            strSerialNumber = pDeviceInfo.serialNumber.decode("ascii")
            if strSerialNumber == self.cam_sn:
                cam_index = i
                break

        return card_index, cam_index

    def opt2d_connect(self):
        pass

    def huaray_capture(self, exposetime):
        try:
            t0 = time.time()
            if exposetime != -1:
                ret = self.mvsdk.IMV_FG_SetDoubleFeatureValue('ExposureTime', float(exposetime) * 1000)
            else:
                ret = self.mvsdk.IMV_FG_SetDoubleFeatureValue('ExposureTime', -1)
            if ret != 0:
                printerror('set ExposureTime Failure')
            frame = IMV_FG_Frame()
            nRet = self.card.IMV_FG_GetFrame(frame, -1)
            if IMV_FG_OK != nRet:
                print("Get frame failed!ErrorCode[%d]" % nRet)
                sys.exit()
            t1 = time.time()
            nChannelNum = 0

            if IMV_FG_EPixelType.IMV_FG_PIXEL_TYPE_Mono8 == frame.frameInfo.pixelFormat:
                nChannelNum = 1
            elif IMV_FG_EPixelType.IMV_FG_PIXEL_TYPE_BGR8 == frame.frameInfo.pixelFormat:
                nChannelNum = 3
            elif IMV_FG_EPixelType.IMV_FG_PIXEL_TYPE_RGB8 == frame.frameInfo.pixelFormat:
                nChannelNum = 3
            if None == frame.pData:
                printerror("stFlipImageParam pSrcData is NULL!")
                return None
            BufSize = frame.frameInfo.width * frame.frameInfo.height * nChannelNum
            pBuf = (c_ubyte * BufSize)()
            cdll.msvcrt.memcpy(byref(pBuf), pBuf, BufSize)
            image = np.array(pBuf)
            image = image.reshape((frame.frameInfo.height, frame.frameInfo.width))

            nRet = self.card.IMV_FG_ReleaseFrame(frame)
            if IMV_FG_OK != nRet:
                print("IMV_FG_ReleaseFrame failed! ErrorCode", nRet)
                sys.exit()
            print('capture once :', t1 - t0)
            return image
        except Exception as e:
            printerror(traceback.format_exc())


if __name__ == "__main__":
    from datetime import datetime

    a = CamComm(0)
    a.init_cam(3)
    cc = 0
    while 1:
        cc+=1
        aaa = datetime.now().strftime('%Y-%m-%d %H-%M-%S-%f.jpg')

        f = a.captrue(25)
        image = cv2.resize(f, (0, 0), fx=0.5, fy=0.5)
        cv2.imwrite('D:/capture' + os.sep + aaa, image)
        if cc >100:
            break
    # cv2.imshow('22',image)
    # cv2.waitKey(0)
