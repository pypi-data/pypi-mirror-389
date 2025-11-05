from abc import ABC, abstractmethod


class VisionCameraBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def _connect(self):
        pass

    @abstractmethod
    def capture(self,**kwargs):
        pass

    @abstractmethod
    def reconnect(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_infos(self):
        pass

    @abstractmethod
    def get_status(self):
        pass
