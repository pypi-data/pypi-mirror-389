from PyInstaller.utils.hooks import (
    collect_dynamic_libs,
    collect_data_files,
    collect_submodules,
)

hiddenimports = collect_submodules("win64_process_toolkit")
datas = collect_data_files("win64_process_toolkit")
binaries = collect_dynamic_libs("win64_process_toolkit", search_patterns=["*.dll"])
