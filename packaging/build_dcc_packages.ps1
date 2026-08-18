param(
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $ProjectRoot "dist"
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$Stage = Join-Path $OutputDirectory "stage"
if ($OutputDirectory -eq [IO.Path]::GetPathRoot($OutputDirectory)) {
    throw "OutputDirectory cannot be a drive root."
}

if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $Stage | Out-Null

$BlenderStage = Join-Path $Stage "BlenderAssetSync"
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "blender\BlenderAssetSync") -Destination $BlenderStage -Recurse
Copy-Item -LiteralPath (Join-Path $ProjectRoot "assetsync") -Destination (Join-Path $BlenderStage "assetsync") -Recurse
Get-ChildItem -LiteralPath $BlenderStage -Recurse -Directory -Filter "__pycache__" | Sort-Object FullName -Descending | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $BlenderStage -Recurse -File | Where-Object { $_.Extension -in ".pyc", ".pyo" } | Remove-Item -Force
$BlenderZip = Join-Path $OutputDirectory "BlenderAssetSync.zip"
if (Test-Path -LiteralPath $BlenderZip) { Remove-Item -LiteralPath $BlenderZip -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($Stage, $BlenderZip, [IO.Compression.CompressionLevel]::Optimal, $false)

$UnrealStage = Join-Path $OutputDirectory "UnrealAssetSync"
if (Test-Path -LiteralPath $UnrealStage) { Remove-Item -LiteralPath $UnrealStage -Recurse -Force }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "unreal\UnrealAssetSync") -Destination $UnrealStage -Recurse
Copy-Item -LiteralPath (Join-Path $ProjectRoot "assetsync") -Destination (Join-Path $UnrealStage "assetsync") -Recurse
Get-ChildItem -LiteralPath $UnrealStage -Recurse -Directory -Filter "__pycache__" | Sort-Object FullName -Descending | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $UnrealStage -Recurse -File | Where-Object { $_.Extension -in ".pyc", ".pyo" } | Remove-Item -Force

$RootBlenderZip = Join-Path $ProjectRoot "BlenderAssetSync.zip"
Copy-Item -LiteralPath $BlenderZip -Destination $RootBlenderZip -Force
$RootUnreal = Join-Path $ProjectRoot "UnrealAssetSync"
if (Test-Path -LiteralPath $RootUnreal) { Remove-Item -LiteralPath $RootUnreal -Recurse -Force }
Copy-Item -LiteralPath $UnrealStage -Destination $RootUnreal -Recurse

Remove-Item -LiteralPath $Stage -Recurse -Force
Write-Output "Built: $RootBlenderZip"
Write-Output "Built: $RootUnreal"
