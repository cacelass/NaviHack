// TinyVigo i18n (I18N-01): textos de la interfaz en gl/es/en, sin dependencias.
// Los catálogos son los JSON de esta carpeta; las claves y los huecos {x} son
// los mismos en los tres (lo comprueba tests/test_i18n.py).
//
//   import { t, setLang, getLang, onLangChange } from "../../i18n/i18n";
//   t("common.walk_min", { min: 11 })   // "11 min andando"
//   setLang("gl")                        // recuerda la elección y avisa a los oyentes
//
// En React: const [, rerender] = useState(0); useEffect(() => onLangChange(() => rerender((n) => n + 1)), []);
import es from "./es.json";
import gl from "./gl.json";
import en from "./en.json";

export const LANGS = ["gl", "es", "en"] as const;
export type Lang = (typeof LANGS)[number];
export type Key = keyof typeof es;
export const LANG_NAMES: Record<Lang, string> = { gl: "Galego", es: "Español", en: "English" };

const CATALOGS: Record<Lang, Record<Key, string>> = { es, gl, en };
const STORAGE_KEY = "tinyvigo.lang";
const FALLBACK: Lang = "es";
const listeners = new Set<(lang: Lang) => void>();

function isLang(value: unknown): value is Lang {
  return typeof value === "string" && (LANGS as readonly string[]).includes(value);
}

/** Orden: ?lang= en la URL, elección guardada, idioma del navegador, español. */
export function detectLang(): Lang {
  const fromUrl = new URLSearchParams(globalThis.location?.search ?? "").get("lang");
  if (isLang(fromUrl)) return fromUrl;
  try {
    const saved = globalThis.localStorage?.getItem(STORAGE_KEY);
    if (isLang(saved)) return saved;
  } catch {
    // almacenamiento bloqueado: se sigue con el navegador
  }
  for (const tag of globalThis.navigator?.languages ?? []) {
    const base = tag.toLowerCase().split("-")[0];
    if (isLang(base)) return base;
  }
  return FALLBACK;
}

let current: Lang = detectLang();

export function getLang(): Lang {
  return current;
}

export function setLang(lang: Lang): void {
  if (!isLang(lang) || lang === current) return;
  current = lang;
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, lang);
  } catch {
    // sin almacenamiento la elección dura lo que la pestaña
  }
  if (globalThis.document) globalThis.document.documentElement.lang = lang;
  listeners.forEach((fn) => fn(lang));
}

/** Suscribe a cambios de idioma; devuelve la función para darse de baja. */
export function onLangChange(fn: (lang: Lang) => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** Texto de `key` en el idioma actual, con {huecos} rellenados. Si falta, cae a español y luego a la clave. */
export function t(key: Key, vars: Record<string, string | number> = {}, lang: Lang = current): string {
  const text = CATALOGS[lang][key] ?? CATALOGS[FALLBACK][key] ?? key;
  return text.replace(/\{(\w+)\}/g, (hole, name: string) => (name in vars ? String(vars[name]) : hole));
}
