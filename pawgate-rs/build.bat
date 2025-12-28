@echo off
REM Build script for PawGate (Rust version)
REM Builds an optimized release binary

echo Building PawGate (Rust)...
echo.

REM Check if Rust is installed
where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Rust/Cargo not found. Please install from https://rustup.rs
    pause
    exit /b 1
)

REM Build release version
echo Running: cargo build --release
cargo build --release

if %errorlevel% neq 0 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

REM Show output location
echo.
echo Build successful!
echo Output: target\release\pawgate.exe
echo.

REM Show binary size
for %%A in (target\release\pawgate.exe) do (
    set size=%%~zA
    echo Binary size: %%~zA bytes
)

echo.
pause
