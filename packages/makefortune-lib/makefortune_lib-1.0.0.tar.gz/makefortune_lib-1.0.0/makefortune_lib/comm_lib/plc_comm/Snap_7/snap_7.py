"""
pip install python-snap7
"""
import snap7
from snap7.exceptions import Snap7Exception
import time
from typing import Union, List, Optional


class S7_Client:
    # 默认型号配置映射 {plc_type: (rack, slot)}
    _PLC_TYPE_MAP = {
        's7_1200': (0, 1),
        's7_1500': (0, 2),
        's7_300': (0, 2),
        's7_400': (0, 3),
        'cpu1214c': (0, 1),
        'cpu1512c': (0, 2),
        'cpu315': (0, 2),
        'cpu414': (0, 3),
    }

    def __init__(self,
                 ip_addr: str = '127.0.0.1',
                 plc_type: Optional[str] = None,
                 rack: Optional[int] = None,
                 slot: Optional[int] = None,
                 port: int = 102,
                 retry: int = 3):
        """
        初始化 S7 客户端（支持通过 plc_type 自动设置 rack/slot）
        :param ip_addr: PLC 的 IP 地址
        :param plc_type: PLC 型号，如 's7_1200', 's7_1500'（不区分大小写）
        :param rack: 机架号（若提供则优先使用）
        :param slot: 插槽号（若提供则优先使用）
        :param port: S7 通信端口，默认 102
        :param retry: 连接重试次数
        """
        self.ip_addr = ip_addr
        self.port = port
        self.retry_time = retry
        self.plc_client = None
        # 解析 rack 和 slot
        self.rack, self.slot = self._get_rack_slot(plc_type, rack, slot)

        # 尝试连接
        self._connect()

    def _get_rack_slot(self, plc_type: Optional[str], rack: Optional[int], slot: Optional[int]) -> tuple:
        """根据 plc_type 或手动参数确定 rack 和 slot"""
        if rack is not None and slot is not None:
            print(f"Using manual rack={rack}, slot={slot}")
            return rack, slot

        if plc_type is None:
            raise ValueError("Either 'plc_type' or both 'rack' and 'slot' must be provided.")

        plc_key = plc_type.lower().strip()
        if plc_key not in self._PLC_TYPE_MAP:
            valid_types = list(self._PLC_TYPE_MAP.keys())
            raise ValueError(f"Unknown plc_type: '{plc_type}'. "
                             f"Valid types: {valid_types}")

        rack, slot = self._PLC_TYPE_MAP[plc_key]
        print(f"Auto-configured for {plc_type.upper()}: Rack={rack}, Slot={slot}")
        return rack, slot

    def _connect(self):
        """内部连接方法，带自动重试"""
        self.plc_client = snap7.client.Client()
        for attempt in range(self.retry_time):
            try:
                self.plc_client.connect(self.ip_addr, self.rack, self.slot, self.port)
                if self.plc_client.get_connected():
                    print(f"✅ Connected to {self.ip_addr}:{self.port} | Rack={self.rack}, Slot={self.slot}")
                    return
            except Snap7Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Unexpected error during connection: {e}")
                time.sleep(0.5)

        print(f"❌ Failed to connect after {self.retry_time} retries. Check IP, network, or PLC settings.")
        self.plc_client = None

    def is_connected(self) -> bool:
        """检查是否连接成功"""
        if self.plc_client is None:
            return False
        try:
            return self.plc_client.get_connected()
        except:
            return False

    def Read(self,
             area: str = 'DB',
             db_number: int = 0,
             start: int = 0,
             size: int = 1,
             dtype: str = 'byte',
             retry: int = 3):
        """
        读取 PLC 数据
        :param area: 区域类型 ['DB', 'I', 'Q', 'M', 'PI', 'PQ']
        :param db_number: DB编号（仅用于DB区）
        :param start: 起始字节地址
        :param size: 要读取的字节数
        :param dtype: 数据类型 ['byte', 'int', 'dint', 'real', 'bool', 'string', 'word', 'dword']
        :param retry: 重试次数
        :return: 解析后的值或原始字节列表，失败返回 None
        """
        if not self.is_connected():
            print("Not connected to PLC. Cannot read.")
            return None

        AREA_MAP = {
            'DB': snap7.types.Areas.DB,
            'I': snap7.types.Areas.PE,  # Input
            'Q': snap7.types.Areas.PA,  # Output
            'M': snap7.types.Areas.MK,  # Memory
            'PI': snap7.types.Areas.PE,  # Peripheral Input
            'PQ': snap7.types.Areas.PA,  # Peripheral Output
        }

        if area not in AREA_MAP:
            print(f"Invalid area: {area}. Choose from {list(AREA_MAP.keys())}")
            return None

        area_code = AREA_MAP[area]

        for attempt in range(retry):
            try:
                if area == 'DB':
                    data = self.plc_client.db_read(db_number, start, size)
                elif area in ['I', 'Q', 'M', 'PI', 'PQ']:
                    data = self.plc_client.read_area(area_code, db_number, start, size)
                else:
                    print(f"Unsupported area: {area}")
                    return None

                return self._parse_data(data, dtype, start=start, size=size)

            except Snap7Exception as e:
                print(f"Read failed (attempt {attempt + 1}): {e}")
                time.sleep(0.02)
            except Exception as e:
                print(f"Unexpected error during read: {e}")
                break

        return None

    def Write(self,
              area: str,
              db_number: int = 0,
              start: int = 0,
              values: Union[int, float, bool, List[int], bytes] = 0,
              dtype: str = 'byte',
              retry: int = 3):
        """
        写入数据到PLC
        :param area: 同 read
        :param db_number: DB编号
        :param start: 起始地址
        :param values: 要写入的值
        :param dtype: 数据类型
        :param retry: 重试次数
        :return: 成功返回 True，否则 False
        """
        if not self.is_connected():
            print("Not connected to PLC. Cannot write.")
            return False

        AREA_MAP = {
            'DB': snap7.types.Areas.DB,
            'I': snap7.types.Areas.PE,
            'Q': snap7.types.Areas.PA,
            'M': snap7.types.Areas.MK,
            'PI': snap7.types.Areas.PE,
            'PQ': snap7.types.Areas.PA,
        }

        if area not in AREA_MAP:
            print(f"Invalid area: {area}")
            return False

        area_code = AREA_MAP[area]

        try:
            data = self._serialize_data(values, dtype)
        except Exception as e:
            print(f"Failed to serialize data: {e}")
            return False
        for attempt in range(retry):
            try:
                if area == 'DB':
                    self.plc_client.db_write(db_number, start, data)
                else:
                    self.plc_client.write_area(area_code, db_number, start, data)
                print(f"✅ Write success: {dtype} → {area}{db_number}[{start}]")
                return True
            except Snap7Exception as e:
                print(f"Write failed (attempt {attempt + 1}): {e}")
                time.sleep(0.02)
            except Exception as e:
                print(f"Unexpected error during write: {e}")
                break
        return False

    def read_bool(self, area: str, db_number: int, byte_offset: int, bit_offset: int) -> bool:
        """读取单个位，例如 M10.3"""
        try:
            data = self.Read(area, db_number, byte_offset, 1, 'byte')
            return bool(data[0] & (1 << bit_offset)) if data else False
        except:
            return False

    def write_bool(self, area: str, db_number: int, byte_offset: int, bit_offset: int, value: bool) -> bool:
        """写入单个位"""
        try:
            current = self.Read(area, db_number, byte_offset, 1, 'byte')
            if not current:
                return False
            byte_val = current[0]
            mask = 1 << bit_offset
            byte_val = (byte_val | mask) if value else (byte_val & ~mask)
            return self.Write(area, db_number, byte_offset, byte_val, 'byte')
        except Exception as e:
            print(f"Write bool failed: {e}")
            return False

    def get_cpu_info(self) -> dict or None:
        """获取CPU信息（型号、序列号等）"""
        if not self.is_connected():
            return None
        try:
            info = self.plc_client.get_cpu_info()
            return {
                "Module": info.ModuleTypeName.strip(),
                "Serial": info.SerialNumber.strip(),
                "Copyright": info.Copyright.strip(),
                "Name": info.ModuleName.strip()
            }
        except Exception as e:
            print(f"Get CPU info failed: {e}")
            return None

    def _parse_data(self, data: bytes, dtype: str, start: int = 0, size: int = 1):
        import struct
        if isinstance(data, list):
            data = bytes(data)

        if dtype == 'byte':
            return list(data)
        elif dtype == 'bool':
            return bool(data[0] & 1) if len(data) > 0 else False
        elif dtype == 'int':
            return struct.unpack(">h", data[:2])[0]
        elif dtype == 'dint':
            return struct.unpack(">i", data[:4])[0]
        elif dtype == 'real':
            return struct.unpack(">f", data[:4])[0]
        elif dtype == 'word':
            return struct.unpack(">H", data[:2])[0]
        elif dtype == 'dword':
            return struct.unpack(">I", data[:4])[0]
        elif dtype == 'string':
            if len(data) < 2:
                return ""
            actual_len = data[0]
            max_len = data[1]
            text = data[2:2 + min(actual_len, max_len)].decode('ascii', errors='ignore')
            return text
        else:
            print(f"Unsupported dtype: {dtype}")
            return None

    def _serialize_data(self, value, dtype: str) -> bytes:
        import struct
        if dtype == 'byte':
            if isinstance(value, int):
                return bytes([value])
            elif isinstance(value, (list, tuple)):
                return bytes(value)
            elif isinstance(value, bytes):
                return value
        elif dtype == 'int':
            return struct.pack(">h", int(value))
        elif dtype == 'dint':
            return struct.pack(">i", int(value))
        elif dtype == 'real':
            return struct.pack(">f", float(value))
        elif dtype == 'bool':
            return b'\x01' if value else b'\x00'
        elif dtype == 'word':
            return struct.pack(">H", int(value))
        elif dtype == 'dword':
            return struct.pack(">I", int(value))
        elif dtype == 'string':
            if isinstance(value, str):
                value = value.encode('ascii', errors='ignore')[:254]
                return bytes([len(value), 254]) + value.ljust(254, b'\x00')
            else:
                raise ValueError("String must be str type")
        else:
            raise ValueError(f"Unsupported dtype: {dtype}")

    def disconnect(self):
        """断开连接"""
        if self.plc_client is not None:
            try:
                self.plc_client.disconnect()
                print("🔌 Disconnected from PLC.")
            except Exception as e:
                print(f"Error during disconnect: {e}")
            finally:
                self.plc_client = None

    def __del__(self):
        self.disconnect()


if __name__ == "__main__":
    # 示例1：使用型号自动配置（推荐）
    plc = S7_Client(ip_addr="192.168.0.10", plc_type="s7_1500")

    # 示例2：也支持别名
    # plc = S7Client(ip_addr="192.168.0.11", plc_type="cpu1214c")

    if not plc.is_connected():
        print("❌ Unable to connect to PLC.")
    else:
        print("\n📊 CPU Info:")
        info = plc.get_cpu_info()
        if info:
            for k, v in info.items():
                print(f"  {k}: {v}")

        print("\n🔍 Reading Data:")
        # 读 DB100.0 REAL
        real_val = plc.Read('DB', 100, 0, 4, 'real')
        print("DB100.0 (REAL):", real_val)

        # 读 M10.3
        m10_3 = plc.read_bool('M', 0, 10, 3)
        print("M10.3:", m10_3)

        # 写 DB100.4 INT
        plc.Write('DB', 100, 4, 999, 'int')

        # 写 M20.0
        plc.write_bool('M', 0, 20, 0, True)

    # 自动断开
