from pathlib import Path
import json, hashlib

site = Path("upstream/dist/web")
index = site / "index.html"

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
        {"src": "./pwa-icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}
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

html = index.read_text(encoding="utf-8")
head_bits = """
<link rel="manifest" href="./manifest.webmanifest">
<meta name="theme-color" content="#111111">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="PrintCraft">
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
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(PRECACHE))
  );
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
print(f"PWA prepared with cache {version} and {len(precache)} precached files")
