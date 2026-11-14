# Licencias y atribuciones (LIC-01)

> Auditoría del 2026-11-14. **Verificado** = comprobado hoy en la fuente
> (metadatos CKAN/ArcGIS, cabeceras o página de términos). **Por confirmar** =
> licencia conocida pero no comprobada hoy en su página; hay que abrirla antes
> de publicar. Lo consume `D-17` (pantalla «Acerca de»).

## Tabla

| Fuente | Licencia | Texto de atribución | Obligación en imágenes derivadas (tiles/sprites) | Estado | Enlace | Verificado |
|---|---|---|---|---|---|---|
| Concello — parkings, agenda, avisos, GTFS Vitrasa (datos.vigo.org) | ODC-BY 1.0 + condiciones del portal (Lei 37/2007 art. 8) | «Concello de Vigo — datos.vigo.org (ODC-BY)» | Citar fuente **y fecha de última actualización**; no alterar ni desnaturalizar el dato | ✅ permitido con atribución | https://datos.vigo.org/condiciones-de-uso-de-los-datos/ | ✅ CKAN `license_title` + página de condiciones |
| Concello — capa navideña ArcGIS (`41caae20…`) | **No declarada** en el item (`licenseInfo` y `accessInformation` vacíos); público | «Concello de Vigo — Puntos de interés de Navidad 2026-27» | Se aplican por defecto las condiciones generales del portal. Textos y **fotos** (`image_url`) pueden tener derechos de terceros | ⚠️ permitido con atribución para datos; **fotos por confirmar** | https://www.arcgis.com/home/item.html?id=41caae2067564a92a79d91f5a08c00f6 | ✅ metadatos del item |
| Concello — Edificios 3D (`1196c4f7…`, `0dda35d1…`) | **No declarada** en el item | «Concello de Vigo — Edificios 3D» | Es la geometría de los tiles (X-05/RENDER-01): **pedir confirmación escrita** al Concello de que se pueden publicar imágenes derivadas | ⚠️ por confirmar (bloqueante para publicar tiles, no para desarrollar) | https://www.arcgis.com/home/item.html?id=1196c4f7cdfa478eb9ac09b1fffc2576 | ✅ metadatos del item |
| Concello — cámaras de tráfico (X-09): dataset `t-camaras` + imágenes de camaras.vigo.org | Dataset ODC-BY; **imágenes sin licencia declarada** | «Imagen: Concello de Vigo (camaras.vigo.org)» | No se copian ni se hace proxy: `<img>` en directo + enlace a la fuente | ✅ enlaces/hotlink con atribución; ⛔ redistribuir o guardar imágenes | https://datos.vigo.org/ | ✅ CKAN + cabeceras (`img-src *`, `X-Frame-Options: SAMEORIGIN`: no se puede embeber la página en iframe, la imagen sí) |
| Renfe GTFS AV/LD/MD | CC BY 4.0 | «Renfe Operadora (CC BY 4.0)» | No aplica (no se dibuja) | ✅ permitido con atribución | https://data.renfe.com/ | ⚠️ por confirmar en data.renfe.com (licencia según el spec) |
| Open-Meteo (forecast + marine) | Datos CC BY 4.0; **API gratuita solo no comercial**, < 10 000 llamadas/día, 5 000/h, 600/min | «Weather data by Open-Meteo.com» (enlace a open-meteo.com) | No aplica | ✅ permitido con atribución **mientras el uso sea no comercial**; si TinyVigo pasa a comercial → plan de pago o API propia | https://open-meteo.com/en/terms | ✅ página de términos |
| IGN — PNOA ortofoto y LiDAR | CC BY 4.0 | «PNOA cedido por © Instituto Geográfico Nacional» | Atribución también en tiles derivados | ✅ permitido con atribución | https://www.ign.es/ | ⚠️ por confirmar |
| IGN/CNIG — MDT05 (pendientes, D-11) | CC BY 4.0 | «MDT05 © Instituto Geográfico Nacional» | No aplica | ✅ permitido con atribución | https://centrodedescargas.cnig.es/ | ⚠️ por confirmar |
| OpenStreetMap | ODbL 1.0 | «© OpenStreetMap contributors» (enlace a openstreetmap.org/copyright) | Los tiles son *Produced Work*: basta la atribución. Si además publicamos un extracto de la base de datos (p. ej. GeoJSON de calles) ese extracto es ODbL (share-alike) | ✅ permitido con atribución | https://www.openstreetmap.org/copyright | ⚠️ por confirmar |
| Catastro (fallback de huellas) | Licencia de uso de la información catastral (reutilización libre con atribución) | «Fuente: Dirección General del Catastro» + fecha | Atribución en derivados | ✅ permitido con atribución | https://www.catastro.hacienda.gob.es/ | ⚠️ por confirmar |
| MeteoGalicia (candidato) | Reutilización con cita de la fuente (licencia exacta sin comprobar) | «MeteoGalicia — Xunta de Galicia» | — | ⚠️ por confirmar; **no usar** hasta confirmar | https://www.meteogalicia.gal/ | ❌ |
| Modelo de imagen (IMGAPI-01, plan B de estilo) | Sin elegir | Nombre del proveedor | Revisar si los términos permiten uso comercial de las imágenes generadas y si reclaman derechos | ⛔ bloqueado hasta que IMGAPI-01 elija proveedor | — | ❌ |
| Google Photorealistic 3D Tiles | Términos de Google Maps Platform | — | Prohíben derivados offline | ⛔ **no se usa** (decisión del spec) | — | — |

## Lo bloqueado y su alternativa

| Bloqueado | Por qué | Alternativa |
|---|---|---|
| Modelo de imagen sin elegir | No se pueden revisar términos de un proveedor que no existe | IMGAPI-01 elige; hasta entonces, tiles placeholder (PYR-01 ya funciona con ellos) |
| Google 3D Tiles | Términos incompatibles con tiles derivados | Edificios 3D del Concello (X-05) + PNOA |
| MeteoGalicia | Licencia sin confirmar | Open-Meteo (ya integrado en D-10) |
| Fotos de la capa navideña | Pueden tener autor distinto del Concello | Fotos propias de R-03 (el spec ya las prefiere); las del Concello solo enlazadas, con crédito |
| Edificios 3D (publicación de tiles) | Sin licencia declarada | Pedir confirmación al Concello por su canal de datos abiertos; fallback Catastro (atribución) si no responde |

## Texto para D-17

```
Datos: Concello de Vigo — datos.vigo.org (ODC-BY), actualizado el {fecha}.
Puntos de Navidad: Concello de Vigo, capa «Puntos de interés de Navidad 2026-27».
Edificios: Concello de Vigo, «Edificios 3D».
Autobuses: Vitrasa, GTFS vía datos.vigo.org (ODC-BY). Horario programado, no tiempo real.
Trenes: Renfe Operadora (CC BY 4.0). Horario programado.
Tiempo: Weather data by Open-Meteo.com (CC BY 4.0).
Ortofoto y relieve: PNOA y MDT05 cedidos por © Instituto Geográfico Nacional (CC BY 4.0).
Mapa base: © OpenStreetMap contributors (ODbL).
Ilustración: {proveedor del modelo de imagen}.
```

`{fecha}` sale del `fetched_at` de cada snapshot (D-01/D-18).
