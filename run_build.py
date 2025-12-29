"""Run PyInstaller build for PawGate."""
import os
import subprocess
import sys

from src.util.path_util import get_config_path


def delete_user_config() -> None:
    """Remove the user config file so each build starts clean."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        os.remove(config_path)
        print(f"Removed user config: {config_path}")
    else:
        print(f"No user config found at: {config_path}")


delete_user_config()

os.chdir(r'C:\github\pawgate')

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--onefile',
    '--distpath=./dist',
    '--workpath=./build',
    '--add-data=./resources/img/icon.ico;./resources/img/',
    '--add-data=./resources/img/icon.png;./resources/img/',
    '--add-data=./resources/config/config.json;./resources/config/',
    '--icon=./resources/img/icon.ico',
    '--hidden-import=plyer.platforms.win.notification',
    '--noconsole',
    '--name=PawGate',
    './src/main.py'
]

print(f"Running: {' '.join(cmd)}")
print("-" * 60)

result = subprocess.run(cmd, capture_output=False)
print("-" * 60)
print(f"Exit code: {result.returncode}")
