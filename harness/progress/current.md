# Tarea actual

**Feature:** BASE-01
**Estado:** in_progress
**Iniciada:** 2026-11-14
**Responsable:** implementer

## Objetivo

Placeholder base image so the web, light, sea and weather can be developed before the final tiles exist. Redraw the 9 render tiles of 1024 px one at a time with gemini-3.1-flash-image (one call at a time, wait on 429, call count recorded), small style swatch plus a narrow neighbour strip, assemble in code with colour matching and soft blending at the joins (no AI on joins or corners), exactly 3072x3072 with the same georeference, publish as a new pyramid version. Style chosen by Jose: high-bit with painted light (p-3-highbit) for the web now; the unlit tiles (p-7) are kept for LIGHT-02.

Criterios de aceptación:
  1. 9 tiles drawn with the prompt of the chosen style, with the call count and 429 count written in pipeline/ledger/image-calls.jsonl
  2. Assembled image is exactly 3072x3072 and aligned with the render (offset measured in pixels)
  3. Colour matched between tiles in LAB and joins blended over 64-96 px by code
  4. Published as a new pyramid version in web/tiles, never overwriting another version
  5. A screenshot of the web at the local URL was looked at and its failures are listed

## Criterios de aceptación

- [ ] 9 tiles drawn with the prompt of the chosen style, with the call count and 429 count written in pipeline/ledger/image-calls.jsonl
- [ ] Assembled image is exactly 3072x3072 and aligned with the render (offset measured in pixels)
- [ ] Colour matched between tiles in LAB and joins blended over 64-96 px by code
- [ ] Published as a new pyramid version in web/tiles, never overwriting another version
- [ ] A screenshot of the web at the local URL was looked at and its failures are listed

## Bitácora

_(pendiente)_

## Bloqueos

_(ninguno)_
