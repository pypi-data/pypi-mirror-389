from pymelsec import Type3E, Type4E
import time


class Melsec_Client:
    def __init__(self,
                 ip_addr='127.0.0.1',
                 Port: int = 5007,
                 protocol: str = '3E',
                 retry: int = 3):

        self.plc_client = None
        self.ip = ip_addr
        self.protocol = protocol.upper()
        self.retry_time = retry
        self.port = Port
        self._connect()

    def _connect(self):
        while self.retry_time > 0:
            try:
                if self.protocol == '3E':
                    self.plc_client = Type3E(
                        host=self.ip,
                        port=self.port,
                    )
                elif self.protocol == '4E':
                    self.plc_client = Type4E(
                        host=self.ip,
                        port=self.port,
                    )
                else:
                    raise ValueError("protocol must be '3E' or '4E'")
                self.plc_client.connect(self.ip, self.port)
                if self.plc_client._is_connected:
                    print('connect success')
                else:
                    self.retry_time -= 1
                    time.sleep(0.05)
            except Exception as e:
                print(f"❌ Connect failed: {e}")
                self.retry_time -= 1
                time.sleep(0.05)
        print(f"❌ Connect failed")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.plc_client._is_connected

    def Read(self, addr, nb: int = 1, data_type: str = 'b'):
        '''
        if data_type == 'BIT' or data_type == 'b':
            return 'b'
        elif data_type == 'SWORD' or data_type == 'h':
            return 'h'
        elif data_type == 'UWORD'or data_type == 'H':
            return 'H'
        elif data_type == 'SDWORD'or data_type == 'i':
            return 'i'
        elif data_type == 'UDWORD'or data_type == 'I':
            return 'I'
        elif data_type == 'FLOAT'or data_type == 'f':
            return 'f'
        elif data_type == 'DOUBLE'or data_type == 'd':
            return 'd'
        elif data_type == 'SLWORD'or data_type == 'q':
            return 'q'
        elif data_type == 'ULWORD'or data_type == 'Q':
            return 'Q'
        '''

        # e.g  response = self.batch_read(ref_device="SD203", read_size=1, data_type=const.DT.UWORD)[0].value
        response = self.plc_client.batch_read(ref_device=addr, read_size=nb, data_type=data_type)
        print(response)
        ret = [r.value for r in response]
        return ret

    def Write(self, addr, value: list, data_type: str = 'b'):
        """
        if data_type == 'BIT' or data_type == 'b':
            return 'b'
        elif data_type == 'SWORD' or data_type == 'h':
            return 'h'
        elif data_type == 'UWORD'or data_type == 'H':
            return 'H'
        elif data_type == 'SDWORD'or data_type == 'i':
            return 'i'
        elif data_type == 'UDWORD'or data_type == 'I':
            return 'I'
        elif data_type == 'FLOAT'or data_type == 'f':
            return 'f'
        elif data_type == 'DOUBLE'or data_type == 'd':
            return 'd'
        elif data_type == 'SLWORD'or data_type == 'q':
            return 'q'
        elif data_type == 'ULWORD'or data_type == 'Q':
            return 'Q'
        """
        # e.g self.batch_write(ref_device="SM213", values=[1], data_type=const.DT.BIT)
        self.plc_client.batch_write(ref_device=addr, values=value, data_type=data_type)

    def disconnect(self):
        if self.plc_client is not None:
            try:
                self.plc_client.close()
            except:
                pass
            finally:
                self.plc_client = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


if __name__ == "__main__":
    pass
