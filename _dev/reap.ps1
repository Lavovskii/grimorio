# Limpeza dos testes do smoke.mjs (corre no arranque de cada smoke; também se pode correr à mão).
# Cada teste usa uma pasta %TEMP%\grim-smoke-XXXXXX com owner.pid = PID do node que a criou.
# Uma pasta está "morta" se esse PID já não é um node vivo (ou é um PID reaproveitado por um node mais recente),
# ou se não tem owner.pid e tem mais de 15 min ($MinAge). Pastas cujo dono é um node vivo nunca são tocadas (testes em paralelo).
#  (a) encontra as pastas mortas; (b) fecha os msedge/chrome cuja linha de comando tem o nome de uma pasta morta;
#  (c) apaga as pastas mortas sem browser com mais de 15 min, dentro do -Budget. É a única regra que apaga pastas.
# -Caller <pid>: o smoke passa o seu PID. Se ele aparecer na lista de nodes vivos, a lista é de confiança e os browsers
#  de pastas mortas fecham logo; sem isso (corrida à mão) só fecha os de pastas mortas com mais de 2 min.
# -Budget <s>: tempo máximo a apagar pastas nesta corrida (o resto fica para a seguinte).
param([int]$Caller = 0, [int]$Budget = 12)
$ErrorActionPreference = 'SilentlyContinue'
$MinAge = 15
$t0 = Get-Date
$tmp = [IO.Path]::GetTempPath()
$dirs = @(Get-ChildItem -LiteralPath $tmp -Directory -Filter 'grim-smoke-*' -Force)

$nodes = @{}
Get-Process node -ErrorAction SilentlyContinue | ForEach-Object { $nodes[$_.Id] = $_.StartTime }
$grace = 2
if ($Caller -gt 0 -and $nodes.ContainsKey($Caller)) { $grace = 0 }

# (a) pastas mortas
$dead = @{}
foreach ($d in $dirs) {
  $age = ($t0 - $d.CreationTime).TotalMinutes
  $own = Join-Path $d.FullName 'owner.pid'
  $isDead = $false
  if (Test-Path -LiteralPath $own) {
    $p = 0
    [void][int]::TryParse(([string](Get-Content -LiteralPath $own -Raw)).Trim(), [ref]$p)
    $alive = $false
    if ($p -gt 0 -and $nodes.ContainsKey($p)) {
      $st = $nodes[$p]
      # um node que arrancou depois de a pasta existir não pode ser o dono (PID reaproveitado)
      $alive = (-not $st) -or ($st -le $d.CreationTime.AddSeconds(5))
    }
    $isDead = -not $alive
  } elseif ($age -gt $MinAge) {
    $isDead = $true
  }
  if ($isDead) { $dead[$d.Name.ToLower()] = @{ age = $age; path = $d.FullName } }
}

# (b) browsers de pastas mortas (e de pastas que já não existem, se o browser tiver mais de 2 min)
$killed = 0
$procs = @(Get-CimInstance Win32_Process -Filter "Name='msedge.exe' OR Name='chrome.exe'" | Where-Object { $_.CommandLine -like '*grim-smoke-*' })
foreach ($pr in $procs) {
  if ($pr.CommandLine -notmatch 'grim-smoke-[A-Za-z0-9]+') { continue }
  $n = $Matches[0].ToLower()
  $kill = $false
  if ($dead.ContainsKey($n)) {
    $kill = $dead[$n].age -ge $grace
  } elseif (-not (Test-Path -LiteralPath (Join-Path $tmp $n))) {
    $kill = $pr.CreationDate -and (($t0 - $pr.CreationDate).TotalMinutes -ge 2)
  }
  if ($kill) { Stop-Process -Id $pr.ProcessId -Force -ErrorAction SilentlyContinue; $killed++ }
}
if ($killed) { Start-Sleep -Milliseconds 800 }

# pastas ainda em uso: nomes grim-smoke-* na linha de comando de um msedge/chrome vivo (depois de (b))
$inuse = @{}
Get-CimInstance Win32_Process -Filter "Name='msedge.exe' OR Name='chrome.exe'" | ForEach-Object {
  if ([string]$_.CommandLine -match 'grim-smoke-[A-Za-z0-9]+') { $inuse[$Matches[0].ToLower()] = 1 }
}

# (c) apaga as pastas mortas sem browser com mais de $MinAge min (uma pasta com dono vivo nunca está em $dead)
foreach ($k in @($dead.Keys)) {
  $x = $dead[$k]
  if ($inuse.ContainsKey($k) -or $x.age -le $MinAge) { continue }
  if (((Get-Date) - $t0).TotalSeconds -gt $Budget) { break }
  try { Remove-Item -LiteralPath $x.path -Recurse -Force -ErrorAction Stop } catch { }
}
