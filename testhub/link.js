import { CHANNEL, validateGameMessage, helloMsg, goMsg, screenshotMsg, newReq } from './protocol.js';

export const REQUEST_TIMEOUT_MS = 10000;
const POLL_MS = 10000;
const STALE_MS = 25000;

function linkError(code, message) {
  const error = new Error(message || code);
  error.code = code;
  return error;
}

const signature = (c) => (c ? `${c.version}|${c.targets.map((x) => x.id).join(',')}` : '');

export function createLink({ game, onChange, timeoutMs = REQUEST_TIMEOUT_MS }) {
  const channel = typeof BroadcastChannel === 'function' ? new BroadcastChannel(CHANNEL) : null;
  const pending = new Map();
  let conn = null;

  function setConn(next) {
    const changed = signature(next) !== signature(conn);
    conn = next;
    if (changed) onChange();
  }

  function settle(msg) {
    const entry = pending.get(msg.req);
    if (!entry) return;
    pending.delete(msg.req);
    clearTimeout(entry.timer);
    if (msg.type === 'error') entry.reject(linkError('remote', msg.message)); else entry.resolve(msg);
  }

  function onMessage(raw) {
    const msg = validateGameMessage(raw);
    if (!msg) return;
    if (msg.type !== 'hello') { settle(msg); return; }
    if (msg.game === game) setConn({ version: msg.version, targets: msg.targets, seen: Date.now() });
  }

  function request(build) {
    if (!channel || !conn) return Promise.reject(linkError('noGame'));
    const req = newReq();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { pending.delete(req); reject(linkError('timeout')); }, timeoutMs);
      pending.set(req, { resolve, reject, timer });
      channel.postMessage(build(req));
    });
  }

  const hello = () => { if (channel) channel.postMessage(helloMsg()); };

  if (channel) channel.onmessage = (event) => onMessage(event.data);
  setInterval(() => {
    hello();
    if (conn && Date.now() - conn.seen > STALE_MS) setConn(null);
  }, POLL_MS);
  hello();

  return {
    get conn() { return conn; },
    go: (id) => request((req) => goMsg(game, id, req)),
    screenshot: () => request((req) => screenshotMsg(game, req)),
  };
}
