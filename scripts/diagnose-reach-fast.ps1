# Fast reachability diagnose — no hanging Store python stub
$log = "d:\expenseTracker\debug-fb4af6.log"
function W($hid, $msg, $data) {
  $o = [ordered]@{
    sessionId = "fb4af6"
    runId = "reach-pre2"
    hypothesisId = $hid
    location = "diagnose-reach-fast.ps1"
    message = $msg
    data = $data
    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  } | ConvertTo-Json -Compress -Depth 8
  Add-Content -LiteralPath $log -Value $o -Encoding utf8
}

# Clear previous partial log content by overwrite via caller delete; append here

$pyPath = (Get-Command python -ErrorAction SilentlyContinue).Source
$isStoreStub = $pyPath -like "*WindowsApps*"
W "H1" "python_path" @{ path = $pyPath; isWindowsStoreStub = $isStoreStub }

W "H2" "venv_check" @{
  venvPython = (Test-Path "d:\expenseTracker\.venv\Scripts\python.exe")
  venvDir = (Test-Path "d:\expenseTracker\.venv")
}

# Find real Python installs without invoking Store stub
$candidates = @()
$searchRoots = @(
  "$env:LOCALAPPDATA\Programs\Python",
  "$env:ProgramFiles\Python*",
  "${env:ProgramFiles(x86)}\Python*",
  "C:\Python*"
)
foreach ($root in $searchRoots) {
  Get-ChildItem -Path $root -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "WindowsApps" } |
    Select-Object -First 5 |
    ForEach-Object { $candidates += $_.FullName }
}
W "H1b" "real_python_search" @{ candidates = $candidates }

# Port 5000 without Get-NetTCPConnection (can hang without admin)
$listen5000 = $false
try {
  $tcp = [System.Net.Sockets.TcpClient]::new()
  $iar = $tcp.BeginConnect("127.0.0.1", 5000, $null, $null)
  $ok = $iar.AsyncWaitHandle.WaitOne(800)
  if ($ok -and $tcp.Connected) { $listen5000 = $true }
  $tcp.Close()
} catch {}
W "H3" "port_5000_tcp_probe" @{ acceptingConnections = $listen5000 }

W "H4" "app_files" @{
  appPy = (Test-Path "d:\expenseTracker\app.py")
  templates = (Test-Path "d:\expenseTracker\templates\login.html")
  staticCss = (Test-Path "d:\expenseTracker\static\css\styles.css")
}

try {
  $req = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:5000/")
  $req.Timeout = 1500
  $req.Method = "GET"
  $resp = $req.GetResponse()
  W "H5" "http_probe" @{ ok = $true; status = [int]$resp.StatusCode }
  $resp.Close()
} catch {
  W "H5" "http_probe" @{ ok = $false; error = $_.Exception.Message }
}

Write-Output "done"
