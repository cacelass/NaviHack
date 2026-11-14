/* Marca TinyVigo — símbolo isométrico (bloque de ciudad + punto de luz).
   Un solo dibujo, dos versiones: con nombre (Inter 600) o solo el símbolo.
   Sin degradados ni sombras: tres caras planas y una estrella en currentColor.
   Se usa en la cabecera de la app; la referencia completa está en marca.html. */
(function () {
  var V = 'viewBox="0 0 40 40" aria-hidden="true"';
  var SYM =
    '<path d="M20 11 33 18.5 20 26 7 18.5Z" fill="#eecb7a"/>' +
    '<path d="M7 18.5 20 26v10L7 28.5Z" fill="#d9a441"/>' +
    '<path d="M33 18.5 20 26v10l13-7.5Z" fill="#a9760f"/>' +
    '<path d="M20 2.6l1 2.9 2.9 1-2.9 1-1 2.9-1-2.9-2.9-1 2.9-1Z" fill="currentColor"/>';

  function svg(size) {
    var s = size || 20;
    return '<svg class="marca__sym" ' + V + ' width="' + s + '" height="' + s + '">' + SYM + '</svg>';
  }
  function full(size) {
    var s = size || 24;
    return '<span class="marca">' + svg(s) + '<span class="marca__wm">TinyVigo</span></span>';
  }
  function mount(root) {
    (root || document).querySelectorAll('[data-marca]').forEach(function (el) {
      var s = +(el.getAttribute('data-size') || 20);
      el.insertAdjacentHTML('afterbegin', svg(s));
      el.removeAttribute('data-marca');
    });
  }
  window.MARCA = { svg: svg, full: full, mount: mount };
  mount(); document.addEventListener('DOMContentLoaded', function () { mount(); });
})();
