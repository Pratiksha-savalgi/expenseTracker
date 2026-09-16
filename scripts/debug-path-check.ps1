# Debug path resolution for prototypes/index.html
$logPath = "d:\expenseTracker\debug-fb4af6.log"
$target = "d:\expenseTracker\docs\design\prototypes\index.html"
$dir = "d:\expenseTracker\docs\design\prototypes"

function Write-AgentLog {
  param($HypothesisId, $Message, $Data)
  $payload = @{
    sessionId = "fb4af6"
    hypothesisId = $HypothesisId
    location = "scripts/debug-path-check.ps1"
    message = $Message
    data = $Data
    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    runId = "pre-fix"
  } | ConvertTo-Json -Compress -Depth 8
  Add-Content -LiteralPath $logPath -Value $payload -Encoding utf8
}

Write-AgentLog -HypothesisId "H1" -Message "file_exists_check" -Data @{
  path = $target
  exists = (Test-Path -LiteralPath $target)
  isFile = (Test-Path -LiteralPath $target -PathType Leaf)
}

$children = @()
if (Test-Path -LiteralPath $dir) {
  $children = @(Get-ChildItem -LiteralPath $dir | ForEach-Object { $_.Name })
}
Write-AgentLog -HypothesisId "H2" -Message "directory_listing" -Data @{
  dir = $dir
  dirExists = (Test-Path -LiteralPath $dir)
  children = $children
}

Write-AgentLog -HypothesisId "H3" -Message "workspace_root_check" -Data @{
  pwd = (Get-Location).Path
  expenseTrackerExists = (Test-Path -LiteralPath "d:\expenseTracker")
  docsExists = (Test-Path -LiteralPath "d:\expenseTracker\docs")
  designExists = (Test-Path -LiteralPath "d:\expenseTracker\docs\design")
}

$encoded = "d:%5CexpenseTracker%5Cdocs%5Cdesign%5Cprototypes%5Cindex.html"
$decoded = [System.Uri]::UnescapeDataString($encoded)
$correctFileUri = "file:///" + ($target -replace "\\", "/")
Write-AgentLog -HypothesisId "H4" -Message "path_encoding_analysis" -Data @{
  errorResource = $encoded
  decoded = $decoded
  badScheme = $encoded.StartsWith("d:%5C")
  correctFileUri = $correctFileUri
  note = "Cursor error uses drive letter as URI scheme with encoded backslashes"
}

if (Test-Path -LiteralPath $target) {
  $item = Get-Item -LiteralPath $target
  Write-AgentLog -HypothesisId "H5" -Message "resolved_file_info" -Data @{
    fullName = $item.FullName
    length = $item.Length
    lastWriteTime = $item.LastWriteTime.ToString("o")
  }
} else {
  Write-AgentLog -HypothesisId "H5" -Message "resolved_file_info" -Data @{ missing = $true }
}

# Try opening with correct file URI via default browser (not Cursor resource resolver)
try {
  Start-Process $correctFileUri
  Write-AgentLog -HypothesisId "H4" -Message "opened_via_file_uri" -Data @{ uri = $correctFileUri; ok = $true }
} catch {
  Write-AgentLog -HypothesisId "H4" -Message "opened_via_file_uri" -Data @{ uri = $correctFileUri; ok = $false; error = $_.Exception.Message }
}

Write-Output "OK"
