<?php
/*
 * Grimório de Tibia — preços do Market por mundo.
 * Proxy com cache da API pública do TibiaMarket (https://api.tibiamarket.top:8001).
 *
 *   GET market.php?world=Bona
 *
 * 200 {"world":"Bona","updated":<unix do scan mais recente>,"fetched":<unix do pedido à origem>,
 *      "stale":false,"items":{"<id>":[sell_offer,buy_offer,month_average_sell,month_average_buy,
 *                                     day_average_sell,day_average_buy,month_sold,month_bought]}}
 *     (só itens com algum valor > 0; -1 da origem passa a 0; "stale":true = cache antiga servida
 *      porque a origem falhou ou está em limite de pedidos)
 * 400 nome inválido · 404 mundo desconhecido/sem dados (não guarda cache) · 503 sem cache e sem origem
 * Cabeçalho X-Cache: HIT (cache válida), MISS (acabou de ir à origem), STALE (cache antiga), ERROR.
 *
 * A origem aceita ~1 pedido a cada 5 s por IP: todos os pedidos à origem passam por um
 * cadeado global (cache/origin.lock) que guarda o instante a partir do qual se pode voltar
 * a pedir. Cada mundo tem o seu cadeado (cache/market-<World>.lock) para nunca haver dois
 * pedidos em simultâneo ao mesmo mundo. A lista de mundos do TibiaMarket (cache/worlds.json,
 * 24 h) filtra nomes inventados sem gastar pedidos à origem.
 */
declare(strict_types=1);

ini_set('display_errors', '0');
ini_set('log_errors', '1');
error_reporting(E_ALL);
set_time_limit(90);
ignore_user_abort(true); // um pedido à origem já iniciado termina e grava a cache

const MK_TTL        = 21600;  // cache dos preços: 6 h
const MK_WORLDS_TTL = 86400;  // lista de mundos: 24 h
const MK_GAP        = 5.5;    // segundos entre pedidos à origem
const MK_BACKOFF    = 120;    // segundos sem voltar a tentar depois de uma falha
const MK_TIMEOUT    = 25;
const MK_BASE       = 'https://api.tibiamarket.top:8001';
const MK_UA         = 'GrimorioDeTibia/1.0 (fan site)';
const MK_FIELDS     = ['sell_offer', 'buy_offer', 'month_average_sell', 'month_average_buy',
                       'day_average_sell', 'day_average_buy', 'month_sold', 'month_bought'];
const MK_JSON       = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES;

define('MK_DIR', __DIR__ . DIRECTORY_SEPARATOR . 'cache');

/* ---------- resposta ---------- */

function send(int $code, string $body, string $cacheControl, string $tag, array $extra = []): never
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: ' . $cacheControl);
    header('Access-Control-Allow-Origin: *');
    header('X-Content-Type-Options: nosniff');
    header('X-Cache: ' . $tag);
    foreach ($extra as $h) {
        header($h);
    }
    if ($code !== 304) {
        echo $body;
    }
    exit;
}

function fail(int $code, string $msg, string $cacheControl, array $extra = []): never
{
    send($code, json_encode(['error' => $msg], MK_JSON), $cacheControl, 'ERROR', $extra);
}

function valid_body($body): bool
{
    return is_string($body) && strncmp($body, '{"world":', 9) === 0 && substr($body, -2) === '}}';
}

/** Serve o ficheiro de cache; devolve false se não existir ou estiver estragado. */
function serve_cache(string $file, bool $stale, string $tag): bool
{
    $body = @file_get_contents($file);
    if (!valid_body($body)) {
        return false;
    }
    if ($stale) {
        $p = strpos($body, '"stale":false');
        if ($p !== false) {
            $body = substr_replace($body, '"stale":true', $p, 13);
        }
    }
    $mtime = (int) @filemtime($file);
    $extra = ['Last-Modified: ' . gmdate('D, d M Y H:i:s', $mtime) . ' GMT'];
    $ims = $_SERVER['HTTP_IF_MODIFIED_SINCE'] ?? '';
    $code = ($ims !== '' && ($t = strtotime($ims)) !== false && $t >= $mtime) ? 304 : 200;
    send($code, $body, $stale ? 'public, max-age=300' : 'public, max-age=1800', $tag, $extra);
}

