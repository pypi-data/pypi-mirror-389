from ..base import VisionCameraBase

class Opt2dAreaScan(VisionCameraBase):

    def __init__(self, sns='', configuration=''):  # 序列号，配置文件
        super().__init__()
        self.sns = sns
        self.config = configuration
        self._connect()

    def _connect(self):
        pass

    def capture(self, expose_time, timeout=-1):
        print('采集', expose_time, timeout)
        pass
    def reconnect(self):
        pass
    def stop(self):
        pass
    def close(self):
        pass
    def get_infos(self):
        pass
    def get_status(self):
        pass


if __name__ == '__main__':
    o = Opt2dAreaScan(sns='dfas', configuration='dfasdf.file')
    o.capture(5000)
