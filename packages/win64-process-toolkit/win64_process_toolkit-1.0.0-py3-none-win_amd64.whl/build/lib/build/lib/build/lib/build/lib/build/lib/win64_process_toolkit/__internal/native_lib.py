import os
from ctypes import CDLL, c_wchar_p, c_uint32, c_bool, c_size_t


def __get_native_lib() -> CDLL:
    """
    Internal function
    Do NOT use this!!!
    """
    if not hasattr(__get_native_lib, "__instance"):
        lib_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "Win64ProcToolkit.dll"
        )
        setattr(__get_native_lib, "__instance", CDLL(lib_path))
        instance: CDLL = getattr(__get_native_lib, "__instance")
        instance.get_process_id.argtypes = [c_wchar_p]
        instance.get_process_id.restype = c_uint32
        instance.inject_dll.argtypes = [c_uint32, c_wchar_p]
        instance.inject_dll.restype = c_bool
        instance.create_process_snapshot.argtypes = []
        instance.create_process_snapshot.restype = c_size_t
        instance.free_process_snapshot.argtypes = []
        instance.free_process_snapshot.restype = None
        instance.get_process_name_from_snapshot.argtypes = [c_size_t]
        instance.get_process_name_from_snapshot.restype = c_wchar_p
        instance.get_process_id_from_snapshot.argtypes = [c_size_t]
        instance.get_process_id_from_snapshot.restype = c_uint32
        instance.kill_process.argtypes = [c_uint32, c_uint32]
        instance.kill_process.restype = c_bool
    return getattr(__get_native_lib, "__instance")
