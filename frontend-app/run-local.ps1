$ErrorActionPreference = "Stop"

Set-Location "D:\Projects\Major Project\frontend-app"

$env:NEXT_PUBLIC_BACKEND_API_URL = "http://127.0.0.1:8000"
$env:NEXT_PUBLIC_WS_URL = "ws://127.0.0.1:8000/ws"

npm.cmd run build
npm.cmd run start -- --port 3001
