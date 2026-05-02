#Requires -Version 5.1
<#
.SYNOPSIS
  Windows helper: optional venv, generate data, upload to S3, invoke run_pipeline.py.

.EXAMPLE
  .\scripts\run_pipeline.ps1 -Bucket "de-template-dev-data-lake-123456789012" -Region "us-east-1" -RunGlue
#>
param(
    [Parameter(Mandatory = $true)][string] $Bucket,
    [string] $Region = "us-east-1",
    [string] $Profile = "",
    [switch] $Generate,
    [switch] $DownloadSample,
    [switch] $RunGlue,
    [string] $GlueRawJob = "",
    [string] $GlueCuratedJob = "",
    [string] $CrawlerStaging = "",
    [string] $CrawlerCurated = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    $py = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $py) {
    Write-Error "Python not found on PATH."
}

& $py.Source -m pip install -q -r "$RepoRoot\scripts\requirements.txt"

$runArgs = @(
    "$RepoRoot\scripts\run_pipeline.py",
    "--bucket", $Bucket,
    "--region", $Region
)
if ($Profile) { $runArgs += @("--profile", $Profile) }
if ($Generate) { $runArgs += "--generate" }
if ($DownloadSample) { $runArgs += "--download-sample" }

if ($RunGlue) {
    if (-not $GlueRawJob -or -not $GlueCuratedJob) {
        Write-Error "When using -RunGlue, set -GlueRawJob and -GlueCuratedJob (see terraform output)."
    }
    $runArgs += "--glue-jobs"
    $runArgs += @("--glue-raw-job", $GlueRawJob)
    $runArgs += @("--glue-curated-job", $GlueCuratedJob)
    foreach ($c in @($CrawlerStaging, $CrawlerCurated)) {
        if ($c) { $runArgs += @("--crawler", $c) }
    }
}

& $py.Source @runArgs
