# Capa navideña del Concello — búsqueda (R-06)

> Rellenado por `R-06`. Es una **línea base opcional** para `R-01`, no una
> dependencia: v1 no depende de esta capa (ver «Decisión»).
> Búsqueda del 2026-11-14, una petición cada vez, con pausas de 1–2 s.

## Resultado: **encontrada**

El Concello publica la Navidad en su organización de **ArcGIS Online**
(`vigo.maps.arcgis.com`, orgid `ss3qikvq575kYKRJ`), no en el CKAN.

| | Valor |
|---|---|
| Item | «Puntos interés Navidad 2026 2027» (`41caae2067564a92a79d91f5a08c00f6`, público) |
| Feature Service | `https://services9.arcgis.com/ss3qikvq575kYKRJ/arcgis/rest/services/Puntos_interés_Navidad_2023_2024/FeatureServer/0` |
| Descarga | `…/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson` |
| Última modificación | 2026-11-13 (`modified` 1794576310000) |
| Puntos | 35 |
| Licencia | **no declarada** en el item (`licenseInfo` vacío) |

> Ojo: el nombre del servicio dice `2023_2024` pero el título y la
> descripción dicen 2026-2027 — el Concello reutiliza el servicio cada año.
> Identificar la temporada por el **título/modificación**, no por la URL.

### Campos

`id`, `nombre`/`nombre_gl`, `descripcion_corta(_gl)`, `descripcion_larga(_gl)`
(HTML), `horario_atencion(_gl)` (HTML, lista), `tipologia(_gl)`, `image_url`,
`dir_nombre_via`, `dir_numero`, `dir_cod_postal`, `dir_barrio`, `dir_distrito`,
`telefono1/2`, `web`, `email`, `lon`, `lat`.

Útil para `I18N-01`: trae español y gallego de serie.

### Contenido por tipología

| Tipología | Nº |
|---|---|
| Elementos lumínicos | 16 |
| Atracciones | 8 |
| Elementos expositivos | 4 |
| Mercados navideños | 2 |
| Papa Noel - Reyes Magos | 2 |
| Galerías de fotos | 2 |
| Photocalls | 1 |

Incluye los hitos de `R-02`: Árbol gigante (Porta do Sol, 46,40 m, horario de
encendido/apagado y animaciones musicales), Noria Gigante, Cíes Market (Plaza
de Vialia), Experiencia «Dentro de Disney+», Pista de Hielo y Karts (Samil),
Circo (desde el 5 de diciembre), Nadal Bus, Tren de Navidad (Vialia).

12 de los 35 puntos **no tienen horario** (photocall de Urzáiz, Nacimiento
Luminoso, Renos, Disney+, galerías de fotos…): `R-04` debe completarlos.

## Comparación con `points.json`

`points.json` todavía no existe (lo produce `R-01`). Cuando exista, comparar
por nombre + distancia (< 50 m) y registrar en el log de investigación los
puntos que solo están en una de las dos fuentes. Mientras tanto, esta capa
cuenta como **una de las ≥3 fuentes** de `R-01` para cada punto que incluya,
con prioridad de fuente oficial.

## Otras capas del mismo portal (no usadas)

- Años anteriores: «Nadal/Navidad Vigo 2019», «Mapa Nadal / Navidad Vigo
  2020», «Puntos interés Navidad 2021», «Nadal2023 _ Punto de interés».
  Sirven para «puntos del año pasado» de `R-01`.
- «Navidad 2026-2027 3D» (Web Scene `ed9c99f27fab41359624d918a0f63d01`) y
  «Gemelo digital 3D Nadal 2025»: candidatos para `X-05`.
- «Plan de movilidad de la Navidad» (StoryMap) y
  «zona_trafico_restringido_nadal23»: cortes de tráfico, fuera de alcance v1.
- «Web Experience Nadal 2025 - 2026»: el visor oficial que consume la capa.

## Lo que se intentó, en orden

1. **CKAN** (`https://datos-ckan.vigo.org/api/3/action/package_search`):
   `nadal`, `luces`, `luzes`, `navidad`, `iluminacion`, `atracciones`,
   `photocall`, `eventos` → 0 resultados. `mercado` → 2 datasets
   (`comercio-mercados`, `turismo-com-mercados`): solo mercados de abastos,
   nada navideño. (`datos.vigo.org/api/3/…` es WordPress y devuelve 404: el
   CKAN vive en `datos-ckan.vigo.org`.)
2. **Agenda** (`agenda-hoy.json`): 1 evento navideño hoy, «Acto de encendido
   de luces de Navidad» en Porta do Sol, sin coordenadas ni hora.
3. **Mapas del portal** (`datos.vigo.org/maps/`) → enlaza `mapas.vigo.org`,
   `mapas-vigo.opendata.arcgis.com` y la galería de `vigo.maps.arcgis.com`.
4. **ArcGIS Online** (`arcgis.com/sharing/rest/search … orgid:ss3qikvq575kYKRJ`):
   `nadal` → 21 items, `navidad` → 26; `luces`/`luzes` → 0. Aquí está la capa.
5. Un mapa de prensa (metropolitano.gal) no se inspeccionó: su certificado
   TLS no valida y no es fuente oficial.

No hizo falta el canal de solicitud. Si la capa desaparece, el canal es
«Solicitude de Datos Abertos» en el menú «Uso de datos» de `datos.vigo.org`.

## Decisión

- **No se crea dependencia** de esta capa: la URL incluye un año antiguo y el
  Concello puede renombrarla o retirarla. `R-01` la usa como semilla y fuente;
  la app lee `points.json`, nunca el Feature Service.
- **Licencia sin declarar:** no se commitean los datos en bruto. Hasta aclararlo
  (`LIC-01`), se cita como «Concello de Vigo — vigo.maps.arcgis.com» y se
  usan hechos (ubicación, horario), no textos ni imágenes.

## Re-consultar

```bash
curl -s "https://services9.arcgis.com/ss3qikvq575kYKRJ/arcgis/rest/services/Puntos_inter%C3%A9s_Navidad_2023_2024/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson" -o navidad.geojson
```
