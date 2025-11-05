from pylogix import PLC
import time


class CIP_Client():
    def __init__(self, ip_addr='127.0.0.1', Port=44818, retry=3):
        self.plc_client = None
        self.ip_addr = ip_addr
        self.Port = Port
        self.retry_time = retry
        self._connect()

    def _connect(self):
        while self.retry_time > 0:
            try:
                self.plc_client = PLC(self.ip_addr, self.Port)
                ret = self.plc_client.Discover()
                if ret.Status == 'Success':
                    print(f"成功连接PLC {self.ip_addr}")
                    return True
                else:
                    print(ret.Status, 'Failed connected')
                    self.retry_time -= 1
                    time.sleep(0.05)
            except Exception as e:
                print(str(e))
                self.retry_time -= 1
                time.sleep(0.5)
        return False

    def Read(self, addr, nb, retry=3):
        ret = False
        while retry > 0:
            try:
                ret = self.plc_client.Read(addr, count=nb)
                return ret
            except Exception as e:
                print(str(e))
                retry -= 1
                time.sleep(0.05)
        return ret

    def Write(self, addr, values, retry=3):
        ret = False
        while retry > 0:
            try:
                ret = self.plc_client.Write(addr, value=values)
                return ret
            except Exception as e:
                print(str(e))
                retry -= 1
                time.sleep(0.02)
        return ret

    def disconnect(self):
        if self.plc_client is not None:
            try:
                self.plc_client.Close()
            except:
                pass
            finally:
                self.plc_client = None

    def __del__(self):
        self.disconnect()
