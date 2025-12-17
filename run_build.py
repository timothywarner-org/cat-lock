"""Run PyInstaller build for PawGate."""
import subprocess
import sys
import os

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
