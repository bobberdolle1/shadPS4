param([int]$Seconds = 10)
$ErrorActionPreference = 'Stop'
$p = Get-Process shadps4 -ErrorAction SilentlyContinue
if (-not $p) { Write-Output 'shadps4 not running'; exit 1 }

function Snap($proc) {
    $proc.Refresh()
    $h = @{}
    foreach ($t in $proc.Threads) {
        try { $h[$t.Id] = [double]$t.TotalProcessorTime.TotalSeconds } catch {}
    }
    $cpu = [double]$proc.TotalProcessorTime.TotalSeconds
    return @{ Threads = $h; Cpu = $cpu; Ws = [double]$proc.WorkingSet64 }
}

$a = Snap $p
$t0 = Get-Date
Start-Sleep -Seconds $Seconds
$p.Refresh()
$b = Snap $p
$t1 = Get-Date
$wall = ($t1 - $t0).TotalSeconds

Write-Output ("wall={0:N1}s process_cpu_delta={1:N2}s ({2:P1} of {3} cores)" -f $wall, ($b.Cpu - $a.Cpu), (($b.Cpu - $a.Cpu) / $wall), [Environment]::ProcessorCount)
Write-Output ("working_set={0:N0} MB" -f ($b.Ws / 1MB))

$rows = @()
foreach ($id in $b.Threads.Keys) {
    if ($a.Threads.ContainsKey($id)) {
        $d = $b.Threads[$id] - $a.Threads[$id]
        if ($d -gt 0.001) {
            $rows += [pscustomobject]@{ Tid = $id; CpuSec = [math]::Round($d, 3); PctOneCore = [math]::Round(100 * $d / $wall, 1) }
        }
    }
}
$rows | Sort-Object CpuSec -Descending | Select-Object -First 12 | Format-Table -AutoSize | Out-String -Width 120
