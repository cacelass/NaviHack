/* Interacciones ligeras de ejemplo. No hay datos reales ni red: es una maqueta. */
(function () {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const root = document.documentElement, isMock = document.body.classList.contains('mock');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hh = m => String(Math.floor(m / 60) % 24).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');

  const PTS = {
    arbol: { name: 'Árbol gigante de Nadal', type: 'Elementos lumínicos', icon: 'tree', open: [1080, 1440], from: '18:00', until: '00:00', hours: 'Todos los días de 18:00 a 00:00', extra: 'Pases de música y luz a las 18:00 y a las 20:00',
      photo: 'assets/foto-arbol.jpg', walk: '4 min andando', story: 'Árbol de luces led de 46,40 metros en la Praza da Porta do Sol. Se puede entrar dentro, escuchar la música y ver el juego de luz desde fuera.', src: 'Concello de Vigo, programa de Navidad' },
    noria: { name: 'Noria gigante', type: 'Atracciones', icon: 'wheel', open: [1020, 1350], from: '17:00', until: '22:30', hours: 'Laborables de 17:00 a 22:30', extra: 'Los horarios cambian del 21 de diciembre al 12 de enero',
      photo: 'assets/foto-noria.jpg', walk: '11 min andando', story: 'La noria cambia de sitio en 2026 y pasa a Vialia. La información viene de la prensa local y el Concello aún no la ha confirmado.', src: 'Prensa local, sin confirmar por el Concello' },
    mercado: { name: 'Mercado de Navidad', type: 'Mercados navideños', icon: 'market', open: [1020, 1350], from: '17:00', until: '22:30', hours: 'Laborables de 17:00 a 22:30', extra: 'Praza de Compostela',
      photo: 'assets/foto-mercado.jpg', walk: '7 min andando', story: 'Productos navideños, gastronomía, regalos y artesanía en la Praza de Compostela.', src: 'Concello de Vigo, programa de Navidad' }
  };
  const state = { time: location.hash.indexOf('day') > -1 ? 720 : (root.getAttribute('data-time') ? +root.getAttribute('data-time') : 1290), pt: 'arbol' };
  const isNight = t => t >= 1080 || t < 420;
  const isOpen = (p, t) => t >= p.open[0] && t < p.open[1];

  function setIcon(el, name) { if (el && el.dataset.cur !== name) { el.innerHTML = PX.svg(name, { size: +(el.dataset.size || 24) }); el.dataset.cur = name; } }
  function renderTime(scope) {
    $$('[data-time]', scope).forEach(e => { e.textContent = hh(state.time); });
    $$('.tctl', scope).forEach(c => { const p = state.time / 1439; c.style.setProperty('--p', p); setIcon($('.tmode', c), isNight(state.time) ? 'moon' : 'sun'); const th = $('.thumb', c); if (th) th.setAttribute('aria-valuenow', state.time); });
  }
  function renderPoint() {
    const p = PTS[state.pt]; if (!p) return; const open = isOpen(p, state.time);
    $$('.mk[data-pt]').forEach(m => { const q = PTS[m.dataset.pt]; m.dataset.state = m.dataset.pt === state.pt && !$('.ficha.closed') ? 'sel' : (q && isOpen(q, state.time) ? 'open' : 'normal'); m.dataset.open = q && isOpen(q, state.time) ? '1' : '0'; });
    const f = $('.ficha[data-live]'); if (!f) return;
    $$('[data-f]', f).forEach(e => {
      const k = e.dataset.f;
      if (k === 'name') e.textContent = p.name; else if (k === 'type') e.textContent = p.type; else if (k === 'hours') e.textContent = p.hours; else if (k === 'extra') e.textContent = p.extra;
      else if (k === 'story') e.textContent = p.story; else if (k === 'src') e.textContent = p.src; else if (k === 'walk') e.textContent = p.walk;
      else if (k === 'photo') e.style.backgroundImage = "url('" + p.photo + "')";
      else if (k === 'sprite') setIcon(e, p.icon);
      else if (k === 'status') { e.dataset.open = open ? '1' : '0'; e.querySelector('.st-ic').innerHTML = PX.svg(open ? 'open' : 'closed', { size: 16 }); e.querySelector('.st-tx').textContent = open ? 'Abierto ahora, hasta las ' + p.until : 'Cerrado ahora, abre a las ' + p.from; }
    });
  }
  function setTime(t) { state.time = Math.max(0, Math.min(1439, Math.round(t / 5) * 5)); renderTime(document); if (isMock) { root.setAttribute('data-mode', isNight(state.time) ? 'night' : 'day'); } renderPoint(); }

  // pista de la hora
  $$('.tctl').forEach(c => {
    const track = $('.track', c); if (!track) return; let drag = false;
    const at = e => { const r = track.getBoundingClientRect(); const p = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)); if (isMock) setTime(p * 1439); else { state.time = Math.round(p * 1439 / 5) * 5; renderTime(c.parentNode); } };
    track.addEventListener('pointerdown', e => { drag = true; track.setPointerCapture(e.pointerId); at(e); });
    track.addEventListener('pointermove', e => { if (drag) at(e); });
    track.addEventListener('pointerup', () => { drag = false; });
    track.addEventListener('keydown', e => { const d = e.key === 'ArrowRight' ? 15 : e.key === 'ArrowLeft' ? -15 : 0; if (d) { e.preventDefault(); isMock ? setTime(state.time + d) : (state.time = Math.max(0, Math.min(1439, state.time + d)), renderTime(c.parentNode)); } });
    const m = $('.tmode', c); if (m) m.addEventListener('click', () => { const t = isNight(state.time) ? 720 : 1290; isMock ? setTime(t) : (state.time = t, renderTime(c.parentNode)); });
  });

  // chips de capas y segmentos
  $$('.chip[aria-pressed]').forEach(c => c.addEventListener('click', () => {
    const on = c.getAttribute('aria-pressed') !== 'true'; c.setAttribute('aria-pressed', on); c.classList.toggle('on', on);
    if (c.dataset.layer) { root.classList.toggle('hide-' + c.dataset.layer, !on); }
  }));
  $$('.seg').forEach(s => s.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; $$('button', s).forEach(x => { x.classList.remove('on'); x.setAttribute('aria-pressed', 'false'); }); b.classList.add('on'); b.setAttribute('aria-pressed', 'true'); }));
  $$('[data-addroute]').forEach(b => b.addEventListener('click', () => {
    const added = b.dataset.added !== '1'; b.dataset.added = added ? '1' : '0';
    const lab = b.querySelector('.lb'); if (lab) lab.textContent = added ? 'En la ruta' : (b.dataset.label || 'Añadir a la ruta');
    const ic = b.querySelector('.bi'); if (ic) ic.innerHTML = PX.svg(added ? 'check' : 'route', { size: 16 });
    b.classList.toggle('is-added', added); if (added) toast('Añadido a la ruta');
  }));
  function toast(msg) { const t = $('#toast'); if (!t) return; $('.tx', t).textContent = msg; t.classList.add('show'); clearTimeout(toast.h); toast.h = setTimeout(() => t.classList.remove('show'), 2200); }

  // maqueta: ficha, marcadores, buscador, capas
  if (isMock) {
    const f = $('.ficha'), search = $('.search'), layers = $('.layers');
    const morph = document.body.classList.contains('d-d') && !reduce && f && f.animate;
    function openFicha(mk) {
      if (mk) state.pt = mk.dataset.pt;
      const was = f.classList.contains('closed'); f.classList.remove('closed'); document.body.classList.remove('no-ficha'); renderPoint();
      if (morph && was && mk) {
        const from = mk.getBoundingClientRect(), to = f.getBoundingClientRect(), cs = getComputedStyle(f);
        Object.assign(f.style, { top: to.top + 'px', left: to.left + 'px', width: to.width + 'px', height: to.height + 'px', right: 'auto', bottom: 'auto' });
        const a = f.animate([{ top: from.top + 'px', left: from.left + 'px', width: from.width + 'px', height: from.height + 'px', borderRadius: '8px' }, { top: to.top + 'px', left: to.left + 'px', width: to.width + 'px', height: to.height + 'px', borderRadius: cs.borderRadius }], { duration: 500, easing: 'cubic-bezier(0.22,1,0.36,1)' });
        const kids = $$('.ficha > *', f).concat([]); kids.forEach((k, i) => k.animate([{ opacity: 0, filter: 'blur(2px)' }, { opacity: 0, filter: 'blur(2px)', offset: .5 }, { opacity: 1, filter: 'blur(0)' }], { duration: 500 + i * 40, easing: 'ease-out' }));
        a.onfinish = () => { ['top', 'left', 'width', 'height', 'right', 'bottom'].forEach(k => f.style[k] = ''); };
      }
    }
    function closeFicha() { f.classList.add('closed'); document.body.classList.add('no-ficha'); renderPoint(); }
    $$('.mk[data-pt]').forEach(m => m.addEventListener('click', e => { e.stopPropagation(); (state.pt === m.dataset.pt && !f.classList.contains('closed')) ? closeFicha() : openFicha(m); }));
    $$('.ficha .close').forEach(b => b.addEventListener('click', closeFicha));
    $$('.map').forEach(m => m.addEventListener('click', () => { if (!f.classList.contains('closed')) closeFicha(); }));
    if (search) {
      const inp = $('input', search), sb = $('.sbtn', search);
      if (sb) sb.addEventListener('click', () => { search.classList.remove('collapsed'); inp && inp.focus(); });
      if (inp) { inp.addEventListener('focus', () => search.classList.add('focus')); inp.addEventListener('blur', () => setTimeout(() => { search.classList.remove('focus'); if (search.classList.contains('collapsible') && !inp.value) search.classList.add('collapsed'); }, 150)); }
      $$('.sres button', search).forEach(b => b.addEventListener('mousedown', e => { e.preventDefault(); const mk = $('.mk[data-pt="' + b.dataset.pt + '"]'); if (mk) openFicha(mk); inp.blur(); }));
    }
    const lb = $('.lbtn'); if (lb && layers) lb.addEventListener('click', () => { layers.classList.toggle('open'); lb.setAttribute('aria-pressed', layers.classList.contains('open')); });
    $$('.zoom button').forEach(b => b.addEventListener('click', () => { const m = $('.map .world'); const z = Math.max(1, Math.min(2.4, (+m.dataset.z || 1) + (b.dataset.dz === '+' ? .4 : -.4))); m.dataset.z = z; m.style.transform = 'scale(' + z + ')'; }));
    setTime(state.time);
    if (location.hash.indexOf('closed') > -1) closeFicha();
  }

  // alternar modo en las hojas de estilo
  $$('[data-mode-toggle]').forEach(b => b.addEventListener('click', () => { const n = root.getAttribute('data-mode') === 'night' ? 'day' : 'night'; root.setAttribute('data-mode', n); b.setAttribute('aria-pressed', n === 'night'); const l = $('.lb', b); if (l) l.textContent = n === 'night' ? 'Noche' : 'Día'; setIcon($('.ic', b), n === 'night' ? 'moon' : 'sun'); }));
  $$('[data-mode-toggle] .ic').forEach(e => { e.dataset.size = 20; setIcon(e, root.getAttribute('data-mode') === 'night' ? 'moon' : 'sun'); });
  window.UI = { setTime, toast };
})();
