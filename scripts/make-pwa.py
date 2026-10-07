from pathlib import Path
import json, hashlib, struct, zlib, binascii

site = Path("upstream/dist/web")
index = site / "index.html"

def write_png(path: Path, size: int):
    bg = (17, 17, 17, 255)
    fg = (255, 255, 255, 255)
    ink = (17, 17, 17, 255)
    px = bytearray(size * size * 4)

    def put(x, y, rgba):
        if 0 <= x < size and 0 <= y < size:
            i = (y * size + x) * 4
            px[i:i+4] = bytes(rgba)

    # Background.
    for y in range(size):
        for x in range(size):
            put(x, y, bg)

    # Document shape.
    x0, y0 = int(size * 0.28), int(size * 0.18)
    x1, y1 = int(size * 0.72), int(size * 0.82)
    fold = int(size * 0.14)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if x > x1 - fold and y < y0 + fold and (x - (x1 - fold)) > (y - y0):
                continue
            put(x, y, fg)

    # Fold outline/fill.
    for y in range(y0, y0 + fold):
        limit = x1 - fold + (y - y0)
        for x in range(int(limit), x1):
            put(x, y, ink)
    for y in range(y0, y0 + fold):
        for x in range(x1 - fold, x1):
            if x <= x1 - fold + (y - y0):
                put(x, y, fg)

    # Text lines.
    line_h = max(3, int(size * 0.035))
    left = int(size * 0.38)
    right = int(size * 0.63)
    ys = [int(size * 0.47), int(size * 0.57), int(size * 0.67)]
    for idx, yy in enumerate(ys):
        rr = right if idx < 2 else int(size * 0.57)
        for y in range(yy, yy + line_h):
            for x in range(left, rr):
                put(x, y, ink)

    raw = bytearray()
    stride = size * 4
    for y in range(size):
        raw.append(0)
        raw.extend(px[y*stride:(y+1)*stride])

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xffffffff)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)

manifest = {
    "name": "PrintCraft Web",
    "short_name": "PrintCraft",
    "description": "Local-first PDF workbench powered by WebAssembly.",
    "id": "./",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#111111",
    "theme_color": "#111111",
    "categories": ["productivity", "utilities"],
    "icons": [
        {"src": "./icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "./icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "./icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        {"src": "./pwa-icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}
    ]
}
(site / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="112" fill="#111111"/>
<path d="M145 92h151l71 71v257H145z" fill="#fff"/>
<path d="M296 92v71h71" fill="none" stroke="#111111" stroke-width="22" stroke-linejoin="round"/>
<path d="M195 242h122M195 292h122M195 342h86" stroke="#111111" stroke-width="22" stroke-linecap="round"/>
</svg>
"""
(site / "pwa-icon.svg").write_text(icon, encoding="utf-8")
write_png(site / "favicon-16x16.png", 16)
write_png(site / "favicon-32x32.png", 32)
write_png(site / "icon-192.png", 192)
write_png(site / "icon-512.png", 512)
write_png(site / "apple-touch-icon.png", 180)

def write_ico(path: Path, png_paths):
    images = [p.read_bytes() for p in png_paths]
    header = struct.pack("<HHH", 0, 1, len(images))
    entries = []
    offset = 6 + 16 * len(images)
    for p, data in zip(png_paths, images):
        size = int(p.stem.split("-")[1].split("x")[0])
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        entries.append(struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    path.write_bytes(header + b"".join(entries) + b"".join(images))

write_ico(site / "favicon.ico", [
    site / "favicon-16x16.png",
    site / "favicon-32x32.png",
])

html = index.read_text(encoding="utf-8")
head_bits = """
<link rel="manifest" href="./manifest.webmanifest">
<meta name="theme-color" content="#111111">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="PrintCraft">
<link rel="apple-touch-icon" sizes="180x180" href="./apple-touch-icon.png">
<link rel="icon" href="./favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="./favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="./favicon-16x16.png">
<link rel="icon" sizes="192x192" href="./icon-192.png" type="image/png">
<link rel="icon" sizes="512x512" href="./icon-512.png" type="image/png">
<link rel="icon" href="./pwa-icon.svg" type="image/svg+xml">
"""
if 'rel="manifest"' not in html:
    html = html.replace("</head>", head_bits + "</head>")

register = """
<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js", { scope: "./" }).catch(console.error);
  });
}
</script>
"""
if "serviceWorker.register" not in html:
    html = html.replace("</body>", register + "</body>")
index.write_text(html, encoding="utf-8")

precache = []
for p in sorted(site.rglob("*")):
    if p.is_file() and p.name not in {"sw.js"}:
        rel = "./" + p.relative_to(site).as_posix()
        precache.append(rel)

version_seed = "\n".join(
    f"{p}:{hashlib.sha256((site / p[2:]).read_bytes()).hexdigest()}"
    for p in precache
)
version = hashlib.sha256(version_seed.encode()).hexdigest()[:12]

sw = f"""const CACHE = "printcraft-web-{version}";
const PRECACHE = {json.dumps(precache, indent=2)};

self.addEventListener("install", event => {{
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)));
}});

self.addEventListener("activate", event => {{
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k.startsWith("printcraft-web-") && k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
}});

self.addEventListener("fetch", event => {{
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (event.request.mode === "navigate") {{
    event.respondWith(
      fetch(event.request)
        .then(response => {{
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put("./", copy));
          return response;
        }})
        .catch(() => caches.match("./"))
    );
    return;
  }}

  event.respondWith(
    caches.match(event.request).then(cached => {{
      if (cached) return cached;
      return fetch(event.request).then(response => {{
        if (response.ok) {{
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(event.request, copy));
        }}
        return response;
      }});
    }})
  );
}});
"""
(site / "sw.js").write_text(sw, encoding="utf-8")
print(f"PWA prepared with cache {version}, favicon + PWA icons, and {len(precache)} precached files")
