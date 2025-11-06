from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs("win64_process_toolkit", search_patterns=["*.dll"])
datas = collect_dynamic_libs("win64_process_toolkit", search_patterns=["*.dll"])
