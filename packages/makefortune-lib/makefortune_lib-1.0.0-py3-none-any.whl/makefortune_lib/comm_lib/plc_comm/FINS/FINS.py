from fins.udp import UDPFinsConnection
from fins.tcp import TCPFinsConnection
from fins.usb import USBFinsConnection
import time


class FINS_Client():
    def __init__(self, ip_addr='192.168.2.22', Port=9600, protocol='UDP'):
        self.plc_client = None
        self.ip_addr = ip_addr
        self.Port = Port
        self.protocol = protocol
        if self.protocol not in ['UDP', 'TCP', 'USB']:
            raise ValueError("protocol 必须是 'UDP' 或 'TCP' 或 'USB'")
        ret = self._connect()
        if not ret:
            raise ConnectionError('FINS CONNECT ERROR')

    def _connect(self):
        try:
            if self.protocol == 'UDP':
                self.plc_client = UDPFinsConnection()
                self.plc_client.connect(self.ip_addr, self.Port)
            elif self.protocol == 'TCP':
                self.plc_client = TCPFinsConnection()
                self.plc_client.connect(self.ip_addr, self.Port)
            elif self.protocol == 'USB':
                self.plc_client = USBFinsConnection()
        except:
            return False
        # 尝试获取节点地址以测试通信
        # self.plc_client.fins_socket.recv(1024)
        # print(f"[FINS] 连接成功: {self.protocol}://{self.ip_addr}:{self.Port}")
        return True

    def Read(self, addr, nb=1, data_type='i', memory_area='d', retry=3):
        """
        data_type Should Specify How to Interpret Data:
            b     : BOOL (bit)
            ui    : UINT (1-word unsigned int)
            udi   : UDINT (2-word unsigned int)
            uli   : ULINT (4-word unsigned int)
            i     : INT (1-word signed int)
            di    : DINT (2-word signed int)
            li    : LINT (4-word signed int)
            uibcd : UINT BCD (1-word)
            udbcd : UDINT BCD (2-word)
            ulbcd : ULINT BCD (4-word)
            r     : REAL (IEEE 754, 2-word float)
            lr    : LREAL (IEEE 754 double, 4-word)
            w     : WORD (hex string, 1-word)
            dw    : DWORD (hex string, 2-word)
            lw    : LWORD (hex string, 4-word)
            str   : STRING (OMRON 格式: 第一字节为长度，后续为字符)
            tim   : TIMER 当前值 (作为 UINT 读取)
            cnt   : COUNTER 当前值 (作为 UINT 读取)
        Memory Areas:
            w : WORK area (WR)
            c : CIO area
            d : Data Memory (DM)
            h : Holding Relay (HR)
        """
        ret = False
        while retry > 0:
            try:
                ret = self.plc_client.read(memory_area, addr,
                                           data_type=data_type, number_of_values=nb)
                return [ret] if isinstance(ret, int) else ret
            except:
                retry -= 1
                time.sleep(0.5)
        return ret

    def Write(self, addr, value, data_type='i', memory_area='d', retry=3) -> bool:
        """
        data_type Should Specify How to Interpret Data:
            b     : BOOL (bit)
            ui    : UINT (1-word unsigned int)
            udi   : UDINT (2-word unsigned int)
            uli   : ULINT (4-word unsigned int)
            i     : INT (1-word signed int)
            di    : DINT (2-word signed int)
            li    : LINT (4-word signed int)
            uibcd : UINT BCD (1-word)
            udbcd : UDINT BCD (2-word)
            ulbcd : ULINT BCD (4-word)
            r     : REAL (IEEE 754, 2-word float)
            lr    : LREAL (IEEE 754 double, 4-word)
            w     : WORD (hex string, 1-word)
            dw    : DWORD (hex string, 2-word)
            lw    : LWORD (hex string, 4-word)
            str   : STRING (OMRON 格式: 第一字节为长度，后续为字符)
            tim   : TIMER 当前值 (作为 UINT 读取)
            cnt   : COUNTER 当前值 (作为 UINT 读取)
        Memory Areas:
            w : WORK area (WR)
            c : CIO area
            d : Data Memory (DM)
            h : Holding Relay (HR)
        """
        ret = False
        while retry > 0:
            try:
                if len(value) == 1:
                    ret = self.plc_client.write(value[0], memory_area=memory_area, word_address=addr,
                                                data_type=data_type)
                else:
                    ret = self.plc_client.write(value, memory_area=memory_area, word_address=addr,
                                                data_type=data_type)
                return ret
            except Exception as e:
                retry -= 1
                time.sleep(0.5)
        return ret

    def reconnect(self):
        self.disconnect()
        self._connect()

    def disconnect(self):
        """断开连接"""
        if self.plc_client:
            try:
                self.plc_client.disconnect()
            except Exception as e:
                pass
            finally:
                self.plc_client = None

    def __del__(self):
        self.disconnect()


if __name__ == '__main__':
    plc = FINS_Client(ip_addr='192.168.14.100', protocol='TCP')

    a = plc.Read(187, 1)
    print(a)
    plc.Write(187, [2])
    print(plc.Read(187, 1))
