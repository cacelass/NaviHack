# Web deck

The TinyVigo pitch as a single web page, built on the same pattern as the Strivon deck: a fixed
1920×1080 stage scaled to the window, one idea per slide, the app's dark theme
(`web/ui/css/tokens.css`) and Lucide icons (`lucide.js`, copied from `web/ui/assets/`).

```bash
python3 -m http.server 8000   # from this folder, then open http://localhost:8000
```

Arrows, space or a click move forward; a click on the left quarter goes back. `F` toggles full
screen and `#4` in the address opens slide 4.

## The story

1. "Hoy es un día muy, muy especial."
2. "Hoy, 14 de noviembre."
3. A photo of the mayor at a lights-on shows for a second, then "Se encienden las luces de Navidad en Vigo." word by word, between garlands whose bulbs light up left to right.
4. The three questions people ask tonight: what and where, is it lit yet, what can I fit in.
5. TinyVigo: logo, one line, the app on desktop.
6. The map drawn once: versions v1 to v7, then 35 spots, 16 lights, 12 car parks.
7. A spot: open/closed from the official programme, nearest car park, next buses.
8. The walk: how much time you have, the route on real streets.
9. Christmas today: a sample agenda drawn from parts, each row with its own photo and state.
10. Getting there: city view, car parks, Vitrasa and Renfe, search, three languages.
11. How it is made: open sources → snapshots → tiles → static web.
12. Closing: the logo, a QR to the demo and the address.
13. "¡Feliz Navidad! Merry Christmas!" under a garland, with the mayor at the lectern and a tiny late footnote.

## How it works

- **Two transitions.** Slides marked `data-wipe` (3, 5, 12, 13) use the string of lights: gold bulbs
  come on left to right, swell into dark cells that cover the slide, then shrink back and go out.
  Everywhere else is a short fade.
- **Entrances in order.** Each `.in` element waits `--i × 340 ms` after the slide shows.
- **Beats inside a slide.** `data-steps="N"` holds a slide for extra clicks and reveals `.step` (unused now).
- **Garlands.** `svg.garland` is filled by script; `data-wires="top"` keeps a single wire.
- **QR drawn as SVG** from an inlined matrix (generated with `segno`), finder squares in gold.

Screenshots in `img/` come from the live app (`web/`, map `v7-puerto-vialia`) in Spanish at
1920×1080 and 390×844 @2x, captured with Playwright. The map versions come from `docs/img/`.

## Credits

`img/abel-caballero.webp` and `img/abel-encendido.webp` are press photos of the 2022 lights-on in Porta do Sol, from
[Metropolitano.gal](https://metropolitano.gal/enfoque/apoteosis-en-un-multitudinario-acto-de-encendido-de-la-navidad-de-vigo).
They are not openly licensed: they are here for the live talk only and should not be republished.
