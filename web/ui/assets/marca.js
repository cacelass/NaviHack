/* Marca NaviVigo — "el árbol que se gira".
   Delante es un abeto mínimo: dos ángulos gruesos y la luz en la punta. Girado 180°, la falda es la V de
   Vigo y la luz cae al vértice. Un solo trazado vectorial para todos los tamaños (nada de rejilla de
   píxeles): el mismo que web/favicon.svg y web/ui/assets/logo-negro.svg / logo-blanco.svg.
   Solo hay dos versiones y no llevan color: negra en modo claro y blanca en modo oscuro. La tinta es
   --tv-tinta (css/tokens.css) y cambia sola con el tema.
   El nombre va SIEMPRE en Inter. Nada de fuente de píxel en el nombre.
   Uso: <span data-tv="simbolo" data-tv-size="24">, data-tv="logo", data-tv="matasellos".
   También monta el marcado antiguo <i class="marca" data-marca data-size="22">. */
(function () {
  function vector(attrs) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" ' + attrs + '>' +
      '<path class="tv-pv" d="M6.4 12.2L12 7L17.6 12.2" stroke-width="3.6" stroke-linecap="butt" stroke-linejoin="miter"/>' +
      '<path class="tv-pv" d="M2.2 22L12 15L21.8 22" stroke-width="3.6" stroke-linecap="butt" stroke-linejoin="miter"/>' +
      '<circle class="tv-pl" cx="12" cy="2.15" r="1.65" stroke="none"/>' +
      '</svg>';
  }

  /* opts: { size, clase } */
  function simbolo(opts) {
    opts = opts || {};
    var s = opts.size || 24;
    var cls = 'tv-simbolo' + (opts.clase ? ' ' + opts.clase : '');
    var dim = 'width="' + s + '" height="' + s + '"';
    return '<span class="' + cls + '" style="--tv-s:' + s + 'px">' + vector(dim) + '</span>';
  }

  /* lockup horizontal: símbolo + nombre en Inter */
  function logotipo(opts) {
    opts = opts || {};
    var s = opts.size || 28;
    return '<span class="tv-lockup" style="--tv-s:' + s + 'px">' +
      simbolo({ size: s }) +
      '<span class="tv-nombre">NaviVigo</span></span>';
  }

  var idn = 0;
  /* matasellos circular de Vigo: aro dentado, VIGO arriba, A NAVIDEÑA abajo */
  function matasellos(opts) {
    opts = opts || {};
    var s = opts.size || 132;
    var fecha = opts.fecha || '14 · 12 · 2026';
    var id = 'tv-mat-' + (++idn);
    return '<svg class="tv-mat" viewBox="0 0 100 100" width="' + s + '" height="' + s + '" aria-hidden="true" focusable="false">' +
      '<defs>' +
      '<path id="' + id + '-a" d="M50 50 m-35 0 a35 35 0 1 1 70 0" fill="none"/>' +
      '<path id="' + id + '-b" d="M50 50 m-33 0 a33 33 0 1 0 66 0" fill="none"/>' +
      '</defs>' +
      '<circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" stroke-width="3.2" stroke-dasharray="2.2 2.6"/>' +
      '<circle cx="50" cy="50" r="40.5" fill="none" stroke="currentColor" stroke-width="1.1"/>' +
      '<text class="tv-mat__arco" font-size="9.4" font-weight="600" letter-spacing="1.5">' +
      '<textPath href="#' + id + '-a" startOffset="50%" text-anchor="middle">VIGO</textPath></text>' +
      '<text class="tv-mat__arco" font-size="7.4" font-weight="500" letter-spacing="1.2">' +
      '<textPath href="#' + id + '-b" startOffset="50%" text-anchor="middle">A NAVIDEÑA</textPath></text>' +
      '<g transform="translate(35.6 27.6) scale(1.2)" fill="none" stroke="currentColor" stroke-width="3.6" stroke-linejoin="miter">' +
      '<path d="M6.4 12.2L12 7L17.6 12.2"/><path d="M2.2 22L12 15L21.8 22"/>' +
      '<circle cx="12" cy="2.15" r="1.65" fill="currentColor" stroke="none"/></g>' +
      '<text class="tv-mat__fecha" x="50" y="66" text-anchor="middle" font-size="6.6" font-weight="500" letter-spacing=".6">' + fecha + '</text>' +
      '</svg>';
  }

  var css = '' +
    '.tv-simbolo{display:inline-block;flex:none;line-height:0;color:var(--tv-tinta,currentColor)}' +
    '.tv-simbolo svg{display:block;width:var(--tv-s,24px);height:var(--tv-s,24px)}' +
    '.tv-pv{fill:none;stroke:currentColor}' +
    '.tv-pl{fill:currentColor}' +
    '.tv-lockup{display:inline-flex;align-items:center;gap:calc(var(--tv-s,28px) * .34);color:var(--tv-tinta,currentColor)}' +
    '.tv-nombre{font:600 calc(var(--tv-s,28px) * .86)/1 var(--f-ui,"Inter",system-ui,sans-serif);letter-spacing:-.02em;color:currentColor}' +
    '.tv-mat__arco,.tv-mat__fecha{fill:currentColor;font-family:var(--f-ui,"Inter",system-ui,sans-serif)}';
  var st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);

  function mount(root) {
    var doc = root || document;
    doc.querySelectorAll('[data-tv]').forEach(function (el) {
      var v = el.getAttribute('data-tv');
      var s = +el.getAttribute('data-tv-size') || undefined;
      var marcado = v === 'logo' ? logotipo({ size: s })
        : v === 'matasellos' ? matasellos({ size: s, fecha: el.getAttribute('data-tv-fecha') })
        : simbolo({ size: s });
      el.insertAdjacentHTML('afterbegin', marcado);
      el.removeAttribute('data-tv');
    });
    /* Marcado antiguo de los HUD (<i class="marca" data-marca data-size="22">): el
       mismo símbolo, para que la cabecera del mapa y esta página no se separen. */
    doc.querySelectorAll('[data-marca]').forEach(function (el) {
      el.innerHTML = simbolo({ size: +(el.getAttribute('data-size') || 22) });
      el.removeAttribute('data-marca');
    });
  }

  window.MARCA = { simbolo: simbolo, logotipo: logotipo, matasellos: matasellos, mount: mount };
  mount();
  document.addEventListener('DOMContentLoaded', function () { mount(); });
})();