/* ---------- ficheiros e cadeados ---------- */

function write_atomic(string $file, string $data): bool
{
    $tmp = $file . '.' . bin2hex(random_bytes(4)) . '.tmp';
    if (@file_put_contents($tmp, $data) !== strlen($data)) {
        @unlink($tmp);
        return false;
    }
    for ($i = 0; $i < 10; $i++) {
        if (@rename($tmp, $file)) {
            return true;
        }
        usleep(100000);
    }
    @unlink($tmp);
    return false;
}

/** @return resource|null */
function lock_open(string $file)
{
    $h = @fopen($file, 'c+');
    return $h ?: null;
}

function lock_wait($h, float $seconds): bool
{
    $end = microtime(true) + $seconds;
    do {
        if (flock($h, LOCK_EX | LOCK_NB)) {
            return true;
        }
        usleep(200000);
    } while (microtime(true) < $end);
    return false;
}

function lock_read($h): float
{
    rewind($h);
    return (float) trim((string) stream_get_contents($h));
}

function lock_write($h, float $value): void
{
    ftruncate($h, 0);
    rewind($h);
    fwrite($h, sprintf('%.3f', $value));
    fflush($h);
}

function lock_release($h): void
{
    flock($h, LOCK_UN);
    fclose($h);
}

/* ---------- origem ---------- */

/**
 * GET à origem, respeitando o limite global de pedidos.
 * @return array{0:int,1:?string,2:int} [estado HTTP (0 = erro de rede, 429 = limite), corpo, segundos até poder tentar]
 */
function origin_get(string $path): array
{
    $g = lock_open(MK_DIR . DIRECTORY_SEPARATOR . 'origin.lock');
    if (!$g) {
        return [0, null, MK_BACKOFF];
    }
    if (!lock_wait($g, 40)) {           // fila demasiado longa
        fclose($g);
        return [429, null, 30];
    }
    $wait = lock_read($g) - microtime(true);
    if ($wait > 30) {                    // a origem pediu para esperar muito
        lock_release($g);
        return [429, null, (int) ceil($wait)];
    }
    if ($wait > 0) {
        usleep((int) ($wait * 1e6));
    }

    $retryAfter = null;
    $ch = curl_init(MK_BASE . $path);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => MK_TIMEOUT,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_USERAGENT      => MK_UA,
        CURLOPT_HTTPHEADER     => ['Accept: application/json'],
        CURLOPT_ENCODING       => '',      // aceita gzip
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_PROTOCOLS      => CURLPROTO_HTTPS,
        CURLOPT_HEADERFUNCTION => function ($ch, string $line) use (&$retryAfter): int {
            if (stripos($line, 'Retry-After:') === 0) {
                $retryAfter = (int) trim(substr($line, 12));
            }
            return strlen($line);
        },
    ]);
    $body = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    curl_close($ch);

    $gap = MK_GAP;
    if ($code === 429) {
        $gap = max(MK_GAP, (float) ($retryAfter ?? 5) + 0.5);
    }
    lock_write($g, microtime(true) + $gap);
    lock_release($g);

    if ($body === false || $errno) {
        error_log("grimorio market: origem falhou ($path): [$errno] $error");
        return [0, null, MK_BACKOFF];
    }
    if ($code !== 200) {
        error_log("grimorio market: origem respondeu $code ($path)");
    }
    return [$code, $body, $code === 429 ? (int) ceil($gap) : MK_BACKOFF];
}

/* ---------- lista de mundos ---------- */

function norm_world(string $w): string
{
    return ucfirst(strtolower($w));
}

/** @return array<string,array{0:string,1:string}>|null  chave = nome em minúsculas */
function read_worlds(string $file, ?int &$age): ?array
{
    $age = PHP_INT_MAX;
    $raw = @file_get_contents($file);
    if (!is_string($raw)) {
        return null;
    }
    $j = json_decode($raw, true);
    if (!is_array($j) || empty($j['worlds']) || !is_array($j['worlds'])) {
        return null;
    }
    $age = time() - (int) ($j['fetched'] ?? 0);
    return $j['worlds'];
}

