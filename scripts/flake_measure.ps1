# flake_measure.ps1 — 公网 flake 度量（M6 二轮 P2-2 硬性闭环：度量机制化）
#
# 背景：M6 二轮复审要求"固定一份可复跑命令 + 结果记录模板"，回答
#   "当前 flake 率是多少"（换人/换时段都可复现），并纳入 goto 重试计数
#   （P2-1：重试一旦触发，计数 > 0 会出现在 pytest_terminal_summary）。
#
# 用法：
#   .\scripts\flake_measure.ps1 -Runs 3 -Marker ui
#   .\scripts\flake_measure.ps1                # 默认 Runs=3, Marker=ui
# 输出：逐次结果（PASS/FAIL + 耗时）+ goto 重试计数（若触发）+ 汇总成功率。
# 记录方式：把输出贴到 MODULE_FEEDBACK「flake 记录」节（固定模板）。
#
# 注意：用项目 venv 解释器（M6 教训：shell 的 python 可能是共享 venv，浏览器版本会错位）。

param(
    [int]$Runs = 3,
    [string]$Marker = "ui"
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Error "项目 venv 不存在: $py (请先创建/激活 .venv)"
    exit 2
}

Write-Output "===== flake measure: marker=$Marker runs=$Runs" (Get-Date -Format 'yyyy-MM-dd HH:mm') "====="
Write-Output "(target = public Demo; set ORANGEHRM_* env vars for local)"

$passCount = 0
for ($i = 1; $i -le $Runs; $i++) {
    $out = & $py -m pytest -m $Marker 2>&1 | Out-String
    $code = $LASTEXITCODE
    $summaryLines = @($out -split "`n" | Where-Object { $_ -match "passed|failed|error|skipped" })
    $summary = ""
    if ($summaryLines.Count -gt 0) { $summary = $summaryLines[$summaryLines.Count - 1] }
    $retryLines = @($out -split "`n" | Where-Object { $_ -match "goto" })
    $retry = ""
    if ($retryLines.Count -gt 0) { $retry = $retryLines[$retryLines.Count - 1] }
    if ($code -eq 0) { $passCount++ }
    $verdict = "PASS"
    if ($code -ne 0) { $verdict = "FAIL" }
    Write-Output ("RUN {0}/{1}: {2} (exit={3})" -f $i, $Runs, $verdict, $code)
    Write-Output ("     last summary: {0}" -f $summary.Trim())
    if ($retry) { Write-Output ("     goto retry: {0}" -f $retry.Trim()) }
}

Write-Output "----- summary -----"
Write-Output ("success rate: {0}/{1}, failures: {2}" -f $passCount, $Runs, ($Runs - $passCount))
Write-Output "record template: | date | pass/total | marker | note |"
Write-Output "===== measure done ====="