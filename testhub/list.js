import { h } from './dom.js';

function matchesFilter(view, block, item) {
  const entry = view.store.get(item.key);
  if (view.filter === 'open' && entry.status === 'done') return false;
  if (view.filter === 'noted' && entry.status !== 'noted') return false;
  if (view.filter === 'done' && entry.status !== 'done') return false;
  const query = view.query.trim().toLowerCase();
  return !query || `${block.heading} ${item.text} ${entry.note}`.toLowerCase().includes(query);
}

function goControl(view, item) {
  if (!item.tag) return null;
  const { t, conn } = view;
  if (!conn) return h('button', { class: 'go', disabled: true, title: item.tag }, t('go'));
  if (!conn.targets.some((target) => target.id === item.tag)) {
    return h('span', { class: 'go-unknown', title: t('goUnknown') }, item.tag);
  }
  return h('button', { class: 'go', onclick: () => view.actions.go(item) }, t('go'));
}

function editor(view, item, entry) {
  const { t, conn, actions, drafts } = view;
  const draft = drafts.has(item.key) ? drafts.get(item.key) : entry.note;
  const area = h('textarea', {
    class: 'note', rows: 3, placeholder: t('notePlaceholder'), 'data-focus': `note:${item.key}`,
    oninput: (e) => drafts.set(item.key, e.target.value),
  }, draft);
  return h('div', { class: 'editor' }, area,
    h('div', { class: 'chips' }, entry.screenshots.map((name) => h('span', { class: 'chip' }, `📷 ${name} ✓`))),
    h('div', { class: 'buttons' },
      h('button', { class: 'shot', type: 'button', disabled: !conn, onclick: () => actions.shot(item) }, t('shot')),
      h('button', { class: 'save', type: 'button', onclick: () => actions.save(item) }, t('save')),
      h('button', { class: 'done', type: 'button', onclick: () => actions.done(item) }, t('done'))));
}

function doneBox(view, item, entry) {
  const { t } = view;
  const done = entry.status === 'done';
  const locked = done && entry.sent;
  const label = t(locked ? 'doneSent' : done ? 'markOpen' : 'markDone');
  return h('button', {
    class: 'box', type: 'button', 'aria-pressed': String(done), 'aria-label': label, title: label,
    disabled: locked, onclick: () => view.actions.toggleDone(item),
  }, done ? '☑' : '☐');
}

function renderItem(view, item) {
  const entry = view.store.get(item.key);
  const open = view.expanded.has(item.key);
  const error = view.errors.get(item.key);
  return h('li', { class: `item ${entry.status}${open ? ' expanded' : ''}`, 'data-key': item.key },
    h('div', { class: 'row' },
      doneBox(view, item, entry), ' ',
      h('button', { class: 'text', 'aria-expanded': String(open), onclick: () => view.actions.toggleItem(item.key) }, item.text),
      goControl(view, item)),
    error ? h('p', { class: 'error', role: 'alert' }, error) : null,
    open ? editor(view, item, entry) : null);
}

function renderBlock(view, block) {
  const visible = block.items.filter((item) => matchesFilter(view, block, item));
  if (visible.length === 0) return null;
  const done = block.items.filter((item) => view.store.get(item.key).status === 'done').length;
  const total = block.items.length;
  const collapsed = view.collapsed.has(block.heading) ? view.collapsed.get(block.heading) : done === total;
  return h('section', { class: 'block', 'data-block': block.heading },
    h('button', { class: 'block-head', 'aria-expanded': String(!collapsed), onclick: () => view.actions.toggleBlock(block.heading, collapsed) },
      h('span', { class: 'block-title' }, `${collapsed ? '▸' : '▾'} ${block.heading}`),
      h('span', { class: 'progress' }, `${done} / ${total} ✓`)),
    collapsed ? null : h('ul', {}, visible.map((item) => renderItem(view, item))));
}

export function renderList(view) {
  const blocks = view.blocks.map((block) => renderBlock(view, block)).filter(Boolean);
  return blocks.length === 0 ? h('p', { class: 'empty' }, view.t('noItems')) : h('div', { class: 'list' }, blocks);
}
