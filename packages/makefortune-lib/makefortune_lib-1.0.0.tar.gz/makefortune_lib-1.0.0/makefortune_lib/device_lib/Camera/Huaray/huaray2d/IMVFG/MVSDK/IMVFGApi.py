# -- coding: utf-8 --
import sys
import platform
import os

x64mvsdk = [x for x in os.getenv('GENICAM_GENTL64_PATH').split(';') if r'Runtime\x64' in x]
assert len(x64mvsdk) == 1, 'MVSDKmd.dll文件路径获取失败'
# 加载SDK动态库
if sys.platform == 'win32':
    print("Windows")
    bits, linkage = platform.architecture()
    if bits == '64bit':
        MVSDKdll = WinDLL(x64mvsdk[0] + "\MVSDKmd.dll")
    else:
        MVSDKdll = WinDLL("../../../../../Runtime/Win32/MVSDKmd.dll")
else:
    print("Linux")
    MVSDKdll = CDLL("../../../lib/libMVSDK.so")


class Capture():

    def __init__(self):
        self._handle = c_void_p()  # 记录采集卡句柄
        self.handle = pointer(self._handle)  # 创建句柄指针

    @staticmethod
    def IMV_FG_GetVersion():  # 获取版本信息 成功时返回版本信息，失败时返回NULL
        MVSDKdll.IMV_FG_GetVersion.restype = c_char_p
        # C原型：const char* IMV_FG_CALL IMV_FG_GetVersion(void);
        return MVSDKdll.IMV_FG_GetVersion()

    # 枚举采集卡设备
    # 成功，返回IMV_FG_OK，错误，返回错误码。
    # 1、当interfaceType = typeGevInterface时，枚举所有GigE网口下的在线设备
    # 2、当interfaceType = typeU3vInterface时，枚举所有USB接口下的在线设备
    # 3、当interfaceType = typeCLInterface时，枚举所有CameraLink接口下的在线设备
    # 4、当interfaceType = typeCXPInterface时，枚举所有CXP接口下的在线设备
    # 5、该接口下的interfaceType支持任意接口类型的组合,如，若枚举所有GigE网口和USB3
    # 接口下的在线设备时, 可将interfaceType设置为 interfaceType = interfaceTypeGige
    # | interfaceTypeUsb3,其它接口类型组合以此类推
    @staticmethod
    def IMV_FG_EnumInterface(interfaceType, pInterfaceList):
        MVSDKdll.IMV_FG_EnumInterface.argtype = (c_uint, c_void_p)
        MVSDKdll.IMV_FG_EnumInterface.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_EnumInterface(OUT IMV_FG_INTERFACE_INFO_LIST *pDeviceList, IN unsigned int interfaceType);
        return MVSDKdll.IMV_FG_EnumInterface(c_uint(interfaceType), byref(pInterfaceList))

    # 采集卡的连接与关闭  采集卡设备（根据句柄连接设备）
    # 成功，返回IMV_FG_OK；错误，返回错误码
    # input 采集卡对象，采集卡对应序号
    def IMV_FG_OpenInterface(self, nIndex):
        MVSDKdll.IMV_FG_OpenInterface.argtype = (c_uint, c_void_p)
        MVSDKdll.IMV_FG_OpenInterface.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_OpenInterface(IN unsigned int nIndex, OUT IMV_FG_IF_HANDLE* handle);
        return MVSDKdll.IMV_FG_OpenInterface(c_uint(nIndex), byref(self.handle))

    def IMV_FG_OpenInterfaceEx(self, mode, pIdentifier):
        MVSDKdll.IMV_FG_OpenInterface.argtype = (c_uint, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_OpenInterface.argtype = (c_uint, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_OpenInterface.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_OpenInterfaceEx(IN IMV_FG_ECreateHandleMode mode, IN void* pIdentifier, OUT IMV_FG_IF_HANDLE* hIFDev);
        return MVSDKdll.IMV_FG_OpenInterfaceEx(c_uint(mode), pIdentifier, byref(self.handle))

    # 判断采集卡设备是否已打开
    # 打开状态，返回true；关闭状态或者掉线状态，返回false
    def IMV_FG_IsOpenInterface(self):
        MVSDKdll.IMV_FG_IsOpenInterface.argtype = c_void_p
        MVSDKdll.IMV_FG_IsOpenInterface.restype = c_bool
        # C原型:int IMV_FG_CALL IMV_FG_IsOpenInterface(IN IMV_FG_IF_HANDLE handle);
        return MVSDKdll.IMV_FG_IsOpenInterface(self.handle)

    # 关闭设备（根据句柄断开设备）
    # 成功，返回IMV_FG_OK；错误，返回错误码
    def IMV_FG_CloseInterface(self):
        MVSDKdll.IMV_FG_CloseInterface.argtype = c_void_p
        MVSDKdll.IMV_FG_CloseInterface.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_CloseInterface(IN IMV_FG_IF_HANDLE handle);
        return MVSDKdll.IMV_FG_CloseInterface(self.handle)

    # 枚举相机设备
    @staticmethod
    def IMV_FG_EnumDevices(nInterfaceType, pDeviceList):
        MVSDKdll.IMV_FG_EnumDevices.argtype = (c_uint, c_void_p)
        MVSDKdll.IMV_FG_EnumDevices.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_EnumDevices(IN unsigned int nInterfaceType, OUT IMV_FG_DEVICE_INFO_LIST* pDeviceList);
        return MVSDKdll.IMV_FG_EnumDevices(c_uint(nInterfaceType), byref(pDeviceList))

    # 设置帧数据缓存个数
    # 成功，返回IMV_FG_OK；错误，返回错误码
    # 不能在拉流过程中设置
    def IMV_FG_SetBufferCount(self, nSize):
        MVSDKdll.IMV_FG_SetBufferCount.argtype = (c_void_p, c_uint)
        MVSDKdll.IMV_FG_SetBufferCount.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_SetBufferCount(IN IMV_FG_IF_HANDLE handle, IN unsigned int nSize);
        return MVSDKdll.IMV_FG_SetBufferCount(self.handle, c_uint(nSize))

    # 清除帧数据缓存
    # 成功，返回IMV_FG_OK；错误，返回错误码
    def IMV_FG_ClearFrameBuffer(self):
        MVSDKdll.IMV_FG_ClearFrameBuffer.argtype = c_void_p
        MVSDKdll.IMV_FG_ClearFrameBuffer.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_ClearFrameBuffer(IN IMV_FG_IF_HANDLE handle);
        return MVSDKdll.IMV_FG_ClearFrameBuffer(self.handle)

    # 开始取流
    # 成功，返回IMV_FG_OK；错误，返回错误码
    def IMV_FG_StartGrabbing(self):
        MVSDKdll.IMV_FG_StartGrabbing.argtype = c_void_p
        MVSDKdll.IMV_FG_StartGrabbing.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_StartGrabbing(IN IMV_FG_IF_HANDLE handle);
        return MVSDKdll.IMV_FG_StartGrabbing(self.handle)

    # 开始取流
    # maxImagesGrabbed  允许最多的取帧数，达到指定取帧数后停止取流，如果为0，表示忽略此参数连续取流(IMV_FG_StartGrabbing 默认0)
    # strategy  取流策略,(IMV_FG_StartGrabbing默认使用grabStrartegySequential策略取流)
    def IMV_FG_StartGrabbingEx(self, maxImagesGrabbed, strategy):
        MVSDKdll.IMV_FG_StartGrabbingEx.argtype = (c_void_p, c_uint64, c_uint)
        MVSDKdll.IMV_FG_StartGrabbingEx.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_StartGrabbingEx(IN IMV_FG_IF_HANDLE handle, IN uint64_t maxImagesGrabbed, IN IMV_FG_EGrabStrategy strategy);
        return MVSDKdll.IMV_FG_StartGrabbingEx(self.handle, c_uint64(maxImagesGrabbed), c_uint(strategy))

    # 判断设备是否正在取流 正在取流，返回true；不在取流，返回false
    def IMV_FG_IsGrabbing(self):
        MVSDKdll.IMV_FG_IsGrabbing.argtype = c_void_p
        MVSDKdll.IMV_FG_IsGrabbing.restype = c_bool
        # C原型:int IMV_FG_CALL IMV_FG_IsGrabbing(IN IMV_FG_IF_HANDLE handle);
        return MVSDKdll.IMV_FG_IsGrabbing(self.handle)

    # 停止取流
    # 成功，返回IMV_FG_OK；错误，返回错误码
    def IMV_FG_StopGrabbing(self):
        MVSDKdll.IMV_FG_StopGrabbing.argtype = c_void_p
        MVSDKdll.IMV_FG_StopGrabbing.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_StopGrabbing(IN IMV_FG_IF_HANDLE handle);
        return MVSDKdll.IMV_FG_StopGrabbing(self.handle)

    #
    #  proc 类型IMV_FG_FrameCallBack  帧数据信息回调函数，建议不要在该函数中处理耗时的操作，否则会阻塞后续帧数据的实时性
    # 注册帧数据回调函数(异步获取帧数据机制)
    # 成功，返回IMV_FG_OK；错误，返回错误码
    # 该异步获取帧数据机制和同步获取帧数据机制(IMV_FG_GetFrame)互斥，对于同一设备，
    # 系统中两者只能选其一
    def IMV_FG_AttachGrabbing(self, proc, pUser):
        MVSDKdll.IMV_FG_AttachGrabbing.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_AttachGrabbing.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_AttachGrabbing(IN IMV_FG_IF_HANDLE handle, IN IMV_FG_FrameCallBack proc, IN void* pUser);
        return MVSDKdll.IMV_FG_AttachGrabbing(self.handle, proc, pUser)

    # 获取一帧图像(同步获取帧数据机制)
    # 成功，返回IMV_FG_OK；错误，返回错误码
    # 该接口不支持多线程调用。
    # 该同步获取帧机制和异步获取帧机制(IMV_FG_AttachGrabbing)
    # 互斥, 对于同一设备，系统
    # 中两者只能选其一
    # pFrame 返回帧数据信息
    #  timeoutMS 获取一帧图像的超时时间, INFINITE时表示无限等待,直到收到一帧数据或者停止取流。单位是毫秒
    def IMV_FG_GetFrame(self, pFrame, timeoutMS):
        MVSDKdll.IMV_FG_GetFrame.argtype = (c_void_p, c_void_p, c_uint)
        MVSDKdll.IMV_FG_GetFrame.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_GetFrame(IN IMV_FG_IF_HANDLE handle, OUT IMV_FG_Frame* pFrame, IN unsigned int timeoutMS);
        return MVSDKdll.IMV_FG_GetFrame(self.handle, byref(pFrame), c_uint(timeoutMS))

    # 释放图像缓存
    def IMV_FG_ReleaseFrame(self, pFrame):
        MVSDKdll.IMV_FG_ReleaseFrame.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_ReleaseFrame.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_ReleaseFrame(IN IMV_FG_IF_HANDLE handle, IN IMV_FG_Frame* pFrame);
        return MVSDKdll.IMV_FG_ReleaseFrame(self.handle, byref(pFrame))

    # 帧数据深拷贝克隆 成功，返回IMV_FG_OK；错误，返回错误码  使用IMV_FG_ReleaseFrame进行释放图像缓存
    # pFrame 克隆源帧数据信息   out 新的帧数据信息
    def IMV_FG_CloneFrame(self, pFrame, pCloneFrame):
        MVSDKdll.IMV_FG_CloneFrame.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_CloneFrame.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_CloneFrame(IN IMV_FG_IF_HANDLE handle, IN IMV_FG_Frame* pFrame, OUT IMV_FG_Frame* pCloneFrame);
        return MVSDKdll.IMV_FG_CloneFrame(self.handle, byref(pFrame), byref(pCloneFrame))

    # 获取流统计信息(IMV_FG_StartGrabbing / IMV_FG_StartGrabbingEx执行后调用)
    def IMV_FG_GetStatisticsInfo(self, pStreamStatsInfo):
        MVSDKdll.IMV_FG_GetStatisticsInfo.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetStatisticsInfo.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_GetStatisticsInfo(IN IMV_FG_IF_HANDLE handle, OUT IMV_FG_StreamStatisticsInfo* pStreamStatsInfo);
        return MVSDKdll.IMV_FG_GetStatisticsInfo(self.handle, byref(pStreamStatsInfo))

    # 重置流统计信息(IMV_FG_StartGrabbing / IMV_FG_StartGrabbingEx执行后调用)
    def IMV_FG_ResetStatisticsInfo(self):
        MVSDKdll.IMV_FG_ResetStatisticsInfo.argtype = (c_void_p)
        MVSDKdll.IMV_FG_ResetStatisticsInfo.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_ResetStatisticsInfo(IN IMV_FG_IF_HANDLE handle);
        return MVSDKdll.IMV_FG_ResetStatisticsInfo(self.handle)

    # 下载设备描述XML文件，并保存到指定路径，如：D://xml.zip
    # 成功，返回IMV_FG_OK；错误，返回错误码
    def IMV_FG_DownLoadGenICamXML(self, pFullFileName):
        MVSDKdll.IMV_FG_DownLoadGenICamXML.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_DownLoadGenICamXML.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_DownLoadGenICamXML(IN HANDLE handle, IN const char* pFullFileName);
        return MVSDKdll.IMV_FG_DownLoadGenICamXML(self.handle, pFullFileName.encode('ascii'))

    # ch:保存设备配置到指定的位置。同名文件已存在时，覆盖。
    def IMV_FG_SaveDeviceCfg(self, pFullFileName):
        MVSDKdll.IMV_FG_SaveDeviceCfg.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SaveDeviceCfg.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SaveDeviceCfg(IN HANDLE handle, IN const char* pFullFileName);
        return MVSDKdll.IMV_FG_SaveDeviceCfg(self.handle, pFullFileName.encode('ascii'))

    # ch:从文件加载设备xml配置
    # 成功，返回IMV_FG_OK；错误，返回错误码。
    def IMV_FG_LoadDeviceCfg(self, pFullFileName, pErrorList):
        MVSDKdll.IMV_FG_LoadDeviceCfg.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_LoadDeviceCfg.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_LoadDeviceCfg(IN HANDLE handle, IN const char* pFullFileName, OUT IMV_ErrorList* pErrorList);
        return MVSDKdll.IMV_FG_LoadDeviceCfg(self.handle, pFullFileName.encode('ascii'), byref(pErrorList))

        # ch:判断属性是否可用

    def IMV_FG_FeatureIsAvailable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsAvailable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsAvailable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsAvailable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsAvailable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否可读
    def IMV_FG_FeatureIsReadable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsReadable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsReadable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsReadable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsReadable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否可写
    def IMV_FG_FeatureIsWriteable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsWriteable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsWriteable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsWriteable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsWriteable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否可流
    def IMV_FG_FeatureIsStreamable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsStreamable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsStreamable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsStreamable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsStreamable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否有效
    def IMV_FG_FeatureIsValid(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsValid.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsValid.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsValid(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsValid(self.handle, pFeatureName.encode('ascii'))

    # ch:获取属性类型
    def IMV_FG_GetFeatureType(self, pFeatureName, pPropertyType):
        MVSDKdll.IMV_FG_GetFeatureType.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetFeatureType.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_GetFeatureType(IN HANDLE handle, IN const char* pFeatureName, OUT IMV_EFeatureType* pPropertyType);
        return MVSDKdll.IMV_FG_GetFeatureType(self.handle, pFeatureName.encode('ascii'), byref(pPropertyType))

    # ch:获取整型属性值
    def IMV_FG_GetIntFeatureValue(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_FG_GetIntFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:获取整型属性可设的最小值
    def IMV_FG_GetIntFeatureMin(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureMin.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureMin.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureMin(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_FG_GetIntFeatureMin(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:获取整型属性可设的最大值
    def IMV_FG_GetIntFeatureMax(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureMax.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureMax.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureMax(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_FG_GetIntFeatureMax(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:获取整型属性步长
    def IMV_FG_GetIntFeatureInc(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureInc.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureInc.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureInc(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_FG_GetIntFeatureInc(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:设置整型属性值
    def IMV_FG_SetIntFeatureValue(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_SetIntFeatureValue.argtype = (c_void_p, c_void_p, c_int64)
        MVSDKdll.IMV_FG_SetIntFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetIntFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN int64_t intValue);
        return MVSDKdll.IMV_FG_SetIntFeatureValue(self.handle, pFeatureName.encode('ascii'), c_int64(pIntValue))

    # ch:获取浮点属性值
    def IMV_FG_GetDoubleFeatureValue(self, pFeatureName, pDoubleValue):
        MVSDKdll.IMV_FG_GetDoubleFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetDoubleFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetDoubleFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT double* pDoubleValue);
        return MVSDKdll.IMV_FG_GetDoubleFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pDoubleValue))

    # ch:获取浮点属性可设的最小值
    def IMV_FG_GetDoubleFeatureMin(self, pFeatureName, pDoubleValue):
        MVSDKdll.IMV_FG_GetDoubleFeatureMin.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetDoubleFeatureMin.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetDoubleFeatureMin(IN HANDLE handle, IN const char* pFeatureName, OUT double* pDoubleValue);
        return MVSDKdll.IMV_FG_GetDoubleFeatureMin(self.handle, pFeatureName.encode('ascii'), byref(pDoubleValue))

    # ch:获取浮点属性可设的最大值
    def IMV_FG_GetDoubleFeatureMax(self, pFeatureName, pDoubleValue):
        MVSDKdll.IMV_FG_GetDoubleFeatureMax.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetDoubleFeatureMax.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetDoubleFeatureMax(IN HANDLE handle, IN const char* pFeatureName, OUT double* pDoubleValue);
        return MVSDKdll.IMV_FG_GetDoubleFeatureMax(self.handle, pFeatureName.encode('ascii'), byref(pDoubleValue))

    # ch:设置浮点属性值
    def IMV_FG_SetDoubleFeatureValue(self, pFeatureName, doubleValue):
        MVSDKdll.IMV_FG_SetDoubleFeatureValue.argtype = (c_void_p, c_void_p, c_double)
        MVSDKdll.IMV_FG_SetDoubleFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetDoubleFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN double doubleValue);
        return MVSDKdll.IMV_FG_SetDoubleFeatureValue(self.handle, pFeatureName.encode('ascii'), c_double(doubleValue))

    # ch:获取布尔属性值
    def IMV_FG_GetBoolFeatureValue(self, pFeatureName, pBoolValue):
        MVSDKdll.IMV_FG_GetBoolFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetBoolFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetBoolFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT bool* pBoolValue);
        return MVSDKdll.IMV_FG_GetBoolFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pBoolValue))

    # ch:设置布尔属性值
    def IMV_FG_SetBoolFeatureValue(self, pFeatureName, boolValue):
        MVSDKdll.IMV_FG_SetBoolFeatureValue.argtype = (c_void_p, c_void_p, c_bool)
        MVSDKdll.IMV_FG_SetBoolFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetBoolFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN bool boolValue);
        return MVSDKdll.IMV_FG_SetBoolFeatureValue(self.handle, pFeatureName.encode('ascii'), c_bool(boolValue))

    # ch:获取枚举属性值
    def IMV_FG_GetEnumFeatureValue(self, pFeatureName, pEnumValue):
        MVSDKdll.IMV_FG_GetEnumFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_etEnumFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT uint64_t* pEnumValue);
        return MVSDKdll.IMV_FG_GetEnumFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pEnumValue))

    # ch:设置枚举属性值
    def IMV_FG_SetEnumFeatureValue(self, pFeatureName, enumValue):
        MVSDKdll.IMV_FG_SetEnumFeatureValue.argtype = (c_void_p, c_void_p, c_uint64)
        MVSDKdll.IMV_FG_SetEnumFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetEnumFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN uint64_t enumValue);
        return MVSDKdll.IMV_FG_SetEnumFeatureValue(self.handle, pFeatureName.encode('ascii'), enumValue)

    # ch:获取枚举属性symbol值
    def IMV_FG_GetEnumFeatureSymbol(self, pFeatureName, pEnumSymbol):
        MVSDKdll.IMV_FG_GetEnumFeatureSymbol.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureSymbol.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetEnumFeatureSymbol(IN HANDLE handle, IN const char* pFeatureName, OUT IMV_String* pEnumSymbol);
        return MVSDKdll.IMV_FG_GetEnumFeatureSymbol(self.handle, pFeatureName.encode('ascii'), byref(pEnumSymbol))

    # ch:设置枚举属性symbol值
    def IMV_FG_SetEnumFeatureSymbol(self, pFeatureName, pEnumSymbol):
        MVSDKdll.IMV_FG_SetEnumFeatureSymbol.argtype = (c_void_p, c_char_p, c_char_p)
        MVSDKdll.IMV_FG_SetEnumFeatureSymbol.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetEnumFeatureSymbol(IN HANDLE handle, IN const char* pFeatureName, IN const char* pEnumSymbol);
        return MVSDKdll.IMV_FG_SetEnumFeatureSymbol(self.handle, pFeatureName.encode('ascii'),
                                                    pEnumSymbol.encode('ascii'))

    # ch:获取枚举属性的可设枚举值的个数
    def IMV_FG_GetEnumFeatureEntryNum(self, pFeatureName, pEntryNum):
        MVSDKdll.IMV_FG_GetEnumFeatureEntryNum.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureEntryNum.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetEnumFeatureEntryNum(IN HANDLE handle, IN const char* pFeatureName, OUT unsigned int* pEntryNum);
        return MVSDKdll.IMV_FG_GetEnumFeatureEntryNum(self.handle, pFeatureName.encode('ascii'), byref(pEntryNum))

    # ch:获取枚举属性的可设枚举值列表
    def IMV_FG_GetEnumFeatureEntrys(self, pFeatureName, pEnumEntryList):
        MVSDKdll.IMV_FG_GetEnumFeatureEntrys.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureEntrys.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetEnumFeatureEntrys(IN HANDLE handle, IN const char* pFeatureName, IN_OUT IMV_EnumEntryList* pEnumEntryList);
        return MVSDKdll.IMV_FG_GetEnumFeatureEntrys(self.handle, pFeatureName.encode('ascii'), byref(pEnumEntryList))

    # ch:获取字符串属性值
    def IMV_FG_GetStringFeatureValue(self, pFeatureName, pStringValue):
        MVSDKdll.IMV_FG_GetStringFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetStringFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_GetStringFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT IMV_String* pStringValue);
        return MVSDKdll.IMV_FG_GetStringFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pStringValue))

    # ch:设置字符串属性值
    def IMV_FG_SetStringFeatureValue(self, pFeatureName, pStringValue):
        MVSDKdll.IMV_FG_SetStringFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SetStringFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetStringFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN const char* pStringValue);
        return MVSDKdll.IMV_FG_SetStringFeatureValue(self.handle, pFeatureName.encode('ascii'),
                                                     pStringValue.encode('ascii'))

    # ch:执行命令属性
    def IMV_FG_ExecuteCommandFeature(self, pFeatureName):
        MVSDKdll.IMV_FG_ExecuteCommandFeature.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_ExecuteCommandFeature.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_ExecuteCommandFeature(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_ExecuteCommandFeature(self.handle, pFeatureName.encode('ascii'))

    # ch:像素格式转换
    # 像素格式转换
    # 成功，返回IMV_FG_OK；错误，返回错误码
    # 只支持转化成目标像素格式gvspPixelRGB8 / gvspPixelBGR8 / gvspPixelMono8 /
    # gvspPixelBGRA8
    # 通过该接口将原始图像数据转换成用户所需的像素格式并存放在调用者指定内存中。
    # 像素格式为YUV411Packed的时，图像宽须能被4整除
    # 像素格式为YUV422Packed的时，图像宽须能被2整除
    # 像素格式为YUYVPacked的时，图像宽须能被2整除
    # 转换后的图像: 数据存储是从最上面第一行开始的，这个是相机数据的默认存储方向
    def IMV_FG_PixelConvert(self, pstPixelConvertParam):
        MVSDKdll.IMV_FG_PixelConvert.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_PixelConvert.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_PixelConvert(IN IMV_FG_IF_HANDLE handle, IN_OUT IMV_PixelConvertParam* pstPixelConvertParam);
        return MVSDKdll.IMV_FG_PixelConvert(self.handle, byref(pstPixelConvertParam))

    # ch:图像翻转
    def IMV_FG_FlipImage(self, pstFlipImageParam):
        MVSDKdll.IMV_FG_FlipImage.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FlipImage.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_FlipImage(IN IMV_FG_IF_HANDLE handle, IN_OUT IMV_FlipImageParam* pstFlipImageParam);
        return MVSDKdll.IMV_FG_FlipImage(self.handle, byref(pstFlipImageParam))

    # ch:图像顺时针旋转
    def IMV_FG_RotateImage(self, pstRotateImageParam):
        MVSDKdll.IMV_FG_RotateImage.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_RotateImage.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_RotateImage(IN IMV_FG_IF_HANDLE handle, IN_OUT IMV_RotateImageParam* pstRotateImageParam);
        return MVSDKdll.IMV_FG_RotateImage(self.handle, byref(pstRotateImageParam))

    # ch:消息通道事件回调注册
    # self 采集卡对象
    # proc 设备连接状态事件回调函数
    # pUser用户自定义数据, 可设为None
    def IMV_FG_SubscribeMsgChannelArg(self, proc, pUser):
        MVSDKdll.IMV_FG_SubscribeMsgChannelArg.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SubscribeMsgChannelArg.restype = c_int
        # C原型:IMV_FG_API int IMV_FG_CALL IMV_FG_SubscribeMsgChannelArg(IN IMV_FG_IF_HANDLE hIFDev, IN IMV_FG_MsgChannelCallBack proc, IN void* pUser);
        return MVSDKdll.IMV_FG_SubscribeMsgChannelArg(self.handle, proc, pUser)

    # ch:保存图像
    def IMV_FG_SaveImageToFile(self, pstSaveFileParam):
        MVSDKdll.IMV_FG_SaveImageToFile.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SaveImageToFile.restype = c_int
        # IMV_API int IMV_FG_CALL IMV_FG_SaveImageToFile(IN IMV_FG_IF_HANDLE handle, IN IMV_FG_SaveImageToFileParam * pstSaveFileParam);
        return MVSDKdll.IMV_FG_SaveImageToFile(self.handle, byref(pstSaveFileParam))


class MvCamera():

    def __init__(self):
        self._handle = c_void_p()  # 记录当前连接设备的句柄
        self.handle = pointer(self._handle)  # 创建句柄指针

    # ch:获取SDK版本号 | en:Get SDK Version
    @staticmethod
    def IMV_FG_GetVersion():
        MVSDKdll.IMV_FG_GetVersion.restype = c_char_p
        # C原型：const char* IMV_FG_CALL IMV_FG_GetVersion(void);
        return MVSDKdll.IMV_FG_GetVersion()

    @staticmethod
    def IMV_FG_EnumDevices(nInterfaceType, pDeviceList):
        MVSDKdll.IMV_FG_EnumDevices.argtype = (c_uint, c_void_p)
        MVSDKdll.IMV_FG_EnumDevices.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_EnumDevices(IN unsigned int nInterfaceType, OUT IMV_FG_DEVICE_INFO_LIST* pDeviceList);
        return MVSDKdll.IMV_FG_EnumDevices(c_uint(nInterfaceType), byref(pDeviceList))

    # ：打开设备
    # 成功，返回IMV_FG_OK；错误，返回错误码         IMV_FG_ECreateHandleMode 创建句柄模式  bytes 打开相机标识
    def IMV_FG_OpenDevice(self, mode, pIdentifier):
        MVSDKdll.IMV_FG_OpenDevice.argtype = (c_int, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_OpenDevice.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_OpenDevice(IN IMV_FG_ECreateHandleMode mode, IN void* pIdentifier, OUT IMV_FG_DEV_HANDLE* handle);
        return MVSDKdll.IMV_FG_OpenDevice(c_int(mode), pIdentifier, byref(self.handle))
        # （支持相机属性自动同步到采集卡功能，如宽，高，tap，像素格式

    def IMV_FG_OpenDeviceEx(self, mode, pIdentifier):
        MVSDKdll.IMV_FG_OpenDeviceEx.argtype = (c_int, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_OpenDeviceEx.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_OpenDeviceEx(IN IMV_FG_ECreateHandleMode mode, IN void* pIdentifier, OUT IMV_FG_DEV_HANDLE* handle);
        return MVSDKdll.IMV_FG_OpenDeviceEx(c_int(mode), pIdentifier, byref(self.handle))

    # 判断设备是否已打开
    def IMV_FG_IsDeviceOpen(self):
        MVSDKdll.IMV_FG_IsDeviceOpen.argtype = c_void_p
        MVSDKdll.IMV_FG_IsDeviceOpen.restype = c_bool
        # C原型:int IMV_FG_CALL IMV_FG_IsDeviceOpen(IN IMV_FG_DEV_HANDLE handle);
        return MVSDKdll.IMV_FG_IsDeviceOpen(self.handle)

    # 关闭设备（根据句柄断开设备）
    def IMV_FG_CloseDevice(self):
        MVSDKdll.IMV_FG_CloseDevice.argtype = c_void_p
        MVSDKdll.IMV_FG_CloseDevice.restype = c_int
        # C原型:int IMV_FG_CALL IMV_FG_CloseDevice(IN IMV_FG_DEV_HANDLE handle);
        return MVSDKdll.IMV_FG_CloseDevice(self.handle)

    # ch:下载设备描述XML文件，并保存到指定路径，如：D:/\xml.zip
    def IMV_FG_DownLoadGenICamXML(self, pFullFileName):
        MVSDKdll.IMV_FG_DownLoadGenICamXML.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_DownLoadGenICamXML.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_DownLoadGenICamXML(IN HANDLE handle, IN const char* pFullFileName);
        return MVSDKdll.IMV_FG_DownLoadGenICamXML(self.handle, pFullFileName.encode('ascii'))

    # ch:保存设备配置到指定的位置。同名文件已存在时，覆盖。
    def IMV_FG_SaveDeviceCfg(self, pFullFileName):
        MVSDKdll.IMV_FG_SaveDeviceCfg.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SaveDeviceCfg.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SaveDeviceCfg(IN HANDLE handle, IN const char* pFullFileName);
        return MVSDKdll.IMV_FG_SaveDeviceCfg(self.handle, pFullFileName.encode('ascii'))

    # ch:保存设备配置到指定的位置。同名文件已存在时，覆盖。
    def IMV_FG_LoadDeviceCfg(self, pFullFileName, pErrorList):
        MVSDKdll.IMV_FG_LoadDeviceCfg.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_LoadDeviceCfg.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_LoadDeviceCfg(IN HANDLE handle, IN const char* pFullFileName, OUT IMV_ErrorList* pErrorList);
        return MVSDKdll.IMV_FG_LoadDeviceCfg(self.handle, pFullFileName.encode('ascii'), byref(pErrorList))

        # ch:判断属性是否可用

    def IMV_FG_FeatureIsAvailable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsAvailable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsAvailable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsAvailable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsAvailable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否可读
    def IMV_FG_FeatureIsReadable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsReadable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsReadable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsReadable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsReadable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否可写
    def IMV_FG_FeatureIsWriteable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsWriteable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsWriteable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsWriteable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsWriteable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否可流
    def IMV_FG_FeatureIsStreamable(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsStreamable.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsStreamable.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsStreamable(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsStreamable(self.handle, pFeatureName.encode('ascii'))

    # ch:判断属性是否有效
    def IMV_FG_FeatureIsValid(self, pFeatureName):
        MVSDKdll.IMV_FG_FeatureIsValid.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_FeatureIsValid.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_FeatureIsValid(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_FeatureIsValid(self.handle, pFeatureName.encode('ascii'))

    # ch:获取属性类型
    def IMV_FG_GetFeatureType(self, pFeatureName, pPropertyType):
        MVSDKdll.IMV_FG_GetFeatureType.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetFeatureType.restype = c_bool
        # C原型:IMV_API bool IMV_FG_CALL IMV_FG_GetFeatureType(IN HANDLE handle, IN const char* pFeatureName, OUT IMV_EFeatureType* pPropertyType);
        return MVSDKdll.IMV_FG_GetFeatureType(self.handle, pFeatureName.encode('ascii'), byref(pPropertyType))

    # ch:获取整型属性值
    def IMV_FG_GetIntFeatureValue(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_GetIntFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:获取整型属性可设的最小值
    def IMV_FG_GetIntFeatureMin(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureMin.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureMin.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureMin(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_FG_GetIntFeatureMin(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:获取整型属性可设的最大值
    def IMV_FG_GetIntFeatureMax(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureMax.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureMax.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureMax(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_FG_GetIntFeatureMax(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:获取整型属性步长
    def IMV_FG_GetIntFeatureInc(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_GetIntFeatureInc.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetIntFeatureInc.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetIntFeatureInc(IN HANDLE handle, IN const char* pFeatureName, OUT int64_t* pIntValue);
        return MVSDKdll.IMV_FG_GetIntFeatureInc(self.handle, pFeatureName.encode('ascii'), byref(pIntValue))

    # ch:设置整型属性值
    def IMV_FG_SetIntFeatureValue(self, pFeatureName, pIntValue):
        MVSDKdll.IMV_FG_SetIntFeatureValue.argtype = (c_void_p, c_void_p, c_int64)
        MVSDKdll.IMV_FG_SetIntFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetIntFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN int64_t intValue);
        return MVSDKdll.IMV_FG_SetIntFeatureValue(self.handle, pFeatureName.encode('ascii'), c_int64(pIntValue))

    # ch:获取浮点属性值
    def IMV_FG_GetDoubleFeatureValue(self, pFeatureName, pDoubleValue):
        MVSDKdll.IMV_FG_GetDoubleFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetDoubleFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetDoubleFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT double* pDoubleValue);
        return MVSDKdll.IMV_FG_GetDoubleFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pDoubleValue))

    # ch:获取浮点属性可设的最小值
    def IMV_FG_GetDoubleFeatureMin(self, pFeatureName, pDoubleValue):
        MVSDKdll.IMV_FG_GetDoubleFeatureMin.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetDoubleFeatureMin.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetDoubleFeatureMin(IN HANDLE handle, IN const char* pFeatureName, OUT double* pDoubleValue);
        return MVSDKdll.IMV_FG_GetDoubleFeatureMin(self.handle, pFeatureName.encode('ascii'), byref(pDoubleValue))

    # ch:获取浮点属性可设的最大值
    def IMV_FG_GetDoubleFeatureMax(self, pFeatureName, pDoubleValue):
        MVSDKdll.IMV_FG_GetDoubleFeatureMax.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetDoubleFeatureMax.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetDoubleFeatureMax(IN HANDLE handle, IN const char* pFeatureName, OUT double* pDoubleValue);
        return MVSDKdll.IMV_FG_GetDoubleFeatureMax(self.handle, pFeatureName.encode('ascii'), byref(pDoubleValue))

    # ch:设置浮点属性值
    def IMV_FG_SetDoubleFeatureValue(self, pFeatureName, doubleValue):
        MVSDKdll.IMV_FG_SetDoubleFeatureValue.argtype = (c_void_p, c_void_p, c_double)
        MVSDKdll.IMV_FG_SetDoubleFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetDoubleFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN double doubleValue);
        return MVSDKdll.IMV_FG_SetDoubleFeatureValue(self.handle, pFeatureName.encode('ascii'), c_double(doubleValue))

    # ch:获取布尔属性值
    def IMV_FG_GetBoolFeatureValue(self, pFeatureName, pBoolValue):
        MVSDKdll.IMV_FG_GetBoolFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetBoolFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetBoolFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT bool* pBoolValue);
        return MVSDKdll.IMV_FG_GetBoolFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pBoolValue))

    # ch:设置布尔属性值
    def IMV_FG_SetBoolFeatureValue(self, pFeatureName, boolValue):
        MVSDKdll.IMV_FG_SetBoolFeatureValue.argtype = (c_void_p, c_void_p, c_bool)
        MVSDKdll.IMV_FG_SetBoolFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetBoolFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN bool boolValue);
        return MVSDKdll.IMV_FG_SetBoolFeatureValue(self.handle, pFeatureName.encode('ascii'), c_bool(boolValue))

    # ch:获取枚举属性值
    def IMV_FG_GetEnumFeatureValue(self, pFeatureName, pEnumValue):
        MVSDKdll.IMV_FG_GetEnumFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_etEnumFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT uint64_t* pEnumValue);
        return MVSDKdll.IMV_FG_GetEnumFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pEnumValue))

    # ch:设置枚举属性值
    def IMV_FG_SetEnumFeatureValue(self, pFeatureName, enumValue):
        MVSDKdll.IMV_FG_SetEnumFeatureValue.argtype = (c_void_p, c_void_p, c_uint64)
        MVSDKdll.IMV_FG_SetEnumFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetEnumFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN uint64_t enumValue);
        return MVSDKdll.IMV_FG_SetEnumFeatureValue(self.handle, pFeatureName.encode('ascii'), enumValue)

    # ch:获取枚举属性symbol值
    def IMV_FG_GetEnumFeatureSymbol(self, pFeatureName, pEnumSymbol):
        MVSDKdll.IMV_FG_GetEnumFeatureSymbol.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureSymbol.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetEnumFeatureSymbol(IN HANDLE handle, IN const char* pFeatureName, OUT IMV_String* pEnumSymbol);
        return MVSDKdll.IMV_FG_GetEnumFeatureSymbol(self.handle, pFeatureName.encode('ascii'), byref(pEnumSymbol))

    # ch:设置枚举属性symbol值
    def IMV_FG_SetEnumFeatureSymbol(self, pFeatureName, pEnumSymbol):
        MVSDKdll.IMV_FG_SetEnumFeatureSymbol.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SetEnumFeatureSymbol.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetEnumFeatureSymbol(IN HANDLE handle, IN const char* pFeatureName, IN const char* pEnumSymbol);
        return MVSDKdll.IMV_FG_SetEnumFeatureSymbol(self.handle, pFeatureName.encode('ascii'),
                                                    pEnumSymbol.encode('ascii'))

    # ch:获取枚举属性的可设枚举值的个数
    def IMV_FG_GetEnumFeatureEntryNum(self, pFeatureName, pEntryNum):
        MVSDKdll.IMV_FG_GetEnumFeatureEntryNum.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureEntryNum.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetEnumFeatureEntryNum(IN HANDLE handle, IN const char* pFeatureName, OUT unsigned int* pEntryNum);
        return MVSDKdll.IMV_FG_GetEnumFeatureEntryNum(self.handle, pFeatureName.encode('ascii'), byref(pEntryNum))

    # ch:获取枚举属性的可设枚举值列表
    def IMV_FG_GetEnumFeatureEntrys(self, pFeatureName, pEnumEntryList):
        MVSDKdll.IMV_FG_GetEnumFeatureEntrys.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetEnumFeatureEntrys.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_GetEnumFeatureEntrys(IN HANDLE handle, IN const char* pFeatureName, IN_OUT IMV_EnumEntryList* pEnumEntryList);
        return MVSDKdll.IMV_FG_GetEnumFeatureEntrys(self.handle, pFeatureName.encode('ascii'), byref(pEnumEntryList))

    # ch:获取字符串属性值
    def IMV_FG_GetStringFeatureValue(self, pFeatureName, pStringValue):
        MVSDKdll.IMV_FG_GetStringFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_GetStringFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_GetStringFeatureValue(IN HANDLE handle, IN const char* pFeatureName, OUT IMV_String* pStringValue);
        return MVSDKdll.IMV_FG_GetStringFeatureValue(self.handle, pFeatureName.encode('ascii'), byref(pStringValue))

    # ch:设置字符串属性值
    def IMV_FG_SetStringFeatureValue(self, pFeatureName, pStringValue):
        MVSDKdll.IMV_FG_SetStringFeatureValue.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SetStringFeatureValue.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SetStringFeatureValue(IN HANDLE handle, IN const char* pFeatureName, IN const char* pStringValue);
        return MVSDKdll.IMV_FG_SetStringFeatureValue(self.handle, pFeatureName.encode('ascii'),
                                                     pStringValue.encode('ascii'))

    # ch:执行命令属性
    def IMV_FG_ExecuteCommandFeature(self, pFeatureName):
        MVSDKdll.IMV_FG_ExecuteCommandFeature.argtype = (c_void_p, c_void_p)
        MVSDKdll.IMV_FG_ExecuteCommandFeature.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_ExecuteCommandFeature(IN HANDLE handle, IN const char* pFeatureName);
        return MVSDKdll.IMV_FG_ExecuteCommandFeature(self.handle, pFeatureName.encode('ascii'))

    # ch:设备连接状态事件回调注册
    def IMV_FG_SubscribeConnectArg(self, proc, pUser):
        MVSDKdll.IMV_FG_SubscribeConnectArg.argtype = (c_void_p, c_void_p, c_void_p)
        MVSDKdll.IMV_FG_SubscribeConnectArg.restype = c_int
        # C原型:IMV_API int IMV_FG_CALL IMV_FG_SubscribeConnectArg(IN IMV_FG_DEV_HANDLE handle, IN IMV_ConnectCallBack proc, IN void* pUser);
        return MVSDKdll.IMV_FG_SubscribeConnectArg(self.handle, proc, pUser)



def displayDeviceInfo(interfaceList,deviceInfoList):
    print("Idx  Type   Vendor              Model           S/N                 DeviceUserID    IP Address")
    print("------------------------------------------------------------------------------------------------")
    for index in range(0,interfaceList.nInterfaceNum):
        interfaceInfo = interfaceList.pInterfaceInfoList[index]
        strType = ""
        strVendorName = ""
        strModeName = ""
        serialNumber = ""
        interfaceName = ""
        for str in interfaceInfo.vendorName:
            strVendorName = strVendorName + chr(str)
        for str in interfaceInfo.modelName:
            strModeName = strModeName + chr(str)
        for str in interfaceInfo.serialNumber:
            serialNumber = serialNumber + chr(str)
        for str in interfaceInfo.interfaceName:
            interfaceName = interfaceName + chr(str)
        if interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeGigEInterface:
            strType = "Gige Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeU3vInterface:
            strType = "U3V Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeCLInterface:
            strType = "CL Card"
        elif interfaceInfo.nInterfaceType == IMV_FG_EInterfaceType.typeCXPInterface:
            strType = "CXP Card"
        print("[%d]  %s   %s    %s        %s            %s " % (
            index+1, strType, strVendorName, strModeName, serialNumber, interfaceName))

        for i in range(0, deviceInfoList.nDevNum):
            pDeviceInfo = deviceInfoList.pDeviceInfoList[i]
            if pDeviceInfo.FGInterfaceInfo.interfaceKey == interfaceInfo.interfaceKey:
                strType = ""
                strVendorName = ""
                strModeName = ""
                strSerialNumber = ""
                strCameraname = ""
                strIpAdress = ""
                for str in pDeviceInfo.vendorName:
                    strVendorName = strVendorName + chr(str)
                for str in pDeviceInfo.modelName:
                    strModeName = strModeName + chr(str)
                for str in pDeviceInfo.serialNumber:
                    strSerialNumber = strSerialNumber + chr(str)
                for str in pDeviceInfo.cameraName:
                    strCameraname = strCameraname + chr(str)
                if pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_GIGE_DEVICE:
                    strType = "Gige"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_U3V_DEVICE:
                    strType = "U3V"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_CL_DEVICE:
                    strType = "CL"
                elif pDeviceInfo.nDeviceType == IMV_FG_EDeviceType.IMV_FG_TYPE_CXP_DEVICE:
                    strType = "CXP"
                print("  |-%d  %s   %s    %s      %s     %s           %s" % (
                 int(i)+1,  strType, strVendorName, strModeName, strSerialNumber, strCameraname, strIpAdress))
    return
