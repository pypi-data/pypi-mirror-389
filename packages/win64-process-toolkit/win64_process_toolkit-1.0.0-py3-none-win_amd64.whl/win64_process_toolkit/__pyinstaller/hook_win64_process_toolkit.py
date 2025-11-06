from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs,
)

hiddenimports = collect_submodules("win64_process_toolkit")
datas = collect_data_files("win64_process_toolkit")
binaries = collect_dynamic_libs("win64_process_toolkit")
