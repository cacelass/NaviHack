# Programa 2026-27 estructurado (R-04)

> Fuente: campo `horario_atencion` de la capa ArcGIS del Concello (2026-11-14).
> Datos: `data/programme_2026.json`; lógica: `scripts/programme.py`; se vuelca en
> `points.json` (`programme`, `show_times`, `last_verified`) al ejecutar
> `python -m scripts.christmas_layer`.

## Cobertura

- **23 puntos con programa** (11 luces, 6 atracciones de Vialia/Samil y
  mercados, pista de hielo, Cartero Real, Casa de Papá Noel, circo, Nadal Bus,
  barco).
- **12 sin horario oficial** (`no_schedule`): photocall, belén luminoso,
  muñecos/violinista/Papá Noel en farolas, trineos, galerías de fotos, renos,
  lámpara mágica, Disney+, Papá Noel con balancín. `is_open` → `None`; la UI no
  dice «abierto» ni «cerrado».
- Festivos usados: 8-dic, 25-dic, 1-ene, 6-ene. Vísperas: el día anterior.

## Horas de espectáculo

- Árbol de Porta do Sol: animación musical 18:00, 19:00, 20:00, 21:00 y 21:50 (10 min).
- Nadal Bus: salidas por tramos de fechas (16–30 nov, 1–19 dic, 20 dic–6 ene) desde Urzáiz-Príncipe.
- Barco de la Navidad: 20:00 diario del 20-nov al 4-ene, 90 min, 25/12/0 €.

## Fechas especiales y cierres

- Luces «toda la noche»: 23, 24, 25, 30, 31-dic y 1, 5, 6-ene (hasta las 08:30).
- Vialia y mercados: 24 y 31-dic de 11:00 a 20:00; 5-ene de 11:00 a 22:00;
  horario de vacaciones (cierre más tarde los laborables) del 21-dic al 12-ene
  (noria) o al 16-ene (resto).
- Pista de hielo: 24, 31-dic y 5-ene de 11:00 a 19:00; 25-dic, 1 y 6-ene de 16:30 a 22:30.
- Cartero Real: solo del 25-dic al 5-ene.
- **Cierres:** el texto oficial no publica días de cierre dentro de temporada;
  `closed_dates` queda vacío por punto y se rellena si R-05 encuentra alguno.

## Dudas abiertas

- **Fin de temporada** de luces y atracciones: el Concello no lo publica (`season.to = null`). Pregunta abierta del spec.
- **Caja gigante de regalo:** ES dice 18:00–01:00/03:00; GL dice 18:30–00:30/02:00. Se usa ES; confirmar in situ (R-02/R-03).
- **Nadal Bus:** «Fecha inicio ventas: 16/11/2025», errata probable por 2026.
- **Circo:** horarios solo en ticketrona.com.
