import { h } from './dom.js';
import { parseTodo } from './parser.js';
import { getStorage, createStore } from './store.js';
import { createT, detectLang } from './strings.js';
import { renderList } from './list.js';
import { createLink } from './link.js';
import { buildExport, isoDate } from './export.js';

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
  notice: null, manual: null,
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

const draftFor = (item) => (ui.drafts.has(item.key) ? ui.drafts.get(item.key) : store.get(item.key).note);

function collectUnsent() {
  const entries = [];
  for (const block of ui.blocks) {
    for (const item of block.items) {
      const entry = store.get(item.key);
      if (entry.sent || (entry.status !== 'noted' && entry.status !== 'done')) continue;
      entries.push({ key: item.key, block: block.heading, text: item.text, tag: item.tag, status: entry.status, note: entry.note, screenshots: entry.screenshots });
    }
  }
  return entries;
}

const markSent = (entries) => entries.forEach((entry) => store.update(entry.key, { sent: true }));

async function copyAll() {
  const entries = collectUnsent();
  if (entries.length === 0) return;
  const version = (conn() && conn().version) || store.version(game);
  const text = buildExport({ game, version, date: isoDate(new Date()), entries });
  ui.notice = ui.manual = null;
  try {
    await navigator.clipboard.writeText(text);
    ui.notice = t('copied', { n: entries.length });
  } catch (error) {
    ui.manual = text;
  }
  markSent(entries);
  render();
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
  save(item) {
    const note = draftFor(item);
    if (!note.trim() && store.get(item.key).screenshots.length === 0) return;
    store.update(item.key, { status: 'noted', note });
    render();
  },
  done(item) {
    store.update(item.key, { status: 'done', note: draftFor(item) });
    render();
  },
  copyAll,
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

function copyButton() {
  const n = collectUnsent().length;
  return h('button', { class: 'copy-all', type: 'button', disabled: n === 0, onclick: actions.copyAll }, t('copyAll', { n }));
}

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
  return [
    store.isPersistent() ? null : h('p', { class: 'notice warn' }, t('noStorage')),
    ui.notice ? h('p', { class: 'notice ok' }, ui.notice) : null,
    ui.manual ? h('div', { class: 'notice' }, h('p', {}, t('copyManual')),
      h('textarea', { class: 'export-box', readonly: true, 'data-focus': 'export' }, ui.manual)) : null,
  ];
}

function body() {
  if (ui.loadError) return h('p', { class: 'load-error' }, t('loadError', { game, reason: ui.loadError }));
  return renderList(view());
}

function render() {
  const focus = captureFocus();
  document.getElementById('app').replaceChildren(header(), statusBar(), toolbar(), ...notices(), body());
  restoreFocus(focus);
  const box = document.querySelector('.export-box');
  if (box) box.select();
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
