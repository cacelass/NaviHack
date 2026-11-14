# Registro de investigación — puntos de Navidad 2026-27 (R-01)

> 2026-11-14. Base: capa oficial del Concello (R-06,
> `scripts/christmas_layer.py`). Resultado: `data/points.json` (35 puntos) +
> `data/points_overrides.json` (cambios fuera de la capa, separado de la copia
> cruda `data/raw/concello_navidad/`).

## Orden de prioridad entre fuentes (protocolo F2)

Cuando dos fuentes discrepan en ubicación, horario o existencia de un punto,
gana la de más arriba; lo que solo sale en una fuente de más abajo entra como
`status: not_confirmed` («aún sin confirmar por el Concello»):

1. Capa ArcGIS del Concello de la temporada en curso (oficial, georreferenciada).
2. Programa oficial 2026-27 del Concello / agenda de datos.vigo.org (horas de actos) → R-04.
3. Visita in situ con foto y GPS fechados (R-02/R-03) — gana a 1 **solo en la posición** si la diferencia supera 15 m.
4. Turismo de Vigo.
5. Prensa local.
6. OpenStreetMap, redes sociales, blogs.

## Lo que el spec esperaba de prensa y ya es oficial

El spec (v4, F2) suponía que la capa sería la de 2025-26 (43 puntos) y que los
cambios de 2026 vendrían de prensa. **El Concello ya publicó la capa 2026-27**
(item editado el 2026-11-13), y trae todos esos cambios:

| Cambio esperado | En la capa 2026-27 | Punto |
|---|---|---|
| Noria en nueva ubicación (Vialia) | ✅ «Noria Gigante», aparcamiento exterior Vialia (42.236839, -8.708156) | `concello-3494` |
| Cíes Market (nueva ubicación) | ✅ «Mercado de Navidad - Cíes Market», Plaza de Vialia | `concello-3496` |
| Pista de hielo | ✅ «Pista de Hielo (Samil)», Av. de Samil 73 | `concello-3512` |
| Regalos gigantes | ✅ «Caja gigante de Regalo», Gran Vía × Urzáiz | `concello-2566` |
| Novedades Disney | ✅ «Experiencia "Dentro de Disney+"», Policarpo Sanz | `concello-4940` |

Por eso no hay ningún punto `not_confirmed` y el fichero de overrides solo
enlaza agenda ↔ punto.

## Diferencias con lo que decía el spec

- **35 puntos, no 43.** La edición 2025-26 ya no se puede consultar: el
  Concello reutiliza el mismo FeatureServer y lo sobrescribe cada temporada
  (el item «Puntos interés Navidad 2025 2026» es solo un *Service Definition*).
  Los criterios del ticket que dicen «43» se cumplen con los 35 de 2026-27,
  que es la temporada que se va a mostrar.
- **7 tipos, los mismos del spec:** 16 luces, 8 atracciones, 4 expositivos,
  2 mercados, 2 Papá Noel/Reyes, 2 galerías de fotos, 1 photocall.

## Avisos por punto

- **Posición aproximada (2):** `concello-3729` y `concello-3730` («Navidad en
  imágenes» I y II) dicen «Por toda la ciudad» y comparten coordenadas
  genéricas → `position: approximate`. No se pintan como punto fijo en el mapa.
- **Fuera del núcleo navideño (para ZONE-01):** Pista de Hielo y Pista de Karts
  (Samil), Circo de Navidad (Av. Castelao 50) y Mercado del Calvario (Urzáiz
  183). Se muestran como marcador sobre la ortofoto, no como asset dibujado.
- **Mismo lugar, dos puntos:** Cartero Real y Casa de Papá Noel (Policarpo
  Sanz 13); Palacio Navideño y Bosque de Navidad (Policarpo Sanz 36). Hay que
  separarlos visualmente en el mapa.
- **Horas:** las 11 luces con «Encendido: … 18:00 h» llevan
  `show_times: ["18:00"]`, sacado del horario oficial. El resto tiene horario
  de apertura en texto; estructurarlo (días, cierres, el 21-dic, 24/31-dic) es
  R-04.

## Enlaces agenda ↔ punto (overrides)

| Evento agenda | Punto | Efecto |
|---|---|---|
| 336 «Acto de encendido de luces de Navidad» (Porta do Sol, 14-nov) | `concello-2552` Árbol gigante | El evento toma la hora 18:00 del punto en vez de «hora por confirmar» |
| 4036 «Desfile "parade" Disney+» (García Barbón, 14-nov) | — | Es un recorrido, no un punto: queda en la lista de eventos |

## Estado

Todos los puntos están en `status: official` (por encima de `unverified`),
con `sources` (capa ArcGIS + URL + fecha) y `last_verified` = fecha de la
copia cruda. Re-verificación semanal: R-05.

## Pendiente fuera de este ticket

- Visitas in situ con foto/GPS: R-02 (6 hitos) y R-03 (todos).
- Horarios estructurados: R-04.
- Licencia de textos y fotos de la capa: `licencias.md` (por confirmar).
