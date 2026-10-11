export const STRINGS = {
  en: {
    title: 'Testhub',
    connected: 'Game connected (v{version} · {n} targets)',
    disconnected: 'No game window',
    openGame: 'Open the game with ?dev=1',
    filter_open: 'Open', filter_noted: 'Noted', filter_done: 'Done',
    search: 'Search…',
    copyAll: 'Copy all {n}',
    go: 'Go ▸',
    goUnknown: 'Unknown target',
    notePlaceholder: 'Note…',
    save: 'Save',
    done: '✓ Done',
    shot: '📷 Screenshot',
    loadError: 'Could not load test-todo.md for {game}: {reason}',
    noItems: 'Nothing to show.',
    noStorage: 'Storage is unavailable: notes are kept for this session only.',
    err_timeout: 'No answer from the game within 10 s.',
    err_noGame: 'No game window connected.',
    copied: 'Copied {n} entries.',
    copyManual: 'Copy was refused. Copy the text below by hand:',
    langToggle: 'DE',
  },
  de: {
    title: 'Testhub',
    connected: 'Spiel verbunden (v{version} · {n} Ziele)',
    disconnected: 'Kein Spielfenster',
    openGame: 'Spiel mit ?dev=1 öffnen',
    filter_open: 'Offen', filter_noted: 'Notiert', filter_done: 'Erledigt',
    search: 'Suchen…',
    copyAll: 'Alle kopieren {n}',
    go: 'Los ▸',
    goUnknown: 'Unbekanntes Ziel',
    notePlaceholder: 'Notiz…',
    save: 'Speichern',
    done: '✓ Erledigt',
    shot: '📷 Screenshot',
    loadError: 'test-todo.md für {game} konnte nicht geladen werden: {reason}',
    noItems: 'Nichts anzuzeigen.',
    noStorage: 'Speicher nicht verfügbar: Notizen gelten nur für diese Sitzung.',
    err_timeout: 'Keine Antwort vom Spiel innerhalb von 10 s.',
    err_noGame: 'Kein Spielfenster verbunden.',
    copied: '{n} Einträge kopiert.',
    copyManual: 'Kopieren wurde abgelehnt. Text unten von Hand kopieren:',
    langToggle: 'EN',
  },
};

export function detectLang(storage, navigatorLanguage) {
  let stored = null;
  try { stored = storage ? storage.getItem('gg-lang') : null; } catch (e) { stored = null; }
  if (stored === 'en' || stored === 'de') return stored;
  return String(navigatorLanguage || 'en').toLowerCase().startsWith('de') ? 'de' : 'en';
}

export function createT(lang) {
  const table = STRINGS[lang] || STRINGS.en;
  return (key, params = {}) => {
    const template = table[key] ?? STRINGS.en[key] ?? key;
    return template.replace(/\{(\w+)\}/g, (match, name) => (name in params ? String(params[name]) : match));
  };
}
