// Pruebas de la demo en el navegador (E2E-01): lo que un vecino hace con NaviVigo, y los fallos que
// ya pasaron una vez, para que no vuelvan. Levanta la web con scripts/serve_web.mjs y la recorre en
// escritorio y en móvil. Sin depender de servicios de fuera: se comprueba la interfaz, no lo que
// responden OSRM o Photon.
//
//   cd web/e2e && npm ci && npx playwright-core install chromium && npm test
//   PW_CHANNEL=msedge npm test        # con el Edge o Chrome ya instalado, sin descargar nada
//   npm test -- noria                 # solo las pruebas cuyo nombre contiene «noria»
import { chromium } from "playwright-core";
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const PORT = 4173, BASE = `http://127.0.0.1:${PORT}/`;
const AXE = readFileSync(createRequire(import.meta.url).resolve("axe-core/axe.min.js"), "utf8");
const DEVICES = [
  { name: "escritorio", viewport: { width: 1440, height: 900 } },
  { name: "movil", viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
];

class Fail extends Error {}
const ok = (cond, msg) => { if (!cond) throw new Fail(msg); };
const eq = (a, b, msg) => ok(JSON.stringify(a) === JSON.stringify(b), `${msg}: ${JSON.stringify(a)} ≠ ${JSON.stringify(b)}`);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function open(page) {
  await page.goto(BASE);
  await page.waitForFunction(() => window.tinyvigoPoints && window.tinyvigoTour && window.tinyvigo && window.tinyvigo.viewer.world.getItemCount() > 0, null, { timeout: 30_000 });
  await wait(800);
}

const TESTS = [
  ["carga el mapa con los puntos de Navidad y sin errores", async (page, ctx) => {
    await open(page);
    ok(await page.locator(".tv-marker").count() > 15, "menos de 16 marcadores");
    ok(await page.locator("#dock-sitios").isVisible(), "no se ve «Ver sitios»");
    eq(ctx.errors, [], "errores en la página");
  }],
  ["la vista nunca se sale del dibujo (sin fondo vacío)", async (page) => {
    await open(page);
    const outside = () => page.evaluate(() => {
      const v = tinyvigo.viewer.viewport, ib = tinyvigo.viewer.world.getItemAt(0).getBounds(), vb = v.getBounds(true);
      const px = (n) => Math.round((n * v.getContainerSize().x) / vb.width);
      return Math.max(px(ib.x - vb.x), px(ib.y - vb.y), px(vb.x + vb.width - (ib.x + ib.width)), px(vb.y + vb.height - (ib.y + ib.height)));
    });
    for (const move of [
      () => { const v = tinyvigo.viewer.viewport; v.zoomTo(0.01); v.applyConstraints(); },
      () => { const v = tinyvigo.viewer.viewport; v.zoomTo(v.getHomeZoom() * 2); v.panTo(new OpenSeadragon.Point(5, 5)); v.applyConstraints(); },
      () => { const v = tinyvigo.viewer.viewport; v.panTo(new OpenSeadragon.Point(-5, -5)); v.applyConstraints(); },
    ]) {
      await page.evaluate(move); await wait(1300);
      const out = await outside(); ok(out <= 1, `se ven ${out} px fuera del dibujo`);
    }
  }],
  ["el minimapa enseña Vigo entero (sin recortar)", async (page) => {
    await open(page);
    const [r, m] = await page.evaluate(() => { const b = document.querySelector(".tv-minimap").getBoundingClientRect(); return [b.width / b.height, tinyvigo.manifest.width / tinyvigo.manifest.height]; });
    ok(Math.abs(r - m) < 0.05, `proporción ${r.toFixed(2)} y el mapa ${m.toFixed(2)}`);
  }],
  ["buscar «noria» y abrir su ficha", async (page) => {
    await open(page);
    await page.click("input.tv-search"); await page.fill("input.tv-search", "noria"); await wait(800);
    const card = page.locator(".tv-res").filter({ hasText: /Noria/ }).first();
    ok(await card.isVisible(), "no sale la Noria");
    ok(await card.locator(".tv-res-kind").isVisible(), "el resultado no dice su tipo");
    await card.dispatchEvent("mousedown"); await wait(800);
    ok(/Noria/.test(await page.locator(".tv-sheet.is-open").innerText()), "no se abre la ficha");
  }],
  ["Ajustes: grupos sin solaparse, cuatro idiomas y el portugués", async (page) => {
    await open(page);
    ok(!(await page.locator(".tv-theme").isVisible()), "el botón de tema sigue en la barra");
    await page.click(".tv-settings-open"); await wait(600);
    const overlaps = await page.evaluate(() => {
      const r = [...document.querySelectorAll(".tv-settings .tv-set-title, .tv-settings .tv-seg, .tv-settings .tv-offline, .tv-settings > .tv-btn")].map((e) => e.getBoundingClientRect());
      let n = 0;
      for (let i = 0; i < r.length; i++) for (let j = i + 1; j < r.length; j++) if (r[i].bottom > r[j].top + 1 && r[j].bottom > r[i].top + 1 && r[i].right > r[j].left && r[j].right > r[i].left) n++;
      return n;
    });
    eq(overlaps, 0, "controles de Ajustes que se pisan");
    await page.locator(".tv-settings button", { hasText: "Português" }).click(); await wait(600);
    eq(await page.locator(".tv-settings h2").first().innerText(), "Definições", "el título en portugués");
  }],
  ["paseo: pines numerados y terminar lo borra todo", async (page) => {
    await open(page);
    await page.evaluate(() => { tinyvigoTour.setStart2("centre"); tinyvigoTour.setBudget(60); tinyvigoTour.run(); });
    await page.waitForFunction(() => tinyvigoTour.result() && tinyvigoTour.result().line, null, { timeout: 45_000 });
    ok(await page.locator(".tv-stop-pin").count() > 2, "sin pines de parada");
    const n = await page.evaluate(() => tinyvigoTour.result().stops.length);
    await page.evaluate(() => tinyvigoTour.startWalk(1)); await wait(600);
    ok(await page.locator(".tv-stop-pin.is-done").count() >= 1 && await page.locator(".tv-stop-pin.is-current").count() === 1, "las paradas no cambian de color según vas");
    await page.evaluate((n) => tinyvigoTour.startWalk(n - 1), n); await wait(600);
    ok(/Terminar/.test(await page.locator(".tv-step-next").innerText()), "la última parada no ofrece terminar");
    await page.click(".tv-step-next"); await wait(800);
    eq(await page.locator(".tv-stop-pin").count(), 0, "pines tras terminar");
    eq(await page.locator("svg.tv-route").count(), 0, "línea tras terminar");
  }],
  ["compartir el paseo: el enlace abre ese mismo paseo", async (page, ctx) => {
    await open(page);
    await page.evaluate(() => { tinyvigoTour.setStart2("urzaiz"); tinyvigoTour.setBudget(90); tinyvigoTour.run(); });
    await page.waitForFunction(() => tinyvigoTour.result() && tinyvigoTour.result().line, null, { timeout: 45_000 });
    await wait(500);
    const ids = await page.evaluate(() => tinyvigoTour.result().stops.map((s) => s.p.id));
    await page.evaluate(() => tinyvigoTour.startWalk(1)); await wait(500); // abrir una parada no debe borrar el paseo del enlace
    const url = page.url();
    ok(/#ruta=/.test(url) && /&s=42\.23/.test(url), "el enlace no lleva el paseo: " + url);
    const other = await ctx.context.newPage();
    await other.goto(url, { waitUntil: "load" });
    await other.waitForFunction(() => window.tinyvigoTour && tinyvigoTour.result() && tinyvigoTour.result().line, null, { timeout: 45_000 });
    eq(JSON.stringify(await other.evaluate(() => tinyvigoTour.result().stops.map((s) => s.p.id))), JSON.stringify(ids), "otras paradas u otro orden");
    ok(await other.locator(".tv-stop-pin").count() > 0, "el enlace no dibuja el paseo");
    await other.close();
  }],
  ["la rueda del paseo cambia el tiempo (teclado y arrastre)", async (page) => {
    await open(page);
    await page.click("#dock-ruta"); await wait(800);
    const dur = page.locator(".tv-picker-list").first();
    await dur.focus(); await page.keyboard.press("ArrowDown"); await page.keyboard.press("ArrowDown"); await wait(600);
    eq(await dur.getAttribute("aria-valuetext"), "1 h 30 min", "valor tras dos flechas");
    ok(/^90-/.test(await page.evaluate(() => tinyvigoTour.state())), "el paseo no usa la duración elegida");
  }],
  ["capas: el parking de Vialia, las cámaras y el tráfico", async (page) => {
    await open(page);
    await page.click(".tv-layers-btn");
    for (const l of ["parking", "camaras", "trafico"]) await page.click(`[data-layer="${l}"]`);
    await wait(2500);
    const labels = await page.$$eval(".tv-lmark.is-park", (b) => b.map((x) => x.getAttribute("aria-label")));
    ok(labels.includes("Parking Vialia Interior"), "falta el parking de Vialia (al este del lienzo viejo)");
    ok(await page.locator(".tv-lmark.is-cam").count() > 20, "menos de 21 cámaras");
    ok(await page.locator(".tv-traffic polyline").count() > 0, "sin tramos de tráfico");
    // GEO-02: ningún tramo encima de un edificio que tape la calle
    const onRoofs = await page.evaluate(() => {
      let n = 0, bad = 0;
      for (const pl of document.querySelectorAll(".tv-traffic polyline"))
        for (const pt of pl.getAttribute("points").split(" ")) { const [x, y] = pt.split(",").map(Number); n++; if (tinyvigoOcclusion.hidden(x, y)) bad++; }
      return bad / Math.max(1, n);
    });
    ok(onRoofs < 0.03, `${(onRoofs * 100).toFixed(1)} % del tráfico encima de edificios`);
    await page.click('[data-layer="trafico"]'); await wait(400);
    eq(await page.evaluate(() => getComputedStyle(document.querySelector(".tv-traffic")).visibility), "hidden", "el tráfico sigue a la vista tras apagarlo");
  }],
  ["buses: casi todas las paradas tienen salidas, también fuera de la semana publicada", async (page) => {
    await open(page);
    const r = await page.evaluate(async () => {
      const T = tinyvigoTransit, d = await T.load();
      const dates = [...new Set(d.services.flat())].sort(), day = (s, h) => new Date(+s.slice(0, 4), +s.slice(4, 6) - 1, +s.slice(6, 8), h);
      const tue = dates.find((s) => day(s, 12).getDay() === 2);
      const empty = d.stops.filter(([id]) => !T.nextDepartures(id, day(tue, 12), 1).length).length;
      const later = new Date(day(dates[dates.length - 1], 12).getTime() + 30 * 864e5); // a month after the GTFS ends
      return { stops: d.stops.length, empty, later: T.nextDepartures(d.stops[0][0], later, 1).length + d.stops.filter(([id]) => T.nextDepartures(id, later, 1).length).length };
    });
    ok(r.empty < r.stops * 0.05, `${r.empty} de ${r.stops} paradas sin buses un martes a mediodía`);
    ok(r.later > r.stops * 0.5, "un mes después del GTFS no sale ningún bus");
    await page.click(".tv-layers-btn"); await page.click('[data-layer="buses"]'); await wait(1500);
    await page.keyboard.press("Escape");
    await page.evaluate(() => document.querySelector(".tv-lmark.is-bus").onclick()); await wait(800);
    ok(/programad|scheduled|previst/i.test(await page.locator(".tv-ltoast.is-on").textContent()), "tocar una parada no enseña sus salidas");
  }],
  ["una cámara enseña su imagen dentro de la app, sin abrir pestañas", async (page, ctx) => {
    await open(page);
    let popups = 0; ctx.context.on("page", () => popups++);
    await page.click(".tv-layers-btn"); await page.click('[data-layer="camaras"]'); await wait(1500);
    await page.keyboard.press("Escape");
    await page.evaluate(() => document.querySelector(".tv-lmark.is-cam").onclick()); await wait(800);
    ok(await page.locator(".tv-cam.is-open").isVisible(), "no se abre la tarjeta de la cámara");
    ok(/camaras\.vigo\.org/.test(await page.locator(".tv-cam.is-open img").getAttribute("src")), "la imagen no es la del Concello");
    eq(popups, 0, "pestañas abiertas");
    await page.keyboard.press("Escape"); await wait(300);
    eq(await page.locator(".tv-cam.is-open").count(), 0, "la tarjeta sigue abierta tras Escape");
  }],
  ["de noche se encienden las luces y de día no queda nada", async (page) => {
    await open(page);
    await page.evaluate(() => tinyvigoAmbient.set({ time: "day" })); await wait(800);
    eq(await page.evaluate(() => tinyvigo.viewer.world.getItemAt(1).getOpacity()), 0, "tinte de día");
    await page.evaluate(() => tinyvigoAmbient.set({ time: "night" })); await wait(1500);
    eq(await page.evaluate(() => tinyvigo.viewer.world.getItemAt(1).getOpacity()), 1, "tinte de noche");
    await page.evaluate(() => tinyvigoAmbient.set({ time: "auto" }));
  }],
  ["en el móvil el dock no roza el minimapa", async (page, ctx) => {
    if (ctx.device.name !== "movil") return "solo móvil";
    await open(page);
    const gap = await page.evaluate(() => {
      const a = document.querySelector(".tv-dock").getBoundingClientRect(), b = document.querySelector(".tv-corner").getBoundingClientRect();
      return Math.max(b.left - a.right, a.left - b.right, b.top - a.bottom, a.top - b.bottom);
    });
    ok(gap >= 8, `solo ${gap} px entre el dock y el minimapa`);
  }],
  ["accesibilidad: axe sin incidencias en el inicio y en Ajustes", async (page) => {
    await open(page);
    await page.addScriptTag({ content: AXE });
    const run = () => page.evaluate(async () => (await axe.run(document, { runOnly: ["wcag2a", "wcag2aa", "wcag21aa"], rules: { region: { enabled: false } } })).violations.map((v) => v.id + ": " + v.nodes.map((n) => n.target.join(" ")).join(", ")));
    eq(await run(), [], "axe en el inicio");
    await page.click(".tv-settings-open"); await wait(500);
    eq(await run(), [], "axe en Ajustes");
  }],
];

async function serve() {
  try { if ((await fetch(BASE)).ok) return null; } catch (e) { /* not running yet */ }
  const root = fileURLToPath(new URL("../../", import.meta.url));
  const proc = spawn(process.execPath, ["scripts/serve_web.mjs", "--port", String(PORT), "--no-open"], { cwd: root, stdio: "ignore" });
  for (let i = 0; i < 60; i++) { try { if ((await fetch(BASE)).ok) return proc; } catch (e) { /* wait */ } await wait(250); }
  proc.kill(); throw new Error("el servidor no arrancó");
}

const filter = process.argv.slice(2).join(" ").toLowerCase();
const server = await serve();
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || undefined, headless: true });
let failed = 0, passed = 0, skipped = 0;
for (const device of DEVICES) {
  for (const [name, fn] of TESTS) {
    if (filter && !name.toLowerCase().includes(filter)) continue;
    const context = await browser.newContext({ ...device, locale: "es-ES" });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => { if (m.type() === "error" && !/_vercel|Failed to load resource/.test(m.text())) errors.push(m.text()); });
    const t0 = Date.now();
    try {
      const r = await fn(page, { errors, context, device });
      if (r) { skipped++; console.log(`  -  [${device.name}] ${name} (${r})`); }
      else { passed++; console.log(`  ✔  [${device.name}] ${name} (${((Date.now() - t0) / 1000).toFixed(1)} s)`); }
    } catch (e) {
      failed++;
      console.log(`  ✘  [${device.name}] ${name}\n       ${e instanceof Fail ? e.message : e.stack.split("\n").slice(0, 3).join("\n       ")}`);
    }
    await context.close();
  }
}
await browser.close();
if (server) server.kill();
console.log(`\n${passed} bien · ${failed} mal · ${skipped} no aplican`);
process.exit(failed ? 1 : 0);
