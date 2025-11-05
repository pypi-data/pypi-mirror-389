import { i as ae, a as A, r as ue, Z as P, g as de, b as fe } from "./Index-DkXuxfhv.js";
const x = window.ms_globals.React, oe = window.ms_globals.React.forwardRef, se = window.ms_globals.React.useRef, le = window.ms_globals.React.useState, ie = window.ms_globals.React.useEffect, ce = window.ms_globals.React.useMemo, W = window.ms_globals.ReactDOM.createPortal, me = window.ms_globals.internalContext.useContextPropsContext, _e = window.ms_globals.internalContext.ContextPropsProvider, he = window.ms_globals.antd.Drawer;
var ge = /\s/;
function pe(e) {
  for (var t = e.length; t-- && ge.test(e.charAt(t)); )
    ;
  return t;
}
var we = /^\s+/;
function be(e) {
  return e && e.slice(0, pe(e) + 1).replace(we, "");
}
var z = NaN, xe = /^[-+]0x[0-9a-f]+$/i, ye = /^0b[01]+$/i, Ce = /^0o[0-7]+$/i, Ee = parseInt;
function B(e) {
  if (typeof e == "number")
    return e;
  if (ae(e))
    return z;
  if (A(e)) {
    var t = typeof e.valueOf == "function" ? e.valueOf() : e;
    e = A(t) ? t + "" : t;
  }
  if (typeof e != "string")
    return e === 0 ? e : +e;
  e = be(e);
  var r = ye.test(e);
  return r || Ce.test(e) ? Ee(e.slice(2), r ? 2 : 8) : xe.test(e) ? z : +e;
}
var L = function() {
  return ue.Date.now();
}, ve = "Expected a function", Ie = Math.max, Se = Math.min;
function Re(e, t, r) {
  var l, s, n, o, i, u, _ = 0, p = !1, c = !1, w = !0;
  if (typeof e != "function")
    throw new TypeError(ve);
  t = B(t) || 0, A(r) && (p = !!r.leading, c = "maxWait" in r, n = c ? Ie(B(r.maxWait) || 0, t) : n, w = "trailing" in r ? !!r.trailing : w);
  function m(d) {
    var y = l, O = s;
    return l = s = void 0, _ = d, o = e.apply(O, y), o;
  }
  function C(d) {
    return _ = d, i = setTimeout(h, t), p ? m(d) : o;
  }
  function v(d) {
    var y = d - u, O = d - _, U = t - y;
    return c ? Se(U, n - O) : U;
  }
  function f(d) {
    var y = d - u, O = d - _;
    return u === void 0 || y >= t || y < 0 || c && O >= n;
  }
  function h() {
    var d = L();
    if (f(d))
      return b(d);
    i = setTimeout(h, v(d));
  }
  function b(d) {
    return i = void 0, w && l ? m(d) : (l = s = void 0, o);
  }
  function R() {
    i !== void 0 && clearTimeout(i), _ = 0, l = u = s = i = void 0;
  }
  function a() {
    return i === void 0 ? o : b(L());
  }
  function I() {
    var d = L(), y = f(d);
    if (l = arguments, s = this, u = d, y) {
      if (i === void 0)
        return C(u);
      if (c)
        return clearTimeout(i), i = setTimeout(h, t), m(u);
    }
    return i === void 0 && (i = setTimeout(h, t)), o;
  }
  return I.cancel = R, I.flush = a, I;
}
var Q = {
  exports: {}
}, j = {};
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Oe = x, Pe = Symbol.for("react.element"), Te = Symbol.for("react.fragment"), ke = Object.prototype.hasOwnProperty, je = Oe.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, Le = {
  key: !0,
  ref: !0,
  __self: !0,
  __source: !0
};
function $(e, t, r) {
  var l, s = {}, n = null, o = null;
  r !== void 0 && (n = "" + r), t.key !== void 0 && (n = "" + t.key), t.ref !== void 0 && (o = t.ref);
  for (l in t) ke.call(t, l) && !Le.hasOwnProperty(l) && (s[l] = t[l]);
  if (e && e.defaultProps) for (l in t = e.defaultProps, t) s[l] === void 0 && (s[l] = t[l]);
  return {
    $$typeof: Pe,
    type: e,
    key: n,
    ref: o,
    props: s,
    _owner: je.current
  };
}
j.Fragment = Te;
j.jsx = $;
j.jsxs = $;
Q.exports = j;
var g = Q.exports;
const {
  SvelteComponent: Fe,
  assign: G,
  binding_callbacks: H,
  check_outros: Ne,
  children: ee,
  claim_element: te,
  claim_space: We,
  component_subscribe: K,
  compute_slots: Ae,
  create_slot: De,
  detach: S,
  element: ne,
  empty: q,
  exclude_internal_props: V,
  get_all_dirty_from_scope: Me,
  get_slot_changes: Ue,
  group_outros: ze,
  init: Be,
  insert_hydration: T,
  safe_not_equal: Ge,
  set_custom_element_data: re,
  space: He,
  transition_in: k,
  transition_out: D,
  update_slot_base: Ke
} = window.__gradio__svelte__internal, {
  beforeUpdate: qe,
  getContext: Ve,
  onDestroy: Je,
  setContext: Xe
} = window.__gradio__svelte__internal;
function J(e) {
  let t, r;
  const l = (
    /*#slots*/
    e[7].default
  ), s = De(
    l,
    e,
    /*$$scope*/
    e[6],
    null
  );
  return {
    c() {
      t = ne("svelte-slot"), s && s.c(), this.h();
    },
    l(n) {
      t = te(n, "SVELTE-SLOT", {
        class: !0
      });
      var o = ee(t);
      s && s.l(o), o.forEach(S), this.h();
    },
    h() {
      re(t, "class", "svelte-1rt0kpf");
    },
    m(n, o) {
      T(n, t, o), s && s.m(t, null), e[9](t), r = !0;
    },
    p(n, o) {
      s && s.p && (!r || o & /*$$scope*/
      64) && Ke(
        s,
        l,
        n,
        /*$$scope*/
        n[6],
        r ? Ue(
          l,
          /*$$scope*/
          n[6],
          o,
          null
        ) : Me(
          /*$$scope*/
          n[6]
        ),
        null
      );
    },
    i(n) {
      r || (k(s, n), r = !0);
    },
    o(n) {
      D(s, n), r = !1;
    },
    d(n) {
      n && S(t), s && s.d(n), e[9](null);
    }
  };
}
function Ye(e) {
  let t, r, l, s, n = (
    /*$$slots*/
    e[4].default && J(e)
  );
  return {
    c() {
      t = ne("react-portal-target"), r = He(), n && n.c(), l = q(), this.h();
    },
    l(o) {
      t = te(o, "REACT-PORTAL-TARGET", {
        class: !0
      }), ee(t).forEach(S), r = We(o), n && n.l(o), l = q(), this.h();
    },
    h() {
      re(t, "class", "svelte-1rt0kpf");
    },
    m(o, i) {
      T(o, t, i), e[8](t), T(o, r, i), n && n.m(o, i), T(o, l, i), s = !0;
    },
    p(o, [i]) {
      /*$$slots*/
      o[4].default ? n ? (n.p(o, i), i & /*$$slots*/
      16 && k(n, 1)) : (n = J(o), n.c(), k(n, 1), n.m(l.parentNode, l)) : n && (ze(), D(n, 1, 1, () => {
        n = null;
      }), Ne());
    },
    i(o) {
      s || (k(n), s = !0);
    },
    o(o) {
      D(n), s = !1;
    },
    d(o) {
      o && (S(t), S(r), S(l)), e[8](null), n && n.d(o);
    }
  };
}
function X(e) {
  const {
    svelteInit: t,
    ...r
  } = e;
  return r;
}
function Ze(e, t, r) {
  let l, s, {
    $$slots: n = {},
    $$scope: o
  } = t;
  const i = Ae(n);
  let {
    svelteInit: u
  } = t;
  const _ = P(X(t)), p = P();
  K(e, p, (a) => r(0, l = a));
  const c = P();
  K(e, c, (a) => r(1, s = a));
  const w = [], m = Ve("$$ms-gr-react-wrapper"), {
    slotKey: C,
    slotIndex: v,
    subSlotIndex: f
  } = de() || {}, h = u({
    parent: m,
    props: _,
    target: p,
    slot: c,
    slotKey: C,
    slotIndex: v,
    subSlotIndex: f,
    onDestroy(a) {
      w.push(a);
    }
  });
  Xe("$$ms-gr-react-wrapper", h), qe(() => {
    _.set(X(t));
  }), Je(() => {
    w.forEach((a) => a());
  });
  function b(a) {
    H[a ? "unshift" : "push"](() => {
      l = a, p.set(l);
    });
  }
  function R(a) {
    H[a ? "unshift" : "push"](() => {
      s = a, c.set(s);
    });
  }
  return e.$$set = (a) => {
    r(17, t = G(G({}, t), V(a))), "svelteInit" in a && r(5, u = a.svelteInit), "$$scope" in a && r(6, o = a.$$scope);
  }, t = V(t), [l, s, p, c, i, u, o, n, b, R];
}
class Qe extends Fe {
  constructor(t) {
    super(), Be(this, t, Ze, Ye, Ge, {
      svelteInit: 5
    });
  }
}
const {
  SvelteComponent: dt
} = window.__gradio__svelte__internal, Y = window.ms_globals.rerender, F = window.ms_globals.tree;
function $e(e, t = {}) {
  function r(l) {
    const s = P(), n = new Qe({
      ...l,
      props: {
        svelteInit(o) {
          window.ms_globals.autokey += 1;
          const i = {
            key: window.ms_globals.autokey,
            svelteInstance: s,
            reactComponent: e,
            props: o.props,
            slot: o.slot,
            target: o.target,
            slotIndex: o.slotIndex,
            subSlotIndex: o.subSlotIndex,
            ignore: t.ignore,
            slotKey: o.slotKey,
            nodes: []
          }, u = o.parent ?? F;
          return u.nodes = [...u.nodes, i], Y({
            createPortal: W,
            node: F
          }), o.onDestroy(() => {
            u.nodes = u.nodes.filter((_) => _.svelteInstance !== s), Y({
              createPortal: W,
              node: F
            });
          }), i;
        },
        ...l.props
      }
    });
    return s.set(n), n;
  }
  return new Promise((l) => {
    window.ms_globals.initializePromise.then(() => {
      l(r);
    });
  });
}
const et = ["animationIterationCount", "borderImageOutset", "borderImageSlice", "borderImageWidth", "boxFlex", "boxFlexGroup", "boxOrdinalGroup", "columnCount", "columns", "flex", "flexGrow", "flexPositive", "flexShrink", "flexNegative", "flexOrder", "gridArea", "gridColumn", "gridColumnEnd", "gridColumnStart", "gridRow", "gridRowEnd", "gridRowStart", "lineClamp", "lineHeight", "opacity", "order", "orphans", "tabSize", "widows", "zIndex", "zoom", "fontWeight", "letterSpacing", "lineHeight"];
function tt(e) {
  return e ? Object.keys(e).reduce((t, r) => {
    const l = e[r];
    return t[r] = nt(r, l), t;
  }, {}) : {};
}
function nt(e, t) {
  return typeof t == "number" && !et.includes(e) ? t + "px" : t;
}
function M(e) {
  const t = [], r = e.cloneNode(!1);
  if (e._reactElement) {
    const s = x.Children.toArray(e._reactElement.props.children).map((n) => {
      if (x.isValidElement(n) && n.props.__slot__) {
        const {
          portals: o,
          clonedElement: i
        } = M(n.props.el);
        return x.cloneElement(n, {
          ...n.props,
          el: i,
          children: [...x.Children.toArray(n.props.children), ...o]
        });
      }
      return null;
    });
    return s.originalChildren = e._reactElement.props.children, t.push(W(x.cloneElement(e._reactElement, {
      ...e._reactElement.props,
      children: s
    }), r)), {
      clonedElement: r,
      portals: t
    };
  }
  Object.keys(e.getEventListeners()).forEach((s) => {
    e.getEventListeners(s).forEach(({
      listener: o,
      type: i,
      useCapture: u
    }) => {
      r.addEventListener(i, o, u);
    });
  });
  const l = Array.from(e.childNodes);
  for (let s = 0; s < l.length; s++) {
    const n = l[s];
    if (n.nodeType === 1) {
      const {
        clonedElement: o,
        portals: i
      } = M(n);
      t.push(...i), r.appendChild(o);
    } else n.nodeType === 3 && r.appendChild(n.cloneNode());
  }
  return {
    clonedElement: r,
    portals: t
  };
}
function rt(e, t) {
  e && (typeof e == "function" ? e(t) : e.current = t);
}
const E = oe(({
  slot: e,
  clone: t,
  className: r,
  style: l,
  observeAttributes: s
}, n) => {
  const o = se(), [i, u] = le([]), {
    forceClone: _
  } = me(), p = _ ? !0 : t;
  return ie(() => {
    var v;
    if (!o.current || !e)
      return;
    let c = e;
    function w() {
      let f = c;
      if (c.tagName.toLowerCase() === "svelte-slot" && c.children.length === 1 && c.children[0] && (f = c.children[0], f.tagName.toLowerCase() === "react-portal-target" && f.children[0] && (f = f.children[0])), rt(n, f), r && f.classList.add(...r.split(" ")), l) {
        const h = tt(l);
        Object.keys(h).forEach((b) => {
          f.style[b] = h[b];
        });
      }
    }
    let m = null, C = null;
    if (p && window.MutationObserver) {
      let f = function() {
        var a, I, d;
        (a = o.current) != null && a.contains(c) && ((I = o.current) == null || I.removeChild(c));
        const {
          portals: b,
          clonedElement: R
        } = M(e);
        c = R, u(b), c.style.display = "contents", C && clearTimeout(C), C = setTimeout(() => {
          w();
        }, 50), (d = o.current) == null || d.appendChild(c);
      };
      f();
      const h = Re(() => {
        f(), m == null || m.disconnect(), m == null || m.observe(e, {
          childList: !0,
          subtree: !0,
          attributes: s
        });
      }, 50);
      m = new window.MutationObserver(h), m.observe(e, {
        attributes: !0,
        childList: !0,
        subtree: !0
      });
    } else
      c.style.display = "contents", w(), (v = o.current) == null || v.appendChild(c);
    return () => {
      var f, h;
      c.style.display = "", (f = o.current) != null && f.contains(c) && ((h = o.current) == null || h.removeChild(c)), m == null || m.disconnect();
    };
  }, [e, p, r, l, n, s, _]), x.createElement("react-child", {
    ref: o,
    style: {
      display: "contents"
    }
  }, ...i);
});
function ot(e) {
  return /^(?:async\s+)?(?:function\s*(?:\w*\s*)?\(|\([\w\s,=]*\)\s*=>|\(\{[\w\s,=]*\}\)\s*=>|function\s*\*\s*\w*\s*\()/i.test(e.trim());
}
function st(e, t = !1) {
  try {
    if (fe(e))
      return e;
    if (t && !ot(e))
      return;
    if (typeof e == "string") {
      let r = e.trim();
      return r.startsWith(";") && (r = r.slice(1)), r.endsWith(";") && (r = r.slice(0, -1)), new Function(`return (...args) => (${r})(...args)`)();
    }
    return;
  } catch {
    return;
  }
}
function N(e, t) {
  return ce(() => st(e, t), [e, t]);
}
const lt = ({
  children: e,
  ...t
}) => /* @__PURE__ */ g.jsx(g.Fragment, {
  children: e(t)
});
function it(e) {
  return x.createElement(lt, {
    children: e
  });
}
function Z(e, t) {
  return e ? t != null && t.forceClone || t != null && t.params ? it((r) => /* @__PURE__ */ g.jsx(_e, {
    forceClone: t == null ? void 0 : t.forceClone,
    params: t == null ? void 0 : t.params,
    children: /* @__PURE__ */ g.jsx(E, {
      slot: e,
      clone: t == null ? void 0 : t.clone,
      ...r
    })
  })) : /* @__PURE__ */ g.jsx(E, {
    slot: e,
    clone: t == null ? void 0 : t.clone
  }) : null;
}
function ct({
  key: e,
  slots: t,
  targets: r
}, l) {
  return t[e] ? (...s) => r ? r.map((n, o) => /* @__PURE__ */ g.jsx(x.Fragment, {
    children: Z(n, {
      clone: !0,
      params: s,
      forceClone: !0
    })
  }, o)) : /* @__PURE__ */ g.jsx(g.Fragment, {
    children: Z(t[e], {
      clone: !0,
      params: s,
      forceClone: !0
    })
  }) : void 0;
}
function at(e) {
  return typeof e == "object" && e !== null ? e : {};
}
const ft = $e(({
  slots: e,
  afterOpenChange: t,
  getContainer: r,
  drawerRender: l,
  setSlotParams: s,
  ...n
}) => {
  const o = N(t), i = N(r), u = N(l), _ = at(n.closable);
  return /* @__PURE__ */ g.jsx(he, {
    ...n,
    afterOpenChange: o,
    closable: e["closable.closeIcon"] ? {
      ..._,
      closeIcon: /* @__PURE__ */ g.jsx(E, {
        slot: e["closable.closeIcon"]
      })
    } : n.closable,
    closeIcon: e.closeIcon ? /* @__PURE__ */ g.jsx(E, {
      slot: e.closeIcon
    }) : n.closeIcon,
    extra: e.extra ? /* @__PURE__ */ g.jsx(E, {
      slot: e.extra
    }) : n.extra,
    footer: e.footer ? /* @__PURE__ */ g.jsx(E, {
      slot: e.footer
    }) : n.footer,
    title: e.title ? /* @__PURE__ */ g.jsx(E, {
      slot: e.title
    }) : n.title,
    drawerRender: e.drawerRender ? ct({
      slots: e,
      key: "drawerRender"
    }) : u,
    getContainer: typeof r == "string" ? i : r
  });
});
export {
  ft as Drawer,
  ft as default
};
