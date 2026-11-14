// Screenshot a page with headless Brave over the DevTools protocol (Node 22+, no dependencies).
// usage: node scripts/shot.mjs <url> <out.png> [width=1400] [height=900] [waitMs=4000] [mobile=0] [js-to-run-before-shot]
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [url, out, w = "1400", h = "900", wait = "4000", mobile = "0", js = ""] = process.argv.slice(2);
const port = 9300 + Math.floor(Math.random() * 500);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "shot-"));
const brave = spawn("brave-browser", [
  "--headless=new", "--disable-gpu", "--no-sandbox", `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function pageWs() {
  for (let i = 0; i < 50; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      const p = list.find((x) => x.type === "page");
      if (p) return p.webSocketDebuggerUrl;
    } catch {}
    await sleep(200);
  }
  throw new Error("brave did not start");
}

try {
  const ws = new WebSocket(await pageWs());
  await new Promise((r) => (ws.onopen = r));
  let id = 0;
  const pending = new Map();
  const logs = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
    if (d.method === "Runtime.consoleAPICalled") logs.push(d.params.args.map((a) => a.value ?? a.description).join(" "));
    if (d.method === "Runtime.exceptionThrown") logs.push("EXC " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text));
  };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: +w, height: +h, deviceScaleFactor: mobile === "1" ? 2 : 1, mobile: mobile === "1" });
  if (mobile === "1") await send("Emulation.setTouchEmulationEnabled", { enabled: true });
  await send("Page.navigate", { url });
  await sleep(+wait);
  if (js) { const r = await send("Runtime.evaluate", { expression: js, awaitPromise: true, returnByValue: true }); logs.push("js: " + JSON.stringify(r.result?.result?.value)); await sleep(1200); }
  const shot = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(out, Buffer.from(shot.result.data, "base64"));
  console.log("wrote", out, logs.length ? "\nconsole:\n" + logs.join("\n") : "");
  ws.close();
} finally {
  brave.kill();
  await sleep(300);
  try { fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5 }); } catch {}
}
