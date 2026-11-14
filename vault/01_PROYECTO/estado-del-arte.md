# Estado del arte — TinyVigo

> Generado por `research find_papers` (backend OpenAlex, 10 referencias).
> Relevancia léxica sobre las palabras clave derivadas del README/pyproject
> (mapa, Vigo, isométrico, Navidad, pixel art, rutas, teselas). Ninguna de
> las referencias es directamente comparable a TinyVigo; se listan para
> trazabilidad y se descartan salvo la primera, que aporta un patrón de
> "estado del arte y direcciones futuras" útil para estructurar este documento.

## Fuentes indexadas

1. **Harnessing three-dimensional (3D) cell culture models for pulmonary infections: State of the art and future directions** (2023, OpenAlex, relevancia 0.33).
   - *Se toma:* el patrón "estado del arte + direcciones futuras" como estructura para este mismo documento.
   - *Se descarta:* todo el contenido (biomedicina, cultivos celulares), sin aplicación a mapas ni a Vigo.

2. **Excitons in Bilayer MoS2 Displaying a Colossal Electric Field Splitting and Tunable Magnetic Response** (2021).
   - *Se toma:* nada.
   - *Se descarta:* física de materiales, sin relación con el proyecto.

3. **Potential immunotherapy for Alzheimer disease and age-related dementia** (2019).
   - *Se toma:* nada.
   - *Se descarta:* neurociencia clínica, sin relación con el proyecto.

4. **Updated Integrated Framework for Making Clinical Decisions Across the Lifespan and Health Conditions** (2021).
   - *Se toma:* nada.
   - *Se descarta:* marco clínico, sin relación con el proyecto.

5. **A Role of the Choroid Plexus in Transplantation Therapy** (2005).
   - *Se toma:* nada.
   - *Se descarta:* neurobiología, sin relación con el proyecto.

6. **Catholic Dressing in the Spanish Franco Dictatorship (1939–1975)** (2021).
   - *Se toma:* nada.
   - *Se descarta:* historia social; aunque menciona España, no aporta al mapa ni a la Navidad de Vigo.

7. **Deconvolution of Focal Segmental Glomerulosclerosis Pathophysiology Using Transcriptomics Techniques** (2021).
   - *Se toma:* nada.
   - *Se descarta:* nefrología, sin relación con el proyecto.

8. **Claves de éxito de las experiencias de transición a la sostenibilidad en reservas de biosfera** (2021).
   - *Se toma:* nada; la metodología participativa podría inspirar talleres con vecinos, pero no es necesaria para el v1.
   - *Se descarta:* sostenibilidad y reservas de biosfera, fuera de alcance.

9. **Work Flows for Cellular Epidemiology, From Conception to Translation** (2019, retirado).
   - *Se toma:* nada.
   - *Se descarta:* epidemiología celular y, además, el manuscrito fue retirado.

10. **Third Emerging Trends in Applied Mathematics and Mechanics. Book of Abstracts** (2024).
    - *Se toma:* nada.
    - *Se descarta:* actas de congreso de matemática aplicada; sin relación con el proyecto.

## Conclusiones

- No se encontró literatura directamente aplicable a mapas isométricos pixel art
  de una ciudad en Navidad. TinyVigo se apoya en la familia de referentes visuales
  (tiny.london, isometric.nyc, tinygyn, tinyrj) y en las fuentes de datos del
  Concello, no en papers.
- La búsqueda es léxica (solapamiento de keywords con título+abstract), por lo
  que los resultados son ruidosos cuando las keywords del proyecto son poco
  frecuentes en la literatura. Para mejorar, refinar las keywords con términos
  del dominio (isometric map, web tiles, GTFS, pixel art rendering).
- Las 10 URLs anteriores quedaron indexadas en el RAG local (`rag index_urls`)
  para poder consultarlas después, aunque su aportación al proyecto es nula.
PY
echo "written"