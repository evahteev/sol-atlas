var ml = Object.defineProperty;
var Ll = (n, a, i) => a in n ? ml(n, a, { enumerable: !0, configurable: !0, writable: !0, value: i }) : n[a] = i;
var t9 = (n, a, i) => (Ll(n, typeof a != "symbol" ? a + "" : a, i), i);
import { utils as x1, init as xl, FormatDateType as c0, DomPosition as o2, ActionType as $l, dispose as bl, TooltipIconPosition as u0, registerOverlay as wl } from "klinecharts";
function vn(n, a, i) {
  const u = (n.x - a.x) * Math.cos(i) - (n.y - a.y) * Math.sin(i) + a.x, f = (n.x - a.x) * Math.sin(i) + (n.y - a.y) * Math.cos(i) + a.y;
  return { x: u, y: f };
}
function o9(n, a) {
  if (n.length > 1) {
    let i;
    return n[0].x === n[1].x && n[0].y !== n[1].y ? n[0].y < n[1].y ? i = {
      x: n[0].x,
      y: a.height
    } : i = {
      x: n[0].x,
      y: 0
    } : n[0].x > n[1].x ? i = {
      x: 0,
      y: x1.getLinearYFromCoordinates(n[0], n[1], { x: 0, y: n[0].y })
    } : i = {
      x: a.width,
      y: x1.getLinearYFromCoordinates(n[0], n[1], { x: a.width, y: n[0].y })
    }, { coordinates: [n[0], i] };
  }
  return [];
}
function Y2(n, a) {
  const i = Math.abs(n.x - a.x), u = Math.abs(n.y - a.y);
  return Math.sqrt(i * i + u * u);
}
const Al = {
  name: "arrow",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n }) => {
    if (n.length > 1) {
      const a = n[1].x > n[0].x ? 0 : 1, i = x1.getLinearSlopeIntercept(n[0], n[1]);
      let u;
      i ? u = Math.atan(i[0]) + Math.PI * a : n[1].y > n[0].y ? u = Math.PI / 2 : u = Math.PI / 2 * 3;
      const f = vn({ x: n[1].x - 8, y: n[1].y + 4 }, n[1], u), g = vn({ x: n[1].x - 8, y: n[1].y - 4 }, n[1], u);
      return [
        {
          type: "line",
          attrs: { coordinates: n }
        },
        {
          type: "line",
          ignoreEvent: !0,
          attrs: { coordinates: [f, n[1], g] }
        }
      ];
    }
    return [];
  }
}, Sl = {
  name: "circle",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  styles: {
    circle: {
      color: "rgba(22, 119, 255, 0.15)"
    }
  },
  createPointFigures: ({ coordinates: n }) => {
    if (n.length > 1) {
      const a = Y2(n[0], n[1]);
      return {
        type: "circle",
        attrs: {
          ...n[0],
          r: a
        },
        styles: { style: "stroke_fill" }
      };
    }
    return [];
  }
}, Ml = {
  name: "rect",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  styles: {
    polygon: {
      color: "rgba(22, 119, 255, 0.15)"
    }
  },
  createPointFigures: ({ coordinates: n }) => n.length > 1 ? [
    {
      type: "polygon",
      attrs: {
        coordinates: [
          n[0],
          { x: n[1].x, y: n[0].y },
          n[1],
          { x: n[0].x, y: n[1].y }
        ]
      },
      styles: { style: "stroke_fill" }
    }
  ] : []
}, Tl = {
  name: "parallelogram",
  totalStep: 4,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  styles: {
    polygon: {
      color: "rgba(22, 119, 255, 0.15)"
    }
  },
  createPointFigures: ({ coordinates: n }) => {
    if (n.length === 2)
      return [
        {
          type: "line",
          ignoreEvent: !0,
          attrs: { coordinates: n }
        }
      ];
    if (n.length === 3) {
      const a = {
        x: n[0].x + n[2].x - n[1].x,
        y: n[0].y + n[2].y - n[1].y
      };
      return [
        {
          type: "polygon",
          attrs: {
            coordinates: [
              n[0],
              n[1],
              n[2],
              a
            ]
          },
          styles: { style: "stroke_fill" }
        }
      ];
    }
    return [];
  },
  performEventPressedMove: ({ points: n, performPointIndex: a, performPoint: i }) => {
    a < 2 && (n[0].price = i.price, n[1].price = i.price);
  },
  performEventMoveForDrawing: ({ currentStep: n, points: a, performPoint: i }) => {
    n === 2 && (a[0].price = i.price);
  }
}, Il = {
  name: "triangle",
  totalStep: 4,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  styles: {
    polygon: {
      color: "rgba(22, 119, 255, 0.15)"
    }
  },
  createPointFigures: ({ coordinates: n }) => [
    {
      type: "polygon",
      attrs: { coordinates: n },
      styles: { style: "stroke_fill" }
    }
  ]
}, kl = {
  name: "fibonacciCircle",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n }) => {
    if (n.length > 1) {
      const a = Math.abs(n[0].x - n[1].x), i = Math.abs(n[0].y - n[1].y), u = Math.sqrt(a * a + i * i), f = [0.236, 0.382, 0.5, 0.618, 0.786, 1], g = [], d = [];
      return f.forEach((p) => {
        const m = u * p;
        g.push(
          { ...n[0], r: m }
        ), d.push({
          x: n[0].x,
          y: n[0].y + m + 6,
          text: `${(p * 100).toFixed(1)}%`
        });
      }), [
        {
          type: "circle",
          attrs: g,
          styles: { style: "stroke" }
        },
        {
          type: "text",
          ignoreEvent: !0,
          attrs: d
        }
      ];
    }
    return [];
  }
}, El = {
  name: "fibonacciSegment",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n, overlay: a, precision: i }) => {
    const u = [], f = [];
    if (n.length > 1) {
      const g = n[1].x > n[0].x ? n[0].x : n[1].x, d = [1, 0.786, 0.618, 0.5, 0.382, 0.236, 0], p = n[0].y - n[1].y, m = a.points, S = m[0].value - m[1].value;
      d.forEach((x) => {
        const M = n[1].y + p * x, D = (m[1].value + S * x).toFixed(i.price);
        u.push({ coordinates: [{ x: n[0].x, y: M }, { x: n[1].x, y: M }] }), f.push({
          x: g,
          y: M,
          text: `${D} (${(x * 100).toFixed(1)}%)`,
          baseline: "bottom"
        });
      });
    }
    return [
      {
        type: "line",
        attrs: u
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: f
      }
    ];
  }
}, Pl = {
  name: "fibonacciSpiral",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n, bounding: a }) => {
    if (n.length > 1) {
      const i = Y2(n[0], n[1]) / Math.sqrt(24), u = n[1].x > n[0].x ? 0 : 1, f = x1.getLinearSlopeIntercept(n[0], n[1]);
      let g;
      f ? g = Math.atan(f[0]) + Math.PI * u : n[1].y > n[0].y ? g = Math.PI / 2 : g = Math.PI / 2 * 3;
      const d = vn(
        { x: n[0].x - i, y: n[0].y },
        n[0],
        g
      ), p = vn(
        { x: n[0].x - i, y: n[0].y - i },
        n[0],
        g
      ), m = [{
        ...d,
        r: i,
        startAngle: g,
        endAngle: g + Math.PI / 2
      }, {
        ...p,
        r: i * 2,
        startAngle: g + Math.PI / 2,
        endAngle: g + Math.PI
      }];
      let S = n[0].x - i, x = n[0].y - i;
      for (let M = 2; M < 9; M++) {
        const D = m[M - 2].r + m[M - 1].r;
        let z = 0;
        switch (M % 4) {
          case 0: {
            z = g, S -= m[M - 2].r;
            break;
          }
          case 1: {
            z = g + Math.PI / 2, x -= m[M - 2].r;
            break;
          }
          case 2: {
            z = g + Math.PI, S += m[M - 2].r;
            break;
          }
          case 3: {
            z = g + Math.PI / 2 * 3, x += m[M - 2].r;
            break;
          }
        }
        const t1 = z + Math.PI / 2, p1 = vn({ x: S, y: x }, n[0], g);
        m.push({
          ...p1,
          r: D,
          startAngle: z,
          endAngle: t1
        });
      }
      return [
        {
          type: "arc",
          attrs: m
        },
        {
          type: "line",
          attrs: o9(n, a)
        }
      ];
    }
    return [];
  }
}, Ol = {
  name: "fibonacciSpeedResistanceFan",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n, bounding: a }) => {
    const i = [];
    let u = [];
    const f = [];
    if (n.length > 1) {
      const g = n[1].x > n[0].x ? -38 : 4, d = n[1].y > n[0].y ? -2 : 20, p = n[1].x - n[0].x, m = n[1].y - n[0].y;
      [1, 0.75, 0.618, 0.5, 0.382, 0.25, 0].forEach((x) => {
        const M = n[1].x - p * x, D = n[1].y - m * x;
        i.push({ coordinates: [{ x: M, y: n[0].y }, { x: M, y: n[1].y }] }), i.push({ coordinates: [{ x: n[0].x, y: D }, { x: n[1].x, y: D }] }), u = u.concat(o9([n[0], { x: M, y: n[1].y }], a)), u = u.concat(o9([n[0], { x: n[1].x, y: D }], a)), f.unshift({
          x: n[0].x + g,
          y: D + 10,
          text: `${x.toFixed(3)}`
        }), f.unshift({
          x: M - 18,
          y: n[0].y + d,
          text: `${x.toFixed(3)}`
        });
      });
    }
    return [
      {
        type: "line",
        attrs: i
      },
      {
        type: "line",
        attrs: u
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: f
      }
    ];
  }
}, Dl = {
  name: "fibonacciExtension",
  totalStep: 4,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n, overlay: a, precision: i }) => {
    const u = [], f = [];
    if (n.length > 2) {
      const g = a.points, d = g[1].value - g[0].value, p = n[1].y - n[0].y, m = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1], S = n[2].x > n[1].x ? n[1].x : n[2].x;
      m.forEach((x) => {
        const M = n[2].y + p * x, D = (g[2].value + d * x).toFixed(i.price);
        u.push({ coordinates: [{ x: n[1].x, y: M }, { x: n[2].x, y: M }] }), f.push({
          x: S,
          y: M,
          text: `${D} (${(x * 100).toFixed(1)}%)`,
          baseline: "bottom"
        });
      });
    }
    return [
      {
        type: "line",
        attrs: { coordinates: n },
        styles: { style: "dashed" }
      },
      {
        type: "line",
        attrs: u
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: f
      }
    ];
  }
}, Rl = {
  name: "gannBox",
  totalStep: 3,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  styles: {
    polygon: {
      color: "rgba(22, 119, 255, 0.15)"
    }
  },
  createPointFigures: ({ coordinates: n }) => {
    if (n.length > 1) {
      const a = (n[1].y - n[0].y) / 4, i = n[1].x - n[0].x, u = [
        { coordinates: [n[0], { x: n[1].x, y: n[1].y - a }] },
        { coordinates: [n[0], { x: n[1].x, y: n[1].y - a * 2 }] },
        { coordinates: [{ x: n[0].x, y: n[1].y }, { x: n[1].x, y: n[0].y + a }] },
        { coordinates: [{ x: n[0].x, y: n[1].y }, { x: n[1].x, y: n[0].y + a * 2 }] },
        { coordinates: [{ ...n[0] }, { x: n[0].x + i * 0.236, y: n[1].y }] },
        { coordinates: [{ ...n[0] }, { x: n[0].x + i * 0.5, y: n[1].y }] },
        { coordinates: [{ x: n[0].x, y: n[1].y }, { x: n[0].x + i * 0.236, y: n[0].y }] },
        { coordinates: [{ x: n[0].x, y: n[1].y }, { x: n[0].x + i * 0.5, y: n[0].y }] }
      ], f = [
        { coordinates: [n[0], n[1]] },
        { coordinates: [{ x: n[0].x, y: n[1].y }, { x: n[1].x, y: n[0].y }] }
      ];
      return [
        {
          type: "line",
          attrs: [
            { coordinates: [n[0], { x: n[1].x, y: n[0].y }] },
            { coordinates: [{ x: n[1].x, y: n[0].y }, n[1]] },
            { coordinates: [n[1], { x: n[0].x, y: n[1].y }] },
            { coordinates: [{ x: n[0].x, y: n[1].y }, n[0]] }
          ]
        },
        {
          type: "polygon",
          ignoreEvent: !0,
          attrs: {
            coordinates: [
              n[0],
              { x: n[1].x, y: n[0].y },
              n[1],
              { x: n[0].x, y: n[1].y }
            ]
          },
          styles: { style: "fill" }
        },
        {
          type: "line",
          attrs: u,
          styles: { style: "dashed" }
        },
        {
          type: "line",
          attrs: f
        }
      ];
    }
    return [];
  }
}, Bl = {
  name: "threeWaves",
  totalStep: 5,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n }) => {
    const a = n.map((i, u) => ({
      ...i,
      text: `(${u})`,
      baseline: "bottom"
    }));
    return [
      {
        type: "line",
        attrs: { coordinates: n }
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: a
      }
    ];
  }
}, Fl = {
  name: "fiveWaves",
  totalStep: 7,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n }) => {
    const a = n.map((i, u) => ({
      ...i,
      text: `(${u})`,
      baseline: "bottom"
    }));
    return [
      {
        type: "line",
        attrs: { coordinates: n }
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: a
      }
    ];
  }
}, Nl = {
  name: "eightWaves",
  totalStep: 10,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n }) => {
    const a = n.map((i, u) => ({
      ...i,
      text: `(${u})`,
      baseline: "bottom"
    }));
    return [
      {
        type: "line",
        attrs: { coordinates: n }
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: a
      }
    ];
  }
}, Kl = {
  name: "anyWaves",
  totalStep: Number.MAX_SAFE_INTEGER,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n }) => {
    const a = n.map((i, u) => ({
      ...i,
      text: `(${u})`,
      baseline: "bottom"
    }));
    return [
      {
        type: "line",
        attrs: { coordinates: n }
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: a
      }
    ];
  }
}, Ul = {
  name: "abcd",
  totalStep: 5,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  createPointFigures: ({ coordinates: n }) => {
    let a = [], i = [];
    const u = ["A", "B", "C", "D"], f = n.map((g, d) => ({
      ...g,
      baseline: "bottom",
      text: `(${u[d]})`
    }));
    return n.length > 2 && (a = [n[0], n[2]], n.length > 3 && (i = [n[1], n[3]])), [
      {
        type: "line",
        attrs: { coordinates: n }
      },
      {
        type: "line",
        attrs: [{ coordinates: a }, { coordinates: i }],
        styles: { style: "dashed" }
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: f
      }
    ];
  }
}, Zl = {
  name: "xabcd",
  totalStep: 6,
  needDefaultPointFigure: !0,
  needDefaultXAxisFigure: !0,
  needDefaultYAxisFigure: !0,
  styles: {
    polygon: {
      color: "rgba(22, 119, 255, 0.15)"
    }
  },
  createPointFigures: ({ coordinates: n, overlay: a }) => {
    const i = [], u = [], f = ["X", "A", "B", "C", "D"], g = n.map((d, p) => ({
      ...d,
      baseline: "bottom",
      text: `(${f[p]})`
    }));
    return n.length > 2 && (i.push({ coordinates: [n[0], n[2]] }), u.push({ coordinates: [n[0], n[1], n[2]] }), n.length > 3 && (i.push({ coordinates: [n[1], n[3]] }), n.length > 4 && (i.push({ coordinates: [n[2], n[4]] }), u.push({ coordinates: [n[2], n[3], n[4]] })))), [
      {
        type: "line",
        attrs: { coordinates: n }
      },
      {
        type: "line",
        attrs: i,
        styles: { style: "dashed" }
      },
      {
        type: "polygon",
        ignoreEvent: !0,
        attrs: u
      },
      {
        type: "text",
        ignoreEvent: !0,
        attrs: g
      }
    ];
  }
}, Wl = [
  Al,
  Sl,
  Ml,
  Il,
  Tl,
  kl,
  El,
  Pl,
  Ol,
  Dl,
  Rl,
  Bl,
  Fl,
  Nl,
  Kl,
  Ul,
  Zl
], zl = (n, a) => n === a, l9 = Symbol("solid-proxy"), Ql = Symbol("solid-track"), _0 = {
  equals: zl
};
let V2 = e3;
const He = 1, d0 = 2, X2 = {
  owned: null,
  cleanups: null,
  context: null,
  owner: null
}, n9 = {};
var S1 = null;
let r9 = null, Hl = null, y1 = null, W1 = null, Qe = null, w0 = 0;
function g0(n, a) {
  const i = y1, u = S1, f = n.length === 0, g = a === void 0 ? u : a, d = f ? X2 : {
    owned: null,
    cleanups: null,
    context: g ? g.context : null,
    owner: g
  }, p = f ? n : () => n(() => be(() => S0(d)));
  S1 = d, y1 = null;
  try {
    return nt(p, !0);
  } finally {
    y1 = i, S1 = u;
  }
}
function V(n, a) {
  a = a ? Object.assign({}, _0, a) : _0;
  const i = {
    value: n,
    observers: null,
    observerSlots: null,
    comparator: a.equals || void 0
  }, u = (f) => (typeof f == "function" && (f = f(i.value)), J2(i, f));
  return [j2.bind(i), u];
}
function l2(n, a, i) {
  const u = A0(n, a, !0, He);
  Bt(u);
}
function P1(n, a, i) {
  const u = A0(n, a, !1, He);
  Bt(u);
}
function Ie(n, a, i) {
  V2 = Jl;
  const u = A0(n, a, !1, He);
  (!i || !i.render) && (u.user = !0), Qe ? Qe.push(u) : Bt(u);
}
function A1(n, a, i) {
  i = i ? Object.assign({}, _0, i) : _0;
  const u = A0(n, a, !0, 0);
  return u.observers = null, u.observerSlots = null, u.comparator = i.equals || void 0, Bt(u), j2.bind(u);
}
function Gl(n) {
  return n && typeof n == "object" && "then" in n;
}
function Yl(n, a, i) {
  let u, f, g;
  arguments.length === 2 && typeof a == "object" || arguments.length === 1 ? (u = !0, f = n, g = a || {}) : (u = n, f = a, g = i || {});
  let d = null, p = n9, m = !1, S = "initialValue" in g, x = typeof u == "function" && A1(u);
  const M = /* @__PURE__ */ new Set(), [D, z] = (g.storage || V)(g.initialValue), [t1, p1] = V(void 0), [n1, i1] = V(void 0, {
    equals: !1
  }), [G, U] = V(S ? "ready" : "unresolved");
  function q(s1, l1, h1, j1) {
    return d === s1 && (d = null, j1 !== void 0 && (S = !0), (s1 === p || l1 === p) && g.onHydrated && queueMicrotask(
      () => g.onHydrated(j1, {
        value: l1
      })
    ), p = n9, $1(l1, h1)), l1;
  }
  function $1(s1, l1) {
    nt(() => {
      l1 === void 0 && z(() => s1), U(l1 !== void 0 ? "errored" : S ? "ready" : "unresolved"), p1(l1);
      for (const h1 of M.keys())
        h1.decrement();
      M.clear();
    }, !1);
  }
  function R1() {
    const s1 = Xl, l1 = D(), h1 = t1();
    if (h1 !== void 0 && !d)
      throw h1;
    return y1 && !y1.user && s1 && l2(() => {
      n1(), d && (s1.resolved || M.has(s1) || (s1.increment(), M.add(s1)));
    }), l1;
  }
  function M1(s1 = !0) {
    if (s1 !== !1 && m)
      return;
    m = !1;
    const l1 = x ? x() : u;
    if (l1 == null || l1 === !1) {
      q(d, be(D));
      return;
    }
    const h1 = p !== n9 ? p : be(
      () => f(l1, {
        value: D(),
        refetching: s1
      })
    );
    return Gl(h1) ? (d = h1, "value" in h1 ? (h1.status === "success" ? q(d, h1.value, void 0, l1) : q(d, void 0, void 0, l1), h1) : (m = !0, queueMicrotask(() => m = !1), nt(() => {
      U(S ? "refreshing" : "pending"), i1();
    }, !1), h1.then(
      (j1) => q(h1, j1, void 0, l1),
      (j1) => q(h1, void 0, n3(j1), l1)
    ))) : (q(d, h1, void 0, l1), h1);
  }
  return Object.defineProperties(R1, {
    state: {
      get: () => G()
    },
    error: {
      get: () => t1()
    },
    loading: {
      get() {
        const s1 = G();
        return s1 === "pending" || s1 === "refreshing";
      }
    },
    latest: {
      get() {
        if (!S)
          return R1();
        const s1 = t1();
        if (s1 && !d)
          throw s1;
        return D();
      }
    }
  }), x ? l2(() => M1(!1)) : M1(!1), [
    R1,
    {
      refetch: M1,
      mutate: z
    }
  ];
}
function be(n) {
  if (y1 === null)
    return n();
  const a = y1;
  y1 = null;
  try {
    return n();
  } finally {
    y1 = a;
  }
}
function q2(n) {
  Ie(() => be(n));
}
function v9(n) {
  return S1 === null || (S1.cleanups === null ? S1.cleanups = [n] : S1.cleanups.push(n)), n;
}
function Vl(n) {
  const a = y1, i = S1;
  return Promise.resolve().then(() => {
    y1 = a, S1 = i;
    let u;
    return nt(n, !1), y1 = S1 = null, u ? u.done : void 0;
  });
}
let Xl;
function j2() {
  if (this.sources && this.state)
    if (this.state === He)
      Bt(this);
    else {
      const n = W1;
      W1 = null, nt(() => C0(this), !1), W1 = n;
    }
  if (y1) {
    const n = this.observers ? this.observers.length : 0;
    y1.sources ? (y1.sources.push(this), y1.sourceSlots.push(n)) : (y1.sources = [this], y1.sourceSlots = [n]), this.observers ? (this.observers.push(y1), this.observerSlots.push(y1.sources.length - 1)) : (this.observers = [y1], this.observerSlots = [y1.sources.length - 1]);
  }
  return this.value;
}
function J2(n, a, i) {
  let u = n.value;
  return (!n.comparator || !n.comparator(u, a)) && (n.value = a, n.observers && n.observers.length && nt(() => {
    for (let f = 0; f < n.observers.length; f += 1) {
      const g = n.observers[f], d = r9 && r9.running;
      d && r9.disposed.has(g), (d ? !g.tState : !g.state) && (g.pure ? W1.push(g) : Qe.push(g), g.observers && t3(g)), d || (g.state = He);
    }
    if (W1.length > 1e6)
      throw W1 = [], new Error();
  }, !1)), a;
}
function Bt(n) {
  if (!n.fn)
    return;
  S0(n);
  const a = w0;
  ql(
    n,
    n.value,
    a
  );
}
function ql(n, a, i) {
  let u;
  const f = S1, g = y1;
  y1 = S1 = n;
  try {
    u = n.fn(a);
  } catch (d) {
    return n.pure && (n.state = He, n.owned && n.owned.forEach(S0), n.owned = null), n.updatedAt = i + 1, r3(d);
  } finally {
    y1 = g, S1 = f;
  }
  (!n.updatedAt || n.updatedAt <= i) && (n.updatedAt != null && "observers" in n ? J2(n, u) : n.value = u, n.updatedAt = i);
}
function A0(n, a, i, u = He, f) {
  const g = {
    fn: n,
    state: u,
    updatedAt: null,
    owned: null,
    sources: null,
    sourceSlots: null,
    cleanups: null,
    value: a,
    owner: S1,
    context: S1 ? S1.context : null,
    pure: i
  };
  return S1 === null || S1 !== X2 && (S1.owned ? S1.owned.push(g) : S1.owned = [g]), g;
}
function v0(n) {
  if (n.state === 0)
    return;
  if (n.state === d0)
    return C0(n);
  if (n.suspense && be(n.suspense.inFallback))
    return n.suspense.effects.push(n);
  const a = [n];
  for (; (n = n.owner) && (!n.updatedAt || n.updatedAt < w0); )
    n.state && a.push(n);
  for (let i = a.length - 1; i >= 0; i--)
    if (n = a[i], n.state === He)
      Bt(n);
    else if (n.state === d0) {
      const u = W1;
      W1 = null, nt(() => C0(n, a[0]), !1), W1 = u;
    }
}
function nt(n, a) {
  if (W1)
    return n();
  let i = !1;
  a || (W1 = []), Qe ? i = !0 : Qe = [], w0++;
  try {
    const u = n();
    return jl(i), u;
  } catch (u) {
    i || (Qe = null), W1 = null, r3(u);
  }
}
function jl(n) {
  if (W1 && (e3(W1), W1 = null), n)
    return;
  const a = Qe;
  Qe = null, a.length && nt(() => V2(a), !1);
}
function e3(n) {
  for (let a = 0; a < n.length; a++)
    v0(n[a]);
}
function Jl(n) {
  let a, i = 0;
  for (a = 0; a < n.length; a++) {
    const u = n[a];
    u.user ? n[i++] = u : v0(u);
  }
  for (a = 0; a < i; a++)
    v0(n[a]);
}
function C0(n, a) {
  n.state = 0;
  for (let i = 0; i < n.sources.length; i += 1) {
    const u = n.sources[i];
    if (u.sources) {
      const f = u.state;
      f === He ? u !== a && (!u.updatedAt || u.updatedAt < w0) && v0(u) : f === d0 && C0(u, a);
    }
  }
}
function t3(n) {
  for (let a = 0; a < n.observers.length; a += 1) {
    const i = n.observers[a];
    i.state || (i.state = d0, i.pure ? W1.push(i) : Qe.push(i), i.observers && t3(i));
  }
}
function S0(n) {
  let a;
  if (n.sources)
    for (; n.sources.length; ) {
      const i = n.sources.pop(), u = n.sourceSlots.pop(), f = i.observers;
      if (f && f.length) {
        const g = f.pop(), d = i.observerSlots.pop();
        u < f.length && (g.sourceSlots[d] = u, f[u] = g, i.observerSlots[u] = d);
      }
    }
  if (n.owned) {
    for (a = n.owned.length - 1; a >= 0; a--)
      S0(n.owned[a]);
    n.owned = null;
  }
  if (n.cleanups) {
    for (a = n.cleanups.length - 1; a >= 0; a--)
      n.cleanups[a]();
    n.cleanups = null;
  }
  n.state = 0;
}
function n3(n) {
  return n instanceof Error ? n : new Error(typeof n == "string" ? n : "Unknown error", {
    cause: n
  });
}
function r3(n, a = S1) {
  throw n3(n);
}
const ec = Symbol("fallback");
function c2(n) {
  for (let a = 0; a < n.length; a++)
    n[a]();
}
function tc(n, a, i = {}) {
  let u = [], f = [], g = [], d = 0, p = a.length > 1 ? [] : null;
  return v9(() => c2(g)), () => {
    let m = n() || [], S, x;
    return m[Ql], be(() => {
      let D = m.length, z, t1, p1, n1, i1, G, U, q, $1;
      if (D === 0)
        d !== 0 && (c2(g), g = [], u = [], f = [], d = 0, p && (p = [])), i.fallback && (u = [ec], f[0] = g0((R1) => (g[0] = R1, i.fallback())), d = 1);
      else if (d === 0) {
        for (f = new Array(D), x = 0; x < D; x++)
          u[x] = m[x], f[x] = g0(M);
        d = D;
      } else {
        for (p1 = new Array(D), n1 = new Array(D), p && (i1 = new Array(D)), G = 0, U = Math.min(d, D); G < U && u[G] === m[G]; G++)
          ;
        for (U = d - 1, q = D - 1; U >= G && q >= G && u[U] === m[q]; U--, q--)
          p1[q] = f[U], n1[q] = g[U], p && (i1[q] = p[U]);
        for (z = /* @__PURE__ */ new Map(), t1 = new Array(q + 1), x = q; x >= G; x--)
          $1 = m[x], S = z.get($1), t1[x] = S === void 0 ? -1 : S, z.set($1, x);
        for (S = G; S <= U; S++)
          $1 = u[S], x = z.get($1), x !== void 0 && x !== -1 ? (p1[x] = f[S], n1[x] = g[S], p && (i1[x] = p[S]), x = t1[x], z.set($1, x)) : g[S]();
        for (x = G; x < D; x++)
          x in p1 ? (f[x] = p1[x], g[x] = n1[x], p && (p[x] = i1[x], p[x](x))) : f[x] = g0(M);
        f = f.slice(0, d = D), u = m.slice(0);
      }
      return f;
    });
    function M(D) {
      if (g[x] = D, p) {
        const [z, t1] = V(x);
        return p[x] = t1, a(m[x], z);
      }
      return a(m[x]);
    }
  };
}
function B(n, a) {
  return be(() => n(a || {}));
}
function f0() {
  return !0;
}
const nc = {
  get(n, a, i) {
    return a === l9 ? i : n.get(a);
  },
  has(n, a) {
    return a === l9 ? !0 : n.has(a);
  },
  set: f0,
  deleteProperty: f0,
  getOwnPropertyDescriptor(n, a) {
    return {
      configurable: !0,
      enumerable: !0,
      get() {
        return n.get(a);
      },
      set: f0,
      deleteProperty: f0
    };
  },
  ownKeys(n) {
    return n.keys();
  }
};
function i9(n) {
  return (n = typeof n == "function" ? n() : n) ? n : {};
}
function rc() {
  for (let n = 0, a = this.length; n < a; ++n) {
    const i = this[n]();
    if (i !== void 0)
      return i;
  }
}
function i3(...n) {
  let a = !1;
  for (let d = 0; d < n.length; d++) {
    const p = n[d];
    a = a || !!p && l9 in p, n[d] = typeof p == "function" ? (a = !0, A1(p)) : p;
  }
  if (a)
    return new Proxy(
      {
        get(d) {
          for (let p = n.length - 1; p >= 0; p--) {
            const m = i9(n[p])[d];
            if (m !== void 0)
              return m;
          }
        },
        has(d) {
          for (let p = n.length - 1; p >= 0; p--)
            if (d in i9(n[p]))
              return !0;
          return !1;
        },
        keys() {
          const d = [];
          for (let p = 0; p < n.length; p++)
            d.push(...Object.keys(i9(n[p])));
          return [...new Set(d)];
        }
      },
      nc
    );
  const i = {}, u = /* @__PURE__ */ Object.create(null);
  for (let d = n.length - 1; d >= 0; d--) {
    const p = n[d];
    if (!p)
      continue;
    const m = Object.getOwnPropertyNames(p);
    for (let S = m.length - 1; S >= 0; S--) {
      const x = m[S];
      if (x === "__proto__" || x === "constructor")
        continue;
      const M = Object.getOwnPropertyDescriptor(p, x);
      if (!u[x])
        u[x] = M.get ? {
          enumerable: !0,
          configurable: !0,
          get: rc.bind(i[x] = [M.get.bind(p)])
        } : M.value !== void 0 ? M : void 0;
      else {
        const D = i[x];
        D && (M.get ? D.push(M.get.bind(p)) : M.value !== void 0 && D.push(() => M.value));
      }
    }
  }
  const f = {}, g = Object.keys(u);
  for (let d = g.length - 1; d >= 0; d--) {
    const p = g[d], m = u[p];
    m && m.get ? Object.defineProperty(f, p, m) : f[p] = m ? m.value : void 0;
  }
  return f;
}
const ic = (n) => `Stale read from <${n}>.`;
function ac(n) {
  const a = "fallback" in n && {
    fallback: () => n.fallback
  };
  return A1(tc(() => n.each, n.children, a || void 0));
}
function Z1(n) {
  const a = n.keyed, i = A1(() => n.when, void 0, {
    equals: (u, f) => a ? u === f : !u == !f
  });
  return A1(
    () => {
      const u = i();
      if (u) {
        const f = n.children;
        return typeof f == "function" && f.length > 0 ? be(
          () => f(
            a ? u : () => {
              if (!be(i))
                throw ic("Show");
              return n.when;
            }
          )
        ) : f;
      }
      return n.fallback;
    },
    void 0,
    void 0
  );
}
function sc(n, a, i) {
  let u = i.length, f = a.length, g = u, d = 0, p = 0, m = a[f - 1].nextSibling, S = null;
  for (; d < f || p < g; ) {
    if (a[d] === i[p]) {
      d++, p++;
      continue;
    }
    for (; a[f - 1] === i[g - 1]; )
      f--, g--;
    if (f === d) {
      const x = g < u ? p ? i[p - 1].nextSibling : i[g - p] : m;
      for (; p < g; )
        n.insertBefore(i[p++], x);
    } else if (g === p)
      for (; d < f; )
        (!S || !S.has(a[d])) && a[d].remove(), d++;
    else if (a[d] === i[g - 1] && i[p] === a[f - 1]) {
      const x = a[--f].nextSibling;
      n.insertBefore(i[p++], a[d++].nextSibling), n.insertBefore(i[--g], x), a[f] = i[g];
    } else {
      if (!S) {
        S = /* @__PURE__ */ new Map();
        let M = p;
        for (; M < g; )
          S.set(i[M], M++);
      }
      const x = S.get(a[d]);
      if (x != null)
        if (p < x && x < g) {
          let M = d, D = 1, z;
          for (; ++M < f && M < g && !((z = S.get(a[M])) == null || z !== x + D); )
            D++;
          if (D > x - p) {
            const t1 = a[d];
            for (; p < x; )
              n.insertBefore(i[p++], t1);
          } else
            n.replaceChild(i[p++], a[d++]);
        } else
          d++;
      else
        a[d++].remove();
    }
  }
}
const u2 = "_$DX_DELEGATE";
function oc(n, a, i, u = {}) {
  let f;
  return g0((g) => {
    f = g, a === document ? n() : F(a, n(), a.firstChild ? null : void 0, i);
  }, u.owner), () => {
    f(), a.textContent = "";
  };
}
function I(n, a, i) {
  let u;
  const f = () => {
    const d = document.createElement("template");
    return d.innerHTML = n, i ? d.content.firstChild.firstChild : d.content.firstChild;
  }, g = a ? () => be(() => document.importNode(u || (u = f()), !0)) : () => (u || (u = f())).cloneNode(!0);
  return g.cloneNode = g, g;
}
function ke(n, a = window.document) {
  const i = a[u2] || (a[u2] = /* @__PURE__ */ new Set());
  for (let u = 0, f = n.length; u < f; u++) {
    const g = n[u];
    i.has(g) || (i.add(g), a.addEventListener(g, lc));
  }
}
function ve(n, a, i) {
  i == null ? n.removeAttribute(a) : n.setAttribute(a, i);
}
function vt(n, a) {
  a == null ? n.removeAttribute("class") : n.className = a;
}
function dt(n, a, i, u) {
  if (u)
    Array.isArray(i) ? (n[`$$${a}`] = i[0], n[`$$${a}Data`] = i[1]) : n[`$$${a}`] = i;
  else if (Array.isArray(i)) {
    const f = i[0];
    n.addEventListener(a, i[0] = (g) => f.call(n, i[1], g));
  } else
    n.addEventListener(a, i);
}
function Ft(n, a, i) {
  if (!a)
    return i ? ve(n, "style") : a;
  const u = n.style;
  if (typeof a == "string")
    return u.cssText = a;
  typeof i == "string" && (u.cssText = i = void 0), i || (i = {}), a || (a = {});
  let f, g;
  for (g in i)
    a[g] == null && u.removeProperty(g), delete i[g];
  for (g in a)
    f = a[g], f !== i[g] && (u.setProperty(g, f), i[g] = f);
  return i;
}
function C9(n, a, i) {
  return be(() => n(a, i));
}
function F(n, a, i, u) {
  if (i !== void 0 && !u && (u = []), typeof a != "function")
    return y0(n, a, u, i);
  P1((f) => y0(n, a(), f, i), u);
}
function lc(n) {
  const a = `$$${n.type}`;
  let i = n.composedPath && n.composedPath()[0] || n.target;
  for (n.target !== i && Object.defineProperty(n, "target", {
    configurable: !0,
    value: i
  }), Object.defineProperty(n, "currentTarget", {
    configurable: !0,
    get() {
      return i || document;
    }
  }); i; ) {
    const u = i[a];
    if (u && !i.disabled) {
      const f = i[`${a}Data`];
      if (f !== void 0 ? u.call(i, f, n) : u.call(i, n), n.cancelBubble)
        return;
    }
    i = i._$host || i.parentNode || i.host;
  }
}
function y0(n, a, i, u, f) {
  for (; typeof i == "function"; )
    i = i();
  if (a === i)
    return i;
  const g = typeof a, d = u !== void 0;
  if (n = d && i[0] && i[0].parentNode || n, g === "string" || g === "number")
    if (g === "number" && (a = a.toString()), d) {
      let p = i[0];
      p && p.nodeType === 3 ? p.data !== a && (p.data = a) : p = document.createTextNode(a), i = Rt(n, i, u, p);
    } else
      i !== "" && typeof i == "string" ? i = n.firstChild.data = a : i = n.textContent = a;
  else if (a == null || g === "boolean")
    i = Rt(n, i, u);
  else {
    if (g === "function")
      return P1(() => {
        let p = a();
        for (; typeof p == "function"; )
          p = p();
        i = y0(n, p, i, u);
      }), () => i;
    if (Array.isArray(a)) {
      const p = [], m = i && Array.isArray(i);
      if (c9(p, a, i, f))
        return P1(() => i = y0(n, p, i, u, !0)), () => i;
      if (p.length === 0) {
        if (i = Rt(n, i, u), d)
          return i;
      } else
        m ? i.length === 0 ? f2(n, p, u) : sc(n, i, p) : (i && Rt(n), f2(n, p));
      i = p;
    } else if (a.nodeType) {
      if (Array.isArray(i)) {
        if (d)
          return i = Rt(n, i, u, a);
        Rt(n, i, null, a);
      } else
        i == null || i === "" || !n.firstChild ? n.appendChild(a) : n.replaceChild(a, n.firstChild);
      i = a;
    }
  }
  return i;
}
function c9(n, a, i, u) {
  let f = !1;
  for (let g = 0, d = a.length; g < d; g++) {
    let p = a[g], m = i && i[n.length], S;
    if (!(p == null || p === !0 || p === !1))
      if ((S = typeof p) == "object" && p.nodeType)
        n.push(p);
      else if (Array.isArray(p))
        f = c9(n, p, m) || f;
      else if (S === "function")
        if (u) {
          for (; typeof p == "function"; )
            p = p();
          f = c9(
            n,
            Array.isArray(p) ? p : [p],
            Array.isArray(m) ? m : [m]
          ) || f;
        } else
          n.push(p), f = !0;
      else {
        const x = String(p);
        m && m.nodeType === 3 && m.data === x ? n.push(m) : n.push(document.createTextNode(x));
      }
  }
  return f;
}
function f2(n, a, i = null) {
  for (let u = 0, f = a.length; u < f; u++)
    n.insertBefore(a[u], i);
}
function Rt(n, a, i, u) {
  if (i === void 0)
    return n.textContent = "";
  const f = u || document.createTextNode("");
  if (a.length) {
    let g = !1;
    for (let d = a.length - 1; d >= 0; d--) {
      const p = a[d];
      if (f !== p) {
        const m = p.parentNode === n;
        !g && !d ? m ? n.replaceChild(f, p) : n.insertBefore(f, i) : m && p.remove();
      } else
        g = !0;
    }
  } else
    n.insertBefore(f, i);
  return [f];
}
var ze = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {};
function a3(n) {
  return n && n.__esModule && Object.prototype.hasOwnProperty.call(n, "default") ? n.default : n;
}
var cc = typeof ze == "object" && ze && ze.Object === Object && ze, s3 = cc, uc = s3, fc = typeof self == "object" && self && self.Object === Object && self, hc = uc || fc || Function("return this")(), Ee = hc, gc = Ee, pc = gc.Symbol, M0 = pc, h2 = M0, o3 = Object.prototype, _c = o3.hasOwnProperty, dc = o3.toString, dn = h2 ? h2.toStringTag : void 0;
function vc(n) {
  var a = _c.call(n, dn), i = n[dn];
  try {
    n[dn] = void 0;
    var u = !0;
  } catch {
  }
  var f = dc.call(n);
  return u && (a ? n[dn] = i : delete n[dn]), f;
}
var Cc = vc, yc = Object.prototype, mc = yc.toString;
function Lc(n) {
  return mc.call(n);
}
var xc = Lc, g2 = M0, $c = Cc, bc = xc, wc = "[object Null]", Ac = "[object Undefined]", p2 = g2 ? g2.toStringTag : void 0;
function Sc(n) {
  return n == null ? n === void 0 ? Ac : wc : p2 && p2 in Object(n) ? $c(n) : bc(n);
}
var Cn = Sc;
function Mc(n) {
  var a = typeof n;
  return n != null && (a == "object" || a == "function");
}
var Nt = Mc, Tc = Cn, Ic = Nt, kc = "[object AsyncFunction]", Ec = "[object Function]", Pc = "[object GeneratorFunction]", Oc = "[object Proxy]";
function Dc(n) {
  if (!Ic(n))
    return !1;
  var a = Tc(n);
  return a == Ec || a == Pc || a == kc || a == Oc;
}
var l3 = Dc, Rc = Ee, Bc = Rc["__core-js_shared__"], Fc = Bc, a9 = Fc, _2 = function() {
  var n = /[^.]+$/.exec(a9 && a9.keys && a9.keys.IE_PROTO || "");
  return n ? "Symbol(src)_1." + n : "";
}();
function Nc(n) {
  return !!_2 && _2 in n;
}
var Kc = Nc, Uc = Function.prototype, Zc = Uc.toString;
function Wc(n) {
  if (n != null) {
    try {
      return Zc.call(n);
    } catch {
    }
    try {
      return n + "";
    } catch {
    }
  }
  return "";
}
var c3 = Wc, zc = l3, Qc = Kc, Hc = Nt, Gc = c3, Yc = /[\\^$.*+?()[\]{}|]/g, Vc = /^\[object .+?Constructor\]$/, Xc = Function.prototype, qc = Object.prototype, jc = Xc.toString, Jc = qc.hasOwnProperty, eu = RegExp(
  "^" + jc.call(Jc).replace(Yc, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
);
function tu(n) {
  if (!Hc(n) || Qc(n))
    return !1;
  var a = zc(n) ? eu : Vc;
  return a.test(Gc(n));
}
var nu = tu;
function ru(n, a) {
  return n == null ? void 0 : n[a];
}
var iu = ru, au = nu, su = iu;
function ou(n, a) {
  var i = su(n, a);
  return au(i) ? i : void 0;
}
var Ct = ou, lu = Ct, cu = function() {
  try {
    var n = lu(Object, "defineProperty");
    return n({}, "", {}), n;
  } catch {
  }
}(), uu = cu, d2 = uu;
function fu(n, a, i) {
  a == "__proto__" && d2 ? d2(n, a, {
    configurable: !0,
    enumerable: !0,
    value: i,
    writable: !0
  }) : n[a] = i;
}
var u3 = fu;
function hu(n, a) {
  return n === a || n !== n && a !== a;
}
var f3 = hu, gu = u3, pu = f3, _u = Object.prototype, du = _u.hasOwnProperty;
function vu(n, a, i) {
  var u = n[a];
  (!(du.call(n, a) && pu(u, i)) || i === void 0 && !(a in n)) && gu(n, a, i);
}
var y9 = vu, Cu = Array.isArray, Kt = Cu;
function yu(n) {
  return n != null && typeof n == "object";
}
var Ut = yu, mu = Cn, Lu = Ut, xu = "[object Symbol]";
function $u(n) {
  return typeof n == "symbol" || Lu(n) && mu(n) == xu;
}
var m9 = $u, bu = Kt, wu = m9, Au = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, Su = /^\w*$/;
function Mu(n, a) {
  if (bu(n))
    return !1;
  var i = typeof n;
  return i == "number" || i == "symbol" || i == "boolean" || n == null || wu(n) ? !0 : Su.test(n) || !Au.test(n) || a != null && n in Object(a);
}
var Tu = Mu, Iu = Ct, ku = Iu(Object, "create"), T0 = ku, v2 = T0;
function Eu() {
  this.__data__ = v2 ? v2(null) : {}, this.size = 0;
}
var Pu = Eu;
function Ou(n) {
  var a = this.has(n) && delete this.__data__[n];
  return this.size -= a ? 1 : 0, a;
}
var Du = Ou, Ru = T0, Bu = "__lodash_hash_undefined__", Fu = Object.prototype, Nu = Fu.hasOwnProperty;
function Ku(n) {
  var a = this.__data__;
  if (Ru) {
    var i = a[n];
    return i === Bu ? void 0 : i;
  }
  return Nu.call(a, n) ? a[n] : void 0;
}
var Uu = Ku, Zu = T0, Wu = Object.prototype, zu = Wu.hasOwnProperty;
function Qu(n) {
  var a = this.__data__;
  return Zu ? a[n] !== void 0 : zu.call(a, n);
}
var Hu = Qu, Gu = T0, Yu = "__lodash_hash_undefined__";
function Vu(n, a) {
  var i = this.__data__;
  return this.size += this.has(n) ? 0 : 1, i[n] = Gu && a === void 0 ? Yu : a, this;
}
var Xu = Vu, qu = Pu, ju = Du, Ju = Uu, ef = Hu, tf = Xu;
function Zt(n) {
  var a = -1, i = n == null ? 0 : n.length;
  for (this.clear(); ++a < i; ) {
    var u = n[a];
    this.set(u[0], u[1]);
  }
}
Zt.prototype.clear = qu;
Zt.prototype.delete = ju;
Zt.prototype.get = Ju;
Zt.prototype.has = ef;
Zt.prototype.set = tf;
var nf = Zt;
function rf() {
  this.__data__ = [], this.size = 0;
}
var af = rf, sf = f3;
function of(n, a) {
  for (var i = n.length; i--; )
    if (sf(n[i][0], a))
      return i;
  return -1;
}
var I0 = of, lf = I0, cf = Array.prototype, uf = cf.splice;
function ff(n) {
  var a = this.__data__, i = lf(a, n);
  if (i < 0)
    return !1;
  var u = a.length - 1;
  return i == u ? a.pop() : uf.call(a, i, 1), --this.size, !0;
}
var hf = ff, gf = I0;
function pf(n) {
  var a = this.__data__, i = gf(a, n);
  return i < 0 ? void 0 : a[i][1];
}
var _f = pf, df = I0;
function vf(n) {
  return df(this.__data__, n) > -1;
}
var Cf = vf, yf = I0;
function mf(n, a) {
  var i = this.__data__, u = yf(i, n);
  return u < 0 ? (++this.size, i.push([n, a])) : i[u][1] = a, this;
}
var Lf = mf, xf = af, $f = hf, bf = _f, wf = Cf, Af = Lf;
function Wt(n) {
  var a = -1, i = n == null ? 0 : n.length;
  for (this.clear(); ++a < i; ) {
    var u = n[a];
    this.set(u[0], u[1]);
  }
}
Wt.prototype.clear = xf;
Wt.prototype.delete = $f;
Wt.prototype.get = bf;
Wt.prototype.has = wf;
Wt.prototype.set = Af;
var k0 = Wt, Sf = Ct, Mf = Ee, Tf = Sf(Mf, "Map"), L9 = Tf, C2 = nf, If = k0, kf = L9;
function Ef() {
  this.size = 0, this.__data__ = {
    hash: new C2(),
    map: new (kf || If)(),
    string: new C2()
  };
}
var Pf = Ef;
function Of(n) {
  var a = typeof n;
  return a == "string" || a == "number" || a == "symbol" || a == "boolean" ? n !== "__proto__" : n === null;
}
var Df = Of, Rf = Df;
function Bf(n, a) {
  var i = n.__data__;
  return Rf(a) ? i[typeof a == "string" ? "string" : "hash"] : i.map;
}
var E0 = Bf, Ff = E0;
function Nf(n) {
  var a = Ff(this, n).delete(n);
  return this.size -= a ? 1 : 0, a;
}
var Kf = Nf, Uf = E0;
function Zf(n) {
  return Uf(this, n).get(n);
}
var Wf = Zf, zf = E0;
function Qf(n) {
  return zf(this, n).has(n);
}
var Hf = Qf, Gf = E0;
function Yf(n, a) {
  var i = Gf(this, n), u = i.size;
  return i.set(n, a), this.size += i.size == u ? 0 : 1, this;
}
var Vf = Yf, Xf = Pf, qf = Kf, jf = Wf, Jf = Hf, eh = Vf;
function zt(n) {
  var a = -1, i = n == null ? 0 : n.length;
  for (this.clear(); ++a < i; ) {
    var u = n[a];
    this.set(u[0], u[1]);
  }
}
zt.prototype.clear = Xf;
zt.prototype.delete = qf;
zt.prototype.get = jf;
zt.prototype.has = Jf;
zt.prototype.set = eh;
var h3 = zt, g3 = h3, th = "Expected a function";
function x9(n, a) {
  if (typeof n != "function" || a != null && typeof a != "function")
    throw new TypeError(th);
  var i = function() {
    var u = arguments, f = a ? a.apply(this, u) : u[0], g = i.cache;
    if (g.has(f))
      return g.get(f);
    var d = n.apply(this, u);
    return i.cache = g.set(f, d) || g, d;
  };
  return i.cache = new (x9.Cache || g3)(), i;
}
x9.Cache = g3;
var nh = x9, rh = nh, ih = 500;
function ah(n) {
  var a = rh(n, function(u) {
    return i.size === ih && i.clear(), u;
  }), i = a.cache;
  return a;
}
var sh = ah, oh = sh, lh = /[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g, ch = /\\(\\)?/g, uh = oh(function(n) {
  var a = [];
  return n.charCodeAt(0) === 46 && a.push(""), n.replace(lh, function(i, u, f, g) {
    a.push(f ? g.replace(ch, "$1") : u || i);
  }), a;
}), fh = uh;
function hh(n, a) {
  for (var i = -1, u = n == null ? 0 : n.length, f = Array(u); ++i < u; )
    f[i] = a(n[i], i, n);
  return f;
}
var gh = hh, y2 = M0, ph = gh, _h = Kt, dh = m9, vh = 1 / 0, m2 = y2 ? y2.prototype : void 0, L2 = m2 ? m2.toString : void 0;
function p3(n) {
  if (typeof n == "string")
    return n;
  if (_h(n))
    return ph(n, p3) + "";
  if (dh(n))
    return L2 ? L2.call(n) : "";
  var a = n + "";
  return a == "0" && 1 / n == -vh ? "-0" : a;
}
var Ch = p3, yh = Ch;
function mh(n) {
  return n == null ? "" : yh(n);
}
var Lh = mh, xh = Kt, $h = Tu, bh = fh, wh = Lh;
function Ah(n, a) {
  return xh(n) ? n : $h(n, a) ? [n] : bh(wh(n));
}
var Sh = Ah, Mh = 9007199254740991, Th = /^(?:0|[1-9]\d*)$/;
function Ih(n, a) {
  var i = typeof n;
  return a = a ?? Mh, !!a && (i == "number" || i != "symbol" && Th.test(n)) && n > -1 && n % 1 == 0 && n < a;
}
var _3 = Ih, kh = m9, Eh = 1 / 0;
function Ph(n) {
  if (typeof n == "string" || kh(n))
    return n;
  var a = n + "";
  return a == "0" && 1 / n == -Eh ? "-0" : a;
}
var Oh = Ph, Dh = y9, Rh = Sh, Bh = _3, x2 = Nt, Fh = Oh;
function Nh(n, a, i, u) {
  if (!x2(n))
    return n;
  a = Rh(a, n);
  for (var f = -1, g = a.length, d = g - 1, p = n; p != null && ++f < g; ) {
    var m = Fh(a[f]), S = i;
    if (m === "__proto__" || m === "constructor" || m === "prototype")
      return n;
    if (f != d) {
      var x = p[m];
      S = u ? u(x, m, p) : void 0, S === void 0 && (S = x2(x) ? x : Bh(a[f + 1]) ? [] : {});
    }
    Dh(p, m, S), p = p[m];
  }
  return n;
}
var Kh = Nh, Uh = Kh;
function Zh(n, a, i) {
  return n == null ? n : Uh(n, a, i);
}
var Wh = Zh;
const u9 = /* @__PURE__ */ a3(Wh);
var zh = k0;
function Qh() {
  this.__data__ = new zh(), this.size = 0;
}
var Hh = Qh;
function Gh(n) {
  var a = this.__data__, i = a.delete(n);
  return this.size = a.size, i;
}
var Yh = Gh;
function Vh(n) {
  return this.__data__.get(n);
}
var Xh = Vh;
function qh(n) {
  return this.__data__.has(n);
}
var jh = qh, Jh = k0, eg = L9, tg = h3, ng = 200;
function rg(n, a) {
  var i = this.__data__;
  if (i instanceof Jh) {
    var u = i.__data__;
    if (!eg || u.length < ng - 1)
      return u.push([n, a]), this.size = ++i.size, this;
    i = this.__data__ = new tg(u);
  }
  return i.set(n, a), this.size = i.size, this;
}
var ig = rg, ag = k0, sg = Hh, og = Yh, lg = Xh, cg = jh, ug = ig;
function Qt(n) {
  var a = this.__data__ = new ag(n);
  this.size = a.size;
}
Qt.prototype.clear = sg;
Qt.prototype.delete = og;
Qt.prototype.get = lg;
Qt.prototype.has = cg;
Qt.prototype.set = ug;
var fg = Qt;
function hg(n, a) {
  for (var i = -1, u = n == null ? 0 : n.length; ++i < u && a(n[i], i, n) !== !1; )
    ;
  return n;
}
var gg = hg, pg = y9, _g = u3;
function dg(n, a, i, u) {
  var f = !i;
  i || (i = {});
  for (var g = -1, d = a.length; ++g < d; ) {
    var p = a[g], m = u ? u(i[p], n[p], p, i, n) : void 0;
    m === void 0 && (m = n[p]), f ? _g(i, p, m) : pg(i, p, m);
  }
  return i;
}
var P0 = dg;
function vg(n, a) {
  for (var i = -1, u = Array(n); ++i < n; )
    u[i] = a(i);
  return u;
}
var Cg = vg, yg = Cn, mg = Ut, Lg = "[object Arguments]";
function xg(n) {
  return mg(n) && yg(n) == Lg;
}
var $g = xg, $2 = $g, bg = Ut, d3 = Object.prototype, wg = d3.hasOwnProperty, Ag = d3.propertyIsEnumerable, Sg = $2(function() {
  return arguments;
}()) ? $2 : function(n) {
  return bg(n) && wg.call(n, "callee") && !Ag.call(n, "callee");
}, Mg = Sg, m0 = { exports: {} };
function Tg() {
  return !1;
}
var Ig = Tg;
m0.exports;
(function(n, a) {
  var i = Ee, u = Ig, f = a && !a.nodeType && a, g = f && !0 && n && !n.nodeType && n, d = g && g.exports === f, p = d ? i.Buffer : void 0, m = p ? p.isBuffer : void 0, S = m || u;
  n.exports = S;
})(m0, m0.exports);
var v3 = m0.exports, kg = 9007199254740991;
function Eg(n) {
  return typeof n == "number" && n > -1 && n % 1 == 0 && n <= kg;
}
var C3 = Eg, Pg = Cn, Og = C3, Dg = Ut, Rg = "[object Arguments]", Bg = "[object Array]", Fg = "[object Boolean]", Ng = "[object Date]", Kg = "[object Error]", Ug = "[object Function]", Zg = "[object Map]", Wg = "[object Number]", zg = "[object Object]", Qg = "[object RegExp]", Hg = "[object Set]", Gg = "[object String]", Yg = "[object WeakMap]", Vg = "[object ArrayBuffer]", Xg = "[object DataView]", qg = "[object Float32Array]", jg = "[object Float64Array]", Jg = "[object Int8Array]", ep = "[object Int16Array]", tp = "[object Int32Array]", np = "[object Uint8Array]", rp = "[object Uint8ClampedArray]", ip = "[object Uint16Array]", ap = "[object Uint32Array]", C1 = {};
C1[qg] = C1[jg] = C1[Jg] = C1[ep] = C1[tp] = C1[np] = C1[rp] = C1[ip] = C1[ap] = !0;
C1[Rg] = C1[Bg] = C1[Vg] = C1[Fg] = C1[Xg] = C1[Ng] = C1[Kg] = C1[Ug] = C1[Zg] = C1[Wg] = C1[zg] = C1[Qg] = C1[Hg] = C1[Gg] = C1[Yg] = !1;
function sp(n) {
  return Dg(n) && Og(n.length) && !!C1[Pg(n)];
}
var op = sp;
function lp(n) {
  return function(a) {
    return n(a);
  };
}
var $9 = lp, L0 = { exports: {} };
L0.exports;
(function(n, a) {
  var i = s3, u = a && !a.nodeType && a, f = u && !0 && n && !n.nodeType && n, g = f && f.exports === u, d = g && i.process, p = function() {
    try {
      var m = f && f.require && f.require("util").types;
      return m || d && d.binding && d.binding("util");
    } catch {
    }
  }();
  n.exports = p;
})(L0, L0.exports);
var b9 = L0.exports, cp = op, up = $9, b2 = b9, w2 = b2 && b2.isTypedArray, fp = w2 ? up(w2) : cp, hp = fp, gp = Cg, pp = Mg, _p = Kt, dp = v3, vp = _3, Cp = hp, yp = Object.prototype, mp = yp.hasOwnProperty;
function Lp(n, a) {
  var i = _p(n), u = !i && pp(n), f = !i && !u && dp(n), g = !i && !u && !f && Cp(n), d = i || u || f || g, p = d ? gp(n.length, String) : [], m = p.length;
  for (var S in n)
    (a || mp.call(n, S)) && !(d && // Safari 9 has enumerable `arguments.length` in strict mode.
    (S == "length" || // Node.js 0.10 has enumerable non-index properties on buffers.
    f && (S == "offset" || S == "parent") || // PhantomJS 2 has enumerable non-index properties on typed arrays.
    g && (S == "buffer" || S == "byteLength" || S == "byteOffset") || // Skip index properties.
    vp(S, m))) && p.push(S);
  return p;
}
var y3 = Lp, xp = Object.prototype;
function $p(n) {
  var a = n && n.constructor, i = typeof a == "function" && a.prototype || xp;
  return n === i;
}
var w9 = $p;
function bp(n, a) {
  return function(i) {
    return n(a(i));
  };
}
var m3 = bp, wp = m3, Ap = wp(Object.keys, Object), Sp = Ap, Mp = w9, Tp = Sp, Ip = Object.prototype, kp = Ip.hasOwnProperty;
function Ep(n) {
  if (!Mp(n))
    return Tp(n);
  var a = [];
  for (var i in Object(n))
    kp.call(n, i) && i != "constructor" && a.push(i);
  return a;
}
var Pp = Ep, Op = l3, Dp = C3;
function Rp(n) {
  return n != null && Dp(n.length) && !Op(n);
}
var L3 = Rp, Bp = y3, Fp = Pp, Np = L3;
function Kp(n) {
  return Np(n) ? Bp(n) : Fp(n);
}
var A9 = Kp, Up = P0, Zp = A9;
function Wp(n, a) {
  return n && Up(a, Zp(a), n);
}
var zp = Wp;
function Qp(n) {
  var a = [];
  if (n != null)
    for (var i in Object(n))
      a.push(i);
  return a;
}
var Hp = Qp, Gp = Nt, Yp = w9, Vp = Hp, Xp = Object.prototype, qp = Xp.hasOwnProperty;
function jp(n) {
  if (!Gp(n))
    return Vp(n);
  var a = Yp(n), i = [];
  for (var u in n)
    u == "constructor" && (a || !qp.call(n, u)) || i.push(u);
  return i;
}
var Jp = jp, e_ = y3, t_ = Jp, n_ = L3;
function r_(n) {
  return n_(n) ? e_(n, !0) : t_(n);
}
var S9 = r_, i_ = P0, a_ = S9;
function s_(n, a) {
  return n && i_(a, a_(a), n);
}
var o_ = s_, x0 = { exports: {} };
x0.exports;
(function(n, a) {
  var i = Ee, u = a && !a.nodeType && a, f = u && !0 && n && !n.nodeType && n, g = f && f.exports === u, d = g ? i.Buffer : void 0, p = d ? d.allocUnsafe : void 0;
  function m(S, x) {
    if (x)
      return S.slice();
    var M = S.length, D = p ? p(M) : new S.constructor(M);
    return S.copy(D), D;
  }
  n.exports = m;
})(x0, x0.exports);
var l_ = x0.exports;
function c_(n, a) {
  var i = -1, u = n.length;
  for (a || (a = Array(u)); ++i < u; )
    a[i] = n[i];
  return a;
}
var u_ = c_;
function f_(n, a) {
  for (var i = -1, u = n == null ? 0 : n.length, f = 0, g = []; ++i < u; ) {
    var d = n[i];
    a(d, i, n) && (g[f++] = d);
  }
  return g;
}
var h_ = f_;
function g_() {
  return [];
}
var x3 = g_, p_ = h_, __ = x3, d_ = Object.prototype, v_ = d_.propertyIsEnumerable, A2 = Object.getOwnPropertySymbols, C_ = A2 ? function(n) {
  return n == null ? [] : (n = Object(n), p_(A2(n), function(a) {
    return v_.call(n, a);
  }));
} : __, M9 = C_, y_ = P0, m_ = M9;
function L_(n, a) {
  return y_(n, m_(n), a);
}
var x_ = L_;
function $_(n, a) {
  for (var i = -1, u = a.length, f = n.length; ++i < u; )
    n[f + i] = a[i];
  return n;
}
var $3 = $_, b_ = m3, w_ = b_(Object.getPrototypeOf, Object), b3 = w_, A_ = $3, S_ = b3, M_ = M9, T_ = x3, I_ = Object.getOwnPropertySymbols, k_ = I_ ? function(n) {
  for (var a = []; n; )
    A_(a, M_(n)), n = S_(n);
  return a;
} : T_, w3 = k_, E_ = P0, P_ = w3;
function O_(n, a) {
  return E_(n, P_(n), a);
}
var D_ = O_, R_ = $3, B_ = Kt;
function F_(n, a, i) {
  var u = a(n);
  return B_(n) ? u : R_(u, i(n));
}
var A3 = F_, N_ = A3, K_ = M9, U_ = A9;
function Z_(n) {
  return N_(n, U_, K_);
}
var W_ = Z_, z_ = A3, Q_ = w3, H_ = S9;
function G_(n) {
  return z_(n, H_, Q_);
}
var Y_ = G_, V_ = Ct, X_ = Ee, q_ = V_(X_, "DataView"), j_ = q_, J_ = Ct, ed = Ee, td = J_(ed, "Promise"), nd = td, rd = Ct, id = Ee, ad = rd(id, "Set"), sd = ad, od = Ct, ld = Ee, cd = od(ld, "WeakMap"), ud = cd, f9 = j_, h9 = L9, g9 = nd, p9 = sd, _9 = ud, S3 = Cn, Ht = c3, S2 = "[object Map]", fd = "[object Object]", M2 = "[object Promise]", T2 = "[object Set]", I2 = "[object WeakMap]", k2 = "[object DataView]", hd = Ht(f9), gd = Ht(h9), pd = Ht(g9), _d = Ht(p9), dd = Ht(_9), _t = S3;
(f9 && _t(new f9(new ArrayBuffer(1))) != k2 || h9 && _t(new h9()) != S2 || g9 && _t(g9.resolve()) != M2 || p9 && _t(new p9()) != T2 || _9 && _t(new _9()) != I2) && (_t = function(n) {
  var a = S3(n), i = a == fd ? n.constructor : void 0, u = i ? Ht(i) : "";
  if (u)
    switch (u) {
      case hd:
        return k2;
      case gd:
        return S2;
      case pd:
        return M2;
      case _d:
        return T2;
      case dd:
        return I2;
    }
  return a;
});
var T9 = _t, vd = Object.prototype, Cd = vd.hasOwnProperty;
function yd(n) {
  var a = n.length, i = new n.constructor(a);
  return a && typeof n[0] == "string" && Cd.call(n, "index") && (i.index = n.index, i.input = n.input), i;
}
var md = yd, Ld = Ee, xd = Ld.Uint8Array, $d = xd, E2 = $d;
function bd(n) {
  var a = new n.constructor(n.byteLength);
  return new E2(a).set(new E2(n)), a;
}
var I9 = bd, wd = I9;
function Ad(n, a) {
  var i = a ? wd(n.buffer) : n.buffer;
  return new n.constructor(i, n.byteOffset, n.byteLength);
}
var Sd = Ad, Md = /\w*$/;
function Td(n) {
  var a = new n.constructor(n.source, Md.exec(n));
  return a.lastIndex = n.lastIndex, a;
}
var Id = Td, P2 = M0, O2 = P2 ? P2.prototype : void 0, D2 = O2 ? O2.valueOf : void 0;
function kd(n) {
  return D2 ? Object(D2.call(n)) : {};
}
var Ed = kd, Pd = I9;
function Od(n, a) {
  var i = a ? Pd(n.buffer) : n.buffer;
  return new n.constructor(i, n.byteOffset, n.length);
}
var Dd = Od, Rd = I9, Bd = Sd, Fd = Id, Nd = Ed, Kd = Dd, Ud = "[object Boolean]", Zd = "[object Date]", Wd = "[object Map]", zd = "[object Number]", Qd = "[object RegExp]", Hd = "[object Set]", Gd = "[object String]", Yd = "[object Symbol]", Vd = "[object ArrayBuffer]", Xd = "[object DataView]", qd = "[object Float32Array]", jd = "[object Float64Array]", Jd = "[object Int8Array]", ev = "[object Int16Array]", tv = "[object Int32Array]", nv = "[object Uint8Array]", rv = "[object Uint8ClampedArray]", iv = "[object Uint16Array]", av = "[object Uint32Array]";
function sv(n, a, i) {
  var u = n.constructor;
  switch (a) {
    case Vd:
      return Rd(n);
    case Ud:
    case Zd:
      return new u(+n);
    case Xd:
      return Bd(n, i);
    case qd:
    case jd:
    case Jd:
    case ev:
    case tv:
    case nv:
    case rv:
    case iv:
    case av:
      return Kd(n, i);
    case Wd:
      return new u();
    case zd:
    case Gd:
      return new u(n);
    case Qd:
      return Fd(n);
    case Hd:
      return new u();
    case Yd:
      return Nd(n);
  }
}
var ov = sv, lv = Nt, R2 = Object.create, cv = function() {
  function n() {
  }
  return function(a) {
    if (!lv(a))
      return {};
    if (R2)
      return R2(a);
    n.prototype = a;
    var i = new n();
    return n.prototype = void 0, i;
  };
}(), uv = cv, fv = uv, hv = b3, gv = w9;
function pv(n) {
  return typeof n.constructor == "function" && !gv(n) ? fv(hv(n)) : {};
}
var _v = pv, dv = T9, vv = Ut, Cv = "[object Map]";
function yv(n) {
  return vv(n) && dv(n) == Cv;
}
var mv = yv, Lv = mv, xv = $9, B2 = b9, F2 = B2 && B2.isMap, $v = F2 ? xv(F2) : Lv, bv = $v, wv = T9, Av = Ut, Sv = "[object Set]";
function Mv(n) {
  return Av(n) && wv(n) == Sv;
}
var Tv = Mv, Iv = Tv, kv = $9, N2 = b9, K2 = N2 && N2.isSet, Ev = K2 ? kv(K2) : Iv, Pv = Ev, Ov = fg, Dv = gg, Rv = y9, Bv = zp, Fv = o_, Nv = l_, Kv = u_, Uv = x_, Zv = D_, Wv = W_, zv = Y_, Qv = T9, Hv = md, Gv = ov, Yv = _v, Vv = Kt, Xv = v3, qv = bv, jv = Nt, Jv = Pv, eC = A9, tC = S9, nC = 1, rC = 2, iC = 4, M3 = "[object Arguments]", aC = "[object Array]", sC = "[object Boolean]", oC = "[object Date]", lC = "[object Error]", T3 = "[object Function]", cC = "[object GeneratorFunction]", uC = "[object Map]", fC = "[object Number]", I3 = "[object Object]", hC = "[object RegExp]", gC = "[object Set]", pC = "[object String]", _C = "[object Symbol]", dC = "[object WeakMap]", vC = "[object ArrayBuffer]", CC = "[object DataView]", yC = "[object Float32Array]", mC = "[object Float64Array]", LC = "[object Int8Array]", xC = "[object Int16Array]", $C = "[object Int32Array]", bC = "[object Uint8Array]", wC = "[object Uint8ClampedArray]", AC = "[object Uint16Array]", SC = "[object Uint32Array]", d1 = {};
d1[M3] = d1[aC] = d1[vC] = d1[CC] = d1[sC] = d1[oC] = d1[yC] = d1[mC] = d1[LC] = d1[xC] = d1[$C] = d1[uC] = d1[fC] = d1[I3] = d1[hC] = d1[gC] = d1[pC] = d1[_C] = d1[bC] = d1[wC] = d1[AC] = d1[SC] = !0;
d1[lC] = d1[T3] = d1[dC] = !1;
function p0(n, a, i, u, f, g) {
  var d, p = a & nC, m = a & rC, S = a & iC;
  if (i && (d = f ? i(n, u, f, g) : i(n)), d !== void 0)
    return d;
  if (!jv(n))
    return n;
  var x = Vv(n);
  if (x) {
    if (d = Hv(n), !p)
      return Kv(n, d);
  } else {
    var M = Qv(n), D = M == T3 || M == cC;
    if (Xv(n))
      return Nv(n, p);
    if (M == I3 || M == M3 || D && !f) {
      if (d = m || D ? {} : Yv(n), !p)
        return m ? Zv(n, Fv(d, n)) : Uv(n, Bv(d, n));
    } else {
      if (!d1[M])
        return f ? n : {};
      d = Gv(n, M, p);
    }
  }
  g || (g = new Ov());
  var z = g.get(n);
  if (z)
    return z;
  g.set(n, d), Jv(n) ? n.forEach(function(n1) {
    d.add(p0(n1, a, i, n1, n, g));
  }) : qv(n) && n.forEach(function(n1, i1) {
    d.set(i1, p0(n1, a, i, i1, n, g));
  });
  var t1 = S ? m ? zv : Wv : m ? tC : eC, p1 = x ? void 0 : t1(n);
  return Dv(p1 || n, function(n1, i1) {
    p1 && (i1 = n1, n1 = n[i1]), Rv(d, i1, p0(n1, a, i, i1, n, g));
  }), d;
}
var MC = p0, TC = MC, IC = 1, kC = 4;
function EC(n) {
  return TC(n, IC | kC);
}
var PC = EC;
const OC = /* @__PURE__ */ a3(PC);
var DC = /* @__PURE__ */ I("<button>");
const RC = (n) => (() => {
  var a = DC();
  return dt(a, "click", n.onClick, !0), F(a, () => n.children), P1((i) => {
    var u = n.style, f = `klinecharts-pro-button ${n.type ?? "confirm"} ${n.class ?? ""}`;
    return i.e = Ft(a, u, i.e), f !== i.t && vt(a, i.t = f), i;
  }, {
    e: void 0,
    t: void 0
  }), a;
})();
ke(["click"]);
var BC = /* @__PURE__ */ I('<svg viewBox="0 0 1024 1024"class=icon><path d="M810.666667 128H213.333333c-46.933333 0-85.333333 38.4-85.333333 85.333333v597.333334c0 46.933333 38.4 85.333333 85.333333 85.333333h597.333334c46.933333 0 85.333333-38.4 85.333333-85.333333V213.333333c0-46.933333-38.4-85.333333-85.333333-85.333333z m-353.706667 567.04a42.496 42.496 0 0 1-60.16 0L243.626667 541.866667c-8.106667-8.106667-12.373333-18.773333-12.373334-29.866667s4.693333-22.186667 12.373334-29.866667a42.496 42.496 0 0 1 60.16 0L426.666667 604.586667l293.546666-293.546667a42.496 42.496 0 1 1 60.16 60.16l-323.413333 323.84z">'), FC = /* @__PURE__ */ I('<svg viewBox="0 0 1024 1024"class=icon><path d="M245.333333 128h533.333334A117.333333 117.333333 0 0 1 896 245.333333v533.333334A117.333333 117.333333 0 0 1 778.666667 896H245.333333A117.333333 117.333333 0 0 1 128 778.666667V245.333333A117.333333 117.333333 0 0 1 245.333333 128z m0 64c-29.44 0-53.333333 23.893333-53.333333 53.333333v533.333334c0 29.44 23.893333 53.333333 53.333333 53.333333h533.333334c29.44 0 53.333333-23.893333 53.333333-53.333333V245.333333c0-29.44-23.893333-53.333333-53.333333-53.333333H245.333333z">'), NC = /* @__PURE__ */ I("<div>"), KC = /* @__PURE__ */ I("<span class=label>");
const UC = () => BC(), ZC = () => FC(), U2 = (n) => {
  const [a, i] = V(n.checked ?? !1);
  return Ie(() => {
    "checked" in n && i(n.checked);
  }), (() => {
    var u = NC();
    return u.$$click = (f) => {
      const g = !a();
      n.onChange && n.onChange(g), i(g);
    }, F(u, (() => {
      var f = A1(() => !!a());
      return () => f() ? B(UC, {}) : B(ZC, {});
    })(), null), F(u, (() => {
      var f = A1(() => !!n.label);
      return () => f() && (() => {
        var g = KC();
        return F(g, () => n.label), g;
      })();
    })(), null), P1((f) => {
      var g = n.style, d = `klinecharts-pro-checkbox ${a() && "checked" || ""} ${n.class || ""}`;
      return f.e = Ft(u, g, f.e), d !== f.t && vt(u, f.t = d), f;
    }, {
      e: void 0,
      t: void 0
    }), u;
  })();
};
ke(["click"]);
var WC = /* @__PURE__ */ I("<div class=klinecharts-pro-loading><i class=circle1></i><i class=circle2></i><i class=circle3>");
const k3 = () => WC();
var zC = /* @__PURE__ */ I('<div class=klinecharts-pro-empty><svg class=icon viewBox="0 0 1024 1024"><path d="M855.6 427.2H168.5c-12.7 0-24.4 6.9-30.6 18L4.4 684.7C1.5 689.9 0 695.8 0 701.8v287.1c0 19.4 15.7 35.1 35.1 35.1H989c19.4 0 35.1-15.7 35.1-35.1V701.8c0-6-1.5-11.8-4.4-17.1L886.2 445.2c-6.2-11.1-17.9-18-30.6-18zM673.4 695.6c-16.5 0-30.8 11.5-34.3 27.7-12.7 58.5-64.8 102.3-127.2 102.3s-114.5-43.8-127.2-102.3c-3.5-16.1-17.8-27.7-34.3-27.7H119c-26.4 0-43.3-28-31.1-51.4l81.7-155.8c6.1-11.6 18-18.8 31.1-18.8h622.4c13 0 25 7.2 31.1 18.8l81.7 155.8c12.2 23.4-4.7 51.4-31.1 51.4H673.4zM819.9 209.5c-1-1.8-2.1-3.7-3.2-5.5-9.8-16.6-31.1-22.2-47.8-12.6L648.5 261c-17 9.8-22.7 31.6-12.6 48.4 0.9 1.4 1.7 2.9 2.5 4.4 9.5 17 31.2 22.8 48 13L807 257.3c16.7-9.7 22.4-31 12.9-47.8zM375.4 261.1L255 191.6c-16.7-9.6-38-4-47.8 12.6-1.1 1.8-2.1 3.6-3.2 5.5-9.5 16.8-3.8 38.1 12.9 47.8L337.3 327c16.9 9.7 38.6 4 48-13.1 0.8-1.5 1.7-2.9 2.5-4.4 10.2-16.8 4.5-38.6-12.4-48.4zM512 239.3h2.5c19.5 0.3 35.5-15.5 35.5-35.1v-139c0-19.3-15.6-34.9-34.8-35.1h-6.4C489.6 30.3 474 46 474 65.2v139c0 19.5 15.9 35.4 35.5 35.1h2.5z">');
const QC = () => zC();
var HC = /* @__PURE__ */ I("<ul>"), GC = /* @__PURE__ */ I("<li>");
const $0 = (n) => (() => {
  var a = HC();
  return F(a, B(Z1, {
    get when() {
      return n.loading;
    },
    get children() {
      return B(k3, {});
    }
  }), null), F(a, B(Z1, {
    get when() {
      var i;
      return !n.loading && !n.children && !((i = n.dataSource) != null && i.length);
    },
    get children() {
      return B(QC, {});
    }
  }), null), F(a, B(Z1, {
    get when() {
      return n.children;
    },
    get children() {
      return n.children;
    }
  }), null), F(a, B(Z1, {
    get when() {
      return !n.children;
    },
    get children() {
      var i;
      return (i = n.dataSource) == null ? void 0 : i.map((u) => {
        var f;
        return ((f = n.renderItem) == null ? void 0 : f.call(n, u)) ?? GC();
      });
    }
  }), null), P1((i) => {
    var u = n.style, f = `klinecharts-pro-list ${n.class ?? ""}`;
    return i.e = Ft(a, u, i.e), f !== i.t && vt(a, i.t = f), i;
  }, {
    e: void 0,
    t: void 0
  }), a;
})();
var YC = /* @__PURE__ */ I('<div class=klinecharts-pro-modal><div class=inner><div class=title-container><svg class=close-icon viewBox="0 0 1024 1024"><path d="M934.184927 199.723787 622.457206 511.452531l311.727721 311.703161c14.334473 14.229073 23.069415 33.951253 23.069415 55.743582 0 43.430138-35.178197 78.660524-78.735226 78.660524-21.664416 0-41.361013-8.865925-55.642275-23.069415L511.149121 622.838388 199.420377 934.490384c-14.204513 14.20349-33.901111 23.069415-55.642275 23.069415-43.482327 0-78.737272-35.230386-78.737272-78.660524 0-21.792329 8.864902-41.513486 23.094998-55.743582l311.677579-311.703161L88.135828 199.723787c-14.230096-14.255679-23.094998-33.92567-23.094998-55.642275 0-43.430138 35.254945-78.762855 78.737272-78.762855 21.741163 0 41.437761 8.813736 55.642275 23.069415l311.727721 311.727721L822.876842 88.389096c14.281261-14.255679 33.977859-23.069415 55.642275-23.069415 43.557028 0 78.735226 35.332716 78.735226 78.762855C957.254342 165.798117 948.5194 185.468109 934.184927 199.723787"></path></svg></div><div class=content-container>'), VC = /* @__PURE__ */ I("<div class=button-container>");
const yn = (n) => (() => {
  var a = YC(), i = a.firstChild, u = i.firstChild, f = u.firstChild, g = u.nextSibling;
  return F(u, () => n.title, f), dt(f, "click", n.onClose, !0), F(g, () => n.children), F(i, (() => {
    var d = A1(() => !!(n.buttons && n.buttons.length > 0));
    return () => d() && (() => {
      var p = VC();
      return F(p, () => n.buttons.map((m) => B(RC, i3(m, {
        get children() {
          return m.children;
        }
      })))), p;
    })();
  })(), null), P1(() => (n.width ? `${n.width ?? 400}px` : "") != null ? i.style.setProperty("width", n.width ? `${n.width ?? 400}px` : "") : i.style.removeProperty("width")), a;
})();
ke(["click"]);
var XC = /* @__PURE__ */ I("<div tabindex=0><div class=selector-container><span class=value></span><i class=arrow>"), qC = /* @__PURE__ */ I("<div class=drop-down-container><ul>"), jC = /* @__PURE__ */ I("<li>");
const E3 = (n) => {
  const [a, i] = V(!1);
  return (() => {
    var u = XC(), f = u.firstChild, g = f.firstChild;
    return u.addEventListener("blur", (d) => {
      i(!1);
    }), u.$$click = (d) => {
      i((p) => !p);
    }, F(g, () => n.value), F(u, (() => {
      var d = A1(() => !!(n.dataSource && n.dataSource.length > 0));
      return () => d() && (() => {
        var p = qC(), m = p.firstChild;
        return F(m, () => n.dataSource.map((S) => {
          const M = S[n.valueKey ?? "text"] ?? S;
          return (() => {
            var D = jC();
            return D.$$click = (z) => {
              var t1;
              z.stopPropagation(), n.value !== M && ((t1 = n.onSelected) == null || t1.call(n, S)), i(!1);
            }, F(D, M), D;
          })();
        })), p;
      })();
    })(), null), P1((d) => {
      var p = n.style, m = `klinecharts-pro-select ${n.class ?? ""} ${a() ? "klinecharts-pro-select-show" : ""}`;
      return d.e = Ft(u, p, d.e), m !== d.t && vt(u, d.t = m), d;
    }, {
      e: void 0,
      t: void 0
    }), u;
  })();
};
ke(["click"]);
var JC = /* @__PURE__ */ I("<span class=prefix>"), ey = /* @__PURE__ */ I("<span class=suffix>"), ty = /* @__PURE__ */ I("<div><input class=value>");
const P3 = (n) => {
  const a = i3({
    min: Number.MIN_SAFE_INTEGER,
    max: Number.MAX_SAFE_INTEGER
  }, n);
  let i;
  const [u, f] = V("normal");
  return (() => {
    var g = ty(), d = g.firstChild;
    return g.$$click = () => {
      i == null || i.focus();
    }, F(g, B(Z1, {
      get when() {
        return a.prefix;
      },
      get children() {
        var p = JC();
        return F(p, () => a.prefix), p;
      }
    }), d), d.addEventListener("change", (p) => {
      var S, x;
      const m = p.target.value;
      if ("precision" in a) {
        let M;
        const D = Math.max(0, Math.floor(a.precision));
        D <= 0 ? M = new RegExp(/^[1-9]\d*$/) : M = new RegExp("^\\d+\\.?\\d{0," + D + "}$"), (m === "" || M.test(m) && +m >= a.min && +m <= a.max) && ((S = a.onChange) == null || S.call(a, m === "" ? m : +m));
      } else
        (x = a.onChange) == null || x.call(a, m);
    }), d.addEventListener("blur", () => {
      f("normal");
    }), d.addEventListener("focus", () => {
      f("focus");
    }), C9((p) => {
      i = p;
    }, d), F(g, B(Z1, {
      get when() {
        return a.suffix;
      },
      get children() {
        var p = ey();
        return F(p, () => a.suffix), p;
      }
    }), null), P1((p) => {
      var m = a.style, S = `klinecharts-pro-input ${a.class ?? ""}`, x = u(), M = a.placeholder ?? "";
      return p.e = Ft(g, m, p.e), S !== p.t && vt(g, p.t = S), x !== p.a && ve(g, "data-status", p.a = x), M !== p.o && ve(d, "placeholder", p.o = M), p;
    }, {
      e: void 0,
      t: void 0,
      a: void 0,
      o: void 0
    }), P1(() => d.value = a.value), g;
  })();
};
ke(["click"]);
var ny = /* @__PURE__ */ I("<div><i class=thumb>");
const ry = (n) => (() => {
  var a = ny();
  return a.$$click = (i) => {
    n.onChange && n.onChange();
  }, P1((i) => {
    var u = n.style, f = `klinecharts-pro-switch ${n.open ? "turn-on" : "turn-off"} ${n.class ?? ""}`;
    return i.e = Ft(a, u, i.e), f !== i.t && vt(a, i.t = f), i;
  }, {
    e: void 0,
    t: void 0
  }), a;
})();
ke(["click"]);
const iy = "指标", ay = "主图指标", sy = "副图指标", oy = "设置", ly = "时区", cy = "截屏", uy = "全屏", fy = "退出全屏", hy = "保存", gy = "确定", py = "取消", _y = "MA(移动平均线)", dy = "EMA(指数平滑移动平均线)", vy = "SMA", Cy = "BOLL(布林线)", yy = "BBI(多空指数)", my = "SAR(停损点指向指标)", Ly = "VOL(成交量)", xy = "MACD(指数平滑异同移动平均线)", $y = "KDJ(随机指标)", by = "RSI(相对强弱指标)", wy = "BIAS(乖离率)", Ay = "BRAR(情绪指标)", Sy = "CCI(顺势指标)", My = "DMI(动向指标)", Ty = "CR(能量指标)", Iy = "PSY(心理线)", ky = "DMA(平行线差指标)", Ey = "TRIX(三重指数平滑平均线)", Py = "OBV(能量潮指标)", Oy = "VR(成交量变异率)", Dy = "WR(威廉指标)", Ry = "MTM(动量指标)", By = "EMV(简易波动指标)", Fy = "ROC(变动率指标)", Ny = "PVT(价量趋势指标)", Ky = "AO(动量震荡指标)", Uy = "世界统一时间", Zy = "(UTC-10) 檀香山", Wy = "(UTC-8) 朱诺", zy = "(UTC-7) 洛杉矶", Qy = "(UTC-5) 芝加哥", Hy = "(UTC-4) 多伦多", Gy = "(UTC-3) 圣保罗", Yy = "(UTC+1) 伦敦", Vy = "(UTC+2) 柏林", Xy = "(UTC+3) 巴林", qy = "(UTC+4) 迪拜", jy = "(UTC+5) 阿什哈巴德", Jy = "(UTC+6) 阿拉木图", em = "(UTC+7) 曼谷", tm = "(UTC+8) 上海", nm = "(UTC+9) 东京", rm = "(UTC+10) 悉尼", im = "(UTC+12) 诺福克岛", am = "水平直线", sm = "水平射线", om = "水平线段", lm = "垂直直线", cm = "垂直射线", um = "垂直线段", fm = "直线", hm = "射线", gm = "线段", pm = "箭头", _m = "价格线", dm = "价格通道线", vm = "平行直线", Cm = "斐波那契回调直线", ym = "斐波那契回调线段", mm = "斐波那契圆环", Lm = "斐波那契螺旋", xm = "斐波那契速度阻力扇", $m = "斐波那契趋势扩展", bm = "江恩箱", wm = "矩形", Am = "平行四边形", Sm = "圆", Mm = "三角形", Tm = "三浪", Im = "五浪", km = "八浪", Em = "任意浪", Pm = "ABCD形态", Om = "XABCD形态", Dm = "弱磁模式", Rm = "强磁模式", Bm = "商品搜索", Fm = "商品代码", Nm = "参数1", Km = "参数2", Um = "参数3", Zm = "参数4", Wm = "参数5", zm = "周期", Qm = "标准差", Hm = "蜡烛图类型", Gm = "全实心", Ym = "全空心", Vm = "涨空心", Xm = "跌空心", qm = "OHLC", jm = "面积图", Jm = "最新价显示", eL = "最高价显示", tL = "最低价显示", nL = "指标最新值显示", rL = "价格轴类型", iL = "线性轴", aL = "百分比轴", sL = "对数轴", oL = "倒置坐标", lL = "网格线显示", cL = "恢复默认", uL = {
  indicator: iy,
  main_indicator: ay,
  sub_indicator: sy,
  setting: oy,
  timezone: ly,
  screenshot: cy,
  full_screen: uy,
  exit_full_screen: fy,
  save: hy,
  confirm: gy,
  cancel: py,
  ma: _y,
  ema: dy,
  sma: vy,
  boll: Cy,
  bbi: yy,
  sar: my,
  vol: Ly,
  macd: xy,
  kdj: $y,
  rsi: by,
  bias: wy,
  brar: Ay,
  cci: Sy,
  dmi: My,
  cr: Ty,
  psy: Iy,
  dma: ky,
  trix: Ey,
  obv: Py,
  vr: Oy,
  wr: Dy,
  mtm: Ry,
  emv: By,
  roc: Fy,
  pvt: Ny,
  ao: Ky,
  utc: Uy,
  honolulu: Zy,
  juneau: Wy,
  los_angeles: zy,
  chicago: Qy,
  toronto: Hy,
  sao_paulo: Gy,
  london: Yy,
  berlin: Vy,
  bahrain: Xy,
  dubai: qy,
  ashkhabad: jy,
  almaty: Jy,
  bangkok: em,
  shanghai: tm,
  tokyo: nm,
  sydney: rm,
  norfolk: im,
  horizontal_straight_line: am,
  horizontal_ray_line: sm,
  horizontal_segment: om,
  vertical_straight_line: lm,
  vertical_ray_line: cm,
  vertical_segment: um,
  straight_line: fm,
  ray_line: hm,
  segment: gm,
  arrow: pm,
  price_line: _m,
  price_channel_line: dm,
  parallel_straight_line: vm,
  fibonacci_line: Cm,
  fibonacci_segment: ym,
  fibonacci_circle: mm,
  fibonacci_spiral: Lm,
  fibonacci_speed_resistance_fan: xm,
  fibonacci_extension: $m,
  gann_box: bm,
  rect: wm,
  parallelogram: Am,
  circle: Sm,
  triangle: Mm,
  three_waves: Tm,
  five_waves: Im,
  eight_waves: km,
  any_waves: Em,
  abcd: Pm,
  xabcd: Om,
  weak_magnet: Dm,
  strong_magnet: Rm,
  symbol_search: Bm,
  symbol_code: Fm,
  params_1: Nm,
  params_2: Km,
  params_3: Um,
  params_4: Zm,
  params_5: Wm,
  period: zm,
  standard_deviation: Qm,
  candle_type: Hm,
  candle_solid: Gm,
  candle_stroke: Ym,
  candle_up_stroke: Vm,
  candle_down_stroke: Xm,
  ohlc: qm,
  area: jm,
  last_price_show: Jm,
  high_price_show: eL,
  low_price_show: tL,
  indicator_last_value_show: nL,
  price_axis_type: rL,
  normal: iL,
  percentage: aL,
  log: sL,
  reverse_coordinate: oL,
  grid_show: lL,
  restore_default: cL
}, fL = "Indicator", hL = "Main Indicator", gL = "Sub Indicator", pL = "Setting", _L = "Timezone", dL = "Screenshot", vL = "Full Screen", CL = "Exit", yL = "Save", mL = "Confirm", LL = "Cancel", xL = "MA (Moving Average)", $L = "EMA (Exponential Moving Average)", bL = "SMA", wL = "BOLL (Bolinger Bands)", AL = "BBI (Bull And Bearlndex)", SL = "SAR (Stop and Reverse)", ML = "VOL (Volume)", TL = "MACD (Moving Average Convergence / Divergence)", IL = "KDJ (KDJ Index)", kL = "RSI (Relative Strength Index)", EL = "BIAS (Bias Ratio)", PL = "BRAR (Sentiment Indicator)", OL = "CCI (Commodity Channel Index)", DL = "DMI (Directional Movement Index)", RL = "CR (Уnergy index)", BL = "PSY (Psychological Line)", FL = "DMA (Different of Moving Average)", NL = "TRIX (Triple Exponentially Smoothed Moving Average)", KL = "OBV (On Balance Volume)", UL = "VR (Volatility Volume Ratio)", ZL = "WR (Williams %R)", WL = "MTM (Momentum Index)", zL = "EMV (Ease of Movement Value)", QL = "ROC (Price Rate of Change)", HL = "PVT (Price and Volume Trend)", GL = "AO (Awesome Oscillator)", YL = "UTC", VL = "(UTC-10) Honolulu", XL = "(UTC-8) Juneau", qL = "(UTC-7) Los Angeles", jL = "(UTC-5) Chicago", JL = "(UTC-4) Toronto", ex = "(UTC-3) Sao Paulo", tx = "(UTC+1) London", nx = "(UTC+2) Berlin", rx = "(UTC+3) Bahrain", ix = "(UTC+4) Dubai", ax = "(UTC+5) Ashkhabad", sx = "(UTC+6) Almaty", ox = "(UTC+7) Bangkok", lx = "(UTC+8) Shanghai", cx = "(UTC+9) Tokyo", ux = "(UTC+10) Sydney", fx = "(UTC+12) Norfolk", hx = "Horizontal Line", gx = "Horizontal Ray", px = "Horizontal Segment", _x = "Vertical Line", dx = "Vertical Ray", vx = "Vertical Segment", Cx = "Trend Line", yx = "Ray", mx = "Segment", Lx = "Arrow", xx = "Price Line", $x = "Price Channel Line", bx = "Parallel Line", wx = "Fibonacci Line", Ax = "Fibonacci Segment", Sx = "Fibonacci Circle", Mx = "Fibonacci Spiral", Tx = "Fibonacci Sector", Ix = "Fibonacci Extension", kx = "Gann Box", Ex = "Rect", Px = "Parallelogram", Ox = "Circle", Dx = "Triangle", Rx = "Three Waves", Bx = "Five Waves", Fx = "Eight Waves", Nx = "Any Waves", Kx = "ABCD Pattern", Ux = "XABCD Pattern", Zx = "Weak Magnet", Wx = "Strong Magnet", zx = "Symbol Search", Qx = "Symbol Code", Hx = "Parameter 1", Gx = "Parameter 2", Yx = "Parameter 3", Vx = "Parameter 4", Xx = "Parameter 5", qx = "Period", jx = "Standard Deviation", Jx = "Candle Type", e$ = "Candle Solid", t$ = "Candle Stroke", n$ = "Candle Up Stroke", r$ = "Candle Down Stroke", i$ = "OHLC", a$ = "Area", s$ = "Show Last Price", o$ = "Show Highest Price", l$ = "Show Lowest Price", c$ = "Show indicator's last value", u$ = "Price Axis Type", f$ = "Normal", h$ = "Percentage", g$ = "Log", p$ = "Reverse Coordinate", _$ = "Show Grids", d$ = "Restore Defaults", v$ = {
  indicator: fL,
  main_indicator: hL,
  sub_indicator: gL,
  setting: pL,
  timezone: _L,
  screenshot: dL,
  full_screen: vL,
  exit_full_screen: CL,
  save: yL,
  confirm: mL,
  cancel: LL,
  ma: xL,
  ema: $L,
  sma: bL,
  boll: wL,
  bbi: AL,
  sar: SL,
  vol: ML,
  macd: TL,
  kdj: IL,
  rsi: kL,
  bias: EL,
  brar: PL,
  cci: OL,
  dmi: DL,
  cr: RL,
  psy: BL,
  dma: FL,
  trix: NL,
  obv: KL,
  vr: UL,
  wr: ZL,
  mtm: WL,
  emv: zL,
  roc: QL,
  pvt: HL,
  ao: GL,
  utc: YL,
  honolulu: VL,
  juneau: XL,
  los_angeles: qL,
  chicago: jL,
  toronto: JL,
  sao_paulo: ex,
  london: tx,
  berlin: nx,
  bahrain: rx,
  dubai: ix,
  ashkhabad: ax,
  almaty: sx,
  bangkok: ox,
  shanghai: lx,
  tokyo: cx,
  sydney: ux,
  norfolk: fx,
  horizontal_straight_line: hx,
  horizontal_ray_line: gx,
  horizontal_segment: px,
  vertical_straight_line: _x,
  vertical_ray_line: dx,
  vertical_segment: vx,
  straight_line: Cx,
  ray_line: yx,
  segment: mx,
  arrow: Lx,
  price_line: xx,
  price_channel_line: $x,
  parallel_straight_line: bx,
  fibonacci_line: wx,
  fibonacci_segment: Ax,
  fibonacci_circle: Sx,
  fibonacci_spiral: Mx,
  fibonacci_speed_resistance_fan: Tx,
  fibonacci_extension: Ix,
  gann_box: kx,
  rect: Ex,
  parallelogram: Px,
  circle: Ox,
  triangle: Dx,
  three_waves: Rx,
  five_waves: Bx,
  eight_waves: Fx,
  any_waves: Nx,
  abcd: Kx,
  xabcd: Ux,
  weak_magnet: Zx,
  strong_magnet: Wx,
  symbol_search: zx,
  symbol_code: Qx,
  params_1: Hx,
  params_2: Gx,
  params_3: Yx,
  params_4: Vx,
  params_5: Xx,
  period: qx,
  standard_deviation: jx,
  candle_type: Jx,
  candle_solid: e$,
  candle_stroke: t$,
  candle_up_stroke: n$,
  candle_down_stroke: r$,
  ohlc: i$,
  area: a$,
  last_price_show: s$,
  high_price_show: o$,
  low_price_show: l$,
  indicator_last_value_show: c$,
  price_axis_type: u$,
  normal: f$,
  percentage: h$,
  log: g$,
  reverse_coordinate: p$,
  grid_show: _$,
  restore_default: d$
}, O3 = {
  "zh-CN": uL,
  "en-US": v$
};
function yw(n, a) {
  O3[n] = a;
}
const P = (n, a) => {
  var i;
  return ((i = O3[a]) == null ? void 0 : i[n]) ?? n;
};
var C$ = /* @__PURE__ */ I("<img alt=symbol>"), y$ = /* @__PURE__ */ I("<div class=symbol><span>"), m$ = /* @__PURE__ */ I('<div class=klinecharts-pro-period-bar><div class=menu-container><svg viewBox="0 0 1024 1024"><path d="M192.037 287.953h640.124c17.673 0 32-14.327 32-32s-14.327-32-32-32H192.037c-17.673 0-32 14.327-32 32s14.327 32 32 32zM832.161 479.169H438.553c-17.673 0-32 14.327-32 32s14.327 32 32 32h393.608c17.673 0 32-14.327 32-32s-14.327-32-32-32zM832.161 735.802H192.037c-17.673 0-32 14.327-32 32s14.327 32 32 32h640.124c17.673 0 32-14.327 32-32s-14.327-32-32-32zM319.028 351.594l-160 160 160 160z"></path></svg></div><div class="item tools"><svg viewBox="0 0 20 20"><path d=M15.873,20L3.65079,20C1.5873,20,0,18.3871,0,16.2903L0,3.70968C-3.78442e-7,1.6129,1.5873,0,3.65079,0L15.873,0C17.9365,0,19.5238,1.6129,19.5238,3.70968C19.5238,4.35484,19.2063,4.51613,18.5714,4.51613C17.9365,4.51613,17.619,4.19355,17.619,3.70968C17.619,2.74194,16.8254,1.93548,15.873,1.93548L3.65079,1.93548C2.69841,1.93548,1.90476,2.74194,1.90476,3.70968L1.90476,16.2903C1.90476,17.2581,2.69841,18.0645,3.65079,18.0645L15.873,18.0645C16.8254,18.0645,17.619,17.2581,17.619,16.2903C17.619,15.8065,18.0952,15.3226,18.5714,15.3226C19.0476,15.3226,19.5238,15.8065,19.5238,16.2903C19.5238,18.2258,17.9365,20,15.873,20ZM14.9206,12.9032C14.7619,12.9032,14.4444,12.9032,14.2857,12.7419L11.2698,9.35484C10.9524,9.03226,10.9524,8.54839,11.2698,8.22581C11.5873,7.90323,12.0635,7.90323,12.381,8.22581L15.3968,11.6129C15.7143,11.9355,15.7143,12.4194,15.3968,12.7419C15.3968,12.9032,15.2381,12.9032,14.9206,12.9032ZM11.4286,13.2258C11.2698,13.2258,11.1111,13.2258,10.9524,13.0645C10.6349,12.7419,10.6349,12.4194,10.9524,12.0968L15.0794,7.74193C15.3968,7.41935,15.7143,7.41935,16.0317,7.74193C16.3492,8.06452,16.3492,8.3871,16.0317,8.70968L11.9048,13.0645C11.746,13.2258,11.5873,13.2258,11.4286,13.2258ZM10.3175,3.70968C10.6349,3.70968,11.4286,3.87097,11.4286,4.67742C11.4286,5.32258,10.4762,5.16129,10.1587,5.16129C8.73016,5.16129,8.25397,5.96774,8.09524,6.6129L7.77778,8.54839L9.36508,8.54839C9.68254,8.54839,10,8.87097,10,9.19355C10,9.51613,9.68254,9.83871,9.36508,9.83871L7.61905,9.83871L6.50794,14.8387Q6.34921,16.2903,5.39683,16.2903Q4.44444,16.2903,4.92064,14.8387L6.03175,10L4.60317,10C4.28571,10,3.96825,9.67742,3.96825,9.35484C3.96825,8.70968,4.28571,8.54839,4.60317,8.54839L6.34921,8.54839L6.8254,6.45161C7.14286,3.70968,9.52381,3.54839,10.3175,3.70968ZM18.4127,6.6129C18.5714,6.12903,18.8889,5.96774,19.3651,5.96774C19.8413,6.12903,20,6.45161,20,6.93548L18.4127,13.3871C18.254,13.871,17.9365,14.0323,17.4603,14.0323C16.9841,13.871,16.8254,13.5484,16.8254,13.0645L18.4127,6.6129Z></path></svg><span></span></div><div class="item tools"><svg width=20 height=20 viewBox="0 0 20 20"><path d=M18.5446,9.09091C18.3333,6.61616,17.2887,4.31818,15.5751,2.63889C13.8498,0.94697,11.6197,0,9.28404,0C8.02817,0,6.81925,0.265151,5.66901,0.782828C5.65728,0.782828,5.65728,0.795454,5.64554,0.795454C5.6338,0.795454,5.6338,0.808081,5.62207,0.808081C4.53052,1.31313,3.55634,2.0202,2.71127,2.92929C1.85446,3.85101,1.18545,4.91162,0.715963,6.11111C0.246479,7.33586,0,8.64899,0,10C0,10.8712,0.105634,11.7172,0.305164,12.5379C0.305164,12.5631,0.316901,12.5884,0.328638,12.6136C0.739437,14.2298,1.51408,15.7197,2.62911,16.9571C4.07277,18.548,5.92723,19.5581,7.93427,19.8737C7.95775,19.8737,7.96948,19.8864,7.99296,19.8864C8.3216,19.9369,8.66197,19.9747,9.00235,19.9747L9.21362,19.9747C9.61268,19.9747,10.3756,19.9369,11.0094,19.697C11.1737,19.6338,11.3028,19.5076,11.3732,19.3434C11.4437,19.1793,11.4554,18.9899,11.3967,18.8131C11.3028,18.5354,11.0563,18.346,10.7864,18.346C10.716,18.346,10.6338,18.3586,10.5634,18.3838C10.0939,18.5606,9.46009,18.5859,9.20188,18.5859L9.09624,18.5859C9.20188,18.2702,9.23709,17.9167,9.15493,17.5505C9.00235,16.8939,8.50939,16.3384,7.58216,15.7955L7.19484,15.5682C6.57277,15.2146,6.23239,15.0253,6.03286,14.7348C5.83333,14.4444,5.69249,13.9899,5.51643,12.9798C5.38732,12.298,5.04695,11.7677,4.50704,11.4646C4.14319,11.2626,3.70892,11.149,3.19249,11.149C2.82864,11.149,2.42958,11.1995,2.00704,11.3005C1.79578,11.351,1.59624,11.4141,1.42019,11.4646C1.33803,10.9848,1.30282,10.4798,1.30282,9.97475C1.30282,6.93182,2.76995,4.26768,4.98826,2.72727C5,3.00505,5.05869,3.29545,5.17606,3.57323C5.48122,4.26768,6.10329,4.7096,7.01878,4.89899C7.06573,4.91162,7.10094,4.91162,7.13615,4.91162L7.1831,4.91162C7.26526,4.91162,7.57042,4.92424,7.88732,5.0505C8.3216,5.2399,8.56808,5.55555,8.65023,6.04798C8.84977,7.61364,9.07277,10.4293,8.79108,11.3384C8.76761,11.4141,8.75587,11.4899,8.75587,11.5657C8.75587,11.9444,9.0493,12.2601,9.40141,12.2601C9.57747,12.2601,9.74179,12.1843,9.85915,12.0581C9.97653,11.9318,12.6174,9.05303,13.3216,8.09343C13.4038,7.97979,13.4859,7.87878,13.5798,7.76515C13.9202,7.33586,14.2723,6.90656,14.4014,6.26262C14.554,5.56818,14.4014,4.79798,13.9437,3.85101C13.615,3.16919,13.5563,2.86616,13.5446,2.75252C13.5563,2.7399,13.5798,2.72727,13.6033,2.71464C15.6221,4.10353,17.0188,6.43939,17.2535,9.19192C17.2887,9.55808,17.5587,9.82323,17.8991,9.82323L17.9577,9.82323C18.3099,9.8106,18.5681,9.48232,18.5446,9.09091ZM3.19249,12.5631C3.48592,12.5631,3.72066,12.6136,3.89671,12.7146C4.08451,12.8283,4.19014,12.9924,4.23709,13.2702C4.43662,14.3434,4.61268,15.0631,5,15.6061C5.37559,16.1364,5.85681,16.4015,6.58451,16.8182L6.60798,16.8308C6.71362,16.8939,6.84272,16.9571,6.96009,17.0328C7.69953,17.4621,7.86385,17.7525,7.89906,17.8914C7.93427,18.0303,7.85211,18.2323,7.74648,18.4343C4.91784,17.8535,2.65258,15.6944,1.73709,12.8283C2.15962,12.702,2.71127,12.5631,3.19249,12.5631ZM12.7934,4.5202C13.4272,5.83333,13.1455,6.18687,12.5822,6.89394C12.4883,7.00758,12.3944,7.12121,12.3005,7.24747C11.9484,7.72727,11.0211,8.77525,10.2113,9.68434C10.2113,9.24242,10.1878,8.73737,10.1526,8.19444C10.0704,6.95707,9.92958,5.90909,9.92958,5.87121L9.92958,5.83333C9.75352,4.83586,9.20188,4.11616,8.3216,3.76263C7.82864,3.56061,7.37089,3.53535,7.19484,3.53535C6.73709,3.43434,6.4554,3.24495,6.33803,2.99242C6.19718,2.68939,6.29108,2.24747,6.38498,1.9697C7.28873,1.59091,8.26291,1.37626,9.28404,1.37626C10.3873,1.37626,11.4437,1.61616,12.4061,2.04545C12.3357,2.18434,12.277,2.34848,12.2535,2.5505C12.2066,3.04293,12.3709,3.64899,12.7934,4.5202Z></path><path d=M15.22299772857666,9.722223632261718C12.59389772857666,9.722223632261718,10.44600772857666,12.020201374511718,10.44600772857666,14.861111374511719C10.44600772857666,17.70202137451172,12.58215772857666,20.000021374511718,15.223007728576661,20.000021374511718C17.86384772857666,20.000021374511718,19.99999772857666,17.70202137451172,19.99999772857666,14.861111374511719C19.99999772857666,12.020201374511718,17.85211772857666,9.72222212709572,15.22299772857666,9.722223632261718ZM15.22299772857666,18.598491374511717C13.30985772857666,18.598491374511717,11.737087728576661,16.91919137451172,11.737087728576661,14.848481374511719C11.737087728576661,12.777781374511719,13.29811772857666,11.098491374511719,15.22299772857666,11.098491374511719C17.14787772857666,11.098491374511719,18.708917728576658,12.777781374511719,18.708917728576658,14.848481374511719C18.708917728576658,16.91919137451172,17.13614772857666,18.59848137451172,15.22299772857666,18.598491374511717Z></path><path d=M15.692486288146974,15.050496970825195L15.692486288146974,12.676760970825196C15.692486288146974,12.297972970825196,15.399058288146973,11.982316970825195,15.046945288146972,11.982316970825195C14.694833288146972,11.982316970825195,14.401406288146973,12.297972970825196,14.401406288146973,12.676760970825196L14.401406288146973,15.340896970825195C14.401406288146973,15.530296970825194,14.471829288146973,15.694436970825196,14.589200288146973,15.833326970825196L15.751176288146972,17.095956970825195C15.868546288146973,17.222216970825194,16.032866288146973,17.297976970825196,16.208916288146973,17.297976970825196C16.384976288146973,17.297976970825196,16.537556288146973,17.222216970825194,16.666666288146974,17.095956970825195C16.78403628814697,16.969686970825194,16.854456288146974,16.792916970825196,16.854456288146974,16.603526970825193C16.854456288146974,16.414136970825197,16.78403628814697,16.237366970825196,16.666666288146974,16.111106970825197L15.692486288146974,15.050496970825195Z></path></svg><span></span></div><div class="item tools"><svg viewBox="0 0 20 20"><path d=M19.7361,12.542L18.1916,11.2919C18.2647,10.8678,18.3025,10.4347,18.3025,10.0017C18.3025,9.56861,18.2647,9.13555,18.1916,8.71142L19.7361,7.46135C19.9743,7.26938,20.0615,6.95686,19.9554,6.6756L19.9342,6.61756C19.5074,5.49026,18.8755,4.45449,18.0549,3.53926L18.0124,3.49238C17.8096,3.26692,17.4819,3.1821,17.1848,3.28032L15.2677,3.92544C14.5603,3.3763,13.7704,2.94324,12.9168,2.63966L12.5466,0.742229C12.49,0.449802,12.2472,0.222111,11.9383,0.168536L11.8746,0.157375C10.6461,-0.0524583,9.35391,-0.0524583,8.1254,0.157375L8.06174,0.168536C7.75284,0.222111,7.50997,0.449802,7.45338,0.742229L7.08082,2.64859C6.2343,2.95217,5.44909,3.383,4.74641,3.92991L2.81522,3.28032C2.52047,3.1821,2.19036,3.26469,1.98757,3.49238L1.94513,3.53926C1.12455,4.45672,0.492609,5.49249,0.0658141,6.61756L0.0445921,6.6756C-0.0615171,6.95463,0.0257283,7.26715,0.263885,7.46135L1.82723,8.72482C1.75413,9.14448,1.71876,9.57308,1.71876,9.99944C1.71876,10.428,1.75413,10.8566,1.82723,11.2741L0.263885,12.5375C0.025729,12.7295,-0.0615164,13.042,0.0445929,13.3233L0.0658148,13.3813C0.49261,14.5064,1.12455,15.5444,1.94513,16.4596L1.98757,16.5065C2.19036,16.732,2.51812,16.8168,2.81522,16.7186L4.74641,16.069C5.44909,16.6159,6.2343,17.0489,7.08082,17.3503L7.45338,19.2567C7.50997,19.5491,7.75284,19.7768,8.06174,19.8303L8.1254,19.8415C8.74084,19.9464,9.37042,20,10,20C10.6296,20,11.2615,19.9464,11.8746,19.8415L11.9383,19.8303C12.2472,19.7768,12.49,19.5491,12.5466,19.2567L12.9168,17.3592C13.7704,17.0556,14.5603,16.6248,15.2677,16.0734L17.1848,16.7186C17.4795,16.8168,17.8096,16.7342,18.0124,16.5065L18.0549,16.4596C18.8755,15.5422,19.5074,14.5064,19.9342,13.3813L19.9554,13.3233C20.0615,13.0487,19.9743,12.7362,19.7361,12.542ZM16.5175,8.97483C16.5764,9.3119,16.6071,9.65791,16.6071,10.0039C16.6071,10.3499,16.5764,10.6959,16.5175,11.033L16.3618,11.9281L18.1233,13.3545C17.8568,13.9372,17.5196,14.4863,17.1188,14.9975L14.9305,14.2631L14.1901,14.839C13.6266,15.2765,12.9994,15.6203,12.3203,15.8614L11.4219,16.1806L10.9998,18.3459C10.3372,18.4173,9.66045,18.4173,8.9955,18.3459L8.57342,16.1761L7.6821,15.8524C7.01008,15.6114,6.38521,15.2676,5.82637,14.8323L5.08596,14.2541L2.88361,14.9953C2.48275,14.4841,2.14791,13.9327,1.8791,13.3523L3.65938,11.9125L3.50611,11.0196C3.44952,10.687,3.41887,10.3432,3.41887,10.0039C3.41887,9.66237,3.44716,9.32083,3.50611,8.98822L3.65938,8.09531L1.8791,6.6555C2.14556,6.07288,2.48275,5.52374,2.88361,5.01255L5.08596,5.75367L5.82637,5.17551C6.38521,4.74022,7.01008,4.39645,7.6821,4.15536L8.57578,3.83615L8.99786,1.66638C9.66045,1.59495,10.3372,1.59495,11.0021,1.66638L11.4242,3.83168L12.3226,4.1509C12.9994,4.39198,13.6289,4.73575,14.1925,5.17328L14.9329,5.7492L17.1211,5.01479C17.522,5.52598,17.8568,6.07734,18.1256,6.65773L16.3642,8.08416L16.5175,8.97483ZM10.0024,5.85189C7.7104,5.85189,5.85231,7.61092,5.85231,9.78068C5.85231,11.9504,7.7104,13.7095,10.0024,13.7095C12.2943,13.7095,14.1524,11.9504,14.1524,9.78068C14.1524,7.61092,12.2943,5.85189,10.0024,5.85189ZM11.8699,11.5486C11.37,12.0196,10.7074,12.2808,10.0024,12.2808C9.29732,12.2808,8.63473,12.0196,8.13483,11.5486C7.6373,11.0754,7.36142,10.4481,7.36142,9.78068C7.36142,9.11323,7.6373,8.48596,8.13483,8.01272C8.63473,7.53948,9.29732,7.28054,10.0024,7.28054C10.7074,7.28054,11.37,7.53948,11.8699,8.01272C12.3674,8.48596,12.6433,9.11323,12.6433,9.78068C12.6433,10.4481,12.3674,11.0754,11.8699,11.5486Z></path></svg><span></span></div><div class="item tools">'), s9 = /* @__PURE__ */ I("<span>"), L$ = /* @__PURE__ */ I('<svg viewBox="0 0 20 20"><path d=M1.08108,0L0,1.079L4.18919,5.27938L2.54826,6.91715L6.9112,6.91715L6.9112,2.56262L5.28957,4.18112L1.08108,0ZM15.8108,5.27938L20,1.079L18.9189,0L14.7104,4.18112L13.0888,2.56262L13.0888,6.91715L17.4517,6.91715L15.8108,5.27938ZM4.16988,14.7014L0.07722,18.8054L1.1583,20L5.27027,15.7996L6.9112,17.4374L6.9112,13.0829L2.54826,13.0829L4.16988,14.7014ZM17.4517,13.0829L13.0888,13.0829L13.0888,17.4374L14.7297,15.7996L18.8417,20L19.9228,18.8054L15.8301,14.7013L17.4517,13.0829Z>'), x$ = /* @__PURE__ */ I('<svg viewBox="0 0 20 20"><path d=M2.93444,1.76899L7.57544,6.40999L6.38918,7.59626L1.76899,2.93444L0,4.70343L0,0L4.70343,0L2.93444,1.76899ZM6.40999,12.4037L1.76899,17.0447L0,15.2758L0,19.9792L4.70343,19.9792L2.93444,18.2102L7.57544,13.5692L6.40999,12.4037ZM15.2758,0L17.0447,1.76899L12.4037,6.40999L13.59,7.59626L18.231,2.95526L20,4.72425L20,0L15.2758,0ZM13.5692,12.4037L12.3829,13.59L17.0239,18.231L15.2549,20L19.9792,20L19.9792,15.2758L18.2102,17.0447L13.5692,12.4037Z>');
const $$ = (n) => {
  let a;
  const [i, u] = V(!1), f = () => {
    u((g) => !g);
  };
  return q2(() => {
    document.addEventListener("fullscreenchange", f), document.addEventListener("mozfullscreenchange", f), document.addEventListener("webkitfullscreenchange", f), document.addEventListener("msfullscreenchange", f);
  }), v9(() => {
    document.removeEventListener("fullscreenchange", f), document.removeEventListener("mozfullscreenchange", f), document.removeEventListener("webkitfullscreenchange", f), document.removeEventListener("msfullscreenchange", f);
  }), (() => {
    var g = m$(), d = g.firstChild, p = d.firstChild, m = d.nextSibling, S = m.firstChild, x = S.nextSibling, M = m.nextSibling, D = M.firstChild, z = D.nextSibling, t1 = M.nextSibling, p1 = t1.firstChild, n1 = p1.nextSibling, i1 = t1.nextSibling;
    return C9((G) => {
      a = G;
    }, g), dt(p, "click", n.onMenuClick, !0), F(g, B(Z1, {
      get when() {
        return n.symbol;
      },
      get children() {
        var G = y$(), U = G.firstChild;
        return dt(G, "click", n.onSymbolClick, !0), F(G, B(Z1, {
          get when() {
            return n.symbol.logo;
          },
          get children() {
            var q = C$();
            return P1(() => ve(q, "src", n.symbol.logo)), q;
          }
        }), U), F(U, () => n.symbol.shortName ?? n.symbol.name ?? n.symbol.ticker), G;
      }
    }), m), F(g, () => n.periods.map((G) => (() => {
      var U = s9();
      return U.$$click = () => {
        n.onPeriodChange(G);
      }, F(U, () => G.text), P1(() => vt(U, `item period ${G.text === n.period.text ? "selected" : ""}`)), U;
    })()), m), dt(m, "click", n.onIndicatorClick, !0), F(x, () => P("indicator", n.locale)), dt(M, "click", n.onTimezoneClick, !0), F(z, () => P("timezone", n.locale)), dt(t1, "click", n.onSettingClick, !0), F(n1, () => P("setting", n.locale)), i1.$$click = () => {
      if (i())
        (document.exitFullscreen ?? // @ts-expect-error
        document.msExitFullscreen ?? // @ts-expect-error
        document.mozCancelFullScreen ?? // @ts-expect-error
        document.webkitExitFullscreen).call(document);
      else {
        const G = a == null ? void 0 : a.parentElement;
        G && (G.requestFullscreen ?? // @ts-expect-error
        G.webkitRequestFullscreen ?? // @ts-expect-error
        G.mozRequestFullScreen ?? // @ts-expect-error
        G.msRequestFullscreen).call(G);
      }
    }, F(i1, (() => {
      var G = A1(() => !!i());
      return () => G() ? [L$(), (() => {
        var U = s9();
        return F(U, () => P("exit_full_screen", n.locale)), U;
      })()] : [x$(), (() => {
        var U = s9();
        return F(U, () => P("full_screen", n.locale)), U;
      })()];
    })()), P1(() => ve(p, "class", n.spread ? "" : "rotate")), g;
  })();
};
ke(["click"]);
var b$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M12.41465,11L18.5,11C18.7761,11,19,11.22386,19,11.5C19,11.77614,18.7761,12,18.5,12L12.41465,12C12.20873,12.5826,11.65311,13,11,13C10.34689,13,9.79127,12.5826,9.58535,12L3.5,12C3.223857,12,3,11.77614,3,11.5C3,11.22386,3.223857,11,3.5,11L9.58535,11C9.79127,10.417404,10.34689,10,11,10C11.65311,10,12.20873,10.417404,12.41465,11Z stroke-opacity=0 stroke=none>');
const w$ = () => b$();
var A$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M6.91465,11L11.08535,11C11.29127,10.417404,11.84689,10,12.5,10C13.15311,10,13.70873,10.417404,13.91465,11L18.5,11C18.7761,11,19,11.22386,19,11.5C19,11.77614,18.7761,12,18.5,12L13.91465,12C13.70873,12.5826,13.15311,13,12.5,13C11.84689,13,11.29127,12.5826,11.08535,12L6.91465,12C6.70873,12.5826,6.15311,13,5.5,13C4.671573,13,4,12.32843,4,11.5C4,10.671573,4.671573,10,5.5,10C6.15311,10,6.70873,10.417404,6.91465,11Z stroke-opacity=0 stroke=none>');
const S$ = () => A$();
var M$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M6.91465,12.5C6.70873,13.0826,6.15311,13.5,5.5,13.5C4.671573,13.5,4,12.82843,4,12C4,11.171573,4.671573,10.5,5.5,10.5C6.15311,10.5,6.70873,10.917404,6.91465,11.5L16.0853,11.5C16.2913,10.917404,16.846899999999998,10.5,17.5,10.5C18.328400000000002,10.5,19,11.171573,19,12C19,12.82843,18.328400000000002,13.5,17.5,13.5C16.846899999999998,13.5,16.2913,13.0826,16.0853,12.5L6.91465,12.5Z stroke-opacity=0 stroke=none>');
const T$ = () => M$();
var I$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M11,12.41465L11,18.5C11,18.7761,11.22386,19,11.5,19C11.77614,19,12,18.7761,12,18.5L12,12.41465C12.5826,12.20873,13,11.65311,13,11C13,10.34689,12.5826,9.79127,12,9.58535L12,3.5C12,3.223857,11.77614,3,11.5,3C11.22386,3,11,3.223857,11,3.5L11,9.58535C10.417404,9.79127,10,10.34689,10,11C10,11.65311,10.417404,12.20873,11,12.41465Z stroke-opacity=0 stroke=none>');
const k$ = () => I$();
var E$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M11.66558837890625,19C10.83716137890625,19,10.16558837890625,18.328400000000002,10.16558837890625,17.5C10.16558837890625,16.846899999999998,10.58298437890625,16.2913,11.16557337890625,16.0854L11.16557337890625,11.91464C10.58298437890625,11.70872,10.16558837890625,11.1531,10.16558837890625,10.5C10.16558837890625,9.8469,10.58298437890625,9.29128,11.16557337890625,9.08536L11.16557337890625,4.5C11.16557337890625,4.223857,11.38942837890625,4,11.66556837890625,4C11.94171837890625,4,12.16556837890625,4.223857,12.16556837890625,4.5L12.16556837890625,9.08535C12.74817837890625,9.291260000000001,13.16558837890625,9.846879999999999,13.16558837890625,10.5C13.16558837890625,11.153120000000001,12.74817837890625,11.708739999999999,12.16556837890625,11.91465L12.16556837890625,16.0854C12.74817837890625,16.2913,13.16558837890625,16.846899999999998,13.16558837890625,17.5C13.16558837890625,18.328400000000002,12.49401837890625,19,11.66558837890625,19Z stroke-opacity=0 stroke=none>');
const P$ = () => E$();
var O$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M11.165603637695312,6.91465C11.748203637695312,6.70873,12.165603637695312,6.15311,12.165603637695312,5.5C12.165603637695312,4.671573,11.494033637695313,4,10.665603637695312,4C9.837176637695313,4,9.165603637695312,4.671573,9.165603637695312,5.5C9.165603637695312,6.15311,9.583007637695312,6.70873,10.165603637695312,6.91465L10.165603637695312,16.0854C9.583007637695312,16.2913,9.165603637695312,16.846899999999998,9.165603637695312,17.5C9.165603637695312,18.328400000000002,9.837176637695313,19,10.665603637695312,19C11.494033637695313,19,12.165603637695312,18.328400000000002,12.165603637695312,17.5C12.165603637695312,16.846899999999998,11.748203637695312,16.2913,11.165603637695312,16.0854L11.165603637695312,6.91465Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const D$ = () => O$();
var R$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M5.146447,15.753C4.9511845,15.9483,4.9511845,16.2649,5.146447,16.4602C5.341709,16.6554,5.658291,16.6554,5.853554,16.4602L8.156600000000001,14.15711C8.352409999999999,14.25082,8.57173,14.3033,8.8033,14.3033C9.631730000000001,14.3033,10.3033,13.63172,10.3033,12.80329C10.3033,12.57172,10.250820000000001,12.352409999999999,10.157119999999999,12.15659L12.156600000000001,10.15711C12.352409999999999,10.250820000000001,12.571729999999999,10.30329,12.8033,10.30329C13.63173,10.30329,14.3033,9.63172,14.3033,8.80329C14.3033,8.57172,14.25082,8.352409999999999,14.15712,8.15659L16.4602,5.853553C16.6554,5.658291,16.6554,5.341709,16.4602,5.146447C16.2649,4.9511843,15.9483,4.9511843,15.753,5.146447L13.45001,7.449479999999999C13.25419,7.35577,13.03487,7.3032900000000005,12.8033,7.3032900000000005C11.97487,7.3032900000000005,11.3033,7.97487,11.3033,8.80329C11.3033,9.03487,11.35578,9.254190000000001,11.44949,9.450009999999999L9.450009999999999,11.449480000000001C9.254190000000001,11.35577,9.03487,11.30329,8.8033,11.30329C7.97487,11.30329,7.3033,11.97487,7.3033,12.80329C7.3033,13.03487,7.35578,13.25419,7.44949,13.45001L5.146447,15.753Z stroke-opacity=0 stroke=none>');
const B$ = () => R$();
var F$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M7.573332939453125,14.54567903564453C7.667042939453125,14.741499035644532,7.719512939453125,14.960809035644532,7.719512939453125,15.19239903564453C7.719512939453125,16.02079903564453,7.047942939453125,16.69239903564453,6.219512939453125,16.69239903564453C5.391085939453125,16.69239903564453,4.719512939453125,16.02079903564453,4.719512939453125,15.19239903564453C4.719512939453125,14.36394903564453,5.391085939453125,13.692379035644532,6.219512939453125,13.692379035644532C6.451092939453125,13.692379035644532,6.670412939453125,13.74485903564453,6.866232939453125,13.83856903564453L9.865702939453126,10.83909903564453C9.771992939453124,10.643279035644532,9.719512939453125,10.42395903564453,9.719512939453125,10.192379035644532C9.719512939453125,9.36394903564453,10.391082939453124,8.692379035644532,11.219512939453125,8.692379035644532C11.451092939453126,8.692379035644532,11.670412939453126,8.74485903564453,11.866232939453125,8.838569035644532L15.462112939453124,5.242645035644531C15.657412939453126,5.047383335644532,15.974012939453125,5.047383335644532,16.169212939453125,5.242645035644531C16.364512939453125,5.437907035644531,16.364512939453125,5.754489035644531,16.169212939453125,5.949752035644531L12.573332939453124,9.545679035644532C12.667042939453125,9.74149903564453,12.719512939453125,9.96080903564453,12.719512939453125,10.192379035644532C12.719512939453125,11.020809035644533,12.047942939453126,11.692379035644532,11.219512939453125,11.692379035644532C10.987942939453125,11.692379035644532,10.768632939453125,11.639909035644532,10.572812939453126,11.54619903564453L7.573332939453125,14.54567903564453Z stroke-opacity=0 stroke=none>');
const N$ = () => F$();
var K$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M15.719512939453125,8.461776733398438C16.547912939453127,8.461776733398438,17.219512939453125,7.7902067333984375,17.219512939453125,6.9617767333984375C17.219512939453125,6.133349733398438,16.547912939453127,5.4617767333984375,15.719512939453125,5.4617767333984375C14.891082939453124,5.4617767333984375,14.219512939453125,6.133349733398438,14.219512939453125,6.9617767333984375C14.219512939453125,7.193346733398437,14.271992939453124,7.412666733398438,14.365692939453124,7.608486733398438L7.366222939453126,14.607956733398437C7.170402939453125,14.514256733398437,6.951082939453125,14.461776733398438,6.719512939453125,14.461776733398438C5.891085939453125,14.461776733398438,5.219512939453125,15.133346733398437,5.219512939453125,15.961776733398438C5.219512939453125,16.79017673339844,5.891085939453125,17.461776733398438,6.719512939453125,17.461776733398438C7.547942939453125,17.461776733398438,8.219512939453125,16.79017673339844,8.219512939453125,15.961776733398438C8.219512939453125,15.730176733398437,8.167032939453126,15.510876733398437,8.073322939453124,15.315066733398437L15.072802939453124,8.315586733398437C15.268612939453124,8.409296733398438,15.487912939453125,8.461776733398438,15.719512939453125,8.461776733398438Z stroke-opacity=0 stroke=none>');
const U$ = () => K$();
var Z$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M17.0643,7.033864912109375L18,3.585784912109375L14.5078,4.509695912109375L15.3537,5.344934912109375L6.02026,14.560584912109375C5.87635,14.517484912109374,5.72366,14.494284912109375,5.5655,14.494284912109375C4.7009,14.494284912109375,4,15.186384912109375,4,16.040084912109375C4,16.893784912109375,4.7009,17.585784912109375,5.5655,17.585784912109375C6.43011,17.585784912109375,7.13101,16.893784912109375,7.13101,16.040084912109375C7.13101,15.722284912109375,7.03392,15.426984912109376,6.86744,15.181384912109374L16.0917,6.073604912109375L17.0643,7.033864912109375Z stroke-opacity=0 stroke=none>');
const W$ = () => Z$();
var z$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M6.91465,13.00505L18.5,13.00505C18.7761,13.00505,19,13.228909999999999,19,13.50505C19,13.781189999999999,18.7761,14.00505,18.5,14.00505L6.91465,14.00505C6.70873,14.58765,6.15311,15.00505,5.5,15.00505C4.671573,15.00505,4,14.33348,4,13.50505C4,12.67662,4.671573,12.00505,5.5,12.00505C6.15311,12.00505,6.70873,12.422450000000001,6.91465,13.00505ZM7.81404,11.625L10.48591,11.625L10.48591,10.90625L9.65193,10.90625L9.65193,7.125L8.997630000000001,7.125C8.71443,7.306641,8.415600000000001,7.419922,7.96443,7.498047L7.96443,8.05078L8.77497,8.05078L8.77497,10.90625L7.81404,10.90625L7.81404,11.625ZM11.081620000000001,11.625L14.0562,11.625L14.0562,10.88281L13.09724,10.88281C12.8863,10.88281,12.59333,10.90625,12.36482,10.93555C13.17537,10.11328,13.84724,9.2207,13.84724,8.39062C13.84724,7.541016,13.28865,7,12.4488,7C11.84333,7,11.446850000000001,7.234375,11.03279,7.679688L11.52497,8.16797C11.747630000000001,7.914062,12.0113,7.697266,12.33552,7.697266C12.7613,7.697266,13.00154,7.982422,13.00154,8.43359C13.00154,9.14648,12.29255,10.00781,11.081620000000001,11.11523L11.081620000000001,11.625ZM15.9605,11.75C16.8121,11.75,17.526899999999998,11.2832,17.526899999999998,10.4375C17.526899999999998,9.82031,17.142200000000003,9.43945,16.6441,9.30078L16.6441,9.27148C17.1129,9.08594,17.3824,8.7207,17.3824,8.21289C17.3824,7.421875,16.8004,7,15.9429,7C15.4215,7,14.9957,7.210938,14.6109,7.541016L15.066,8.11133C15.3258,7.849609,15.5836,7.697266,15.9019,7.697266C16.2789,7.697266,16.4957,7.914062,16.4957,8.28125C16.4957,8.70898,16.2301,9,15.4215,9L15.4215,9.63672C16.3804,9.63672,16.6383,9.91992,16.6383,10.38086C16.6383,10.79688,16.3336,11.03125,15.8824,11.03125C15.4742,11.03125,15.1578,10.82227,14.8922,10.55078L14.4781,11.13281C14.7906,11.486329999999999,15.2652,11.75,15.9605,11.75Z stroke-opacity=0 stroke=none>');
const Q$ = () => z$();
var H$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M3.146447,14.178126025390625C2.9511847,13.982826025390626,2.9511847,13.666226025390625,3.146447,13.470926025390625L7.39146,9.225966025390626C7.35417,9.095106025390624,7.33421,8.956946025390625,7.33421,8.814116025390625C7.33421,7.985696025390625,8.00578,7.314116025390625,8.834209999999999,7.314116025390625C8.97703,7.314116025390625,9.11519,7.334086025390625,9.24605,7.371366025390625L13.753,2.864373025390625C13.9483,2.669110325390625,14.2649,2.669110325390625,14.4602,2.864373025390625C14.6554,3.059635025390625,14.6554,3.376217025390625,14.4602,3.571479025390625L10.06916,7.962476025390625C10.23631,8.204386025390626,10.334209999999999,8.497826025390625,10.334209999999999,8.814116025390625C10.334209999999999,9.642546025390626,9.66264,10.314116025390625,8.834209999999999,10.314116025390625C8.51791,10.314116025390625,8.22448,10.216226025390625,7.98256,10.049076025390626L3.853554,14.178126025390625C3.658291,14.373326025390625,3.341709,14.373326025390625,3.146447,14.178126025390625ZM7.67736,19.188526025390626C7.4821,18.993226025390626,7.4821,18.676626025390625,7.67736,18.481426025390626L9.9804,16.178326025390625C9.88669,15.982526025390625,9.834209999999999,15.763226025390624,9.834209999999999,15.531626025390626C9.834209999999999,14.703226025390626,10.50578,14.031626025390626,11.33421,14.031626025390626C11.56579,14.031626025390626,11.78511,14.084126025390624,11.98093,14.177826025390624L13.9804,12.178356025390626C13.8867,11.982536025390624,13.8342,11.763216025390625,13.8342,11.531636025390625C13.8342,10.703206025390624,14.5058,10.031636025390625,15.3342,10.031636025390625C15.5658,10.031636025390625,15.7851,10.084116025390625,15.9809,10.177826025390626L18.284,7.874796025390625C18.4792,7.679536025390625,18.7958,7.679536025390625,18.9911,7.874796025390625C19.1863,8.070056025390624,19.1863,8.386636025390626,18.9911,8.581906025390625L16.688000000000002,10.884936025390624C16.7817,11.080756025390626,16.8342,11.300066025390626,16.8342,11.531636025390625C16.8342,12.360066025390624,16.162599999999998,13.031626025390626,15.3342,13.031626025390626C15.1026,13.031626025390626,14.8833,12.979126025390626,14.6875,12.885426025390625L12.68803,14.884926025390625C12.78174,15.080726025390625,12.83421,15.300026025390626,12.83421,15.531626025390626C12.83421,16.360026025390624,12.16264,17.031626025390626,11.33421,17.031626025390626C11.10264,17.031626025390626,10.88333,16.979126025390627,10.68751,16.885426025390625L8.38446,19.188526025390626C8.1892,19.383726025390626,7.87262,19.383726025390626,7.67736,19.188526025390626Z stroke-opacity=0 stroke=none>');
const G$ = () => H$();
var Y$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M3.3367688759765626,12.63173C3.5320318759765623,12.82699,3.8486138759765627,12.82699,4.043876875976562,12.63173L11.822052875976562,4.853553C12.017312875976563,4.658291,12.017312875976563,4.341708,11.822052875976562,4.146446C11.626792875976562,3.9511843,11.310202875976563,3.9511843,11.114942875976563,4.146446L3.3367688759765626,11.92462C3.1415071759765625,12.11988,3.1415071759765625,12.43647,3.3367688759765626,12.63173ZM5.001492875976562,17.0351C4.806232875976562,16.8399,4.806232875976562,16.5233,5.001492875976562,16.328L7.304532875976562,14.025C7.210822875976563,13.82916,7.158352875976563,13.60984,7.158352875976563,13.37827C7.158352875976563,12.54984,7.829922875976562,11.87827,8.658352875976561,11.87827C8.889922875976563,11.87827,9.109232875976563,11.93075,9.305052875976562,12.02446L11.304532875976562,10.02498C11.210822875976563,9.82916,11.158352875976561,9.60984,11.158352875976561,9.37827C11.158352875976561,8.54984,11.829922875976562,7.8782700000000006,12.658352875976563,7.8782700000000006C12.889922875976563,7.8782700000000006,13.109232875976563,7.93075,13.305022875976562,8.024460000000001L15.608122875976562,5.72142C15.803322875976562,5.5261499999999995,16.119922875976563,5.5261499999999995,16.315222875976563,5.72142C16.510422875976563,5.9166799999999995,16.510422875976563,6.23326,16.315222875976563,6.42852L14.012122875976562,8.73156C14.105822875976562,8.92738,14.158322875976562,9.1467,14.158322875976562,9.37827C14.158322875976562,10.2067,13.486822875976562,10.87827,12.658352875976563,10.87827C12.426772875976562,10.87827,12.207452875976562,10.82579,12.011642875976563,10.73209L10.012162875976562,12.73156C10.105872875976562,12.92738,10.158352875976561,13.1467,10.158352875976561,13.37827C10.158352875976561,14.2067,9.486772875976563,14.8783,8.658352875976561,14.8783C8.426772875976562,14.8783,8.207452875976562,14.8258,8.011642875976563,14.7321L5.708602875976562,17.0351C5.513342875976562,17.2304,5.196752875976562,17.2304,5.001492875976562,17.0351ZM10.415712875976563,18.328C10.220452875976562,18.5233,9.903862875976563,18.5233,9.708602875976563,18.328C9.513342875976562,18.1328,9.513342875976562,17.816200000000002,9.708602875976563,17.6209L12.304532875976562,15.025C12.210822875976563,14.8292,12.158352875976563,14.6098,12.158352875976563,14.3783C12.158352875976563,13.54984,12.829922875976562,12.87827,13.658322875976562,12.87827C13.889922875976563,12.87827,14.109222875976563,12.93075,14.305022875976562,13.02446L17.486822875976564,9.84274C17.682022875976564,9.64747,17.99862287597656,9.64747,18.19392287597656,9.84274C18.38912287597656,10.038,18.38912287597656,10.35458,18.19392287597656,10.54984L15.012122875976562,13.73156C15.105822875976562,13.92738,15.158322875976562,14.1467,15.158322875976562,14.3783C15.158322875976562,15.2067,14.486822875976562,15.8783,13.658322875976562,15.8783C13.426822875976562,15.8783,13.207422875976562,15.8258,13.011642875976563,15.7321L10.415712875976563,18.328Z stroke-opacity=0 stroke=none>');
const V$ = () => Y$();
var X$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M13.1889,6C12.98303,6.582599999999999,12.42741,7,11.7743,7C11.12119,7,10.565570000000001,6.582599999999999,10.35965,6L3.5,6C3.223857,6,3,5.77614,3,5.5C3,5.22386,3.223857,5,3.5,5L10.35965,5C10.565570000000001,4.417404,11.12119,4,11.7743,4C12.42741,4,12.98303,4.417404,13.1889,5L18.5,5C18.7761,5,19,5.22386,19,5.5C19,5.77614,18.7761,6,18.5,6L13.1889,6ZM3,8.5C3,8.22386,3.223857,8,3.5,8L18.5,8C18.7761,8,19,8.22386,19,8.5C19,8.77614,18.7761,9,18.5,9L3.5,9C3.223857,9,3,8.77614,3,8.5ZM3.278549,11.5C3.278549,11.22386,3.502407,11,3.778549,11L18.7785,11C19.0547,11,19.2785,11.22386,19.2785,11.5C19.2785,11.77614,19.0547,12,18.7785,12L3.778549,12C3.502407,12,3.278549,11.77614,3.278549,11.5ZM3.139267,14.5C3.139267,14.2239,3.363124,14,3.6392670000000003,14L18.6393,14C18.915399999999998,14,19.1393,14.2239,19.1393,14.5C19.1393,14.7761,18.915399999999998,15,18.6393,15L3.6392670000000003,15C3.363124,15,3.139267,14.7761,3.139267,14.5ZM13.1889,18C12.98303,18.5826,12.42741,19,11.7743,19C11.12119,19,10.565570000000001,18.5826,10.35965,18L3.778549,18C3.502407,18,3.278549,17.7761,3.278549,17.5C3.278549,17.2239,3.502407,17,3.778549,17L10.35965,17C10.565570000000001,16.4174,11.12119,16,11.7743,16C12.42741,16,12.98303,16.4174,13.1889,17L18.7785,17C19.0547,17,19.2785,17.2239,19.2785,17.5C19.2785,17.7761,19.0547,18,18.7785,18L13.1889,18Z stroke-opacity=0 stroke=none>');
const q$ = () => X$();
var j$ = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M4.91465,6C4.70873,6.582599999999999,4.15311,7,3.5,7C2.671573,7,2,6.32843,2,5.5C2,4.671573,2.671573,4,3.5,4C4.15311,4,4.70873,4.417404,4.91465,5L18.2257,5C18.5018,5,18.7257,5.22386,18.7257,5.5C18.7257,5.77614,18.5018,6,18.2257,6L4.91465,6ZM2.7257,8.5C2.7257,8.22386,2.949558,8,3.2257,8L18.2257,8C18.5018,8,18.7257,8.22386,18.7257,8.5C18.7257,8.77614,18.5018,9,18.2257,9L3.2257,9C2.949558,9,2.7257,8.77614,2.7257,8.5ZM3.00425,11.5C3.00425,11.22386,3.22811,11,3.50425,11L18.5042,11C18.7804,11,19.0042,11.22386,19.0042,11.5C19.0042,11.77614,18.7804,12,18.5042,12L3.50425,12C3.22811,12,3.00425,11.77614,3.00425,11.5ZM2.864967,14.5C2.864967,14.2239,3.08882,14,3.36497,14L18.365,14C18.6411,14,18.865,14.2239,18.865,14.5C18.865,14.7761,18.6411,15,18.365,15L3.36497,15C3.08882,15,2.864967,14.7761,2.864967,14.5ZM20,17.5C20,18.328400000000002,19.3284,19,18.5,19C17.846899999999998,19,17.2913,18.5826,17.0854,18L3.50425,18C3.22811,18,3.00425,17.7761,3.00425,17.5C3.00425,17.2239,3.22811,17,3.50425,17L17.0854,17C17.2913,16.4174,17.846899999999998,16,18.5,16C19.3284,16,20,16.671599999999998,20,17.5Z stroke-opacity=0 stroke=none>');
const J$ = () => j$();
var eb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><ellipse cx=10.5 cy=11.5 rx=1.5 ry=1.5 stroke-opacity=0 stroke=none></ellipse><ellipse cx=17.5 cy=11.5 rx=1.5 ry=1.5 stroke-opacity=0 stroke=none></ellipse><ellipse cx=10.5 cy=11.5 rx=7 ry=7 fill-opacity=0 stroke-opacity=1 fill=none stroke-width=1></ellipse><ellipse cx=10.5 cy=11.5 rx=5 ry=5 fill-opacity=0 stroke-opacity=1 fill=none stroke-width=1></ellipse><ellipse cx=10.5 cy=11.5 rx=3 ry=3 fill-opacity=0 stroke-opacity=1 fill=none stroke-width=1>');
const tb = () => eb();
var nb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M3,7.32468C5.90649,3.3893050000000002,11.49833,2.81306,14.6674,6.31944C14.9056,6.1554199999999994,15.192,6.05979,15.5,6.05979C15.845,6.05979,16.1628,6.17974,16.4162,6.381349999999999L18.4509,4.23827L19,4.816615L16.8945,7.03429C16.962600000000002,7.21075,17,7.40319,17,7.60463C17,8.45782,16.328400000000002,9.14947,15.5,9.14947C14.6716,9.14947,14,8.45782,14,7.60463C14,7.36402,14.0534,7.13625,14.1487,6.93322C11.32695,3.748365,6.25159,4.253956,3.612785,7.82695L3,7.32468ZM14.09,15.4717C15.7427,13.78985,16.244500000000002,11.524740000000001,15.5633,9.30134L15.5618,9.30134L16.3012,9.0502C17.072400000000002,11.56646,16.497700000000002,14.158,14.6282,16.0599C12.28737,18.442,8.62386,18.6988,6.41348,16.4501C4.5526,14.5572,4.52076,11.19671,6.36766,9.3177C7.89069,7.76754,10.07544,7.706189999999999,11.56741,9.22363C11.95453,9.61742,12.24817,10.08363,12.43369,10.57677L14.1451,8.77421L14.6942,9.35256L12.64982,11.50582C12.65827,11.59712,12.66295,11.68839,12.66378,11.77936C12.87398,12.04523,13,12.38451,13,12.7541C13,13.60729,12.32843,14.2989,11.5,14.2989C10.67157,14.2989,10,13.60729,10,12.7541C10,11.90091,10.67157,11.20926,11.5,11.20926C11.60387,11.20926,11.70528,11.220130000000001,11.8032,11.240829999999999L11.81763,11.22564C11.69858,10.71874,11.42858,10.21929,11.0284,9.81179C9.844000000000001,8.60765,8.136890000000001,8.65592,6.90822,9.90586C5.37975,11.460930000000001,5.40693,14.288,6.95404,15.8619C8.84598,17.7867,12.03496,17.5626,14.09,15.4717Z stroke-opacity=0 stroke=none>');
const rb = () => nb();
var ib = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M4,17.0854L4,3.5C4,3.223858,4.22386,3,4.5,3C4.77614,3,5,3.223858,5,3.5L5,10L7.57584,10L9.8127,4.46359C9.91614,4.20756,10.20756,4.08386,10.46359,4.1873000000000005C10.71963,4.29075,10.84333,4.58216,10.73988,4.8382000000000005L8.65438,10L11.08535,10C11.29127,9.4174,11.84689,9,12.5,9C12.65154,9,12.79784,9.02247,12.93573,9.06427L16.6464,5.35355C16.8417,5.15829,17.1583,5.15829,17.3536,5.35355C17.5488,5.54882,17.5488,5.8654,17.3536,6.06066L13.7475,9.66675C13.907,9.90508,14,10.19168,14,10.5C14,11.15311,13.5826,11.70873,13,11.91465L13,14.3638L18.3714,12.1936C18.6274,12.09015,18.918799999999997,12.21385,19.0222,12.46989C19.1257,12.72592,19.002,13.0173,18.746000000000002,13.1208L13,15.4423L13,18L19.5,18C19.7761,18,20,18.2239,20,18.5C20,18.7761,19.7761,19,19.5,19L5.91465,19C5.70873,19.5826,5.15311,20,4.5,20C3.671573,20,3,19.3284,3,18.5C3,17.846899999999998,3.417404,17.2913,4,17.0854ZM6.3729499999999994,17.0413L12,14.7678L12,11.91465C11.88136,11.87271,11.76956,11.81627,11.66675,11.74746L6.3729499999999994,17.0413ZM12,15.8463L6.6694700000000005,18L12,18L12,15.8463ZM6.38629,15.6137L8.250350000000001,11L11,11L6.38629,15.6137ZM5,11L7.17182,11L5,16.3754L5,11Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const ab = () => ib();
var sb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M17,4.5C17,5.32843,16.328400000000002,6,15.5,6C15.0931,6,14.7241,5.83802,14.4539,5.57503L5.98992,8.32515C5.99658,8.38251,6,8.440850000000001,6,8.5C6,9.15311,5.582599999999999,9.70873,5,9.91465L5,11.08535C5.42621,11.236,5.763999999999999,11.57379,5.91465,12L19.5,12C19.7761,12,20,12.22386,20,12.5C20,12.77614,19.7761,13,19.5,13L5.91465,13C5.70873,13.5826,5.15311,14,4.5,14C3.671573,14,3,13.3284,3,12.5C3,11.84689,3.417404,11.29127,4,11.08535L4,9.91465C3.417404,9.70873,3,9.15311,3,8.5C3,7.67157,3.671573,7,4.5,7C4.90411,7,5.2709,7.15981,5.5406200000000005,7.41967L14.0093,4.66802C14.0032,4.6128599999999995,14,4.5568,14,4.5C14,3.671573,14.6716,3,15.5,3C16.328400000000002,3,17,3.671573,17,4.5ZM4,15.5C4,15.2239,4.22386,15,4.5,15L19.5,15C19.7761,15,20,15.2239,20,15.5C20,15.7761,19.7761,16,19.5,16L4.5,16C4.22386,16,4,15.7761,4,15.5ZM4,18.5C4,18.2239,4.22386,18,4.5,18L19.5,18C19.7761,18,20,18.2239,20,18.5C20,18.7761,19.7761,19,19.5,19L4.5,19C4.22386,19,4,18.7761,4,18.5Z stroke-opacity=0 stroke=none>');
const ob = () => sb();
var lb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M20,3.5C20,4.15311,19.5826,4.70873,19,4.91465L19,18.5C19,18.7761,18.7761,19,18.5,19L4.91465,19C4.70873,19.5826,4.15311,20,3.5,20C2.671573,20,2,19.3284,2,18.5C2,17.846899999999998,2.417404,17.2913,3,17.0854L3,3.5C3,3.22386,3.22386,3,3.5,3L17.0854,3C17.2913,2.417404,17.846899999999998,2,18.5,2C19.3284,2,20,2.671573,20,3.5ZM17.0854,4C17.236,4.42621,17.5738,4.763999999999999,18,4.91465L18,8L14,8L14,4L17.0854,4ZM13,4L13,8L9,8L9,4L13,4ZM13,9L9,9L9,13L13,13L13,9ZM13,14L9,14L9,18L13,18L13,14ZM14,18L14,14L18,14L18,18L14,18ZM18,13L14,13L14,9L18,9L18,13ZM4.91465,18C4.763999999999999,17.5738,4.42621,17.236,4,17.0854L4,14L8,14L8,18L4.91465,18ZM4,8L4,4L8,4L8,8L4,8ZM8,9L8,13L4,13L4,9L8,9Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const cb = () => lb();
var ub = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><ellipse cx=10.5 cy=11.5 rx=1.5 ry=1.5 stroke-opacity=0 stroke=none></ellipse><ellipse cx=17.5 cy=11.5 rx=1.5 ry=1.5 stroke-opacity=0 stroke=none></ellipse><ellipse cx=10.5 cy=11.5 rx=7 ry=7 fill-opacity=0 fill=none stroke-opacity=1 stroke-width=1>');
const fb = () => ub();
var hb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M11.57625,6.9981C11.55099,6.999359999999999,11.52557,7,11.5,7C11.34,7,11.18584,6.97495,11.04125,6.9285499999999995L5.55401,16.4327C5.713760000000001,16.5905,5.83826,16.7839,5.91465,17L16.0854,17C16.2187,16.622700000000002,16.4987,16.314700000000002,16.8569,16.1445L11.57625,6.9981ZM12.50759,6.611219999999999C12.81005,6.336790000000001,13,5.94058,13,5.5C13,4.671573,12.32843,4,11.5,4C10.67157,4,10,4.671573,10,5.5C10,5.80059,10.08841,6.08052,10.24066,6.31522L4.64514,16.0069C4.59738,16.002299999999998,4.54896,16,4.5,16C3.671573,16,3,16.671599999999998,3,17.5C3,18.328400000000002,3.671573,19,4.5,19C5.15311,19,5.70873,18.5826,5.91465,18L16.0854,18C16.2913,18.5826,16.846899999999998,19,17.5,19C18.328400000000002,19,19,18.328400000000002,19,17.5C19,16.8365,18.5691,16.2735,17.971899999999998,16.075699999999998L12.50759,6.611219999999999Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const gb = () => hb();
var pb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M19,4.5C19,5.15311,18.5826,5.70873,18,5.91465L18,18.5C18,18.7761,17.7761,19,17.5,19L5.91465,19C5.70873,19.5826,5.15311,20,4.5,20C3.671573,20,3,19.3284,3,18.5C3,17.846899999999998,3.417404,17.2913,4,17.0854L4,4.5C4,4.22386,4.22386,4,4.5,4L16.0854,4C16.2913,3.417404,16.846899999999998,3,17.5,3C18.328400000000002,3,19,3.671573,19,4.5ZM5,5L16.0854,5C16.236,5.42621,16.5738,5.763999999999999,17,5.91465L17,18L5.91465,18C5.763999999999999,17.5738,5.42621,17.236,5,17.0854L5,5Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const _b = () => pb();
var db = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M19.6401,7.99355C20.4028,7.92291,21,7.2811900000000005,21,6.5C21,5.671573,20.3284,5,19.5,5C18.8469,5,18.2913,5.417404,18.0854,6L7.62067,6C7.34453,6,7.12067,6.22386,7.12067,6.5C7.12067,6.5479,7.12741,6.59423,7.13999,6.63809L3.2294099999999997,15.0243C2.530138,15.1517,2,15.764,2,16.5C2,17.328400000000002,2.671573,18,3.5,18C4.15311,18,4.70873,17.5826,4.91465,17L14.5963,17C14.6456,17.076,14.7162,17.1396,14.8044,17.1807C15.0546,17.2974,15.3521,17.1891,15.4688,16.9388L19.6401,7.99355ZM14.7896,16.0293L18.6551,7.739599999999999C18.3942,7.56144,18.1925,7.30307,18.0854,7L8.0746,7L4.25044,15.2009C4.55701,15.3784,4.79493,15.6613,4.91465,16L14.6207,16C14.68,16,14.7368,16.0103,14.7896,16.0293Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const vb = () => db();
var Cb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M8.134443814697265,7.494615087890625L8.764323814697265,7.494615087890625L8.764323814697265,3.414215087890625L8.310223814697267,3.414215087890625L7.294603814697266,4.005035087890625L7.289713814697266,4.634915087890625L8.134443814697265,4.149892087890625L8.134443814697265,7.494615087890625ZM18.832003814697266,6.933095087890624Q19.004603814697266,6.635245087890625,19.004603814697266,6.2543850878906255Q19.004603814697266,5.884915087890625,18.845103814697264,5.593575087890625Q18.685503814697267,5.3006050878906255,18.399103814697266,5.136225087890625Q18.114303814697266,4.9702050878906245,17.754603814697266,4.9653250878906245L18.820603814697265,3.840647087890625L18.820603814697265,3.414215087890625L16.519203814697264,3.414215087890625L16.519203814697264,3.939931087890625L18.050803814697264,3.939931087890625L16.719403814697266,5.334785087890625L17.074203814697263,5.7205350878906245Q17.254903814697265,5.484525087890625,17.619503814697268,5.484525087890625Q17.980803814697268,5.484525087890625,18.187503814697266,5.689605087890625Q18.394203814697267,5.894685087890625,18.394203814697267,6.2543850878906255Q18.394203814697267,6.604315087890625,18.187503814697266,6.822415087890625Q17.980803814697268,7.0405150878906255,17.640603814697265,7.0405150878906255Q17.334603814697267,7.0405150878906255,17.124703814697266,6.890775087890625Q16.914703814697265,6.739415087890626,16.820303814697265,6.469225087890624L16.354803814697263,6.744295087890626Q16.480103814697266,7.125155087890625,16.821903814697265,7.341625087890625Q17.165403814697264,7.559725087890625,17.640603814697265,7.559725087890625Q18.039403814697266,7.559725087890625,18.348603814697267,7.393705087890625Q18.659503814697267,7.229315087890625,18.832003814697266,6.933095087890624ZM10.000003814697266,10.634915087890626C10.000003814697266,11.024655087890626,9.851363814697265,11.379685087890625,9.607683814697266,11.646395087890625L12.168903814697266,15.171615087890626C12.275403814697265,15.147615087890625,12.386203814697266,15.134915087890626,12.500003814697266,15.134915087890626C12.596503814697266,15.134915087890626,12.690803814697265,15.144015087890624,12.782303814697265,15.161415087890624L16.108803814697268,11.196955087890625C16.038703814697264,11.023375087890624,16.000003814697266,10.833655087890625,16.000003814697266,10.634915087890626C16.000003814697266,9.806495087890625,16.671603814697264,9.134915087890626,17.500003814697266,9.134915087890626C18.328403814697264,9.134915087890626,19.000003814697266,9.806495087890625,19.000003814697266,10.634915087890626C19.000003814697266,11.463345087890625,18.328403814697264,12.134915087890626,17.500003814697266,12.134915087890626C17.239503814697265,12.134915087890626,16.994503814697268,12.068495087890625,16.781003814697264,11.951675087890624L13.654703814697266,15.677415087890624C13.870303814697266,15.937215087890625,14.000003814697266,16.270915087890625,14.000003814697266,16.634915087890626C14.000003814697266,17.463315087890624,13.328403814697266,18.134915087890626,12.500003814697266,18.134915087890626C11.671573814697265,18.134915087890626,11.000003814697266,17.463315087890624,11.000003814697266,16.634915087890626C11.000003814697266,16.284415087890626,11.120193814697265,15.962015087890626,11.321603814697266,15.706715087890625L8.715393814697265,12.119565087890624C8.645053814697267,12.129685087890625,8.573143814697266,12.134915087890626,8.500003814697266,12.134915087890626C8.162103814697264,12.134915087890626,7.8503038146972655,12.023195087890626,7.599523814697266,11.834665087890626L4.505583814697266,15.521915087890624C4.809213814697266,15.796415087890624,5.000003814697266,16.193415087890624,5.000003814697266,16.634915087890626C5.000003814697266,17.463315087890624,4.328433814697266,18.134915087890626,3.5000038146972656,18.134915087890626C2.6715768146972656,18.134915087890626,2.0000038146972656,17.463315087890624,2.0000038146972656,16.634915087890626C2.0000038146972656,15.806515087890626,2.6715768146972656,15.134915087890626,3.5000038146972656,15.134915087890626C3.508253814697266,15.134915087890626,3.5164838146972657,15.135015087890626,3.524703814697266,15.135115087890625L7.033823814697266,10.953115087890625C7.011673814697265,10.850565087890626,7.000003814697266,10.744105087890624,7.000003814697266,10.634915087890626C7.000003814697266,9.806495087890625,7.671573814697266,9.134915087890626,8.500003814697266,9.134915087890626C9.328433814697267,9.134915087890626,10.000003814697266,9.806495087890625,10.000003814697266,10.634915087890626Z stroke-opacity=0 stroke=none>');
const yb = () => Cb();
var mb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M8.13444,7.494615087890625L8.76432,7.494615087890625L8.76432,3.414215087890625L8.310220000000001,3.414215087890625L7.2946,4.005035087890625L7.28971,4.634915087890625L8.13444,4.149892087890625L8.13444,7.494615087890625ZM18.832,6.929835087890625Q19.0046,6.635245087890625,19.0046,6.2543850878906255Q19.0046,5.889805087890625,18.8451,5.5952050878906245Q18.6855,5.3006050878906255,18.3975,5.132965087890625Q18.1094,4.9653250878906245,17.7399,4.9653250878906245Q17.435499999999998,4.9653250878906245,17.1556,5.149245087890625L17.2793,3.939931087890625L18.8304,3.939931087890625L18.8304,3.414215087890625L16.7406,3.414215087890625L16.5094,5.665195087890625L17.0156,5.795405087890625Q17.095399999999998,5.655425087890626,17.2516,5.570795087890625Q17.4095,5.484525087890625,17.6357,5.484525087890625Q17.9694,5.484525087890625,18.1842,5.697745087890625Q18.4007,5.909335087890625,18.4007,6.2543850878906255Q18.4007,6.604315087890625,18.1842,6.822415087890625Q17.9694,7.0405150878906255,17.6292,7.0405150878906255Q17.3298,7.0405150878906255,17.119799999999998,6.890775087890625Q16.9098,6.739415087890626,16.825200000000002,6.474115087890625L16.3597,6.749175087890626Q16.470399999999998,7.110505087890624,16.807299999999998,7.335115087890625Q17.144199999999998,7.559725087890625,17.6292,7.559725087890625Q18.0296,7.559725087890625,18.3438,7.392075087890625Q18.6595,7.224435087890625,18.832,6.929835087890625ZM10,10.634915087890626C10,11.024655087890626,9.85136,11.379685087890625,9.60768,11.646395087890625L12.1689,15.171615087890626C12.2754,15.147615087890625,12.3862,15.134915087890626,12.5,15.134915087890626C12.5965,15.134915087890626,12.6908,15.144015087890624,12.7823,15.161415087890624L16.108800000000002,11.196955087890625C16.0387,11.023375087890624,16,10.833655087890625,16,10.634915087890626C16,9.806495087890625,16.671599999999998,9.134915087890626,17.5,9.134915087890626C18.3284,9.134915087890626,19,9.806495087890625,19,10.634915087890626C19,11.463345087890625,18.3284,12.134915087890626,17.5,12.134915087890626C17.2395,12.134915087890626,16.994500000000002,12.068505087890625,16.781,11.951675087890624L13.6547,15.677415087890624C13.8703,15.937215087890625,14,16.270915087890625,14,16.634915087890626C14,17.463315087890624,13.3284,18.134915087890626,12.5,18.134915087890626C11.67157,18.134915087890626,11,17.463315087890624,11,16.634915087890626C11,16.284415087890626,11.12019,15.962015087890626,11.3216,15.706715087890625L8.71539,12.119565087890624C8.645050000000001,12.129685087890625,8.57314,12.134915087890626,8.5,12.134915087890626C8.162099999999999,12.134915087890626,7.8503,12.023195087890626,7.59952,11.834665087890626L4.50558,15.521915087890624C4.80921,15.796415087890624,5,16.193415087890624,5,16.634915087890626C5,17.463315087890624,4.32843,18.134915087890626,3.5,18.134915087890626C2.671573,18.134915087890626,2,17.463315087890624,2,16.634915087890626C2,15.806515087890626,2.671573,15.134915087890626,3.5,15.134915087890626C3.5082500000000003,15.134915087890626,3.51648,15.135015087890626,3.5247,15.135115087890625L7.03382,10.953115087890625C7.01167,10.850565087890626,7,10.744105087890624,7,10.634915087890626C7,9.806495087890625,7.67157,9.134915087890626,8.5,9.134915087890626C9.32843,9.134915087890626,10,9.806495087890625,10,10.634915087890626Z stroke-opacity=0 stroke=none>');
const Lb = () => mb();
var xb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M18.8532,7.020985087890625Q19.0257,6.734525087890625,19.0257,6.369945087890625Q19.0257,6.020005087890625,18.8499,5.754705087890625Q18.6758,5.489415087890626,18.3649,5.339675087890625Q18.5944,5.209465087890625,18.7214,4.994615087890625Q18.8499,4.779775087890625,18.8499,4.5193550878906255Q18.8499,4.2003480878906245,18.7002,3.951324087890625Q18.5505,3.700673087890625,18.277,3.557444087890625Q18.0052,3.414215087890625,17.6455,3.414215087890625Q17.285800000000002,3.414215087890625,17.0107,3.557444087890625Q16.7357,3.700673087890625,16.5843,3.951324087890625Q16.4346,4.2003480878906245,16.4346,4.5193550878906255Q16.4346,4.779775087890625,16.561500000000002,4.994615087890625Q16.6901,5.209465087890625,16.919600000000003,5.339675087890625Q16.6055,5.489415087890626,16.4297,5.757965087890625Q16.255499999999998,6.024895087890625,16.255499999999998,6.369945087890625Q16.255499999999998,6.734525087890625,16.4297,7.020985087890625Q16.6055,7.305815087890625,16.919600000000003,7.465325087890625Q17.2354,7.624825087890625,17.6455,7.624825087890625Q18.0557,7.624825087890625,18.3682,7.465325087890625Q18.6807,7.305815087890625,18.8532,7.020985087890625ZM8.76432,7.559725087890625L8.13444,7.559725087890625L8.13444,4.214996087890625L7.28971,4.700025087890625L7.2946,4.070139087890625L8.310220000000001,3.479319087890625L8.76432,3.479319087890625L8.76432,7.559725087890625ZM17.1816,4.955555087890625Q17.0042,4.784655087890625,17.0042,4.5095950878906255Q17.0042,4.229645087890625,17.18,4.057119087890625Q17.355800000000002,3.884592087890625,17.6455,3.884592087890625Q17.935200000000002,3.884592087890625,18.1077,4.057119087890625Q18.2803,4.229645087890625,18.2803,4.5095950878906255Q18.2803,4.784655087890625,18.1045,4.955555087890625Q17.930300000000003,5.124825087890625,17.6455,5.124825087890625Q17.3607,5.124825087890625,17.1816,4.955555087890625ZM18.2217,5.7953950878906255Q18.4398,6.005365087890625,18.4398,6.3552950878906245Q18.4398,6.705235087890625,18.2217,6.915195087890625Q18.0052,7.125155087890625,17.6455,7.125155087890625Q17.285800000000002,7.125155087890625,17.067700000000002,6.915195087890625Q16.849600000000002,6.705235087890625,16.849600000000002,6.3552950878906245Q16.849600000000002,6.005365087890625,17.064500000000002,5.7953950878906255Q17.2793,5.585435087890625,17.6455,5.585435087890625Q18.0052,5.585435087890625,18.2217,5.7953950878906255ZM9.60768,11.711495087890626C9.85136,11.444785087890626,10,11.089765087890626,10,10.700025087890625C10,9.871595087890626,9.32843,9.200025087890625,8.5,9.200025087890625C7.67157,9.200025087890625,7,9.871595087890626,7,10.700025087890625C7,10.809205087890625,7.01167,10.915665087890625,7.03382,11.018215087890624L3.5247,15.200215087890625C3.51648,15.200115087890625,3.5082500000000003,15.200015087890625,3.5,15.200015087890625C2.671573,15.200015087890625,2,15.871615087890625,2,16.700015087890627C2,17.528415087890625,2.671573,18.200015087890627,3.5,18.200015087890627C4.32843,18.200015087890627,5,17.528415087890625,5,16.700015087890627C5,16.258515087890625,4.80921,15.861515087890625,4.50558,15.587015087890626L7.59952,11.899765087890625C7.8503,12.088295087890625,8.162099999999999,12.200025087890625,8.5,12.200025087890625C8.57314,12.200025087890625,8.645050000000001,12.194785087890626,8.71539,12.184675087890625L11.3216,15.771815087890625C11.12019,16.027215087890625,11,16.349515087890623,11,16.700015087890627C11,17.528415087890625,11.67157,18.200015087890627,12.5,18.200015087890627C13.3284,18.200015087890627,14,17.528415087890625,14,16.700015087890627C14,16.336015087890623,13.8703,16.002315087890626,13.6547,15.742515087890625L16.781,12.016775087890625C16.994500000000002,12.133605087890626,17.2395,12.200025087890625,17.5,12.200025087890625C18.3284,12.200025087890625,19,11.528445087890624,19,10.700025087890625C19,9.871595087890626,18.3284,9.200025087890625,17.5,9.200025087890625C16.671599999999998,9.200025087890625,16,9.871595087890626,16,10.700025087890625C16,10.898765087890624,16.0387,11.088475087890625,16.108800000000002,11.262055087890625L12.7823,15.226515087890625C12.6908,15.209115087890625,12.5965,15.200015087890625,12.5,15.200015087890625C12.3862,15.200015087890625,12.2754,15.212715087890626,12.1689,15.236715087890625L9.60768,11.711495087890626Z stroke-opacity=0 stroke=none>');
const $b = () => xb();
var bb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M9.474616630859375,7.494615087890625L8.844736630859375,7.494615087890625L8.844736630859375,4.149892087890625L8.000006630859374,4.634915087890625L8.004896630859374,4.005035087890625L9.020516630859376,3.414215087890625L9.474616630859375,3.414215087890625L9.474616630859375,7.494615087890625ZM18.529296630859378,4.8318550878906255Q18.307996630859375,5.028795087890625,18.122396630859377,5.385245087890625Q17.868496630859376,5.019035087890625,17.629196630859376,4.8269750878906255Q17.389996630859375,4.634915087890625,17.168596630859376,4.634915087890625Q16.794296630859375,4.634915087890625,16.522496630859376,4.976715087890625Q16.252296630859377,5.3168850878906255,16.252296630859377,5.7856350878906255Q16.252296630859377,6.218575087890625,16.502896630859375,6.521315087890625Q16.755196630859373,6.822415087890625,17.114896630859377,6.822415087890625Q17.368796630859375,6.822415087890625,17.588596630859374,6.625475087890624Q17.809896630859377,6.428535087890625,17.998696630859374,6.0688350878906245Q18.249396630859373,6.439935087890625,18.488596630859377,6.631985087890625Q18.727896630859377,6.822415087890625,18.952496630859375,6.822415087890625Q19.326796630859373,6.822415087890625,19.596996630859376,6.482245087890625Q19.868796630859375,6.140455087890626,19.868796630859375,5.671705087890626Q19.868796630859375,5.238755087890625,19.618196630859376,4.937655087890625Q19.367496630859375,4.634915087890625,19.006196630859375,4.634915087890625Q18.750696630859377,4.634915087890625,18.529296630859378,4.8318550878906255ZM18.337296630859377,5.674955087890625L18.278696630859375,5.596835087890625Q18.449596630859375,5.272935087890625,18.622096630859374,5.1101750878906245Q18.794596630859374,4.947415087890625,18.967096630859373,4.947415087890625Q19.194996630859375,4.947415087890625,19.346396630859374,5.1345950878906255Q19.497696630859377,5.320135087890625,19.497696630859377,5.598455087890625Q19.497696630859377,5.8914250878906245,19.360996630859376,6.096505087890625Q19.224296630859374,6.301585087890626,19.027396630859375,6.301585087890626Q18.915096630859374,6.301585087890626,18.742496630859375,6.146965087890624Q18.569996630859375,5.992335087890625,18.337296630859377,5.674955087890625ZM17.785496630859377,5.779125087890625L17.842496630859372,5.857245087890625Q17.668296630859373,6.186025087890625,17.495796630859374,6.348785087890625Q17.324896630859374,6.509915087890625,17.153996630859375,6.509915087890625Q16.926096630859377,6.509915087890625,16.774796630859377,6.324375087890624Q16.623396630859375,6.137195087890625,16.623396630859375,5.858875087890625Q16.623396630859375,5.565905087890625,16.761696630859376,5.360825087890625Q16.900096630859373,5.1557550878906255,17.095396630859376,5.1557550878906255Q17.228896630859374,5.1557550878906255,17.365596630859375,5.2778250878906245Q17.502296630859377,5.399895087890625,17.785496630859377,5.779125087890625ZM10.710296630859375,10.634915087890626C10.710296630859375,11.024655087890626,10.561656630859375,11.379685087890625,10.317976630859375,11.646395087890625L12.879196630859376,15.171615087890626C12.985696630859374,15.147615087890625,13.096496630859376,15.134915087890626,13.210296630859375,15.134915087890626C13.306796630859376,15.134915087890626,13.401096630859374,15.144015087890624,13.492596630859374,15.161415087890624L16.819096630859377,11.196955087890625C16.748996630859374,11.023375087890624,16.710296630859375,10.833655087890625,16.710296630859375,10.634915087890626C16.710296630859375,9.806495087890625,17.381896630859373,9.134915087890626,18.210296630859375,9.134915087890626C19.038696630859373,9.134915087890626,19.710296630859375,9.806495087890625,19.710296630859375,10.634915087890626C19.710296630859375,11.463345087890625,19.038696630859373,12.134915087890626,18.210296630859375,12.134915087890626C17.949796630859375,12.134915087890626,17.704796630859377,12.068505087890625,17.491296630859374,11.951675087890624L14.364996630859375,15.677415087890624C14.580596630859375,15.937215087890625,14.710296630859375,16.270915087890625,14.710296630859375,16.634915087890626C14.710296630859375,17.463315087890624,14.038696630859375,18.134915087890626,13.210296630859375,18.134915087890626C12.381866630859374,18.134915087890626,11.710296630859375,17.463315087890624,11.710296630859375,16.634915087890626C11.710296630859375,16.284415087890626,11.830486630859374,15.962015087890626,12.031896630859375,15.706715087890625L9.425686630859374,12.119565087890624C9.355346630859376,12.129685087890625,9.283436630859375,12.134915087890626,9.210296630859375,12.134915087890626C8.872396630859374,12.134915087890626,8.560596630859376,12.023195087890626,8.309816630859375,11.834665087890626L5.215876630859375,15.521915087890624C5.519506630859375,15.796415087890624,5.710296630859375,16.193415087890624,5.710296630859375,16.634915087890626C5.710296630859375,17.463315087890624,5.038726630859375,18.134915087890626,4.210296630859375,18.134915087890626C3.381869630859375,18.134915087890626,2.710296630859375,17.463315087890624,2.710296630859375,16.634915087890626C2.710296630859375,15.806515087890626,3.381869630859375,15.134915087890626,4.210296630859375,15.134915087890626C4.218546630859375,15.134915087890626,4.226776630859375,15.135015087890626,4.234996630859375,15.135115087890625L7.744116630859375,10.953115087890625C7.721966630859375,10.850565087890626,7.710296630859375,10.744105087890624,7.710296630859375,10.634915087890626C7.710296630859375,9.806495087890625,8.381866630859374,9.134915087890626,9.210296630859375,9.134915087890626C10.038726630859376,9.134915087890626,10.710296630859375,9.806495087890625,10.710296630859375,10.634915087890626Z stroke-opacity=0 stroke=none>');
const wb = () => bb();
var Ab = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M21,5.5C21,6.32843,20.3284,7,19.5,7C19.4136,7,19.3289,6.99269,19.2465,6.97866L15.6257,15.5086C15.8587,15.7729,16,16.119999999999997,16,16.5C16,17.328400000000002,15.3284,18,14.5,18C13.8469,18,13.2913,17.5826,13.0854,17L3.91465,17C3.70873,17.5826,3.15311,18,2.5,18C1.671573,18,1,17.328400000000002,1,16.5C1,15.6716,1.671573,15,2.5,15C2.5840199999999998,15,2.66643,15.0069,2.74668,15.0202L6.36934,6.48574C6.13933,6.22213,6,5.87733,6,5.5C6,4.671573,6.67157,4,7.5,4C8.15311,4,8.70873,4.417404,8.91465,5L18.0854,5C18.2913,4.417404,18.8469,4,19.5,4C20.3284,4,21,4.671573,21,5.5ZM18.0854,6L8.91465,6C8.892579999999999,6.06243,8.8665,6.12296,8.83672,6.18128L13.9814,15.0921C14.143,15.0325,14.3177,15,14.5,15C14.584,15,14.6664,15.0069,14.7467,15.0202L18.3693,6.48574C18.2462,6.3446,18.149,6.1802,18.0854,6ZM13.2036,15.745L8.0861,6.8811800000000005C7.90605,6.95768,7.70797,7,7.5,7C7.41359,7,7.32888,6.99269,7.24647,6.97866L3.62571,15.5086C3.7512,15.651,3.8501,15.8174,3.91465,16L13.0854,16C13.1169,15.9108,13.1566,15.8255,13.2036,15.745Z stroke-opacity=0 stroke=none>');
const Sb = () => Ab();
var Mb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M5.92159,5.93994C6.04014,5.90529,6.152620000000001,5.85639,6.25704,5.79523L9.12729,9.89437C9.045449999999999,10.07959,9,10.28449,9,10.5C9,10.79522,9.08529,11.07053,9.232569999999999,11.30262L4.97573,16.7511L5.92159,5.93994ZM4.92259,5.8848400000000005C4.38078,5.658659999999999,4,5.1238,4,4.5C4,3.671573,4.67157,3,5.5,3C6.2157,3,6.81433,3.50124,6.96399,4.17183L15.1309,4.88634C15.3654,4.36387,15.8902,4,16.5,4C17.328400000000002,4,18,4.67157,18,5.5C18,6.08983,17.659599999999998,6.60015,17.1645,6.84518L18.4264,14.0018C18.4508,14.0006,18.4753,14,18.5,14C19.3284,14,20,14.6716,20,15.5C20,16.328400000000002,19.3284,17,18.5,17C17.932499999999997,17,17.4386,16.6849,17.183799999999998,16.22L5.99686,18.5979C5.946429999999999,19.3807,5.29554,20,4.5,20C3.671573,20,3,19.3284,3,18.5C3,17.869300000000003,3.389292,17.3295,3.94071,17.1077L4.92259,5.8848400000000005ZM5.72452,17.6334C5.69799,17.596,5.6698,17.5599,5.64004,17.525100000000002L10.01843,11.92103C10.16958,11.97223,10.33155,12,10.5,12C10.80059,12,11.08052,11.91158,11.31522,11.75934L17.0606,15.0765C17.0457,15.1271,17.0335,15.1789,17.023899999999998,15.2317L5.72452,17.6334ZM11.92855,10.95875L17.4349,14.1379L16.1699,6.96356C15.9874,6.92257,15.8174,6.8483,15.6667,6.74746L11.99771,10.4165C11.99923,10.44414,12,10.47198,12,10.5C12,10.66,11.97495,10.814160000000001,11.92855,10.95875ZM10.5,9C10.259830000000001,9,10.03285,9.05644,9.83159,9.15679L7.04919,5.1831L15.0493,5.88302C15.054,5.90072,15.059,5.91829,15.0643,5.9357299999999995L11.56066,9.43934C11.28921,9.16789,10.91421,9,10.5,9Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const Tb = () => Mb();
var Ib = /* @__PURE__ */ I('<svg viewBox="0 0 22 22"><path d=M4.727219638671875,8.007996215820313L9.973849638671876,2.7629472158203123C10.167279638671875,2.5696791158203123,10.480729638671875,2.5696791158203123,10.674169638671875,2.7629472158203123L13.223329638671874,5.311756215820313C13.416929638671874,5.505236215820313,13.416929638671874,5.8189862158203125,13.223329638671874,6.012466215820313L7.977129638671875,11.257906215820313C7.379859638671875,11.855176215820313,7.407609638671875,12.909396215820312,8.033809638671876,13.535596215820313C8.660409638671876,14.162596215820313,9.713849638671874,14.189996215820312,10.311129638671876,13.591896215820313L15.556929638671875,8.346066215820311C15.750429638671875,8.152526215820313,16.064229638671875,8.152526215820313,16.257629638671872,8.346066215820311L18.806529638671876,10.895266215820312C19.000029638671876,11.088746215820313,19.000029638671876,11.402496215820312,18.806529638671876,11.595976215820313L13.560629638671875,16.841796215820313C11.165619638671876,19.237196215820312,7.197149638671875,19.19919621582031,4.783499638671875,16.785496215820313C2.3698426386718747,14.371896215820312,2.331397638671875,10.403416215820313,4.727219638671875,8.007996215820313ZM12.172299638671875,5.662106215820312L10.323809638671875,3.8136162158203124L5.4287196386718755,8.709096215820313C3.422893638671875,10.714536215820312,3.4549956386718748,14.055196215820313,5.484999638671875,16.08479621582031C7.514609638671875,18.114796215820313,10.855289638671875,18.146496215820314,12.860719638671876,16.141096215820312L15.465629638671874,13.535796215820312L14.090929638671875,12.160756215820312L14.791629638671875,11.460436215820312L16.166229638671876,12.834996215820313L17.755829638671877,11.245226215820313L15.907729638671874,9.396736215820312L11.011839638671875,14.292596215820312C10.042809638671875,15.262396215820312,8.418249638671874,15.243796215820312,7.406019638671875,14.306496215820312L7.333099638671875,14.236296215820312C6.327599638671876,13.230796215820313,6.284009638671876,11.550396215820312,7.276419638671875,10.557586215820312L9.882199638671874,7.952026215820313L8.501079638671875,6.570906215820313L9.201789638671876,5.870186215820313L10.582939638671874,7.251336215820312L12.172299638671875,5.662106215820312Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const kb = (n) => (() => {
  var a = Ib();
  return ve(a, "class", `icon-overlay ${n ?? ""}`), a;
})();
var Eb = /* @__PURE__ */ I('<svg viewBox="0 0 22 22"><defs><clipPath id=master_svg0_151_615><rect x=0 y=0 width=22 height=22 rx=0></rect></clipPath></defs><g clip-path=url(#master_svg0_151_615)><path d=M19.672,3.0673368C19.4417,2.9354008,19.1463,3.00292252,18.9994,3.2210900000000002L17.4588,5.50622L16.743299999999998,3.781253L13.9915,7.4662L13.9618,7.51108C13.8339,7.72862,13.8936,8.005659999999999,14.1004,8.15391L14.1462,8.183430000000001C14.3683,8.308720000000001,14.6511,8.25001,14.8022,8.047229999999999L16.4907,5.78571L17.246299999999998,7.60713L19.8374,3.7635389999999997L19.8651,3.717088C19.9871,3.484615,19.9023,3.199273,19.672,3.0673368ZM4.79974,8.462530000000001L10.117740000000001,3.252975C10.31381,3.0610145,10.63152,3.0610145,10.82759,3.252975L13.4115,5.78453C13.6076,5.976710000000001,13.6076,6.28833,13.4115,6.4805L8.093869999999999,11.69045C7.48847,12.28368,7.51659,13.3308,8.151309999999999,13.9528C8.786439999999999,14.5755,9.85421,14.6027,10.45961,14.0087L15.7768,8.79831C15.9729,8.60609,16.2909,8.60609,16.487099999999998,8.79831L19.0705,11.33026C19.2667,11.52244,19.2667,11.83406,19.0705,12.02623L13.7533,17.2366C11.32572,19.6158,7.30328,19.578,4.85679,17.1807C2.410298,14.7834,2.371331,10.84174,4.79974,8.462530000000001ZM12.3461,6.1325199999999995L10.47246,4.29654L5.51079,9.15889C3.477674,11.15076,3.510214,14.4688,5.56784,16.4847C7.62506,18.500999999999998,11.01117,18.5325,13.0439,16.540599999999998L15.6842,13.9529L14.2908,12.58718L15.0011,11.89161L16.394399999999997,13.2569L18.0056,11.67786L16.1323,9.84188L11.16985,14.7046C10.18764,15.6679,8.540980000000001,15.6494,7.51498,14.7184L7.44107,14.6487C6.4219,13.65,6.37771,11.98096,7.38362,10.994869999999999L10.02485,8.40693L8.624939999999999,7.03516L9.335180000000001,6.33919L10.73512,7.71099L12.3461,6.1325199999999995Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const Pb = (n) => (() => {
  var a = Eb();
  return ve(a, "class", `icon-overlay ${n ?? ""}`), a;
})();
var Ob = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M11,17C5.80945,17,3.667717,12.85,3.113386,11.575C2.9622047,11.2,2.9622047,10.8,3.113386,10.425C3.667717,9.15,5.80945,5,11,5C16.165399999999998,5,18.3323,9.15,18.8866,10.425C19.0378,10.8,19.0378,11.2,18.8866,11.575C18.3323,12.85,16.165399999999998,17,11,17ZM4.04567,10.8C3.995276,10.925,3.995276,11.05,4.04567,11.175C4.52441,12.325,6.43937,16,11,16C15.5606,16,17.4756,12.325,17.9543,11.2C18.0047,11.075,18.0047,10.95,17.9543,10.825C17.4756,9.675,15.5606,6,11,6C6.43937,6,4.52441,9.675,4.04567,10.8ZM11,13.5C9.61417,13.5,8.480319999999999,12.375,8.480319999999999,11C8.480319999999999,9.625,9.61417,8.5,11,8.5C12.38583,8.5,13.5197,9.625,13.5197,11C13.5197,12.375,12.38583,13.5,11,13.5ZM11,9.5C10.1685,9.5,9.48819,10.175,9.48819,11C9.48819,11.825,10.1685,12.5,11,12.5C11.8315,12.5,12.51181,11.825,12.51181,11C12.51181,10.175,11.8315,9.5,11,9.5Z stroke-opacity=0 fill-opacity=1>');
const Db = () => Ob();
var Rb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M5.80417,14.9887L4.62563,16.167299999999997C4.43037,16.3625,4.43037,16.6791,4.62563,16.8744C4.82089,17.0696,5.13748,17.0696,5.332739999999999,16.8744L6.62638,15.5807C7.75595,16.290100000000002,9.19328,16.7929,11,16.7929C16.165399999999998,16.7929,18.3323,12.64289,18.8866,11.36789C19.0378,10.99289,19.0378,10.59289,18.8866,10.21789C18.5549,9.45486,17.6456,7.66212,15.8617,6.34545L17.3536,4.853553C17.5488,4.658291,17.5488,4.341709,17.3536,4.146447C17.1583,3.9511845,16.8417,3.9511845,16.6464,4.146447L15.0014,5.7915399999999995C13.9314,5.1969,12.61166,4.792893,11,4.792893C5.80945,4.792893,3.667717,8.94289,3.113386,10.21789C2.9622049,10.59289,2.9622049,10.99289,3.113386,11.36789C3.424435,12.08333,4.2353000000000005,13.70399,5.80417,14.9887ZM7.36012,14.847C8.32327,15.4074,9.52286,15.7929,11,15.7929C15.5606,15.7929,17.4756,12.11789,17.9543,10.99289C18.0047,10.86789,18.0047,10.74289,17.9543,10.61789C17.659,9.90846,16.8171,8.23812,15.1447,7.06241L12.96929,9.23782C13.3134,9.66543,13.5197,10.20642,13.5197,10.79289C13.5197,12.16789,12.38583,13.29289,11,13.29289C10.41596,13.29289,9.87667,13.09308,9.44815,12.75896L7.36012,14.847ZM8.794609999999999,11.99829L6.520099999999999,14.2728C5.06905,13.12119,4.32057,11.628250000000001,4.04567,10.96789C3.995275,10.84289,3.995275,10.71789,4.04567,10.59289C4.52441,9.46789,6.43937,5.79289,11,5.79289C12.28868,5.79289,13.3661,6.086320000000001,14.2596,6.53329L12.19759,8.5953C11.84086,8.40257,11.43271,8.29289,11,8.29289C9.61417,8.29289,8.480319999999999,9.41789,8.480319999999999,10.79289C8.480319999999999,11.22918,8.594470000000001,11.64029,8.794609999999999,11.99829ZM10.16528,12.04183C10.404869999999999,12.20032,10.692070000000001,12.29289,11,12.29289C11.8315,12.29289,12.51181,11.61789,12.51181,10.79289C12.51181,10.48318,12.41593,10.194600000000001,12.25216,9.95494L10.16528,12.04183ZM11.43602,9.35687L9.55616,11.236740000000001C9.512,11.09633,9.48819,10.94724,9.48819,10.79289C9.48819,9.96789,10.1685,9.29289,11,9.29289C11.15142,9.29289,11.29782,9.31528,11.43602,9.35687Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const Bb = () => Rb();
var Fb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><defs><clipPath id=master_svg0_151_625><rect x=0 y=0 width=22 height=22 rx=0></rect></clipPath></defs><g clip-path=url(#master_svg0_151_625)><path d=M14.5385,9.76923L15.6538,9.76923C16.6538,9.76923,17.4615,10.576920000000001,17.4615,11.576920000000001L17.4615,17.1923C17.4615,18.1923,16.6538,19,15.6538,19L5.80769,19C4.807692,19,4,18.1923,4,17.1923L4,11.576920000000001C4,10.576920000000001,4.807692,9.76923,5.80769,9.76923L7.23077,9.76923L7.23077,7.576919999999999C7.23077,5.61538,8.88462,4,10.88462,4C12.88462,4,14.5385,5.61538,14.5385,7.576919999999999L14.5385,9.76923ZM10.88461,5.15385C9.5,5.15385,8.38461,6.23077,8.38461,7.576919999999999L8.38461,9.76923L13.38462,9.76923L13.38462,7.576919999999999C13.38462,6.23077,12.26923,5.15385,10.88461,5.15385ZM15.6538,17.8462C16,17.8462,16.3077,17.5385,16.3077,17.1923L16.3077,11.576920000000001C16.3077,11.23077,16,10.923079999999999,15.6538,10.923079999999999L5.80769,10.923079999999999C5.46154,10.923079999999999,5.15385,11.23077,5.15385,11.576920000000001L5.15385,17.1923C5.15385,17.5385,5.46154,17.8462,5.80769,17.8462L15.6538,17.8462ZM10.153839999999999,12.65385C10.153839999999999,12.34615,10.42307,12.07692,10.73076,12.07692C11.038450000000001,12.07692,11.307680000000001,12.34615,11.307680000000001,12.65385L11.307680000000001,14.5769C11.307680000000001,14.8846,11.038450000000001,15.1538,10.73076,15.1538C10.42307,15.1538,10.153839999999999,14.8846,10.153839999999999,14.5769L10.153839999999999,12.65385Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const Nb = () => Fb();
var Kb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><defs><clipPath id=master_svg0_151_620><rect x=0 y=0 width=22 height=22 rx=0></rect></clipPath></defs><g clip-path=url(#master_svg0_151_620)><path d=M8.38461,9.76923L15.6538,9.76923C16.6538,9.76923,17.4615,10.576920000000001,17.4615,11.576920000000001L17.4615,17.1923C17.4615,18.1923,16.6538,19,15.6538,19L5.80769,19C4.807692,19,4,18.1923,4,17.1923L4,11.576920000000001C4,10.576920000000001,4.807693,9.76923,5.80769,9.76923L7.23077,9.76923L7.23077,7.576919999999999C7.23077,5.61538,8.88462,4,10.88462,4C12.46154,4,13.84615,4.961539,14.3462,6.423080000000001C14.4615,6.73077,14.3077,7.038460000000001,14,7.15385C13.69231,7.26923,13.38461,7.11538,13.26923,6.80769C12.92308,5.80769,11.96154,5.15385,10.88462,5.15385C9.5,5.15385,8.38461,6.23077,8.38461,7.576919999999999L8.38461,9.76923ZM15.6538,17.8462C16,17.8462,16.3077,17.5385,16.3077,17.1923L16.3077,11.576920000000001C16.3077,11.23077,16,10.923079999999999,15.6538,10.923079999999999L5.80769,10.923079999999999C5.46154,10.923079999999999,5.15385,11.23077,5.15385,11.576920000000001L5.15385,17.1923C5.15385,17.5385,5.46154,17.8462,5.80769,17.8462L15.6538,17.8462ZM10.153839999999999,12.65385C10.153839999999999,12.34615,10.42307,12.07692,10.73076,12.07692C11.03846,12.07692,11.307690000000001,12.34615,11.307690000000001,12.65385L11.307690000000001,14.5769C11.307690000000001,14.8846,11.03846,15.1538,10.73076,15.1538C10.42307,15.1538,10.153839999999999,14.8846,10.153839999999999,14.5769L10.153839999999999,12.65385Z stroke-opacity=0 fill-rule=evenodd fill-opacity=1>');
const Ub = () => Kb();
var Zb = /* @__PURE__ */ I('<svg class=icon-overlay viewBox="0 0 22 22"><path d=M16.966900000000003,8.67144C16.6669,8.67144,16.4247,8.91558,16.4247,9.21802L16.4247,16.631500000000003C16.4247,17.322,16.007199999999997,17.9068,15.5139,17.9068L13.93072,17.9068L13.93072,9.2162C13.93072,8.91741,13.68675,8.67144,13.38855,8.67144C13.09036,8.67144,12.84639,8.91741,12.84639,9.21802L12.84639,17.9068L10.151810000000001,17.9068L10.151810000000001,9.21802C10.151810000000001,8.91741,9.90783,8.67144,9.609639999999999,8.67144C9.31145,8.67144,9.06747,8.91741,9.06747,9.219850000000001L9.06747,17.9068L7.48614,17.9068C6.99277,17.9068,6.5753,17.322,6.5753,16.631500000000003L6.5753,9.21802C6.5753,8.91558,6.333130000000001,8.67144,6.03313,8.67144C5.73313,8.67144,5.49096,8.91558,5.49096,9.21802L5.49096,16.631500000000003C5.49096,17.9378,6.385540000000001,19,7.48614,19L15.512,19C16.6127,19,17.509,17.9378,17.509,16.631500000000003L17.509,9.21802C17.509,8.91558,17.2669,8.67144,16.966900000000003,8.67144ZM18.4578,6.21183L4.542169,6.21183C4.243976,6.21183,4,6.45779,4,6.75841C4,7.05903,4.243976,7.30499,4.542169,7.30499L18.4578,7.30499C18.756,7.30499,19,7.05903,19,6.75841C19,6.45779,18.756,6.21183,18.4578,6.21183ZM8.68072,5.10045L14.3193,5.10045C14.6175,5.10045,14.8614,4.852666,14.8614,4.550225C14.8614,4.247783,14.6175,4,14.3193,4L8.68072,4C8.38253,4,8.13855,4.247783,8.13855,4.550225C8.13855,4.852666,8.38253,5.10045,8.68072,5.10045Z stroke-opacity=0 fill-opacity=1>');
const Wb = () => Zb(), zb = {
  horizontalStraightLine: w$,
  horizontalRayLine: S$,
  horizontalSegment: T$,
  verticalStraightLine: k$,
  verticalRayLine: P$,
  verticalSegment: D$,
  straightLine: B$,
  rayLine: N$,
  segment: U$,
  arrow: W$,
  priceLine: Q$,
  priceChannelLine: G$,
  parallelStraightLine: V$,
  fibonacciLine: q$,
  fibonacciSegment: J$,
  fibonacciCircle: tb,
  fibonacciSpiral: rb,
  fibonacciSpeedResistanceFan: ab,
  fibonacciExtension: ob,
  gannBox: cb,
  circle: fb,
  triangle: gb,
  rect: _b,
  parallelogram: vb,
  threeWaves: yb,
  fiveWaves: Lb,
  eightWaves: $b,
  anyWaves: wb,
  abcd: Sb,
  xabcd: Tb,
  weak_magnet: kb,
  strong_magnet: Pb,
  lock: Nb,
  unlock: Ub,
  visible: Db,
  invisible: Bb,
  remove: Wb
};
function Qb(n) {
  return [
    { key: "horizontalStraightLine", text: P("horizontal_straight_line", n) },
    { key: "horizontalRayLine", text: P("horizontal_ray_line", n) },
    { key: "horizontalSegment", text: P("horizontal_segment", n) },
    { key: "verticalStraightLine", text: P("vertical_straight_line", n) },
    { key: "verticalRayLine", text: P("vertical_ray_line", n) },
    { key: "verticalSegment", text: P("vertical_segment", n) },
    { key: "straightLine", text: P("straight_line", n) },
    { key: "rayLine", text: P("ray_line", n) },
    { key: "segment", text: P("segment", n) },
    { key: "arrow", text: P("arrow", n) },
    { key: "priceLine", text: P("price_line", n) }
  ];
}
function Hb(n) {
  return [
    { key: "priceChannelLine", text: P("price_channel_line", n) },
    { key: "parallelStraightLine", text: P("parallel_straight_line", n) }
  ];
}
function Gb(n) {
  return [
    { key: "circle", text: P("circle", n) },
    { key: "rect", text: P("rect", n) },
    { key: "parallelogram", text: P("parallelogram", n) },
    { key: "triangle", text: P("triangle", n) }
  ];
}
function Yb(n) {
  return [
    { key: "fibonacciLine", text: P("fibonacci_line", n) },
    { key: "fibonacciSegment", text: P("fibonacci_segment", n) },
    { key: "fibonacciCircle", text: P("fibonacci_circle", n) },
    { key: "fibonacciSpiral", text: P("fibonacci_spiral", n) },
    { key: "fibonacciSpeedResistanceFan", text: P("fibonacci_speed_resistance_fan", n) },
    { key: "fibonacciExtension", text: P("fibonacci_extension", n) },
    { key: "gannBox", text: P("gann_box", n) }
  ];
}
function Vb(n) {
  return [
    { key: "xabcd", text: P("xabcd", n) },
    { key: "abcd", text: P("abcd", n) },
    { key: "threeWaves", text: P("three_waves", n) },
    { key: "fiveWaves", text: P("five_waves", n) },
    { key: "eightWaves", text: P("eight_waves", n) },
    { key: "anyWaves", text: P("any_waves", n) }
  ];
}
function Xb(n) {
  return [
    { key: "weak_magnet", text: P("weak_magnet", n) },
    { key: "strong_magnet", text: P("strong_magnet", n) }
  ];
}
const de = (n) => zb[n.name](n.class);
var qb = /* @__PURE__ */ I('<div class=klinecharts-pro-drawing-bar><span class=split-line></span><div class=item tabindex=0><span style=width:32px;height:32px></span><div class=icon-arrow><svg viewBox="0 0 4 6"><path d=M1.07298,0.159458C0.827521,-0.0531526,0.429553,-0.0531526,0.184094,0.159458C-0.0613648,0.372068,-0.0613648,0.716778,0.184094,0.929388L2.61275,3.03303L0.260362,5.07061C0.0149035,5.28322,0.0149035,5.62793,0.260362,5.84054C0.505822,6.05315,0.903789,6.05315,1.14925,5.84054L3.81591,3.53075C4.01812,3.3556,4.05374,3.0908,3.92279,2.88406C3.93219,2.73496,3.87113,2.58315,3.73964,2.46925L1.07298,0.159458Z stroke=none stroke-opacity=0></path></svg></div></div><div class=item><span style=width:32px;height:32px></span></div><div class=item><span style=width:32px;height:32px></span></div><span class=split-line></span><div class=item><span style=width:32px;height:32px>'), jb = /* @__PURE__ */ I('<div class=item tabindex=0><span style=width:32px;height:32px></span><div class=icon-arrow><svg viewBox="0 0 4 6"><path d=M1.07298,0.159458C0.827521,-0.0531526,0.429553,-0.0531526,0.184094,0.159458C-0.0613648,0.372068,-0.0613648,0.716778,0.184094,0.929388L2.61275,3.03303L0.260362,5.07061C0.0149035,5.28322,0.0149035,5.62793,0.260362,5.84054C0.505822,6.05315,0.903789,6.05315,1.14925,5.84054L3.81591,3.53075C4.01812,3.3556,4.05374,3.0908,3.92279,2.88406C3.93219,2.73496,3.87113,2.58315,3.73964,2.46925L1.07298,0.159458Z stroke=none stroke-opacity=0>'), Z2 = /* @__PURE__ */ I("<li><span style=padding-left:8px>");
const W2 = "drawing_tools", Jb = (n) => {
  const [a, i] = V("horizontalStraightLine"), [u, f] = V("priceChannelLine"), [g, d] = V("circle"), [p, m] = V("fibonacciLine"), [S, x] = V("xabcd"), [M, D] = V("weak_magnet"), [z, t1] = V("normal"), [p1, n1] = V(!1), [i1, G] = V(!0), [U, q] = V(""), $1 = A1(() => [{
    key: "singleLine",
    icon: a(),
    list: Qb(n.locale),
    setter: i
  }, {
    key: "moreLine",
    icon: u(),
    list: Hb(n.locale),
    setter: f
  }, {
    key: "polygon",
    icon: g(),
    list: Gb(n.locale),
    setter: d
  }, {
    key: "fibonacci",
    icon: p(),
    list: Yb(n.locale),
    setter: m
  }, {
    key: "wave",
    icon: S(),
    list: Vb(n.locale),
    setter: x
  }]), R1 = A1(() => Xb(n.locale));
  return (() => {
    var M1 = qb(), s1 = M1.firstChild, l1 = s1.nextSibling, h1 = l1.firstChild, j1 = h1.nextSibling, Gt = j1.firstChild, Yt = l1.nextSibling, rt = Yt.firstChild, Pe = Yt.nextSibling, yt = Pe.firstChild, oe = Pe.nextSibling, J1 = oe.nextSibling, mt = J1.firstChild;
    return F(M1, () => $1().map((a1) => (() => {
      var u1 = jb(), ee = u1.firstChild, we = ee.nextSibling, it = we.firstChild;
      return u1.addEventListener("blur", () => {
        q("");
      }), ee.$$click = () => {
        n.onDrawingItemClick({
          groupId: W2,
          name: a1.icon,
          visible: i1(),
          lock: p1(),
          mode: z()
        });
      }, F(ee, B(de, {
        get name() {
          return a1.icon;
        }
      })), we.$$click = () => {
        a1.key === U() ? q("") : q(a1.key);
      }, F(u1, (() => {
        var Ce = A1(() => a1.key === U());
        return () => Ce() && B($0, {
          class: "list",
          get children() {
            return a1.list.map((T) => (() => {
              var A = Z2(), E = A.firstChild;
              return A.$$click = () => {
                a1.setter(T.key), n.onDrawingItemClick({
                  name: T.key,
                  lock: p1(),
                  mode: z()
                }), q("");
              }, F(A, B(de, {
                get name() {
                  return T.key;
                }
              }), E), F(E, () => T.text), A;
            })());
          }
        });
      })(), null), P1(() => ve(it, "class", a1.key === U() ? "rotate" : "")), u1;
    })()), s1), l1.addEventListener("blur", () => {
      q("");
    }), h1.$$click = () => {
      let a1 = M();
      z() !== "normal" && (a1 = "normal"), t1(a1), n.onModeChange(a1);
    }, F(h1, (() => {
      var a1 = A1(() => M() === "weak_magnet");
      return () => a1() ? (() => {
        var u1 = A1(() => z() === "weak_magnet");
        return () => u1() ? B(de, {
          name: "weak_magnet",
          class: "selected"
        }) : B(de, {
          name: "weak_magnet"
        });
      })() : (() => {
        var u1 = A1(() => z() === "strong_magnet");
        return () => u1() ? B(de, {
          name: "strong_magnet",
          class: "selected"
        }) : B(de, {
          name: "strong_magnet"
        });
      })();
    })()), j1.$$click = () => {
      U() === "mode" ? q("") : q("mode");
    }, F(l1, (() => {
      var a1 = A1(() => U() === "mode");
      return () => a1() && B($0, {
        class: "list",
        get children() {
          return R1().map((u1) => (() => {
            var ee = Z2(), we = ee.firstChild;
            return ee.$$click = () => {
              D(u1.key), t1(u1.key), n.onModeChange(u1.key), q("");
            }, F(ee, B(de, {
              get name() {
                return u1.key;
              }
            }), we), F(we, () => u1.text), ee;
          })());
        }
      });
    })(), null), rt.$$click = () => {
      const a1 = !p1();
      n1(a1), n.onLockChange(a1);
    }, F(rt, (() => {
      var a1 = A1(() => !!p1());
      return () => a1() ? B(de, {
        name: "lock"
      }) : B(de, {
        name: "unlock"
      });
    })()), yt.$$click = () => {
      const a1 = !i1();
      G(a1), n.onVisibleChange(a1);
    }, F(yt, (() => {
      var a1 = A1(() => !!i1());
      return () => a1() ? B(de, {
        name: "visible"
      }) : B(de, {
        name: "invisible"
      });
    })()), mt.$$click = () => {
      n.onRemoveClick(W2);
    }, F(mt, B(de, {
      name: "remove"
    })), P1(() => ve(Gt, "class", U() === "mode" ? "rotate" : "")), M1;
  })();
};
ke(["click"]);
var z2 = /* @__PURE__ */ I("<li class=title>"), Q2 = /* @__PURE__ */ I("<li class=row>");
const ew = (n) => B(yn, {
  get title() {
    return P("indicator", n.locale);
  },
  width: 400,
  get onClose() {
    return n.onClose;
  },
  get children() {
    return B($0, {
      class: "klinecharts-pro-indicator-modal-list",
      get children() {
        return [(() => {
          var a = z2();
          return F(a, () => P("main_indicator", n.locale)), a;
        })(), A1(() => ["MA", "EMA", "SMA", "BOLL", "SAR", "BBI"].map((a) => {
          const i = n.mainIndicators.includes(a);
          return (() => {
            var u = Q2();
            return u.$$click = (f) => {
              n.onMainIndicatorChange({
                name: a,
                paneId: "candle_pane",
                added: !i
              });
            }, F(u, B(U2, {
              checked: i,
              get label() {
                return P(a.toLowerCase(), n.locale);
              }
            })), u;
          })();
        })), (() => {
          var a = z2();
          return F(a, () => P("sub_indicator", n.locale)), a;
        })(), A1(() => ["MA", "EMA", "VOL", "MACD", "BOLL", "KDJ", "RSI", "BIAS", "BRAR", "CCI", "DMI", "CR", "PSY", "DMA", "TRIX", "OBV", "VR", "WR", "MTM", "EMV", "SAR", "SMA", "ROC", "PVT", "BBI", "AO"].map((a) => {
          const i = a in n.subIndicators;
          return (() => {
            var u = Q2();
            return u.$$click = (f) => {
              n.onSubIndicatorChange({
                name: a,
                paneId: n.subIndicators[a] ?? "",
                added: !i
              });
            }, F(u, B(U2, {
              checked: i,
              get label() {
                return P(a.toLowerCase(), n.locale);
              }
            })), u;
          })();
        }))];
      }
    });
  }
});
ke(["click"]);
const d9 = {
  "Etc/UTC": "utc",
  "Pacific/Honolulu": "honolulu",
  "America/Juneau": "juneau",
  "America/Los_Angeles": "los_angeles",
  "America/Chicago": "chicago",
  "America/Toronto": "toronto",
  "America/Sao_Paulo": "sao_paulo",
  "Europe/London": "london",
  "Europe/Berlin": "berlin",
  "Asia/Bahrain": "bahrain",
  "Asia/Dubai": "dubai",
  "Asia/Ashkhabad": "ashkhabad",
  "Asia/Almaty": "almaty",
  "Asia/Bangkok": "bangkok",
  "Asia/Shanghai": "shanghai",
  "Asia/Tokyo": "tokyo",
  "Australia/Sydney": "sydney",
  "Pacific/Norfolk": "norfolk"
};
function H2(n, a) {
  return P(d9[n], a);
}
function tw(n) {
  return Object.keys(d9).map((a) => ({
    key: a,
    text: P(d9[a], n)
  }));
}
const nw = (n) => {
  const [a, i] = V(n.timezone), u = A1(() => tw(n.locale));
  return B(yn, {
    get title() {
      return P("timezone", n.locale);
    },
    width: 320,
    get buttons() {
      return [{
        children: P("confirm", n.locale),
        onClick: () => {
          n.onConfirm(a()), n.onClose();
        }
      }];
    },
    get onClose() {
      return n.onClose;
    },
    get children() {
      return B(E3, {
        style: {
          width: "100%",
          "margin-top": "20px"
        },
        get value() {
          return a().text;
        },
        onSelected: (f) => {
          i(f);
        },
        get dataSource() {
          return u();
        }
      });
    }
  });
};
function G2(n) {
  return [
    {
      key: "candle.type",
      text: P("candle_type", n),
      component: "select",
      dataSource: [
        { key: "candle_solid", text: P("candle_solid", n) },
        { key: "candle_stroke", text: P("candle_stroke", n) },
        { key: "candle_up_stroke", text: P("candle_up_stroke", n) },
        { key: "candle_down_stroke", text: P("candle_down_stroke", n) },
        { key: "ohlc", text: P("ohlc", n) },
        { key: "area", text: P("area", n) }
      ]
    },
    {
      key: "candle.priceMark.last.show",
      text: P("last_price_show", n),
      component: "switch"
    },
    {
      key: "candle.priceMark.high.show",
      text: P("high_price_show", n),
      component: "switch"
    },
    {
      key: "candle.priceMark.low.show",
      text: P("low_price_show", n),
      component: "switch"
    },
    {
      key: "indicator.lastValueMark.show",
      text: P("indicator_last_value_show", n),
      component: "switch"
    },
    {
      key: "yAxis.type",
      text: P("price_axis_type", n),
      component: "select",
      dataSource: [
        { key: "normal", text: P("normal", n) },
        { key: "percentage", text: P("percentage", n) },
        { key: "log", text: P("log", n) }
      ]
    },
    {
      key: "yAxis.reverse",
      text: P("reverse_coordinate", n),
      component: "switch"
    },
    {
      key: "grid.show",
      text: P("grid_show", n),
      component: "switch"
    }
  ];
}
var rw = /* @__PURE__ */ I("<div class=klinecharts-pro-setting-modal-content>"), iw = /* @__PURE__ */ I("<span class=caption>");
const aw = (n) => {
  const [a, i] = V(n.currentStyles), [u, f] = V(G2(n.locale));
  Ie(() => {
    f(G2(n.locale));
  });
  const g = (d, p) => {
    const m = {};
    u9(m, d.key, p);
    const S = x1.clone(a());
    u9(S, d.key, p), i(S), f(u().map((x) => ({
      ...x
    }))), n.onChange(m);
  };
  return B(yn, {
    get title() {
      return P("setting", n.locale);
    },
    width: 800,
    get buttons() {
      return [{
        children: P("restore_default", n.locale),
        onClick: () => {
          n.onRestoreDefault(u()), n.onClose();
        }
      }];
    },
    get onClose() {
      return n.onClose;
    },
    get children() {
      var d = rw();
      return F(d, B(ac, {
        get each() {
          return u();
        },
        children: (p) => {
          let m;
          const S = x1.formatValue(a(), p.key);
          switch (p.component) {
            case "select": {
              m = B(E3, {
                class: "control",
                get value() {
                  return P(S, n.locale);
                },
                get dataSource() {
                  return p.dataSource;
                },
                onSelected: (x) => {
                  const M = x.key;
                  g(p, M);
                }
              });
              break;
            }
            case "switch": {
              const x = !!S;
              m = B(ry, {
                class: "control",
                open: x,
                onChange: () => {
                  g(p, !x);
                }
              });
              break;
            }
          }
          return [(() => {
            var x = iw();
            return F(x, () => p.text), x;
          })(), m];
        }
      })), d;
    }
  });
}, D3 = {
  AO: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 5 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 34 }
  ],
  BIAS: [
    {
      paramNameKey: "BIAS1",
      precision: 0,
      min: 1,
      styleKey: "lines[0].color"
    },
    {
      paramNameKey: "BIAS2",
      precision: 0,
      min: 1,
      styleKey: "lines[1].color"
    },
    {
      paramNameKey: "BIAS3",
      precision: 0,
      min: 1,
      styleKey: "lines[2].color"
    },
    {
      paramNameKey: "BIAS4",
      precision: 0,
      min: 1,
      styleKey: "lines[3].color"
    },
    {
      paramNameKey: "BIAS5",
      precision: 0,
      min: 1,
      styleKey: "lines[4].color"
    }
  ],
  BOLL: [
    { paramNameKey: "period", precision: 0, min: 1, default: 20 },
    { paramNameKey: "standard_deviation", precision: 2, min: 1, default: 2 }
  ],
  BRAR: [{ paramNameKey: "period", precision: 0, min: 1, default: 26 }],
  BBI: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 3 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 6 },
    { paramNameKey: "params_3", precision: 0, min: 1, default: 12 },
    { paramNameKey: "params_4", precision: 0, min: 1, default: 24 }
  ],
  CCI: [{ paramNameKey: "params_1", precision: 0, min: 1, default: 20 }],
  CR: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 26 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 10 },
    { paramNameKey: "params_3", precision: 0, min: 1, default: 20 },
    { paramNameKey: "params_4", precision: 0, min: 1, default: 40 },
    { paramNameKey: "params_5", precision: 0, min: 1, default: 60 }
  ],
  DMA: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 10 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 50 },
    { paramNameKey: "params_3", precision: 0, min: 1, default: 10 }
  ],
  DMI: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 14 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 6 }
  ],
  EMV: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 14 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 9 }
  ],
  EMA: [
    {
      paramNameKey: "EMA1",
      precision: 0,
      min: 1,
      styleKey: "lines[0].color"
    },
    {
      paramNameKey: "EMA2",
      precision: 0,
      min: 1,
      styleKey: "lines[1].color"
    },
    {
      paramNameKey: "EMA3",
      precision: 0,
      min: 1,
      styleKey: "lines[2].color"
    },
    {
      paramNameKey: "EMA4",
      precision: 0,
      min: 1,
      styleKey: "lines[3].color"
    },
    {
      paramNameKey: "EMA5",
      precision: 0,
      min: 1,
      styleKey: "lines[4].color"
    }
  ],
  MTM: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 12 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 6 }
  ],
  MA: [
    { paramNameKey: "MA1", precision: 0, min: 1, styleKey: "lines[0].color" },
    { paramNameKey: "MA2", precision: 0, min: 1, styleKey: "lines[1].color" },
    { paramNameKey: "MA3", precision: 0, min: 1, styleKey: "lines[2].color" },
    { paramNameKey: "MA4", precision: 0, min: 1, styleKey: "lines[3].color" },
    { paramNameKey: "MA5", precision: 0, min: 1, styleKey: "lines[4].color" }
  ],
  MACD: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 12 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 26 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 9 }
  ],
  OBV: [{ paramNameKey: "params_1", precision: 0, min: 1, default: 30 }],
  PVT: [],
  PSY: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 12 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 6 }
  ],
  ROC: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 12 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 6 }
  ],
  RSI: [
    {
      paramNameKey: "RSI1",
      precision: 0,
      min: 1,
      styleKey: "lines[0].color"
    },
    {
      paramNameKey: "RSI2",
      precision: 0,
      min: 1,
      styleKey: "lines[1].color"
    },
    {
      paramNameKey: "RSI3",
      precision: 0,
      min: 1,
      styleKey: "lines[2].color"
    },
    {
      paramNameKey: "RSI4",
      precision: 0,
      min: 1,
      styleKey: "lines[3].color"
    },
    {
      paramNameKey: "RSI5",
      precision: 0,
      min: 1,
      styleKey: "lines[4].color"
    }
  ],
  SMA: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 12 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 2 }
  ],
  KDJ: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 9 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 3 },
    { paramNameKey: "params_3", precision: 0, min: 1, default: 3 }
  ],
  SAR: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 2 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 2 },
    { paramNameKey: "params_3", precision: 0, min: 1, default: 20 }
  ],
  TRIX: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 12 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 9 }
  ],
  VOL: [
    { paramNameKey: "MA1", precision: 0, min: 1, styleKey: "lines[0].color" },
    { paramNameKey: "MA2", precision: 0, min: 1, styleKey: "lines[1].color" },
    { paramNameKey: "MA3", precision: 0, min: 1, styleKey: "lines[2].color" },
    { paramNameKey: "MA4", precision: 0, min: 1, styleKey: "lines[3].color" },
    { paramNameKey: "MA5", precision: 0, min: 1, styleKey: "lines[4].color" }
  ],
  VR: [
    { paramNameKey: "params_1", precision: 0, min: 1, default: 26 },
    { paramNameKey: "params_2", precision: 0, min: 1, default: 6 }
  ],
  WR: [
    { paramNameKey: "WR1", precision: 0, min: 1, styleKey: "lines[0].color" },
    { paramNameKey: "WR2", precision: 0, min: 1, styleKey: "lines[1].color" },
    { paramNameKey: "WR3", precision: 0, min: 1, styleKey: "lines[2].color" },
    { paramNameKey: "WR4", precision: 0, min: 1, styleKey: "lines[3].color" },
    { paramNameKey: "WR5", precision: 0, min: 1, styleKey: "lines[4].color" }
  ]
};
var sw = /* @__PURE__ */ I("<div class=klinecharts-pro-indicator-setting-modal-content>"), ow = /* @__PURE__ */ I("<span>");
const lw = (n) => {
  const [a, i] = V(x1.clone(n.params.calcParams)), u = (f) => D3[f];
  return B(yn, {
    get title() {
      return n.params.indicatorName;
    },
    width: 360,
    get buttons() {
      return [{
        type: "confirm",
        children: P("confirm", n.locale),
        onClick: () => {
          const f = u(n.params.indicatorName), g = [];
          x1.clone(a()).forEach((d, p) => {
            !x1.isValid(d) || d === "" ? "default" in f[p] && g.push(f[p].default) : g.push(d);
          }), n.onConfirm(g), n.onClose();
        }
      }];
    },
    get onClose() {
      return n.onClose;
    },
    get children() {
      var f = sw();
      return F(f, () => u(n.params.indicatorName).map((g, d) => [(() => {
        var p = ow();
        return F(p, () => P(g.paramNameKey, n.locale)), p;
      })(), B(P3, {
        style: {
          width: "200px"
        },
        get value() {
          return a()[d] ?? "";
        },
        get precision() {
          return g.precision;
        },
        get min() {
          return g.min;
        },
        onChange: (p) => {
          const m = x1.clone(a());
          m[d] = p, i(m);
        }
      })])), f;
    }
  });
};
var cw = /* @__PURE__ */ I('<svg viewBox="0 0 1024 1024"><path d="M945.066667 898.133333l-189.866667-189.866666c55.466667-64 87.466667-149.333333 87.466667-241.066667 0-204.8-168.533333-373.333333-373.333334-373.333333S96 264.533333 96 469.333333 264.533333 842.666667 469.333333 842.666667c91.733333 0 174.933333-34.133333 241.066667-87.466667l189.866667 189.866667c6.4 6.4 14.933333 8.533333 23.466666 8.533333s17.066667-2.133333 23.466667-8.533333c8.533333-12.8 8.533333-34.133333-2.133333-46.933334zM469.333333 778.666667C298.666667 778.666667 160 640 160 469.333333S298.666667 160 469.333333 160 778.666667 298.666667 778.666667 469.333333 640 778.666667 469.333333 778.666667z">'), uw = /* @__PURE__ */ I("<img alt=symbol>"), fw = /* @__PURE__ */ I("<li><div><span>");
const hw = (n) => {
  const [a, i] = V(""), [u] = Yl(a, n.datafeed.searchSymbols.bind(n.datafeed));
  return B(yn, {
    get title() {
      return P("symbol_search", n.locale);
    },
    width: 460,
    get onClose() {
      return n.onClose;
    },
    get children() {
      return [B(P3, {
        class: "klinecharts-pro-symbol-search-modal-input",
        get placeholder() {
          return P("symbol_code", n.locale);
        },
        get suffix() {
          return cw();
        },
        get value() {
          return a();
        },
        onChange: (f) => {
          const g = `${f}`;
          i(g);
        }
      }), B($0, {
        class: "klinecharts-pro-symbol-search-modal-list",
        get loading() {
          return u.loading;
        },
        get dataSource() {
          return u() ?? [];
        },
        renderItem: (f) => (() => {
          var g = fw(), d = g.firstChild, p = d.firstChild;
          return g.$$click = () => {
            n.onSymbolSelected(f), n.onClose();
          }, F(d, B(Z1, {
            get when() {
              return f.logo;
            },
            get children() {
              var m = uw();
              return P1(() => ve(m, "src", f.logo)), m;
            }
          }), p), F(p, () => f.shortName ?? f.ticker, null), F(p, () => `${f.name ? `(${f.name})` : ""}`, null), F(g, () => f.exchange ?? "", null), P1(() => ve(p, "title", f.name ?? "")), g;
        })()
      })];
    }
  });
};
ke(["click"]);
var gw = /* @__PURE__ */ I('<i class="icon-close klinecharts-pro-load-icon">'), pw = /* @__PURE__ */ I("<div class=klinecharts-pro-content><div class=klinecharts-pro-widget>");
function h0(n, a, i, u) {
  return a === "VOL" && (u = {
    gap: {
      bottom: 2
    },
    ...u
  }), (n == null ? void 0 : n.createIndicator({
    name: a,
    // @ts-expect-error
    createTooltipDataSource: ({
      indicator: f,
      defaultStyles: g
    }) => {
      const d = [], p = Object.keys(D3[`${f.name}`]).length > 0;
      return f.visible ? (d.push(g.tooltip.icons[1]), p && d.push(g.tooltip.icons[2]), d.push(g.tooltip.icons[3])) : (d.push(g.tooltip.icons[0]), p && d.push(g.tooltip.icons[2]), d.push(g.tooltip.icons[3])), {
        icons: d
      };
    }
  }, i, u)) ?? null;
}
const _w = (n) => {
  let a, i = null, u, f = !1;
  const [g, d] = V(n.theme), [p, m] = V(n.styles), [S, x] = V(n.locale), [M, D] = V(n.symbol), [z, t1] = V(n.period), [p1, n1] = V(!1), [i1, G] = V([...n.mainIndicators]), [U, q] = V({}), [$1, R1] = V(!1), [M1, s1] = V({
    key: n.timezone,
    text: H2(n.timezone, n.locale)
  }), [l1, h1] = V(!1), [j1, Gt] = V(), [Yt, rt] = V(""), [Pe, yt] = V(n.drawingBarVisible), [oe, J1] = V(!1), [mt, a1] = V(!1), [u1, ee] = V({
    visible: !1,
    indicatorName: "",
    paneId: "",
    calcParams: []
  });
  n.ref({
    setTheme: d,
    getTheme: () => g(),
    setStyles: m,
    getStyles: () => i.getStyles(),
    setLocale: x,
    getLocale: () => S(),
    setTimezone: (T) => {
      s1({
        key: T,
        text: H2(n.timezone, S())
      });
    },
    getTimezone: () => M1().key,
    setSymbol: D,
    getSymbol: () => M(),
    setPeriod: t1,
    getPeriod: () => z(),
    getInstance: () => i
  });
  const we = () => {
    i == null || i.resize();
  }, it = (T, A, E) => {
    let N = A, m1 = N;
    switch (T.timespan) {
      case "minute": {
        N = N - N % (60 * 1e3), m1 = N - E * T.multiplier * 60 * 1e3;
        break;
      }
      case "hour": {
        N = N - N % (60 * 60 * 1e3), m1 = N - E * T.multiplier * 60 * 60 * 1e3;
        break;
      }
      case "day": {
        N = N - N % (60 * 60 * 1e3), m1 = N - E * T.multiplier * 24 * 60 * 60 * 1e3;
        break;
      }
      case "week": {
        const G1 = new Date(N).getDay(), Ae = G1 === 0 ? 6 : G1 - 1;
        N = N - Ae * 60 * 60 * 24;
        const O1 = new Date(N);
        N = (/* @__PURE__ */ new Date(`${O1.getFullYear()}-${O1.getMonth() + 1}-${O1.getDate()}`)).getTime(), m1 = E * T.multiplier * 7 * 24 * 60 * 60 * 1e3;
        break;
      }
      case "month": {
        const B1 = new Date(N), G1 = B1.getFullYear(), Ae = B1.getMonth() + 1;
        N = (/* @__PURE__ */ new Date(`${G1}-${Ae}-01`)).getTime(), m1 = E * T.multiplier * 30 * 24 * 60 * 60 * 1e3;
        const O1 = new Date(m1);
        m1 = (/* @__PURE__ */ new Date(`${O1.getFullYear()}-${O1.getMonth() + 1}-01`)).getTime();
        break;
      }
      case "year": {
        const G1 = new Date(N).getFullYear();
        N = (/* @__PURE__ */ new Date(`${G1}-01-01`)).getTime(), m1 = E * T.multiplier * 365 * 24 * 60 * 60 * 1e3;
        const Ae = new Date(m1);
        m1 = (/* @__PURE__ */ new Date(`${Ae.getFullYear()}-01-01`)).getTime();
        break;
      }
    }
    return [m1, N];
  }, Ce = (T) => {
    i == null || i.createOverlay({
      ...T,
      onDrawEnd: ({
        overlay: A
      }) => {
        var E;
        return (E = n.onOverlayChange) == null || E.call(n, A), !0;
      },
      onPressedMoveEnd: ({
        overlay: A
      }) => {
        var E;
        return (E = n.onOverlayChange) == null || E.call(n, A), !0;
      },
      onRemoved: ({
        overlay: A
      }) => {
        var E;
        return (E = n.onOverlayRemove) == null || E.call(n, A), !0;
      }
    });
  };
  return q2(() => {
    if (window.addEventListener("resize", we), i = xl(a, {
      customApi: {
        formatDate: (A, E, N, m1) => {
          switch (z().timespan) {
            case "minute":
              return m1 === c0.XAxis ? x1.formatDate(A, E, "HH:mm") : x1.formatDate(A, E, "YYYY-MM-DD HH:mm");
            case "hour":
              return m1 === c0.XAxis ? x1.formatDate(A, E, "MM-DD HH:mm") : x1.formatDate(A, E, "YYYY-MM-DD HH:mm");
            case "day":
            case "week":
              return x1.formatDate(A, E, "YYYY-MM-DD");
            case "month":
              return m1 === c0.XAxis ? x1.formatDate(A, E, "YYYY-MM") : x1.formatDate(A, E, "YYYY-MM-DD");
            case "year":
              return m1 === c0.XAxis ? x1.formatDate(A, E, "YYYY") : x1.formatDate(A, E, "YYYY-MM-DD");
          }
          return x1.formatDate(A, E, "YYYY-MM-DD HH:mm");
        }
      }
    }), i) {
      const A = i.getDom("candle_pane", o2.Main);
      if (A) {
        let N = document.createElement("div");
        if (N.className = "klinecharts-pro-watermark", x1.isString(n.watermark)) {
          const m1 = n.watermark.replace(/(^\s*)|(\s*$)/g, "");
          N.innerHTML = m1;
        } else
          N.appendChild(n.watermark);
        A.appendChild(N);
      }
      const E = i.getDom("candle_pane", o2.YAxis);
      u = document.createElement("span"), u.className = "klinecharts-pro-price-unit", E == null || E.appendChild(u);
    }
    i1().forEach((A) => {
      h0(i, A, !0, {
        id: "candle_pane"
      });
    });
    const T = {};
    n.subIndicators.forEach((A) => {
      const E = h0(i, A, !0);
      E && (T[A] = E);
    }), q(T), i == null || i.loadMore((A) => {
      f = !0;
      const E = z(), [N] = it(E, A, 1), [m1] = it(E, N, 100);
      n.datafeed.getHistoryKLineData(M(), E, m1, N).then((B1) => {
        i == null || i.applyMoreData(B1, (B1 == null ? void 0 : B1.length) > 0), f = !1;
      });
    }), i == null || i.subscribeAction($l.OnTooltipIconClick, (A) => {
      if (A.indicatorName)
        switch (A.iconId) {
          case "visible": {
            i == null || i.overrideIndicator({
              name: A.indicatorName,
              visible: !0
            }, A.paneId);
            break;
          }
          case "invisible": {
            i == null || i.overrideIndicator({
              name: A.indicatorName,
              visible: !1
            }, A.paneId);
            break;
          }
          case "setting": {
            const E = i == null ? void 0 : i.getIndicatorByPaneId(A.paneId, A.indicatorName);
            ee({
              visible: !0,
              indicatorName: A.indicatorName,
              paneId: A.paneId,
              calcParams: E.calcParams
            });
            break;
          }
          case "close":
            if (A.paneId === "candle_pane") {
              const E = [...i1()];
              i == null || i.removeIndicator("candle_pane", A.indicatorName), E.splice(E.indexOf(A.indicatorName), 1), G(E);
            } else {
              const E = {
                ...U()
              };
              i == null || i.removeIndicator(A.paneId, A.indicatorName), delete E[A.indicatorName], q(E);
            }
        }
    }), n.overlays.forEach((A) => {
      Ce(A);
    });
  }), v9(() => {
    window.removeEventListener("resize", we), bl(a);
  }), Ie(() => {
    const T = M();
    T != null && T.priceCurrency ? (u.innerHTML = T == null ? void 0 : T.priceCurrency.toLocaleUpperCase(), u.style.display = "flex") : u.style.display = "none", i == null || i.setPriceVolumePrecision((T == null ? void 0 : T.pricePrecision) ?? 2, (T == null ? void 0 : T.volumePrecision) ?? 0);
  }), Ie((T) => {
    if (f)
      return T;
    T && n.datafeed.unsubscribe(T.symbol, T.period);
    const A = M(), E = z();
    return f = !0, a1(!0), (async () => {
      const [m1, B1] = it(E, (/* @__PURE__ */ new Date()).getTime(), 250), G1 = await n.datafeed.getHistoryKLineData(A, E, m1, B1);
      i == null || i.applyNewData(G1, G1.length > 0), n.datafeed.subscribe(A, E, (Ae) => {
        i == null || i.updateData(Ae);
      }), f = !1, a1(!1);
    })(), {
      symbol: A,
      period: E
    };
  }), Ie(() => {
    const T = g();
    i == null || i.setStyles(T);
    const A = T === "dark" ? "#929AA5" : "#76808F";
    i == null || i.setStyles({
      indicator: {
        tooltip: {
          icons: [{
            id: "visible",
            position: u0.Middle,
            marginLeft: 8,
            marginTop: 7,
            marginRight: 0,
            marginBottom: 0,
            paddingLeft: 0,
            paddingTop: 0,
            paddingRight: 0,
            paddingBottom: 0,
            icon: "",
            fontFamily: "icomoon",
            size: 14,
            color: A,
            activeColor: A,
            backgroundColor: "transparent",
            activeBackgroundColor: "rgba(22, 119, 255, 0.15)"
          }, {
            id: "invisible",
            position: u0.Middle,
            marginLeft: 8,
            marginTop: 7,
            marginRight: 0,
            marginBottom: 0,
            paddingLeft: 0,
            paddingTop: 0,
            paddingRight: 0,
            paddingBottom: 0,
            icon: "",
            fontFamily: "icomoon",
            size: 14,
            color: A,
            activeColor: A,
            backgroundColor: "transparent",
            activeBackgroundColor: "rgba(22, 119, 255, 0.15)"
          }, {
            id: "setting",
            position: u0.Middle,
            marginLeft: 6,
            marginTop: 7,
            marginBottom: 0,
            marginRight: 0,
            paddingLeft: 0,
            paddingTop: 0,
            paddingRight: 0,
            paddingBottom: 0,
            icon: "",
            fontFamily: "icomoon",
            size: 14,
            color: A,
            activeColor: A,
            backgroundColor: "transparent",
            activeBackgroundColor: "rgba(22, 119, 255, 0.15)"
          }, {
            id: "close",
            position: u0.Middle,
            marginLeft: 6,
            marginTop: 7,
            marginRight: 0,
            marginBottom: 0,
            paddingLeft: 0,
            paddingTop: 0,
            paddingRight: 0,
            paddingBottom: 0,
            icon: "",
            fontFamily: "icomoon",
            size: 14,
            color: A,
            activeColor: A,
            backgroundColor: "transparent",
            activeBackgroundColor: "rgba(22, 119, 255, 0.15)"
          }]
        }
      }
    });
  }), Ie(() => {
    i == null || i.setLocale(S());
  }), Ie(() => {
    i == null || i.setTimezone(M1().key);
  }), Ie(() => {
    p() && (i == null || i.setStyles(p()), Gt(OC(i.getStyles())));
  }), Ie(() => {
    i == null || i.setLocale(S());
  }), [gw(), B(Z1, {
    get when() {
      return oe();
    },
    get children() {
      return B(hw, {
        get locale() {
          return n.locale;
        },
        get datafeed() {
          return n.datafeed;
        },
        onSymbolSelected: (T) => {
          D(T);
        },
        onClose: () => {
          J1(!1);
        }
      });
    }
  }), B(Z1, {
    get when() {
      return p1();
    },
    get children() {
      return B(ew, {
        get locale() {
          return n.locale;
        },
        get mainIndicators() {
          return i1();
        },
        get subIndicators() {
          return U();
        },
        onClose: () => {
          n1(!1);
        },
        onMainIndicatorChange: (T) => {
          var E;
          const A = [...i1()];
          T.added ? (h0(i, T.name, !0, {
            id: "candle_pane"
          }), A.push(T.name)) : (i == null || i.removeIndicator("candle_pane", T.name), A.splice(A.indexOf(T.name), 1)), G(A), (E = n.onMainIndicatorsChange) == null || E.call(n, A);
        },
        onSubIndicatorChange: (T) => {
          var E;
          const A = {
            ...U()
          };
          if (T.added) {
            const N = h0(i, T.name);
            N && (A[T.name] = N);
          } else
            T.paneId && (i == null || i.removeIndicator(T.paneId, T.name), delete A[T.name]);
          q(A), (E = n.onSubIndicatorsChange) == null || E.call(n, A);
        }
      });
    }
  }), B(Z1, {
    get when() {
      return $1();
    },
    get children() {
      return B(nw, {
        get locale() {
          return n.locale;
        },
        get timezone() {
          return M1();
        },
        onClose: () => {
          R1(!1);
        },
        onConfirm: (T) => {
          var A;
          (A = n.onTimezoneChange) == null || A.call(n, T.key), s1(T);
        }
      });
    }
  }), B(Z1, {
    get when() {
      return l1();
    },
    get children() {
      return B(aw, {
        get locale() {
          return n.locale;
        },
        get currentStyles() {
          return x1.clone(i.getStyles());
        },
        onClose: () => {
          h1(!1);
        },
        onChange: (T) => {
          var A;
          (A = n.onSettingsChange) == null || A.call(n, T), i == null || i.setStyles(T);
        },
        onRestoreDefault: (T) => {
          const A = {};
          T.forEach((E) => {
            const N = E.key;
            u9(A, N, x1.formatValue(j1(), N));
          }), i == null || i.setStyles(A);
        }
      });
    }
  }), B(Z1, {
    get when() {
      return u1().visible;
    },
    get children() {
      return B(lw, {
        get locale() {
          return n.locale;
        },
        get params() {
          return u1();
        },
        onClose: () => {
          ee({
            visible: !1,
            indicatorName: "",
            paneId: "",
            calcParams: []
          });
        },
        onConfirm: (T) => {
          const A = u1();
          i == null || i.overrideIndicator({
            name: A.indicatorName,
            calcParams: T
          }, A.paneId);
        }
      });
    }
  }), B($$, {
    get locale() {
      return n.locale;
    },
    get symbol() {
      return M();
    },
    get spread() {
      return Pe();
    },
    get period() {
      return z();
    },
    get periods() {
      return n.periods;
    },
    onMenuClick: async () => {
      try {
        await Vl(() => yt(!Pe())), i == null || i.resize();
      } catch {
      }
    },
    onSymbolClick: () => {
      J1(!oe());
    },
    onPeriodChange: (T) => {
      var A;
      f || (t1(T), (A = n.onPeriodChange) == null || A.call(n, T));
    },
    onIndicatorClick: () => {
      n1((T) => !T);
    },
    onTimezoneClick: () => {
      R1((T) => !T);
    },
    onSettingClick: () => {
      h1((T) => !T);
    },
    onScreenshotClick: () => {
      if (i) {
        const T = i.getConvertPictureUrl(!0, "jpeg", n.theme === "dark" ? "#151517" : "#ffffff");
        rt(T);
      }
    }
  }), (() => {
    var T = pw(), A = T.firstChild;
    F(T, B(Z1, {
      get when() {
        return mt();
      },
      get children() {
        return B(k3, {});
      }
    }), A), F(T, B(Z1, {
      get when() {
        return Pe();
      },
      get children() {
        return B(Jb, {
          get locale() {
            return n.locale;
          },
          onDrawingItemClick: Ce,
          onModeChange: (N) => {
            i == null || i.overrideOverlay({
              mode: N
            });
          },
          onLockChange: (N) => {
            i == null || i.overrideOverlay({
              lock: N
            });
          },
          onVisibleChange: (N) => {
            i == null || i.overrideOverlay({
              visible: N
            });
          },
          onRemoveClick: (N) => {
            i == null || i.removeOverlay({
              groupId: N
            });
          }
        });
      }
    }), A);
    var E = a;
    return typeof E == "function" ? C9(E, A) : a = A, P1(() => ve(A, "data-drawing-bar-visible", Pe())), T;
  })()];
};
var b0 = { exports: {} };
/**
 * @license
 * Lodash <https://lodash.com/>
 * Copyright OpenJS Foundation and other contributors <https://openjsf.org/>
 * Released under MIT license <https://lodash.com/license>
 * Based on Underscore.js 1.8.3 <http://underscorejs.org/LICENSE>
 * Copyright Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
 */
b0.exports;
(function(n, a) {
  (function() {
    var i, u = "4.17.21", f = 200, g = "Unsupported core-js use. Try https://npms.io/search?q=ponyfill.", d = "Expected a function", p = "Invalid `variable` option passed into `_.template`", m = "__lodash_hash_undefined__", S = 500, x = "__lodash_placeholder__", M = 1, D = 2, z = 4, t1 = 1, p1 = 2, n1 = 1, i1 = 2, G = 4, U = 8, q = 16, $1 = 32, R1 = 64, M1 = 128, s1 = 256, l1 = 512, h1 = 30, j1 = "...", Gt = 800, Yt = 16, rt = 1, Pe = 2, yt = 3, oe = 1 / 0, J1 = 9007199254740991, mt = 17976931348623157e292, a1 = 0 / 0, u1 = 4294967295, ee = u1 - 1, we = u1 >>> 1, it = [
      ["ary", M1],
      ["bind", n1],
      ["bindKey", i1],
      ["curry", U],
      ["curryRight", q],
      ["flip", l1],
      ["partial", $1],
      ["partialRight", R1],
      ["rearg", s1]
    ], Ce = "[object Arguments]", T = "[object Array]", A = "[object AsyncFunction]", E = "[object Boolean]", N = "[object Date]", m1 = "[object DOMException]", B1 = "[object Error]", G1 = "[object Function]", Ae = "[object GeneratorFunction]", O1 = "[object Map]", Vt = "[object Number]", R3 = "[object Null]", Oe = "[object Object]", k9 = "[object Promise]", B3 = "[object Proxy]", Xt = "[object RegExp]", ye = "[object Set]", qt = "[object String]", mn = "[object Symbol]", F3 = "[object Undefined]", jt = "[object WeakMap]", N3 = "[object WeakSet]", Jt = "[object ArrayBuffer]", Lt = "[object DataView]", O0 = "[object Float32Array]", D0 = "[object Float64Array]", R0 = "[object Int8Array]", B0 = "[object Int16Array]", F0 = "[object Int32Array]", N0 = "[object Uint8Array]", K0 = "[object Uint8ClampedArray]", U0 = "[object Uint16Array]", Z0 = "[object Uint32Array]", K3 = /\b__p \+= '';/g, U3 = /\b(__p \+=) '' \+/g, Z3 = /(__e\(.*?\)|\b__t\)) \+\n'';/g, E9 = /&(?:amp|lt|gt|quot|#39);/g, P9 = /[&<>"']/g, W3 = RegExp(E9.source), z3 = RegExp(P9.source), Q3 = /<%-([\s\S]+?)%>/g, H3 = /<%([\s\S]+?)%>/g, O9 = /<%=([\s\S]+?)%>/g, G3 = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, Y3 = /^\w*$/, V3 = /[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g, W0 = /[\\^$.*+?()[\]{}|]/g, X3 = RegExp(W0.source), z0 = /^\s+/, q3 = /\s/, j3 = /\{(?:\n\/\* \[wrapped with .+\] \*\/)?\n?/, J3 = /\{\n\/\* \[wrapped with (.+)\] \*/, e8 = /,? & /, t8 = /[^\x00-\x2f\x3a-\x40\x5b-\x60\x7b-\x7f]+/g, n8 = /[()=,{}\[\]\/\s]/, r8 = /\\(\\)?/g, i8 = /\$\{([^\\}]*(?:\\.[^\\}]*)*)\}/g, D9 = /\w*$/, a8 = /^[-+]0x[0-9a-f]+$/i, s8 = /^0b[01]+$/i, o8 = /^\[object .+?Constructor\]$/, l8 = /^0o[0-7]+$/i, c8 = /^(?:0|[1-9]\d*)$/, u8 = /[\xc0-\xd6\xd8-\xf6\xf8-\xff\u0100-\u017f]/g, Ln = /($^)/, f8 = /['\n\r\u2028\u2029\\]/g, xn = "\\ud800-\\udfff", h8 = "\\u0300-\\u036f", g8 = "\\ufe20-\\ufe2f", p8 = "\\u20d0-\\u20ff", R9 = h8 + g8 + p8, B9 = "\\u2700-\\u27bf", F9 = "a-z\\xdf-\\xf6\\xf8-\\xff", _8 = "\\xac\\xb1\\xd7\\xf7", d8 = "\\x00-\\x2f\\x3a-\\x40\\x5b-\\x60\\x7b-\\xbf", v8 = "\\u2000-\\u206f", C8 = " \\t\\x0b\\f\\xa0\\ufeff\\n\\r\\u2028\\u2029\\u1680\\u180e\\u2000\\u2001\\u2002\\u2003\\u2004\\u2005\\u2006\\u2007\\u2008\\u2009\\u200a\\u202f\\u205f\\u3000", N9 = "A-Z\\xc0-\\xd6\\xd8-\\xde", K9 = "\\ufe0e\\ufe0f", U9 = _8 + d8 + v8 + C8, Q0 = "['’]", y8 = "[" + xn + "]", Z9 = "[" + U9 + "]", $n = "[" + R9 + "]", W9 = "\\d+", m8 = "[" + B9 + "]", z9 = "[" + F9 + "]", Q9 = "[^" + xn + U9 + W9 + B9 + F9 + N9 + "]", H0 = "\\ud83c[\\udffb-\\udfff]", L8 = "(?:" + $n + "|" + H0 + ")", H9 = "[^" + xn + "]", G0 = "(?:\\ud83c[\\udde6-\\uddff]){2}", Y0 = "[\\ud800-\\udbff][\\udc00-\\udfff]", xt = "[" + N9 + "]", G9 = "\\u200d", Y9 = "(?:" + z9 + "|" + Q9 + ")", x8 = "(?:" + xt + "|" + Q9 + ")", V9 = "(?:" + Q0 + "(?:d|ll|m|re|s|t|ve))?", X9 = "(?:" + Q0 + "(?:D|LL|M|RE|S|T|VE))?", q9 = L8 + "?", j9 = "[" + K9 + "]?", $8 = "(?:" + G9 + "(?:" + [H9, G0, Y0].join("|") + ")" + j9 + q9 + ")*", b8 = "\\d*(?:1st|2nd|3rd|(?![123])\\dth)(?=\\b|[A-Z_])", w8 = "\\d*(?:1ST|2ND|3RD|(?![123])\\dTH)(?=\\b|[a-z_])", J9 = j9 + q9 + $8, A8 = "(?:" + [m8, G0, Y0].join("|") + ")" + J9, S8 = "(?:" + [H9 + $n + "?", $n, G0, Y0, y8].join("|") + ")", M8 = RegExp(Q0, "g"), T8 = RegExp($n, "g"), V0 = RegExp(H0 + "(?=" + H0 + ")|" + S8 + J9, "g"), I8 = RegExp([
      xt + "?" + z9 + "+" + V9 + "(?=" + [Z9, xt, "$"].join("|") + ")",
      x8 + "+" + X9 + "(?=" + [Z9, xt + Y9, "$"].join("|") + ")",
      xt + "?" + Y9 + "+" + V9,
      xt + "+" + X9,
      w8,
      b8,
      W9,
      A8
    ].join("|"), "g"), k8 = RegExp("[" + G9 + xn + R9 + K9 + "]"), E8 = /[a-z][A-Z]|[A-Z]{2}[a-z]|[0-9][a-zA-Z]|[a-zA-Z][0-9]|[^a-zA-Z0-9 ]/, P8 = [
      "Array",
      "Buffer",
      "DataView",
      "Date",
      "Error",
      "Float32Array",
      "Float64Array",
      "Function",
      "Int8Array",
      "Int16Array",
      "Int32Array",
      "Map",
      "Math",
      "Object",
      "Promise",
      "RegExp",
      "Set",
      "String",
      "Symbol",
      "TypeError",
      "Uint8Array",
      "Uint8ClampedArray",
      "Uint16Array",
      "Uint32Array",
      "WeakMap",
      "_",
      "clearTimeout",
      "isFinite",
      "parseInt",
      "setTimeout"
    ], O8 = -1, v1 = {};
    v1[O0] = v1[D0] = v1[R0] = v1[B0] = v1[F0] = v1[N0] = v1[K0] = v1[U0] = v1[Z0] = !0, v1[Ce] = v1[T] = v1[Jt] = v1[E] = v1[Lt] = v1[N] = v1[B1] = v1[G1] = v1[O1] = v1[Vt] = v1[Oe] = v1[Xt] = v1[ye] = v1[qt] = v1[jt] = !1;
    var _1 = {};
    _1[Ce] = _1[T] = _1[Jt] = _1[Lt] = _1[E] = _1[N] = _1[O0] = _1[D0] = _1[R0] = _1[B0] = _1[F0] = _1[O1] = _1[Vt] = _1[Oe] = _1[Xt] = _1[ye] = _1[qt] = _1[mn] = _1[N0] = _1[K0] = _1[U0] = _1[Z0] = !0, _1[B1] = _1[G1] = _1[jt] = !1;
    var D8 = {
      // Latin-1 Supplement block.
      À: "A",
      Á: "A",
      Â: "A",
      Ã: "A",
      Ä: "A",
      Å: "A",
      à: "a",
      á: "a",
      â: "a",
      ã: "a",
      ä: "a",
      å: "a",
      Ç: "C",
      ç: "c",
      Ð: "D",
      ð: "d",
      È: "E",
      É: "E",
      Ê: "E",
      Ë: "E",
      è: "e",
      é: "e",
      ê: "e",
      ë: "e",
      Ì: "I",
      Í: "I",
      Î: "I",
      Ï: "I",
      ì: "i",
      í: "i",
      î: "i",
      ï: "i",
      Ñ: "N",
      ñ: "n",
      Ò: "O",
      Ó: "O",
      Ô: "O",
      Õ: "O",
      Ö: "O",
      Ø: "O",
      ò: "o",
      ó: "o",
      ô: "o",
      õ: "o",
      ö: "o",
      ø: "o",
      Ù: "U",
      Ú: "U",
      Û: "U",
      Ü: "U",
      ù: "u",
      ú: "u",
      û: "u",
      ü: "u",
      Ý: "Y",
      ý: "y",
      ÿ: "y",
      Æ: "Ae",
      æ: "ae",
      Þ: "Th",
      þ: "th",
      ß: "ss",
      // Latin Extended-A block.
      Ā: "A",
      Ă: "A",
      Ą: "A",
      ā: "a",
      ă: "a",
      ą: "a",
      Ć: "C",
      Ĉ: "C",
      Ċ: "C",
      Č: "C",
      ć: "c",
      ĉ: "c",
      ċ: "c",
      č: "c",
      Ď: "D",
      Đ: "D",
      ď: "d",
      đ: "d",
      Ē: "E",
      Ĕ: "E",
      Ė: "E",
      Ę: "E",
      Ě: "E",
      ē: "e",
      ĕ: "e",
      ė: "e",
      ę: "e",
      ě: "e",
      Ĝ: "G",
      Ğ: "G",
      Ġ: "G",
      Ģ: "G",
      ĝ: "g",
      ğ: "g",
      ġ: "g",
      ģ: "g",
      Ĥ: "H",
      Ħ: "H",
      ĥ: "h",
      ħ: "h",
      Ĩ: "I",
      Ī: "I",
      Ĭ: "I",
      Į: "I",
      İ: "I",
      ĩ: "i",
      ī: "i",
      ĭ: "i",
      į: "i",
      ı: "i",
      Ĵ: "J",
      ĵ: "j",
      Ķ: "K",
      ķ: "k",
      ĸ: "k",
      Ĺ: "L",
      Ļ: "L",
      Ľ: "L",
      Ŀ: "L",
      Ł: "L",
      ĺ: "l",
      ļ: "l",
      ľ: "l",
      ŀ: "l",
      ł: "l",
      Ń: "N",
      Ņ: "N",
      Ň: "N",
      Ŋ: "N",
      ń: "n",
      ņ: "n",
      ň: "n",
      ŋ: "n",
      Ō: "O",
      Ŏ: "O",
      Ő: "O",
      ō: "o",
      ŏ: "o",
      ő: "o",
      Ŕ: "R",
      Ŗ: "R",
      Ř: "R",
      ŕ: "r",
      ŗ: "r",
      ř: "r",
      Ś: "S",
      Ŝ: "S",
      Ş: "S",
      Š: "S",
      ś: "s",
      ŝ: "s",
      ş: "s",
      š: "s",
      Ţ: "T",
      Ť: "T",
      Ŧ: "T",
      ţ: "t",
      ť: "t",
      ŧ: "t",
      Ũ: "U",
      Ū: "U",
      Ŭ: "U",
      Ů: "U",
      Ű: "U",
      Ų: "U",
      ũ: "u",
      ū: "u",
      ŭ: "u",
      ů: "u",
      ű: "u",
      ų: "u",
      Ŵ: "W",
      ŵ: "w",
      Ŷ: "Y",
      ŷ: "y",
      Ÿ: "Y",
      Ź: "Z",
      Ż: "Z",
      Ž: "Z",
      ź: "z",
      ż: "z",
      ž: "z",
      Ĳ: "IJ",
      ĳ: "ij",
      Œ: "Oe",
      œ: "oe",
      ŉ: "'n",
      ſ: "s"
    }, R8 = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }, B8 = {
      "&amp;": "&",
      "&lt;": "<",
      "&gt;": ">",
      "&quot;": '"',
      "&#39;": "'"
    }, F8 = {
      "\\": "\\",
      "'": "'",
      "\n": "n",
      "\r": "r",
      "\u2028": "u2028",
      "\u2029": "u2029"
    }, N8 = parseFloat, K8 = parseInt, e5 = typeof ze == "object" && ze && ze.Object === Object && ze, U8 = typeof self == "object" && self && self.Object === Object && self, F1 = e5 || U8 || Function("return this")(), X0 = a && !a.nodeType && a, at = X0 && !0 && n && !n.nodeType && n, t5 = at && at.exports === X0, q0 = t5 && e5.process, le = function() {
      try {
        var v = at && at.require && at.require("util").types;
        return v || q0 && q0.binding && q0.binding("util");
      } catch {
      }
    }(), n5 = le && le.isArrayBuffer, r5 = le && le.isDate, i5 = le && le.isMap, a5 = le && le.isRegExp, s5 = le && le.isSet, o5 = le && le.isTypedArray;
    function te(v, L, y) {
      switch (y.length) {
        case 0:
          return v.call(L);
        case 1:
          return v.call(L, y[0]);
        case 2:
          return v.call(L, y[0], y[1]);
        case 3:
          return v.call(L, y[0], y[1], y[2]);
      }
      return v.apply(L, y);
    }
    function Z8(v, L, y, O) {
      for (var Q = -1, o1 = v == null ? 0 : v.length; ++Q < o1; ) {
        var k1 = v[Q];
        L(O, k1, y(k1), v);
      }
      return O;
    }
    function ce(v, L) {
      for (var y = -1, O = v == null ? 0 : v.length; ++y < O && L(v[y], y, v) !== !1; )
        ;
      return v;
    }
    function W8(v, L) {
      for (var y = v == null ? 0 : v.length; y-- && L(v[y], y, v) !== !1; )
        ;
      return v;
    }
    function l5(v, L) {
      for (var y = -1, O = v == null ? 0 : v.length; ++y < O; )
        if (!L(v[y], y, v))
          return !1;
      return !0;
    }
    function Ge(v, L) {
      for (var y = -1, O = v == null ? 0 : v.length, Q = 0, o1 = []; ++y < O; ) {
        var k1 = v[y];
        L(k1, y, v) && (o1[Q++] = k1);
      }
      return o1;
    }
    function bn(v, L) {
      var y = v == null ? 0 : v.length;
      return !!y && $t(v, L, 0) > -1;
    }
    function j0(v, L, y) {
      for (var O = -1, Q = v == null ? 0 : v.length; ++O < Q; )
        if (y(L, v[O]))
          return !0;
      return !1;
    }
    function L1(v, L) {
      for (var y = -1, O = v == null ? 0 : v.length, Q = Array(O); ++y < O; )
        Q[y] = L(v[y], y, v);
      return Q;
    }
    function Ye(v, L) {
      for (var y = -1, O = L.length, Q = v.length; ++y < O; )
        v[Q + y] = L[y];
      return v;
    }
    function J0(v, L, y, O) {
      var Q = -1, o1 = v == null ? 0 : v.length;
      for (O && o1 && (y = v[++Q]); ++Q < o1; )
        y = L(y, v[Q], Q, v);
      return y;
    }
    function z8(v, L, y, O) {
      var Q = v == null ? 0 : v.length;
      for (O && Q && (y = v[--Q]); Q--; )
        y = L(y, v[Q], Q, v);
      return y;
    }
    function er(v, L) {
      for (var y = -1, O = v == null ? 0 : v.length; ++y < O; )
        if (L(v[y], y, v))
          return !0;
      return !1;
    }
    var Q8 = tr("length");
    function H8(v) {
      return v.split("");
    }
    function G8(v) {
      return v.match(t8) || [];
    }
    function c5(v, L, y) {
      var O;
      return y(v, function(Q, o1, k1) {
        if (L(Q, o1, k1))
          return O = o1, !1;
      }), O;
    }
    function wn(v, L, y, O) {
      for (var Q = v.length, o1 = y + (O ? 1 : -1); O ? o1-- : ++o1 < Q; )
        if (L(v[o1], o1, v))
          return o1;
      return -1;
    }
    function $t(v, L, y) {
      return L === L ? ai(v, L, y) : wn(v, u5, y);
    }
    function Y8(v, L, y, O) {
      for (var Q = y - 1, o1 = v.length; ++Q < o1; )
        if (O(v[Q], L))
          return Q;
      return -1;
    }
    function u5(v) {
      return v !== v;
    }
    function f5(v, L) {
      var y = v == null ? 0 : v.length;
      return y ? rr(v, L) / y : a1;
    }
    function tr(v) {
      return function(L) {
        return L == null ? i : L[v];
      };
    }
    function nr(v) {
      return function(L) {
        return v == null ? i : v[L];
      };
    }
    function h5(v, L, y, O, Q) {
      return Q(v, function(o1, k1, g1) {
        y = O ? (O = !1, o1) : L(y, o1, k1, g1);
      }), y;
    }
    function V8(v, L) {
      var y = v.length;
      for (v.sort(L); y--; )
        v[y] = v[y].value;
      return v;
    }
    function rr(v, L) {
      for (var y, O = -1, Q = v.length; ++O < Q; ) {
        var o1 = L(v[O]);
        o1 !== i && (y = y === i ? o1 : y + o1);
      }
      return y;
    }
    function ir(v, L) {
      for (var y = -1, O = Array(v); ++y < v; )
        O[y] = L(y);
      return O;
    }
    function X8(v, L) {
      return L1(L, function(y) {
        return [y, v[y]];
      });
    }
    function g5(v) {
      return v && v.slice(0, v5(v) + 1).replace(z0, "");
    }
    function ne(v) {
      return function(L) {
        return v(L);
      };
    }
    function ar(v, L) {
      return L1(L, function(y) {
        return v[y];
      });
    }
    function en(v, L) {
      return v.has(L);
    }
    function p5(v, L) {
      for (var y = -1, O = v.length; ++y < O && $t(L, v[y], 0) > -1; )
        ;
      return y;
    }
    function _5(v, L) {
      for (var y = v.length; y-- && $t(L, v[y], 0) > -1; )
        ;
      return y;
    }
    function q8(v, L) {
      for (var y = v.length, O = 0; y--; )
        v[y] === L && ++O;
      return O;
    }
    var j8 = nr(D8), J8 = nr(R8);
    function ei(v) {
      return "\\" + F8[v];
    }
    function ti(v, L) {
      return v == null ? i : v[L];
    }
    function bt(v) {
      return k8.test(v);
    }
    function ni(v) {
      return E8.test(v);
    }
    function ri(v) {
      for (var L, y = []; !(L = v.next()).done; )
        y.push(L.value);
      return y;
    }
    function sr(v) {
      var L = -1, y = Array(v.size);
      return v.forEach(function(O, Q) {
        y[++L] = [Q, O];
      }), y;
    }
    function d5(v, L) {
      return function(y) {
        return v(L(y));
      };
    }
    function Ve(v, L) {
      for (var y = -1, O = v.length, Q = 0, o1 = []; ++y < O; ) {
        var k1 = v[y];
        (k1 === L || k1 === x) && (v[y] = x, o1[Q++] = y);
      }
      return o1;
    }
    function An(v) {
      var L = -1, y = Array(v.size);
      return v.forEach(function(O) {
        y[++L] = O;
      }), y;
    }
    function ii(v) {
      var L = -1, y = Array(v.size);
      return v.forEach(function(O) {
        y[++L] = [O, O];
      }), y;
    }
    function ai(v, L, y) {
      for (var O = y - 1, Q = v.length; ++O < Q; )
        if (v[O] === L)
          return O;
      return -1;
    }
    function si(v, L, y) {
      for (var O = y + 1; O--; )
        if (v[O] === L)
          return O;
      return O;
    }
    function wt(v) {
      return bt(v) ? li(v) : Q8(v);
    }
    function me(v) {
      return bt(v) ? ci(v) : H8(v);
    }
    function v5(v) {
      for (var L = v.length; L-- && q3.test(v.charAt(L)); )
        ;
      return L;
    }
    var oi = nr(B8);
    function li(v) {
      for (var L = V0.lastIndex = 0; V0.test(v); )
        ++L;
      return L;
    }
    function ci(v) {
      return v.match(V0) || [];
    }
    function ui(v) {
      return v.match(I8) || [];
    }
    var fi = function v(L) {
      L = L == null ? F1 : At.defaults(F1.Object(), L, At.pick(F1, P8));
      var y = L.Array, O = L.Date, Q = L.Error, o1 = L.Function, k1 = L.Math, g1 = L.Object, or = L.RegExp, hi = L.String, ue = L.TypeError, Sn = y.prototype, gi = o1.prototype, St = g1.prototype, Mn = L["__core-js_shared__"], Tn = gi.toString, f1 = St.hasOwnProperty, pi = 0, C5 = function() {
        var e = /[^.]+$/.exec(Mn && Mn.keys && Mn.keys.IE_PROTO || "");
        return e ? "Symbol(src)_1." + e : "";
      }(), In = St.toString, _i = Tn.call(g1), di = F1._, vi = or(
        "^" + Tn.call(f1).replace(W0, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
      ), kn = t5 ? L.Buffer : i, Xe = L.Symbol, En = L.Uint8Array, y5 = kn ? kn.allocUnsafe : i, Pn = d5(g1.getPrototypeOf, g1), m5 = g1.create, L5 = St.propertyIsEnumerable, On = Sn.splice, x5 = Xe ? Xe.isConcatSpreadable : i, tn = Xe ? Xe.iterator : i, st = Xe ? Xe.toStringTag : i, Dn = function() {
        try {
          var e = ft(g1, "defineProperty");
          return e({}, "", {}), e;
        } catch {
        }
      }(), Ci = L.clearTimeout !== F1.clearTimeout && L.clearTimeout, yi = O && O.now !== F1.Date.now && O.now, mi = L.setTimeout !== F1.setTimeout && L.setTimeout, Rn = k1.ceil, Bn = k1.floor, lr = g1.getOwnPropertySymbols, Li = kn ? kn.isBuffer : i, $5 = L.isFinite, xi = Sn.join, $i = d5(g1.keys, g1), E1 = k1.max, K1 = k1.min, bi = O.now, wi = L.parseInt, b5 = k1.random, Ai = Sn.reverse, cr = ft(L, "DataView"), nn = ft(L, "Map"), ur = ft(L, "Promise"), Mt = ft(L, "Set"), rn = ft(L, "WeakMap"), an = ft(g1, "create"), Fn = rn && new rn(), Tt = {}, Si = ht(cr), Mi = ht(nn), Ti = ht(ur), Ii = ht(Mt), ki = ht(rn), Nn = Xe ? Xe.prototype : i, sn = Nn ? Nn.valueOf : i, w5 = Nn ? Nn.toString : i;
      function l(e) {
        if (w1(e) && !H(e) && !(e instanceof e1)) {
          if (e instanceof fe)
            return e;
          if (f1.call(e, "__wrapped__"))
            return A6(e);
        }
        return new fe(e);
      }
      var It = function() {
        function e() {
        }
        return function(t) {
          if (!b1(t))
            return {};
          if (m5)
            return m5(t);
          e.prototype = t;
          var r = new e();
          return e.prototype = i, r;
        };
      }();
      function Kn() {
      }
      function fe(e, t) {
        this.__wrapped__ = e, this.__actions__ = [], this.__chain__ = !!t, this.__index__ = 0, this.__values__ = i;
      }
      l.templateSettings = {
        /**
         * Used to detect `data` property values to be HTML-escaped.
         *
         * @memberOf _.templateSettings
         * @type {RegExp}
         */
        escape: Q3,
        /**
         * Used to detect code to be evaluated.
         *
         * @memberOf _.templateSettings
         * @type {RegExp}
         */
        evaluate: H3,
        /**
         * Used to detect `data` property values to inject.
         *
         * @memberOf _.templateSettings
         * @type {RegExp}
         */
        interpolate: O9,
        /**
         * Used to reference the data object in the template text.
         *
         * @memberOf _.templateSettings
         * @type {string}
         */
        variable: "",
        /**
         * Used to import variables into the compiled template.
         *
         * @memberOf _.templateSettings
         * @type {Object}
         */
        imports: {
          /**
           * A reference to the `lodash` function.
           *
           * @memberOf _.templateSettings.imports
           * @type {Function}
           */
          _: l
        }
      }, l.prototype = Kn.prototype, l.prototype.constructor = l, fe.prototype = It(Kn.prototype), fe.prototype.constructor = fe;
      function e1(e) {
        this.__wrapped__ = e, this.__actions__ = [], this.__dir__ = 1, this.__filtered__ = !1, this.__iteratees__ = [], this.__takeCount__ = u1, this.__views__ = [];
      }
      function Ei() {
        var e = new e1(this.__wrapped__);
        return e.__actions__ = Y1(this.__actions__), e.__dir__ = this.__dir__, e.__filtered__ = this.__filtered__, e.__iteratees__ = Y1(this.__iteratees__), e.__takeCount__ = this.__takeCount__, e.__views__ = Y1(this.__views__), e;
      }
      function Pi() {
        if (this.__filtered__) {
          var e = new e1(this);
          e.__dir__ = -1, e.__filtered__ = !0;
        } else
          e = this.clone(), e.__dir__ *= -1;
        return e;
      }
      function Oi() {
        var e = this.__wrapped__.value(), t = this.__dir__, r = H(e), s = t < 0, o = r ? e.length : 0, c = H7(0, o, this.__views__), h = c.start, _ = c.end, C = _ - h, $ = s ? _ : h - 1, b = this.__iteratees__, w = b.length, k = 0, R = K1(C, this.__takeCount__);
        if (!r || !s && o == C && R == C)
          return V5(e, this.__actions__);
        var Z = [];
        e:
          for (; C-- && k < R; ) {
            $ += t;
            for (var X = -1, W = e[$]; ++X < w; ) {
              var J = b[X], r1 = J.iteratee, ae = J.type, H1 = r1(W);
              if (ae == Pe)
                W = H1;
              else if (!H1) {
                if (ae == rt)
                  continue e;
                break e;
              }
            }
            Z[k++] = W;
          }
        return Z;
      }
      e1.prototype = It(Kn.prototype), e1.prototype.constructor = e1;
      function ot(e) {
        var t = -1, r = e == null ? 0 : e.length;
        for (this.clear(); ++t < r; ) {
          var s = e[t];
          this.set(s[0], s[1]);
        }
      }
      function Di() {
        this.__data__ = an ? an(null) : {}, this.size = 0;
      }
      function Ri(e) {
        var t = this.has(e) && delete this.__data__[e];
        return this.size -= t ? 1 : 0, t;
      }
      function Bi(e) {
        var t = this.__data__;
        if (an) {
          var r = t[e];
          return r === m ? i : r;
        }
        return f1.call(t, e) ? t[e] : i;
      }
      function Fi(e) {
        var t = this.__data__;
        return an ? t[e] !== i : f1.call(t, e);
      }
      function Ni(e, t) {
        var r = this.__data__;
        return this.size += this.has(e) ? 0 : 1, r[e] = an && t === i ? m : t, this;
      }
      ot.prototype.clear = Di, ot.prototype.delete = Ri, ot.prototype.get = Bi, ot.prototype.has = Fi, ot.prototype.set = Ni;
      function De(e) {
        var t = -1, r = e == null ? 0 : e.length;
        for (this.clear(); ++t < r; ) {
          var s = e[t];
          this.set(s[0], s[1]);
        }
      }
      function Ki() {
        this.__data__ = [], this.size = 0;
      }
      function Ui(e) {
        var t = this.__data__, r = Un(t, e);
        if (r < 0)
          return !1;
        var s = t.length - 1;
        return r == s ? t.pop() : On.call(t, r, 1), --this.size, !0;
      }
      function Zi(e) {
        var t = this.__data__, r = Un(t, e);
        return r < 0 ? i : t[r][1];
      }
      function Wi(e) {
        return Un(this.__data__, e) > -1;
      }
      function zi(e, t) {
        var r = this.__data__, s = Un(r, e);
        return s < 0 ? (++this.size, r.push([e, t])) : r[s][1] = t, this;
      }
      De.prototype.clear = Ki, De.prototype.delete = Ui, De.prototype.get = Zi, De.prototype.has = Wi, De.prototype.set = zi;
      function Re(e) {
        var t = -1, r = e == null ? 0 : e.length;
        for (this.clear(); ++t < r; ) {
          var s = e[t];
          this.set(s[0], s[1]);
        }
      }
      function Qi() {
        this.size = 0, this.__data__ = {
          hash: new ot(),
          map: new (nn || De)(),
          string: new ot()
        };
      }
      function Hi(e) {
        var t = Jn(this, e).delete(e);
        return this.size -= t ? 1 : 0, t;
      }
      function Gi(e) {
        return Jn(this, e).get(e);
      }
      function Yi(e) {
        return Jn(this, e).has(e);
      }
      function Vi(e, t) {
        var r = Jn(this, e), s = r.size;
        return r.set(e, t), this.size += r.size == s ? 0 : 1, this;
      }
      Re.prototype.clear = Qi, Re.prototype.delete = Hi, Re.prototype.get = Gi, Re.prototype.has = Yi, Re.prototype.set = Vi;
      function lt(e) {
        var t = -1, r = e == null ? 0 : e.length;
        for (this.__data__ = new Re(); ++t < r; )
          this.add(e[t]);
      }
      function Xi(e) {
        return this.__data__.set(e, m), this;
      }
      function qi(e) {
        return this.__data__.has(e);
      }
      lt.prototype.add = lt.prototype.push = Xi, lt.prototype.has = qi;
      function Le(e) {
        var t = this.__data__ = new De(e);
        this.size = t.size;
      }
      function ji() {
        this.__data__ = new De(), this.size = 0;
      }
      function Ji(e) {
        var t = this.__data__, r = t.delete(e);
        return this.size = t.size, r;
      }
      function e7(e) {
        return this.__data__.get(e);
      }
      function t7(e) {
        return this.__data__.has(e);
      }
      function n7(e, t) {
        var r = this.__data__;
        if (r instanceof De) {
          var s = r.__data__;
          if (!nn || s.length < f - 1)
            return s.push([e, t]), this.size = ++r.size, this;
          r = this.__data__ = new Re(s);
        }
        return r.set(e, t), this.size = r.size, this;
      }
      Le.prototype.clear = ji, Le.prototype.delete = Ji, Le.prototype.get = e7, Le.prototype.has = t7, Le.prototype.set = n7;
      function A5(e, t) {
        var r = H(e), s = !r && gt(e), o = !r && !s && tt(e), c = !r && !s && !o && Ot(e), h = r || s || o || c, _ = h ? ir(e.length, hi) : [], C = _.length;
        for (var $ in e)
          (t || f1.call(e, $)) && !(h && // Safari 9 has enumerable `arguments.length` in strict mode.
          ($ == "length" || // Node.js 0.10 has enumerable non-index properties on buffers.
          o && ($ == "offset" || $ == "parent") || // PhantomJS 2 has enumerable non-index properties on typed arrays.
          c && ($ == "buffer" || $ == "byteLength" || $ == "byteOffset") || // Skip index properties.
          Ke($, C))) && _.push($);
        return _;
      }
      function S5(e) {
        var t = e.length;
        return t ? e[Lr(0, t - 1)] : i;
      }
      function r7(e, t) {
        return e0(Y1(e), ct(t, 0, e.length));
      }
      function i7(e) {
        return e0(Y1(e));
      }
      function fr(e, t, r) {
        (r !== i && !xe(e[t], r) || r === i && !(t in e)) && Be(e, t, r);
      }
      function on(e, t, r) {
        var s = e[t];
        (!(f1.call(e, t) && xe(s, r)) || r === i && !(t in e)) && Be(e, t, r);
      }
      function Un(e, t) {
        for (var r = e.length; r--; )
          if (xe(e[r][0], t))
            return r;
        return -1;
      }
      function a7(e, t, r, s) {
        return qe(e, function(o, c, h) {
          t(s, o, r(o), h);
        }), s;
      }
      function M5(e, t) {
        return e && Me(t, D1(t), e);
      }
      function s7(e, t) {
        return e && Me(t, X1(t), e);
      }
      function Be(e, t, r) {
        t == "__proto__" && Dn ? Dn(e, t, {
          configurable: !0,
          enumerable: !0,
          value: r,
          writable: !0
        }) : e[t] = r;
      }
      function hr(e, t) {
        for (var r = -1, s = t.length, o = y(s), c = e == null; ++r < s; )
          o[r] = c ? i : Hr(e, t[r]);
        return o;
      }
      function ct(e, t, r) {
        return e === e && (r !== i && (e = e <= r ? e : r), t !== i && (e = e >= t ? e : t)), e;
      }
      function he(e, t, r, s, o, c) {
        var h, _ = t & M, C = t & D, $ = t & z;
        if (r && (h = o ? r(e, s, o, c) : r(e)), h !== i)
          return h;
        if (!b1(e))
          return e;
        var b = H(e);
        if (b) {
          if (h = Y7(e), !_)
            return Y1(e, h);
        } else {
          var w = U1(e), k = w == G1 || w == Ae;
          if (tt(e))
            return j5(e, _);
          if (w == Oe || w == Ce || k && !o) {
            if (h = C || k ? {} : v6(e), !_)
              return C ? B7(e, s7(h, e)) : R7(e, M5(h, e));
          } else {
            if (!_1[w])
              return o ? e : {};
            h = V7(e, w, _);
          }
        }
        c || (c = new Le());
        var R = c.get(e);
        if (R)
          return R;
        c.set(e, h), H6(e) ? e.forEach(function(W) {
          h.add(he(W, t, r, W, e, c));
        }) : z6(e) && e.forEach(function(W, J) {
          h.set(J, he(W, t, r, J, e, c));
        });
        var Z = $ ? C ? Er : kr : C ? X1 : D1, X = b ? i : Z(e);
        return ce(X || e, function(W, J) {
          X && (J = W, W = e[J]), on(h, J, he(W, t, r, J, e, c));
        }), h;
      }
      function o7(e) {
        var t = D1(e);
        return function(r) {
          return T5(r, e, t);
        };
      }
      function T5(e, t, r) {
        var s = r.length;
        if (e == null)
          return !s;
        for (e = g1(e); s--; ) {
          var o = r[s], c = t[o], h = e[o];
          if (h === i && !(o in e) || !c(h))
            return !1;
        }
        return !0;
      }
      function I5(e, t, r) {
        if (typeof e != "function")
          throw new ue(d);
        return pn(function() {
          e.apply(i, r);
        }, t);
      }
      function ln(e, t, r, s) {
        var o = -1, c = bn, h = !0, _ = e.length, C = [], $ = t.length;
        if (!_)
          return C;
        r && (t = L1(t, ne(r))), s ? (c = j0, h = !1) : t.length >= f && (c = en, h = !1, t = new lt(t));
        e:
          for (; ++o < _; ) {
            var b = e[o], w = r == null ? b : r(b);
            if (b = s || b !== 0 ? b : 0, h && w === w) {
              for (var k = $; k--; )
                if (t[k] === w)
                  continue e;
              C.push(b);
            } else
              c(t, w, s) || C.push(b);
          }
        return C;
      }
      var qe = r6(Se), k5 = r6(pr, !0);
      function l7(e, t) {
        var r = !0;
        return qe(e, function(s, o, c) {
          return r = !!t(s, o, c), r;
        }), r;
      }
      function Zn(e, t, r) {
        for (var s = -1, o = e.length; ++s < o; ) {
          var c = e[s], h = t(c);
          if (h != null && (_ === i ? h === h && !ie(h) : r(h, _)))
            var _ = h, C = c;
        }
        return C;
      }
      function c7(e, t, r, s) {
        var o = e.length;
        for (r = Y(r), r < 0 && (r = -r > o ? 0 : o + r), s = s === i || s > o ? o : Y(s), s < 0 && (s += o), s = r > s ? 0 : Y6(s); r < s; )
          e[r++] = t;
        return e;
      }
      function E5(e, t) {
        var r = [];
        return qe(e, function(s, o, c) {
          t(s, o, c) && r.push(s);
        }), r;
      }
      function N1(e, t, r, s, o) {
        var c = -1, h = e.length;
        for (r || (r = q7), o || (o = []); ++c < h; ) {
          var _ = e[c];
          t > 0 && r(_) ? t > 1 ? N1(_, t - 1, r, s, o) : Ye(o, _) : s || (o[o.length] = _);
        }
        return o;
      }
      var gr = i6(), P5 = i6(!0);
      function Se(e, t) {
        return e && gr(e, t, D1);
      }
      function pr(e, t) {
        return e && P5(e, t, D1);
      }
      function Wn(e, t) {
        return Ge(t, function(r) {
          return Ue(e[r]);
        });
      }
      function ut(e, t) {
        t = Je(t, e);
        for (var r = 0, s = t.length; e != null && r < s; )
          e = e[Te(t[r++])];
        return r && r == s ? e : i;
      }
      function O5(e, t, r) {
        var s = t(e);
        return H(e) ? s : Ye(s, r(e));
      }
      function z1(e) {
        return e == null ? e === i ? F3 : R3 : st && st in g1(e) ? Q7(e) : ia(e);
      }
      function _r(e, t) {
        return e > t;
      }
      function u7(e, t) {
        return e != null && f1.call(e, t);
      }
      function f7(e, t) {
        return e != null && t in g1(e);
      }
      function h7(e, t, r) {
        return e >= K1(t, r) && e < E1(t, r);
      }
      function dr(e, t, r) {
        for (var s = r ? j0 : bn, o = e[0].length, c = e.length, h = c, _ = y(c), C = 1 / 0, $ = []; h--; ) {
          var b = e[h];
          h && t && (b = L1(b, ne(t))), C = K1(b.length, C), _[h] = !r && (t || o >= 120 && b.length >= 120) ? new lt(h && b) : i;
        }
        b = e[0];
        var w = -1, k = _[0];
        e:
          for (; ++w < o && $.length < C; ) {
            var R = b[w], Z = t ? t(R) : R;
            if (R = r || R !== 0 ? R : 0, !(k ? en(k, Z) : s($, Z, r))) {
              for (h = c; --h; ) {
                var X = _[h];
                if (!(X ? en(X, Z) : s(e[h], Z, r)))
                  continue e;
              }
              k && k.push(Z), $.push(R);
            }
          }
        return $;
      }
      function g7(e, t, r, s) {
        return Se(e, function(o, c, h) {
          t(s, r(o), c, h);
        }), s;
      }
      function cn(e, t, r) {
        t = Je(t, e), e = L6(e, t);
        var s = e == null ? e : e[Te(pe(t))];
        return s == null ? i : te(s, e, r);
      }
      function D5(e) {
        return w1(e) && z1(e) == Ce;
      }
      function p7(e) {
        return w1(e) && z1(e) == Jt;
      }
      function _7(e) {
        return w1(e) && z1(e) == N;
      }
      function un(e, t, r, s, o) {
        return e === t ? !0 : e == null || t == null || !w1(e) && !w1(t) ? e !== e && t !== t : d7(e, t, r, s, un, o);
      }
      function d7(e, t, r, s, o, c) {
        var h = H(e), _ = H(t), C = h ? T : U1(e), $ = _ ? T : U1(t);
        C = C == Ce ? Oe : C, $ = $ == Ce ? Oe : $;
        var b = C == Oe, w = $ == Oe, k = C == $;
        if (k && tt(e)) {
          if (!tt(t))
            return !1;
          h = !0, b = !1;
        }
        if (k && !b)
          return c || (c = new Le()), h || Ot(e) ? p6(e, t, r, s, o, c) : W7(e, t, C, r, s, o, c);
        if (!(r & t1)) {
          var R = b && f1.call(e, "__wrapped__"), Z = w && f1.call(t, "__wrapped__");
          if (R || Z) {
            var X = R ? e.value() : e, W = Z ? t.value() : t;
            return c || (c = new Le()), o(X, W, r, s, c);
          }
        }
        return k ? (c || (c = new Le()), z7(e, t, r, s, o, c)) : !1;
      }
      function v7(e) {
        return w1(e) && U1(e) == O1;
      }
      function vr(e, t, r, s) {
        var o = r.length, c = o, h = !s;
        if (e == null)
          return !c;
        for (e = g1(e); o--; ) {
          var _ = r[o];
          if (h && _[2] ? _[1] !== e[_[0]] : !(_[0] in e))
            return !1;
        }
        for (; ++o < c; ) {
          _ = r[o];
          var C = _[0], $ = e[C], b = _[1];
          if (h && _[2]) {
            if ($ === i && !(C in e))
              return !1;
          } else {
            var w = new Le();
            if (s)
              var k = s($, b, C, e, t, w);
            if (!(k === i ? un(b, $, t1 | p1, s, w) : k))
              return !1;
          }
        }
        return !0;
      }
      function R5(e) {
        if (!b1(e) || J7(e))
          return !1;
        var t = Ue(e) ? vi : o8;
        return t.test(ht(e));
      }
      function C7(e) {
        return w1(e) && z1(e) == Xt;
      }
      function y7(e) {
        return w1(e) && U1(e) == ye;
      }
      function m7(e) {
        return w1(e) && s0(e.length) && !!v1[z1(e)];
      }
      function B5(e) {
        return typeof e == "function" ? e : e == null ? q1 : typeof e == "object" ? H(e) ? K5(e[0], e[1]) : N5(e) : a2(e);
      }
      function Cr(e) {
        if (!gn(e))
          return $i(e);
        var t = [];
        for (var r in g1(e))
          f1.call(e, r) && r != "constructor" && t.push(r);
        return t;
      }
      function L7(e) {
        if (!b1(e))
          return ra(e);
        var t = gn(e), r = [];
        for (var s in e)
          s == "constructor" && (t || !f1.call(e, s)) || r.push(s);
        return r;
      }
      function yr(e, t) {
        return e < t;
      }
      function F5(e, t) {
        var r = -1, s = V1(e) ? y(e.length) : [];
        return qe(e, function(o, c, h) {
          s[++r] = t(o, c, h);
        }), s;
      }
      function N5(e) {
        var t = Or(e);
        return t.length == 1 && t[0][2] ? y6(t[0][0], t[0][1]) : function(r) {
          return r === e || vr(r, e, t);
        };
      }
      function K5(e, t) {
        return Rr(e) && C6(t) ? y6(Te(e), t) : function(r) {
          var s = Hr(r, e);
          return s === i && s === t ? Gr(r, e) : un(t, s, t1 | p1);
        };
      }
      function zn(e, t, r, s, o) {
        e !== t && gr(t, function(c, h) {
          if (o || (o = new Le()), b1(c))
            x7(e, t, h, r, zn, s, o);
          else {
            var _ = s ? s(Fr(e, h), c, h + "", e, t, o) : i;
            _ === i && (_ = c), fr(e, h, _);
          }
        }, X1);
      }
      function x7(e, t, r, s, o, c, h) {
        var _ = Fr(e, r), C = Fr(t, r), $ = h.get(C);
        if ($) {
          fr(e, r, $);
          return;
        }
        var b = c ? c(_, C, r + "", e, t, h) : i, w = b === i;
        if (w) {
          var k = H(C), R = !k && tt(C), Z = !k && !R && Ot(C);
          b = C, k || R || Z ? H(_) ? b = _ : T1(_) ? b = Y1(_) : R ? (w = !1, b = j5(C, !0)) : Z ? (w = !1, b = J5(C, !0)) : b = [] : _n(C) || gt(C) ? (b = _, gt(_) ? b = V6(_) : (!b1(_) || Ue(_)) && (b = v6(C))) : w = !1;
        }
        w && (h.set(C, b), o(b, C, s, c, h), h.delete(C)), fr(e, r, b);
      }
      function U5(e, t) {
        var r = e.length;
        if (r)
          return t += t < 0 ? r : 0, Ke(t, r) ? e[t] : i;
      }
      function Z5(e, t, r) {
        t.length ? t = L1(t, function(c) {
          return H(c) ? function(h) {
            return ut(h, c.length === 1 ? c[0] : c);
          } : c;
        }) : t = [q1];
        var s = -1;
        t = L1(t, ne(K()));
        var o = F5(e, function(c, h, _) {
          var C = L1(t, function($) {
            return $(c);
          });
          return { criteria: C, index: ++s, value: c };
        });
        return V8(o, function(c, h) {
          return D7(c, h, r);
        });
      }
      function $7(e, t) {
        return W5(e, t, function(r, s) {
          return Gr(e, s);
        });
      }
      function W5(e, t, r) {
        for (var s = -1, o = t.length, c = {}; ++s < o; ) {
          var h = t[s], _ = ut(e, h);
          r(_, h) && fn(c, Je(h, e), _);
        }
        return c;
      }
      function b7(e) {
        return function(t) {
          return ut(t, e);
        };
      }
      function mr(e, t, r, s) {
        var o = s ? Y8 : $t, c = -1, h = t.length, _ = e;
        for (e === t && (t = Y1(t)), r && (_ = L1(e, ne(r))); ++c < h; )
          for (var C = 0, $ = t[c], b = r ? r($) : $; (C = o(_, b, C, s)) > -1; )
            _ !== e && On.call(_, C, 1), On.call(e, C, 1);
        return e;
      }
      function z5(e, t) {
        for (var r = e ? t.length : 0, s = r - 1; r--; ) {
          var o = t[r];
          if (r == s || o !== c) {
            var c = o;
            Ke(o) ? On.call(e, o, 1) : br(e, o);
          }
        }
        return e;
      }
      function Lr(e, t) {
        return e + Bn(b5() * (t - e + 1));
      }
      function w7(e, t, r, s) {
        for (var o = -1, c = E1(Rn((t - e) / (r || 1)), 0), h = y(c); c--; )
          h[s ? c : ++o] = e, e += r;
        return h;
      }
      function xr(e, t) {
        var r = "";
        if (!e || t < 1 || t > J1)
          return r;
        do
          t % 2 && (r += e), t = Bn(t / 2), t && (e += e);
        while (t);
        return r;
      }
      function j(e, t) {
        return Nr(m6(e, t, q1), e + "");
      }
      function A7(e) {
        return S5(Dt(e));
      }
      function S7(e, t) {
        var r = Dt(e);
        return e0(r, ct(t, 0, r.length));
      }
      function fn(e, t, r, s) {
        if (!b1(e))
          return e;
        t = Je(t, e);
        for (var o = -1, c = t.length, h = c - 1, _ = e; _ != null && ++o < c; ) {
          var C = Te(t[o]), $ = r;
          if (C === "__proto__" || C === "constructor" || C === "prototype")
            return e;
          if (o != h) {
            var b = _[C];
            $ = s ? s(b, C, _) : i, $ === i && ($ = b1(b) ? b : Ke(t[o + 1]) ? [] : {});
          }
          on(_, C, $), _ = _[C];
        }
        return e;
      }
      var Q5 = Fn ? function(e, t) {
        return Fn.set(e, t), e;
      } : q1, M7 = Dn ? function(e, t) {
        return Dn(e, "toString", {
          configurable: !0,
          enumerable: !1,
          value: Vr(t),
          writable: !0
        });
      } : q1;
      function T7(e) {
        return e0(Dt(e));
      }
      function ge(e, t, r) {
        var s = -1, o = e.length;
        t < 0 && (t = -t > o ? 0 : o + t), r = r > o ? o : r, r < 0 && (r += o), o = t > r ? 0 : r - t >>> 0, t >>>= 0;
        for (var c = y(o); ++s < o; )
          c[s] = e[s + t];
        return c;
      }
      function I7(e, t) {
        var r;
        return qe(e, function(s, o, c) {
          return r = t(s, o, c), !r;
        }), !!r;
      }
      function Qn(e, t, r) {
        var s = 0, o = e == null ? s : e.length;
        if (typeof t == "number" && t === t && o <= we) {
          for (; s < o; ) {
            var c = s + o >>> 1, h = e[c];
            h !== null && !ie(h) && (r ? h <= t : h < t) ? s = c + 1 : o = c;
          }
          return o;
        }
        return $r(e, t, q1, r);
      }
      function $r(e, t, r, s) {
        var o = 0, c = e == null ? 0 : e.length;
        if (c === 0)
          return 0;
        t = r(t);
        for (var h = t !== t, _ = t === null, C = ie(t), $ = t === i; o < c; ) {
          var b = Bn((o + c) / 2), w = r(e[b]), k = w !== i, R = w === null, Z = w === w, X = ie(w);
          if (h)
            var W = s || Z;
          else
            $ ? W = Z && (s || k) : _ ? W = Z && k && (s || !R) : C ? W = Z && k && !R && (s || !X) : R || X ? W = !1 : W = s ? w <= t : w < t;
          W ? o = b + 1 : c = b;
        }
        return K1(c, ee);
      }
      function H5(e, t) {
        for (var r = -1, s = e.length, o = 0, c = []; ++r < s; ) {
          var h = e[r], _ = t ? t(h) : h;
          if (!r || !xe(_, C)) {
            var C = _;
            c[o++] = h === 0 ? 0 : h;
          }
        }
        return c;
      }
      function G5(e) {
        return typeof e == "number" ? e : ie(e) ? a1 : +e;
      }
      function re(e) {
        if (typeof e == "string")
          return e;
        if (H(e))
          return L1(e, re) + "";
        if (ie(e))
          return w5 ? w5.call(e) : "";
        var t = e + "";
        return t == "0" && 1 / e == -oe ? "-0" : t;
      }
      function je(e, t, r) {
        var s = -1, o = bn, c = e.length, h = !0, _ = [], C = _;
        if (r)
          h = !1, o = j0;
        else if (c >= f) {
          var $ = t ? null : U7(e);
          if ($)
            return An($);
          h = !1, o = en, C = new lt();
        } else
          C = t ? [] : _;
        e:
          for (; ++s < c; ) {
            var b = e[s], w = t ? t(b) : b;
            if (b = r || b !== 0 ? b : 0, h && w === w) {
              for (var k = C.length; k--; )
                if (C[k] === w)
                  continue e;
              t && C.push(w), _.push(b);
            } else
              o(C, w, r) || (C !== _ && C.push(w), _.push(b));
          }
        return _;
      }
      function br(e, t) {
        return t = Je(t, e), e = L6(e, t), e == null || delete e[Te(pe(t))];
      }
      function Y5(e, t, r, s) {
        return fn(e, t, r(ut(e, t)), s);
      }
      function Hn(e, t, r, s) {
        for (var o = e.length, c = s ? o : -1; (s ? c-- : ++c < o) && t(e[c], c, e); )
          ;
        return r ? ge(e, s ? 0 : c, s ? c + 1 : o) : ge(e, s ? c + 1 : 0, s ? o : c);
      }
      function V5(e, t) {
        var r = e;
        return r instanceof e1 && (r = r.value()), J0(t, function(s, o) {
          return o.func.apply(o.thisArg, Ye([s], o.args));
        }, r);
      }
      function wr(e, t, r) {
        var s = e.length;
        if (s < 2)
          return s ? je(e[0]) : [];
        for (var o = -1, c = y(s); ++o < s; )
          for (var h = e[o], _ = -1; ++_ < s; )
            _ != o && (c[o] = ln(c[o] || h, e[_], t, r));
        return je(N1(c, 1), t, r);
      }
      function X5(e, t, r) {
        for (var s = -1, o = e.length, c = t.length, h = {}; ++s < o; ) {
          var _ = s < c ? t[s] : i;
          r(h, e[s], _);
        }
        return h;
      }
      function Ar(e) {
        return T1(e) ? e : [];
      }
      function Sr(e) {
        return typeof e == "function" ? e : q1;
      }
      function Je(e, t) {
        return H(e) ? e : Rr(e, t) ? [e] : w6(c1(e));
      }
      var k7 = j;
      function et(e, t, r) {
        var s = e.length;
        return r = r === i ? s : r, !t && r >= s ? e : ge(e, t, r);
      }
      var q5 = Ci || function(e) {
        return F1.clearTimeout(e);
      };
      function j5(e, t) {
        if (t)
          return e.slice();
        var r = e.length, s = y5 ? y5(r) : new e.constructor(r);
        return e.copy(s), s;
      }
      function Mr(e) {
        var t = new e.constructor(e.byteLength);
        return new En(t).set(new En(e)), t;
      }
      function E7(e, t) {
        var r = t ? Mr(e.buffer) : e.buffer;
        return new e.constructor(r, e.byteOffset, e.byteLength);
      }
      function P7(e) {
        var t = new e.constructor(e.source, D9.exec(e));
        return t.lastIndex = e.lastIndex, t;
      }
      function O7(e) {
        return sn ? g1(sn.call(e)) : {};
      }
      function J5(e, t) {
        var r = t ? Mr(e.buffer) : e.buffer;
        return new e.constructor(r, e.byteOffset, e.length);
      }
      function e6(e, t) {
        if (e !== t) {
          var r = e !== i, s = e === null, o = e === e, c = ie(e), h = t !== i, _ = t === null, C = t === t, $ = ie(t);
          if (!_ && !$ && !c && e > t || c && h && C && !_ && !$ || s && h && C || !r && C || !o)
            return 1;
          if (!s && !c && !$ && e < t || $ && r && o && !s && !c || _ && r && o || !h && o || !C)
            return -1;
        }
        return 0;
      }
      function D7(e, t, r) {
        for (var s = -1, o = e.criteria, c = t.criteria, h = o.length, _ = r.length; ++s < h; ) {
          var C = e6(o[s], c[s]);
          if (C) {
            if (s >= _)
              return C;
            var $ = r[s];
            return C * ($ == "desc" ? -1 : 1);
          }
        }
        return e.index - t.index;
      }
      function t6(e, t, r, s) {
        for (var o = -1, c = e.length, h = r.length, _ = -1, C = t.length, $ = E1(c - h, 0), b = y(C + $), w = !s; ++_ < C; )
          b[_] = t[_];
        for (; ++o < h; )
          (w || o < c) && (b[r[o]] = e[o]);
        for (; $--; )
          b[_++] = e[o++];
        return b;
      }
      function n6(e, t, r, s) {
        for (var o = -1, c = e.length, h = -1, _ = r.length, C = -1, $ = t.length, b = E1(c - _, 0), w = y(b + $), k = !s; ++o < b; )
          w[o] = e[o];
        for (var R = o; ++C < $; )
          w[R + C] = t[C];
        for (; ++h < _; )
          (k || o < c) && (w[R + r[h]] = e[o++]);
        return w;
      }
      function Y1(e, t) {
        var r = -1, s = e.length;
        for (t || (t = y(s)); ++r < s; )
          t[r] = e[r];
        return t;
      }
      function Me(e, t, r, s) {
        var o = !r;
        r || (r = {});
        for (var c = -1, h = t.length; ++c < h; ) {
          var _ = t[c], C = s ? s(r[_], e[_], _, r, e) : i;
          C === i && (C = e[_]), o ? Be(r, _, C) : on(r, _, C);
        }
        return r;
      }
      function R7(e, t) {
        return Me(e, Dr(e), t);
      }
      function B7(e, t) {
        return Me(e, _6(e), t);
      }
      function Gn(e, t) {
        return function(r, s) {
          var o = H(r) ? Z8 : a7, c = t ? t() : {};
          return o(r, e, K(s, 2), c);
        };
      }
      function kt(e) {
        return j(function(t, r) {
          var s = -1, o = r.length, c = o > 1 ? r[o - 1] : i, h = o > 2 ? r[2] : i;
          for (c = e.length > 3 && typeof c == "function" ? (o--, c) : i, h && Q1(r[0], r[1], h) && (c = o < 3 ? i : c, o = 1), t = g1(t); ++s < o; ) {
            var _ = r[s];
            _ && e(t, _, s, c);
          }
          return t;
        });
      }
      function r6(e, t) {
        return function(r, s) {
          if (r == null)
            return r;
          if (!V1(r))
            return e(r, s);
          for (var o = r.length, c = t ? o : -1, h = g1(r); (t ? c-- : ++c < o) && s(h[c], c, h) !== !1; )
            ;
          return r;
        };
      }
      function i6(e) {
        return function(t, r, s) {
          for (var o = -1, c = g1(t), h = s(t), _ = h.length; _--; ) {
            var C = h[e ? _ : ++o];
            if (r(c[C], C, c) === !1)
              break;
          }
          return t;
        };
      }
      function F7(e, t, r) {
        var s = t & n1, o = hn(e);
        function c() {
          var h = this && this !== F1 && this instanceof c ? o : e;
          return h.apply(s ? r : this, arguments);
        }
        return c;
      }
      function a6(e) {
        return function(t) {
          t = c1(t);
          var r = bt(t) ? me(t) : i, s = r ? r[0] : t.charAt(0), o = r ? et(r, 1).join("") : t.slice(1);
          return s[e]() + o;
        };
      }
      function Et(e) {
        return function(t) {
          return J0(r2(n2(t).replace(M8, "")), e, "");
        };
      }
      function hn(e) {
        return function() {
          var t = arguments;
          switch (t.length) {
            case 0:
              return new e();
            case 1:
              return new e(t[0]);
            case 2:
              return new e(t[0], t[1]);
            case 3:
              return new e(t[0], t[1], t[2]);
            case 4:
              return new e(t[0], t[1], t[2], t[3]);
            case 5:
              return new e(t[0], t[1], t[2], t[3], t[4]);
            case 6:
              return new e(t[0], t[1], t[2], t[3], t[4], t[5]);
            case 7:
              return new e(t[0], t[1], t[2], t[3], t[4], t[5], t[6]);
          }
          var r = It(e.prototype), s = e.apply(r, t);
          return b1(s) ? s : r;
        };
      }
      function N7(e, t, r) {
        var s = hn(e);
        function o() {
          for (var c = arguments.length, h = y(c), _ = c, C = Pt(o); _--; )
            h[_] = arguments[_];
          var $ = c < 3 && h[0] !== C && h[c - 1] !== C ? [] : Ve(h, C);
          if (c -= $.length, c < r)
            return u6(
              e,
              t,
              Yn,
              o.placeholder,
              i,
              h,
              $,
              i,
              i,
              r - c
            );
          var b = this && this !== F1 && this instanceof o ? s : e;
          return te(b, this, h);
        }
        return o;
      }
      function s6(e) {
        return function(t, r, s) {
          var o = g1(t);
          if (!V1(t)) {
            var c = K(r, 3);
            t = D1(t), r = function(_) {
              return c(o[_], _, o);
            };
          }
          var h = e(t, r, s);
          return h > -1 ? o[c ? t[h] : h] : i;
        };
      }
      function o6(e) {
        return Ne(function(t) {
          var r = t.length, s = r, o = fe.prototype.thru;
          for (e && t.reverse(); s--; ) {
            var c = t[s];
            if (typeof c != "function")
              throw new ue(d);
            if (o && !h && jn(c) == "wrapper")
              var h = new fe([], !0);
          }
          for (s = h ? s : r; ++s < r; ) {
            c = t[s];
            var _ = jn(c), C = _ == "wrapper" ? Pr(c) : i;
            C && Br(C[0]) && C[1] == (M1 | U | $1 | s1) && !C[4].length && C[9] == 1 ? h = h[jn(C[0])].apply(h, C[3]) : h = c.length == 1 && Br(c) ? h[_]() : h.thru(c);
          }
          return function() {
            var $ = arguments, b = $[0];
            if (h && $.length == 1 && H(b))
              return h.plant(b).value();
            for (var w = 0, k = r ? t[w].apply(this, $) : b; ++w < r; )
              k = t[w].call(this, k);
            return k;
          };
        });
      }
      function Yn(e, t, r, s, o, c, h, _, C, $) {
        var b = t & M1, w = t & n1, k = t & i1, R = t & (U | q), Z = t & l1, X = k ? i : hn(e);
        function W() {
          for (var J = arguments.length, r1 = y(J), ae = J; ae--; )
            r1[ae] = arguments[ae];
          if (R)
            var H1 = Pt(W), se = q8(r1, H1);
          if (s && (r1 = t6(r1, s, o, R)), c && (r1 = n6(r1, c, h, R)), J -= se, R && J < $) {
            var I1 = Ve(r1, H1);
            return u6(
              e,
              t,
              Yn,
              W.placeholder,
              r,
              r1,
              I1,
              _,
              C,
              $ - J
            );
          }
          var $e = w ? r : this, We = k ? $e[e] : e;
          return J = r1.length, _ ? r1 = aa(r1, _) : Z && J > 1 && r1.reverse(), b && C < J && (r1.length = C), this && this !== F1 && this instanceof W && (We = X || hn(We)), We.apply($e, r1);
        }
        return W;
      }
      function l6(e, t) {
        return function(r, s) {
          return g7(r, e, t(s), {});
        };
      }
      function Vn(e, t) {
        return function(r, s) {
          var o;
          if (r === i && s === i)
            return t;
          if (r !== i && (o = r), s !== i) {
            if (o === i)
              return s;
            typeof r == "string" || typeof s == "string" ? (r = re(r), s = re(s)) : (r = G5(r), s = G5(s)), o = e(r, s);
          }
          return o;
        };
      }
      function Tr(e) {
        return Ne(function(t) {
          return t = L1(t, ne(K())), j(function(r) {
            var s = this;
            return e(t, function(o) {
              return te(o, s, r);
            });
          });
        });
      }
      function Xn(e, t) {
        t = t === i ? " " : re(t);
        var r = t.length;
        if (r < 2)
          return r ? xr(t, e) : t;
        var s = xr(t, Rn(e / wt(t)));
        return bt(t) ? et(me(s), 0, e).join("") : s.slice(0, e);
      }
      function K7(e, t, r, s) {
        var o = t & n1, c = hn(e);
        function h() {
          for (var _ = -1, C = arguments.length, $ = -1, b = s.length, w = y(b + C), k = this && this !== F1 && this instanceof h ? c : e; ++$ < b; )
            w[$] = s[$];
          for (; C--; )
            w[$++] = arguments[++_];
          return te(k, o ? r : this, w);
        }
        return h;
      }
      function c6(e) {
        return function(t, r, s) {
          return s && typeof s != "number" && Q1(t, r, s) && (r = s = i), t = Ze(t), r === i ? (r = t, t = 0) : r = Ze(r), s = s === i ? t < r ? 1 : -1 : Ze(s), w7(t, r, s, e);
        };
      }
      function qn(e) {
        return function(t, r) {
          return typeof t == "string" && typeof r == "string" || (t = _e(t), r = _e(r)), e(t, r);
        };
      }
      function u6(e, t, r, s, o, c, h, _, C, $) {
        var b = t & U, w = b ? h : i, k = b ? i : h, R = b ? c : i, Z = b ? i : c;
        t |= b ? $1 : R1, t &= ~(b ? R1 : $1), t & G || (t &= ~(n1 | i1));
        var X = [
          e,
          t,
          o,
          R,
          w,
          Z,
          k,
          _,
          C,
          $
        ], W = r.apply(i, X);
        return Br(e) && x6(W, X), W.placeholder = s, $6(W, e, t);
      }
      function Ir(e) {
        var t = k1[e];
        return function(r, s) {
          if (r = _e(r), s = s == null ? 0 : K1(Y(s), 292), s && $5(r)) {
            var o = (c1(r) + "e").split("e"), c = t(o[0] + "e" + (+o[1] + s));
            return o = (c1(c) + "e").split("e"), +(o[0] + "e" + (+o[1] - s));
          }
          return t(r);
        };
      }
      var U7 = Mt && 1 / An(new Mt([, -0]))[1] == oe ? function(e) {
        return new Mt(e);
      } : jr;
      function f6(e) {
        return function(t) {
          var r = U1(t);
          return r == O1 ? sr(t) : r == ye ? ii(t) : X8(t, e(t));
        };
      }
      function Fe(e, t, r, s, o, c, h, _) {
        var C = t & i1;
        if (!C && typeof e != "function")
          throw new ue(d);
        var $ = s ? s.length : 0;
        if ($ || (t &= ~($1 | R1), s = o = i), h = h === i ? h : E1(Y(h), 0), _ = _ === i ? _ : Y(_), $ -= o ? o.length : 0, t & R1) {
          var b = s, w = o;
          s = o = i;
        }
        var k = C ? i : Pr(e), R = [
          e,
          t,
          r,
          s,
          o,
          b,
          w,
          c,
          h,
          _
        ];
        if (k && na(R, k), e = R[0], t = R[1], r = R[2], s = R[3], o = R[4], _ = R[9] = R[9] === i ? C ? 0 : e.length : E1(R[9] - $, 0), !_ && t & (U | q) && (t &= ~(U | q)), !t || t == n1)
          var Z = F7(e, t, r);
        else
          t == U || t == q ? Z = N7(e, t, _) : (t == $1 || t == (n1 | $1)) && !o.length ? Z = K7(e, t, r, s) : Z = Yn.apply(i, R);
        var X = k ? Q5 : x6;
        return $6(X(Z, R), e, t);
      }
      function h6(e, t, r, s) {
        return e === i || xe(e, St[r]) && !f1.call(s, r) ? t : e;
      }
      function g6(e, t, r, s, o, c) {
        return b1(e) && b1(t) && (c.set(t, e), zn(e, t, i, g6, c), c.delete(t)), e;
      }
      function Z7(e) {
        return _n(e) ? i : e;
      }
      function p6(e, t, r, s, o, c) {
        var h = r & t1, _ = e.length, C = t.length;
        if (_ != C && !(h && C > _))
          return !1;
        var $ = c.get(e), b = c.get(t);
        if ($ && b)
          return $ == t && b == e;
        var w = -1, k = !0, R = r & p1 ? new lt() : i;
        for (c.set(e, t), c.set(t, e); ++w < _; ) {
          var Z = e[w], X = t[w];
          if (s)
            var W = h ? s(X, Z, w, t, e, c) : s(Z, X, w, e, t, c);
          if (W !== i) {
            if (W)
              continue;
            k = !1;
            break;
          }
          if (R) {
            if (!er(t, function(J, r1) {
              if (!en(R, r1) && (Z === J || o(Z, J, r, s, c)))
                return R.push(r1);
            })) {
              k = !1;
              break;
            }
          } else if (!(Z === X || o(Z, X, r, s, c))) {
            k = !1;
            break;
          }
        }
        return c.delete(e), c.delete(t), k;
      }
      function W7(e, t, r, s, o, c, h) {
        switch (r) {
          case Lt:
            if (e.byteLength != t.byteLength || e.byteOffset != t.byteOffset)
              return !1;
            e = e.buffer, t = t.buffer;
          case Jt:
            return !(e.byteLength != t.byteLength || !c(new En(e), new En(t)));
          case E:
          case N:
          case Vt:
            return xe(+e, +t);
          case B1:
            return e.name == t.name && e.message == t.message;
          case Xt:
          case qt:
            return e == t + "";
          case O1:
            var _ = sr;
          case ye:
            var C = s & t1;
            if (_ || (_ = An), e.size != t.size && !C)
              return !1;
            var $ = h.get(e);
            if ($)
              return $ == t;
            s |= p1, h.set(e, t);
            var b = p6(_(e), _(t), s, o, c, h);
            return h.delete(e), b;
          case mn:
            if (sn)
              return sn.call(e) == sn.call(t);
        }
        return !1;
      }
      function z7(e, t, r, s, o, c) {
        var h = r & t1, _ = kr(e), C = _.length, $ = kr(t), b = $.length;
        if (C != b && !h)
          return !1;
        for (var w = C; w--; ) {
          var k = _[w];
          if (!(h ? k in t : f1.call(t, k)))
            return !1;
        }
        var R = c.get(e), Z = c.get(t);
        if (R && Z)
          return R == t && Z == e;
        var X = !0;
        c.set(e, t), c.set(t, e);
        for (var W = h; ++w < C; ) {
          k = _[w];
          var J = e[k], r1 = t[k];
          if (s)
            var ae = h ? s(r1, J, k, t, e, c) : s(J, r1, k, e, t, c);
          if (!(ae === i ? J === r1 || o(J, r1, r, s, c) : ae)) {
            X = !1;
            break;
          }
          W || (W = k == "constructor");
        }
        if (X && !W) {
          var H1 = e.constructor, se = t.constructor;
          H1 != se && "constructor" in e && "constructor" in t && !(typeof H1 == "function" && H1 instanceof H1 && typeof se == "function" && se instanceof se) && (X = !1);
        }
        return c.delete(e), c.delete(t), X;
      }
      function Ne(e) {
        return Nr(m6(e, i, T6), e + "");
      }
      function kr(e) {
        return O5(e, D1, Dr);
      }
      function Er(e) {
        return O5(e, X1, _6);
      }
      var Pr = Fn ? function(e) {
        return Fn.get(e);
      } : jr;
      function jn(e) {
        for (var t = e.name + "", r = Tt[t], s = f1.call(Tt, t) ? r.length : 0; s--; ) {
          var o = r[s], c = o.func;
          if (c == null || c == e)
            return o.name;
        }
        return t;
      }
      function Pt(e) {
        var t = f1.call(l, "placeholder") ? l : e;
        return t.placeholder;
      }
      function K() {
        var e = l.iteratee || Xr;
        return e = e === Xr ? B5 : e, arguments.length ? e(arguments[0], arguments[1]) : e;
      }
      function Jn(e, t) {
        var r = e.__data__;
        return j7(t) ? r[typeof t == "string" ? "string" : "hash"] : r.map;
      }
      function Or(e) {
        for (var t = D1(e), r = t.length; r--; ) {
          var s = t[r], o = e[s];
          t[r] = [s, o, C6(o)];
        }
        return t;
      }
      function ft(e, t) {
        var r = ti(e, t);
        return R5(r) ? r : i;
      }
      function Q7(e) {
        var t = f1.call(e, st), r = e[st];
        try {
          e[st] = i;
          var s = !0;
        } catch {
        }
        var o = In.call(e);
        return s && (t ? e[st] = r : delete e[st]), o;
      }
      var Dr = lr ? function(e) {
        return e == null ? [] : (e = g1(e), Ge(lr(e), function(t) {
          return L5.call(e, t);
        }));
      } : Jr, _6 = lr ? function(e) {
        for (var t = []; e; )
          Ye(t, Dr(e)), e = Pn(e);
        return t;
      } : Jr, U1 = z1;
      (cr && U1(new cr(new ArrayBuffer(1))) != Lt || nn && U1(new nn()) != O1 || ur && U1(ur.resolve()) != k9 || Mt && U1(new Mt()) != ye || rn && U1(new rn()) != jt) && (U1 = function(e) {
        var t = z1(e), r = t == Oe ? e.constructor : i, s = r ? ht(r) : "";
        if (s)
          switch (s) {
            case Si:
              return Lt;
            case Mi:
              return O1;
            case Ti:
              return k9;
            case Ii:
              return ye;
            case ki:
              return jt;
          }
        return t;
      });
      function H7(e, t, r) {
        for (var s = -1, o = r.length; ++s < o; ) {
          var c = r[s], h = c.size;
          switch (c.type) {
            case "drop":
              e += h;
              break;
            case "dropRight":
              t -= h;
              break;
            case "take":
              t = K1(t, e + h);
              break;
            case "takeRight":
              e = E1(e, t - h);
              break;
          }
        }
        return { start: e, end: t };
      }
      function G7(e) {
        var t = e.match(J3);
        return t ? t[1].split(e8) : [];
      }
      function d6(e, t, r) {
        t = Je(t, e);
        for (var s = -1, o = t.length, c = !1; ++s < o; ) {
          var h = Te(t[s]);
          if (!(c = e != null && r(e, h)))
            break;
          e = e[h];
        }
        return c || ++s != o ? c : (o = e == null ? 0 : e.length, !!o && s0(o) && Ke(h, o) && (H(e) || gt(e)));
      }
      function Y7(e) {
        var t = e.length, r = new e.constructor(t);
        return t && typeof e[0] == "string" && f1.call(e, "index") && (r.index = e.index, r.input = e.input), r;
      }
      function v6(e) {
        return typeof e.constructor == "function" && !gn(e) ? It(Pn(e)) : {};
      }
      function V7(e, t, r) {
        var s = e.constructor;
        switch (t) {
          case Jt:
            return Mr(e);
          case E:
          case N:
            return new s(+e);
          case Lt:
            return E7(e, r);
          case O0:
          case D0:
          case R0:
          case B0:
          case F0:
          case N0:
          case K0:
          case U0:
          case Z0:
            return J5(e, r);
          case O1:
            return new s();
          case Vt:
          case qt:
            return new s(e);
          case Xt:
            return P7(e);
          case ye:
            return new s();
          case mn:
            return O7(e);
        }
      }
      function X7(e, t) {
        var r = t.length;
        if (!r)
          return e;
        var s = r - 1;
        return t[s] = (r > 1 ? "& " : "") + t[s], t = t.join(r > 2 ? ", " : " "), e.replace(j3, `{
/* [wrapped with ` + t + `] */
`);
      }
      function q7(e) {
        return H(e) || gt(e) || !!(x5 && e && e[x5]);
      }
      function Ke(e, t) {
        var r = typeof e;
        return t = t ?? J1, !!t && (r == "number" || r != "symbol" && c8.test(e)) && e > -1 && e % 1 == 0 && e < t;
      }
      function Q1(e, t, r) {
        if (!b1(r))
          return !1;
        var s = typeof t;
        return (s == "number" ? V1(r) && Ke(t, r.length) : s == "string" && t in r) ? xe(r[t], e) : !1;
      }
      function Rr(e, t) {
        if (H(e))
          return !1;
        var r = typeof e;
        return r == "number" || r == "symbol" || r == "boolean" || e == null || ie(e) ? !0 : Y3.test(e) || !G3.test(e) || t != null && e in g1(t);
      }
      function j7(e) {
        var t = typeof e;
        return t == "string" || t == "number" || t == "symbol" || t == "boolean" ? e !== "__proto__" : e === null;
      }
      function Br(e) {
        var t = jn(e), r = l[t];
        if (typeof r != "function" || !(t in e1.prototype))
          return !1;
        if (e === r)
          return !0;
        var s = Pr(r);
        return !!s && e === s[0];
      }
      function J7(e) {
        return !!C5 && C5 in e;
      }
      var ea = Mn ? Ue : e9;
      function gn(e) {
        var t = e && e.constructor, r = typeof t == "function" && t.prototype || St;
        return e === r;
      }
      function C6(e) {
        return e === e && !b1(e);
      }
      function y6(e, t) {
        return function(r) {
          return r == null ? !1 : r[e] === t && (t !== i || e in g1(r));
        };
      }
      function ta(e) {
        var t = i0(e, function(s) {
          return r.size === S && r.clear(), s;
        }), r = t.cache;
        return t;
      }
      function na(e, t) {
        var r = e[1], s = t[1], o = r | s, c = o < (n1 | i1 | M1), h = s == M1 && r == U || s == M1 && r == s1 && e[7].length <= t[8] || s == (M1 | s1) && t[7].length <= t[8] && r == U;
        if (!(c || h))
          return e;
        s & n1 && (e[2] = t[2], o |= r & n1 ? 0 : G);
        var _ = t[3];
        if (_) {
          var C = e[3];
          e[3] = C ? t6(C, _, t[4]) : _, e[4] = C ? Ve(e[3], x) : t[4];
        }
        return _ = t[5], _ && (C = e[5], e[5] = C ? n6(C, _, t[6]) : _, e[6] = C ? Ve(e[5], x) : t[6]), _ = t[7], _ && (e[7] = _), s & M1 && (e[8] = e[8] == null ? t[8] : K1(e[8], t[8])), e[9] == null && (e[9] = t[9]), e[0] = t[0], e[1] = o, e;
      }
      function ra(e) {
        var t = [];
        if (e != null)
          for (var r in g1(e))
            t.push(r);
        return t;
      }
      function ia(e) {
        return In.call(e);
      }
      function m6(e, t, r) {
        return t = E1(t === i ? e.length - 1 : t, 0), function() {
          for (var s = arguments, o = -1, c = E1(s.length - t, 0), h = y(c); ++o < c; )
            h[o] = s[t + o];
          o = -1;
          for (var _ = y(t + 1); ++o < t; )
            _[o] = s[o];
          return _[t] = r(h), te(e, this, _);
        };
      }
      function L6(e, t) {
        return t.length < 2 ? e : ut(e, ge(t, 0, -1));
      }
      function aa(e, t) {
        for (var r = e.length, s = K1(t.length, r), o = Y1(e); s--; ) {
          var c = t[s];
          e[s] = Ke(c, r) ? o[c] : i;
        }
        return e;
      }
      function Fr(e, t) {
        if (!(t === "constructor" && typeof e[t] == "function") && t != "__proto__")
          return e[t];
      }
      var x6 = b6(Q5), pn = mi || function(e, t) {
        return F1.setTimeout(e, t);
      }, Nr = b6(M7);
      function $6(e, t, r) {
        var s = t + "";
        return Nr(e, X7(s, sa(G7(s), r)));
      }
      function b6(e) {
        var t = 0, r = 0;
        return function() {
          var s = bi(), o = Yt - (s - r);
          if (r = s, o > 0) {
            if (++t >= Gt)
              return arguments[0];
          } else
            t = 0;
          return e.apply(i, arguments);
        };
      }
      function e0(e, t) {
        var r = -1, s = e.length, o = s - 1;
        for (t = t === i ? s : t; ++r < t; ) {
          var c = Lr(r, o), h = e[c];
          e[c] = e[r], e[r] = h;
        }
        return e.length = t, e;
      }
      var w6 = ta(function(e) {
        var t = [];
        return e.charCodeAt(0) === 46 && t.push(""), e.replace(V3, function(r, s, o, c) {
          t.push(o ? c.replace(r8, "$1") : s || r);
        }), t;
      });
      function Te(e) {
        if (typeof e == "string" || ie(e))
          return e;
        var t = e + "";
        return t == "0" && 1 / e == -oe ? "-0" : t;
      }
      function ht(e) {
        if (e != null) {
          try {
            return Tn.call(e);
          } catch {
          }
          try {
            return e + "";
          } catch {
          }
        }
        return "";
      }
      function sa(e, t) {
        return ce(it, function(r) {
          var s = "_." + r[0];
          t & r[1] && !bn(e, s) && e.push(s);
        }), e.sort();
      }
      function A6(e) {
        if (e instanceof e1)
          return e.clone();
        var t = new fe(e.__wrapped__, e.__chain__);
        return t.__actions__ = Y1(e.__actions__), t.__index__ = e.__index__, t.__values__ = e.__values__, t;
      }
      function oa(e, t, r) {
        (r ? Q1(e, t, r) : t === i) ? t = 1 : t = E1(Y(t), 0);
        var s = e == null ? 0 : e.length;
        if (!s || t < 1)
          return [];
        for (var o = 0, c = 0, h = y(Rn(s / t)); o < s; )
          h[c++] = ge(e, o, o += t);
        return h;
      }
      function la(e) {
        for (var t = -1, r = e == null ? 0 : e.length, s = 0, o = []; ++t < r; ) {
          var c = e[t];
          c && (o[s++] = c);
        }
        return o;
      }
      function ca() {
        var e = arguments.length;
        if (!e)
          return [];
        for (var t = y(e - 1), r = arguments[0], s = e; s--; )
          t[s - 1] = arguments[s];
        return Ye(H(r) ? Y1(r) : [r], N1(t, 1));
      }
      var ua = j(function(e, t) {
        return T1(e) ? ln(e, N1(t, 1, T1, !0)) : [];
      }), fa = j(function(e, t) {
        var r = pe(t);
        return T1(r) && (r = i), T1(e) ? ln(e, N1(t, 1, T1, !0), K(r, 2)) : [];
      }), ha = j(function(e, t) {
        var r = pe(t);
        return T1(r) && (r = i), T1(e) ? ln(e, N1(t, 1, T1, !0), i, r) : [];
      });
      function ga(e, t, r) {
        var s = e == null ? 0 : e.length;
        return s ? (t = r || t === i ? 1 : Y(t), ge(e, t < 0 ? 0 : t, s)) : [];
      }
      function pa(e, t, r) {
        var s = e == null ? 0 : e.length;
        return s ? (t = r || t === i ? 1 : Y(t), t = s - t, ge(e, 0, t < 0 ? 0 : t)) : [];
      }
      function _a(e, t) {
        return e && e.length ? Hn(e, K(t, 3), !0, !0) : [];
      }
      function da(e, t) {
        return e && e.length ? Hn(e, K(t, 3), !0) : [];
      }
      function va(e, t, r, s) {
        var o = e == null ? 0 : e.length;
        return o ? (r && typeof r != "number" && Q1(e, t, r) && (r = 0, s = o), c7(e, t, r, s)) : [];
      }
      function S6(e, t, r) {
        var s = e == null ? 0 : e.length;
        if (!s)
          return -1;
        var o = r == null ? 0 : Y(r);
        return o < 0 && (o = E1(s + o, 0)), wn(e, K(t, 3), o);
      }
      function M6(e, t, r) {
        var s = e == null ? 0 : e.length;
        if (!s)
          return -1;
        var o = s - 1;
        return r !== i && (o = Y(r), o = r < 0 ? E1(s + o, 0) : K1(o, s - 1)), wn(e, K(t, 3), o, !0);
      }
      function T6(e) {
        var t = e == null ? 0 : e.length;
        return t ? N1(e, 1) : [];
      }
      function Ca(e) {
        var t = e == null ? 0 : e.length;
        return t ? N1(e, oe) : [];
      }
      function ya(e, t) {
        var r = e == null ? 0 : e.length;
        return r ? (t = t === i ? 1 : Y(t), N1(e, t)) : [];
      }
      function ma(e) {
        for (var t = -1, r = e == null ? 0 : e.length, s = {}; ++t < r; ) {
          var o = e[t];
          s[o[0]] = o[1];
        }
        return s;
      }
      function I6(e) {
        return e && e.length ? e[0] : i;
      }
      function La(e, t, r) {
        var s = e == null ? 0 : e.length;
        if (!s)
          return -1;
        var o = r == null ? 0 : Y(r);
        return o < 0 && (o = E1(s + o, 0)), $t(e, t, o);
      }
      function xa(e) {
        var t = e == null ? 0 : e.length;
        return t ? ge(e, 0, -1) : [];
      }
      var $a = j(function(e) {
        var t = L1(e, Ar);
        return t.length && t[0] === e[0] ? dr(t) : [];
      }), ba = j(function(e) {
        var t = pe(e), r = L1(e, Ar);
        return t === pe(r) ? t = i : r.pop(), r.length && r[0] === e[0] ? dr(r, K(t, 2)) : [];
      }), wa = j(function(e) {
        var t = pe(e), r = L1(e, Ar);
        return t = typeof t == "function" ? t : i, t && r.pop(), r.length && r[0] === e[0] ? dr(r, i, t) : [];
      });
      function Aa(e, t) {
        return e == null ? "" : xi.call(e, t);
      }
      function pe(e) {
        var t = e == null ? 0 : e.length;
        return t ? e[t - 1] : i;
      }
      function Sa(e, t, r) {
        var s = e == null ? 0 : e.length;
        if (!s)
          return -1;
        var o = s;
        return r !== i && (o = Y(r), o = o < 0 ? E1(s + o, 0) : K1(o, s - 1)), t === t ? si(e, t, o) : wn(e, u5, o, !0);
      }
      function Ma(e, t) {
        return e && e.length ? U5(e, Y(t)) : i;
      }
      var Ta = j(k6);
      function k6(e, t) {
        return e && e.length && t && t.length ? mr(e, t) : e;
      }
      function Ia(e, t, r) {
        return e && e.length && t && t.length ? mr(e, t, K(r, 2)) : e;
      }
      function ka(e, t, r) {
        return e && e.length && t && t.length ? mr(e, t, i, r) : e;
      }
      var Ea = Ne(function(e, t) {
        var r = e == null ? 0 : e.length, s = hr(e, t);
        return z5(e, L1(t, function(o) {
          return Ke(o, r) ? +o : o;
        }).sort(e6)), s;
      });
      function Pa(e, t) {
        var r = [];
        if (!(e && e.length))
          return r;
        var s = -1, o = [], c = e.length;
        for (t = K(t, 3); ++s < c; ) {
          var h = e[s];
          t(h, s, e) && (r.push(h), o.push(s));
        }
        return z5(e, o), r;
      }
      function Kr(e) {
        return e == null ? e : Ai.call(e);
      }
      function Oa(e, t, r) {
        var s = e == null ? 0 : e.length;
        return s ? (r && typeof r != "number" && Q1(e, t, r) ? (t = 0, r = s) : (t = t == null ? 0 : Y(t), r = r === i ? s : Y(r)), ge(e, t, r)) : [];
      }
      function Da(e, t) {
        return Qn(e, t);
      }
      function Ra(e, t, r) {
        return $r(e, t, K(r, 2));
      }
      function Ba(e, t) {
        var r = e == null ? 0 : e.length;
        if (r) {
          var s = Qn(e, t);
          if (s < r && xe(e[s], t))
            return s;
        }
        return -1;
      }
      function Fa(e, t) {
        return Qn(e, t, !0);
      }
      function Na(e, t, r) {
        return $r(e, t, K(r, 2), !0);
      }
      function Ka(e, t) {
        var r = e == null ? 0 : e.length;
        if (r) {
          var s = Qn(e, t, !0) - 1;
          if (xe(e[s], t))
            return s;
        }
        return -1;
      }
      function Ua(e) {
        return e && e.length ? H5(e) : [];
      }
      function Za(e, t) {
        return e && e.length ? H5(e, K(t, 2)) : [];
      }
      function Wa(e) {
        var t = e == null ? 0 : e.length;
        return t ? ge(e, 1, t) : [];
      }
      function za(e, t, r) {
        return e && e.length ? (t = r || t === i ? 1 : Y(t), ge(e, 0, t < 0 ? 0 : t)) : [];
      }
      function Qa(e, t, r) {
        var s = e == null ? 0 : e.length;
        return s ? (t = r || t === i ? 1 : Y(t), t = s - t, ge(e, t < 0 ? 0 : t, s)) : [];
      }
      function Ha(e, t) {
        return e && e.length ? Hn(e, K(t, 3), !1, !0) : [];
      }
      function Ga(e, t) {
        return e && e.length ? Hn(e, K(t, 3)) : [];
      }
      var Ya = j(function(e) {
        return je(N1(e, 1, T1, !0));
      }), Va = j(function(e) {
        var t = pe(e);
        return T1(t) && (t = i), je(N1(e, 1, T1, !0), K(t, 2));
      }), Xa = j(function(e) {
        var t = pe(e);
        return t = typeof t == "function" ? t : i, je(N1(e, 1, T1, !0), i, t);
      });
      function qa(e) {
        return e && e.length ? je(e) : [];
      }
      function ja(e, t) {
        return e && e.length ? je(e, K(t, 2)) : [];
      }
      function Ja(e, t) {
        return t = typeof t == "function" ? t : i, e && e.length ? je(e, i, t) : [];
      }
      function Ur(e) {
        if (!(e && e.length))
          return [];
        var t = 0;
        return e = Ge(e, function(r) {
          if (T1(r))
            return t = E1(r.length, t), !0;
        }), ir(t, function(r) {
          return L1(e, tr(r));
        });
      }
      function E6(e, t) {
        if (!(e && e.length))
          return [];
        var r = Ur(e);
        return t == null ? r : L1(r, function(s) {
          return te(t, i, s);
        });
      }
      var e4 = j(function(e, t) {
        return T1(e) ? ln(e, t) : [];
      }), t4 = j(function(e) {
        return wr(Ge(e, T1));
      }), n4 = j(function(e) {
        var t = pe(e);
        return T1(t) && (t = i), wr(Ge(e, T1), K(t, 2));
      }), r4 = j(function(e) {
        var t = pe(e);
        return t = typeof t == "function" ? t : i, wr(Ge(e, T1), i, t);
      }), i4 = j(Ur);
      function a4(e, t) {
        return X5(e || [], t || [], on);
      }
      function s4(e, t) {
        return X5(e || [], t || [], fn);
      }
      var o4 = j(function(e) {
        var t = e.length, r = t > 1 ? e[t - 1] : i;
        return r = typeof r == "function" ? (e.pop(), r) : i, E6(e, r);
      });
      function P6(e) {
        var t = l(e);
        return t.__chain__ = !0, t;
      }
      function l4(e, t) {
        return t(e), e;
      }
      function t0(e, t) {
        return t(e);
      }
      var c4 = Ne(function(e) {
        var t = e.length, r = t ? e[0] : 0, s = this.__wrapped__, o = function(c) {
          return hr(c, e);
        };
        return t > 1 || this.__actions__.length || !(s instanceof e1) || !Ke(r) ? this.thru(o) : (s = s.slice(r, +r + (t ? 1 : 0)), s.__actions__.push({
          func: t0,
          args: [o],
          thisArg: i
        }), new fe(s, this.__chain__).thru(function(c) {
          return t && !c.length && c.push(i), c;
        }));
      });
      function u4() {
        return P6(this);
      }
      function f4() {
        return new fe(this.value(), this.__chain__);
      }
      function h4() {
        this.__values__ === i && (this.__values__ = G6(this.value()));
        var e = this.__index__ >= this.__values__.length, t = e ? i : this.__values__[this.__index__++];
        return { done: e, value: t };
      }
      function g4() {
        return this;
      }
      function p4(e) {
        for (var t, r = this; r instanceof Kn; ) {
          var s = A6(r);
          s.__index__ = 0, s.__values__ = i, t ? o.__wrapped__ = s : t = s;
          var o = s;
          r = r.__wrapped__;
        }
        return o.__wrapped__ = e, t;
      }
      function _4() {
        var e = this.__wrapped__;
        if (e instanceof e1) {
          var t = e;
          return this.__actions__.length && (t = new e1(this)), t = t.reverse(), t.__actions__.push({
            func: t0,
            args: [Kr],
            thisArg: i
          }), new fe(t, this.__chain__);
        }
        return this.thru(Kr);
      }
      function d4() {
        return V5(this.__wrapped__, this.__actions__);
      }
      var v4 = Gn(function(e, t, r) {
        f1.call(e, r) ? ++e[r] : Be(e, r, 1);
      });
      function C4(e, t, r) {
        var s = H(e) ? l5 : l7;
        return r && Q1(e, t, r) && (t = i), s(e, K(t, 3));
      }
      function y4(e, t) {
        var r = H(e) ? Ge : E5;
        return r(e, K(t, 3));
      }
      var m4 = s6(S6), L4 = s6(M6);
      function x4(e, t) {
        return N1(n0(e, t), 1);
      }
      function $4(e, t) {
        return N1(n0(e, t), oe);
      }
      function b4(e, t, r) {
        return r = r === i ? 1 : Y(r), N1(n0(e, t), r);
      }
      function O6(e, t) {
        var r = H(e) ? ce : qe;
        return r(e, K(t, 3));
      }
      function D6(e, t) {
        var r = H(e) ? W8 : k5;
        return r(e, K(t, 3));
      }
      var w4 = Gn(function(e, t, r) {
        f1.call(e, r) ? e[r].push(t) : Be(e, r, [t]);
      });
      function A4(e, t, r, s) {
        e = V1(e) ? e : Dt(e), r = r && !s ? Y(r) : 0;
        var o = e.length;
        return r < 0 && (r = E1(o + r, 0)), o0(e) ? r <= o && e.indexOf(t, r) > -1 : !!o && $t(e, t, r) > -1;
      }
      var S4 = j(function(e, t, r) {
        var s = -1, o = typeof t == "function", c = V1(e) ? y(e.length) : [];
        return qe(e, function(h) {
          c[++s] = o ? te(t, h, r) : cn(h, t, r);
        }), c;
      }), M4 = Gn(function(e, t, r) {
        Be(e, r, t);
      });
      function n0(e, t) {
        var r = H(e) ? L1 : F5;
        return r(e, K(t, 3));
      }
      function T4(e, t, r, s) {
        return e == null ? [] : (H(t) || (t = t == null ? [] : [t]), r = s ? i : r, H(r) || (r = r == null ? [] : [r]), Z5(e, t, r));
      }
      var I4 = Gn(function(e, t, r) {
        e[r ? 0 : 1].push(t);
      }, function() {
        return [[], []];
      });
      function k4(e, t, r) {
        var s = H(e) ? J0 : h5, o = arguments.length < 3;
        return s(e, K(t, 4), r, o, qe);
      }
      function E4(e, t, r) {
        var s = H(e) ? z8 : h5, o = arguments.length < 3;
        return s(e, K(t, 4), r, o, k5);
      }
      function P4(e, t) {
        var r = H(e) ? Ge : E5;
        return r(e, a0(K(t, 3)));
      }
      function O4(e) {
        var t = H(e) ? S5 : A7;
        return t(e);
      }
      function D4(e, t, r) {
        (r ? Q1(e, t, r) : t === i) ? t = 1 : t = Y(t);
        var s = H(e) ? r7 : S7;
        return s(e, t);
      }
      function R4(e) {
        var t = H(e) ? i7 : T7;
        return t(e);
      }
      function B4(e) {
        if (e == null)
          return 0;
        if (V1(e))
          return o0(e) ? wt(e) : e.length;
        var t = U1(e);
        return t == O1 || t == ye ? e.size : Cr(e).length;
      }
      function F4(e, t, r) {
        var s = H(e) ? er : I7;
        return r && Q1(e, t, r) && (t = i), s(e, K(t, 3));
      }
      var N4 = j(function(e, t) {
        if (e == null)
          return [];
        var r = t.length;
        return r > 1 && Q1(e, t[0], t[1]) ? t = [] : r > 2 && Q1(t[0], t[1], t[2]) && (t = [t[0]]), Z5(e, N1(t, 1), []);
      }), r0 = yi || function() {
        return F1.Date.now();
      };
      function K4(e, t) {
        if (typeof t != "function")
          throw new ue(d);
        return e = Y(e), function() {
          if (--e < 1)
            return t.apply(this, arguments);
        };
      }
      function R6(e, t, r) {
        return t = r ? i : t, t = e && t == null ? e.length : t, Fe(e, M1, i, i, i, i, t);
      }
      function B6(e, t) {
        var r;
        if (typeof t != "function")
          throw new ue(d);
        return e = Y(e), function() {
          return --e > 0 && (r = t.apply(this, arguments)), e <= 1 && (t = i), r;
        };
      }
      var Zr = j(function(e, t, r) {
        var s = n1;
        if (r.length) {
          var o = Ve(r, Pt(Zr));
          s |= $1;
        }
        return Fe(e, s, t, r, o);
      }), F6 = j(function(e, t, r) {
        var s = n1 | i1;
        if (r.length) {
          var o = Ve(r, Pt(F6));
          s |= $1;
        }
        return Fe(t, s, e, r, o);
      });
      function N6(e, t, r) {
        t = r ? i : t;
        var s = Fe(e, U, i, i, i, i, i, t);
        return s.placeholder = N6.placeholder, s;
      }
      function K6(e, t, r) {
        t = r ? i : t;
        var s = Fe(e, q, i, i, i, i, i, t);
        return s.placeholder = K6.placeholder, s;
      }
      function U6(e, t, r) {
        var s, o, c, h, _, C, $ = 0, b = !1, w = !1, k = !0;
        if (typeof e != "function")
          throw new ue(d);
        t = _e(t) || 0, b1(r) && (b = !!r.leading, w = "maxWait" in r, c = w ? E1(_e(r.maxWait) || 0, t) : c, k = "trailing" in r ? !!r.trailing : k);
        function R(I1) {
          var $e = s, We = o;
          return s = o = i, $ = I1, h = e.apply(We, $e), h;
        }
        function Z(I1) {
          return $ = I1, _ = pn(J, t), b ? R(I1) : h;
        }
        function X(I1) {
          var $e = I1 - C, We = I1 - $, s2 = t - $e;
          return w ? K1(s2, c - We) : s2;
        }
        function W(I1) {
          var $e = I1 - C, We = I1 - $;
          return C === i || $e >= t || $e < 0 || w && We >= c;
        }
        function J() {
          var I1 = r0();
          if (W(I1))
            return r1(I1);
          _ = pn(J, X(I1));
        }
        function r1(I1) {
          return _ = i, k && s ? R(I1) : (s = o = i, h);
        }
        function ae() {
          _ !== i && q5(_), $ = 0, s = C = o = _ = i;
        }
        function H1() {
          return _ === i ? h : r1(r0());
        }
        function se() {
          var I1 = r0(), $e = W(I1);
          if (s = arguments, o = this, C = I1, $e) {
            if (_ === i)
              return Z(C);
            if (w)
              return q5(_), _ = pn(J, t), R(C);
          }
          return _ === i && (_ = pn(J, t)), h;
        }
        return se.cancel = ae, se.flush = H1, se;
      }
      var U4 = j(function(e, t) {
        return I5(e, 1, t);
      }), Z4 = j(function(e, t, r) {
        return I5(e, _e(t) || 0, r);
      });
      function W4(e) {
        return Fe(e, l1);
      }
      function i0(e, t) {
        if (typeof e != "function" || t != null && typeof t != "function")
          throw new ue(d);
        var r = function() {
          var s = arguments, o = t ? t.apply(this, s) : s[0], c = r.cache;
          if (c.has(o))
            return c.get(o);
          var h = e.apply(this, s);
          return r.cache = c.set(o, h) || c, h;
        };
        return r.cache = new (i0.Cache || Re)(), r;
      }
      i0.Cache = Re;
      function a0(e) {
        if (typeof e != "function")
          throw new ue(d);
        return function() {
          var t = arguments;
          switch (t.length) {
            case 0:
              return !e.call(this);
            case 1:
              return !e.call(this, t[0]);
            case 2:
              return !e.call(this, t[0], t[1]);
            case 3:
              return !e.call(this, t[0], t[1], t[2]);
          }
          return !e.apply(this, t);
        };
      }
      function z4(e) {
        return B6(2, e);
      }
      var Q4 = k7(function(e, t) {
        t = t.length == 1 && H(t[0]) ? L1(t[0], ne(K())) : L1(N1(t, 1), ne(K()));
        var r = t.length;
        return j(function(s) {
          for (var o = -1, c = K1(s.length, r); ++o < c; )
            s[o] = t[o].call(this, s[o]);
          return te(e, this, s);
        });
      }), Wr = j(function(e, t) {
        var r = Ve(t, Pt(Wr));
        return Fe(e, $1, i, t, r);
      }), Z6 = j(function(e, t) {
        var r = Ve(t, Pt(Z6));
        return Fe(e, R1, i, t, r);
      }), H4 = Ne(function(e, t) {
        return Fe(e, s1, i, i, i, t);
      });
      function G4(e, t) {
        if (typeof e != "function")
          throw new ue(d);
        return t = t === i ? t : Y(t), j(e, t);
      }
      function Y4(e, t) {
        if (typeof e != "function")
          throw new ue(d);
        return t = t == null ? 0 : E1(Y(t), 0), j(function(r) {
          var s = r[t], o = et(r, 0, t);
          return s && Ye(o, s), te(e, this, o);
        });
      }
      function V4(e, t, r) {
        var s = !0, o = !0;
        if (typeof e != "function")
          throw new ue(d);
        return b1(r) && (s = "leading" in r ? !!r.leading : s, o = "trailing" in r ? !!r.trailing : o), U6(e, t, {
          leading: s,
          maxWait: t,
          trailing: o
        });
      }
      function X4(e) {
        return R6(e, 1);
      }
      function q4(e, t) {
        return Wr(Sr(t), e);
      }
      function j4() {
        if (!arguments.length)
          return [];
        var e = arguments[0];
        return H(e) ? e : [e];
      }
      function J4(e) {
        return he(e, z);
      }
      function es(e, t) {
        return t = typeof t == "function" ? t : i, he(e, z, t);
      }
      function ts(e) {
        return he(e, M | z);
      }
      function ns(e, t) {
        return t = typeof t == "function" ? t : i, he(e, M | z, t);
      }
      function rs(e, t) {
        return t == null || T5(e, t, D1(t));
      }
      function xe(e, t) {
        return e === t || e !== e && t !== t;
      }
      var is = qn(_r), as = qn(function(e, t) {
        return e >= t;
      }), gt = D5(function() {
        return arguments;
      }()) ? D5 : function(e) {
        return w1(e) && f1.call(e, "callee") && !L5.call(e, "callee");
      }, H = y.isArray, ss = n5 ? ne(n5) : p7;
      function V1(e) {
        return e != null && s0(e.length) && !Ue(e);
      }
      function T1(e) {
        return w1(e) && V1(e);
      }
      function os(e) {
        return e === !0 || e === !1 || w1(e) && z1(e) == E;
      }
      var tt = Li || e9, ls = r5 ? ne(r5) : _7;
      function cs(e) {
        return w1(e) && e.nodeType === 1 && !_n(e);
      }
      function us(e) {
        if (e == null)
          return !0;
        if (V1(e) && (H(e) || typeof e == "string" || typeof e.splice == "function" || tt(e) || Ot(e) || gt(e)))
          return !e.length;
        var t = U1(e);
        if (t == O1 || t == ye)
          return !e.size;
        if (gn(e))
          return !Cr(e).length;
        for (var r in e)
          if (f1.call(e, r))
            return !1;
        return !0;
      }
      function fs(e, t) {
        return un(e, t);
      }
      function hs(e, t, r) {
        r = typeof r == "function" ? r : i;
        var s = r ? r(e, t) : i;
        return s === i ? un(e, t, i, r) : !!s;
      }
      function zr(e) {
        if (!w1(e))
          return !1;
        var t = z1(e);
        return t == B1 || t == m1 || typeof e.message == "string" && typeof e.name == "string" && !_n(e);
      }
      function gs(e) {
        return typeof e == "number" && $5(e);
      }
      function Ue(e) {
        if (!b1(e))
          return !1;
        var t = z1(e);
        return t == G1 || t == Ae || t == A || t == B3;
      }
      function W6(e) {
        return typeof e == "number" && e == Y(e);
      }
      function s0(e) {
        return typeof e == "number" && e > -1 && e % 1 == 0 && e <= J1;
      }
      function b1(e) {
        var t = typeof e;
        return e != null && (t == "object" || t == "function");
      }
      function w1(e) {
        return e != null && typeof e == "object";
      }
      var z6 = i5 ? ne(i5) : v7;
      function ps(e, t) {
        return e === t || vr(e, t, Or(t));
      }
      function _s(e, t, r) {
        return r = typeof r == "function" ? r : i, vr(e, t, Or(t), r);
      }
      function ds(e) {
        return Q6(e) && e != +e;
      }
      function vs(e) {
        if (ea(e))
          throw new Q(g);
        return R5(e);
      }
      function Cs(e) {
        return e === null;
      }
      function ys(e) {
        return e == null;
      }
      function Q6(e) {
        return typeof e == "number" || w1(e) && z1(e) == Vt;
      }
      function _n(e) {
        if (!w1(e) || z1(e) != Oe)
          return !1;
        var t = Pn(e);
        if (t === null)
          return !0;
        var r = f1.call(t, "constructor") && t.constructor;
        return typeof r == "function" && r instanceof r && Tn.call(r) == _i;
      }
      var Qr = a5 ? ne(a5) : C7;
      function ms(e) {
        return W6(e) && e >= -J1 && e <= J1;
      }
      var H6 = s5 ? ne(s5) : y7;
      function o0(e) {
        return typeof e == "string" || !H(e) && w1(e) && z1(e) == qt;
      }
      function ie(e) {
        return typeof e == "symbol" || w1(e) && z1(e) == mn;
      }
      var Ot = o5 ? ne(o5) : m7;
      function Ls(e) {
        return e === i;
      }
      function xs(e) {
        return w1(e) && U1(e) == jt;
      }
      function $s(e) {
        return w1(e) && z1(e) == N3;
      }
      var bs = qn(yr), ws = qn(function(e, t) {
        return e <= t;
      });
      function G6(e) {
        if (!e)
          return [];
        if (V1(e))
          return o0(e) ? me(e) : Y1(e);
        if (tn && e[tn])
          return ri(e[tn]());
        var t = U1(e), r = t == O1 ? sr : t == ye ? An : Dt;
        return r(e);
      }
      function Ze(e) {
        if (!e)
          return e === 0 ? e : 0;
        if (e = _e(e), e === oe || e === -oe) {
          var t = e < 0 ? -1 : 1;
          return t * mt;
        }
        return e === e ? e : 0;
      }
      function Y(e) {
        var t = Ze(e), r = t % 1;
        return t === t ? r ? t - r : t : 0;
      }
      function Y6(e) {
        return e ? ct(Y(e), 0, u1) : 0;
      }
      function _e(e) {
        if (typeof e == "number")
          return e;
        if (ie(e))
          return a1;
        if (b1(e)) {
          var t = typeof e.valueOf == "function" ? e.valueOf() : e;
          e = b1(t) ? t + "" : t;
        }
        if (typeof e != "string")
          return e === 0 ? e : +e;
        e = g5(e);
        var r = s8.test(e);
        return r || l8.test(e) ? K8(e.slice(2), r ? 2 : 8) : a8.test(e) ? a1 : +e;
      }
      function V6(e) {
        return Me(e, X1(e));
      }
      function As(e) {
        return e ? ct(Y(e), -J1, J1) : e === 0 ? e : 0;
      }
      function c1(e) {
        return e == null ? "" : re(e);
      }
      var Ss = kt(function(e, t) {
        if (gn(t) || V1(t)) {
          Me(t, D1(t), e);
          return;
        }
        for (var r in t)
          f1.call(t, r) && on(e, r, t[r]);
      }), X6 = kt(function(e, t) {
        Me(t, X1(t), e);
      }), l0 = kt(function(e, t, r, s) {
        Me(t, X1(t), e, s);
      }), Ms = kt(function(e, t, r, s) {
        Me(t, D1(t), e, s);
      }), Ts = Ne(hr);
      function Is(e, t) {
        var r = It(e);
        return t == null ? r : M5(r, t);
      }
      var ks = j(function(e, t) {
        e = g1(e);
        var r = -1, s = t.length, o = s > 2 ? t[2] : i;
        for (o && Q1(t[0], t[1], o) && (s = 1); ++r < s; )
          for (var c = t[r], h = X1(c), _ = -1, C = h.length; ++_ < C; ) {
            var $ = h[_], b = e[$];
            (b === i || xe(b, St[$]) && !f1.call(e, $)) && (e[$] = c[$]);
          }
        return e;
      }), Es = j(function(e) {
        return e.push(i, g6), te(q6, i, e);
      });
      function Ps(e, t) {
        return c5(e, K(t, 3), Se);
      }
      function Os(e, t) {
        return c5(e, K(t, 3), pr);
      }
      function Ds(e, t) {
        return e == null ? e : gr(e, K(t, 3), X1);
      }
      function Rs(e, t) {
        return e == null ? e : P5(e, K(t, 3), X1);
      }
      function Bs(e, t) {
        return e && Se(e, K(t, 3));
      }
      function Fs(e, t) {
        return e && pr(e, K(t, 3));
      }
      function Ns(e) {
        return e == null ? [] : Wn(e, D1(e));
      }
      function Ks(e) {
        return e == null ? [] : Wn(e, X1(e));
      }
      function Hr(e, t, r) {
        var s = e == null ? i : ut(e, t);
        return s === i ? r : s;
      }
      function Us(e, t) {
        return e != null && d6(e, t, u7);
      }
      function Gr(e, t) {
        return e != null && d6(e, t, f7);
      }
      var Zs = l6(function(e, t, r) {
        t != null && typeof t.toString != "function" && (t = In.call(t)), e[t] = r;
      }, Vr(q1)), Ws = l6(function(e, t, r) {
        t != null && typeof t.toString != "function" && (t = In.call(t)), f1.call(e, t) ? e[t].push(r) : e[t] = [r];
      }, K), zs = j(cn);
      function D1(e) {
        return V1(e) ? A5(e) : Cr(e);
      }
      function X1(e) {
        return V1(e) ? A5(e, !0) : L7(e);
      }
      function Qs(e, t) {
        var r = {};
        return t = K(t, 3), Se(e, function(s, o, c) {
          Be(r, t(s, o, c), s);
        }), r;
      }
      function Hs(e, t) {
        var r = {};
        return t = K(t, 3), Se(e, function(s, o, c) {
          Be(r, o, t(s, o, c));
        }), r;
      }
      var Gs = kt(function(e, t, r) {
        zn(e, t, r);
      }), q6 = kt(function(e, t, r, s) {
        zn(e, t, r, s);
      }), Ys = Ne(function(e, t) {
        var r = {};
        if (e == null)
          return r;
        var s = !1;
        t = L1(t, function(c) {
          return c = Je(c, e), s || (s = c.length > 1), c;
        }), Me(e, Er(e), r), s && (r = he(r, M | D | z, Z7));
        for (var o = t.length; o--; )
          br(r, t[o]);
        return r;
      });
      function Vs(e, t) {
        return j6(e, a0(K(t)));
      }
      var Xs = Ne(function(e, t) {
        return e == null ? {} : $7(e, t);
      });
      function j6(e, t) {
        if (e == null)
          return {};
        var r = L1(Er(e), function(s) {
          return [s];
        });
        return t = K(t), W5(e, r, function(s, o) {
          return t(s, o[0]);
        });
      }
      function qs(e, t, r) {
        t = Je(t, e);
        var s = -1, o = t.length;
        for (o || (o = 1, e = i); ++s < o; ) {
          var c = e == null ? i : e[Te(t[s])];
          c === i && (s = o, c = r), e = Ue(c) ? c.call(e) : c;
        }
        return e;
      }
      function js(e, t, r) {
        return e == null ? e : fn(e, t, r);
      }
      function Js(e, t, r, s) {
        return s = typeof s == "function" ? s : i, e == null ? e : fn(e, t, r, s);
      }
      var J6 = f6(D1), e2 = f6(X1);
      function eo(e, t, r) {
        var s = H(e), o = s || tt(e) || Ot(e);
        if (t = K(t, 4), r == null) {
          var c = e && e.constructor;
          o ? r = s ? new c() : [] : b1(e) ? r = Ue(c) ? It(Pn(e)) : {} : r = {};
        }
        return (o ? ce : Se)(e, function(h, _, C) {
          return t(r, h, _, C);
        }), r;
      }
      function to(e, t) {
        return e == null ? !0 : br(e, t);
      }
      function no(e, t, r) {
        return e == null ? e : Y5(e, t, Sr(r));
      }
      function ro(e, t, r, s) {
        return s = typeof s == "function" ? s : i, e == null ? e : Y5(e, t, Sr(r), s);
      }
      function Dt(e) {
        return e == null ? [] : ar(e, D1(e));
      }
      function io(e) {
        return e == null ? [] : ar(e, X1(e));
      }
      function ao(e, t, r) {
        return r === i && (r = t, t = i), r !== i && (r = _e(r), r = r === r ? r : 0), t !== i && (t = _e(t), t = t === t ? t : 0), ct(_e(e), t, r);
      }
      function so(e, t, r) {
        return t = Ze(t), r === i ? (r = t, t = 0) : r = Ze(r), e = _e(e), h7(e, t, r);
      }
      function oo(e, t, r) {
        if (r && typeof r != "boolean" && Q1(e, t, r) && (t = r = i), r === i && (typeof t == "boolean" ? (r = t, t = i) : typeof e == "boolean" && (r = e, e = i)), e === i && t === i ? (e = 0, t = 1) : (e = Ze(e), t === i ? (t = e, e = 0) : t = Ze(t)), e > t) {
          var s = e;
          e = t, t = s;
        }
        if (r || e % 1 || t % 1) {
          var o = b5();
          return K1(e + o * (t - e + N8("1e-" + ((o + "").length - 1))), t);
        }
        return Lr(e, t);
      }
      var lo = Et(function(e, t, r) {
        return t = t.toLowerCase(), e + (r ? t2(t) : t);
      });
      function t2(e) {
        return Yr(c1(e).toLowerCase());
      }
      function n2(e) {
        return e = c1(e), e && e.replace(u8, j8).replace(T8, "");
      }
      function co(e, t, r) {
        e = c1(e), t = re(t);
        var s = e.length;
        r = r === i ? s : ct(Y(r), 0, s);
        var o = r;
        return r -= t.length, r >= 0 && e.slice(r, o) == t;
      }
      function uo(e) {
        return e = c1(e), e && z3.test(e) ? e.replace(P9, J8) : e;
      }
      function fo(e) {
        return e = c1(e), e && X3.test(e) ? e.replace(W0, "\\$&") : e;
      }
      var ho = Et(function(e, t, r) {
        return e + (r ? "-" : "") + t.toLowerCase();
      }), go = Et(function(e, t, r) {
        return e + (r ? " " : "") + t.toLowerCase();
      }), po = a6("toLowerCase");
      function _o(e, t, r) {
        e = c1(e), t = Y(t);
        var s = t ? wt(e) : 0;
        if (!t || s >= t)
          return e;
        var o = (t - s) / 2;
        return Xn(Bn(o), r) + e + Xn(Rn(o), r);
      }
      function vo(e, t, r) {
        e = c1(e), t = Y(t);
        var s = t ? wt(e) : 0;
        return t && s < t ? e + Xn(t - s, r) : e;
      }
      function Co(e, t, r) {
        e = c1(e), t = Y(t);
        var s = t ? wt(e) : 0;
        return t && s < t ? Xn(t - s, r) + e : e;
      }
      function yo(e, t, r) {
        return r || t == null ? t = 0 : t && (t = +t), wi(c1(e).replace(z0, ""), t || 0);
      }
      function mo(e, t, r) {
        return (r ? Q1(e, t, r) : t === i) ? t = 1 : t = Y(t), xr(c1(e), t);
      }
      function Lo() {
        var e = arguments, t = c1(e[0]);
        return e.length < 3 ? t : t.replace(e[1], e[2]);
      }
      var xo = Et(function(e, t, r) {
        return e + (r ? "_" : "") + t.toLowerCase();
      });
      function $o(e, t, r) {
        return r && typeof r != "number" && Q1(e, t, r) && (t = r = i), r = r === i ? u1 : r >>> 0, r ? (e = c1(e), e && (typeof t == "string" || t != null && !Qr(t)) && (t = re(t), !t && bt(e)) ? et(me(e), 0, r) : e.split(t, r)) : [];
      }
      var bo = Et(function(e, t, r) {
        return e + (r ? " " : "") + Yr(t);
      });
      function wo(e, t, r) {
        return e = c1(e), r = r == null ? 0 : ct(Y(r), 0, e.length), t = re(t), e.slice(r, r + t.length) == t;
      }
      function Ao(e, t, r) {
        var s = l.templateSettings;
        r && Q1(e, t, r) && (t = i), e = c1(e), t = l0({}, t, s, h6);
        var o = l0({}, t.imports, s.imports, h6), c = D1(o), h = ar(o, c), _, C, $ = 0, b = t.interpolate || Ln, w = "__p += '", k = or(
          (t.escape || Ln).source + "|" + b.source + "|" + (b === O9 ? i8 : Ln).source + "|" + (t.evaluate || Ln).source + "|$",
          "g"
        ), R = "//# sourceURL=" + (f1.call(t, "sourceURL") ? (t.sourceURL + "").replace(/\s/g, " ") : "lodash.templateSources[" + ++O8 + "]") + `
`;
        e.replace(k, function(W, J, r1, ae, H1, se) {
          return r1 || (r1 = ae), w += e.slice($, se).replace(f8, ei), J && (_ = !0, w += `' +
__e(` + J + `) +
'`), H1 && (C = !0, w += `';
` + H1 + `;
__p += '`), r1 && (w += `' +
((__t = (` + r1 + `)) == null ? '' : __t) +
'`), $ = se + W.length, W;
        }), w += `';
`;
        var Z = f1.call(t, "variable") && t.variable;
        if (!Z)
          w = `with (obj) {
` + w + `
}
`;
        else if (n8.test(Z))
          throw new Q(p);
        w = (C ? w.replace(K3, "") : w).replace(U3, "$1").replace(Z3, "$1;"), w = "function(" + (Z || "obj") + `) {
` + (Z ? "" : `obj || (obj = {});
`) + "var __t, __p = ''" + (_ ? ", __e = _.escape" : "") + (C ? `, __j = Array.prototype.join;
function print() { __p += __j.call(arguments, '') }
` : `;
`) + w + `return __p
}`;
        var X = i2(function() {
          return o1(c, R + "return " + w).apply(i, h);
        });
        if (X.source = w, zr(X))
          throw X;
        return X;
      }
      function So(e) {
        return c1(e).toLowerCase();
      }
      function Mo(e) {
        return c1(e).toUpperCase();
      }
      function To(e, t, r) {
        if (e = c1(e), e && (r || t === i))
          return g5(e);
        if (!e || !(t = re(t)))
          return e;
        var s = me(e), o = me(t), c = p5(s, o), h = _5(s, o) + 1;
        return et(s, c, h).join("");
      }
      function Io(e, t, r) {
        if (e = c1(e), e && (r || t === i))
          return e.slice(0, v5(e) + 1);
        if (!e || !(t = re(t)))
          return e;
        var s = me(e), o = _5(s, me(t)) + 1;
        return et(s, 0, o).join("");
      }
      function ko(e, t, r) {
        if (e = c1(e), e && (r || t === i))
          return e.replace(z0, "");
        if (!e || !(t = re(t)))
          return e;
        var s = me(e), o = p5(s, me(t));
        return et(s, o).join("");
      }
      function Eo(e, t) {
        var r = h1, s = j1;
        if (b1(t)) {
          var o = "separator" in t ? t.separator : o;
          r = "length" in t ? Y(t.length) : r, s = "omission" in t ? re(t.omission) : s;
        }
        e = c1(e);
        var c = e.length;
        if (bt(e)) {
          var h = me(e);
          c = h.length;
        }
        if (r >= c)
          return e;
        var _ = r - wt(s);
        if (_ < 1)
          return s;
        var C = h ? et(h, 0, _).join("") : e.slice(0, _);
        if (o === i)
          return C + s;
        if (h && (_ += C.length - _), Qr(o)) {
          if (e.slice(_).search(o)) {
            var $, b = C;
            for (o.global || (o = or(o.source, c1(D9.exec(o)) + "g")), o.lastIndex = 0; $ = o.exec(b); )
              var w = $.index;
            C = C.slice(0, w === i ? _ : w);
          }
        } else if (e.indexOf(re(o), _) != _) {
          var k = C.lastIndexOf(o);
          k > -1 && (C = C.slice(0, k));
        }
        return C + s;
      }
      function Po(e) {
        return e = c1(e), e && W3.test(e) ? e.replace(E9, oi) : e;
      }
      var Oo = Et(function(e, t, r) {
        return e + (r ? " " : "") + t.toUpperCase();
      }), Yr = a6("toUpperCase");
      function r2(e, t, r) {
        return e = c1(e), t = r ? i : t, t === i ? ni(e) ? ui(e) : G8(e) : e.match(t) || [];
      }
      var i2 = j(function(e, t) {
        try {
          return te(e, i, t);
        } catch (r) {
          return zr(r) ? r : new Q(r);
        }
      }), Do = Ne(function(e, t) {
        return ce(t, function(r) {
          r = Te(r), Be(e, r, Zr(e[r], e));
        }), e;
      });
      function Ro(e) {
        var t = e == null ? 0 : e.length, r = K();
        return e = t ? L1(e, function(s) {
          if (typeof s[1] != "function")
            throw new ue(d);
          return [r(s[0]), s[1]];
        }) : [], j(function(s) {
          for (var o = -1; ++o < t; ) {
            var c = e[o];
            if (te(c[0], this, s))
              return te(c[1], this, s);
          }
        });
      }
      function Bo(e) {
        return o7(he(e, M));
      }
      function Vr(e) {
        return function() {
          return e;
        };
      }
      function Fo(e, t) {
        return e == null || e !== e ? t : e;
      }
      var No = o6(), Ko = o6(!0);
      function q1(e) {
        return e;
      }
      function Xr(e) {
        return B5(typeof e == "function" ? e : he(e, M));
      }
      function Uo(e) {
        return N5(he(e, M));
      }
      function Zo(e, t) {
        return K5(e, he(t, M));
      }
      var Wo = j(function(e, t) {
        return function(r) {
          return cn(r, e, t);
        };
      }), zo = j(function(e, t) {
        return function(r) {
          return cn(e, r, t);
        };
      });
      function qr(e, t, r) {
        var s = D1(t), o = Wn(t, s);
        r == null && !(b1(t) && (o.length || !s.length)) && (r = t, t = e, e = this, o = Wn(t, D1(t)));
        var c = !(b1(r) && "chain" in r) || !!r.chain, h = Ue(e);
        return ce(o, function(_) {
          var C = t[_];
          e[_] = C, h && (e.prototype[_] = function() {
            var $ = this.__chain__;
            if (c || $) {
              var b = e(this.__wrapped__), w = b.__actions__ = Y1(this.__actions__);
              return w.push({ func: C, args: arguments, thisArg: e }), b.__chain__ = $, b;
            }
            return C.apply(e, Ye([this.value()], arguments));
          });
        }), e;
      }
      function Qo() {
        return F1._ === this && (F1._ = di), this;
      }
      function jr() {
      }
      function Ho(e) {
        return e = Y(e), j(function(t) {
          return U5(t, e);
        });
      }
      var Go = Tr(L1), Yo = Tr(l5), Vo = Tr(er);
      function a2(e) {
        return Rr(e) ? tr(Te(e)) : b7(e);
      }
      function Xo(e) {
        return function(t) {
          return e == null ? i : ut(e, t);
        };
      }
      var qo = c6(), jo = c6(!0);
      function Jr() {
        return [];
      }
      function e9() {
        return !1;
      }
      function Jo() {
        return {};
      }
      function el() {
        return "";
      }
      function tl() {
        return !0;
      }
      function nl(e, t) {
        if (e = Y(e), e < 1 || e > J1)
          return [];
        var r = u1, s = K1(e, u1);
        t = K(t), e -= u1;
        for (var o = ir(s, t); ++r < e; )
          t(r);
        return o;
      }
      function rl(e) {
        return H(e) ? L1(e, Te) : ie(e) ? [e] : Y1(w6(c1(e)));
      }
      function il(e) {
        var t = ++pi;
        return c1(e) + t;
      }
      var al = Vn(function(e, t) {
        return e + t;
      }, 0), sl = Ir("ceil"), ol = Vn(function(e, t) {
        return e / t;
      }, 1), ll = Ir("floor");
      function cl(e) {
        return e && e.length ? Zn(e, q1, _r) : i;
      }
      function ul(e, t) {
        return e && e.length ? Zn(e, K(t, 2), _r) : i;
      }
      function fl(e) {
        return f5(e, q1);
      }
      function hl(e, t) {
        return f5(e, K(t, 2));
      }
      function gl(e) {
        return e && e.length ? Zn(e, q1, yr) : i;
      }
      function pl(e, t) {
        return e && e.length ? Zn(e, K(t, 2), yr) : i;
      }
      var _l = Vn(function(e, t) {
        return e * t;
      }, 1), dl = Ir("round"), vl = Vn(function(e, t) {
        return e - t;
      }, 0);
      function Cl(e) {
        return e && e.length ? rr(e, q1) : 0;
      }
      function yl(e, t) {
        return e && e.length ? rr(e, K(t, 2)) : 0;
      }
      return l.after = K4, l.ary = R6, l.assign = Ss, l.assignIn = X6, l.assignInWith = l0, l.assignWith = Ms, l.at = Ts, l.before = B6, l.bind = Zr, l.bindAll = Do, l.bindKey = F6, l.castArray = j4, l.chain = P6, l.chunk = oa, l.compact = la, l.concat = ca, l.cond = Ro, l.conforms = Bo, l.constant = Vr, l.countBy = v4, l.create = Is, l.curry = N6, l.curryRight = K6, l.debounce = U6, l.defaults = ks, l.defaultsDeep = Es, l.defer = U4, l.delay = Z4, l.difference = ua, l.differenceBy = fa, l.differenceWith = ha, l.drop = ga, l.dropRight = pa, l.dropRightWhile = _a, l.dropWhile = da, l.fill = va, l.filter = y4, l.flatMap = x4, l.flatMapDeep = $4, l.flatMapDepth = b4, l.flatten = T6, l.flattenDeep = Ca, l.flattenDepth = ya, l.flip = W4, l.flow = No, l.flowRight = Ko, l.fromPairs = ma, l.functions = Ns, l.functionsIn = Ks, l.groupBy = w4, l.initial = xa, l.intersection = $a, l.intersectionBy = ba, l.intersectionWith = wa, l.invert = Zs, l.invertBy = Ws, l.invokeMap = S4, l.iteratee = Xr, l.keyBy = M4, l.keys = D1, l.keysIn = X1, l.map = n0, l.mapKeys = Qs, l.mapValues = Hs, l.matches = Uo, l.matchesProperty = Zo, l.memoize = i0, l.merge = Gs, l.mergeWith = q6, l.method = Wo, l.methodOf = zo, l.mixin = qr, l.negate = a0, l.nthArg = Ho, l.omit = Ys, l.omitBy = Vs, l.once = z4, l.orderBy = T4, l.over = Go, l.overArgs = Q4, l.overEvery = Yo, l.overSome = Vo, l.partial = Wr, l.partialRight = Z6, l.partition = I4, l.pick = Xs, l.pickBy = j6, l.property = a2, l.propertyOf = Xo, l.pull = Ta, l.pullAll = k6, l.pullAllBy = Ia, l.pullAllWith = ka, l.pullAt = Ea, l.range = qo, l.rangeRight = jo, l.rearg = H4, l.reject = P4, l.remove = Pa, l.rest = G4, l.reverse = Kr, l.sampleSize = D4, l.set = js, l.setWith = Js, l.shuffle = R4, l.slice = Oa, l.sortBy = N4, l.sortedUniq = Ua, l.sortedUniqBy = Za, l.split = $o, l.spread = Y4, l.tail = Wa, l.take = za, l.takeRight = Qa, l.takeRightWhile = Ha, l.takeWhile = Ga, l.tap = l4, l.throttle = V4, l.thru = t0, l.toArray = G6, l.toPairs = J6, l.toPairsIn = e2, l.toPath = rl, l.toPlainObject = V6, l.transform = eo, l.unary = X4, l.union = Ya, l.unionBy = Va, l.unionWith = Xa, l.uniq = qa, l.uniqBy = ja, l.uniqWith = Ja, l.unset = to, l.unzip = Ur, l.unzipWith = E6, l.update = no, l.updateWith = ro, l.values = Dt, l.valuesIn = io, l.without = e4, l.words = r2, l.wrap = q4, l.xor = t4, l.xorBy = n4, l.xorWith = r4, l.zip = i4, l.zipObject = a4, l.zipObjectDeep = s4, l.zipWith = o4, l.entries = J6, l.entriesIn = e2, l.extend = X6, l.extendWith = l0, qr(l, l), l.add = al, l.attempt = i2, l.camelCase = lo, l.capitalize = t2, l.ceil = sl, l.clamp = ao, l.clone = J4, l.cloneDeep = ts, l.cloneDeepWith = ns, l.cloneWith = es, l.conformsTo = rs, l.deburr = n2, l.defaultTo = Fo, l.divide = ol, l.endsWith = co, l.eq = xe, l.escape = uo, l.escapeRegExp = fo, l.every = C4, l.find = m4, l.findIndex = S6, l.findKey = Ps, l.findLast = L4, l.findLastIndex = M6, l.findLastKey = Os, l.floor = ll, l.forEach = O6, l.forEachRight = D6, l.forIn = Ds, l.forInRight = Rs, l.forOwn = Bs, l.forOwnRight = Fs, l.get = Hr, l.gt = is, l.gte = as, l.has = Us, l.hasIn = Gr, l.head = I6, l.identity = q1, l.includes = A4, l.indexOf = La, l.inRange = so, l.invoke = zs, l.isArguments = gt, l.isArray = H, l.isArrayBuffer = ss, l.isArrayLike = V1, l.isArrayLikeObject = T1, l.isBoolean = os, l.isBuffer = tt, l.isDate = ls, l.isElement = cs, l.isEmpty = us, l.isEqual = fs, l.isEqualWith = hs, l.isError = zr, l.isFinite = gs, l.isFunction = Ue, l.isInteger = W6, l.isLength = s0, l.isMap = z6, l.isMatch = ps, l.isMatchWith = _s, l.isNaN = ds, l.isNative = vs, l.isNil = ys, l.isNull = Cs, l.isNumber = Q6, l.isObject = b1, l.isObjectLike = w1, l.isPlainObject = _n, l.isRegExp = Qr, l.isSafeInteger = ms, l.isSet = H6, l.isString = o0, l.isSymbol = ie, l.isTypedArray = Ot, l.isUndefined = Ls, l.isWeakMap = xs, l.isWeakSet = $s, l.join = Aa, l.kebabCase = ho, l.last = pe, l.lastIndexOf = Sa, l.lowerCase = go, l.lowerFirst = po, l.lt = bs, l.lte = ws, l.max = cl, l.maxBy = ul, l.mean = fl, l.meanBy = hl, l.min = gl, l.minBy = pl, l.stubArray = Jr, l.stubFalse = e9, l.stubObject = Jo, l.stubString = el, l.stubTrue = tl, l.multiply = _l, l.nth = Ma, l.noConflict = Qo, l.noop = jr, l.now = r0, l.pad = _o, l.padEnd = vo, l.padStart = Co, l.parseInt = yo, l.random = oo, l.reduce = k4, l.reduceRight = E4, l.repeat = mo, l.replace = Lo, l.result = qs, l.round = dl, l.runInContext = v, l.sample = O4, l.size = B4, l.snakeCase = xo, l.some = F4, l.sortedIndex = Da, l.sortedIndexBy = Ra, l.sortedIndexOf = Ba, l.sortedLastIndex = Fa, l.sortedLastIndexBy = Na, l.sortedLastIndexOf = Ka, l.startCase = bo, l.startsWith = wo, l.subtract = vl, l.sum = Cl, l.sumBy = yl, l.template = Ao, l.times = nl, l.toFinite = Ze, l.toInteger = Y, l.toLength = Y6, l.toLower = So, l.toNumber = _e, l.toSafeInteger = As, l.toString = c1, l.toUpper = Mo, l.trim = To, l.trimEnd = Io, l.trimStart = ko, l.truncate = Eo, l.unescape = Po, l.uniqueId = il, l.upperCase = Oo, l.upperFirst = Yr, l.each = O6, l.eachRight = D6, l.first = I6, qr(l, function() {
        var e = {};
        return Se(l, function(t, r) {
          f1.call(l.prototype, r) || (e[r] = t);
        }), e;
      }(), { chain: !1 }), l.VERSION = u, ce(["bind", "bindKey", "curry", "curryRight", "partial", "partialRight"], function(e) {
        l[e].placeholder = l;
      }), ce(["drop", "take"], function(e, t) {
        e1.prototype[e] = function(r) {
          r = r === i ? 1 : E1(Y(r), 0);
          var s = this.__filtered__ && !t ? new e1(this) : this.clone();
          return s.__filtered__ ? s.__takeCount__ = K1(r, s.__takeCount__) : s.__views__.push({
            size: K1(r, u1),
            type: e + (s.__dir__ < 0 ? "Right" : "")
          }), s;
        }, e1.prototype[e + "Right"] = function(r) {
          return this.reverse()[e](r).reverse();
        };
      }), ce(["filter", "map", "takeWhile"], function(e, t) {
        var r = t + 1, s = r == rt || r == yt;
        e1.prototype[e] = function(o) {
          var c = this.clone();
          return c.__iteratees__.push({
            iteratee: K(o, 3),
            type: r
          }), c.__filtered__ = c.__filtered__ || s, c;
        };
      }), ce(["head", "last"], function(e, t) {
        var r = "take" + (t ? "Right" : "");
        e1.prototype[e] = function() {
          return this[r](1).value()[0];
        };
      }), ce(["initial", "tail"], function(e, t) {
        var r = "drop" + (t ? "" : "Right");
        e1.prototype[e] = function() {
          return this.__filtered__ ? new e1(this) : this[r](1);
        };
      }), e1.prototype.compact = function() {
        return this.filter(q1);
      }, e1.prototype.find = function(e) {
        return this.filter(e).head();
      }, e1.prototype.findLast = function(e) {
        return this.reverse().find(e);
      }, e1.prototype.invokeMap = j(function(e, t) {
        return typeof e == "function" ? new e1(this) : this.map(function(r) {
          return cn(r, e, t);
        });
      }), e1.prototype.reject = function(e) {
        return this.filter(a0(K(e)));
      }, e1.prototype.slice = function(e, t) {
        e = Y(e);
        var r = this;
        return r.__filtered__ && (e > 0 || t < 0) ? new e1(r) : (e < 0 ? r = r.takeRight(-e) : e && (r = r.drop(e)), t !== i && (t = Y(t), r = t < 0 ? r.dropRight(-t) : r.take(t - e)), r);
      }, e1.prototype.takeRightWhile = function(e) {
        return this.reverse().takeWhile(e).reverse();
      }, e1.prototype.toArray = function() {
        return this.take(u1);
      }, Se(e1.prototype, function(e, t) {
        var r = /^(?:filter|find|map|reject)|While$/.test(t), s = /^(?:head|last)$/.test(t), o = l[s ? "take" + (t == "last" ? "Right" : "") : t], c = s || /^find/.test(t);
        o && (l.prototype[t] = function() {
          var h = this.__wrapped__, _ = s ? [1] : arguments, C = h instanceof e1, $ = _[0], b = C || H(h), w = function(J) {
            var r1 = o.apply(l, Ye([J], _));
            return s && k ? r1[0] : r1;
          };
          b && r && typeof $ == "function" && $.length != 1 && (C = b = !1);
          var k = this.__chain__, R = !!this.__actions__.length, Z = c && !k, X = C && !R;
          if (!c && b) {
            h = X ? h : new e1(this);
            var W = e.apply(h, _);
            return W.__actions__.push({ func: t0, args: [w], thisArg: i }), new fe(W, k);
          }
          return Z && X ? e.apply(this, _) : (W = this.thru(w), Z ? s ? W.value()[0] : W.value() : W);
        });
      }), ce(["pop", "push", "shift", "sort", "splice", "unshift"], function(e) {
        var t = Sn[e], r = /^(?:push|sort|unshift)$/.test(e) ? "tap" : "thru", s = /^(?:pop|shift)$/.test(e);
        l.prototype[e] = function() {
          var o = arguments;
          if (s && !this.__chain__) {
            var c = this.value();
            return t.apply(H(c) ? c : [], o);
          }
          return this[r](function(h) {
            return t.apply(H(h) ? h : [], o);
          });
        };
      }), Se(e1.prototype, function(e, t) {
        var r = l[t];
        if (r) {
          var s = r.name + "";
          f1.call(Tt, s) || (Tt[s] = []), Tt[s].push({ name: t, func: r });
        }
      }), Tt[Yn(i, i1).name] = [{
        name: "wrapper",
        func: i
      }], e1.prototype.clone = Ei, e1.prototype.reverse = Pi, e1.prototype.value = Oi, l.prototype.at = c4, l.prototype.chain = u4, l.prototype.commit = f4, l.prototype.next = h4, l.prototype.plant = p4, l.prototype.reverse = _4, l.prototype.toJSON = l.prototype.valueOf = l.prototype.value = d4, l.prototype.first = l.prototype.head, tn && (l.prototype[tn] = g4), l;
    }, At = fi();
    at ? ((at.exports = At)._ = At, X0._ = At) : F1._ = At;
  }).call(ze);
})(b0, b0.exports);
var pt = b0.exports, dw = /* @__PURE__ */ I("<span>");
class mw {
  constructor(a) {
    t9(this, "_container");
    t9(this, "_chartApi", null);
    if (x1.isString(a.container)) {
      if (this._container = document.getElementById(a.container), !this._container)
        throw new Error("Container is null");
    } else
      this._container = a.container;
    this._container.classList.add("klinecharts-pro"), this._container.setAttribute("data-theme", a.theme ?? "light"), oc(() => {
      const i = this;
      return B(_w, {
        ref: (u) => {
          i._chartApi = u;
        },
        get styles() {
          return a.styles ?? {};
        },
        get watermark() {
          return a.watermark ?? dw();
        },
        get theme() {
          return a.theme ?? "light";
        },
        get locale() {
          return a.locale ?? "zh-CN";
        },
        get drawingBarVisible() {
          return a.drawingBarVisible ?? !0;
        },
        get symbol() {
          return a.symbol;
        },
        get period() {
          return a.period;
        },
        get periods() {
          return a.periods ?? [{
            multiplier: 1,
            timespan: "minute",
            text: "1m"
          }, {
            multiplier: 5,
            timespan: "minute",
            text: "5m"
          }, {
            multiplier: 15,
            timespan: "minute",
            text: "15m"
          }, {
            multiplier: 1,
            timespan: "hour",
            text: "1H"
          }, {
            multiplier: 2,
            timespan: "hour",
            text: "2H"
          }, {
            multiplier: 4,
            timespan: "hour",
            text: "4H"
          }, {
            multiplier: 1,
            timespan: "day",
            text: "D"
          }, {
            multiplier: 1,
            timespan: "week",
            text: "W"
          }, {
            multiplier: 1,
            timespan: "month",
            text: "M"
          }, {
            multiplier: 1,
            timespan: "year",
            text: "Y"
          }];
        },
        get overlays() {
          return a.overlays ?? [];
        },
        get timezone() {
          return a.timezone ?? "Asia/Shanghai";
        },
        get mainIndicators() {
          return a.mainIndicators ?? ["MA"];
        },
        get subIndicators() {
          return a.subIndicators ?? ["VOL"];
        },
        get datafeed() {
          return a.datafeed;
        },
        get onMainIndicatorsChange() {
          return a.onMainIndicatorsChange ?? pt.noop;
        },
        get onSubIndicatorsChange() {
          return a.onSubIndicatorsChange ?? pt.noop;
        },
        get onTimezoneChange() {
          return a.onTimezoneChange ?? pt.noop;
        },
        get onSettingsChange() {
          return a.onSettingsChange ?? pt.noop;
        },
        get onPeriodChange() {
          return a.onPeriodChange ?? pt.noop;
        },
        get onOverlayChange() {
          return a.onOverlayChange ?? pt.noop;
        },
        get onOverlayRemove() {
          return a.onOverlayRemove ?? pt.noop;
        }
      });
    }, this._container);
  }
  setTheme(a) {
    var i;
    (i = this._container) == null || i.setAttribute("data-theme", a), this._chartApi.setTheme(a);
  }
  getTheme() {
    return this._chartApi.getTheme();
  }
  setStyles(a) {
    this._chartApi.setStyles(a);
  }
  getStyles() {
    return this._chartApi.getStyles();
  }
  setLocale(a) {
    this._chartApi.setLocale(a);
  }
  getLocale() {
    return this._chartApi.getLocale();
  }
  setTimezone(a) {
    this._chartApi.setTimezone(a);
  }
  getTimezone() {
    return this._chartApi.getTimezone();
  }
  setSymbol(a) {
    this._chartApi.setSymbol(a);
  }
  getSymbol() {
    return this._chartApi.getSymbol();
  }
  setPeriod(a) {
    this._chartApi.setPeriod(a);
  }
  getPeriod() {
    return this._chartApi.getPeriod();
  }
  getInstance() {
    var a;
    return ((a = this._chartApi) == null ? void 0 : a.getInstance()) || null;
  }
}
Wl.forEach((n) => {
  wl(n);
});
export {
  mw as KLineChartPro,
  yw as loadLocales
};
//# sourceMappingURL=klinecharts-pro.js.map
