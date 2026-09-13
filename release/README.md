# Solyaris Agent demo

## Windows quick start

1. Download the repository as a ZIP from GitHub.
2. Extract the ZIP to a local folder.
3. Open this `release` folder.
4. Double-click `run-demo.bat` or `SolyarisAgent.exe`.

The executable is a portable Windows demo. It includes its Python runtime and does not require Python, Docker, Flet, or a GigaChat key for the local traffic-light analysis flow. It opens the interface in its own window.

## If Windows shows "Failed to load Python DLL"

The release includes the bundled Python runtime and VC++ DLLs. If this error still appears, download the ZIP again and extract it completely; do not copy only the EXE out of the `release` folder.

- [Microsoft Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)

Install [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) if the window does not open. Flet uses WebView2 for the embedded application window.

If Windows SmartScreen appears, choose **More info** and verify that the file was downloaded from the author's GitHub repository before continuing.

Keep `SolyarisAgent.exe` and `run-demo.bat` in the same folder.
