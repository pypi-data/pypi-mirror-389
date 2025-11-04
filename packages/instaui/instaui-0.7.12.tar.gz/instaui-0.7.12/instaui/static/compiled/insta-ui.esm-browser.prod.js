var mr = Object.defineProperty;
var gr = (e, t, n) => t in e ? mr(e, t, { enumerable: !0, configurable: !0, writable: !0, value: n }) : e[t] = n;
var T = (e, t, n) => gr(e, typeof t != "symbol" ? t + "" : t, n);
import * as yr from "vue";
import { toRaw as mn, toValue as Se, normalizeClass as ft, normalizeStyle as vr, cloneVNode as se, vModelDynamic as wr, vShow as _r, withDirectives as gn, h as J, toDisplayString as yn, withModifiers as Er, resolveDynamicComponent as br, normalizeProps as Sr, TransitionGroup as kr, createTextVNode as Rr, unref as q, toRef as me, readonly as Rt, customRef as ye, ref as z, onBeforeUnmount as Or, onMounted as vn, nextTick as ke, getCurrentScope as Pr, onScopeDispose as Nr, getCurrentInstance as Ge, watch as Q, isRef as Ot, shallowRef as ae, watchEffect as Pt, computed as L, isVNode as Vr, inject as ce, shallowReactive as Cr, defineComponent as ee, reactive as Ar, provide as K, onUnmounted as xr, onErrorCaptured as $r, openBlock as fe, createElementBlock as be, createElementVNode as wn, createVNode as Tr, createCommentVNode as dt, mergeProps as de, createBlock as _n, Teleport as Ir, renderSlot as Dr, useAttrs as Mr, Fragment as Br, useSlots as Me, KeepAlive as jr } from "vue";
let En;
function Lr(e) {
  En = e;
}
function We() {
  return En;
}
function ze() {
  const { queryPath: e, pathParams: t, queryParams: n } = We();
  return {
    path: e,
    ...t === void 0 ? {} : { params: t },
    ...n === void 0 ? {} : { queryParams: n }
  };
}
function Mt(e, t) {
  Object.entries(e).forEach(([n, r]) => t(r, n));
}
function qe(e, t) {
  return bn(e, {
    valueFn: t
  });
}
function bn(e, t) {
  const { valueFn: n, keyFn: r } = t;
  return Object.fromEntries(
    Object.entries(e).map(([s, o], i) => [
      r ? r(s, o) : s,
      n(o, s, i)
    ])
  );
}
function Fr(e, t, n) {
  if (Array.isArray(t)) {
    const [s, ...o] = t;
    switch (s) {
      case "!":
        return !e;
      case "+":
        return e + o[0];
      case "~+":
        return o[0] + e;
    }
  }
  const r = Ur(t);
  return e[r];
}
function Ur(e, t) {
  if (typeof e == "string" || typeof e == "number")
    return e;
  if (!Array.isArray(e))
    throw new Error(`Invalid path ${e}`);
  const [n, ...r] = e;
  switch (n) {
    case "bind":
      throw new Error("No bindable function provided");
    default:
      throw new Error(`Invalid flag ${n} in array at ${e}`);
  }
}
function Wr(e, t, n) {
  return t.reduce(
    (r, s) => Fr(r, s),
    e
  );
}
function zr(e, t) {
  return t ? t.reduce((n, r) => n[r], e) : e;
}
const Hr = window.structuredClone || ((e) => JSON.parse(JSON.stringify(e)));
function Nt(e) {
  if (typeof e == "function")
    return e;
  try {
    return Hr(mn(Se(e)));
  } catch {
    return e;
  }
}
function Kr(e, t) {
  const n = e.classes;
  if (!n)
    return null;
  if (typeof n == "string")
    return ft(n);
  const { str: r, map: s, bind: o } = n, { bindingGetter: i } = t, a = [];
  return r && a.push(r), s && a.push(
    qe(
      s,
      (c) => i.getValue(c)
    )
  ), o && a.push(...o.map((c) => i.getValue(c))), ft(a);
}
function Gr(e, t) {
  const n = [], { bindingGetter: r } = t, { dStyle: s = {}, sStyle: o = [] } = e;
  n.push(
    qe(
      s || {},
      (c) => r.getValue(c)
    )
  ), n.push(
    ...o.map((c) => r.getValue(c))
  );
  const i = vr([e.style || {}, n]);
  return {
    hasStyle: i && Object.keys(i).length > 0,
    styles: i
  };
}
function qr(e, t, n) {
  const r = [], { dir: s = [] } = t, { bindingGetter: o } = n;
  return s.forEach((i) => {
    const { sys: a, name: c, arg: d, value: u, mf: l } = i;
    if (c === "vmodel") {
      const f = o.getRef(u);
      if (e = se(e, {
        [`onUpdate:${d}`]: (h) => {
          f.value = h;
        }
      }), a === 1) {
        const h = l ? Object.fromEntries(l.map((m) => [m, !0])) : {};
        r.push([wr, f.value, void 0, h]);
      } else
        e = se(e, {
          [d]: f.value
        });
    } else if (c === "vshow") {
      const f = o.getValue(u);
      r.push([_r, f]);
    } else
      console.warn(`Directive ${c} is not supported yet`);
  }), r.length > 0 ? gn(e, r) : e;
}
function Te(e, t) {
  return J(ur, {
    config: e,
    vforSetting: t == null ? void 0 : t.vforSetting,
    slotSetting: t == null ? void 0 : t.slotSetting
  });
}
function Jr(e, t, n) {
  if (!e.slots)
    return;
  const r = e.slots ?? {};
  if (t) {
    const a = r[":"];
    if (!a)
      return;
    const { scope: c, items: d } = a;
    return c ? Te(c, {
      buildOptions: n
    }) : d == null ? void 0 : d.map((u) => ve(u, n));
  }
  return bn(r, { keyFn: (a) => a === ":" ? "default" : a, valueFn: (a) => {
    const { usePropId: c, scope: d } = a;
    return d ? (u) => Te(d, {
      buildOptions: n,
      slotSetting: c ? {
        id: c,
        value: u
      } : void 0
    }) : () => {
      var u;
      return (u = a.items) == null ? void 0 : u.map((l) => ve(l, n));
    };
  } });
}
function Y(e, t) {
  t = t || {};
  const n = [...Object.keys(t), "__Vue"], r = [...Object.values(t), yr];
  try {
    return new Function(...n, `return (${e})`)(...r);
  } catch (s) {
    throw new Error(s + " in function code: " + e);
  }
}
function He(e, t = !0) {
  if (!(typeof e != "object" || e === null)) {
    if (Array.isArray(e)) {
      t && e.forEach((n) => He(n, !0));
      return;
    }
    for (const [n, r] of Object.entries(e))
      if (n.startsWith(":"))
        try {
          e[n.slice(1)] = new Function(`return (${r})`)(), delete e[n];
        } catch (s) {
          console.error(
            `Error while converting ${n} attribute to function:`,
            s
          );
        }
      else
        t && He(r, !0);
  }
}
function Qr(e, t) {
  const n = e.startsWith(":");
  return n && (e = e.slice(1), t = Y(t)), { name: e, value: t, isFunc: n };
}
class Yr {
  toString() {
    return "";
  }
}
const Ie = new Yr();
function Re(e) {
  return mn(e) === Ie;
}
function Xr(e, t) {
  var o;
  const n = {}, r = e.props ?? {}, { bindingGetter: s } = t;
  return He(r), Mt(e.bProps || {}, (i, a) => {
    const c = s.getValue(i);
    Re(c) || (He(c), n[a] = Zr(c, a));
  }), (o = e.proxyProps) == null || o.forEach((i) => {
    const a = s.getValue(i);
    typeof a == "object" && Mt(a, (c, d) => {
      const { name: u, value: l } = Qr(d, c);
      n[u] = l;
    });
  }), { ...r, ...n };
}
function Zr(e, t) {
  return t === "innerText" ? yn(e) : e;
}
class es {
  async eventSend(t, n) {
    const { fType: r, hKey: s, key: o } = t, i = We().webServerInfo, a = o !== void 0 ? { key: o } : {}, c = r === "sync" ? i.event_url : i.event_async_url;
    let d = {};
    const u = await fetch(c, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        bind: n,
        hKey: s,
        ...a,
        page: ze(),
        ...d
      })
    });
    if (!u.ok)
      throw new Error(`HTTP error! status: ${u.status}`);
    return await u.json();
  }
  async watchSend(t) {
    const { fType: n, key: r } = t.watchConfig, s = We().webServerInfo, o = n === "sync" ? s.watch_url : s.watch_async_url, i = t.getServerInputs(), a = {
      key: r,
      input: i,
      page: ze()
    };
    return await (await fetch(o, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(a)
    })).json();
  }
}
class ts {
  async eventSend(t, n) {
    const { fType: r, hKey: s, key: o } = t, i = o !== void 0 ? { key: o } : {};
    let a = {};
    const c = {
      bind: n,
      fType: r,
      hKey: s,
      ...i,
      page: ze(),
      ...a
    };
    return await window.pywebview.api.event_call(c);
  }
  async watchSend(t) {
    const { fType: n, key: r } = t.watchConfig, s = t.getServerInputs(), o = {
      key: r,
      input: s,
      fType: n,
      page: ze()
    };
    return await window.pywebview.api.watch_call(o);
  }
}
let ht;
function ns(e) {
  switch (e) {
    case "web":
      ht = new es();
      break;
    case "webview":
      ht = new ts();
      break;
  }
}
function Sn() {
  return ht;
}
function kn(e) {
  const { config: t, bindingGetter: n } = e;
  if (!t)
    return {
      run: () => {
      },
      tryReset: () => {
      }
    };
  const r = t.map((i) => {
    const [a, c, d] = i, u = n.getRef(a);
    function l(f, h) {
      const { type: m, value: p } = h;
      if (m === "const") {
        f.value = p;
        return;
      }
      if (m === "action") {
        const y = rs(p, n);
        f.value = y;
        return;
      }
    }
    return {
      run: () => l(u, c),
      reset: () => l(u, d)
    };
  });
  return {
    run: () => {
      r.forEach((i) => i.run());
    },
    tryReset: () => {
      r.forEach((i) => i.reset());
    }
  };
}
function rs(e, t) {
  const { inputs: n = [], code: r } = e, s = Y(r), o = n.map((i) => t.getValue(i));
  return s(...o);
}
function Bt(e) {
  return e == null;
}
const re = {
  Ref: 0,
  EventContext: 1,
  Data: 2,
  JsFn: 3,
  ElementRef: 4,
  EventContextDataset: 5
}, jt = {
  const: "c",
  ref: "r",
  range: "n"
}, Ee = {
  Ref: 0,
  RouterAction: 1,
  ElementRefAction: 2,
  JsCode: 3,
  FileDownload: 4
};
class Rn extends Error {
  constructor(t) {
    super(t), this.name = "BrowserNotSupportedError";
  }
}
function On(e, t) {
  switch (t) {
    case "kb":
      return e * 1024;
    case "mb":
      return e * 1024 * 1024;
    case "gb":
      return e * 1024 * 1024 * 1024;
    default:
      return e;
  }
}
class ss {
  constructor(t, n) {
    T(this, "filename");
    T(this, "filepath");
    T(this, "chuckedConfig");
    T(this, "onProgress");
    T(this, "onStatus");
    T(this, "controller", null);
    T(this, "receivedBytes", 0);
    T(this, "totalBytes", 0);
    T(this, "chunks", []);
    T(this, "downloading", !1);
    this.url = t, this.filename = n.filename, this.filepath = n.filepath, this.chuckedConfig = n.config, this.onProgress = () => {
    }, this.onStatus = () => {
    };
  }
  async start() {
    this.downloading || (this.downloading = !0, await this.fetchChunk(this.receivedBytes));
  }
  pause() {
    var t;
    this.downloading && (this.downloading = !1, (t = this.controller) == null || t.abort());
  }
  async resume() {
    this.downloading || (this.downloading = !0, await this.fetchChunk(this.receivedBytes));
  }
  async fetchChunk(t) {
    var d;
    this.controller = new AbortController();
    const n = On(
      this.chuckedConfig.chunk_size,
      this.chuckedConfig.chunk_size_unit
    ), r = new URLSearchParams({
      filepath: this.filepath,
      mode: "chunked",
      chunk_bytes: n.toString()
    }), s = `${this.url}?` + r.toString(), o = t ? { Range: `bytes=${t}-` } : {}, i = await fetch(s, {
      headers: o,
      signal: this.controller.signal
    });
    if (!i.ok && i.status !== 206 && i.status !== 200) {
      this.downloading = !1;
      return;
    }
    const a = i.headers.get("Content-Range");
    this.totalBytes = a && parseInt(a.split("/")[1]) || parseInt(i.headers.get("Content-Length") || "0", 10);
    const c = (d = i.body) == null ? void 0 : d.getReader();
    if (!c)
      throw new Rn("Browser does not support streaming download");
    for (; this.downloading; ) {
      const { done: u, value: l } = await c.read();
      if (u) break;
      l && (this.chunks.push(l), this.receivedBytes += l.length, this.updateProgress());
    }
    this.receivedBytes >= this.totalBytes && this.finish();
  }
  updateProgress() {
    if (this.totalBytes > 0) {
      const t = parseFloat(
        (this.receivedBytes / this.totalBytes * 100).toFixed(2)
      );
      this.onProgress(t);
    } else
      (this.receivedBytes / 1024 / 1024).toFixed(2);
  }
  finish() {
    this.downloading = !1;
    const t = this.chunks.reduce(
      (i, a) => i + a.length,
      0
    ), n = new Uint8Array(t);
    let r = 0;
    for (const i of this.chunks)
      n.set(i, r), r += i.length;
    const s = new Blob([n]), o = document.createElement("a");
    o.href = URL.createObjectURL(s), o.download = this.filename, o.click(), URL.revokeObjectURL(o.href), this.chunks = [];
  }
  get progress() {
    return { received: this.receivedBytes, total: this.totalBytes };
  }
  get isDownloading() {
    return this.downloading;
  }
}
class pt {
  constructor(t, n) {
    T(this, "filename");
    T(this, "filepath");
    T(this, "onProgress");
    T(this, "onStatus");
    T(this, "controller", null);
    T(this, "receivedBytes", 0);
    T(this, "totalBytes", 0);
    T(this, "downloading", !1);
    this.url = t, this.filename = n.filename, this.filepath = n.filepath, this.onProgress = () => {
    }, this.onStatus = () => {
    };
  }
  async start() {
    this.downloading || (this.downloading = !0, await this.downloadFile());
  }
  pause() {
    var t;
    this.downloading && (this.downloading = !1, (t = this.controller) == null || t.abort());
  }
  async downloadFile() {
    var r;
    this.controller = new AbortController();
    const t = new URLSearchParams({ filepath: this.filepath }), n = `${this.url}?` + t.toString();
    try {
      const s = await fetch(n, {
        signal: this.controller.signal
      });
      if (!s.ok) {
        this.onStatus(`Download failed: ${s.statusText}`), this.downloading = !1;
        return;
      }
      this.totalBytes = parseInt(s.headers.get("Content-Length") || "0", 10);
      const o = (r = s.body) == null ? void 0 : r.getReader();
      if (!o) {
        this.onStatus("Web Browser not support download file"), this.downloading = !1;
        return;
      }
      const i = [];
      for (; this.downloading; ) {
        const { done: a, value: c } = await o.read();
        if (a) break;
        c && (i.push(c), this.receivedBytes += c.length, this.updateProgress());
      }
      this.receivedBytes >= this.totalBytes && this.finishDownload(i);
    } catch (s) {
      this.onStatus(`Download error: ${s instanceof Error ? s.message : String(s)}`), this.downloading = !1;
    }
  }
  updateProgress() {
    if (this.totalBytes > 0) {
      const t = parseFloat(
        (this.receivedBytes / this.totalBytes * 100).toFixed(2)
      );
      this.onProgress(t);
    }
  }
  finishDownload(t) {
    this.downloading = !1;
    const n = t.reduce((a, c) => a + c.length, 0), r = new Uint8Array(n);
    let s = 0;
    for (const a of t)
      r.set(a, s), s += a.length;
    const o = new Blob([r]), i = document.createElement("a");
    i.href = URL.createObjectURL(o), i.download = this.filename, i.click(), URL.revokeObjectURL(i.href);
  }
  get progress() {
    return { received: this.receivedBytes, total: this.totalBytes };
  }
  get isDownloading() {
    return this.downloading;
  }
}
async function os(e) {
  const t = We().webServerInfo.download_url;
  if (e.mode === "auto") {
    if (!e.config)
      throw new Error("Auto mode requires config parameters");
    const n = e.config, r = On(
      n.threshold_size,
      n.threshold_size_unit
    );
    e.filesize < r ? await new pt(t, e).start() : await Lt(t, e);
    return;
  }
  if (e.mode === "chunked") {
    await Lt(t, e);
    return;
  }
  if (e.mode === "standard") {
    await new pt(t, e).start();
    return;
  }
}
async function Lt(e, t) {
  try {
    await new ss(e, t).start();
  } catch (n) {
    if (n instanceof Rn)
      await new pt(e, t).start();
    else
      throw n;
  }
}
function Je(e, t, n) {
  if (Bt(t) || Bt(e.values))
    return;
  t = t;
  const r = e.values, s = e.types ?? Array.from({ length: t.length }).fill(0);
  t.forEach((o, i) => {
    const a = s[i];
    if (a === 1)
      return;
    if (o.type === Ee.Ref) {
      if (a === 2) {
        r[i].forEach(([u, l]) => {
          const f = o.ref, h = {
            ...f,
            path: [...f.path ?? [], ...u]
          };
          n.updateValue(h, l);
        });
        return;
      }
      n.updateValue(o.ref, r[i]);
      return;
    }
    if (o.type === Ee.RouterAction) {
      const d = r[i], u = n.getRouter(o.ref)[d.fn];
      u(...d.args);
      return;
    }
    if (o.type === Ee.ElementRefAction) {
      const d = o.ref, u = n.getRef(d).value, l = r[i], { method: f, args: h = [] } = l;
      u[f](...h);
      return;
    }
    if (o.type === Ee.JsCode) {
      const d = r[i];
      if (!d)
        return;
      const u = Y(d);
      Promise.resolve(u());
      return;
    }
    if (o.type === Ee.FileDownload) {
      const d = r[i];
      os(d);
      return;
    }
    const c = n.getRef(o.ref);
    c.value = r[i];
  });
}
class is extends Map {
  constructor(t) {
    super(), this.factory = t;
  }
  getOrDefault(t) {
    if (!this.has(t)) {
      const n = this.factory();
      return this.set(t, n), n;
    }
    return super.get(t);
  }
}
function Pn(e) {
  return new is(e);
}
const as = "on:mounted";
function cs(e, t, n) {
  if (!t)
    return e;
  const r = Pn(() => []);
  t.map(([a, c]) => {
    const d = ls(c, n), { eventName: u, handleEvent: l } = ps({
      eventName: a,
      info: c,
      handleEvent: d
    });
    r.getOrDefault(u).push(l);
  });
  const s = {};
  for (const [a, c] of r) {
    const d = c.length === 1 ? c[0] : (...u) => c.forEach((l) => Promise.resolve().then(() => l(...u)));
    s[a] = d;
  }
  const { [as]: o, ...i } = s;
  return e = se(e, i), o && (e = gn(e, [
    [
      {
        mounted(a) {
          o(a);
        }
      }
    ]
  ])), e;
}
function ls(e, t) {
  if (e.type === "web") {
    const n = us(e, t);
    return fs(e, n, t);
  } else {
    if (e.type === "vue")
      return hs(e, t);
    if (e.type === "js")
      return ds(e, t);
  }
  throw new Error(`unknown event type ${e}`);
}
function us(e, t) {
  const { inputs: n = [] } = e, { bindingGetter: r } = t;
  return (...s) => n.map(({ value: o, type: i }) => {
    if (i === re.EventContext || i === re.EventContextDataset) {
      const { path: a } = o;
      if (a.startsWith(":")) {
        const c = a.slice(1);
        return Y(c)(...s);
      }
      return zr(s[0], a.split("."));
    }
    return i === re.Ref ? r.getValue(o) : o;
  });
}
function fs(e, t, n) {
  const { bindingGetter: r } = n;
  async function s(...o) {
    const i = t(...o), a = kn({
      config: e.preSetup,
      bindingGetter: r
    });
    try {
      a.run();
      const c = await Sn().eventSend(e, i);
      if (!c)
        return;
      Je(c, e.sets, r);
    } finally {
      a.tryReset();
    }
  }
  return s;
}
function ds(e, t) {
  const { sets: n, code: r, inputs: s = [] } = e, { bindingGetter: o } = t, i = Y(r);
  async function a(...c) {
    const d = s.map(({ value: l, type: f }) => {
      const h = f === re.EventContextDataset;
      if (f === re.EventContext || h) {
        if (l.path.startsWith(":")) {
          const m = l.path.slice(1), p = Y(m)(...c);
          return p == null ? p : h ? JSON.parse(p) : p;
        }
        return Wr(c[0], l.path.split("."));
      }
      if (f === re.Ref)
        return o.getValue(l);
      if (f === re.Data)
        return l;
      if (f === re.ElementRef || f === re.JsFn)
        return o.getValue(l);
      throw new Error(`unknown input type ${f}`);
    }), u = await i(...d);
    if (n !== void 0) {
      const f = n.length === 1 ? [u] : u, h = f.map((m) => m === void 0 ? 1 : 0);
      Je(
        { values: f, types: h },
        n,
        o
      );
    }
  }
  return a;
}
function hs(e, t) {
  const { code: n, inputs: r = {} } = e, { bindingGetter: s } = t, o = qe(
    r,
    (c) => c.type !== re.Data ? s.getRef(c.value) : c.value
  ), i = Y(n, o);
  function a(...c) {
    i(...c);
  }
  return a;
}
function ps(e) {
  const { eventName: t, info: n, handleEvent: r } = e;
  if (n.type === "vue")
    return {
      eventName: t,
      handleEvent: r
    };
  const { modifier: s = [] } = n;
  if (s.length === 0)
    return {
      eventName: t,
      handleEvent: r
    };
  const o = ["passive", "capture", "once"], i = [], a = [];
  for (const u of s)
    o.includes(u) ? i.push(u[0].toUpperCase() + u.slice(1)) : a.push(u);
  const c = i.length > 0 ? t + i.join("") : t, d = a.length > 0 ? Er(r, a) : r;
  return {
    eventName: c,
    handleEvent: d
  };
}
function ms(e, t, n) {
  const { eRef: r } = t, { bindingGetter: s } = n;
  return r ? se(e, { ref: s.getRef(r) }) : e;
}
function gs(e, t) {
  const n = ys(e, t), r = br(n), s = typeof r == "string", o = Kr(e, t), { styles: i, hasStyle: a } = Gr(e, t), c = Jr(e, s, t), d = Xr(e, t), u = Sr(d) || {};
  a && (u.style = i), o && (u.class = o);
  let l = J(r, { ...u }, c);
  return l = cs(l, e.events, t), l = ms(l, e, t), qr(l, e, t);
}
function ys(e, t) {
  const { tag: n } = e;
  return typeof n == "string" ? n : t.bindingGetter.getValue(n);
}
function vs(e, t) {
  var l, f, h;
  const { fkey: n, tsGroup: r = {}, scope: s } = e, o = !!((l = e.used) != null && l.item), i = !!((f = e.used) != null && f.index), a = !!((h = e.used) != null && h.key), c = [], { sourceInfo: d, iterSource: u } = ws(e, t);
  for (const [m, p, y] of u) {
    const w = {};
    o && (w.item = {
      value: p,
      id: e.used.item
    }, d && (w.item.sourceInfo = {
      source: d.source,
      type: d.type,
      index: m,
      key: y
    })), i && (w.index = {
      value: m,
      id: e.used.index
    }), a && (w.key = {
      value: y,
      id: e.used.key
    });
    let _ = Te(s, {
      buildOptions: t,
      vforSetting: w
    });
    const S = bs(n, { value: p, index: m });
    _ = se(_, { key: S }), c.push(_);
  }
  return r && Object.keys(r).length > 0 ? J(kr, r, {
    default: () => c
  }) : c;
}
function ws(e, t) {
  const { type: n, value: r } = e.array, { bindingGetter: s } = t, o = n === jt.range, i = n === jt.const || o && typeof r == "number";
  if (o) {
    const { start: a = 0, end: c, step: d = 1 } = r, u = typeof a == "number" ? a : s.getValue(a), l = typeof c == "number" ? c : s.getValue(c), f = typeof d == "number" ? d : s.getValue(d);
    return {
      sourceInfo: void 0,
      iterSource: Ft(u, l, f)
    };
  }
  {
    const a = i ? r : s.getValue(e.array.value);
    if (typeof a == "number")
      return {
        sourceInfo: void 0,
        iterSource: Ft(0, a, 1)
      };
    if (Array.isArray(a)) {
      function* c() {
        for (let d = 0; d < a.length; d++)
          yield [d, a[d]];
      }
      return {
        sourceInfo: i ? void 0 : {
          source: s.getRef(e.array.value),
          type: "array"
        },
        iterSource: c()
      };
    }
    if (typeof a == "object" && a !== null) {
      function* c() {
        let d = 0;
        for (const [u, l] of Object.entries(a))
          yield [d++, l, u];
      }
      return {
        sourceInfo: i ? void 0 : {
          source: s.getRef(e.array.value),
          type: "object"
        },
        iterSource: c()
      };
    }
    if (Re(a))
      return a;
  }
  throw new Error("Not implemented yet");
}
function* Ft(e, t, n = 1) {
  if (n === 0)
    throw new Error("Step cannot be 0");
  let r = 0;
  if (n > 0)
    for (let s = e; s < t; s += n)
      yield [r++, s];
  else
    for (let s = e; s > t; s += n)
      yield [r++, s];
}
const _s = (e) => e, Es = (e, t) => t;
function bs(e, t) {
  const { value: n, index: r } = t, s = Ss(e ?? "index");
  return typeof s == "function" ? s(n, r) : e === "item" ? _s(n) : Es(n, r);
}
function Ss(e) {
  const t = e.trim();
  if (t === "item" || t === "index")
    return;
  if (e.startsWith(":")) {
    e = e.slice(1);
    try {
      return Y(e);
    } catch (r) {
      throw new Error(r + " in function code: " + e);
    }
  }
  const n = `(item, index) => { return ${t}; }`;
  try {
    return Y(n);
  } catch (r) {
    throw new Error(r + " in function code: " + n);
  }
}
function ks(e, t) {
  const { on: n, items: r } = e;
  return (typeof n == "boolean" ? n : t.bindingGetter.getValue(n)) ? r == null ? void 0 : r.map((o) => ve(o, t)) : void 0;
}
function Rs(e, t) {
  const { cond: n, const: r = 0, cases: s, default: o } = e, a = r === 1 ? n : t.bindingGetter.getValue(n), c = [];
  let d = !1;
  for (const { value: u, items: l = [] } of s || [])
    if (u === a) {
      c.push(...l.map((f) => ve(f, t))), d = !0;
      break;
    }
  return !d && o && o.items && c.push(
    ...o.items.map((u) => ve(u, t))
  ), c;
}
function Os(e, t) {
  const { value: n, r = 0 } = e, s = r === 1 ? t.bindingGetter.getValue(n) : n;
  return Rr(s);
}
const Ps = /* @__PURE__ */ new Map(
  [
    ["vfor", vs],
    ["vif", ks],
    ["match", Rs],
    ["content", Os]
  ]
);
function Ns(e, t) {
  const n = Ps.get(e.tag);
  if (!n)
    throw new Error(`Unknown logic component ${e.tag}`);
  return n(e, t);
}
function ve(e, t) {
  const { type: n } = e;
  if (n === "cp")
    return gs(e, t);
  if (n === "logic")
    return Ns(e, t);
  if (n === "scope")
    return Te(e, {
      buildOptions: t
    });
  throw new Error(`Unknown component type ${n}`);
}
function Nn(e) {
  return "r" in e;
}
function Vt(e) {
  return Pr() ? (Nr(e), !0) : !1;
}
function ne(e) {
  return typeof e == "function" ? e() : q(e);
}
const Vn = typeof window < "u" && typeof document < "u";
typeof WorkerGlobalScope < "u" && globalThis instanceof WorkerGlobalScope;
const Vs = (e) => e != null, Cs = Object.prototype.toString, As = (e) => Cs.call(e) === "[object Object]", De = () => {
};
function xs(e, t) {
  function n(...r) {
    return new Promise((s, o) => {
      Promise.resolve(e(() => t.apply(this, r), { fn: t, thisArg: this, args: r })).then(s).catch(o);
    });
  }
  return n;
}
const Cn = (e) => e();
function $s(e = Cn) {
  const t = z(!0);
  function n() {
    t.value = !1;
  }
  function r() {
    t.value = !0;
  }
  const s = (...o) => {
    t.value && e(...o);
  };
  return { isActive: Rt(t), pause: n, resume: r, eventFilter: s };
}
function mt(e, t = !1, n = "Timeout") {
  return new Promise((r, s) => {
    setTimeout(t ? () => s(n) : r, e);
  });
}
function An(e) {
  return Ge();
}
function xn(...e) {
  if (e.length !== 1)
    return me(...e);
  const t = e[0];
  return typeof t == "function" ? Rt(ye(() => ({ get: t, set: De }))) : z(t);
}
function Ts(e, t, n = {}) {
  const {
    eventFilter: r = Cn,
    ...s
  } = n;
  return Q(
    e,
    xs(
      r,
      t
    ),
    s
  );
}
function Is(e, t, n = {}) {
  const {
    eventFilter: r,
    ...s
  } = n, { eventFilter: o, pause: i, resume: a, isActive: c } = $s(r);
  return { stop: Ts(
    e,
    t,
    {
      ...s,
      eventFilter: o
    }
  ), pause: i, resume: a, isActive: c };
}
function Ds(e, t) {
  An() && Or(e, t);
}
function $n(e, t = !0, n) {
  An() ? vn(e, n) : t ? e() : ke(e);
}
function gt(e, t = !1) {
  function n(l, { flush: f = "sync", deep: h = !1, timeout: m, throwOnTimeout: p } = {}) {
    let y = null;
    const _ = [new Promise((S) => {
      y = Q(
        e,
        (v) => {
          l(v) !== t && (y ? y() : ke(() => y == null ? void 0 : y()), S(v));
        },
        {
          flush: f,
          deep: h,
          immediate: !0
        }
      );
    })];
    return m != null && _.push(
      mt(m, p).then(() => ne(e)).finally(() => y == null ? void 0 : y())
    ), Promise.race(_);
  }
  function r(l, f) {
    if (!Ot(l))
      return n((v) => v === l, f);
    const { flush: h = "sync", deep: m = !1, timeout: p, throwOnTimeout: y } = f ?? {};
    let w = null;
    const S = [new Promise((v) => {
      w = Q(
        [e, l],
        ([R, A]) => {
          t !== (R === A) && (w ? w() : ke(() => w == null ? void 0 : w()), v(R));
        },
        {
          flush: h,
          deep: m,
          immediate: !0
        }
      );
    })];
    return p != null && S.push(
      mt(p, y).then(() => ne(e)).finally(() => (w == null || w(), ne(e)))
    ), Promise.race(S);
  }
  function s(l) {
    return n((f) => !!f, l);
  }
  function o(l) {
    return r(null, l);
  }
  function i(l) {
    return r(void 0, l);
  }
  function a(l) {
    return n(Number.isNaN, l);
  }
  function c(l, f) {
    return n((h) => {
      const m = Array.from(h);
      return m.includes(l) || m.includes(ne(l));
    }, f);
  }
  function d(l) {
    return u(1, l);
  }
  function u(l = 1, f) {
    let h = -1;
    return n(() => (h += 1, h >= l), f);
  }
  return Array.isArray(ne(e)) ? {
    toMatch: n,
    toContains: c,
    changed: d,
    changedTimes: u,
    get not() {
      return gt(e, !t);
    }
  } : {
    toMatch: n,
    toBe: r,
    toBeTruthy: s,
    toBeNull: o,
    toBeNaN: a,
    toBeUndefined: i,
    changed: d,
    changedTimes: u,
    get not() {
      return gt(e, !t);
    }
  };
}
function Ms(e) {
  return gt(e);
}
function Bs(e, t, n) {
  let r;
  Ot(n) ? r = {
    evaluating: n
  } : r = n || {};
  const {
    lazy: s = !1,
    evaluating: o = void 0,
    shallow: i = !0,
    onError: a = De
  } = r, c = z(!s), d = i ? ae(t) : z(t);
  let u = 0;
  return Pt(async (l) => {
    if (!c.value)
      return;
    u++;
    const f = u;
    let h = !1;
    o && Promise.resolve().then(() => {
      o.value = !0;
    });
    try {
      const m = await e((p) => {
        l(() => {
          o && (o.value = !1), h || p();
        });
      });
      f === u && (d.value = m);
    } catch (m) {
      a(m);
    } finally {
      o && f === u && (o.value = !1), h = !0;
    }
  }), s ? L(() => (c.value = !0, d.value)) : d;
}
const Oe = Vn ? window : void 0, js = Vn ? window.document : void 0;
function Ct(e) {
  var t;
  const n = ne(e);
  return (t = n == null ? void 0 : n.$el) != null ? t : n;
}
function Ut(...e) {
  let t, n, r, s;
  if (typeof e[0] == "string" || Array.isArray(e[0]) ? ([n, r, s] = e, t = Oe) : [t, n, r, s] = e, !t)
    return De;
  Array.isArray(n) || (n = [n]), Array.isArray(r) || (r = [r]);
  const o = [], i = () => {
    o.forEach((u) => u()), o.length = 0;
  }, a = (u, l, f, h) => (u.addEventListener(l, f, h), () => u.removeEventListener(l, f, h)), c = Q(
    () => [Ct(t), ne(s)],
    ([u, l]) => {
      if (i(), !u)
        return;
      const f = As(l) ? { ...l } : l;
      o.push(
        ...n.flatMap((h) => r.map((m) => a(u, h, m, f)))
      );
    },
    { immediate: !0, flush: "post" }
  ), d = () => {
    c(), i();
  };
  return Vt(d), d;
}
function Ls() {
  const e = z(!1), t = Ge();
  return t && vn(() => {
    e.value = !0;
  }, t), e;
}
function Tn(e) {
  const t = Ls();
  return L(() => (t.value, !!e()));
}
function Fs(e, t, n = {}) {
  const { window: r = Oe, ...s } = n;
  let o;
  const i = Tn(() => r && "MutationObserver" in r), a = () => {
    o && (o.disconnect(), o = void 0);
  }, c = L(() => {
    const f = ne(e), h = (Array.isArray(f) ? f : [f]).map(Ct).filter(Vs);
    return new Set(h);
  }), d = Q(
    () => c.value,
    (f) => {
      a(), i.value && f.size && (o = new MutationObserver(t), f.forEach((h) => o.observe(h, s)));
    },
    { immediate: !0, flush: "post" }
  ), u = () => o == null ? void 0 : o.takeRecords(), l = () => {
    d(), a();
  };
  return Vt(l), {
    isSupported: i,
    stop: l,
    takeRecords: u
  };
}
function Us(e, t, n) {
  const {
    immediate: r = !0,
    delay: s = 0,
    onError: o = De,
    onSuccess: i = De,
    resetOnExecute: a = !0,
    shallow: c = !0,
    throwError: d
  } = {}, u = c ? ae(t) : z(t), l = z(!1), f = z(!1), h = ae(void 0);
  async function m(w = 0, ..._) {
    a && (u.value = t), h.value = void 0, l.value = !1, f.value = !0, w > 0 && await mt(w);
    const S = typeof e == "function" ? e(..._) : e;
    try {
      const v = await S;
      u.value = v, l.value = !0, i(v);
    } catch (v) {
      if (h.value = v, o(v), d)
        throw v;
    } finally {
      f.value = !1;
    }
    return u.value;
  }
  r && m(s);
  const p = {
    state: u,
    isReady: l,
    isLoading: f,
    error: h,
    execute: m
  };
  function y() {
    return new Promise((w, _) => {
      Ms(f).toBe(!1).then(() => w(p)).catch(_);
    });
  }
  return {
    ...p,
    then(w, _) {
      return y().then(w, _);
    }
  };
}
function Ws(e, t = {}) {
  const { window: n = Oe } = t, r = Tn(() => n && "matchMedia" in n && typeof n.matchMedia == "function");
  let s;
  const o = z(!1), i = (d) => {
    o.value = d.matches;
  }, a = () => {
    s && ("removeEventListener" in s ? s.removeEventListener("change", i) : s.removeListener(i));
  }, c = Pt(() => {
    r.value && (a(), s = n.matchMedia(ne(e)), "addEventListener" in s ? s.addEventListener("change", i) : s.addListener(i), o.value = s.matches);
  });
  return Vt(() => {
    c(), a(), s = void 0;
  }), o;
}
const Le = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {}, Fe = "__vueuse_ssr_handlers__", zs = /* @__PURE__ */ Hs();
function Hs() {
  return Fe in Le || (Le[Fe] = Le[Fe] || {}), Le[Fe];
}
function In(e, t) {
  return zs[e] || t;
}
function Ks(e) {
  return Ws("(prefers-color-scheme: dark)", e);
}
function Gs(e) {
  return e == null ? "any" : e instanceof Set ? "set" : e instanceof Map ? "map" : e instanceof Date ? "date" : typeof e == "boolean" ? "boolean" : typeof e == "string" ? "string" : typeof e == "object" ? "object" : Number.isNaN(e) ? "any" : "number";
}
const qs = {
  boolean: {
    read: (e) => e === "true",
    write: (e) => String(e)
  },
  object: {
    read: (e) => JSON.parse(e),
    write: (e) => JSON.stringify(e)
  },
  number: {
    read: (e) => Number.parseFloat(e),
    write: (e) => String(e)
  },
  any: {
    read: (e) => e,
    write: (e) => String(e)
  },
  string: {
    read: (e) => e,
    write: (e) => String(e)
  },
  map: {
    read: (e) => new Map(JSON.parse(e)),
    write: (e) => JSON.stringify(Array.from(e.entries()))
  },
  set: {
    read: (e) => new Set(JSON.parse(e)),
    write: (e) => JSON.stringify(Array.from(e))
  },
  date: {
    read: (e) => new Date(e),
    write: (e) => e.toISOString()
  }
}, Wt = "vueuse-storage";
function yt(e, t, n, r = {}) {
  var s;
  const {
    flush: o = "pre",
    deep: i = !0,
    listenToStorageChanges: a = !0,
    writeDefaults: c = !0,
    mergeDefaults: d = !1,
    shallow: u,
    window: l = Oe,
    eventFilter: f,
    onError: h = (N) => {
      console.error(N);
    },
    initOnMounted: m
  } = r, p = (u ? ae : z)(typeof t == "function" ? t() : t);
  if (!n)
    try {
      n = In("getDefaultStorage", () => {
        var N;
        return (N = Oe) == null ? void 0 : N.localStorage;
      })();
    } catch (N) {
      h(N);
    }
  if (!n)
    return p;
  const y = ne(t), w = Gs(y), _ = (s = r.serializer) != null ? s : qs[w], { pause: S, resume: v } = Is(
    p,
    () => A(p.value),
    { flush: o, deep: i, eventFilter: f }
  );
  l && a && $n(() => {
    n instanceof Storage ? Ut(l, "storage", F) : Ut(l, Wt, X), m && F();
  }), m || F();
  function R(N, D) {
    if (l) {
      const U = {
        key: e,
        oldValue: N,
        newValue: D,
        storageArea: n
      };
      l.dispatchEvent(n instanceof Storage ? new StorageEvent("storage", U) : new CustomEvent(Wt, {
        detail: U
      }));
    }
  }
  function A(N) {
    try {
      const D = n.getItem(e);
      if (N == null)
        R(D, null), n.removeItem(e);
      else {
        const U = _.write(N);
        D !== U && (n.setItem(e, U), R(D, U));
      }
    } catch (D) {
      h(D);
    }
  }
  function I(N) {
    const D = N ? N.newValue : n.getItem(e);
    if (D == null)
      return c && y != null && n.setItem(e, _.write(y)), y;
    if (!N && d) {
      const U = _.read(D);
      return typeof d == "function" ? d(U, y) : w === "object" && !Array.isArray(U) ? { ...y, ...U } : U;
    } else return typeof D != "string" ? D : _.read(D);
  }
  function F(N) {
    if (!(N && N.storageArea !== n)) {
      if (N && N.key == null) {
        p.value = y;
        return;
      }
      if (!(N && N.key !== e)) {
        S();
        try {
          (N == null ? void 0 : N.newValue) !== _.write(p.value) && (p.value = I(N));
        } catch (D) {
          h(D);
        } finally {
          N ? ke(v) : v();
        }
      }
    }
  }
  function X(N) {
    F(N.detail);
  }
  return p;
}
const Js = "*,*::before,*::after{-webkit-transition:none!important;-moz-transition:none!important;-o-transition:none!important;-ms-transition:none!important;transition:none!important}";
function Qs(e = {}) {
  const {
    selector: t = "html",
    attribute: n = "class",
    initialValue: r = "auto",
    window: s = Oe,
    storage: o,
    storageKey: i = "vueuse-color-scheme",
    listenToStorageChanges: a = !0,
    storageRef: c,
    emitAuto: d,
    disableTransition: u = !0
  } = e, l = {
    auto: "",
    light: "light",
    dark: "dark",
    ...e.modes || {}
  }, f = Ks({ window: s }), h = L(() => f.value ? "dark" : "light"), m = c || (i == null ? xn(r) : yt(i, r, o, { window: s, listenToStorageChanges: a })), p = L(() => m.value === "auto" ? h.value : m.value), y = In(
    "updateHTMLAttrs",
    (v, R, A) => {
      const I = typeof v == "string" ? s == null ? void 0 : s.document.querySelector(v) : Ct(v);
      if (!I)
        return;
      const F = /* @__PURE__ */ new Set(), X = /* @__PURE__ */ new Set();
      let N = null;
      if (R === "class") {
        const U = A.split(/\s/g);
        Object.values(l).flatMap((te) => (te || "").split(/\s/g)).filter(Boolean).forEach((te) => {
          U.includes(te) ? F.add(te) : X.add(te);
        });
      } else
        N = { key: R, value: A };
      if (F.size === 0 && X.size === 0 && N === null)
        return;
      let D;
      u && (D = s.document.createElement("style"), D.appendChild(document.createTextNode(Js)), s.document.head.appendChild(D));
      for (const U of F)
        I.classList.add(U);
      for (const U of X)
        I.classList.remove(U);
      N && I.setAttribute(N.key, N.value), u && (s.getComputedStyle(D).opacity, document.head.removeChild(D));
    }
  );
  function w(v) {
    var R;
    y(t, n, (R = l[v]) != null ? R : v);
  }
  function _(v) {
    e.onChanged ? e.onChanged(v, w) : w(v);
  }
  Q(p, _, { flush: "post", immediate: !0 }), $n(() => _(p.value));
  const S = L({
    get() {
      return d ? m.value : p.value;
    },
    set(v) {
      m.value = v;
    }
  });
  return Object.assign(S, { store: m, system: h, state: p });
}
function Ys(e = {}) {
  const {
    valueDark: t = "dark",
    valueLight: n = ""
  } = e, r = Qs({
    ...e,
    onChanged: (i, a) => {
      var c;
      e.onChanged ? (c = e.onChanged) == null || c.call(e, i === "dark", a, i) : a(i);
    },
    modes: {
      dark: t,
      light: n
    }
  }), s = L(() => r.system.value);
  return L({
    get() {
      return r.value === "dark";
    },
    set(i) {
      const a = i ? "dark" : "light";
      s.value === a ? r.value = "auto" : r.value = a;
    }
  });
}
function Xs(e = null, t = {}) {
  var n, r, s;
  const {
    document: o = js,
    restoreOnUnmount: i = (l) => l
  } = t, a = (n = o == null ? void 0 : o.title) != null ? n : "", c = xn((r = e ?? (o == null ? void 0 : o.title)) != null ? r : null), d = e && typeof e == "function";
  function u(l) {
    if (!("titleTemplate" in t))
      return l;
    const f = t.titleTemplate || "%s";
    return typeof f == "function" ? f(l) : ne(f).replace(/%s/g, l);
  }
  return Q(
    c,
    (l, f) => {
      l !== f && o && (o.title = u(typeof l == "string" ? l : ""));
    },
    { immediate: !0 }
  ), t.observe && !t.titleTemplate && o && !d && Fs(
    (s = o.head) == null ? void 0 : s.querySelector("title"),
    () => {
      o && o.title !== c.value && (c.value = u(o.title));
    },
    { childList: !0 }
  ), Ds(() => {
    if (i) {
      const l = i(a, c.value || "");
      l != null && o && (o.title = l);
    }
  }), c;
}
function Dn(e) {
  return e.constructor.name === "AsyncFunction";
}
function Mn(e, t, n) {
  const [r] = t;
  switch (r) {
    case "bind":
      return e[H(t, n)];
    case "!":
      return !e;
    case "+":
      return e + H(t, n);
    case "~+":
      return H(t, n) + e;
    case "-":
      return e - H(t, n);
    case "~-":
      return H(t, n) - e;
    case "*":
      return e * H(t, n);
    case "~*":
      return H(t, n) * e;
    case "/":
      return e / H(t, n);
    case "~/":
      return H(t, n) / e;
    case "<":
      return e < H(t, n);
    case "<=":
      return e <= H(t, n);
    case ">":
      return e > H(t, n);
    case ">=":
      return e >= H(t, n);
    case "==":
      return e == H(t, n);
    case "!=":
      return e != H(t, n);
    case "||":
      return e || H(t, n);
    case "&&":
      return e && H(t, n);
    case "len":
      return e.length;
    default:
      throw new Error(`Invalid flag ${r} in array at ${t}`);
  }
}
function H(e, t) {
  const [n, r, s] = e, o = () => s && s[0] ? t(r[0]) : r[0];
  switch (n) {
    case "bind":
    case "+":
    case "~+":
    case "-":
    case "~-":
    case "*":
    case "~*":
    case "/":
    case "~/":
    case "<":
    case "<=":
    case ">":
    case ">=":
    case "==":
    case "!=":
    case "||":
    case "&&":
      return o();
    default:
      throw new Error(`Invalid flag ${n} in array at ${e}`);
  }
}
function Zs(e, t, n) {
  return jn(t).reduce(
    (r, s) => Mn(r, s, n),
    e
  );
}
function Bn(e, t, n, r) {
  jn(t).reduce((s, o, i) => {
    if (i === t.length - 1)
      s[H(o, r)] = n;
    else
      return Mn(s, o, r);
  }, e);
}
function jn(e) {
  return eo(e) ? e.map((t) => ["bind", [t]]) : e;
}
function eo(e) {
  return !Array.isArray(e[0]);
}
function to(e, t, n) {
  const { paths: r, getBindableValueFn: s } = t, { paths: o, getBindableValueFn: i } = t;
  return r === void 0 || r.length === 0 ? e : ye(() => ({
    get() {
      try {
        return Zs(
          Se(e),
          r,
          s
        );
      } catch {
        return;
      }
    },
    set(a) {
      Bn(
        Se(e),
        o || r,
        a,
        i
      );
    }
  }));
}
function zt(e, t) {
  return !Re(e) && JSON.stringify(t) === JSON.stringify(e);
}
function At(e) {
  if (Ot(e)) {
    const t = e;
    return ye(() => ({
      get() {
        return Se(t);
      },
      set(n) {
        const r = Se(t);
        zt(r, n) || (t.value = n);
      }
    }));
  }
  return ye((t, n) => ({
    get() {
      return t(), e;
    },
    set(r) {
      zt(e, r) || (e = r, n());
    }
  }));
}
function Ln(e) {
  return Vr(e) || e instanceof Element;
}
function no(e) {
  const { type: t, key: n, value: r } = e.args;
  return t === "local" ? yt(n, r) : yt(n, r, sessionStorage);
}
const ro = "insta-color-scheme";
function so(e) {
  return Ys({
    storageKey: ro,
    onChanged(n) {
      n ? (document.documentElement.setAttribute("theme-mode", "dark"), document.documentElement.classList.add("insta-dark")) : (document.documentElement.setAttribute("theme-mode", "light"), document.documentElement.classList.remove("insta-dark"));
    }
  });
}
function oo(e) {
  return Xs();
}
const io = z("en_US");
function ao() {
  return io;
}
const co = /* @__PURE__ */ new Map([
  ["storage", no],
  ["useDark", so],
  ["usePageTitle", oo],
  ["useLanguage", ao]
]);
function lo(e) {
  const { type: t } = e;
  if (!t)
    throw new Error("Invalid ref type");
  const n = co.get(t);
  if (!n)
    throw new Error(`Invalid ref type ${t}`);
  return n(e);
}
function uo(e) {
  if (!e) return null;
  switch (e) {
    case "unwrap_reactive":
      return fo;
    default:
      throw new Error(`Invalid js computed tool ${e}`);
  }
}
function fo(e, t, ...n) {
  const r = Nt(e);
  return t.forEach((s, o) => {
    const i = n[o];
    let a = r;
    for (let d = 0; d < s.length - 1; d++) {
      const u = s[d];
      a = a[u];
    }
    const c = s[s.length - 1];
    a[c] = i;
  }), r;
}
function ho(e, t) {
  const { deepCompare: n = !1, type: r } = e;
  if (!r) {
    const { value: s } = e;
    return n ? At(s) : z(s);
  }
  return lo(e);
}
function po(e, t, n) {
  const { bind: r = {}, code: s, const: o = [] } = e, i = Object.values(r).map((u, l) => o[l] === 1 ? u : t.getRef(u));
  if (Dn(new Function(s)))
    return Bs(
      async () => {
        const u = Object.fromEntries(
          Object.keys(r).map((l, f) => [l, i[f]])
        );
        return await Y(s, u)();
      },
      null,
      { lazy: !0 }
    );
  const a = Object.fromEntries(
    Object.keys(r).map((u, l) => [u, i[l]])
  ), c = Y(s, a);
  return L(c);
}
function mo(e) {
  const { init: t, deepEqOnInput: n } = e;
  return n === void 0 ? ae(t ?? Ie) : At(t ?? Ie);
}
function go(e, t, n) {
  const {
    inputs: r = [],
    code: s,
    slient: o,
    data: i,
    asyncInit: a = null,
    deepEqOnInput: c = 0,
    tool: d
  } = e, u = o || Array(r.length).fill(0), l = i || Array(r.length).fill(0), f = r.filter((w, _) => u[_] === 0 && l[_] === 0).map((w) => t.getRef(w));
  function h() {
    return r.map((w, _) => {
      if (l[_] === 1)
        return w;
      const S = t.getValue(w);
      return Ln(S) ? S : Nt(S);
    });
  }
  const m = uo(d) ?? Y(s), p = c === 0 ? ae(Ie) : At(Ie), y = { immediate: !0, deep: !0 };
  return Dn(m) ? (p.value = a, Q(
    f,
    async () => {
      h().some(Re) || (p.value = await m(...h()));
    },
    y
  )) : Q(
    f,
    () => {
      const w = h();
      w.some(Re) || (p.value = m(...w));
    },
    y
  ), Rt(p);
}
function yo(e, t, n) {
  const s = {
    ref: {
      r: n.getBindIndex(M(e, t.id))
    },
    type: Ee.Ref
  };
  return {
    ...t,
    immediate: !0,
    outputs: [s, ...t.outputs || []]
  };
}
function vo(e) {
  const { watchConfigs: t, computedConfigs: n, bindingGetter: r, sid: s } = e;
  return new wo(t, n, r, s);
}
class wo {
  constructor(t, n, r, s) {
    T(this, "taskQueue", []);
    T(this, "id2TaskMap", /* @__PURE__ */ new Map());
    T(this, "input2TaskIdMap", Pn(() => []));
    this.bindingGetter = r;
    const o = [], i = (a) => {
      var d;
      const c = new _o(a, r);
      return this.id2TaskMap.set(c.id, c), (d = a.inputs) == null || d.forEach((u, l) => {
        var h, m;
        if (((h = a.data) == null ? void 0 : h[l]) === 0 && ((m = a.slient) == null ? void 0 : m[l]) === 0) {
          const p = u.r;
          this.input2TaskIdMap.getOrDefault(p).push(c.id);
        }
      }), c;
    };
    t == null || t.forEach((a) => {
      const c = i(a);
      o.push(c);
    }), n == null || n.forEach((a) => {
      const c = i(
        yo(s, a, r)
      );
      o.push(c);
    }), o.forEach((a) => {
      const {
        deep: c = !0,
        once: d,
        flush: u,
        immediate: l = !0
      } = a.watchConfig, f = {
        immediate: l,
        deep: c,
        once: d,
        flush: u
      }, h = this._getWatchTargets(a);
      Q(
        h,
        (m) => {
          m.some(Re) || (a.modify = !0, this.taskQueue.push(new Eo(a)), this._scheduleNextTick());
        },
        f
      );
    });
  }
  _getWatchTargets(t) {
    if (!t.watchConfig.inputs)
      return [];
    const n = t.slientInputs, r = t.constDataInputs;
    return t.watchConfig.inputs.filter(
      (o, i) => !r[i] && !n[i]
    ).map((o) => this.bindingGetter.getRef(o));
  }
  _scheduleNextTick() {
    ke(() => this._runAllTasks());
  }
  _runAllTasks() {
    const t = this.taskQueue.slice();
    this.taskQueue.length = 0, this._setTaskNodeRelations(t), t.forEach((n) => {
      n.run();
    });
  }
  _setTaskNodeRelations(t) {
    t.forEach((n) => {
      const r = this._findNextNodes(n, t);
      n.appendNextNodes(...r), r.forEach((s) => {
        s.appendPrevNodes(n);
      });
    });
  }
  _findNextNodes(t, n) {
    const r = t.watchTask.watchConfig.outputs;
    if (r && r.length <= 0)
      return [];
    const s = this._getCalculatorTasksByOutput(
      t.watchTask.watchConfig.outputs
    );
    return n.filter(
      (o) => s.has(o.watchTask.id) && o.watchTask.id !== t.watchTask.id
    );
  }
  _getCalculatorTasksByOutput(t) {
    const n = /* @__PURE__ */ new Set();
    return t == null || t.forEach((r) => {
      if (!Nn(r.ref))
        return;
      const s = r.ref.r;
      (this.input2TaskIdMap.get(s) || []).forEach((i) => n.add(i));
    }), n;
  }
}
class _o {
  constructor(t, n) {
    T(this, "modify", !0);
    T(this, "_running", !1);
    T(this, "id");
    T(this, "_runningPromise", null);
    T(this, "_runningPromiseResolve", null);
    T(this, "_inputInfos");
    this.watchConfig = t, this.bindingGetter = n, this.id = Symbol(t.debug), this._inputInfos = this.createInputInfos();
  }
  createInputInfos() {
    const { inputs: t = [] } = this.watchConfig, n = this.watchConfig.data || Array.from({ length: t.length }).fill(0), r = this.watchConfig.slient || Array.from({ length: t.length }).fill(0);
    return {
      const_data: n,
      slients: r
    };
  }
  get slientInputs() {
    return this._inputInfos.slients;
  }
  get constDataInputs() {
    return this._inputInfos.const_data;
  }
  getServerInputs() {
    const { const_data: t } = this._inputInfos;
    return this.watchConfig.inputs ? this.watchConfig.inputs.map((n, r) => t[r] === 0 ? this.bindingGetter.getValue(n) : n) : [];
  }
  get running() {
    return this._running;
  }
  get runningPromise() {
    return this._runningPromise;
  }
  /**
   * setRunning
   */
  setRunning() {
    this._running = !0, this._runningPromise = new Promise((t) => {
      this._runningPromiseResolve = t;
    });
  }
  /**
   * taskDone
   */
  taskDone() {
    this._running = !1, this._runningPromiseResolve && (this._runningPromiseResolve(), this._runningPromiseResolve = null);
  }
}
class Eo {
  /**
   *
   */
  constructor(t) {
    T(this, "prevNodes", []);
    T(this, "nextNodes", []);
    T(this, "_runningPrev", !1);
    this.watchTask = t;
  }
  /**
   * appendPrevNodes
   */
  appendPrevNodes(...t) {
    this.prevNodes.push(...t);
  }
  /**
   *
   */
  appendNextNodes(...t) {
    this.nextNodes.push(...t);
  }
  /**
   * hasNextNodes
   */
  hasNextNodes() {
    return this.nextNodes.length > 0;
  }
  /**
   * run
   */
  async run() {
    if (this.prevNodes.length > 0 && !this._runningPrev)
      try {
        this._runningPrev = !0, await Promise.all(this.prevNodes.map((t) => t.run()));
      } finally {
        this._runningPrev = !1;
      }
    if (this.watchTask.running) {
      await this.watchTask.runningPromise;
      return;
    }
    if (this.watchTask.modify) {
      this.watchTask.modify = !1, this.watchTask.setRunning();
      try {
        await bo(this.watchTask);
      } finally {
        this.watchTask.taskDone();
      }
    }
  }
}
async function bo(e) {
  const { bindingGetter: t } = e, { outputs: n, preSetup: r } = e.watchConfig, s = kn({
    config: r,
    bindingGetter: t
  });
  try {
    s.run(), e.taskDone();
    const o = await Sn().watchSend(e);
    if (!o)
      return;
    Je(o, n, t);
  } finally {
    s.tryReset();
  }
}
function So(e, t) {
  const {
    on: n,
    code: r,
    immediate: s,
    deep: o,
    once: i,
    flush: a,
    bind: c = {},
    onData: d,
    bindData: u
  } = e, l = d || Array.from({ length: n.length }).fill(0), f = u || Array.from({ length: Object.keys(c).length }).fill(0), h = qe(
    c,
    (y, w, _) => f[_] === 0 ? t.getRef(y) : y
  ), m = Y(r, h), p = n.length === 1 ? Ht(l[0] === 1, n[0], t) : n.map(
    (y, w) => Ht(l[w] === 1, y, t)
  );
  return Q(p, m, { immediate: s, deep: o, once: i, flush: a });
}
function Ht(e, t, n) {
  return e ? () => t : n.getRef(t);
}
function ko(e, t) {
  const {
    inputs: n = [],
    outputs: r,
    slient: s,
    data: o,
    code: i,
    immediate: a = !0,
    deep: c,
    once: d,
    flush: u
  } = e, l = s || Array.from({ length: n.length }).fill(0), f = o || Array.from({ length: n.length }).fill(0), h = Y(i), m = n.filter((y, w) => l[w] === 0 && f[w] === 0).map((y) => t.getRef(y));
  function p() {
    return n.map((y, w) => {
      if (f[w] === 0) {
        const _ = t.getValue(y);
        return Ln(_) ? _ : Nt(_);
      }
      return y;
    });
  }
  Q(
    m,
    async () => {
      let y = await h(...p());
      if (!r)
        return;
      const _ = r.length === 1 ? [y] : y, S = _.map((v) => v === void 0 ? 1 : 0);
      Je(
        {
          values: _,
          types: S
        },
        r,
        t
      );
    },
    { immediate: a, deep: c, once: d, flush: u }
  );
}
function Ro() {
  return Fn().__VUE_DEVTOOLS_GLOBAL_HOOK__;
}
function Fn() {
  return typeof navigator < "u" && typeof window < "u" ? window : typeof globalThis < "u" ? globalThis : {};
}
const Oo = typeof Proxy == "function", Po = "devtools-plugin:setup", No = "plugin:settings:set";
let _e, vt;
function Vo() {
  var e;
  return _e !== void 0 || (typeof window < "u" && window.performance ? (_e = !0, vt = window.performance) : typeof globalThis < "u" && (!((e = globalThis.perf_hooks) === null || e === void 0) && e.performance) ? (_e = !0, vt = globalThis.perf_hooks.performance) : _e = !1), _e;
}
function Co() {
  return Vo() ? vt.now() : Date.now();
}
class Ao {
  constructor(t, n) {
    this.target = null, this.targetQueue = [], this.onQueue = [], this.plugin = t, this.hook = n;
    const r = {};
    if (t.settings)
      for (const i in t.settings) {
        const a = t.settings[i];
        r[i] = a.defaultValue;
      }
    const s = `__vue-devtools-plugin-settings__${t.id}`;
    let o = Object.assign({}, r);
    try {
      const i = localStorage.getItem(s), a = JSON.parse(i);
      Object.assign(o, a);
    } catch {
    }
    this.fallbacks = {
      getSettings() {
        return o;
      },
      setSettings(i) {
        try {
          localStorage.setItem(s, JSON.stringify(i));
        } catch {
        }
        o = i;
      },
      now() {
        return Co();
      }
    }, n && n.on(No, (i, a) => {
      i === this.plugin.id && this.fallbacks.setSettings(a);
    }), this.proxiedOn = new Proxy({}, {
      get: (i, a) => this.target ? this.target.on[a] : (...c) => {
        this.onQueue.push({
          method: a,
          args: c
        });
      }
    }), this.proxiedTarget = new Proxy({}, {
      get: (i, a) => this.target ? this.target[a] : a === "on" ? this.proxiedOn : Object.keys(this.fallbacks).includes(a) ? (...c) => (this.targetQueue.push({
        method: a,
        args: c,
        resolve: () => {
        }
      }), this.fallbacks[a](...c)) : (...c) => new Promise((d) => {
        this.targetQueue.push({
          method: a,
          args: c,
          resolve: d
        });
      })
    });
  }
  async setRealTarget(t) {
    this.target = t;
    for (const n of this.onQueue)
      this.target.on[n.method](...n.args);
    for (const n of this.targetQueue)
      n.resolve(await this.target[n.method](...n.args));
  }
}
function xo(e, t) {
  const n = e, r = Fn(), s = Ro(), o = Oo && n.enableEarlyProxy;
  if (s && (r.__VUE_DEVTOOLS_PLUGIN_API_AVAILABLE__ || !o))
    s.emit(Po, e, t);
  else {
    const i = o ? new Ao(n, s) : null;
    (r.__VUE_DEVTOOLS_PLUGINS__ = r.__VUE_DEVTOOLS_PLUGINS__ || []).push({
      pluginDescriptor: n,
      setupFn: t,
      proxy: i
    }), i && t(i.proxiedTarget);
  }
}
var O = {};
const ie = typeof document < "u";
function Un(e) {
  return typeof e == "object" || "displayName" in e || "props" in e || "__vccOpts" in e;
}
function $o(e) {
  return e.__esModule || e[Symbol.toStringTag] === "Module" || // support CF with dynamic imports that do not
  // add the Module string tag
  e.default && Un(e.default);
}
const x = Object.assign;
function at(e, t) {
  const n = {};
  for (const r in t) {
    const s = t[r];
    n[r] = Z(s) ? s.map(e) : e(s);
  }
  return n;
}
const xe = () => {
}, Z = Array.isArray;
function P(e) {
  const t = Array.from(arguments).slice(1);
  console.warn.apply(console, ["[Vue Router warn]: " + e].concat(t));
}
const Wn = /#/g, To = /&/g, Io = /\//g, Do = /=/g, Mo = /\?/g, zn = /\+/g, Bo = /%5B/g, jo = /%5D/g, Hn = /%5E/g, Lo = /%60/g, Kn = /%7B/g, Fo = /%7C/g, Gn = /%7D/g, Uo = /%20/g;
function xt(e) {
  return encodeURI("" + e).replace(Fo, "|").replace(Bo, "[").replace(jo, "]");
}
function Wo(e) {
  return xt(e).replace(Kn, "{").replace(Gn, "}").replace(Hn, "^");
}
function wt(e) {
  return xt(e).replace(zn, "%2B").replace(Uo, "+").replace(Wn, "%23").replace(To, "%26").replace(Lo, "`").replace(Kn, "{").replace(Gn, "}").replace(Hn, "^");
}
function zo(e) {
  return wt(e).replace(Do, "%3D");
}
function Ho(e) {
  return xt(e).replace(Wn, "%23").replace(Mo, "%3F");
}
function Ko(e) {
  return e == null ? "" : Ho(e).replace(Io, "%2F");
}
function Pe(e) {
  try {
    return decodeURIComponent("" + e);
  } catch {
    O.NODE_ENV !== "production" && P(`Error decoding "${e}". Using original value`);
  }
  return "" + e;
}
const Go = /\/$/, qo = (e) => e.replace(Go, "");
function ct(e, t, n = "/") {
  let r, s = {}, o = "", i = "";
  const a = t.indexOf("#");
  let c = t.indexOf("?");
  return a < c && a >= 0 && (c = -1), c > -1 && (r = t.slice(0, c), o = t.slice(c + 1, a > -1 ? a : t.length), s = e(o)), a > -1 && (r = r || t.slice(0, a), i = t.slice(a, t.length)), r = Yo(r ?? t, n), {
    fullPath: r + (o && "?") + o + i,
    path: r,
    query: s,
    hash: Pe(i)
  };
}
function Jo(e, t) {
  const n = t.query ? e(t.query) : "";
  return t.path + (n && "?") + n + (t.hash || "");
}
function Kt(e, t) {
  return !t || !e.toLowerCase().startsWith(t.toLowerCase()) ? e : e.slice(t.length) || "/";
}
function Gt(e, t, n) {
  const r = t.matched.length - 1, s = n.matched.length - 1;
  return r > -1 && r === s && he(t.matched[r], n.matched[s]) && qn(t.params, n.params) && e(t.query) === e(n.query) && t.hash === n.hash;
}
function he(e, t) {
  return (e.aliasOf || e) === (t.aliasOf || t);
}
function qn(e, t) {
  if (Object.keys(e).length !== Object.keys(t).length)
    return !1;
  for (const n in e)
    if (!Qo(e[n], t[n]))
      return !1;
  return !0;
}
function Qo(e, t) {
  return Z(e) ? qt(e, t) : Z(t) ? qt(t, e) : e === t;
}
function qt(e, t) {
  return Z(t) ? e.length === t.length && e.every((n, r) => n === t[r]) : e.length === 1 && e[0] === t;
}
function Yo(e, t) {
  if (e.startsWith("/"))
    return e;
  if (O.NODE_ENV !== "production" && !t.startsWith("/"))
    return P(`Cannot resolve a relative location without an absolute path. Trying to resolve "${e}" from "${t}". It should look like "/${t}".`), e;
  if (!e)
    return t;
  const n = t.split("/"), r = e.split("/"), s = r[r.length - 1];
  (s === ".." || s === ".") && r.push("");
  let o = n.length - 1, i, a;
  for (i = 0; i < r.length; i++)
    if (a = r[i], a !== ".")
      if (a === "..")
        o > 1 && o--;
      else
        break;
  return n.slice(0, o).join("/") + "/" + r.slice(i).join("/");
}
const le = {
  path: "/",
  // TODO: could we use a symbol in the future?
  name: void 0,
  params: {},
  query: {},
  hash: "",
  fullPath: "/",
  matched: [],
  meta: {},
  redirectedFrom: void 0
};
var Ne;
(function(e) {
  e.pop = "pop", e.push = "push";
})(Ne || (Ne = {}));
var ge;
(function(e) {
  e.back = "back", e.forward = "forward", e.unknown = "";
})(ge || (ge = {}));
const lt = "";
function Jn(e) {
  if (!e)
    if (ie) {
      const t = document.querySelector("base");
      e = t && t.getAttribute("href") || "/", e = e.replace(/^\w+:\/\/[^\/]+/, "");
    } else
      e = "/";
  return e[0] !== "/" && e[0] !== "#" && (e = "/" + e), qo(e);
}
const Xo = /^[^#]+#/;
function Qn(e, t) {
  return e.replace(Xo, "#") + t;
}
function Zo(e, t) {
  const n = document.documentElement.getBoundingClientRect(), r = e.getBoundingClientRect();
  return {
    behavior: t.behavior,
    left: r.left - n.left - (t.left || 0),
    top: r.top - n.top - (t.top || 0)
  };
}
const Qe = () => ({
  left: window.scrollX,
  top: window.scrollY
});
function ei(e) {
  let t;
  if ("el" in e) {
    const n = e.el, r = typeof n == "string" && n.startsWith("#");
    if (O.NODE_ENV !== "production" && typeof e.el == "string" && (!r || !document.getElementById(e.el.slice(1))))
      try {
        const o = document.querySelector(e.el);
        if (r && o) {
          P(`The selector "${e.el}" should be passed as "el: document.querySelector('${e.el}')" because it starts with "#".`);
          return;
        }
      } catch {
        P(`The selector "${e.el}" is invalid. If you are using an id selector, make sure to escape it. You can find more information about escaping characters in selectors at https://mathiasbynens.be/notes/css-escapes or use CSS.escape (https://developer.mozilla.org/en-US/docs/Web/API/CSS/escape).`);
        return;
      }
    const s = typeof n == "string" ? r ? document.getElementById(n.slice(1)) : document.querySelector(n) : n;
    if (!s) {
      O.NODE_ENV !== "production" && P(`Couldn't find element using selector "${e.el}" returned by scrollBehavior.`);
      return;
    }
    t = Zo(s, e);
  } else
    t = e;
  "scrollBehavior" in document.documentElement.style ? window.scrollTo(t) : window.scrollTo(t.left != null ? t.left : window.scrollX, t.top != null ? t.top : window.scrollY);
}
function Jt(e, t) {
  return (history.state ? history.state.position - t : -1) + e;
}
const _t = /* @__PURE__ */ new Map();
function ti(e, t) {
  _t.set(e, t);
}
function ni(e) {
  const t = _t.get(e);
  return _t.delete(e), t;
}
let ri = () => location.protocol + "//" + location.host;
function Yn(e, t) {
  const { pathname: n, search: r, hash: s } = t, o = e.indexOf("#");
  if (o > -1) {
    let a = s.includes(e.slice(o)) ? e.slice(o).length : 1, c = s.slice(a);
    return c[0] !== "/" && (c = "/" + c), Kt(c, "");
  }
  return Kt(n, e) + r + s;
}
function si(e, t, n, r) {
  let s = [], o = [], i = null;
  const a = ({ state: f }) => {
    const h = Yn(e, location), m = n.value, p = t.value;
    let y = 0;
    if (f) {
      if (n.value = h, t.value = f, i && i === m) {
        i = null;
        return;
      }
      y = p ? f.position - p.position : 0;
    } else
      r(h);
    s.forEach((w) => {
      w(n.value, m, {
        delta: y,
        type: Ne.pop,
        direction: y ? y > 0 ? ge.forward : ge.back : ge.unknown
      });
    });
  };
  function c() {
    i = n.value;
  }
  function d(f) {
    s.push(f);
    const h = () => {
      const m = s.indexOf(f);
      m > -1 && s.splice(m, 1);
    };
    return o.push(h), h;
  }
  function u() {
    const { history: f } = window;
    f.state && f.replaceState(x({}, f.state, { scroll: Qe() }), "");
  }
  function l() {
    for (const f of o)
      f();
    o = [], window.removeEventListener("popstate", a), window.removeEventListener("beforeunload", u);
  }
  return window.addEventListener("popstate", a), window.addEventListener("beforeunload", u, {
    passive: !0
  }), {
    pauseListeners: c,
    listen: d,
    destroy: l
  };
}
function Qt(e, t, n, r = !1, s = !1) {
  return {
    back: e,
    current: t,
    forward: n,
    replaced: r,
    position: window.history.length,
    scroll: s ? Qe() : null
  };
}
function oi(e) {
  const { history: t, location: n } = window, r = {
    value: Yn(e, n)
  }, s = { value: t.state };
  s.value || o(r.value, {
    back: null,
    current: r.value,
    forward: null,
    // the length is off by one, we need to decrease it
    position: t.length - 1,
    replaced: !0,
    // don't add a scroll as the user may have an anchor, and we want
    // scrollBehavior to be triggered without a saved position
    scroll: null
  }, !0);
  function o(c, d, u) {
    const l = e.indexOf("#"), f = l > -1 ? (n.host && document.querySelector("base") ? e : e.slice(l)) + c : ri() + e + c;
    try {
      t[u ? "replaceState" : "pushState"](d, "", f), s.value = d;
    } catch (h) {
      O.NODE_ENV !== "production" ? P("Error with push/replace State", h) : console.error(h), n[u ? "replace" : "assign"](f);
    }
  }
  function i(c, d) {
    const u = x({}, t.state, Qt(
      s.value.back,
      // keep back and forward entries but override current position
      c,
      s.value.forward,
      !0
    ), d, { position: s.value.position });
    o(c, u, !0), r.value = c;
  }
  function a(c, d) {
    const u = x(
      {},
      // use current history state to gracefully handle a wrong call to
      // history.replaceState
      // https://github.com/vuejs/router/issues/366
      s.value,
      t.state,
      {
        forward: c,
        scroll: Qe()
      }
    );
    O.NODE_ENV !== "production" && !t.state && P(`history.state seems to have been manually replaced without preserving the necessary values. Make sure to preserve existing history state if you are manually calling history.replaceState:

history.replaceState(history.state, '', url)

You can find more information at https://router.vuejs.org/guide/migration/#Usage-of-history-state`), o(u.current, u, !0);
    const l = x({}, Qt(r.value, c, null), { position: u.position + 1 }, d);
    o(c, l, !1), r.value = c;
  }
  return {
    location: r,
    state: s,
    push: a,
    replace: i
  };
}
function Xn(e) {
  e = Jn(e);
  const t = oi(e), n = si(e, t.state, t.location, t.replace);
  function r(o, i = !0) {
    i || n.pauseListeners(), history.go(o);
  }
  const s = x({
    // it's overridden right after
    location: "",
    base: e,
    go: r,
    createHref: Qn.bind(null, e)
  }, t, n);
  return Object.defineProperty(s, "location", {
    enumerable: !0,
    get: () => t.location.value
  }), Object.defineProperty(s, "state", {
    enumerable: !0,
    get: () => t.state.value
  }), s;
}
function ii(e = "") {
  let t = [], n = [lt], r = 0;
  e = Jn(e);
  function s(a) {
    r++, r !== n.length && n.splice(r), n.push(a);
  }
  function o(a, c, { direction: d, delta: u }) {
    const l = {
      direction: d,
      delta: u,
      type: Ne.pop
    };
    for (const f of t)
      f(a, c, l);
  }
  const i = {
    // rewritten by Object.defineProperty
    location: lt,
    // TODO: should be kept in queue
    state: {},
    base: e,
    createHref: Qn.bind(null, e),
    replace(a) {
      n.splice(r--, 1), s(a);
    },
    push(a, c) {
      s(a);
    },
    listen(a) {
      return t.push(a), () => {
        const c = t.indexOf(a);
        c > -1 && t.splice(c, 1);
      };
    },
    destroy() {
      t = [], n = [lt], r = 0;
    },
    go(a, c = !0) {
      const d = this.location, u = (
        // we are considering delta === 0 going forward, but in abstract mode
        // using 0 for the delta doesn't make sense like it does in html5 where
        // it reloads the page
        a < 0 ? ge.back : ge.forward
      );
      r = Math.max(0, Math.min(r + a, n.length - 1)), c && o(this.location, d, {
        direction: u,
        delta: a
      });
    }
  };
  return Object.defineProperty(i, "location", {
    enumerable: !0,
    get: () => n[r]
  }), i;
}
function ai(e) {
  return e = location.host ? e || location.pathname + location.search : "", e.includes("#") || (e += "#"), O.NODE_ENV !== "production" && !e.endsWith("#/") && !e.endsWith("#") && P(`A hash base must end with a "#":
"${e}" should be "${e.replace(/#.*$/, "#")}".`), Xn(e);
}
function Ke(e) {
  return typeof e == "string" || e && typeof e == "object";
}
function Zn(e) {
  return typeof e == "string" || typeof e == "symbol";
}
const Et = Symbol(O.NODE_ENV !== "production" ? "navigation failure" : "");
var Yt;
(function(e) {
  e[e.aborted = 4] = "aborted", e[e.cancelled = 8] = "cancelled", e[e.duplicated = 16] = "duplicated";
})(Yt || (Yt = {}));
const ci = {
  1({ location: e, currentLocation: t }) {
    return `No match for
 ${JSON.stringify(e)}${t ? `
while being at
` + JSON.stringify(t) : ""}`;
  },
  2({ from: e, to: t }) {
    return `Redirected from "${e.fullPath}" to "${ui(t)}" via a navigation guard.`;
  },
  4({ from: e, to: t }) {
    return `Navigation aborted from "${e.fullPath}" to "${t.fullPath}" via a navigation guard.`;
  },
  8({ from: e, to: t }) {
    return `Navigation cancelled from "${e.fullPath}" to "${t.fullPath}" with a new navigation.`;
  },
  16({ from: e, to: t }) {
    return `Avoided redundant navigation to current location: "${e.fullPath}".`;
  }
};
function Ve(e, t) {
  return O.NODE_ENV !== "production" ? x(new Error(ci[e](t)), {
    type: e,
    [Et]: !0
  }, t) : x(new Error(), {
    type: e,
    [Et]: !0
  }, t);
}
function oe(e, t) {
  return e instanceof Error && Et in e && (t == null || !!(e.type & t));
}
const li = ["params", "query", "hash"];
function ui(e) {
  if (typeof e == "string")
    return e;
  if (e.path != null)
    return e.path;
  const t = {};
  for (const n of li)
    n in e && (t[n] = e[n]);
  return JSON.stringify(t, null, 2);
}
const Xt = "[^/]+?", fi = {
  sensitive: !1,
  strict: !1,
  start: !0,
  end: !0
}, di = /[.+*?^${}()[\]/\\]/g;
function hi(e, t) {
  const n = x({}, fi, t), r = [];
  let s = n.start ? "^" : "";
  const o = [];
  for (const d of e) {
    const u = d.length ? [] : [
      90
      /* PathScore.Root */
    ];
    n.strict && !d.length && (s += "/");
    for (let l = 0; l < d.length; l++) {
      const f = d[l];
      let h = 40 + (n.sensitive ? 0.25 : 0);
      if (f.type === 0)
        l || (s += "/"), s += f.value.replace(di, "\\$&"), h += 40;
      else if (f.type === 1) {
        const { value: m, repeatable: p, optional: y, regexp: w } = f;
        o.push({
          name: m,
          repeatable: p,
          optional: y
        });
        const _ = w || Xt;
        if (_ !== Xt) {
          h += 10;
          try {
            new RegExp(`(${_})`);
          } catch (v) {
            throw new Error(`Invalid custom RegExp for param "${m}" (${_}): ` + v.message);
          }
        }
        let S = p ? `((?:${_})(?:/(?:${_}))*)` : `(${_})`;
        l || (S = // avoid an optional / if there are more segments e.g. /:p?-static
        // or /:p?-:p2
        y && d.length < 2 ? `(?:/${S})` : "/" + S), y && (S += "?"), s += S, h += 20, y && (h += -8), p && (h += -20), _ === ".*" && (h += -50);
      }
      u.push(h);
    }
    r.push(u);
  }
  if (n.strict && n.end) {
    const d = r.length - 1;
    r[d][r[d].length - 1] += 0.7000000000000001;
  }
  n.strict || (s += "/?"), n.end ? s += "$" : n.strict && !s.endsWith("/") && (s += "(?:/|$)");
  const i = new RegExp(s, n.sensitive ? "" : "i");
  function a(d) {
    const u = d.match(i), l = {};
    if (!u)
      return null;
    for (let f = 1; f < u.length; f++) {
      const h = u[f] || "", m = o[f - 1];
      l[m.name] = h && m.repeatable ? h.split("/") : h;
    }
    return l;
  }
  function c(d) {
    let u = "", l = !1;
    for (const f of e) {
      (!l || !u.endsWith("/")) && (u += "/"), l = !1;
      for (const h of f)
        if (h.type === 0)
          u += h.value;
        else if (h.type === 1) {
          const { value: m, repeatable: p, optional: y } = h, w = m in d ? d[m] : "";
          if (Z(w) && !p)
            throw new Error(`Provided param "${m}" is an array but it is not repeatable (* or + modifiers)`);
          const _ = Z(w) ? w.join("/") : w;
          if (!_)
            if (y)
              f.length < 2 && (u.endsWith("/") ? u = u.slice(0, -1) : l = !0);
            else
              throw new Error(`Missing required param "${m}"`);
          u += _;
        }
    }
    return u || "/";
  }
  return {
    re: i,
    score: r,
    keys: o,
    parse: a,
    stringify: c
  };
}
function pi(e, t) {
  let n = 0;
  for (; n < e.length && n < t.length; ) {
    const r = t[n] - e[n];
    if (r)
      return r;
    n++;
  }
  return e.length < t.length ? e.length === 1 && e[0] === 80 ? -1 : 1 : e.length > t.length ? t.length === 1 && t[0] === 80 ? 1 : -1 : 0;
}
function er(e, t) {
  let n = 0;
  const r = e.score, s = t.score;
  for (; n < r.length && n < s.length; ) {
    const o = pi(r[n], s[n]);
    if (o)
      return o;
    n++;
  }
  if (Math.abs(s.length - r.length) === 1) {
    if (Zt(r))
      return 1;
    if (Zt(s))
      return -1;
  }
  return s.length - r.length;
}
function Zt(e) {
  const t = e[e.length - 1];
  return e.length > 0 && t[t.length - 1] < 0;
}
const mi = {
  type: 0,
  value: ""
}, gi = /[a-zA-Z0-9_]/;
function yi(e) {
  if (!e)
    return [[]];
  if (e === "/")
    return [[mi]];
  if (!e.startsWith("/"))
    throw new Error(O.NODE_ENV !== "production" ? `Route paths should start with a "/": "${e}" should be "/${e}".` : `Invalid path "${e}"`);
  function t(h) {
    throw new Error(`ERR (${n})/"${d}": ${h}`);
  }
  let n = 0, r = n;
  const s = [];
  let o;
  function i() {
    o && s.push(o), o = [];
  }
  let a = 0, c, d = "", u = "";
  function l() {
    d && (n === 0 ? o.push({
      type: 0,
      value: d
    }) : n === 1 || n === 2 || n === 3 ? (o.length > 1 && (c === "*" || c === "+") && t(`A repeatable param (${d}) must be alone in its segment. eg: '/:ids+.`), o.push({
      type: 1,
      value: d,
      regexp: u,
      repeatable: c === "*" || c === "+",
      optional: c === "*" || c === "?"
    })) : t("Invalid state to consume buffer"), d = "");
  }
  function f() {
    d += c;
  }
  for (; a < e.length; ) {
    if (c = e[a++], c === "\\" && n !== 2) {
      r = n, n = 4;
      continue;
    }
    switch (n) {
      case 0:
        c === "/" ? (d && l(), i()) : c === ":" ? (l(), n = 1) : f();
        break;
      case 4:
        f(), n = r;
        break;
      case 1:
        c === "(" ? n = 2 : gi.test(c) ? f() : (l(), n = 0, c !== "*" && c !== "?" && c !== "+" && a--);
        break;
      case 2:
        c === ")" ? u[u.length - 1] == "\\" ? u = u.slice(0, -1) + c : n = 3 : u += c;
        break;
      case 3:
        l(), n = 0, c !== "*" && c !== "?" && c !== "+" && a--, u = "";
        break;
      default:
        t("Unknown state");
        break;
    }
  }
  return n === 2 && t(`Unfinished custom RegExp for param "${d}"`), l(), i(), s;
}
function vi(e, t, n) {
  const r = hi(yi(e.path), n);
  if (O.NODE_ENV !== "production") {
    const o = /* @__PURE__ */ new Set();
    for (const i of r.keys)
      o.has(i.name) && P(`Found duplicated params with name "${i.name}" for path "${e.path}". Only the last one will be available on "$route.params".`), o.add(i.name);
  }
  const s = x(r, {
    record: e,
    parent: t,
    // these needs to be populated by the parent
    children: [],
    alias: []
  });
  return t && !s.record.aliasOf == !t.record.aliasOf && t.children.push(s), s;
}
function wi(e, t) {
  const n = [], r = /* @__PURE__ */ new Map();
  t = rn({ strict: !1, end: !0, sensitive: !1 }, t);
  function s(l) {
    return r.get(l);
  }
  function o(l, f, h) {
    const m = !h, p = tn(l);
    O.NODE_ENV !== "production" && Si(p, f), p.aliasOf = h && h.record;
    const y = rn(t, l), w = [p];
    if ("alias" in l) {
      const v = typeof l.alias == "string" ? [l.alias] : l.alias;
      for (const R of v)
        w.push(
          // we need to normalize again to ensure the `mods` property
          // being non enumerable
          tn(x({}, p, {
            // this allows us to hold a copy of the `components` option
            // so that async components cache is hold on the original record
            components: h ? h.record.components : p.components,
            path: R,
            // we might be the child of an alias
            aliasOf: h ? h.record : p
            // the aliases are always of the same kind as the original since they
            // are defined on the same record
          }))
        );
    }
    let _, S;
    for (const v of w) {
      const { path: R } = v;
      if (f && R[0] !== "/") {
        const A = f.record.path, I = A[A.length - 1] === "/" ? "" : "/";
        v.path = f.record.path + (R && I + R);
      }
      if (O.NODE_ENV !== "production" && v.path === "*")
        throw new Error(`Catch all routes ("*") must now be defined using a param with a custom regexp.
See more at https://router.vuejs.org/guide/migration/#Removed-star-or-catch-all-routes.`);
      if (_ = vi(v, f, y), O.NODE_ENV !== "production" && f && R[0] === "/" && Ri(_, f), h ? (h.alias.push(_), O.NODE_ENV !== "production" && bi(h, _)) : (S = S || _, S !== _ && S.alias.push(_), m && l.name && !nn(_) && (O.NODE_ENV !== "production" && ki(l, f), i(l.name))), tr(_) && c(_), p.children) {
        const A = p.children;
        for (let I = 0; I < A.length; I++)
          o(A[I], _, h && h.children[I]);
      }
      h = h || _;
    }
    return S ? () => {
      i(S);
    } : xe;
  }
  function i(l) {
    if (Zn(l)) {
      const f = r.get(l);
      f && (r.delete(l), n.splice(n.indexOf(f), 1), f.children.forEach(i), f.alias.forEach(i));
    } else {
      const f = n.indexOf(l);
      f > -1 && (n.splice(f, 1), l.record.name && r.delete(l.record.name), l.children.forEach(i), l.alias.forEach(i));
    }
  }
  function a() {
    return n;
  }
  function c(l) {
    const f = Oi(l, n);
    n.splice(f, 0, l), l.record.name && !nn(l) && r.set(l.record.name, l);
  }
  function d(l, f) {
    let h, m = {}, p, y;
    if ("name" in l && l.name) {
      if (h = r.get(l.name), !h)
        throw Ve(1, {
          location: l
        });
      if (O.NODE_ENV !== "production") {
        const S = Object.keys(l.params || {}).filter((v) => !h.keys.find((R) => R.name === v));
        S.length && P(`Discarded invalid param(s) "${S.join('", "')}" when navigating. See https://github.com/vuejs/router/blob/main/packages/router/CHANGELOG.md#414-2022-08-22 for more details.`);
      }
      y = h.record.name, m = x(
        // paramsFromLocation is a new object
        en(
          f.params,
          // only keep params that exist in the resolved location
          // only keep optional params coming from a parent record
          h.keys.filter((S) => !S.optional).concat(h.parent ? h.parent.keys.filter((S) => S.optional) : []).map((S) => S.name)
        ),
        // discard any existing params in the current location that do not exist here
        // #1497 this ensures better active/exact matching
        l.params && en(l.params, h.keys.map((S) => S.name))
      ), p = h.stringify(m);
    } else if (l.path != null)
      p = l.path, O.NODE_ENV !== "production" && !p.startsWith("/") && P(`The Matcher cannot resolve relative paths but received "${p}". Unless you directly called \`matcher.resolve("${p}")\`, this is probably a bug in vue-router. Please open an issue at https://github.com/vuejs/router/issues/new/choose.`), h = n.find((S) => S.re.test(p)), h && (m = h.parse(p), y = h.record.name);
    else {
      if (h = f.name ? r.get(f.name) : n.find((S) => S.re.test(f.path)), !h)
        throw Ve(1, {
          location: l,
          currentLocation: f
        });
      y = h.record.name, m = x({}, f.params, l.params), p = h.stringify(m);
    }
    const w = [];
    let _ = h;
    for (; _; )
      w.unshift(_.record), _ = _.parent;
    return {
      name: y,
      path: p,
      params: m,
      matched: w,
      meta: Ei(w)
    };
  }
  e.forEach((l) => o(l));
  function u() {
    n.length = 0, r.clear();
  }
  return {
    addRoute: o,
    resolve: d,
    removeRoute: i,
    clearRoutes: u,
    getRoutes: a,
    getRecordMatcher: s
  };
}
function en(e, t) {
  const n = {};
  for (const r of t)
    r in e && (n[r] = e[r]);
  return n;
}
function tn(e) {
  const t = {
    path: e.path,
    redirect: e.redirect,
    name: e.name,
    meta: e.meta || {},
    aliasOf: e.aliasOf,
    beforeEnter: e.beforeEnter,
    props: _i(e),
    children: e.children || [],
    instances: {},
    leaveGuards: /* @__PURE__ */ new Set(),
    updateGuards: /* @__PURE__ */ new Set(),
    enterCallbacks: {},
    // must be declared afterwards
    // mods: {},
    components: "components" in e ? e.components || null : e.component && { default: e.component }
  };
  return Object.defineProperty(t, "mods", {
    value: {}
  }), t;
}
function _i(e) {
  const t = {}, n = e.props || !1;
  if ("component" in e)
    t.default = n;
  else
    for (const r in e.components)
      t[r] = typeof n == "object" ? n[r] : n;
  return t;
}
function nn(e) {
  for (; e; ) {
    if (e.record.aliasOf)
      return !0;
    e = e.parent;
  }
  return !1;
}
function Ei(e) {
  return e.reduce((t, n) => x(t, n.meta), {});
}
function rn(e, t) {
  const n = {};
  for (const r in e)
    n[r] = r in t ? t[r] : e[r];
  return n;
}
function bt(e, t) {
  return e.name === t.name && e.optional === t.optional && e.repeatable === t.repeatable;
}
function bi(e, t) {
  for (const n of e.keys)
    if (!n.optional && !t.keys.find(bt.bind(null, n)))
      return P(`Alias "${t.record.path}" and the original record: "${e.record.path}" must have the exact same param named "${n.name}"`);
  for (const n of t.keys)
    if (!n.optional && !e.keys.find(bt.bind(null, n)))
      return P(`Alias "${t.record.path}" and the original record: "${e.record.path}" must have the exact same param named "${n.name}"`);
}
function Si(e, t) {
  t && t.record.name && !e.name && !e.path && P(`The route named "${String(t.record.name)}" has a child without a name and an empty path. Using that name won't render the empty path child so you probably want to move the name to the child instead. If this is intentional, add a name to the child route to remove the warning.`);
}
function ki(e, t) {
  for (let n = t; n; n = n.parent)
    if (n.record.name === e.name)
      throw new Error(`A route named "${String(e.name)}" has been added as a ${t === n ? "child" : "descendant"} of a route with the same name. Route names must be unique and a nested route cannot use the same name as an ancestor.`);
}
function Ri(e, t) {
  for (const n of t.keys)
    if (!e.keys.find(bt.bind(null, n)))
      return P(`Absolute path "${e.record.path}" must have the exact same param named "${n.name}" as its parent "${t.record.path}".`);
}
function Oi(e, t) {
  let n = 0, r = t.length;
  for (; n !== r; ) {
    const o = n + r >> 1;
    er(e, t[o]) < 0 ? r = o : n = o + 1;
  }
  const s = Pi(e);
  return s && (r = t.lastIndexOf(s, r - 1), O.NODE_ENV !== "production" && r < 0 && P(`Finding ancestor route "${s.record.path}" failed for "${e.record.path}"`)), r;
}
function Pi(e) {
  let t = e;
  for (; t = t.parent; )
    if (tr(t) && er(e, t) === 0)
      return t;
}
function tr({ record: e }) {
  return !!(e.name || e.components && Object.keys(e.components).length || e.redirect);
}
function Ni(e) {
  const t = {};
  if (e === "" || e === "?")
    return t;
  const r = (e[0] === "?" ? e.slice(1) : e).split("&");
  for (let s = 0; s < r.length; ++s) {
    const o = r[s].replace(zn, " "), i = o.indexOf("="), a = Pe(i < 0 ? o : o.slice(0, i)), c = i < 0 ? null : Pe(o.slice(i + 1));
    if (a in t) {
      let d = t[a];
      Z(d) || (d = t[a] = [d]), d.push(c);
    } else
      t[a] = c;
  }
  return t;
}
function sn(e) {
  let t = "";
  for (let n in e) {
    const r = e[n];
    if (n = zo(n), r == null) {
      r !== void 0 && (t += (t.length ? "&" : "") + n);
      continue;
    }
    (Z(r) ? r.map((o) => o && wt(o)) : [r && wt(r)]).forEach((o) => {
      o !== void 0 && (t += (t.length ? "&" : "") + n, o != null && (t += "=" + o));
    });
  }
  return t;
}
function Vi(e) {
  const t = {};
  for (const n in e) {
    const r = e[n];
    r !== void 0 && (t[n] = Z(r) ? r.map((s) => s == null ? null : "" + s) : r == null ? r : "" + r);
  }
  return t;
}
const Ci = Symbol(O.NODE_ENV !== "production" ? "router view location matched" : ""), on = Symbol(O.NODE_ENV !== "production" ? "router view depth" : ""), Ye = Symbol(O.NODE_ENV !== "production" ? "router" : ""), $t = Symbol(O.NODE_ENV !== "production" ? "route location" : ""), St = Symbol(O.NODE_ENV !== "production" ? "router view location" : "");
function Ce() {
  let e = [];
  function t(r) {
    return e.push(r), () => {
      const s = e.indexOf(r);
      s > -1 && e.splice(s, 1);
    };
  }
  function n() {
    e = [];
  }
  return {
    add: t,
    list: () => e.slice(),
    reset: n
  };
}
function ue(e, t, n, r, s, o = (i) => i()) {
  const i = r && // name is defined if record is because of the function overload
  (r.enterCallbacks[s] = r.enterCallbacks[s] || []);
  return () => new Promise((a, c) => {
    const d = (f) => {
      f === !1 ? c(Ve(4, {
        from: n,
        to: t
      })) : f instanceof Error ? c(f) : Ke(f) ? c(Ve(2, {
        from: t,
        to: f
      })) : (i && // since enterCallbackArray is truthy, both record and name also are
      r.enterCallbacks[s] === i && typeof f == "function" && i.push(f), a());
    }, u = o(() => e.call(r && r.instances[s], t, n, O.NODE_ENV !== "production" ? Ai(d, t, n) : d));
    let l = Promise.resolve(u);
    if (e.length < 3 && (l = l.then(d)), O.NODE_ENV !== "production" && e.length > 2) {
      const f = `The "next" callback was never called inside of ${e.name ? '"' + e.name + '"' : ""}:
${e.toString()}
. If you are returning a value instead of calling "next", make sure to remove the "next" parameter from your function.`;
      if (typeof u == "object" && "then" in u)
        l = l.then((h) => d._called ? h : (P(f), Promise.reject(new Error("Invalid navigation guard"))));
      else if (u !== void 0 && !d._called) {
        P(f), c(new Error("Invalid navigation guard"));
        return;
      }
    }
    l.catch((f) => c(f));
  });
}
function Ai(e, t, n) {
  let r = 0;
  return function() {
    r++ === 1 && P(`The "next" callback was called more than once in one navigation guard when going from "${n.fullPath}" to "${t.fullPath}". It should be called exactly one time in each navigation guard. This will fail in production.`), e._called = !0, r === 1 && e.apply(null, arguments);
  };
}
function ut(e, t, n, r, s = (o) => o()) {
  const o = [];
  for (const i of e) {
    O.NODE_ENV !== "production" && !i.components && !i.children.length && P(`Record with path "${i.path}" is either missing a "component(s)" or "children" property.`);
    for (const a in i.components) {
      let c = i.components[a];
      if (O.NODE_ENV !== "production") {
        if (!c || typeof c != "object" && typeof c != "function")
          throw P(`Component "${a}" in record with path "${i.path}" is not a valid component. Received "${String(c)}".`), new Error("Invalid route component");
        if ("then" in c) {
          P(`Component "${a}" in record with path "${i.path}" is a Promise instead of a function that returns a Promise. Did you write "import('./MyPage.vue')" instead of "() => import('./MyPage.vue')" ? This will break in production if not fixed.`);
          const d = c;
          c = () => d;
        } else c.__asyncLoader && // warn only once per component
        !c.__warnedDefineAsync && (c.__warnedDefineAsync = !0, P(`Component "${a}" in record with path "${i.path}" is defined using "defineAsyncComponent()". Write "() => import('./MyPage.vue')" instead of "defineAsyncComponent(() => import('./MyPage.vue'))".`));
      }
      if (!(t !== "beforeRouteEnter" && !i.instances[a]))
        if (Un(c)) {
          const u = (c.__vccOpts || c)[t];
          u && o.push(ue(u, n, r, i, a, s));
        } else {
          let d = c();
          O.NODE_ENV !== "production" && !("catch" in d) && (P(`Component "${a}" in record with path "${i.path}" is a function that does not return a Promise. If you were passing a functional component, make sure to add a "displayName" to the component. This will break in production if not fixed.`), d = Promise.resolve(d)), o.push(() => d.then((u) => {
            if (!u)
              throw new Error(`Couldn't resolve component "${a}" at "${i.path}"`);
            const l = $o(u) ? u.default : u;
            i.mods[a] = u, i.components[a] = l;
            const h = (l.__vccOpts || l)[t];
            return h && ue(h, n, r, i, a, s)();
          }));
        }
    }
  }
  return o;
}
function an(e) {
  const t = ce(Ye), n = ce($t);
  let r = !1, s = null;
  const o = L(() => {
    const u = q(e.to);
    return O.NODE_ENV !== "production" && (!r || u !== s) && (Ke(u) || (r ? P(`Invalid value for prop "to" in useLink()
- to:`, u, `
- previous to:`, s, `
- props:`, e) : P(`Invalid value for prop "to" in useLink()
- to:`, u, `
- props:`, e)), s = u, r = !0), t.resolve(u);
  }), i = L(() => {
    const { matched: u } = o.value, { length: l } = u, f = u[l - 1], h = n.matched;
    if (!f || !h.length)
      return -1;
    const m = h.findIndex(he.bind(null, f));
    if (m > -1)
      return m;
    const p = cn(u[l - 2]);
    return (
      // we are dealing with nested routes
      l > 1 && // if the parent and matched route have the same path, this link is
      // referring to the empty child. Or we currently are on a different
      // child of the same parent
      cn(f) === p && // avoid comparing the child with its parent
      h[h.length - 1].path !== p ? h.findIndex(he.bind(null, u[l - 2])) : m
    );
  }), a = L(() => i.value > -1 && Di(n.params, o.value.params)), c = L(() => i.value > -1 && i.value === n.matched.length - 1 && qn(n.params, o.value.params));
  function d(u = {}) {
    if (Ii(u)) {
      const l = t[q(e.replace) ? "replace" : "push"](
        q(e.to)
        // avoid uncaught errors are they are logged anyway
      ).catch(xe);
      return e.viewTransition && typeof document < "u" && "startViewTransition" in document && document.startViewTransition(() => l), l;
    }
    return Promise.resolve();
  }
  if (O.NODE_ENV !== "production" && ie) {
    const u = Ge();
    if (u) {
      const l = {
        route: o.value,
        isActive: a.value,
        isExactActive: c.value,
        error: null
      };
      u.__vrl_devtools = u.__vrl_devtools || [], u.__vrl_devtools.push(l), Pt(() => {
        l.route = o.value, l.isActive = a.value, l.isExactActive = c.value, l.error = Ke(q(e.to)) ? null : 'Invalid "to" value';
      }, { flush: "post" });
    }
  }
  return {
    route: o,
    href: L(() => o.value.href),
    isActive: a,
    isExactActive: c,
    navigate: d
  };
}
function xi(e) {
  return e.length === 1 ? e[0] : e;
}
const $i = /* @__PURE__ */ ee({
  name: "RouterLink",
  compatConfig: { MODE: 3 },
  props: {
    to: {
      type: [String, Object],
      required: !0
    },
    replace: Boolean,
    activeClass: String,
    // inactiveClass: String,
    exactActiveClass: String,
    custom: Boolean,
    ariaCurrentValue: {
      type: String,
      default: "page"
    }
  },
  useLink: an,
  setup(e, { slots: t }) {
    const n = Ar(an(e)), { options: r } = ce(Ye), s = L(() => ({
      [ln(e.activeClass, r.linkActiveClass, "router-link-active")]: n.isActive,
      // [getLinkClass(
      //   props.inactiveClass,
      //   options.linkInactiveClass,
      //   'router-link-inactive'
      // )]: !link.isExactActive,
      [ln(e.exactActiveClass, r.linkExactActiveClass, "router-link-exact-active")]: n.isExactActive
    }));
    return () => {
      const o = t.default && xi(t.default(n));
      return e.custom ? o : J("a", {
        "aria-current": n.isExactActive ? e.ariaCurrentValue : null,
        href: n.href,
        // this would override user added attrs but Vue will still add
        // the listener, so we end up triggering both
        onClick: n.navigate,
        class: s.value
      }, o);
    };
  }
}), Ti = $i;
function Ii(e) {
  if (!(e.metaKey || e.altKey || e.ctrlKey || e.shiftKey) && !e.defaultPrevented && !(e.button !== void 0 && e.button !== 0)) {
    if (e.currentTarget && e.currentTarget.getAttribute) {
      const t = e.currentTarget.getAttribute("target");
      if (/\b_blank\b/i.test(t))
        return;
    }
    return e.preventDefault && e.preventDefault(), !0;
  }
}
function Di(e, t) {
  for (const n in t) {
    const r = t[n], s = e[n];
    if (typeof r == "string") {
      if (r !== s)
        return !1;
    } else if (!Z(s) || s.length !== r.length || r.some((o, i) => o !== s[i]))
      return !1;
  }
  return !0;
}
function cn(e) {
  return e ? e.aliasOf ? e.aliasOf.path : e.path : "";
}
const ln = (e, t, n) => e ?? t ?? n, Mi = /* @__PURE__ */ ee({
  name: "RouterView",
  // #674 we manually inherit them
  inheritAttrs: !1,
  props: {
    name: {
      type: String,
      default: "default"
    },
    route: Object
  },
  // Better compat for @vue/compat users
  // https://github.com/vuejs/router/issues/1315
  compatConfig: { MODE: 3 },
  setup(e, { attrs: t, slots: n }) {
    O.NODE_ENV !== "production" && ji();
    const r = ce(St), s = L(() => e.route || r.value), o = ce(on, 0), i = L(() => {
      let d = q(o);
      const { matched: u } = s.value;
      let l;
      for (; (l = u[d]) && !l.components; )
        d++;
      return d;
    }), a = L(() => s.value.matched[i.value]);
    K(on, L(() => i.value + 1)), K(Ci, a), K(St, s);
    const c = z();
    return Q(() => [c.value, a.value, e.name], ([d, u, l], [f, h, m]) => {
      u && (u.instances[l] = d, h && h !== u && d && d === f && (u.leaveGuards.size || (u.leaveGuards = h.leaveGuards), u.updateGuards.size || (u.updateGuards = h.updateGuards))), d && u && // if there is no instance but to and from are the same this might be
      // the first visit
      (!h || !he(u, h) || !f) && (u.enterCallbacks[l] || []).forEach((p) => p(d));
    }, { flush: "post" }), () => {
      const d = s.value, u = e.name, l = a.value, f = l && l.components[u];
      if (!f)
        return un(n.default, { Component: f, route: d });
      const h = l.props[u], m = h ? h === !0 ? d.params : typeof h == "function" ? h(d) : h : null, y = J(f, x({}, m, t, {
        onVnodeUnmounted: (w) => {
          w.component.isUnmounted && (l.instances[u] = null);
        },
        ref: c
      }));
      if (O.NODE_ENV !== "production" && ie && y.ref) {
        const w = {
          depth: i.value,
          name: l.name,
          path: l.path,
          meta: l.meta
        };
        (Z(y.ref) ? y.ref.map((S) => S.i) : [y.ref.i]).forEach((S) => {
          S.__vrv_devtools = w;
        });
      }
      return (
        // pass the vnode to the slot as a prop.
        // h and <component :is="..."> both accept vnodes
        un(n.default, { Component: y, route: d }) || y
      );
    };
  }
});
function un(e, t) {
  if (!e)
    return null;
  const n = e(t);
  return n.length === 1 ? n[0] : n;
}
const Bi = Mi;
function ji() {
  const e = Ge(), t = e.parent && e.parent.type.name, n = e.parent && e.parent.subTree && e.parent.subTree.type;
  if (t && (t === "KeepAlive" || t.includes("Transition")) && typeof n == "object" && n.name === "RouterView") {
    const r = t === "KeepAlive" ? "keep-alive" : "transition";
    P(`<router-view> can no longer be used directly inside <transition> or <keep-alive>.
Use slot props instead:

<router-view v-slot="{ Component }">
  <${r}>
    <component :is="Component" />
  </${r}>
</router-view>`);
  }
}
function Ae(e, t) {
  const n = x({}, e, {
    // remove variables that can contain vue instances
    matched: e.matched.map((r) => Qi(r, ["instances", "children", "aliasOf"]))
  });
  return {
    _custom: {
      type: null,
      readOnly: !0,
      display: e.fullPath,
      tooltip: t,
      value: n
    }
  };
}
function Ue(e) {
  return {
    _custom: {
      display: e
    }
  };
}
let Li = 0;
function Fi(e, t, n) {
  if (t.__hasDevtools)
    return;
  t.__hasDevtools = !0;
  const r = Li++;
  xo({
    id: "org.vuejs.router" + (r ? "." + r : ""),
    label: "Vue Router",
    packageName: "vue-router",
    homepage: "https://router.vuejs.org",
    logo: "https://router.vuejs.org/logo.png",
    componentStateTypes: ["Routing"],
    app: e
  }, (s) => {
    typeof s.now != "function" && console.warn("[Vue Router]: You seem to be using an outdated version of Vue Devtools. Are you still using the Beta release instead of the stable one? You can find the links at https://devtools.vuejs.org/guide/installation.html."), s.on.inspectComponent((u, l) => {
      u.instanceData && u.instanceData.state.push({
        type: "Routing",
        key: "$route",
        editable: !1,
        value: Ae(t.currentRoute.value, "Current Route")
      });
    }), s.on.visitComponentTree(({ treeNode: u, componentInstance: l }) => {
      if (l.__vrv_devtools) {
        const f = l.__vrv_devtools;
        u.tags.push({
          label: (f.name ? `${f.name.toString()}: ` : "") + f.path,
          textColor: 0,
          tooltip: "This component is rendered by &lt;router-view&gt;",
          backgroundColor: nr
        });
      }
      Z(l.__vrl_devtools) && (l.__devtoolsApi = s, l.__vrl_devtools.forEach((f) => {
        let h = f.route.path, m = or, p = "", y = 0;
        f.error ? (h = f.error, m = Ki, y = Gi) : f.isExactActive ? (m = sr, p = "This is exactly active") : f.isActive && (m = rr, p = "This link is active"), u.tags.push({
          label: h,
          textColor: y,
          tooltip: p,
          backgroundColor: m
        });
      }));
    }), Q(t.currentRoute, () => {
      c(), s.notifyComponentUpdate(), s.sendInspectorTree(a), s.sendInspectorState(a);
    });
    const o = "router:navigations:" + r;
    s.addTimelineLayer({
      id: o,
      label: `Router${r ? " " + r : ""} Navigations`,
      color: 4237508
    }), t.onError((u, l) => {
      s.addTimelineEvent({
        layerId: o,
        event: {
          title: "Error during Navigation",
          subtitle: l.fullPath,
          logType: "error",
          time: s.now(),
          data: { error: u },
          groupId: l.meta.__navigationId
        }
      });
    });
    let i = 0;
    t.beforeEach((u, l) => {
      const f = {
        guard: Ue("beforeEach"),
        from: Ae(l, "Current Location during this navigation"),
        to: Ae(u, "Target location")
      };
      Object.defineProperty(u.meta, "__navigationId", {
        value: i++
      }), s.addTimelineEvent({
        layerId: o,
        event: {
          time: s.now(),
          title: "Start of navigation",
          subtitle: u.fullPath,
          data: f,
          groupId: u.meta.__navigationId
        }
      });
    }), t.afterEach((u, l, f) => {
      const h = {
        guard: Ue("afterEach")
      };
      f ? (h.failure = {
        _custom: {
          type: Error,
          readOnly: !0,
          display: f ? f.message : "",
          tooltip: "Navigation Failure",
          value: f
        }
      }, h.status = Ue("❌")) : h.status = Ue("✅"), h.from = Ae(l, "Current Location during this navigation"), h.to = Ae(u, "Target location"), s.addTimelineEvent({
        layerId: o,
        event: {
          title: "End of navigation",
          subtitle: u.fullPath,
          time: s.now(),
          data: h,
          logType: f ? "warning" : "default",
          groupId: u.meta.__navigationId
        }
      });
    });
    const a = "router-inspector:" + r;
    s.addInspector({
      id: a,
      label: "Routes" + (r ? " " + r : ""),
      icon: "book",
      treeFilterPlaceholder: "Search routes"
    });
    function c() {
      if (!d)
        return;
      const u = d;
      let l = n.getRoutes().filter((f) => !f.parent || // these routes have a parent with no component which will not appear in the view
      // therefore we still need to include them
      !f.parent.record.components);
      l.forEach(cr), u.filter && (l = l.filter((f) => (
        // save matches state based on the payload
        kt(f, u.filter.toLowerCase())
      ))), l.forEach((f) => ar(f, t.currentRoute.value)), u.rootNodes = l.map(ir);
    }
    let d;
    s.on.getInspectorTree((u) => {
      d = u, u.app === e && u.inspectorId === a && c();
    }), s.on.getInspectorState((u) => {
      if (u.app === e && u.inspectorId === a) {
        const f = n.getRoutes().find((h) => h.record.__vd_id === u.nodeId);
        f && (u.state = {
          options: Wi(f)
        });
      }
    }), s.sendInspectorTree(a), s.sendInspectorState(a);
  });
}
function Ui(e) {
  return e.optional ? e.repeatable ? "*" : "?" : e.repeatable ? "+" : "";
}
function Wi(e) {
  const { record: t } = e, n = [
    { editable: !1, key: "path", value: t.path }
  ];
  return t.name != null && n.push({
    editable: !1,
    key: "name",
    value: t.name
  }), n.push({ editable: !1, key: "regexp", value: e.re }), e.keys.length && n.push({
    editable: !1,
    key: "keys",
    value: {
      _custom: {
        type: null,
        readOnly: !0,
        display: e.keys.map((r) => `${r.name}${Ui(r)}`).join(" "),
        tooltip: "Param keys",
        value: e.keys
      }
    }
  }), t.redirect != null && n.push({
    editable: !1,
    key: "redirect",
    value: t.redirect
  }), e.alias.length && n.push({
    editable: !1,
    key: "aliases",
    value: e.alias.map((r) => r.record.path)
  }), Object.keys(e.record.meta).length && n.push({
    editable: !1,
    key: "meta",
    value: e.record.meta
  }), n.push({
    key: "score",
    editable: !1,
    value: {
      _custom: {
        type: null,
        readOnly: !0,
        display: e.score.map((r) => r.join(", ")).join(" | "),
        tooltip: "Score used to sort routes",
        value: e.score
      }
    }
  }), n;
}
const nr = 15485081, rr = 2450411, sr = 8702998, zi = 2282478, or = 16486972, Hi = 6710886, Ki = 16704226, Gi = 12131356;
function ir(e) {
  const t = [], { record: n } = e;
  n.name != null && t.push({
    label: String(n.name),
    textColor: 0,
    backgroundColor: zi
  }), n.aliasOf && t.push({
    label: "alias",
    textColor: 0,
    backgroundColor: or
  }), e.__vd_match && t.push({
    label: "matches",
    textColor: 0,
    backgroundColor: nr
  }), e.__vd_exactActive && t.push({
    label: "exact",
    textColor: 0,
    backgroundColor: sr
  }), e.__vd_active && t.push({
    label: "active",
    textColor: 0,
    backgroundColor: rr
  }), n.redirect && t.push({
    label: typeof n.redirect == "string" ? `redirect: ${n.redirect}` : "redirects",
    textColor: 16777215,
    backgroundColor: Hi
  });
  let r = n.__vd_id;
  return r == null && (r = String(qi++), n.__vd_id = r), {
    id: r,
    label: n.path,
    tags: t,
    children: e.children.map(ir)
  };
}
let qi = 0;
const Ji = /^\/(.*)\/([a-z]*)$/;
function ar(e, t) {
  const n = t.matched.length && he(t.matched[t.matched.length - 1], e.record);
  e.__vd_exactActive = e.__vd_active = n, n || (e.__vd_active = t.matched.some((r) => he(r, e.record))), e.children.forEach((r) => ar(r, t));
}
function cr(e) {
  e.__vd_match = !1, e.children.forEach(cr);
}
function kt(e, t) {
  const n = String(e.re).match(Ji);
  if (e.__vd_match = !1, !n || n.length < 3)
    return !1;
  if (new RegExp(n[1].replace(/\$$/, ""), n[2]).test(t))
    return e.children.forEach((i) => kt(i, t)), e.record.path !== "/" || t === "/" ? (e.__vd_match = e.re.test(t), !0) : !1;
  const s = e.record.path.toLowerCase(), o = Pe(s);
  return !t.startsWith("/") && (o.includes(t) || s.includes(t)) || o.startsWith(t) || s.startsWith(t) || e.record.name && String(e.record.name).includes(t) ? !0 : e.children.some((i) => kt(i, t));
}
function Qi(e, t) {
  const n = {};
  for (const r in e)
    t.includes(r) || (n[r] = e[r]);
  return n;
}
function Yi(e) {
  const t = wi(e.routes, e), n = e.parseQuery || Ni, r = e.stringifyQuery || sn, s = e.history;
  if (O.NODE_ENV !== "production" && !s)
    throw new Error('Provide the "history" option when calling "createRouter()": https://router.vuejs.org/api/interfaces/RouterOptions.html#history');
  const o = Ce(), i = Ce(), a = Ce(), c = ae(le);
  let d = le;
  ie && e.scrollBehavior && "scrollRestoration" in history && (history.scrollRestoration = "manual");
  const u = at.bind(null, (g) => "" + g), l = at.bind(null, Ko), f = (
    // @ts-expect-error: intentionally avoid the type check
    at.bind(null, Pe)
  );
  function h(g, b) {
    let E, k;
    return Zn(g) ? (E = t.getRecordMatcher(g), O.NODE_ENV !== "production" && !E && P(`Parent route "${String(g)}" not found when adding child route`, b), k = b) : k = g, t.addRoute(k, E);
  }
  function m(g) {
    const b = t.getRecordMatcher(g);
    b ? t.removeRoute(b) : O.NODE_ENV !== "production" && P(`Cannot remove non-existent route "${String(g)}"`);
  }
  function p() {
    return t.getRoutes().map((g) => g.record);
  }
  function y(g) {
    return !!t.getRecordMatcher(g);
  }
  function w(g, b) {
    if (b = x({}, b || c.value), typeof g == "string") {
      const V = ct(n, g, b.path), j = t.resolve({ path: V.path }, b), pe = s.createHref(V.fullPath);
      return O.NODE_ENV !== "production" && (pe.startsWith("//") ? P(`Location "${g}" resolved to "${pe}". A resolved location cannot start with multiple slashes.`) : j.matched.length || P(`No match found for location with path "${g}"`)), x(V, j, {
        params: f(j.params),
        hash: Pe(V.hash),
        redirectedFrom: void 0,
        href: pe
      });
    }
    if (O.NODE_ENV !== "production" && !Ke(g))
      return P(`router.resolve() was passed an invalid location. This will fail in production.
- Location:`, g), w({});
    let E;
    if (g.path != null)
      O.NODE_ENV !== "production" && "params" in g && !("name" in g) && // @ts-expect-error: the type is never
      Object.keys(g.params).length && P(`Path "${g.path}" was passed with params but they will be ignored. Use a named route alongside params instead.`), E = x({}, g, {
        path: ct(n, g.path, b.path).path
      });
    else {
      const V = x({}, g.params);
      for (const j in V)
        V[j] == null && delete V[j];
      E = x({}, g, {
        params: l(V)
      }), b.params = l(b.params);
    }
    const k = t.resolve(E, b), $ = g.hash || "";
    O.NODE_ENV !== "production" && $ && !$.startsWith("#") && P(`A \`hash\` should always start with the character "#". Replace "${$}" with "#${$}".`), k.params = u(f(k.params));
    const W = Jo(r, x({}, g, {
      hash: Wo($),
      path: k.path
    })), C = s.createHref(W);
    return O.NODE_ENV !== "production" && (C.startsWith("//") ? P(`Location "${g}" resolved to "${C}". A resolved location cannot start with multiple slashes.`) : k.matched.length || P(`No match found for location with path "${g.path != null ? g.path : g}"`)), x({
      fullPath: W,
      // keep the hash encoded so fullPath is effectively path + encodedQuery +
      // hash
      hash: $,
      query: (
        // if the user is using a custom query lib like qs, we might have
        // nested objects, so we keep the query as is, meaning it can contain
        // numbers at `$route.query`, but at the point, the user will have to
        // use their own type anyway.
        // https://github.com/vuejs/router/issues/328#issuecomment-649481567
        r === sn ? Vi(g.query) : g.query || {}
      )
    }, k, {
      redirectedFrom: void 0,
      href: C
    });
  }
  function _(g) {
    return typeof g == "string" ? ct(n, g, c.value.path) : x({}, g);
  }
  function S(g, b) {
    if (d !== g)
      return Ve(8, {
        from: b,
        to: g
      });
  }
  function v(g) {
    return I(g);
  }
  function R(g) {
    return v(x(_(g), { replace: !0 }));
  }
  function A(g) {
    const b = g.matched[g.matched.length - 1];
    if (b && b.redirect) {
      const { redirect: E } = b;
      let k = typeof E == "function" ? E(g) : E;
      if (typeof k == "string" && (k = k.includes("?") || k.includes("#") ? k = _(k) : (
        // force empty params
        { path: k }
      ), k.params = {}), O.NODE_ENV !== "production" && k.path == null && !("name" in k))
        throw P(`Invalid redirect found:
${JSON.stringify(k, null, 2)}
 when navigating to "${g.fullPath}". A redirect must contain a name or path. This will break in production.`), new Error("Invalid redirect");
      return x({
        query: g.query,
        hash: g.hash,
        // avoid transferring params if the redirect has a path
        params: k.path != null ? {} : g.params
      }, k);
    }
  }
  function I(g, b) {
    const E = d = w(g), k = c.value, $ = g.state, W = g.force, C = g.replace === !0, V = A(E);
    if (V)
      return I(
        x(_(V), {
          state: typeof V == "object" ? x({}, $, V.state) : $,
          force: W,
          replace: C
        }),
        // keep original redirectedFrom if it exists
        b || E
      );
    const j = E;
    j.redirectedFrom = b;
    let pe;
    return !W && Gt(r, k, E) && (pe = Ve(16, { to: j, from: k }), It(
      k,
      k,
      // this is a push, the only way for it to be triggered from a
      // history.listen is with a redirect, which makes it become a push
      !0,
      // This cannot be the first navigation because the initial location
      // cannot be manually navigated to
      !1
    )), (pe ? Promise.resolve(pe) : N(j, k)).catch((G) => oe(G) ? (
      // navigation redirects still mark the router as ready
      oe(
        G,
        2
        /* ErrorTypes.NAVIGATION_GUARD_REDIRECT */
      ) ? G : st(G)
    ) : (
      // reject any unknown error
      rt(G, j, k)
    )).then((G) => {
      if (G) {
        if (oe(
          G,
          2
          /* ErrorTypes.NAVIGATION_GUARD_REDIRECT */
        ))
          return O.NODE_ENV !== "production" && // we are redirecting to the same location we were already at
          Gt(r, w(G.to), j) && // and we have done it a couple of times
          b && // @ts-expect-error: added only in dev
          (b._count = b._count ? (
            // @ts-expect-error
            b._count + 1
          ) : 1) > 30 ? (P(`Detected a possibly infinite redirection in a navigation guard when going from "${k.fullPath}" to "${j.fullPath}". Aborting to avoid a Stack Overflow.
 Are you always returning a new location within a navigation guard? That would lead to this error. Only return when redirecting or aborting, that should fix this. This might break in production if not fixed.`), Promise.reject(new Error("Infinite redirect in navigation guard"))) : I(
            // keep options
            x({
              // preserve an existing replacement but allow the redirect to override it
              replace: C
            }, _(G.to), {
              state: typeof G.to == "object" ? x({}, $, G.to.state) : $,
              force: W
            }),
            // preserve the original redirectedFrom if any
            b || j
          );
      } else
        G = U(j, k, !0, C, $);
      return D(j, k, G), G;
    });
  }
  function F(g, b) {
    const E = S(g, b);
    return E ? Promise.reject(E) : Promise.resolve();
  }
  function X(g) {
    const b = je.values().next().value;
    return b && typeof b.runWithContext == "function" ? b.runWithContext(g) : g();
  }
  function N(g, b) {
    let E;
    const [k, $, W] = Xi(g, b);
    E = ut(k.reverse(), "beforeRouteLeave", g, b);
    for (const V of k)
      V.leaveGuards.forEach((j) => {
        E.push(ue(j, g, b));
      });
    const C = F.bind(null, g, b);
    return E.push(C), we(E).then(() => {
      E = [];
      for (const V of o.list())
        E.push(ue(V, g, b));
      return E.push(C), we(E);
    }).then(() => {
      E = ut($, "beforeRouteUpdate", g, b);
      for (const V of $)
        V.updateGuards.forEach((j) => {
          E.push(ue(j, g, b));
        });
      return E.push(C), we(E);
    }).then(() => {
      E = [];
      for (const V of W)
        if (V.beforeEnter)
          if (Z(V.beforeEnter))
            for (const j of V.beforeEnter)
              E.push(ue(j, g, b));
          else
            E.push(ue(V.beforeEnter, g, b));
      return E.push(C), we(E);
    }).then(() => (g.matched.forEach((V) => V.enterCallbacks = {}), E = ut(W, "beforeRouteEnter", g, b, X), E.push(C), we(E))).then(() => {
      E = [];
      for (const V of i.list())
        E.push(ue(V, g, b));
      return E.push(C), we(E);
    }).catch((V) => oe(
      V,
      8
      /* ErrorTypes.NAVIGATION_CANCELLED */
    ) ? V : Promise.reject(V));
  }
  function D(g, b, E) {
    a.list().forEach((k) => X(() => k(g, b, E)));
  }
  function U(g, b, E, k, $) {
    const W = S(g, b);
    if (W)
      return W;
    const C = b === le, V = ie ? history.state : {};
    E && (k || C ? s.replace(g.fullPath, x({
      scroll: C && V && V.scroll
    }, $)) : s.push(g.fullPath, $)), c.value = g, It(g, b, E, C), st();
  }
  let te;
  function hr() {
    te || (te = s.listen((g, b, E) => {
      if (!Dt.listening)
        return;
      const k = w(g), $ = A(k);
      if ($) {
        I(x($, { replace: !0, force: !0 }), k).catch(xe);
        return;
      }
      d = k;
      const W = c.value;
      ie && ti(Jt(W.fullPath, E.delta), Qe()), N(k, W).catch((C) => oe(
        C,
        12
        /* ErrorTypes.NAVIGATION_CANCELLED */
      ) ? C : oe(
        C,
        2
        /* ErrorTypes.NAVIGATION_GUARD_REDIRECT */
      ) ? (I(
        x(_(C.to), {
          force: !0
        }),
        k
        // avoid an uncaught rejection, let push call triggerError
      ).then((V) => {
        oe(
          V,
          20
          /* ErrorTypes.NAVIGATION_DUPLICATED */
        ) && !E.delta && E.type === Ne.pop && s.go(-1, !1);
      }).catch(xe), Promise.reject()) : (E.delta && s.go(-E.delta, !1), rt(C, k, W))).then((C) => {
        C = C || U(
          // after navigation, all matched components are resolved
          k,
          W,
          !1
        ), C && (E.delta && // a new navigation has been triggered, so we do not want to revert, that will change the current history
        // entry while a different route is displayed
        !oe(
          C,
          8
          /* ErrorTypes.NAVIGATION_CANCELLED */
        ) ? s.go(-E.delta, !1) : E.type === Ne.pop && oe(
          C,
          20
          /* ErrorTypes.NAVIGATION_DUPLICATED */
        ) && s.go(-1, !1)), D(k, W, C);
      }).catch(xe);
    }));
  }
  let nt = Ce(), Tt = Ce(), Be;
  function rt(g, b, E) {
    st(g);
    const k = Tt.list();
    return k.length ? k.forEach(($) => $(g, b, E)) : (O.NODE_ENV !== "production" && P("uncaught error during route navigation:"), console.error(g)), Promise.reject(g);
  }
  function pr() {
    return Be && c.value !== le ? Promise.resolve() : new Promise((g, b) => {
      nt.add([g, b]);
    });
  }
  function st(g) {
    return Be || (Be = !g, hr(), nt.list().forEach(([b, E]) => g ? E(g) : b()), nt.reset()), g;
  }
  function It(g, b, E, k) {
    const { scrollBehavior: $ } = e;
    if (!ie || !$)
      return Promise.resolve();
    const W = !E && ni(Jt(g.fullPath, 0)) || (k || !E) && history.state && history.state.scroll || null;
    return ke().then(() => $(g, b, W)).then((C) => C && ei(C)).catch((C) => rt(C, g, b));
  }
  const ot = (g) => s.go(g);
  let it;
  const je = /* @__PURE__ */ new Set(), Dt = {
    currentRoute: c,
    listening: !0,
    addRoute: h,
    removeRoute: m,
    clearRoutes: t.clearRoutes,
    hasRoute: y,
    getRoutes: p,
    resolve: w,
    options: e,
    push: v,
    replace: R,
    go: ot,
    back: () => ot(-1),
    forward: () => ot(1),
    beforeEach: o.add,
    beforeResolve: i.add,
    afterEach: a.add,
    onError: Tt.add,
    isReady: pr,
    install(g) {
      const b = this;
      g.component("RouterLink", Ti), g.component("RouterView", Bi), g.config.globalProperties.$router = b, Object.defineProperty(g.config.globalProperties, "$route", {
        enumerable: !0,
        get: () => q(c)
      }), ie && // used for the initial navigation client side to avoid pushing
      // multiple times when the router is used in multiple apps
      !it && c.value === le && (it = !0, v(s.location).catch(($) => {
        O.NODE_ENV !== "production" && P("Unexpected error when starting the router:", $);
      }));
      const E = {};
      for (const $ in le)
        Object.defineProperty(E, $, {
          get: () => c.value[$],
          enumerable: !0
        });
      g.provide(Ye, b), g.provide($t, Cr(E)), g.provide(St, c);
      const k = g.unmount;
      je.add(g), g.unmount = function() {
        je.delete(g), je.size < 1 && (d = le, te && te(), te = null, c.value = le, it = !1, Be = !1), k();
      }, O.NODE_ENV !== "production" && ie && Fi(g, b, t);
    }
  };
  function we(g) {
    return g.reduce((b, E) => b.then(() => X(E)), Promise.resolve());
  }
  return Dt;
}
function Xi(e, t) {
  const n = [], r = [], s = [], o = Math.max(t.matched.length, e.matched.length);
  for (let i = 0; i < o; i++) {
    const a = t.matched[i];
    a && (e.matched.find((d) => he(d, a)) ? r.push(a) : n.push(a));
    const c = e.matched[i];
    c && (t.matched.find((d) => he(d, c)) || s.push(c));
  }
  return [n, r, s];
}
function Zi() {
  return ce(Ye);
}
function ea(e) {
  return ce($t);
}
const lr = Symbol("BINDING_GETTER_KEY");
function ta(e, t) {
  const n = oa(e, t);
  return na(e, n, t), xr(() => {
    n._release();
  }), K(lr, n), {
    bindingGetter: n
  };
}
function na(e, t, n) {
  var s, o, i, a, c, d, u, l, f;
  const { id: r } = e;
  if (ra(n.vforSetting, r, t), sa(n.slotSetting, r, t), e.routerParam) {
    const h = M(r, e.routerParam), m = ea(), p = L(() => m.params);
    t._registerBinding(h, p), K(h, p);
  }
  if (e.routerAct) {
    const h = M(r, e.routerAct), m = Zi();
    t._registerBinding(h, m), K(h, m);
  }
  (s = e.data) == null || s.forEach((h) => {
    const m = M(r, h.id);
    t._registerBinding(m, h.value), K(m, h.value);
  }), (o = e.jsFn) == null || o.forEach((h) => {
    const m = M(r, h.id), p = ia(h);
    t._registerBinding(m, p), K(m, p);
  }), (i = e.eRefs) == null || i.forEach((h) => {
    const m = M(r, h.id), p = ae(null);
    t._registerBinding(m, p), K(m, p);
  }), (a = e.refs) == null || a.forEach((h) => {
    const { id: m, constData: p } = h, w = p !== void 0 ? t.getValue(h.value) : h.value, _ = M(r, m), S = ho({ ...h, value: w });
    t._registerBinding(_, S), K(_, S);
  }), (c = e.web_computed) == null || c.forEach((h) => {
    const m = M(r, h.id), p = mo(h);
    t._registerBinding(m, p), K(m, p);
  }), (d = e.js_computed) == null || d.forEach((h) => {
    const m = M(r, h.id), p = go(
      h,
      t
    );
    t._registerBinding(m, p), K(m, p);
  }), (u = e.vue_computed) == null || u.forEach((h) => {
    const m = M(r, h.id), p = po(
      h,
      t
    );
    t._registerBinding(m, p), K(m, p);
  }), vo({
    watchConfigs: e.py_watch || [],
    computedConfigs: e.web_computed || [],
    bindingGetter: t,
    sid: r
  }), (l = e.js_watch) == null || l.forEach((h) => {
    ko(h, t);
  }), (f = e.vue_watch) == null || f.forEach((h) => {
    So(h, t);
  });
}
function ra(e, t, n) {
  if (e != null && e.item) {
    const { id: r } = e.item, s = M(t, r), o = aa(e.item, n);
    n._registerBinding(s, o), K(s, o);
  }
  if (e != null && e.index) {
    const { id: r, value: s } = e.index, o = M(t, r), i = z(s);
    n._registerBinding(o, i), K(o, i);
  }
  if (e != null && e.key) {
    const { id: r, value: s } = e.key, o = M(t, r), i = z(s);
    n._registerBinding(o, i), K(o, i);
  }
}
function sa(e, t, n) {
  if (!e)
    return;
  const { id: r, value: s } = e, o = M(t, r), i = ae(s);
  n._registerBinding(o, i), K(o, i);
}
function oa(e, t) {
  const { binds: n } = e, r = /* @__PURE__ */ new Map(), s = /* @__PURE__ */ new Map();
  let o = null, i = null;
  const a = ca(
    n,
    e.web_computed,
    e.id,
    t
  );
  a == null || a.forEach((v, R) => {
    const { sid: A, id: I } = v, F = M(A, I);
    if (A !== e.id) {
      const X = ce(F);
      r.set(R, X);
    } else
      s.set(F, R);
  });
  function c(v) {
    const R = d(v);
    return to(R, {
      paths: v.path,
      getBindableValueFn: u
    });
  }
  function d(v) {
    const R = r.get(v.r);
    if (!R)
      throw new Error(`Binding not found: ${JSON.stringify(v)}`);
    return R;
  }
  function u(v) {
    return Se(c(v));
  }
  function l(v) {
    const R = r.get(v.r);
    if (!R)
      throw new Error(`Router binding not found: ${JSON.stringify(v)}`);
    return R;
  }
  function f(v, R) {
    if (Nn(v)) {
      const A = d(v);
      if (v.path) {
        Bn(A.value, v.path, R, u);
        return;
      }
      A.value = R;
      return;
    }
    throw new Error(`Unsupported output binding: ${v}`);
  }
  function h(v) {
    if (v != null && v.item) {
      const { id: R, value: A, sourceInfo: I } = v.item;
      if (I) {
        const { index: N, key: D } = I;
        o && (o.value = N), i && (i.value = D);
      }
      const F = M(e.id, R), X = c({ r: p(F) });
      X.value = A;
    }
    if (v != null && v.index) {
      const { id: R, value: A } = v.index, I = M(e.id, R), F = c({ r: p(I) });
      F.value = A;
    }
    if (v != null && v.key) {
      const { id: R, value: A } = v.key, I = M(e.id, R), F = c({ r: p(I) });
      F.value = A;
    }
  }
  function m(v) {
    if (!v)
      return;
    const { id: R, value: A } = v, I = M(e.id, R), F = c({ r: p(I) });
    F.value = A;
  }
  function p(v) {
    return s.get(v);
  }
  function y(v, R) {
    const A = s.get(v);
    A !== void 0 && r.set(A, R);
  }
  function w() {
    r.clear(), s.clear();
  }
  function _(v) {
    return o = z(v), o;
  }
  function S(v) {
    return i = z(v), i;
  }
  return {
    getValue: u,
    getRef: c,
    updateValue: f,
    getBindIndex: p,
    updateVForInfo: h,
    updateSlotInfo: m,
    getRouter: l,
    initVForIndexRef: _,
    initVForKeyRef: S,
    _registerBinding: y,
    _release: w
  };
}
function M(e, t) {
  return `${e}-${t}`;
}
function ia(e) {
  const { immediately: t = !1, code: n } = e;
  let r = Y(n);
  return t && (r = r()), ye(() => ({
    get() {
      return r;
    },
    set() {
      throw new Error("Cannot set value to js function");
    }
  }));
}
function lc() {
  const { getRef: e, getRouter: t, getValue: n } = ce(lr);
  return {
    getRef: e,
    getRouter: t,
    getValue: n
  };
}
function aa(e, t) {
  const { value: n, sourceInfo: r } = e;
  if (r) {
    const { source: s, type: o, index: i, key: a } = r, c = t.initVForIndexRef(i);
    return o === "array" ? ye(() => ({
      get() {
        return s.value[c.value];
      },
      set(d) {
        s.value[c.value] = d;
      }
    })) : ye(() => {
      const d = t.initVForKeyRef(a);
      return {
        get() {
          return s.value[d.value];
        },
        set(u) {
          s.value[d.value] = u;
        }
      };
    });
  }
  return z(n);
}
function ca(e, t, n, r) {
  const s = new Set(e == null ? void 0 : e.map((c) => M(c.sid, c.id))), o = la(
    e,
    s,
    t,
    n
  ), i = ua(
    o,
    s,
    n,
    r
  );
  return fa(
    i,
    s,
    n,
    r
  );
}
function la(e, t, n, r) {
  if (!n)
    return e;
  const s = n.filter((o) => !t.has(M(r, o.id))).map((o) => ({ id: o.id, sid: r }));
  return [...e ?? [], ...s];
}
function ua(e, t, n, r) {
  if (!r.vforSetting)
    return e;
  const s = [];
  return r.vforSetting.item && !t.has(M(n, r.vforSetting.item.id)) && s.push({
    id: r.vforSetting.item.id,
    sid: n
  }), r.vforSetting.index && !t.has(M(n, r.vforSetting.index.id)) && s.push({
    id: r.vforSetting.index.id,
    sid: n
  }), r.vforSetting.key && !t.has(M(n, r.vforSetting.key.id)) && s.push({
    id: r.vforSetting.key.id,
    sid: n
  }), [...e ?? [], ...s];
}
function fa(e, t, n, r) {
  return !r.slotSetting || t.has(M(n, r.slotSetting.id)) ? e : [
    ...e ?? [],
    { id: r.slotSetting.id, sid: n }
  ];
}
const ur = ee(da, {
  props: ["config", "vforSetting", "slotSetting"]
});
function da(e) {
  const { config: t, vforSetting: n, slotSetting: r } = e, { items: s } = t, { bindingGetter: o } = ta(t, { vforSetting: n, slotSetting: r });
  return () => {
    if (o.updateVForInfo(e.vforSetting), o.updateSlotInfo(e.slotSetting), !s)
      return null;
    if (s.length === 1) {
      const i = s[0];
      return ve(i, { sid: t.id, bindingGetter: o });
    }
    return s == null ? void 0 : s.map(
      (i) => ve(i, { sid: t.id, bindingGetter: o })
    );
  };
}
function ha(e, t) {
  const { state: n, isReady: r, isLoading: s } = Us(async () => {
    let o = e;
    const i = t;
    if (!o && !i)
      throw new Error("Either config or configUrl must be provided");
    if (!o && i && (o = await (await fetch(i)).json()), !o)
      throw new Error("Failed to load config");
    return o;
  }, {});
  return { config: n, isReady: r, isLoading: s };
}
function pa(e) {
  const t = z(!1), n = z("");
  function r(s, o) {
    let i;
    return o.component ? i = `Error captured from component:tag: ${o.component.tag} ; id: ${o.component.id} ` : i = "Error captured from app init", console.group(i), console.error("Component:", o.component), console.error("Error:", s), console.groupEnd(), e && (t.value = !0, n.value = `${i} ${s.message}`), !1;
  }
  return $r(r), { hasError: t, errorMessage: n };
}
function ma(e) {
  if (!(e === "web" || e === "webview") && e !== "zero")
    throw new Error(`Unsupported mode: ${e}`);
}
function ga(e, t) {
  const n = L(() => {
    const r = e.value;
    if (!r)
      return null;
    const i = new DOMParser().parseFromString(r, "image/svg+xml").querySelector("svg");
    if (!i)
      throw new Error("Invalid svg string");
    const a = {};
    for (const f of i.attributes)
      a[f.name] = f.value;
    const { size: c, color: d, attrs: u } = t;
    d.value !== null && d.value !== void 0 && (i.removeAttribute("fill"), i.querySelectorAll("*").forEach((h) => {
      h.hasAttribute("fill") && h.setAttribute("fill", "currentColor");
    }), a.color = d.value), c.value !== null && c.value !== void 0 && (a.width = c.value.toString(), a.height = c.value.toString());
    const l = i.innerHTML;
    return {
      ...a,
      ...u,
      innerHTML: l
    };
  });
  return () => {
    if (!n.value)
      return null;
    const r = n.value;
    return J("svg", r);
  };
}
const fn = "assets/icons";
async function ya(e) {
  if (!e) return;
  const { names: t, sets: n } = e, r = [];
  if (t) {
    const o = {};
    for (const i of t) {
      const [a, c] = i.split(":");
      o[a] || (o[a] = []), o[a].push(c);
    }
    for (const i of Object.keys(o)) {
      const a = `/${fn}/${i}.svg`, c = await fetch(a);
      if (!c.ok) throw new Error(`Failed to load ${a}`);
      const d = await c.text(), l = new DOMParser().parseFromString(d, "image/svg+xml");
      for (const f of o[i]) {
        const h = l.getElementById(f);
        if (!h) {
          console.warn(`Failed to find icon ${f} in ${a}`);
          continue;
        }
        h.setAttribute("id", `${i}:${f}`), r.push(h.outerHTML);
      }
    }
  }
  if (n)
    for (const o of n) {
      const i = `/${fn}/${o}.svg`, a = await fetch(i);
      if (!a.ok) throw new Error(`Failed to load ${i}`);
      const c = await a.text(), u = new DOMParser().parseFromString(c, "image/svg+xml"), l = Array.from(u.querySelectorAll("symbol"));
      if (l.length === 0) {
        console.warn(`No <symbol> found in ${i}`);
        continue;
      }
      for (const f of l) {
        const h = f.getAttribute("id");
        h && (f.setAttribute("id", `${o}:${h}`), r.push(f.outerHTML));
      }
    }
  const s = `<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
${r.join(
    `
`
  )}
</svg>`;
  document.body.insertAdjacentHTML("afterbegin", s);
}
const va = {
  class: "app-box insta-theme",
  "data-scaling": "100%"
}, wa = {
  key: 0,
  style: { position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)" }
}, _a = {
  key: 0,
  style: { color: "red", "font-size": "1.2em", margin: "1rem", border: "1px dashed red", padding: "1rem" }
}, Ea = /* @__PURE__ */ ee({
  __name: "App",
  props: {
    config: {},
    meta: {},
    configUrl: {}
  },
  setup(e) {
    const t = e, { debug: n = !1 } = t.meta, { config: r, isLoading: s } = ha(
      t.config,
      t.configUrl
    );
    Q(r, (a) => {
      a.url && (Lr({
        mode: t.meta.mode,
        version: t.meta.version,
        queryPath: a.url.path,
        pathParams: a.url.params,
        webServerInfo: a.webInfo,
        debug: n
      }), ns(t.meta.mode), ya(a.icons)), ma(t.meta.mode);
    });
    const { hasError: o, errorMessage: i } = pa(n);
    return (a, c) => (fe(), be("div", va, [
      q(s) ? (fe(), be("div", wa, c[0] || (c[0] = [
        wn("p", { style: { margin: "auto" } }, "Loading ...", -1)
      ]))) : (fe(), be("div", {
        key: 1,
        class: ft(["insta-main", q(r).class])
      }, [
        Tr(q(ur), {
          config: q(r).scope
        }, null, 8, ["config"]),
        q(o) ? (fe(), be("div", _a, yn(q(i)), 1)) : dt("", !0)
      ], 2))
    ]));
  }
}), dn = /* @__PURE__ */ new Map([
  [
    "size",
    {
      classes: "ist-r-size",
      handler: (e) => ba(e)
    }
  ],
  [
    "weight",
    {
      classes: "ist-r-weight",
      styleVar: "--weight",
      handler: (e) => e
    }
  ],
  [
    "text_align",
    {
      classes: "ist-r-ta",
      styleVar: "--ta",
      handler: (e) => e
    }
  ],
  [
    "trim",
    {
      classes: (e) => Sa("ist-r", e)
    }
  ],
  [
    "truncate",
    {
      classes: "ist-r-truncate"
    }
  ],
  [
    "text_wrap",
    {
      classes: "ist-r-tw",
      handler: (e) => ka(e)
    }
  ]
]);
function fr(e) {
  const t = {}, n = [], r = {};
  for (const [o, i] of Object.entries(e)) {
    if (i === void 0 || !dn.has(o))
      continue;
    const a = typeof i == "object" ? i : { initial: i };
    for (const [c, d] of Object.entries(a)) {
      const { classes: u, styleVar: l, handler: f, propHandler: h } = dn.get(o), m = c === "initial";
      if (u) {
        const p = typeof u == "function" ? u(d) : u, y = m ? p : `${c}:${p}`;
        n.push(y);
      }
      if (f) {
        const p = f(d);
        if (l) {
          const y = m ? l : `${l}-${c}`;
          t[y] = p;
        } else {
          if (!Array.isArray(p))
            throw new Error(`Invalid style value: ${p}`);
          p.forEach((y) => {
            for (const [w, _] of Object.entries(y))
              t[w] = _;
          });
        }
      }
      if (h) {
        const p = h(d);
        for (const [y, w] of Object.entries(p))
          r[y] = w;
      }
    }
  }
  return {
    classes: n.join(" "),
    style: t,
    props: r
  };
}
function ba(e) {
  const t = Number(e);
  if (isNaN(t))
    throw new Error(`Invalid font size value: ${e}`);
  return [
    { "--fs": `var(--font-size-${t})` },
    { "--lh": `var(--line-height-${t})` },
    { "--ls": `var(--letter-spacing-${t})` }
  ];
}
function Sa(e, t) {
  return `${e}-lt-${t}`;
}
function ka(e) {
  if (e === "wrap")
    return [
      {
        "--ws": "normal"
      }
    ];
  if (e === "nowrap")
    return [
      {
        "--ws": "nowrap"
      }
    ];
  if (e === "pretty")
    return [{ "--ws": "normal" }, { "--tw": "pretty" }];
  if (e === "balance")
    return [{ "--ws": "normal" }, { "--tw": "balance" }];
  throw new Error(`Invalid text wrap value: ${e}`);
}
const Ra = "insta-Heading", Oa = ee(Pa, {
  props: [
    "as",
    "as_child",
    "size",
    "weight",
    "align",
    "trim",
    "truncate",
    "text_wrap",
    "innerText"
  ]
});
function Pa(e) {
  return () => {
    const { classes: t, style: n, props: r } = fr(e), s = de(
      { class: t, style: n, ...r },
      { class: Ra }
    );
    return J(e.as || "h1", s, e.innerText);
  };
}
const Na = /* @__PURE__ */ ee({
  __name: "_Teleport",
  props: {
    to: {},
    defer: { type: Boolean, default: !0 },
    disabled: { type: Boolean, default: !1 }
  },
  setup(e) {
    return (t, n) => (fe(), _n(Ir, {
      to: t.to,
      defer: t.defer,
      disabled: t.disabled
    }, [
      Dr(t.$slots, "default")
    ], 8, ["to", "defer", "disabled"]));
  }
}), Va = ["width", "height", "color"], Ca = ["xlink:href"], Aa = /* @__PURE__ */ ee({
  __name: "Icon",
  props: {
    size: {},
    icon: {},
    color: {},
    assetPath: {},
    svgName: {},
    rawSvg: {}
  },
  setup(e) {
    const t = e, n = me(() => t.icon ? t.icon.split(":")[1] : ""), r = me(() => t.size || "1em"), s = me(() => t.color || "currentColor"), o = me(() => t.rawSvg || null), i = L(() => `#${t.icon}`), a = Mr(), c = ga(o, {
      size: me(() => t.size),
      color: me(() => t.color),
      attrs: a
    });
    return (d, u) => (fe(), be(Br, null, [
      n.value ? (fe(), be("svg", de({
        key: 0,
        width: r.value,
        height: r.value,
        color: s.value
      }, q(a)), [
        wn("use", { "xlink:href": i.value }, null, 8, Ca)
      ], 16, Va)) : dt("", !0),
      o.value ? (fe(), _n(q(c), { key: 1 })) : dt("", !0)
    ], 64));
  }
}), $e = /* @__PURE__ */ new Map([
  [
    "p",
    {
      classes: "ist-r-p",
      styleVar: "--p",
      handler: (e) => B("space", e)
    }
  ],
  [
    "px",
    {
      classes: "ist-r-px",
      styleVar: "--px",
      handler: (e) => B("space", e)
    }
  ],
  [
    "py",
    {
      classes: "ist-r-py",
      styleVar: "--py",
      handler: (e) => B("space", e)
    }
  ],
  [
    "pt",
    {
      classes: "ist-r-pt",
      styleVar: "--pt",
      handler: (e) => B("space", e)
    }
  ],
  [
    "pb",
    {
      classes: "ist-r-pb",
      styleVar: "--pb",
      handler: (e) => B("space", e)
    }
  ],
  [
    "pl",
    {
      classes: "ist-r-pl",
      styleVar: "--pl",
      handler: (e) => B("space", e)
    }
  ],
  [
    "pr",
    {
      classes: "ist-r-pr",
      styleVar: "--pr",
      handler: (e) => B("space", e)
    }
  ],
  [
    "width",
    {
      classes: "ist-r-w",
      styleVar: "--width",
      handler: (e) => e
    }
  ],
  [
    "height",
    {
      classes: "ist-r-h",
      styleVar: "--height",
      handler: (e) => e
    }
  ],
  [
    "min_width",
    {
      classes: "ist-r-min-w",
      styleVar: "--min_width",
      handler: (e) => e
    }
  ],
  [
    "min_height",
    {
      classes: "ist-r-min-h",
      styleVar: "--min_height",
      handler: (e) => e
    }
  ],
  [
    "max_width",
    {
      classes: "ist-r-max-w",
      styleVar: "--max_width",
      handler: (e) => e
    }
  ],
  [
    "max_height",
    {
      classes: "ist-r-max-h",
      styleVar: "--max_height",
      handler: (e) => e
    }
  ],
  [
    "position",
    {
      classes: "ist-r-position",
      styleVar: "--position",
      handler: (e) => e
    }
  ],
  [
    "inset",
    {
      classes: "ist-r-inset",
      styleVar: "--inset",
      handler: (e) => B("space", e)
    }
  ],
  [
    "top",
    {
      classes: "ist-r-top",
      styleVar: "--top",
      handler: (e) => B("space", e)
    }
  ],
  [
    "right",
    {
      classes: "ist-r-right",
      styleVar: "--right",
      handler: (e) => B("space", e)
    }
  ],
  [
    "bottom",
    {
      classes: "ist-r-bottom",
      styleVar: "--bottom",
      handler: (e) => B("space", e)
    }
  ],
  [
    "left",
    {
      classes: "ist-r-left",
      styleVar: "--left",
      handler: (e) => B("space", e)
    }
  ],
  [
    "overflow",
    {
      classes: "ist-r-overflow",
      styleVar: "--overflow",
      handler: (e) => e
    }
  ],
  [
    "overflow_x",
    {
      classes: "ist-r-ox",
      styleVar: "--overflow_x",
      handler: (e) => e
    }
  ],
  [
    "overflow_y",
    {
      classes: "ist-r-oy",
      styleVar: "--overflow_y",
      handler: (e) => e
    }
  ],
  [
    "flex_basis",
    {
      classes: "ist-r-fb",
      styleVar: "--flex_basis",
      handler: (e) => e
    }
  ],
  [
    "flex_shrink",
    {
      classes: "ist-r-fs",
      styleVar: "--flex_shrink",
      handler: (e) => e
    }
  ],
  [
    "flex_grow",
    {
      classes: "ist-r-fg",
      styleVar: "--flex_grow",
      handler: (e) => e
    }
  ],
  [
    "grid_area",
    {
      classes: "ist-r-ga",
      styleVar: "--grid_area",
      handler: (e) => e
    }
  ],
  [
    "grid_column",
    {
      classes: "ist-r-gc",
      styleVar: "--grid_column",
      handler: (e) => e
    }
  ],
  [
    "grid_column_start",
    {
      classes: "ist-r-gcs",
      styleVar: "--grid_column_start",
      handler: (e) => e
    }
  ],
  [
    "grid_column_end",
    {
      classes: "ist-r-gce",
      styleVar: "--grid_column_end",
      handler: (e) => e
    }
  ],
  [
    "grid_row",
    {
      classes: "ist-r-gr",
      styleVar: "--grid_row",
      handler: (e) => e
    }
  ],
  [
    "grid_row_start",
    {
      classes: "ist-r-grs",
      styleVar: "--grid_row_start",
      handler: (e) => e
    }
  ],
  [
    "grid_row_end",
    {
      classes: "ist-r-gre",
      styleVar: "--grid_row_end",
      handler: (e) => e
    }
  ],
  [
    "m",
    {
      classes: "ist-r-m",
      styleVar: "--m",
      handler: (e) => B("space", e)
    }
  ],
  [
    "mx",
    {
      classes: "ist-r-mx",
      styleVar: "--mx",
      handler: (e) => B("space", e)
    }
  ],
  [
    "my",
    {
      classes: "ist-r-my",
      styleVar: "--my",
      handler: (e) => B("space", e)
    }
  ],
  [
    "mt",
    {
      classes: "ist-r-mt",
      styleVar: "--mt",
      handler: (e) => B("space", e)
    }
  ],
  [
    "mr",
    {
      classes: "ist-r-mr",
      styleVar: "--mr",
      handler: (e) => B("space", e)
    }
  ],
  [
    "mb",
    {
      classes: "ist-r-mb",
      styleVar: "--mb",
      handler: (e) => B("space", e)
    }
  ],
  [
    "ml",
    {
      classes: "ist-r-ml",
      styleVar: "--ml",
      handler: (e) => B("space", e)
    }
  ],
  [
    "display",
    {
      classes: "ist-r-display",
      styleVar: "--display",
      handler: (e) => e
    }
  ],
  [
    "direction",
    {
      classes: "ist-r-fd",
      styleVar: "--direction",
      handler: (e) => e
    }
  ],
  [
    "align",
    {
      classes: "ist-r-ai",
      styleVar: "--align",
      handler: (e) => e
    }
  ],
  [
    "justify",
    {
      classes: "ist-r-jc",
      styleVar: "--justify",
      handler: (e) => e
    }
  ],
  [
    "wrap",
    {
      classes: "ist-r-wrap",
      styleVar: "--wrap",
      handler: (e) => e
    }
  ],
  [
    "gap",
    {
      classes: "ist-r-gap",
      styleVar: "--gap",
      handler: (e) => B("space", e)
    }
  ],
  [
    "gap_x",
    {
      classes: "ist-r-cg",
      styleVar: "--gap_x",
      handler: (e) => B("space", e)
    }
  ],
  [
    "gap_y",
    {
      classes: "ist-r-rg",
      styleVar: "--gap_y",
      handler: (e) => B("space", e)
    }
  ],
  [
    "areas",
    {
      classes: "ist-r-gta",
      styleVar: "--areas",
      handler: (e) => e
    }
  ],
  [
    "columns",
    {
      classes: "ist-r-gtc",
      styleVar: "--columns",
      handler: (e) => hn(e)
    }
  ],
  [
    "rows",
    {
      classes: "ist-r-gtr",
      styleVar: "--rows",
      handler: (e) => hn(e)
    }
  ],
  [
    "flow",
    {
      classes: "ist-r-gaf",
      styleVar: "--flow",
      handler: (e) => e
    }
  ],
  [
    "ctn_size",
    {
      classes: "ist-r-ctn_size",
      styleVar: "--ctn_size",
      handler: (e) => B("container", e)
    }
  ]
]);
function Xe(e) {
  e.length > 1 && console.warn("Only accept one child element when as_child is true");
}
function Ze(e) {
  return Object.fromEntries(
    Object.entries(e).filter(([t, n]) => n !== void 0)
  );
}
function et(e, t) {
  const n = {}, r = [], s = new Set(t || []), o = {
    style: {},
    class: []
  };
  for (const [a, c] of Object.entries(e)) {
    if (!$e.has(a))
      continue;
    const d = typeof c == "object" ? c : { initial: c };
    for (const [u, l] of Object.entries(d)) {
      const { classes: f, styleVar: h, handler: m } = $e.get(a), p = u === "initial", y = p ? f : `${u}:${f}`, w = p ? h : `${h}-${u}`, _ = m(l);
      if (s.has(a)) {
        o.class.push(y), o.style[w] = _;
        continue;
      }
      r.push(y), n[w] = _;
    }
  }
  return {
    classes: r.join(" "),
    style: n,
    excludeReslut: o
  };
}
function B(e, t) {
  const n = Number(t);
  if (isNaN(n))
    return t;
  {
    const r = n < 0 ? -1 : 1;
    return `calc(var(--${e}-${n}) * ${r})`;
  }
}
function hn(e) {
  const t = Number(e);
  return isNaN(t) ? e : `repeat(${t}, 1fr)`;
}
const tt = [
  "p",
  "px",
  "py",
  "pt",
  "pb",
  "pl",
  "pr",
  "width",
  "height",
  "min_width",
  "min_height",
  "max_width",
  "max_height",
  "position",
  "inset",
  "top",
  "right",
  "bottom",
  "left",
  "overflow",
  "overflow_x",
  "overflow_y",
  "flex_basis",
  "flex_shrink",
  "flex_grow",
  "grid_area",
  "grid_column",
  "grid_column_start",
  "grid_column_end",
  "grid_row",
  "grid_row_start",
  "grid_row_end",
  "m",
  "mx",
  "my",
  "mt",
  "mr",
  "mb",
  "ml"
], xa = [
  "as",
  "as_child",
  "display",
  "align",
  "justify",
  "wrap",
  "gap",
  "gap_x",
  "gap_y"
].concat(tt), $a = ["direction"].concat(xa), Ta = [
  "as_child",
  "size",
  "display",
  "align",
  "ctn_size"
].concat(tt), Ia = ["as", "as_child", "display"].concat(tt), Da = [
  "as",
  "as_child",
  "display",
  "areas",
  "columns",
  "rows",
  "flow",
  "align",
  "justify",
  "gap",
  "gap_x",
  "gap_y"
].concat(tt), Ma = "insta-Box", Ba = ee(ja, {
  props: Ia
});
function ja(e) {
  const t = Me();
  return () => {
    var a;
    const n = Ze(e), { classes: r, style: s } = et(n), o = de(
      { class: r, style: s },
      { class: Ma }
    ), i = (a = t.default) == null ? void 0 : a.call(t);
    return e.as_child && i && i.length > 0 ? (Xe(i), se(i[0], o)) : J(e.as || "div", o, i);
  };
}
const La = "insta-Flex", Fa = {
  gap: "2"
}, Ua = ee(Wa, {
  props: $a
});
function Wa(e) {
  const t = Me();
  return () => {
    var a;
    const n = { ...Fa, ...Ze(e) }, { classes: r, style: s } = et(n), o = de(
      { class: r, style: s },
      { class: La }
    ), i = (a = t.default) == null ? void 0 : a.call(t);
    return e.as_child && i && i.length > 0 ? (Xe(i), se(i[0], o)) : J(e.as || "div", o, i);
  };
}
const za = "insta-Grid", Ha = {
  gap: "2"
}, Ka = ee(Ga, {
  props: Da
});
function Ga(e) {
  const t = Me();
  return () => {
    var c;
    const n = { ...Ha, ...Ze(e) }, r = et(n), [s, o] = qa(r.classes, r.style), i = de(
      { class: s, style: o },
      { class: za }
    ), a = (c = t.default) == null ? void 0 : c.call(t);
    return e.as_child && a && a.length > 0 ? (Xe(a), se(a[0], i)) : J(e.as || "div", i, a);
  };
}
function qa(e, t) {
  const n = $e.get("areas").styleVar, r = $e.get("columns").styleVar, s = n in t, o = r in t;
  if (!s || o)
    return [e, t];
  const i = Ja(t[n]);
  if (i) {
    const { classes: a, styleVar: c } = $e.get("columns");
    e = `${e} ${a}`, t[c] = i;
  }
  return [e, t];
}
function Ja(e) {
  if (typeof e != "string") return null;
  const t = [...e.matchAll(/"([^"]+)"/g)].map((i) => i[1]);
  if (t.length === 0) return null;
  const s = t[0].trim().split(/\s+/).length;
  return t.every(
    (i) => i.trim().split(/\s+/).length === s
  ) ? `repeat(${s}, 1fr)` : null;
}
const Qa = "insta-Container", Ya = ee(Xa, {
  props: Ta
});
function Xa(e) {
  const t = Me();
  return () => {
    var d;
    const n = Ze(e), { classes: r, style: s, excludeReslut: o } = et(n, [
      "ctn_size"
    ]), i = de(
      { class: r, style: s },
      { class: Qa }
    ), a = (d = t.default) == null ? void 0 : d.call(t);
    if (e.as_child && a && a.length > 0)
      return Xe(a), se(a[0], i);
    const c = J(
      "div",
      de({ class: "insta-ContainerInner" }, o),
      a
    );
    return J("div", i, c);
  };
}
const Za = "insta-Text", ec = ee(tc, {
  props: [
    "as",
    "as_child",
    "size",
    "weight",
    "align",
    "trim",
    "truncate",
    "text_wrap",
    "innerText"
  ]
});
function tc(e) {
  return () => {
    const { classes: t, style: n, props: r } = fr(e), s = de(
      { class: t, style: n, ...r },
      { class: Za }
    );
    return J(e.as || "span", s, e.innerText);
  };
}
const pn = "insta-Link", nc = ee(rc, {
  props: ["href", "text", "target", "type"]
});
function rc(e) {
  const t = Me().default;
  return () => {
    const n = t ? [pn, "has-child"] : [pn], r = {
      href: e.href,
      target: e.target,
      type: e.type,
      class: n
    };
    return J("a", r, t ? t() : e.text);
  };
}
function sc(e, t) {
  const { mode: n = "hash" } = t.router, r = n === "hash" ? ai() : n === "memory" ? ii() : Xn();
  e.use(
    Yi({
      history: r,
      routes: oc(t)
    })
  );
}
function oc(e) {
  if (!e.router)
    throw new Error("Router config is not provided.");
  const { routes: t = [], kAlive: n = !1 } = e.router;
  return t.map(
    (s) => dr(s, n)
  );
}
function dr(e, t) {
  const {
    server: n = !1,
    vueItem: r,
    scope: s,
    children: o
  } = e, i = () => {
    if (n)
      throw new Error("Server-side rendering is not supported yet.");
    return Promise.resolve(ic(e, t));
  }, a = o == null ? void 0 : o.map(
    (d) => dr(d, t)
  ), c = {
    ...r,
    children: a,
    component: i
  };
  return s || delete c.component, a || delete c.children, c;
}
function ic(e, t) {
  const { scope: n } = e;
  if (!n)
    throw new Error("Scope is not provided.");
  const r = se(Te(n), { key: n.id });
  return t ? J(jr, null, () => r) : r;
}
function uc(e, t) {
  e.component("insta-ui", Ea), e.component("teleport", Na), e.component("icon", Aa), e.component("heading", Oa), e.component("box", Ba), e.component("flex", Ua), e.component("grid", Ka), e.component("container", Ya), e.component("ui-text", ec), e.component("ui-link", nc), t.router && sc(e, t);
}
export {
  He as convertDynamicProperties,
  We as getAppInfo,
  uc as install,
  lc as useBindingGetter,
  ao as useLanguage
};