/** Mundos que o TibiaMarket conhece; null se a lista não estiver disponível (não filtra). */
function world_list(): ?array
{
    $file = MK_DIR . DIRECTORY_SEPARATOR . 'worlds.json';
    $map = read_worlds($file, $age);
    if ($map !== null && $age < MK_WORLDS_TTL) {
        return $map;
    }
    $h = lock_open(MK_DIR . DIRECTORY_SEPARATOR . 'worlds.lock');
    if (!$h) {
        return $map;
    }
    if (!lock_wait($h, 45)) {
        fclose($h);
        return $map;
    }
    $again = read_worlds($file, $age);
    if ($again !== null && $age < MK_WORLDS_TTL) {
        lock_release($h);
        return $again;
    }
    if (microtime(true) < lock_read($h)) {   // falhou há pouco
        lock_release($h);
        return $map;
    }
    [$code, $body] = origin_get('/world_data');
    $new = [];
    if ($code === 200 && is_string($body)) {
        $rows = json_decode($body, true);
        if (is_array($rows)) {
            foreach ($rows as $r) {
                if (is_array($r) && isset($r['name']) && is_string($r['name'])
                    && preg_match('/^[A-Za-z]{3,20}$/', $r['name'])) {
                    $new[strtolower($r['name'])] = [norm_world($r['name']), (string) ($r['last_update'] ?? '')];
                }
            }
        }
    }
    if ($new) {
        ksort($new);
        write_atomic($file, json_encode(['fetched' => time(), 'worlds' => $new], MK_JSON));
        lock_write($h, 0);
        lock_release($h);
        return $new;
    }
    lock_write($h, microtime(true) + MK_BACKOFF);
    lock_release($h);
    return $map;
}

/* ---------- pedido ---------- */

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($method === 'OPTIONS') {
    send(204, '', 'public, max-age=86400', 'NONE', [
        'Access-Control-Allow-Methods: GET, HEAD, OPTIONS',
        'Access-Control-Max-Age: 86400',
    ]);
}
if ($method !== 'GET' && $method !== 'HEAD') {
    fail(405, 'Só aceita pedidos GET.', 'no-store', ['Allow: GET, HEAD, OPTIONS']);
}

$world = $_GET['world'] ?? '';
if (!is_string($world) || !preg_match('/^[A-Za-z]{3,20}$/', $world)) {
    fail(400, 'Nome de mundo inválido: usa só letras (3 a 20).', 'public, max-age=86400');
}
$world = norm_world($world);

if (!is_dir(MK_DIR)) {
    @mkdir(MK_DIR, 0775, true);
}
if (!is_file(MK_DIR . DIRECTORY_SEPARATOR . '.htaccess')) {
    // o <FilesMatch> é preciso: o .htaccess do grimorio abre os .json com outro <FilesMatch>
    @file_put_contents(MK_DIR . DIRECTORY_SEPARATOR . '.htaccess',
        "Require all denied\n\n<FilesMatch \".\">\n\tRequire all denied\n</FilesMatch>\n");
}

$cache = MK_DIR . DIRECTORY_SEPARATOR . 'market-' . $world . '.json';
$mtime = @filemtime($cache);
$have = $mtime !== false;

// 1) cache válida
if ($have && time() - $mtime < MK_TTL) {
    serve_cache($cache, false, 'HIT');
    $have = false; // ficheiro estragado: vai à origem
}

// 2) nomes inventados não chegam à origem nem criam ficheiros (a origem responde 500,
//    e não lista vazia, a mundos que não conhece). Sem lista de mundos não se arrisca.
if (!$have) {
    $worlds = world_list();
    if ($worlds === null) {
        fail(503, 'Os preços do Market não estão disponíveis de momento. Tenta daqui a pouco.', 'no-store', ['Retry-After: 60']);
    }
    if (!isset($worlds[strtolower($world)])) {
        fail(404, 'Mundo desconhecido no TibiaMarket.', 'public, max-age=3600');
    }
    $world = $worlds[strtolower($world)][0];
}

