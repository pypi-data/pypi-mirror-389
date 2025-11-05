import { defineComponent as z, useAttrs as Y, useSlots as J, createBlock as G, openBlock as B, mergeProps as Q, unref as g, createSlots as k, renderList as L, withCtx as C, renderSlot as tt, normalizeProps as et, guardReactiveProps as rt, computed as w, ref as Jt, createElementVNode as St, createVNode as ve, toDisplayString as lt, createTextVNode as Ct, resolveDynamicComponent as be } from "vue";
import * as R from "tdesign-vue-next";
import { DateRangePickerPanel as me, useConfig as Ae, MessagePlugin as we, NotifyPlugin as Te } from "tdesign-vue-next";
function Oe(t) {
  const { container: e = ".insta-main" } = t;
  return e;
}
const $e = /* @__PURE__ */ z({
  inheritAttrs: !1,
  __name: "Affix",
  setup(t) {
    const e = Y(), r = J(), n = Oe(e);
    return (a, i) => (B(), G(R.Affix, Q(g(e), { container: g(n) }), k({ _: 2 }, [
      L(g(r), (o, u) => ({
        name: u,
        fn: C((s) => [
          tt(a.$slots, u, et(rt(s)))
        ])
      }))
    ]), 1040, ["container"]));
  }
});
function Pe(t) {
  const e = [], r = w(() => t.data ?? []);
  return {
    tableData: w(() => {
      const i = r.value;
      return e.reduce((o, u) => u(o), i);
    }),
    orgData: r,
    registerRowsHandler: (i) => {
      e.push(i);
    }
  };
}
function Se(t) {
  const { tableData: e, attrs: r } = t, n = [], a = w(() => {
    const o = r.extraColumns ?? [];
    let f = [...!r.columns && e.value.length > 0 ? Ce(e.value) : r.columns ?? [], ...o];
    f = f.map(xe);
    for (const c of n)
      f = c(f);
    return f;
  });
  function i(o) {
    n.push(o);
  }
  return [a, i];
}
function Ce(t) {
  const e = t[0];
  return Object.keys(e).map((n) => ({
    colKey: n,
    title: n,
    sorter: !0
  }));
}
function xe(t) {
  const e = t.name ?? t.colKey, r = `header-cell-${e}`, n = `body-cell-${e}`, a = t.label ?? t.colKey;
  return {
    ...t,
    name: e,
    label: a,
    title: r,
    cell: n
  };
}
function Ee(t) {
  const { tableData: e, attrs: r } = t;
  return w(() => {
    const { pagination: n } = r;
    let a;
    if (typeof n == "boolean") {
      if (!n)
        return;
      a = {
        defaultPageSize: 10
      };
    }
    return typeof n == "number" && n > 0 && (a = {
      defaultPageSize: n
    }), typeof n == "object" && n !== null && (a = n), {
      defaultCurrent: 1,
      total: e.value.length,
      ...a
    };
  });
}
var Qt = typeof global == "object" && global && global.Object === Object && global, Re = typeof self == "object" && self && self.Object === Object && self, O = Qt || Re || Function("return this")(), x = O.Symbol, kt = Object.prototype, De = kt.hasOwnProperty, je = kt.toString, K = x ? x.toStringTag : void 0;
function Fe(t) {
  var e = De.call(t, K), r = t[K];
  try {
    t[K] = void 0;
    var n = !0;
  } catch {
  }
  var a = je.call(t);
  return n && (e ? t[K] = r : delete t[K]), a;
}
var Ie = Object.prototype, Me = Ie.toString;
function Le(t) {
  return Me.call(t);
}
var Ne = "[object Null]", ze = "[object Undefined]", xt = x ? x.toStringTag : void 0;
function H(t) {
  return t == null ? t === void 0 ? ze : Ne : xt && xt in Object(t) ? Fe(t) : Le(t);
}
function N(t) {
  return t != null && typeof t == "object";
}
var Ge = "[object Symbol]";
function q(t) {
  return typeof t == "symbol" || N(t) && H(t) == Ge;
}
function it(t, e) {
  for (var r = -1, n = t == null ? 0 : t.length, a = Array(n); ++r < n; )
    a[r] = e(t[r], r, t);
  return a;
}
var A = Array.isArray, Et = x ? x.prototype : void 0, Rt = Et ? Et.toString : void 0;
function te(t) {
  if (typeof t == "string")
    return t;
  if (A(t))
    return it(t, te) + "";
  if (q(t))
    return Rt ? Rt.call(t) : "";
  var e = t + "";
  return e == "0" && 1 / t == -1 / 0 ? "-0" : e;
}
function vt(t) {
  var e = typeof t;
  return t != null && (e == "object" || e == "function");
}
function ee(t) {
  return t;
}
var Be = "[object AsyncFunction]", He = "[object Function]", Ue = "[object GeneratorFunction]", Ke = "[object Proxy]";
function re(t) {
  if (!vt(t))
    return !1;
  var e = H(t);
  return e == He || e == Ue || e == Be || e == Ke;
}
var ct = O["__core-js_shared__"], Dt = function() {
  var t = /[^.]+$/.exec(ct && ct.keys && ct.keys.IE_PROTO || "");
  return t ? "Symbol(src)_1." + t : "";
}();
function We(t) {
  return !!Dt && Dt in t;
}
var qe = Function.prototype, Ve = qe.toString;
function j(t) {
  if (t != null) {
    try {
      return Ve.call(t);
    } catch {
    }
    try {
      return t + "";
    } catch {
    }
  }
  return "";
}
var Xe = /[\\^$.*+?()[\]{}|]/g, Ze = /^\[object .+?Constructor\]$/, Ye = Function.prototype, Je = Object.prototype, Qe = Ye.toString, ke = Je.hasOwnProperty, tr = RegExp(
  "^" + Qe.call(ke).replace(Xe, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
);
function er(t) {
  if (!vt(t) || We(t))
    return !1;
  var e = re(t) ? tr : Ze;
  return e.test(j(t));
}
function rr(t, e) {
  return t?.[e];
}
function U(t, e) {
  var r = rr(t, e);
  return er(r) ? r : void 0;
}
var dt = U(O, "WeakMap");
function nr() {
}
function ir(t, e, r, n) {
  for (var a = t.length, i = r + -1; ++i < a; )
    if (e(t[i], i, t))
      return i;
  return -1;
}
function ar(t) {
  return t !== t;
}
function or(t, e, r) {
  for (var n = r - 1, a = t.length; ++n < a; )
    if (t[n] === e)
      return n;
  return -1;
}
function sr(t, e, r) {
  return e === e ? or(t, e, r) : ir(t, ar, r);
}
function ur(t, e) {
  var r = t == null ? 0 : t.length;
  return !!r && sr(t, e, 0) > -1;
}
var fr = 9007199254740991, lr = /^(?:0|[1-9]\d*)$/;
function ne(t, e) {
  var r = typeof t;
  return e = e ?? fr, !!e && (r == "number" || r != "symbol" && lr.test(t)) && t > -1 && t % 1 == 0 && t < e;
}
function ie(t, e) {
  return t === e || t !== t && e !== e;
}
var cr = 9007199254740991;
function bt(t) {
  return typeof t == "number" && t > -1 && t % 1 == 0 && t <= cr;
}
function mt(t) {
  return t != null && bt(t.length) && !re(t);
}
var pr = Object.prototype;
function gr(t) {
  var e = t && t.constructor, r = typeof e == "function" && e.prototype || pr;
  return t === r;
}
function dr(t, e) {
  for (var r = -1, n = Array(t); ++r < t; )
    n[r] = e(r);
  return n;
}
var hr = "[object Arguments]";
function jt(t) {
  return N(t) && H(t) == hr;
}
var ae = Object.prototype, _r = ae.hasOwnProperty, yr = ae.propertyIsEnumerable, oe = jt(/* @__PURE__ */ function() {
  return arguments;
}()) ? jt : function(t) {
  return N(t) && _r.call(t, "callee") && !yr.call(t, "callee");
};
function vr() {
  return !1;
}
var se = typeof exports == "object" && exports && !exports.nodeType && exports, Ft = se && typeof module == "object" && module && !module.nodeType && module, br = Ft && Ft.exports === se, It = br ? O.Buffer : void 0, mr = It ? It.isBuffer : void 0, ht = mr || vr, Ar = "[object Arguments]", wr = "[object Array]", Tr = "[object Boolean]", Or = "[object Date]", $r = "[object Error]", Pr = "[object Function]", Sr = "[object Map]", Cr = "[object Number]", xr = "[object Object]", Er = "[object RegExp]", Rr = "[object Set]", Dr = "[object String]", jr = "[object WeakMap]", Fr = "[object ArrayBuffer]", Ir = "[object DataView]", Mr = "[object Float32Array]", Lr = "[object Float64Array]", Nr = "[object Int8Array]", zr = "[object Int16Array]", Gr = "[object Int32Array]", Br = "[object Uint8Array]", Hr = "[object Uint8ClampedArray]", Ur = "[object Uint16Array]", Kr = "[object Uint32Array]", _ = {};
_[Mr] = _[Lr] = _[Nr] = _[zr] = _[Gr] = _[Br] = _[Hr] = _[Ur] = _[Kr] = !0;
_[Ar] = _[wr] = _[Fr] = _[Tr] = _[Ir] = _[Or] = _[$r] = _[Pr] = _[Sr] = _[Cr] = _[xr] = _[Er] = _[Rr] = _[Dr] = _[jr] = !1;
function Wr(t) {
  return N(t) && bt(t.length) && !!_[H(t)];
}
function ue(t) {
  return function(e) {
    return t(e);
  };
}
var fe = typeof exports == "object" && exports && !exports.nodeType && exports, W = fe && typeof module == "object" && module && !module.nodeType && module, qr = W && W.exports === fe, pt = qr && Qt.process, Mt = function() {
  try {
    var t = W && W.require && W.require("util").types;
    return t || pt && pt.binding && pt.binding("util");
  } catch {
  }
}(), Lt = Mt && Mt.isTypedArray, le = Lt ? ue(Lt) : Wr, Vr = Object.prototype, Xr = Vr.hasOwnProperty;
function Zr(t, e) {
  var r = A(t), n = !r && oe(t), a = !r && !n && ht(t), i = !r && !n && !a && le(t), o = r || n || a || i, u = o ? dr(t.length, String) : [], s = u.length;
  for (var f in t)
    Xr.call(t, f) && !(o && // Safari 9 has enumerable `arguments.length` in strict mode.
    (f == "length" || // Node.js 0.10 has enumerable non-index properties on buffers.
    a && (f == "offset" || f == "parent") || // PhantomJS 2 has enumerable non-index properties on typed arrays.
    i && (f == "buffer" || f == "byteLength" || f == "byteOffset") || // Skip index properties.
    ne(f, s))) && u.push(f);
  return u;
}
function Yr(t, e) {
  return function(r) {
    return t(e(r));
  };
}
var Jr = Yr(Object.keys, Object), Qr = Object.prototype, kr = Qr.hasOwnProperty;
function tn(t) {
  if (!gr(t))
    return Jr(t);
  var e = [];
  for (var r in Object(t))
    kr.call(t, r) && r != "constructor" && e.push(r);
  return e;
}
function At(t) {
  return mt(t) ? Zr(t) : tn(t);
}
var en = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, rn = /^\w*$/;
function wt(t, e) {
  if (A(t))
    return !1;
  var r = typeof t;
  return r == "number" || r == "symbol" || r == "boolean" || t == null || q(t) ? !0 : rn.test(t) || !en.test(t) || e != null && t in Object(e);
}
var V = U(Object, "create");
function nn() {
  this.__data__ = V ? V(null) : {}, this.size = 0;
}
function an(t) {
  var e = this.has(t) && delete this.__data__[t];
  return this.size -= e ? 1 : 0, e;
}
var on = "__lodash_hash_undefined__", sn = Object.prototype, un = sn.hasOwnProperty;
function fn(t) {
  var e = this.__data__;
  if (V) {
    var r = e[t];
    return r === on ? void 0 : r;
  }
  return un.call(e, t) ? e[t] : void 0;
}
var ln = Object.prototype, cn = ln.hasOwnProperty;
function pn(t) {
  var e = this.__data__;
  return V ? e[t] !== void 0 : cn.call(e, t);
}
var gn = "__lodash_hash_undefined__";
function dn(t, e) {
  var r = this.__data__;
  return this.size += this.has(t) ? 0 : 1, r[t] = V && e === void 0 ? gn : e, this;
}
function D(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.clear(); ++e < r; ) {
    var n = t[e];
    this.set(n[0], n[1]);
  }
}
D.prototype.clear = nn;
D.prototype.delete = an;
D.prototype.get = fn;
D.prototype.has = pn;
D.prototype.set = dn;
function hn() {
  this.__data__ = [], this.size = 0;
}
function at(t, e) {
  for (var r = t.length; r--; )
    if (ie(t[r][0], e))
      return r;
  return -1;
}
var _n = Array.prototype, yn = _n.splice;
function vn(t) {
  var e = this.__data__, r = at(e, t);
  if (r < 0)
    return !1;
  var n = e.length - 1;
  return r == n ? e.pop() : yn.call(e, r, 1), --this.size, !0;
}
function bn(t) {
  var e = this.__data__, r = at(e, t);
  return r < 0 ? void 0 : e[r][1];
}
function mn(t) {
  return at(this.__data__, t) > -1;
}
function An(t, e) {
  var r = this.__data__, n = at(r, t);
  return n < 0 ? (++this.size, r.push([t, e])) : r[n][1] = e, this;
}
function $(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.clear(); ++e < r; ) {
    var n = t[e];
    this.set(n[0], n[1]);
  }
}
$.prototype.clear = hn;
$.prototype.delete = vn;
$.prototype.get = bn;
$.prototype.has = mn;
$.prototype.set = An;
var X = U(O, "Map");
function wn() {
  this.size = 0, this.__data__ = {
    hash: new D(),
    map: new (X || $)(),
    string: new D()
  };
}
function Tn(t) {
  var e = typeof t;
  return e == "string" || e == "number" || e == "symbol" || e == "boolean" ? t !== "__proto__" : t === null;
}
function ot(t, e) {
  var r = t.__data__;
  return Tn(e) ? r[typeof e == "string" ? "string" : "hash"] : r.map;
}
function On(t) {
  var e = ot(this, t).delete(t);
  return this.size -= e ? 1 : 0, e;
}
function $n(t) {
  return ot(this, t).get(t);
}
function Pn(t) {
  return ot(this, t).has(t);
}
function Sn(t, e) {
  var r = ot(this, t), n = r.size;
  return r.set(t, e), this.size += r.size == n ? 0 : 1, this;
}
function P(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.clear(); ++e < r; ) {
    var n = t[e];
    this.set(n[0], n[1]);
  }
}
P.prototype.clear = wn;
P.prototype.delete = On;
P.prototype.get = $n;
P.prototype.has = Pn;
P.prototype.set = Sn;
var Cn = "Expected a function";
function Tt(t, e) {
  if (typeof t != "function" || e != null && typeof e != "function")
    throw new TypeError(Cn);
  var r = function() {
    var n = arguments, a = e ? e.apply(this, n) : n[0], i = r.cache;
    if (i.has(a))
      return i.get(a);
    var o = t.apply(this, n);
    return r.cache = i.set(a, o) || i, o;
  };
  return r.cache = new (Tt.Cache || P)(), r;
}
Tt.Cache = P;
var xn = 500;
function En(t) {
  var e = Tt(t, function(n) {
    return r.size === xn && r.clear(), n;
  }), r = e.cache;
  return e;
}
var Rn = /[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g, Dn = /\\(\\)?/g, jn = En(function(t) {
  var e = [];
  return t.charCodeAt(0) === 46 && e.push(""), t.replace(Rn, function(r, n, a, i) {
    e.push(a ? i.replace(Dn, "$1") : n || r);
  }), e;
});
function Fn(t) {
  return t == null ? "" : te(t);
}
function ce(t, e) {
  return A(t) ? t : wt(t, e) ? [t] : jn(Fn(t));
}
function st(t) {
  if (typeof t == "string" || q(t))
    return t;
  var e = t + "";
  return e == "0" && 1 / t == -1 / 0 ? "-0" : e;
}
function Ot(t, e) {
  e = ce(e, t);
  for (var r = 0, n = e.length; t != null && r < n; )
    t = t[st(e[r++])];
  return r && r == n ? t : void 0;
}
function In(t, e, r) {
  var n = t == null ? void 0 : Ot(t, e);
  return n === void 0 ? r : n;
}
function Mn(t, e) {
  for (var r = -1, n = e.length, a = t.length; ++r < n; )
    t[a + r] = e[r];
  return t;
}
function Ln() {
  this.__data__ = new $(), this.size = 0;
}
function Nn(t) {
  var e = this.__data__, r = e.delete(t);
  return this.size = e.size, r;
}
function zn(t) {
  return this.__data__.get(t);
}
function Gn(t) {
  return this.__data__.has(t);
}
var Bn = 200;
function Hn(t, e) {
  var r = this.__data__;
  if (r instanceof $) {
    var n = r.__data__;
    if (!X || n.length < Bn - 1)
      return n.push([t, e]), this.size = ++r.size, this;
    r = this.__data__ = new P(n);
  }
  return r.set(t, e), this.size = r.size, this;
}
function T(t) {
  var e = this.__data__ = new $(t);
  this.size = e.size;
}
T.prototype.clear = Ln;
T.prototype.delete = Nn;
T.prototype.get = zn;
T.prototype.has = Gn;
T.prototype.set = Hn;
function Un(t, e) {
  for (var r = -1, n = t == null ? 0 : t.length, a = 0, i = []; ++r < n; ) {
    var o = t[r];
    e(o, r, t) && (i[a++] = o);
  }
  return i;
}
function Kn() {
  return [];
}
var Wn = Object.prototype, qn = Wn.propertyIsEnumerable, Nt = Object.getOwnPropertySymbols, Vn = Nt ? function(t) {
  return t == null ? [] : (t = Object(t), Un(Nt(t), function(e) {
    return qn.call(t, e);
  }));
} : Kn;
function Xn(t, e, r) {
  var n = e(t);
  return A(t) ? n : Mn(n, r(t));
}
function zt(t) {
  return Xn(t, At, Vn);
}
var _t = U(O, "DataView"), yt = U(O, "Promise"), M = U(O, "Set"), Gt = "[object Map]", Zn = "[object Object]", Bt = "[object Promise]", Ht = "[object Set]", Ut = "[object WeakMap]", Kt = "[object DataView]", Yn = j(_t), Jn = j(X), Qn = j(yt), kn = j(M), ti = j(dt), S = H;
(_t && S(new _t(new ArrayBuffer(1))) != Kt || X && S(new X()) != Gt || yt && S(yt.resolve()) != Bt || M && S(new M()) != Ht || dt && S(new dt()) != Ut) && (S = function(t) {
  var e = H(t), r = e == Zn ? t.constructor : void 0, n = r ? j(r) : "";
  if (n)
    switch (n) {
      case Yn:
        return Kt;
      case Jn:
        return Gt;
      case Qn:
        return Bt;
      case kn:
        return Ht;
      case ti:
        return Ut;
    }
  return e;
});
var Wt = O.Uint8Array, ei = "__lodash_hash_undefined__";
function ri(t) {
  return this.__data__.set(t, ei), this;
}
function ni(t) {
  return this.__data__.has(t);
}
function Z(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.__data__ = new P(); ++e < r; )
    this.add(t[e]);
}
Z.prototype.add = Z.prototype.push = ri;
Z.prototype.has = ni;
function ii(t, e) {
  for (var r = -1, n = t == null ? 0 : t.length; ++r < n; )
    if (e(t[r], r, t))
      return !0;
  return !1;
}
function pe(t, e) {
  return t.has(e);
}
var ai = 1, oi = 2;
function ge(t, e, r, n, a, i) {
  var o = r & ai, u = t.length, s = e.length;
  if (u != s && !(o && s > u))
    return !1;
  var f = i.get(t), c = i.get(e);
  if (f && c)
    return f == e && c == t;
  var p = -1, l = !0, y = r & oi ? new Z() : void 0;
  for (i.set(t, e), i.set(e, t); ++p < u; ) {
    var h = t[p], v = e[p];
    if (n)
      var d = o ? n(v, h, p, e, t, i) : n(h, v, p, t, e, i);
    if (d !== void 0) {
      if (d)
        continue;
      l = !1;
      break;
    }
    if (y) {
      if (!ii(e, function(b, m) {
        if (!pe(y, m) && (h === b || a(h, b, r, n, i)))
          return y.push(m);
      })) {
        l = !1;
        break;
      }
    } else if (!(h === v || a(h, v, r, n, i))) {
      l = !1;
      break;
    }
  }
  return i.delete(t), i.delete(e), l;
}
function si(t) {
  var e = -1, r = Array(t.size);
  return t.forEach(function(n, a) {
    r[++e] = [a, n];
  }), r;
}
function $t(t) {
  var e = -1, r = Array(t.size);
  return t.forEach(function(n) {
    r[++e] = n;
  }), r;
}
var ui = 1, fi = 2, li = "[object Boolean]", ci = "[object Date]", pi = "[object Error]", gi = "[object Map]", di = "[object Number]", hi = "[object RegExp]", _i = "[object Set]", yi = "[object String]", vi = "[object Symbol]", bi = "[object ArrayBuffer]", mi = "[object DataView]", qt = x ? x.prototype : void 0, gt = qt ? qt.valueOf : void 0;
function Ai(t, e, r, n, a, i, o) {
  switch (r) {
    case mi:
      if (t.byteLength != e.byteLength || t.byteOffset != e.byteOffset)
        return !1;
      t = t.buffer, e = e.buffer;
    case bi:
      return !(t.byteLength != e.byteLength || !i(new Wt(t), new Wt(e)));
    case li:
    case ci:
    case di:
      return ie(+t, +e);
    case pi:
      return t.name == e.name && t.message == e.message;
    case hi:
    case yi:
      return t == e + "";
    case gi:
      var u = si;
    case _i:
      var s = n & ui;
      if (u || (u = $t), t.size != e.size && !s)
        return !1;
      var f = o.get(t);
      if (f)
        return f == e;
      n |= fi, o.set(t, e);
      var c = ge(u(t), u(e), n, a, i, o);
      return o.delete(t), c;
    case vi:
      if (gt)
        return gt.call(t) == gt.call(e);
  }
  return !1;
}
var wi = 1, Ti = Object.prototype, Oi = Ti.hasOwnProperty;
function $i(t, e, r, n, a, i) {
  var o = r & wi, u = zt(t), s = u.length, f = zt(e), c = f.length;
  if (s != c && !o)
    return !1;
  for (var p = s; p--; ) {
    var l = u[p];
    if (!(o ? l in e : Oi.call(e, l)))
      return !1;
  }
  var y = i.get(t), h = i.get(e);
  if (y && h)
    return y == e && h == t;
  var v = !0;
  i.set(t, e), i.set(e, t);
  for (var d = o; ++p < s; ) {
    l = u[p];
    var b = t[l], m = e[l];
    if (n)
      var E = o ? n(m, b, l, e, t, i) : n(b, m, l, t, e, i);
    if (!(E === void 0 ? b === m || a(b, m, r, n, i) : E)) {
      v = !1;
      break;
    }
    d || (d = l == "constructor");
  }
  if (v && !d) {
    var F = t.constructor, I = e.constructor;
    F != I && "constructor" in t && "constructor" in e && !(typeof F == "function" && F instanceof F && typeof I == "function" && I instanceof I) && (v = !1);
  }
  return i.delete(t), i.delete(e), v;
}
var Pi = 1, Vt = "[object Arguments]", Xt = "[object Array]", nt = "[object Object]", Si = Object.prototype, Zt = Si.hasOwnProperty;
function Ci(t, e, r, n, a, i) {
  var o = A(t), u = A(e), s = o ? Xt : S(t), f = u ? Xt : S(e);
  s = s == Vt ? nt : s, f = f == Vt ? nt : f;
  var c = s == nt, p = f == nt, l = s == f;
  if (l && ht(t)) {
    if (!ht(e))
      return !1;
    o = !0, c = !1;
  }
  if (l && !c)
    return i || (i = new T()), o || le(t) ? ge(t, e, r, n, a, i) : Ai(t, e, s, r, n, a, i);
  if (!(r & Pi)) {
    var y = c && Zt.call(t, "__wrapped__"), h = p && Zt.call(e, "__wrapped__");
    if (y || h) {
      var v = y ? t.value() : t, d = h ? e.value() : e;
      return i || (i = new T()), a(v, d, r, n, i);
    }
  }
  return l ? (i || (i = new T()), $i(t, e, r, n, a, i)) : !1;
}
function Pt(t, e, r, n, a) {
  return t === e ? !0 : t == null || e == null || !N(t) && !N(e) ? t !== t && e !== e : Ci(t, e, r, n, Pt, a);
}
var xi = 1, Ei = 2;
function Ri(t, e, r, n) {
  var a = r.length, i = a;
  if (t == null)
    return !i;
  for (t = Object(t); a--; ) {
    var o = r[a];
    if (o[2] ? o[1] !== t[o[0]] : !(o[0] in t))
      return !1;
  }
  for (; ++a < i; ) {
    o = r[a];
    var u = o[0], s = t[u], f = o[1];
    if (o[2]) {
      if (s === void 0 && !(u in t))
        return !1;
    } else {
      var c = new T(), p;
      if (!(p === void 0 ? Pt(f, s, xi | Ei, n, c) : p))
        return !1;
    }
  }
  return !0;
}
function de(t) {
  return t === t && !vt(t);
}
function Di(t) {
  for (var e = At(t), r = e.length; r--; ) {
    var n = e[r], a = t[n];
    e[r] = [n, a, de(a)];
  }
  return e;
}
function he(t, e) {
  return function(r) {
    return r == null ? !1 : r[t] === e && (e !== void 0 || t in Object(r));
  };
}
function ji(t) {
  var e = Di(t);
  return e.length == 1 && e[0][2] ? he(e[0][0], e[0][1]) : function(r) {
    return r === t || Ri(r, t, e);
  };
}
function Fi(t, e) {
  return t != null && e in Object(t);
}
function Ii(t, e, r) {
  e = ce(e, t);
  for (var n = -1, a = e.length, i = !1; ++n < a; ) {
    var o = st(e[n]);
    if (!(i = t != null && r(t, o)))
      break;
    t = t[o];
  }
  return i || ++n != a ? i : (a = t == null ? 0 : t.length, !!a && bt(a) && ne(o, a) && (A(t) || oe(t)));
}
function Mi(t, e) {
  return t != null && Ii(t, e, Fi);
}
var Li = 1, Ni = 2;
function zi(t, e) {
  return wt(t) && de(e) ? he(st(t), e) : function(r) {
    var n = In(r, t);
    return n === void 0 && n === e ? Mi(r, t) : Pt(e, n, Li | Ni);
  };
}
function Gi(t) {
  return function(e) {
    return e?.[t];
  };
}
function Bi(t) {
  return function(e) {
    return Ot(e, t);
  };
}
function Hi(t) {
  return wt(t) ? Gi(st(t)) : Bi(t);
}
function _e(t) {
  return typeof t == "function" ? t : t == null ? ee : typeof t == "object" ? A(t) ? zi(t[0], t[1]) : ji(t) : Hi(t);
}
function Ui(t) {
  return function(e, r, n) {
    for (var a = -1, i = Object(e), o = n(e), u = o.length; u--; ) {
      var s = o[++a];
      if (r(i[s], s, i) === !1)
        break;
    }
    return e;
  };
}
var Ki = Ui();
function Wi(t, e) {
  return t && Ki(t, e, At);
}
function qi(t, e) {
  return function(r, n) {
    if (r == null)
      return r;
    if (!mt(r))
      return t(r, n);
    for (var a = r.length, i = -1, o = Object(r); ++i < a && n(o[i], i, o) !== !1; )
      ;
    return r;
  };
}
var Vi = qi(Wi);
function Xi(t, e) {
  var r = -1, n = mt(t) ? Array(t.length) : [];
  return Vi(t, function(a, i, o) {
    n[++r] = e(a, i, o);
  }), n;
}
function Zi(t, e) {
  var r = t.length;
  for (t.sort(e); r--; )
    t[r] = t[r].value;
  return t;
}
function Yi(t, e) {
  if (t !== e) {
    var r = t !== void 0, n = t === null, a = t === t, i = q(t), o = e !== void 0, u = e === null, s = e === e, f = q(e);
    if (!u && !f && !i && t > e || i && o && s && !u && !f || n && o && s || !r && s || !a)
      return 1;
    if (!n && !i && !f && t < e || f && r && a && !n && !i || u && r && a || !o && a || !s)
      return -1;
  }
  return 0;
}
function Ji(t, e, r) {
  for (var n = -1, a = t.criteria, i = e.criteria, o = a.length, u = r.length; ++n < o; ) {
    var s = Yi(a[n], i[n]);
    if (s) {
      if (n >= u)
        return s;
      var f = r[n];
      return s * (f == "desc" ? -1 : 1);
    }
  }
  return t.index - e.index;
}
function Qi(t, e, r) {
  e.length ? e = it(e, function(i) {
    return A(i) ? function(o) {
      return Ot(o, i.length === 1 ? i[0] : i);
    } : i;
  }) : e = [ee];
  var n = -1;
  e = it(e, ue(_e));
  var a = Xi(t, function(i, o, u) {
    var s = it(e, function(f) {
      return f(i);
    });
    return { criteria: s, index: ++n, value: i };
  });
  return Zi(a, function(i, o) {
    return Ji(i, o, r);
  });
}
function ki(t, e, r, n) {
  return t == null ? [] : (A(e) || (e = e == null ? [] : [e]), r = r, A(r) || (r = r == null ? [] : [r]), Qi(t, e, r));
}
var ta = 1 / 0, ea = M && 1 / $t(new M([, -0]))[1] == ta ? function(t) {
  return new M(t);
} : nr, ra = 200;
function na(t, e, r) {
  var n = -1, a = ur, i = t.length, o = !0, u = [], s = u;
  if (i >= ra) {
    var f = e ? null : ea(t);
    if (f)
      return $t(f);
    o = !1, a = pe, s = new Z();
  } else
    s = e ? [] : u;
  t:
    for (; ++n < i; ) {
      var c = t[n], p = e ? e(c) : c;
      if (c = c !== 0 ? c : 0, o && p === p) {
        for (var l = s.length; l--; )
          if (s[l] === p)
            continue t;
        e && s.push(p), u.push(c);
      } else a(s, p, r) || (s !== u && s.push(p), u.push(c));
    }
  return u;
}
function Yt(t, e) {
  return t && t.length ? na(t, _e(e)) : [];
}
function ia(t) {
  const { attrs: e, columns: r, registerRowsHandler: n } = t;
  let a = Jt(e.sort);
  const i = w(() => r.value?.some((s) => s.sorter)), o = w(
    () => r.value.filter((s) => s.sorter).length > 1
  );
  return n((s) => {
    if (!a.value)
      return s;
    const f = Array.isArray(a.value) ? a.value : [a.value], c = f.map((l) => l.sortBy), p = f.map(
      (l) => l.descending ? "desc" : "asc"
    );
    return ki(s, c, p);
  }), {
    onSortChange: (s) => {
      i.value && (a.value = s);
    },
    multipleSort: o,
    sort: a
  };
}
function aa(t) {
  return new Function("return " + t)();
}
function oa(t) {
  const { tableData: e, registerColumnsHandler: r, registerRowsHandler: n, columns: a } = t;
  r(
    (c) => c.map(
      (p) => sa(
        p,
        e,
        t.tdesignGlobalConfig
      )
    )
  );
  const i = Jt(), o = new Map(a.value.map((c) => [c.colKey, c]));
  n((c) => {
    if (!i.value)
      return c;
    const p = Object.keys(i.value).map((l) => {
      const y = i.value[l], h = o.get(l).filter, v = h.type, d = h.predicate ? aa(h.predicate) : void 0, b = v ?? h._type;
      return {
        key: l,
        value: y,
        type: b,
        predicate: d
      };
    });
    return c.filter((l) => p.every((y) => {
      const h = y.type, v = y.predicate;
      if (h === "multiple") {
        const d = y.value;
        return d.length === 0 ? !0 : v ? v(i, l) : d.includes(l[y.key]);
      }
      if (h === "single") {
        const d = y.value;
        return d ? v ? v(d, l) : l[y.key] === d : !0;
      }
      if (h === "input") {
        const d = y.value;
        return d ? v ? v(d, l) : l[y.key].toString().includes(d) : !0;
      }
      if (h === "date") {
        const d = y.value;
        if (!d || d === "") return !0;
        const [b, m] = d, E = new Date(l[y.key]);
        return v ? v(d, l) : new Date(b) <= E && E <= new Date(m);
      }
      throw new Error(`not support filter type ${h}`);
    }));
  });
  const u = (c, p) => {
    if (!p.col) {
      i.value = void 0;
      return;
    }
    i.value = {
      ...c
    };
  };
  function s() {
    i.value = void 0;
  }
  function f() {
    return i.value ? Object.keys(i.value).map((c) => {
      const p = o.get(c).label, l = i.value[c];
      return l.length === 0 ? "" : `${p}: ${JSON.stringify(l)}`;
    }).join("; ") : null;
  }
  return {
    onFilterChange: u,
    filterValue: i,
    resetFilters: s,
    filterResultText: f
  };
}
function sa(t, e, r) {
  if (!("filter" in t))
    return t;
  if (!("type" in t.filter)) throw new Error("filter type is required");
  const { colKey: a } = t, i = t.filter.type;
  if (i === "multiple") {
    const o = Yt(e.value, a).map((s) => ({
      label: s[a],
      value: s[a]
    })), u = {
      resetValue: [],
      list: [
        { label: r.selectAllText, checkAll: !0 },
        ...o
      ],
      ...t.filter
    };
    return {
      ...t,
      filter: u
    };
  }
  if (i === "single") {
    const u = {
      resetValue: null,
      list: Yt(e.value, a).map((s) => ({
        label: s[a],
        value: s[a]
      })),
      showConfirmAndReset: !0,
      ...t.filter
    };
    return {
      ...t,
      filter: u
    };
  }
  if (i === "input") {
    const o = {
      resetValue: "",
      confirmEvents: ["onEnter"],
      showConfirmAndReset: !0,
      ...t.filter,
      props: {
        ...t.filter?.props
      }
    };
    return {
      ...t,
      filter: o
    };
  }
  if (i === "date") {
    const o = {
      resetValue: "",
      showConfirmAndReset: !0,
      props: {
        firstDayOfWeek: 7,
        ...t.filter?.props
      },
      style: {
        fontSize: "14px"
      },
      classNames: "custom-class-name",
      attrs: {
        "data-type": "date-range-picker"
      },
      ...t.filter,
      component: me,
      _type: "date"
    };
    return delete o.type, {
      ...t,
      filter: o
    };
  }
  throw new Error(`not support filter type ${i}`);
}
const ua = {
  hover: !0,
  bordered: !0,
  tableLayout: "auto",
  showSortColumnBgColor: !0
};
function fa(t) {
  const { attrs: e } = t;
  return w(() => ({
    ...ua,
    ...e
  }));
}
function la(t, e) {
  return w(() => {
    const r = Object.keys(t).filter(
      (n) => n.startsWith("header-cell-")
    );
    return e.value.filter((n) => !r.includes(n.title)).map((n) => ({
      slotName: `header-cell-${n.name}`,
      content: n.label ?? n.colKey
    }));
  });
}
function ca(t) {
  const e = new Set(t.value.map((r) => r.cell));
  return (r, n) => e.has(r) ? { ...n, currentValue: n.row[n.col.colKey] } : n;
}
const pa = /* @__PURE__ */ z({
  inheritAttrs: !1,
  __name: "Table",
  setup(t) {
    const e = Y(), { t: r, globalConfig: n } = Ae("table"), { tableData: a, orgData: i, registerRowsHandler: o } = Pe(e), [u, s] = Se({
      tableData: a,
      attrs: e
    }), f = Ee({ tableData: a, attrs: e }), { sort: c, onSortChange: p, multipleSort: l } = ia({
      registerRowsHandler: o,
      attrs: e,
      columns: u
    }), { onFilterChange: y, filterValue: h, resetFilters: v, filterResultText: d } = oa({
      tableData: i,
      registerRowsHandler: o,
      registerColumnsHandler: s,
      columns: u,
      tdesignGlobalConfig: n.value
    }), b = fa({ attrs: e }), m = J(), E = la(m, u), F = ca(u);
    return (I, ba) => (B(), G(R.Table, Q(g(b), {
      pagination: g(f),
      sort: g(c),
      data: g(a),
      columns: g(u),
      "filter-value": g(h),
      onSortChange: g(p),
      onFilterChange: g(y),
      "multiple-sort": g(l)
    }), k({
      "filter-row": C(() => [
        St("div", null, [
          St("span", null, lt(g(r)(g(n).searchResultText, {
            result: g(d)(),
            count: g(a).length
          })), 1),
          ve(R.Button, {
            theme: "primary",
            variant: "text",
            onClick: g(v)
          }, {
            default: C(() => [
              Ct(lt(g(n).clearFilterResultButtonText), 1)
            ]),
            _: 1
          }, 8, ["onClick"])
        ])
      ]),
      _: 2
    }, [
      L(g(E), (ut) => ({
        name: ut.slotName,
        fn: C(() => [
          Ct(lt(ut.content), 1)
        ])
      })),
      L(g(m), (ut, ft) => ({
        name: ft,
        fn: C((ye) => [
          tt(I.$slots, ft, et(rt(g(F)(ft, ye))))
        ])
      }))
    ]), 1040, ["pagination", "sort", "data", "columns", "filter-value", "onSortChange", "onFilterChange", "multiple-sort"]));
  }
});
function ga(t) {
  const { affixProps: e = {} } = t;
  return {
    container: ".insta-main",
    ...e
  };
}
function da(t) {
  const { container: e = ".insta-main" } = t;
  return e;
}
const ha = /* @__PURE__ */ z({
  inheritAttrs: !1,
  __name: "Anchor",
  setup(t) {
    const e = Y(), r = J(), n = ga(e), a = da(e);
    return (i, o) => (B(), G(R.Anchor, Q(g(e), {
      container: g(a),
      "affix-props": g(n)
    }), k({ _: 2 }, [
      L(g(r), (u, s) => ({
        name: s,
        fn: C((f) => [
          tt(i.$slots, s, et(rt(f)))
        ])
      }))
    ]), 1040, ["container", "affix-props"]));
  }
}), _a = /* @__PURE__ */ z({
  __name: "Icon",
  props: {
    name: {},
    size: {},
    color: {},
    prefix: {}
  },
  setup(t) {
    const e = t, r = w(() => {
      const [n, a] = e.name.split(":");
      return a ? e.name : `${e.prefix || "tdesign"}:${e.name}`;
    });
    return (n, a) => (B(), G(be("icon"), {
      class: "t-icon",
      icon: r.value,
      size: n.size,
      color: n.color
    }, null, 8, ["icon", "size", "color"]));
  }
}), ya = /* @__PURE__ */ z({
  inheritAttrs: !1,
  __name: "Select",
  props: {
    options: {}
  },
  setup(t) {
    const e = t, r = Y(), n = J(), a = w(() => {
      const i = e.options;
      if (i) {
        if (Array.isArray(i))
          return i.length === 0 ? void 0 : i.map(
            (o) => typeof o == "string" || typeof o == "number" ? { label: o, value: o } : o
          );
        throw new Error("options must be an array");
      }
    });
    return (i, o) => (B(), G(R.Select, Q(g(r), { options: a.value }), k({ _: 2 }, [
      L(g(n), (u, s) => ({
        name: s,
        fn: C((f) => [
          tt(i.$slots, s, et(rt(f)))
        ])
      }))
    ]), 1040, ["options"]));
  }
}), va = /* @__PURE__ */ z({
  inheritAttrs: !1,
  __name: "RadioGroup",
  props: {
    options: {}
  },
  setup(t) {
    const e = t, r = Y(), n = J(), a = w(() => {
      const i = e.options;
      if (i) {
        if (Array.isArray(i))
          return i.length === 0 ? void 0 : i.map(
            (o) => typeof o == "string" || typeof o == "number" ? { label: o, value: o } : o
          );
        throw new Error("options must be an array");
      }
    });
    return (i, o) => (B(), G(R.RadioGroup, Q(g(r), { options: a.value }), k({ _: 2 }, [
      L(g(n), (u, s) => ({
        name: s,
        fn: C((f) => [
          tt(i.$slots, s, et(rt(f)))
        ])
      }))
    ]), 1040, ["options"]));
  }
});
function wa(t) {
  t.use(R), t.component("t-table", pa), t.component("t-affix", $e), t.component("t-anchor", ha), t.component("t-icon", _a), t.component("t-select", ya), t.component("t-radio-group", va), window.$tdesign = {
    NotifyPlugin: Te,
    MessagePlugin: we
  };
}
export {
  wa as install
};
