# Solyaris Agent demo

## Windows quick start

1. Download the repository as a ZIP from GitHub.
2. Extract the ZIP to a local folder.
3. Open this `release` folder.
4. Double-click `run-demo.bat` or `SolyarisAgent.exe`.

The executable is a portable Windows demo. It includes its Python runtime and does not require Python, Docker, Flet, WebView2, or a GigaChat key for the local traffic-light analysis flow. It opens the interface in the default web browser.

## If Windows shows "Failed to load Python DLL"

The release includes the bundled Python runtime and VC++ DLLs. If this error still appears, download the ZIP again and extract it completely; do not copy only the EXE out of the `release` folder.

- [Microsoft Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)

The x64 VC++ installer is only a fallback for older Windows installations. WebView2 is not required because the demo opens in the system browser.

If Windows SmartScreen appears, choose **More info** and verify that the file was downloaded from the author's GitHub repository before continuing.

Keep `SolyarisAgent.exe` and `run-demo.bat` in the same folder.
