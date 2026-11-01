<?php
/*
 * Grimório de Tibia — estatísticas próprias, sem cookies (r34).
 *
 *   POST stats.php   corpo JSON (navigator.sendBeacon do shared/pub.js), no máximo 1 KB:
 *        {"s":"g"|"q"|"p", "p":"hunts", "r":"google.com", "l":"pt-PT", "m":"m"|"d", "f":1}
 *        s = site (Grimório, Questski, política), p = rota (o que vem depois do #, sem números de personagem),
 *        r = site de onde a pessoa veio (só o domínio; vazio = entrada direta), l = língua, m = telemóvel ou computador,
 *        f = 1 na primeira página da visita (aberturas do site), 0 nas mudanças de página dentro dele.
 *   204 sempre (nada a ler; quem vê os números é o _dev/estatisticas.py no servidor).
 *
 * Privacidade: não há cookies nem nada guardado no browser. O endereço IP e o browser só servem para fazer um código
 * (sha256 com um sal aleatório que muda todos os dias e é apagado), para contar visitantes únicos do dia; o IP não é
 * guardado. Ao mudar o dia, os códigos do dia anterior são trocados pela contagem. Ficheiros em cache/stats/
 * (fechados ao público pelo .htaccess da cache), um por dia: stats-AAAA-MM-DD.json.
 */
declare(strict_types=1);

ini_set('display_errors', '0');
error_reporting(E_ALL);
header('Cache-Control: no-store');

const ST_DIR = __DIR__ . DIRECTORY_SEPARATOR . 'cache' . DIRECTORY_SEPARATOR . 'stats';
const ST_MAXKEYS = 1500;   // rotas/origens diferentes por dia; o resto conta em "(outras)"
const ST_KEEP = 400;       // dias guardados (a política promete apagar ao fim de 12 meses)

function done(): void { http_response_code(204); exit; }

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { http_response_code(405); header('Allow: POST'); exit; }
$ua = substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 400);
if ($ua === '' || preg_match('/bot|crawl|spider|slurp|preview|headless|lighthouse|python|curl|wget|java\/|go-http/i', $ua)) done();

$raw = file_get_contents('php://input', false, null, 0, 1025);
if ($raw === false || strlen($raw) > 1024) done();
$in = json_decode($raw, true);
if (!is_array($in)) done();

$site = in_array($in['s'] ?? '', ['g', 'q', 'p'], true) ? $in['s'] : 'g';
$path = strtolower((string)($in['p'] ?? ''));
$path = preg_replace('~[^a-z0-9/_\-.]~', '', $path);
$path = preg_replace('~/\d{2,}~', '/n', $path);            // números (ids, níveis) não interessam
$path = substr(trim($path, '/'), 0, 60);
$page = $site . ':' . ($path === '' ? 'inicio' : $path);
$ref = strtolower((string)($in['r'] ?? ''));
$ref = preg_match('/^[a-z0-9.-]{3,60}$/', $ref) ? preg_replace('/^www\./', '', $ref) : '';
$lang = preg_match('/^[a-z]{2}(-[A-Z]{2})?$/', (string)($in['l'] ?? '')) ? $in['l'] : '?';
$dev = ($in['m'] ?? '') === 'm' ? 'telemóvel' : 'computador';
$first = !empty($in['f']);

if (!is_dir(ST_DIR)) @mkdir(ST_DIR, 0775, true);
$cacheHt = dirname(ST_DIR) . DIRECTORY_SEPARATOR . '.htaccess';
if (!is_file($cacheHt)) {
    // a mesma proteção que o market.php põe na cache
    @file_put_contents($cacheHt, "Require all denied\n\n<FilesMatch \".\">\n\tRequire all denied\n</FilesMatch>\n");
}

$day = gmdate('Y-m-d');
$file = ST_DIR . DIRECTORY_SEPARATOR . 'stats-' . $day . '.json';
$h = @fopen($file, 'c+');
if (!$h) done();
flock($h, LOCK_EX);
$d = json_decode((string)stream_get_contents($h), true);
$new = !is_array($d);
if ($new) $d = ['dia' => $day, 'aberturas' => 0, 'paginas' => 0, 'uv' => [], 'rotas' => [], 'origens' => [], 'linguas' => [], 'aparelhos' => []];

// sal do dia: aleatório, guardado só hoje (o de ontem é apagado), para o código do visitante não durar mais de um dia
$saltFile = ST_DIR . DIRECTORY_SEPARATOR . 'sal-' . $day . '.txt';
$salt = @file_get_contents($saltFile);
if (!$salt) { $salt = bin2hex(random_bytes(16)); @file_put_contents($saltFile, $salt); }
$ip = (string)($_SERVER['REMOTE_ADDR'] ?? '');
$vid = substr(hash('sha256', $salt . '|' . $ip . '|' . $ua), 0, 16);

$bump = function (array &$a, string $k): void {
    if (!isset($a[$k]) && count($a) >= ST_MAXKEYS) $k = '(outras)';
    $a[$k] = ($a[$k] ?? 0) + 1;
};
$d['paginas']++;
if ($first) { $d['aberturas']++; $bump($d['origens'], $ref === '' ? '(direto)' : $ref); }
$d['uv'][$vid] = 1;
$bump($d['rotas'], $page);
$bump($d['linguas'], $lang);
$bump($d['aparelhos'], $dev);

ftruncate($h, 0);
rewind($h);
fwrite($h, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_FORCE_OBJECT));
fflush($h);
flock($h, LOCK_UN);
fclose($h);

if ($new) {
    // primeiro pedido do dia: fecha os dias anteriores (códigos → contagem), apaga sais velhos e dias com mais de 400 dias
    foreach (glob(ST_DIR . DIRECTORY_SEPARATOR . 'sal-*.txt') ?: [] as $f) if ($f !== $saltFile) @unlink($f);
    $limit = gmdate('Y-m-d', time() - ST_KEEP * 86400);
    foreach (glob(ST_DIR . DIRECTORY_SEPARATOR . 'stats-*.json') ?: [] as $f) {
        if ($f === $file) continue;
        $dd = substr(basename($f, '.json'), 6);
        if ($dd < $limit) { @unlink($f); continue; }
        $o = @fopen($f, 'c+');
        if (!$o) continue;
        flock($o, LOCK_EX);
        $x = json_decode((string)stream_get_contents($o), true);
        if (is_array($x) && is_array($x['uv'] ?? null)) {
            $x['visitantes'] = count($x['uv']);
            unset($x['uv']);
            ftruncate($o, 0); rewind($o);
            fwrite($o, json_encode($x, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_FORCE_OBJECT));
            fflush($o);
        }
        flock($o, LOCK_UN);
        fclose($o);
    }
}
done();
