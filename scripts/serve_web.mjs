// Servidor estático de web/ para la demo (make website). Node 18+, sin dependencias.
// El http.server de Python en Windows deja respuestas colgadas a mitad con varias
// conexiones a la vez (scripts de 150-250 KB): la primera carga quedaba en blanco.
//   node scripts/serve_web.mjs [--port 8000] [--no-open]
import http from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, resolve, sep } from "node:path";
import { exec } from "node:child_process";
import { fileURLToPath } from "node:url";

const WEB = resolve(fileURLToPath(new URL("../web/", import.meta.url)));
const args = process.argv.slice(2);
const port = Number(args[args.indexOf("--port") + 1]) || 8000;
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".webp": "image/webp",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml",
  ".ttf": "font/ttf", ".woff2": "font/woff2", ".ico": "image/x-icon", ".md": "text/plain; charset=utf-8",
};

const server = http.createServer(async (req, res) => {
  try {
    let path = decodeURIComponent(new URL(req.url, "http://x").pathname);
    if (path.endsWith("/")) path += "index.html";
    const file = normalize(join(WEB, path));
    if (!file.startsWith(WEB + sep) && file !== WEB) { res.writeHead(403).end(); return; }
    const body = await readFile(file);
    res.writeHead(200, { "Content-Type": TYPES[extname(file).toLowerCase()] || "application/octet-stream", "Content-Length": body.length, "Cache-Control": "no-cache" });
    res.end(body);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" }).end("No encontrado");
  }
});

server.listen(port, "127.0.0.1", () => {
  const url = `http://127.0.0.1:${port}/`;
  console.log(`TinyVigo en ${url}  (Ctrl+C para parar)`);
  if (!args.includes("--no-open")) {
    const cmd = process.platform === "win32" ? `start "" "${url}"` : process.platform === "darwin" ? `open ${url}` : `xdg-open ${url}`;
    exec(cmd);
  }
});
