const KEY = 'gg-testhub';
const pad = (n) => String(n).padStart(2, '0');
const emptyState = () => ({ v: 1, items: {}, versions: {} });

function migrateEntry(stored) {
  const entry = stored && typeof stored === 'object' ? stored : {};
  if (Array.isArray(entry.notes)) {
    return { status: entry.status === 'done' ? 'done' : 'open', notes: entry.notes, draftShots: entry.draftShots || [], sent: Boolean(entry.sent) };
  }
  const text = typeof entry.note === 'string' ? entry.note : '';
  const screenshots = Array.isArray(entry.screenshots) ? entry.screenshots : [];
  const notes = text.trim() || screenshots.length ? [{ text, ts: null, screenshots: [...screenshots], sent: Boolean(entry.sent) }] : [];
  return { status: entry.status === 'done' ? 'done' : 'open', notes, draftShots: [], sent: Boolean(entry.sent) };
}
export function getStorage() {
  try { return globalThis.localStorage || null; } catch (e) { return null; }
}

function readState(storage) {
  if (!storage) return emptyState();
  try {
    const parsed = JSON.parse(storage.getItem(KEY));
    const valid = parsed && typeof parsed === 'object' && !Array.isArray(parsed) && parsed.items && typeof parsed.items === 'object';
    if (!valid) return emptyState();
    const items = Object.fromEntries(Object.entries(parsed.items).map(([key, value]) => [key, migrateEntry(value)]));
    return { v: 1, items, versions: parsed.versions && typeof parsed.versions === 'object' ? parsed.versions : {} };
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

  function raw(key) {
    return state.items[key] || { status: 'open', notes: [], draftShots: [], sent: false };
  }

  function get(key) {
    const stored = raw(key);
    const status = stored.status === 'done' ? 'done' : stored.notes.length ? 'noted' : 'open';
    return {
      status,
      notes: stored.notes.map((note) => ({ ...note, screenshots: [...note.screenshots] })),
      draftShots: [...stored.draftShots],
      sent: stored.sent,
    };
  }

  function write(key, patch) {
    state.items[key] = { ...raw(key), ...patch };
    save();
  }

  function update(key, patch) {
    write(key, 'sent' in patch ? patch : { ...patch, sent: false });
  }

  function addNote(key, text, ts) {
    const entry = raw(key);
    const clean = String(text).trim();
    if (!clean && entry.draftShots.length === 0) return false;
    write(key, { notes: [...entry.notes, { text: clean, ts, screenshots: [...entry.draftShots], sent: false }], draftShots: [] });
    return true;
  }

  function deleteNote(key, index) {
    const entry = raw(key);
    if (!entry.notes[index] || entry.notes[index].sent) return false;
    write(key, { notes: entry.notes.filter((note, i) => i !== index) });
    return true;
  }

  function addDraftShot(key, name) {
    write(key, { draftShots: [...raw(key).draftShots, name] });
  }

  function markSent(key, noteIndexes, done) {
    const entry = raw(key);
    write(key, { notes: entry.notes.map((note, i) => (noteIndexes.includes(i) ? { ...note, sent: true } : note)), sent: done ? true : entry.sent });
  }

  function toggleDone(key) {
    const entry = raw(key);
    if (entry.status === 'done') {
      if (entry.sent) return null;
      write(key, { status: 'open' });
      return get(key).status;
    }
    write(key, { status: 'done', sent: false });
    return 'done';
  }

  function nextShotName(game, date) {
    const prefix = `fb-${game}-${pad(date.getMonth() + 1)}${pad(date.getDate())}-`;
    let highest = 0;
    for (const entry of Object.values(state.items)) {
      const names = [...entry.draftShots, ...entry.notes.flatMap((note) => note.screenshots)];
      for (const name of names) {
        if (name.startsWith(prefix)) highest = Math.max(highest, parseInt(name.slice(prefix.length), 10) || 0);
      }
    }
    return `${prefix}${highest + 1}.png`;
  }

  return {
    get, update, addNote, deleteNote, addDraftShot, markSent, toggleDone, nextShotName,
    setVersion(game, version) { state.versions[game] = version; save(); },
    version: (game) => state.versions[game] || '',
    isPersistent: () => persistent,
  };
}
