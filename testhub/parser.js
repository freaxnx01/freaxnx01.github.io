const TAG_RE = /\{go:\s*([a-z0-9._-]+)\s*\}/;
const TAG_STRIP_RE = /\s*\{go:\s*[a-z0-9._-]+\s*\}/g;
const H1_RE = /^#\s/;
const H2_RE = /^##\s+(.*\S)\s*$/;
const ITEM_RE = /^\s*- \[ \]\s+(.*\S)\s*$/;

export function splitTag(text) {
  const match = TAG_RE.exec(text);
  return { text: text.replace(TAG_STRIP_RE, '').replace(/\s+/g, ' ').trim(), tag: match ? match[1] : null };
}

export const itemKey = (game, heading, text) => `${game}|${heading}|${text}`;

export function parseTodo(markdown, game) {
  const blocks = [];
  let block = null;
  for (const line of markdown.split(/\r?\n/)) {
    if (H1_RE.test(line)) { block = null; continue; }
    const heading = H2_RE.exec(line);
    if (heading) {
      const { text, tag } = splitTag(heading[1]);
      block = { heading: text, tag, items: [] };
      blocks.push(block);
      continue;
    }
    const item = ITEM_RE.exec(line);
    if (!item || !block) continue;
    const { text, tag } = splitTag(item[1]);
    if (text) block.items.push({ key: itemKey(game, block.heading, text), text, tag: tag || block.tag });
  }
  return blocks.filter((b) => b.items.length > 0);
}
