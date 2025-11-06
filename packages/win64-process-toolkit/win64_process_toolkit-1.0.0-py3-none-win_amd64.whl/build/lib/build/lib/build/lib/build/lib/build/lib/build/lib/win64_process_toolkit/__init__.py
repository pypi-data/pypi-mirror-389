from typing import List
from win64_process_toolkit.__internal.native_lib import __get_native_lib


class ProcessInfo:
    """Windows Process Information"""

    @property
    def name(self):
        """Process Name (read only)"""
        return getattr(self, "__name")

    @property
    def id(self):
        """Process ID (read only)"""
        return getattr(self, "__id")


def get_process_id(process_name: str) -> int:
    """
    Get the ID of a process by name

    Args:
        process_name (str): _description_

    Returns:
        int: Process ID (0 if process not exist)
    """
    return __get_native_lib().get_process_id(process_name)


def inject_dll(process_id: int, dll_path: str) -> bool:
    """Inject a DLL into an existed process

    Args:
        process_id (int): The process ID
        dll_path (str): The file path of the DLL

    Returns:
        bool: True if succeed
    """
    return __get_native_lib().inject_dll(process_id, dll_path)


def get_runtime_processes() -> List[ProcessInfo]:
    """Get all running process information

    Returns:
        List[ProcessInfo]: Runtime processes
    """
    result = []
    lib = __get_native_lib()
    count = lib.create_process_snapshot()
    for index in range(count):
        info = ProcessInfo()
        setattr(info, "__name", lib.get_process_name_from_snapshot(index))
        setattr(info, "__id", lib.get_process_id_from_snapshot(index))
        result.append(info)
    lib.free_process_snapshot()
    return result


def get_runtime_process_names() -> List[str]:
    """Get all running process names

    Returns:
        List[str]: Runtime process names
    """
    result = []
    lib = __get_native_lib()
    count = lib.create_process_snapshot()
    for index in range(count):
        result.append(lib.get_process_name_from_snapshot(index))
    lib.free_process_snapshot()
    return result


def kill_process(process_id: int, exit_code: int = 1) -> bool:
    """Kill an existing process

    Args:
        process_id (int): The process ID
        exit_code (int, optional): Process exit code. Defaults to 1.

    Returns:
        bool: True if succeed
    """
    __get_native_lib().kill_process(process_id, exit_code)
