$ErrorActionPreference = "Stop"

Set-Location "D:\Projects\Major Project\backend-api"

$env:DATABASE_URL = "sqlite:///backend-api.db"
$env:AI_SERVICE_URL = "http://127.0.0.1:8001"
$env:AI_FINALIZE_TIMEOUT_SECONDS = "900"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
