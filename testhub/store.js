const KEY = 'gg-testhub';
const DEFAULT_ENTRY = { status: 'open', note: '', screenshots: [], sent: false };
const pad = (n) => String(n).padStart(2, '0');
const emptyState = () => ({ v: 1, items: {}, versions: {} });

export function getStorage() {
  try { return globalThis.localStorage || null; } catch (e) { return null; }
}

function readState(storage) {
  if (!storage) return emptyState();
  try {
    const parsed = JSON.parse(storage.getItem(KEY));
    const valid = parsed && typeof parsed === 'object' && !Array.isArray(parsed) && parsed.items && typeof parsed.items === 'object';
    if (!valid) return emptyState();
    return { v: 1, items: parsed.items, versions: parsed.versions && typeof parsed.versions === 'object' ? parsed.versions : {} };
  } catch (e) {
    return emptyState();
  }
}

export function createStore(storage) {
  const state = readState(storage);
  let persistent = Boolean(storage);

  function save() {
    if (!storage) { persistent = false; return; }
    try { storage.setItem(KEY, JSON.stringify(state)); } catch (e) { persistent = false; }
  }

  function get(key) {
    const stored = state.items[key] || {};
    return { ...DEFAULT_ENTRY, ...stored, screenshots: [...(stored.screenshots || [])] };
  }

  function update(key, patch) {
    const next = { ...get(key), ...patch };
    if (!('sent' in patch)) next.sent = false;
    state.items[key] = next;
    save();
  }

  function toggleDone(key, note) {
    const entry = get(key);
    if (entry.status === 'done') {
      if (entry.sent) return null;
      const status = entry.note.trim() || entry.screenshots.length ? 'noted' : 'open';
      update(key, { status });
      return status;
    }
    update(key, { status: 'done', note });
    return 'done';
  }

  function nextShotName(game, date) {
    const prefix = `fb-${game}-${pad(date.getMonth() + 1)}${pad(date.getDate())}-`;
    let highest = 0;
    for (const entry of Object.values(state.items)) {
      for (const name of entry.screenshots || []) {
        if (name.startsWith(prefix)) highest = Math.max(highest, parseInt(name.slice(prefix.length), 10) || 0);
      }
    }
    return `${prefix}${highest + 1}.png`;
  }

  return {
    get, update, toggleDone, nextShotName,
    setVersion(game, version) { state.versions[game] = version; save(); },
    version: (game) => state.versions[game] || '',
    isPersistent: () => persistent,
  };
}
