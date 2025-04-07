import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "include_files": ["config.ini"]
}

# base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="Updater",
    version="0.1",
    description="Updater",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base="Console", icon="icon.ico", target_name="Updater.exe")],
)