// 3) cadeado do mundo: só um pedido à origem de cada vez
$lockFile = MK_DIR . DIRECTORY_SEPARATOR . 'market-' . $world . '.lock';
$h = lock_open($lockFile);
if (!$h) {
    if ($have) {
        serve_cache($cache, true, 'STALE');
    }
    fail(503, 'Os preços do Market não estão disponíveis de momento. Tenta daqui a pouco.', 'no-store', ['Retry-After: 30']);
}
if ($have) {
    if (!flock($h, LOCK_EX | LOCK_NB)) {     // outro pedido já está a atualizar
        fclose($h);
        serve_cache($cache, true, 'STALE');
        fail(503, 'Os preços do Market não estão disponíveis de momento. Tenta daqui a pouco.', 'no-store', ['Retry-After: 30']);
    }
} elseif (!lock_wait($h, 60)) {
    fclose($h);
    fail(503, 'Os preços do Market não estão disponíveis de momento. Tenta daqui a pouco.', 'no-store', ['Retry-After: 30']);
}

// outro pedido pode ter acabado de gravar a cache enquanto esperávamos
clearstatcache(true, $cache);
$mtime = @filemtime($cache);
if ($mtime !== false && time() - $mtime < MK_TTL && valid_body(@file_get_contents($cache))) {
    lock_release($h);
    serve_cache($cache, false, 'HIT');
}
$have = $mtime !== false;

$failUntil = lock_read($h);
if (microtime(true) < $failUntil) {           // falhou há pouco: não insistir
    lock_release($h);
    if ($have) {
        serve_cache($cache, true, 'STALE');
    }
    fail(503, 'Os preços do Market não estão disponíveis de momento. Tenta daqui a pouco.', 'no-store',
        ['Retry-After: ' . max(1, (int) ceil($failUntil - microtime(true)))]);
}

// 4) pedido à origem
[$code, $body, $retry] = origin_get('/market_values?server=' . rawurlencode($world) . '&limit=10000');
$rows = ($code === 200 && is_string($body)) ? json_decode($body, true) : null;

if (is_array($rows) && $rows === []) {        // mundo sem dados: não guarda cache
    lock_write($h, 0);
    lock_release($h);
    if ($have) {
        serve_cache($cache, true, 'STALE');
    }
    @unlink($lockFile);
    fail(404, 'Mundo desconhecido no TibiaMarket.', 'public, max-age=3600');
}

if (!is_array($rows) || !array_is_list($rows)) {
    lock_write($h, microtime(true) + max($retry, 30));
    lock_release($h);
    if ($have) {
        serve_cache($cache, true, 'STALE');
    }
    fail(503, 'Os preços do Market não estão disponíveis de momento. Tenta daqui a pouco.', 'no-store',
        ['Retry-After: ' . max(1, $retry)]);
}

$items = [];
$updated = 0.0;
foreach ($rows as $r) {
    if (!is_array($r) || !isset($r['id']) || !is_numeric($r['id'])) {
        continue;
    }
    $id = (int) $r['id'];
    if ($id <= 0) {
        continue;
    }
    if (isset($r['time']) && is_numeric($r['time']) && (float) $r['time'] > $updated) {
        $updated = (float) $r['time'];
    }
    $v = [];
    $any = false;
    foreach (MK_FIELDS as $k) {
        $x = (isset($r[$k]) && is_numeric($r[$k])) ? (int) $r[$k] : 0;
        if ($x < 0) {
            $x = 0;
        }
        if ($x > 0) {
            $any = true;
        }
        $v[] = $x;
    }
    if ($any) {
        $items[$id] = $v;
    }
}
ksort($items, SORT_NUMERIC);
unset($rows, $body);

$out = json_encode([
    'world'   => $world,
    'updated' => (int) $updated,
    'fetched' => time(),
    'stale'   => false,
    'items'   => (object) $items,
], MK_JSON);

if (!write_atomic($cache, $out)) {
    error_log('grimorio market: não consegui gravar ' . $cache);
}
lock_write($h, 0);
lock_release($h);

send(200, $out, 'public, max-age=1800', 'MISS', ['Last-Modified: ' . gmdate('D, d M Y H:i:s') . ' GMT']);
