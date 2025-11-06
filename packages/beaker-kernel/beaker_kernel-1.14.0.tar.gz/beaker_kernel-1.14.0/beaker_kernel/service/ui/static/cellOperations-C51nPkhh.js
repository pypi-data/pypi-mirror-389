import { m as k, __tla as __tla_0 } from "./renderers-707ItvV_.js";
import { f as L, c as N, __tla as __tla_1 } from "./BeakerRawCell.vue_vue_type_style_index_0_lang-OdsdCFW2.js";
import { d as V, i as w, r as j, x as R, f as u, R as $, A as r, o as s, G as p, B as i, M as D, H as v, K as c, V as F, W as z, j as P, u as y, ar as b, aq as T, S as U, a3 as W, I as G, J as _ } from "./primevue-BhybIXDC.js";
let ve, ye;
let __tla = Promise.all([
    (()=>{
        try {
            return __tla_0;
        } catch  {}
    })(),
    (()=>{
        try {
            return __tla_1;
        } catch  {}
    })()
]).then(async ()=>{
    let J, K, X, Y, Z, ee, te, ne, se, re, oe, ae, le, ie;
    J = {
        class: "llm-query-event"
    };
    K = {
        key: 0
    };
    X = {
        key: 1
    };
    Y = [
        "innerHTML"
    ];
    Z = {
        key: 3
    };
    ee = {
        key: 4
    };
    te = [
        "innerHTML"
    ];
    ne = {
        key: 5,
        style: {
            position: "relative"
        }
    };
    se = {
        key: 6
    };
    re = {
        key: 7
    };
    oe = {
        key: 0,
        class: "pre"
    };
    ae = {
        key: 1,
        class: "pre"
    };
    le = {
        key: 0,
        class: "pre"
    };
    ve = V({
        __name: "BeakerQueryCellEvent",
        props: [
            "event",
            "parentQueryCell",
            "codeStyles",
            "shouldHideAnsweredQuestions"
        ],
        setup (a, { expose: B }) {
            const g = w("beakerSession"), f = w("notebook"), m = j(), e = a;
            R(()=>{
                k.setOptions({});
            });
            const S = ()=>{
                f && f.selectCell(e.event?.content.cell_id);
            }, A = u(()=>g.session.notebook.cells.indexOf(e.parentQueryCell.value)), M = u(()=>f ? A.value.toString() === f.selectedCellId : !1), x = u(()=>e.parentQueryCell?.children?.map(((t)=>t?.outputs?.every((l)=>{
                        if (l?.data !== void 0) {
                            const o = Object.keys(l?.data);
                            return l?.output_type === "execute_result" && o.length === 1 && o[0] === "text/plain";
                        } else return !0;
                    }))).every((t)=>t) ? [] : e.parentQueryCell?.children?.entries()), O = u(()=>{
                const n = [];
                return e.parentQueryCell?.children?.entries()?.forEach(([t, l])=>{
                    l?.outputs?.forEach((o)=>{
                        const d = [
                            "image/png",
                            "text/html"
                        ];
                        [
                            "execute_result",
                            "display_data"
                        ].includes(o?.output_type) && d.map((h)=>Object.keys(o?.data ?? []).includes(h)).some((h)=>h) && n.push(t);
                    });
                }), n;
            }), Q = (n)=>{
                const t = g.session.notebook;
                for (const l of t.cells){
                    const o = l.children?.find((d)=>d.id === n);
                    if (typeof o < "u") return o;
                }
            }, C = (n)=>[
                    "response",
                    "user_answer",
                    "user_question"
                ].includes(n.type), q = (n)=>!(n.type === "response" && n.content === "None"), H = (n)=>n.type === "user_question" && n.waitForUserInput, I = u(()=>C(e.event) ? k.parse(e.event.content, {
                    async: !1
                }).trim() : "");
            function E() {}
            return B({
                execute: E
            }), (n, t)=>{
                const l = $("keybindings");
                return s(), r("div", J, [
                    H(a.event) ? (s(), r("div", K, [
                        ...t[0] || (t[0] = [
                            i("span", {
                                class: "waiting-text"
                            }, [
                                i("i", {
                                    class: "pi pi-spin pi-spinner",
                                    style: {
                                        "font-size": "1rem"
                                    }
                                }),
                                D(" Waiting for user input in conversation. ")
                            ], -1)
                        ])
                    ])) : a.event.type === "user_question" && e.shouldHideAnsweredQuestions ? (s(), r("div", X)) : C(a.event) && q(a.event) ? (s(), r("div", {
                        key: 2,
                        innerHTML: I.value,
                        class: "md-inline"
                    }, null, 8, Y)) : p("", !0),
                    e.event?.type === "response" && x.value !== 0 ? (s(), r("div", Z, [
                        v(y(T), {
                            multiple: !0,
                            "active-index": O.value
                        }, {
                            default: c(()=>[
                                    (s(!0), r(F, null, z(x.value, ([o, d])=>(s(), P(y(b), {
                                            key: o,
                                            pt: {
                                                header: {
                                                    class: [
                                                        "agent-response-header"
                                                    ]
                                                },
                                                headerAction: {
                                                    class: [
                                                        "agent-response-headeraction"
                                                    ]
                                                },
                                                content: {
                                                    class: [
                                                        "agent-response-content"
                                                    ]
                                                },
                                                headerIcon: {
                                                    class: [
                                                        "agent-response-icon"
                                                    ]
                                                }
                                            }
                                        }, {
                                            header: c(()=>[
                                                    ...t[1] || (t[1] = [
                                                        i("span", {
                                                            class: "flex align-items-center gap-2 w-full"
                                                        }, [
                                                            i("span", null, "Outputs")
                                                        ], -1)
                                                    ])
                                                ]),
                                            default: c(()=>[
                                                    v(L, {
                                                        outputs: d?.outputs
                                                    }, null, 8, [
                                                        "outputs"
                                                    ])
                                                ]),
                                            _: 2
                                        }, 1024))), 128))
                                ]),
                            _: 1
                        }, 8, [
                            "active-index"
                        ])
                    ])) : e.event?.type === "thought" ? (s(), r("div", ee, [
                        i("div", {
                            innerHTML: y(k).parse(e.event.content.thought)
                        }, null, 8, te)
                    ])) : e.event?.type === "code_cell" ? (s(), r("div", ne, [
                        U(v(N, {
                            onClick: S,
                            cell: Q(e?.event.content.cell_id),
                            "drag-enabled": !1,
                            "code-styles": e.codeStyles,
                            class: G({
                                selected: M.value,
                                "query-event-code-cell": !0
                            }),
                            "hide-output": !1,
                            ref_key: "codeCellRef",
                            ref: m
                        }, null, 8, [
                            "cell",
                            "code-styles",
                            "class"
                        ]), [
                            [
                                l,
                                {
                                    "keydown.enter.ctrl.prevent.capture.in-editor": (o)=>{
                                        m.value.execute();
                                    },
                                    "keydown.enter.shift.prevent.capture.in-editor": (o)=>{
                                        m.value.execute();
                                    }
                                }
                            ]
                        ]),
                        W(n.$slots, "code-cell-controls")
                    ])) : e.event?.type === "error" && e.event.content.ename === "CancelledError" ? (s(), r("span", se, [
                        ...t[2] || (t[2] = [
                            i("h4", {
                                class: "p-error"
                            }, "Request cancelled.", -1)
                        ])
                    ])) : e.event?.type === "error" ? (s(), r("span", re, [
                        i("div", null, [
                            e?.event.content.ename ? (s(), r("pre", oe, "                    " + _(e?.event.content.ename) + `
                `, 1)) : p("", !0),
                            e?.event.content.evalue ? (s(), r("pre", ae, "                    " + _(e?.event.content.evalue) + `
                `, 1)) : p("", !0),
                            v(y(T), null, {
                                default: c(()=>[
                                        v(y(b), {
                                            pt: {
                                                header: {
                                                    class: [
                                                        "agent-response-header"
                                                    ]
                                                },
                                                headerAction: {
                                                    class: [
                                                        "agent-response-headeraction"
                                                    ]
                                                },
                                                content: {
                                                    class: [
                                                        "agent-response-content",
                                                        "agent-response-content-error"
                                                    ]
                                                },
                                                headerIcon: {
                                                    class: [
                                                        "agent-response-icon"
                                                    ]
                                                }
                                            }
                                        }, {
                                            header: c(()=>[
                                                    ...t[3] || (t[3] = [
                                                        i("span", {
                                                            class: "flex align-items-center gap-2 w-full"
                                                        }, [
                                                            i("span", {
                                                                class: "font-bold white-space-nowrap"
                                                            }, "Traceback:")
                                                        ], -1)
                                                    ])
                                                ]),
                                            default: c(()=>[
                                                    e?.event.content.traceback ? (s(), r("pre", le, "                            " + _(e?.event.content.traceback?.join(`
`)) + `
                        `, 1)) : p("", !0)
                                                ]),
                                            _: 1
                                        })
                                    ]),
                                _: 1
                            })
                        ])
                    ])) : p("", !0)
                ]);
            };
        }
    });
    ie = [
        "error",
        "response"
    ];
    ye = (a)=>a?.length > 0 ? ie.includes(a[a.length - 1].type) : !1;
});
export { ve as _, ye as i, __tla };
