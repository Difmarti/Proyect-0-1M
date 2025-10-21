Why MetaTrader5 isn't in the main requirements

The official `MetaTrader5` Python package is a Windows-only binary that depends on the MetaTrader terminal and Windows-specific extensions. It is not available on Linux manylinux wheels, so installing it inside Linux-based Docker images will fail.

What I changed

- Removed `MetaTrader5` from `requirements.txt` (the Linux/container-friendly list).
- Added `requirements-windows.txt` containing `MetaTrader5==5.0.37` for Windows installs.

How to work with MT5 locally (Windows)

1. Create and activate a Python virtual environment (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install normal requirements:

```powershell
pip install -r python-bridge/requirements.txt
```

3. Install the MT5 package (Windows only):

```powershell
pip install -r python-bridge/requirements-windows.txt
```

Running in Docker

- If you want to run the `python-bridge` service in Docker on Linux, do not include `MetaTrader5` in the image. Build the image normally; MT5 will be unavailable inside the container. Use the bridge to communicate with a remote Windows machine running MetaTrader and the necessary connector.

Windows containers (advanced)

- It is possible to build a Windows-based container that includes MetaTrader5, but Windows containers require a Windows host (or Windows Server) and different Docker base images. This is more complex and usually unnecessary for development.

Alternative: remote MT5 gateway

- For CI or Linux deployments, run the MetaTrader terminal and Python script on a Windows VM or host, and have your Linux services communicate with it over the network (HTTP/gRPC/RPC). This keeps your Linux containers lightweight and avoids Windows-only binaries inside Linux images.

