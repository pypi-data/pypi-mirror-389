import serial
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
import time


class ModbusRTU_Client:
    def __init__(self, Port='COM3', baudrate=9600, bytesize=8, parity='E', stopbits=1, timeout=5, retry=3):
        self.plc_client = None
        self.Port = Port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.retry_time = retry
        self._connect()

    def _connect(self):
        while self.retry_time > 0:
            try:
                self.plc_client = modbus_rtu.RtuMaster(
                    serial.Serial(port=self.Port, baudrate=self.baudrate, bytesize=self.bytesize,
                                  parity=self.parity, stopbits=self.stopbits, xonxoff=0)
                )
                self.plc_client.set_timeout(self.timeout)
                self.plc_client.set_verbose(True)
                return
            except Exception as e:
                print(str(e))
                self.retry_time -= 1
                time.sleep(0.05)

    def Read(self, addr, nb, registerType='保持寄存器', floatRWtype='ABCD', strRWtype='AB', retry=3):
        ret = False
        while retry > 0:
            try:
                assert registerType in ['保持寄存器', '线圈', '离散量', '输入寄存器'], '无效的寄存器类型'
                if registerType == '保持寄存器':
                    ret = self.plc_client.execute(1, cst.READ_HOLDING_REGISTERS, addr, nb)
                elif registerType == '线圈':
                    ret = self.plc_client.execute(1, cst.READ_COILS, addr, nb)
                elif registerType == '离散量':
                    ret = self.plc_client.execute(1, cst.READ_DISCRETE_INPUTS, addr, nb)
                elif registerType == '输入寄存器':
                    ret = self.plc_client.execute(1, cst.READ_INPUT_REGISTERS, addr, nb)
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
                    ret = self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, addr, output_value=values)
                elif registerType == '线圈':
                    ret = self.plc_client.execute(1, cst.WRITE_MULTIPLE_COILS, addr, output_value=values)
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
