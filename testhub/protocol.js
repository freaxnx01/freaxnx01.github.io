export const CHANNEL = 'gg-testhub';

const ID_RE = /^[a-z0-9._-]+$/;
const MAX_TARGETS = 500;
const MAX_DATA_URL = 15 * 1024 * 1024;
const PNG_PREFIX = 'data:image/png;base64,';

const isString = (v, max = 300) => typeof v === 'string' && v.length <= max;
const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function validateTargets(list) {
  if (!Array.isArray(list) || list.length > MAX_TARGETS) return null;
  const out = [];
  for (const target of list) {
    const valid = isObject(target) && isString(target.id, 100) && ID_RE.test(target.id) && isString(target.label, 200);
    if (!valid) return null;
    out.push({ id: target.id, label: target.label });
  }
  return out;
}

function validateHello(msg) {
  const targets = validateTargets(msg.targets);
  if (!targets || !isString(msg.game, 100) || !isString(msg.version, 50)) return null;
  return { type: 'hello', game: msg.game, version: msg.version, targets };
}

export function validateGameMessage(msg) {
  if (!isObject(msg) || !isString(msg.type, 20)) return null;
  if (msg.type === 'hello') return validateHello(msg);
  if (!isString(msg.req, 100)) return null;
  if (msg.type === 'done') return { type: 'done', req: msg.req };
  if (msg.type === 'error') return isString(msg.message, 500) ? { type: 'error', req: msg.req, message: msg.message } : null;
  if (msg.type === 'png') {
    return isString(msg.dataUrl, MAX_DATA_URL) && msg.dataUrl.startsWith(PNG_PREFIX) ? { type: 'png', req: msg.req, dataUrl: msg.dataUrl } : null;
  }
  return null;
}

export const helloMsg = () => ({ type: 'hello' });
export const goMsg = (game, id, req) => ({ type: 'go', game, id, req });
export const screenshotMsg = (game, req) => ({ type: 'screenshot', game, req });
export const newReq = () => Math.random().toString(36).slice(2) + Date.now().toString(36);
