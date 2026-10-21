# Serve Tibia Questski on http://localhost:8080 without Python, using the PowerShell that ships with Windows.
# Usage: powershell -ExecutionPolicy Bypass -File serve.ps1 [-Port 8080] [-NoBrowser]
param([int]$Port = 8080, [switch]$NoBrowser)

$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'site'))
$types = @{
  '.html' = 'text/html; charset=utf-8'; '.js' = 'text/javascript; charset=utf-8'; '.css' = 'text/css; charset=utf-8'
  '.json' = 'application/json; charset=utf-8'; '.txt' = 'text/plain; charset=utf-8'; '.svg' = 'image/svg+xml'
  '.png' = 'image/png'; '.gif' = 'image/gif'; '.jpg' = 'image/jpeg'; '.jpeg' = 'image/jpeg'; '.webp' = 'image/webp'
  '.ico' = 'image/x-icon'; '.woff' = 'font/woff'; '.woff2' = 'font/woff2'
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:${Port}/")
try { $listener.Start() }
catch {
  Write-Host "Nao foi possivel abrir a porta ${Port}: $($_.Exception.Message)"
  Write-Host "Se o site ja esta aberto noutra janela, usa essa."
  exit 1
}
Write-Host "Tibia Questski a correr em http://localhost:${Port}  (fecha esta janela para parar)"
if (-not $NoBrowser) { Start-Process "http://localhost:${Port}/" }

while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  $res = $ctx.Response
  try {
    $rel = [System.Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath).TrimStart('/')
    if ($rel -eq '' -or $rel.EndsWith('/')) { $rel += 'index.html' }
    $path = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($root, $rel))
    # only files inside site/
    if ($path.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase) -and [System.IO.File]::Exists($path)) {
      $bytes = [System.IO.File]::ReadAllBytes($path)
      $ext = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
      if ($types.ContainsKey($ext)) { $res.ContentType = $types[$ext] } else { $res.ContentType = 'application/octet-stream' }
      $res.Headers['Cache-Control'] = 'no-cache'
      $res.ContentLength64 = $bytes.Length
      $res.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
      $res.StatusCode = 404
    }
  } catch {
    try { $res.StatusCode = 500 } catch {}
  } finally {
    try { $res.Close() } catch {}
  }
}
