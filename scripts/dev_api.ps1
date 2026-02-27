Param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload
)

Write-Host "Starting QVM API at http://$Host:$Port ..."
$reloadFlag = ""
if ($Reload) { $reloadFlag = "--reload" }

python -m src.qvm.server --host $Host --port $Port $reloadFlag
