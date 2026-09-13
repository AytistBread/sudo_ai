# Solyaris Agent demo

## Windows quick start

1. Download the repository as a ZIP from GitHub.
2. Extract the ZIP to a local folder.
3. Open this `release` folder.
4. Double-click `run-demo.bat` or `SolyarisAgent.exe`.

The executable is a Windows desktop demo. It does not require Python, Docker, or a GigaChat key for the local traffic-light analysis flow.

## If Windows shows "Failed to load Python DLL"

The error means that Windows cannot load a dependency of the bundled Python runtime. Install these Microsoft components, then run the demo again:

- [Microsoft Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/)

Extract the GitHub ZIP completely before starting the EXE. Do not run it from inside the ZIP preview. Use the x64 VC++ installer even if Python is not installed. Restarting Windows is normally not required.

If Windows SmartScreen appears, choose **More info** and verify that the file was downloaded from the author's GitHub repository before continuing.

Keep `SolyarisAgent.exe` and `run-demo.bat` in the same folder.
