from PyInstaller.utils.hooks import collect_dynamic_libs,collect_submodules,collect_data_files

binaries = collect_dynamic_libs("win64_process_toolkit", search_patterns=["*.dll"])
hiddenimports = collect_submodules("win64_process_toolkit")
datas = collect_data_files("win64_process_toolkit")
