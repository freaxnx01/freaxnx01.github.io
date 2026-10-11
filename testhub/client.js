// Classic script, loaded async by a game in dev mode only. Contract: window.ggTesthub = { setInfo({game, version}) once,
// register(id, fn, label) (sync fn, repeated id replaces), onScreenshot(fn) }; register after 'gg-testhub-ready' fires on window.
(function () {
  'use strict';
  if (window.ggTesthub) return;

  var ID_RE = /^[a-z0-9._-]+$/;
  var PNG_PREFIX = 'data:image/png;base64,';
  var targets = new Map();
  var info = { game: '', version: '' };
  var screenshotFn = null;
  var helloQueued = false;
  var channel = null;
  try { channel = new BroadcastChannel('gg-testhub'); } catch (e) { channel = null; }

  function send(message) { if (channel) channel.postMessage(message); }
  function isText(v, max) { return typeof v === 'string' && v.length <= max; }
  function isOptionalText(v) { return v === undefined || isText(v, 100); }

  function sendHello() {
    helloQueued = false;
    var list = [];
    targets.forEach(function (target, id) { list.push({ id: id, label: target.label }); });
    send({ type: 'hello', game: info.game, version: info.version, targets: list });
  }

  function queueHello() {
    if (helloQueued) return;
    helloQueued = true;
    setTimeout(sendHello, 0);
  }

  function fail(req, err) {
    send({ type: 'error', req: req || '', message: String(err && err.message ? err.message : err).slice(0, 500) });
  }

  function parse(m) {
    if (!m || typeof m !== 'object' || Array.isArray(m) || typeof m.type !== 'string') return null;
    if (m.type === 'hello') return m.targets === undefined ? { type: 'hello' } : null;
    if (!isOptionalText(m.game) || !isOptionalText(m.req)) return null;
    if (m.type === 'go') return isText(m.id, 100) && ID_RE.test(m.id) ? { type: 'go', game: m.game, id: m.id, req: m.req } : null;
    if (m.type === 'screenshot') return isText(m.req, 100) ? { type: 'screenshot', game: m.game, req: m.req } : null;
    return null;
  }

  function onGo(m) {
    var target = targets.get(m.id);
    if (!target) { fail(m.req, 'unknown target ' + m.id); return; }
    try { target.fn(); } catch (err) { fail(m.req, err); return; }
    send({ type: 'done', req: m.req || '' });
  }

  function onScreenshotRequest(m) {
    if (!screenshotFn) { fail(m.req, 'no screenshot handler'); return; }
    Promise.resolve().then(screenshotFn).then(function (url) {
      if (typeof url !== 'string' || url.indexOf(PNG_PREFIX) !== 0) throw new Error('screenshot is not a PNG data URL');
      send({ type: 'png', req: m.req, dataUrl: url });
    }).catch(function (err) { fail(m.req, err); });
  }

  if (channel) {
    channel.onmessage = function (event) {
      var m = parse(event.data);
      if (!m) return;
      if (m.type === 'hello') { sendHello(); return; }
      if (m.game && info.game && m.game !== info.game) return;
      if (m.type === 'go') onGo(m); else onScreenshotRequest(m);
    };
  }

  window.ggTesthub = {
    register: function (id, fn, label) {
      if (typeof id !== 'string' || !ID_RE.test(id)) throw new TypeError('ggTesthub.register: id must match [a-z0-9._-]+');
      if (typeof fn !== 'function') throw new TypeError('ggTesthub.register: fn must be a function');
      targets.set(id, { fn: fn, label: label ? String(label) : id });
      queueHello();
    },
    onScreenshot: function (fn) {
      if (typeof fn !== 'function') throw new TypeError('ggTesthub.onScreenshot: fn must be a function');
      screenshotFn = fn;
    },
    setInfo: function (next) {
      info = { game: String((next && next.game) || ''), version: String((next && next.version) || '') };
      queueHello();
    },
  };

  window.dispatchEvent(new Event('gg-testhub-ready'));
  queueHello();
})();
