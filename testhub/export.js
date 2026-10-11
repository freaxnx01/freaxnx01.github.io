const pad = (n) => String(n).padStart(2, '0');

export const isoDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

function noteLine(entry) {
  const tag = entry.tag ? ` · go:${entry.tag}` : '';
  const note = entry.note.replace(/\s+/g, ' ').trim();
  const shots = entry.screenshots.length ? `(📷 ${entry.screenshots.join(', ')})` : '';
  return `- [${entry.block} · "${entry.text}"${tag}] ${[note, shots].filter(Boolean).join(' ')}`;
}

export function buildExport({ game, version, date, entries }) {
  const lines = [`Testhub feedback — ${game} ${version ? `v${version}` : 'version unknown'} — ${date}`];
  for (const entry of entries) {
    if (entry.note.trim() || entry.screenshots.length) lines.push(noteLine(entry));
    if (entry.status === 'done') lines.push(`- ✓ tested: [${entry.block} · "${entry.text}"]`);
  }
  return lines.join('\n');
}
