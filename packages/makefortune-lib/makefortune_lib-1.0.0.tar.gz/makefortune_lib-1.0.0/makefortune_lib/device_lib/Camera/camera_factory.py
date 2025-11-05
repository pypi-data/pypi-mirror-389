from .Keyence import Keyence3dLineScan
from .HIKVISION import Hik2dLineScan, Hik2dAreaScan
from .OPT import Opt2dAreaScan


def get_camera_instance(Camera_type, *args, **kwargs):
    Camera_type_dict = {
        "Keyence3dLineScan": Keyence3dLineScan,
        "Hik2dLineScan": Hik2dLineScan,
        'Hik2dAreaScan': Hik2dAreaScan,
        'Opt2dAreaScan': Opt2dAreaScan
    }
    assert Camera_type in Camera_type_dict.keys(), f'not find Camera type! only apply {Camera_type_dict.keys()}'
    return Camera_type_dict.get(Camera_type)(*args, **kwargs)
