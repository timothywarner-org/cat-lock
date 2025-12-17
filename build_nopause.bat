@echo off
cd /d C:\github\pawgate
.venv\Scripts\pyinstaller.exe --onefile --distpath=dist --workpath=build --add-data="resources/img/icon.ico;resources/img/" --add-data="resources/img/icon.png;resources/img/" --add-data="resources/config/config.json;resources/config/" --icon=resources/img/icon.ico --hidden-import plyer.platforms.win.notification --noconsole --name=PawGate src/main.py
