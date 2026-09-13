@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0SolyarisAgent.exe" (
	echo SolyarisAgent.exe was not found in this folder.
	pause
	exit /b 1
)
start "Solyaris Agent" "%~dp0SolyarisAgent.exe"
