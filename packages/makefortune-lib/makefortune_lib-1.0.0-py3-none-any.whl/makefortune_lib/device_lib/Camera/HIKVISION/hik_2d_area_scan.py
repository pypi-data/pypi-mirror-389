
from ..base import VisionCameraBase

class Hik2dAreaScan(VisionCameraBase):

    def __init__(self):
        super().__init__()

    def _connect(self):
        pass

    def reconnect(self):
        print(111)

    def stop(self):
        pass

    def get_infos(self):
        pass

    def get_status(self):
        pass

if __name__ == '__main__':
    a = Hik2dAreaScan()
