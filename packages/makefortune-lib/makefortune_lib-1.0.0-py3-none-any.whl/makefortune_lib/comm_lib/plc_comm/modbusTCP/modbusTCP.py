from pyModbusTCP.client import ModbusClient
import time

"""通过心跳监听连接状态"""


class ModbusTCP_Client():
    def __init__(self, ip_addr='0.0.0.0', Port=502, retry=3):
        self.plc_client = None
        self.ip_addr = ip_addr
        self.Port = Port
        self.retry_time = retry
        self._connect()

    def _connect(self):
        while self.retry_time > 0:
            try:
                client = ModbusClient()
                client.port(self.Port)
                if not client.host(self.ip_addr):
                    raise Exception(f'client.host({self.ip_addr}) error!!!')
                else:
                    print('Connect PLC TCP success！')
                client.open()
                self.plc_client = client
                return
            except Exception as e:
                self.retry_time -= 1
                time.sleep(0.5)

    def Read(self, addr, nb, registerType='保持寄存器', floatRWtype='ABCD', strRWtype='AB', retry=3):
        ret = False
        while retry > 0:
            try:
                assert registerType in ['保持寄存器', '线圈', '离散量', '输入寄存器'], '无效的寄存器类型'
                if registerType == '保持寄存器':
                    ret = self.plc_client.read_holding_registers(addr, nb)
                elif registerType == '线圈':
                    ret = self.plc_client.read_coils(addr, nb)
                elif registerType == '离散量':
                    ret = self.plc_client.read_discrete_inputs(addr, nb)
                elif registerType == '输入寄存器':
                    ret = self.plc_client.read_input_registers(addr, nb)
                return ret

            except Exception as e:
                print(str(e))
                retry -= 1
                time.sleep(0.02)
        return ret

    def Write(self, addr, values, registerType='保持寄存器', floatRWtype='ABCD', strRWtype='AB', retry=3):
        ret = False
        while retry > 0:
            try:
                assert registerType in ['保持寄存器', '线圈'], '无效的寄存器类型'
                if registerType == '保持寄存器':
                    ret = self.plc_client.write_multiple_registers(addr, values)
                elif registerType == '线圈':
                    ret = self.plc_client.write_multiple_coils(addr, values)
                return ret

            except Exception as e:
                print(str(e))
                retry -= 1
                time.sleep(0.02)
        return ret

    def disconnect(self):
        if self.plc_client is not None:
            try:
                self.plc_client.close()
            except:
                pass
            finally:
                self.plc_client = None

    def __del__(self):
        self.disconnect()
