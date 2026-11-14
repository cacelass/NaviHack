// One image-model call through Vertex with the user's gcloud session (no key in the repo).
// usage: MODEL=gemini-3-pro-image SIZE=4K AR=1:1 LABEL=x node pipeline/imggen.mjs out.png prompt.txt img1 [img2 ...]
// - one call at a time, waits and retries on 429 (the quota is shared)
// - every attempt is appended to pipeline/ledger/image-calls.jsonl (count the "OK" lines)
import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const [out, promptFile, ...imgs] = process.argv.slice(2);
const MODEL = process.env.MODEL || "gemini-3.1-flash-image";
const gcloud = path.join(process.env.HOME, "google-cloud-sdk/bin/gcloud");
const project = process.env.GCP_PROJECT || execSync(`${gcloud} config get-value project`, { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
const ledger = path.join(path.dirname(fileURLToPath(import.meta.url)), "ledger", "image-calls.jsonl");
const log = (status, extra = {}) => fs.appendFileSync(ledger, JSON.stringify({ t: new Date().toISOString(), model: MODEL, label: process.env.LABEL || path.basename(out), size: process.env.SIZE || "default", status, ...extra }) + "\n");
const mime = (f) => (/\.jpe?g$/i.test(f) ? "image/jpeg" : "image/png");

let token;
try { token = execSync(`${gcloud} auth print-access-token`, { stdio: ["ignore", "pipe", "pipe"] }).toString().trim(); }
catch { log("AUTH_EXPIRED"); console.error("gcloud session expired: stop and ask the user to log in again"); process.exit(3); }

const parts = imgs.map((f) => ({ inlineData: { mimeType: mime(f), data: fs.readFileSync(f).toString("base64") } }));
parts.push({ text: fs.readFileSync(promptFile, "utf8") });
const url = `https://aiplatform.googleapis.com/v1beta1/projects/${project}/locations/global/publishers/google/models/${MODEL}:generateContent`;
const imageConfig = { aspectRatio: process.env.AR || "1:1", ...(process.env.SIZE ? { imageSize: process.env.SIZE } : {}) };

for (let attempt = 0; attempt < 8; attempt++) {
  let j;
  try {
    const r = await fetch(url, { method: "POST", headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify({ contents: [{ role: "user", parts }], generationConfig: { responseModalities: ["IMAGE"], imageConfig } }) });
    j = await r.json();
  } catch (e) { log("NETERR", { msg: String(e.message).slice(0, 100) }); await new Promise((r) => setTimeout(r, 15000)); continue; }
  if (j.error?.code === 429) { log("429"); console.log("429, waiting 45 s"); await new Promise((r) => setTimeout(r, 45000)); continue; }
  if (j.error) { log("ERR", { code: j.error.code, msg: String(j.error.message).slice(0, 160) }); console.error("ERR", j.error.code, String(j.error.message).slice(0, 200)); process.exit(1); }
  const img = (j.candidates?.[0]?.content?.parts || []).find((p) => p.inlineData);
  if (!img) { log("NOIMG", { finish: j.candidates?.[0]?.finishReason }); console.error("NOIMG", JSON.stringify(j).slice(0, 300)); process.exit(1); }
  fs.writeFileSync(out, Buffer.from(img.inlineData.data, "base64"));
  log("OK"); console.log("OK", out); process.exit(0);
}
log("GAVE_UP"); console.error("gave up after retries"); process.exit(1);
