<#
  Grimório de Tibia — visitas por dia, a partir do registo do Apache (r34).
  Conta as aberturas da página do Grimório e do Questski e os visitantes únicos (endereços IP diferentes) de cada dia.
  Não conta robôs, os testes do smoke.mjs (browser sem janela) nem a rede de casa.

    powershell -ExecutionPolicy Bypass -File C:\xampp\htdocs\grimorio\_dev\visitas.ps1
    powershell -ExecutionPolicy Bypass -File C:\xampp\htdocs\grimorio\_dev\visitas.ps1 -Dias 30
    powershell -ExecutionPolicy Bypass -File C:\xampp\htdocs\grimorio\_dev\visitas.ps1 -Limpar 365

  -Log     o registo do Apache (por omissão C:\xampp\apache\logs\access.log)
  -Dias    só os últimos N dias (por omissão todos)
  -Limpar  apaga do registo as linhas com mais de N dias (a política de privacidade promete 12 meses: usa 365).
           Pára o Apache antes (XAMPP Control Panel) e volta a ligá-lo depois; fica uma cópia access.log.bak.
  Só lê o registo, a não ser com -Limpar. Não manda nada para fora do PC.
#>
param(
  [string]$Log = 'C:\xampp\apache\logs\access.log',
  [int]$Dias = 0,
  [int]$Limpar = 0
)
$ErrorActionPreference = 'Stop'
$inv = [Globalization.CultureInfo]::InvariantCulture
$linha = '^(\S+) \S+ \S+ \[(\d{2}/\w{3}/\d{4}):'

if ($Limpar -gt 0) {
  $corte = (Get-Date).Date.AddDays(-$Limpar)
  Copy-Item $Log "$Log.bak" -Force
  $fica = Get-Content $Log | Where-Object {
    if ($_ -match $linha) { [datetime]::ParseExact($matches[2], 'dd/MMM/yyyy', $inv) -ge $corte } else { $true }
  }
  Set-Content -Path $Log -Value $fica -Encoding Ascii
  Write-Host "Registo limpo: ficaram as linhas desde $($corte.ToString('yyyy-MM-dd')). Cópia em $Log.bak"
  return
}

# página do Grimório (/, /index.html) ou do Questski (/quests/), com ou sem ?…; só respostas 200 e 304
$pagina = '"GET /(grimorio/)?(quests/)?(index\.html)?(\?\S*)? HTTP/[\d.]+" (200|304) '
$robo = 'bot|crawl|spider|slurp|curl|wget|python|java/|Go-http|Headless|lighthouse|monitor|preview'
$casa = '^(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|::1|fe80:)'
$desde = if ($Dias -gt 0) { (Get-Date).Date.AddDays(-$Dias + 1) } else { [datetime]::MinValue }

$porDia = @{}
foreach ($l in [IO.File]::ReadLines($Log)) {
  if ($l -notmatch $pagina -or $l -match $robo) { continue }
  if ($l -notmatch $linha) { continue }
  $ip = $matches[1]; $d = [datetime]::ParseExact($matches[2], 'dd/MMM/yyyy', $inv)
  if ($ip -match $casa -or $d -lt $desde) { continue }
  $k = $d.ToString('yyyy-MM-dd')
  if (-not $porDia.ContainsKey($k)) { $porDia[$k] = @{ v = 0; ips = New-Object 'System.Collections.Generic.HashSet[string]' } }
  $porDia[$k].v++
  [void]$porDia[$k].ips.Add($ip)
}
if ($porDia.Count -eq 0) { Write-Host 'Sem visitas no registo (ou o caminho do -Log está errado).'; return }

$t = $porDia.GetEnumerator() | Sort-Object Name | ForEach-Object {
  [pscustomobject]@{ Dia = $_.Name; Visitantes = $_.Value.ips.Count; Aberturas = $_.Value.v }
}
$t | Format-Table -AutoSize
$m = ($t | Measure-Object Visitantes -Average -Maximum)
Write-Host ("Dias: {0}   média de visitantes por dia: {1:N0}   melhor dia: {2}" -f $t.Count, $m.Average, $m.Maximum)
