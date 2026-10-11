import { h } from './dom.js';
import { parseTodo } from './parser.js';
import { getStorage, createStore } from './store.js';
import { createT, detectLang } from './strings.js';
import { renderList } from './list.js';
import { createLink } from './link.js';

export const GAMES = ['rhyflitzer', 'wipfelkratzer'];
const SLUG_RE = /^[a-z0-9-]+$/;

const requested = new URLSearchParams(location.search).get('game');
const game = requested && SLUG_RE.test(requested) ? requested : GAMES[0];
const games = GAMES.includes(game) ? GAMES : [...GAMES, game];
const storage = getStorage();
const store = createStore(storage);
let lang = detectLang(storage, navigator.language);
let t = createT(lang);
const link = createLink({
  game,
  onChange: () => { if (link.conn) store.setVersion(game, link.conn.version); render(); },
});

const ui = {
  blocks: [], loadError: null, filter: 'open', query: '',
  expanded: new Set(), collapsed: new Map(), drafts: new Map(), errors: new Map(),
};
const conn = () => link.conn;

function captureFocus() {
  const el = document.activeElement;
  if (!el || !el.dataset || !el.dataset.focus) return null;
  return { id: el.dataset.focus, start: el.selectionStart };
}

function restoreFocus(saved) {
  const el = saved && document.querySelector(`[data-focus="${CSS.escape(saved.id)}"]`);
  if (!el) return;
  el.focus();
  if (typeof saved.start === 'number') el.setSelectionRange(saved.start, saved.start);
}

const errorText = (error) => (error.code && error.code !== 'remote' ? t(`err_${error.code}`) : error.message);

function download(dataUrl, name) {
  const anchor = h('a', { href: dataUrl, download: name });
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
}

const actions = {
  toggleItem(key) {
    if (ui.expanded.has(key)) ui.expanded.delete(key); else ui.expanded.add(key);
    render();
  },
  toggleBlock(heading, wasCollapsed) {
    ui.collapsed.set(heading, !wasCollapsed);
    render();
  },
  async go(item) {
    ui.errors.delete(item.key);
    try { await link.go(item.tag); } catch (error) { ui.errors.set(item.key, errorText(error)); }
    render();
  },
  async shot(item) {
    ui.errors.delete(item.key);
    try {
      const png = await link.screenshot();
      const name = store.nextShotName(game, new Date());
      download(png.dataUrl, name);
      store.update(item.key, { screenshots: [...store.get(item.key).screenshots, name] });
    } catch (error) {
      ui.errors.set(item.key, errorText(error));
    }
    render();
  },
};

const view = () => ({ ...ui, t, store, conn: conn(), actions });

function switchLang() {
  lang = lang === 'en' ? 'de' : 'en';
  t = createT(lang);
  try { if (storage) storage.setItem('gg-lang', lang); } catch (e) { /* stays for this session */ }
  render();
}

function header() {
  const picker = h('select', { class: 'picker', 'aria-label': 'Game', onchange: (e) => { location.search = `?game=${e.target.value}`; } },
    games.map((g) => h('option', { value: g, selected: g === game }, g)));
  return h('header', { class: 'head' }, h('h1', {}, t('title')), picker,
    h('button', { class: 'lang', type: 'button', onclick: switchLang }, t('langToggle')));
}

const copyButton = () => null; // replaced in Task 9

function statusBar() {
  const c = conn();
  const line = c
    ? h('span', {}, '● ', t('connected', { version: c.version, n: c.targets.length }))
    : h('span', {}, '● ', t('disconnected'), ' ',
      h('a', { href: `/game-${game}/?dev=1`, target: '_blank', rel: 'noopener' }, t('openGame')));
  return h('div', { class: `status ${c ? 'on' : 'off'}` }, line, copyButton());
}

function toolbar() {
  const radios = ['open', 'noted', 'done'].map((f) => h('label', {},
    h('input', { type: 'radio', name: 'filter', value: f, checked: ui.filter === f, onchange: () => { ui.filter = f; render(); } }),
    ' ', t(`filter_${f}`)));
  const search = h('input', {
    type: 'search', class: 'search', placeholder: t('search'), value: ui.query, 'data-focus': 'search',
    oninput: (e) => { ui.query = e.target.value; render(); },
  });
  return h('div', { class: 'toolbar' }, radios, search);
}

function notices() {
  return [store.isPersistent() ? null : h('p', { class: 'notice warn' }, t('noStorage'))];
}

function body() {
  if (ui.loadError) return h('p', { class: 'load-error' }, t('loadError', { game, reason: ui.loadError }));
  return renderList(view());
}

function render() {
  const focus = captureFocus();
  document.getElementById('app').replaceChildren(header(), statusBar(), toolbar(), ...notices(), body());
  restoreFocus(focus);
}

async function loadTodo() {
  try {
    const response = await fetch(`/game-${game}/test-todo.md`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    ui.blocks = parseTodo(await response.text(), game);
    ui.loadError = null;
  } catch (e) {
    ui.blocks = [];
    ui.loadError = e.message;
  }
  render();
}

render();
loadTodo();
