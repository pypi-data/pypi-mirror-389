import { d as F, i as P, r as k, j as E, o as a, u as t, a1 as he, K as u, H as n, a as D, w as T, N as M, a2 as pe, n as fe, f as w, A as v, B as p, a3 as ae, V as G, W as le, a4 as ge, g as se, x as _e, y as ye, z as ke, R as W, G as I, S as V, a5 as de, a6 as ie, a7 as re, J as ne, I as L, M as X, a8 as we, a9 as be, U as ce, aa as Ce, p as xe } from "./primevue-BhybIXDC.js";
import { h as $e, a as qe, L as Se, b as Re, w as Ie, _ as Me, c as ue, d as R, e as Ee, f as Pe, g as Ne, __tla as __tla_0 } from "./renderers-707ItvV_.js";
import { d as ve, a as Te, b as Ve, c as Be, _ as ze, __tla as __tla_1 } from "./BeakerRawCell.vue_vue_type_style_index_0_lang-OdsdCFW2.js";
import { _ as Qe, a as Ae, b as De, __tla as __tla_2 } from "./MediaPanel.vue_vue_type_style_index_0_lang-BvwUDR1l.js";
import { N as Fe } from "./NotebookSvg-BSyKzMd5.js";
import { i as J, _ as oe, __tla as __tla_3 } from "./cellOperations-C51nPkhh.js";
import { u as Le } from "./BaseQueryCell-5qJKeHAI.js";
import { _ as He, a as Ue, l as Oe, __tla as __tla_4 } from "./IntegrationPanel.vue_vue_type_style_index_0_lang-CAs3cGuu.js";
import { _ as Ke } from "./_plugin-vue_export-helper-DlAUqK2U.js";
import { s as je } from "./jupyterlab-Bq9OOClR.js";
import { __tla as __tla_5 } from "./index-wfwXefED.js";
import "./codemirror-CEJpu35t.js";
import "./xlsx-C3u7rb2R.js";
import { __tla as __tla_6 } from "./pdfjs-B7zhfHd9.js";
let Ut;
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
    })(),
    (()=>{
        try {
            return __tla_2;
        } catch  {}
    })(),
    (()=>{
        try {
            return __tla_3;
        } catch  {}
    })(),
    (()=>{
        try {
            return __tla_4;
        } catch  {}
    })(),
    (()=>{
        try {
            return __tla_5;
        } catch  {}
    })(),
    (()=>{
        try {
            return __tla_6;
        } catch  {}
    })()
]).then(async ()=>{
    let Je, Ge, We, Xe, Ye, Ze, et, tt, nt, st, ot, lt, at, it, rt, ct, ut, pt, dt, vt, mt, ht, ft, gt, _t, yt, kt, wt, bt, Ct, xt, $t, qt, St, Rt, It;
    Je = F({
        __name: "AgentQuery",
        props: [
            "placeholder"
        ],
        emits: [
            "select-cell",
            "run-cell"
        ],
        setup ($, { emit: g }) {
            const _ = P("beakerSession"), s = k(""), i = $, f = P("session"), c = (b)=>{
                const h = f.notebook;
                if (!s.value.trim()) return;
                if (h.cells.length === 1) {
                    const m = h.cells[0];
                    m.cell_type === "code" && m.source === "" && m.execution_count === null && m.outputs.length === 0 && h.removeCell(0);
                }
                const r = f.addQueryCell(s.value);
                s.value = "", fe(()=>{
                    _.findNotebookCellById(r.id).execute();
                });
            };
            return (b, h)=>(a(), E(t(he), {
                    class: "agent-input-card"
                }, {
                    content: u(()=>[
                            n(t(pe), null, {
                                default: u(()=>[
                                        n(ve, {
                                            class: "agent-query-textarea",
                                            onKeydown: [
                                                D(T(c, [
                                                    "exact",
                                                    "prevent"
                                                ]), [
                                                    "enter"
                                                ]),
                                                h[0] || (h[0] = D(T((r)=>r.target.blur(), [
                                                    "prevent",
                                                    "stop"
                                                ]), [
                                                    "escape"
                                                ]))
                                            ],
                                            modelValue: s.value,
                                            "onUpdate:modelValue": h[1] || (h[1] = (r)=>s.value = r),
                                            placeholder: i.placeholder ?? "How can the agent help?"
                                        }, null, 8, [
                                            "onKeydown",
                                            "modelValue",
                                            "placeholder"
                                        ]),
                                        n(t(M), {
                                            icon: "pi pi-send",
                                            outlined: "",
                                            onClick: c
                                        })
                                    ]),
                                _: 1
                            })
                        ]),
                    _: 1
                }));
        }
    });
    Ge = {
        class: "panel-cell-container"
    };
    We = {
        class: "flex-background"
    };
    Xe = {
        class: "chat-help-text-display query-answer-chat-override"
    };
    Ye = F({
        __name: "ChatPanel",
        props: [
            "cellMap"
        ],
        setup ($) {
            const g = P("session"), _ = $, s = w(()=>g.notebook.cells.filter((i)=>!i.metadata?.parent_query_cell));
            return (i, f)=>(a(), v("div", Ge, [
                    p("div", We, [
                        ae(i.$slots, "notebook-background")
                    ]),
                    p("span", Xe, [
                        ae(i.$slots, "help-text")
                    ]),
                    (a(!0), v(G, null, le(s.value, (c, b)=>(a(), E(ge(_.cellMap[c.cell_type]), {
                            cell: c,
                            key: c.id || b,
                            class: "beaker-chat-cell"
                        }, null, 8, [
                            "cell"
                        ]))), 128))
                ]));
        }
    });
    Ze = {
        class: "llm-query-cell"
    };
    et = {
        class: "llm-prompt-container llm-prompt-container-chat"
    };
    tt = {
        class: "prompt-input-container"
    };
    nt = {
        class: "prompt-controls"
    };
    st = [
        "data-cell-id"
    ];
    ot = {
        key: 0,
        class: "event-container"
    };
    lt = {
        class: "events"
    };
    at = {
        class: "white-space-nowrap",
        style: {
            display: "flex",
            "align-items": "center",
            "font-weight": "400",
            "font-family": "'Courier New', Courier, monospace",
            "font-size": "0.8rem",
            color: "var(--p-text-color-secondary)"
        }
    };
    it = {
        style: {
            display: "flex",
            "flex-direction": "column"
        }
    };
    rt = {
        class: "white-space-nowrap",
        style: {
            display: "flex",
            "align-items": "center",
            "font-weight": "400",
            "font-family": "'Courier New', Courier, monospace",
            "font-size": "0.8rem",
            color: "var(--p-text-color-secondary)"
        }
    };
    ct = {
        key: 1,
        class: "query-answer-chat-override"
    };
    ut = {
        key: 1,
        class: "input-request-chat-override"
    };
    pt = {
        class: "input-request-wrapper input-request-wrapper-chat"
    };
    dt = {
        modelClass: $e,
        icon: "pi pi-sparkles"
    };
    vt = F({
        ...dt,
        __name: "ChatQueryCell",
        props: [
            "index",
            "cell"
        ],
        setup ($, { expose: g }) {
            const _ = $, { cell: s, isEditing: i, promptEditorMinHeight: f, promptText: c, response: b, textarea: h, events: r, execute: m, enter: C, exit: N, clear: x, respond: q } = Le(_);
            let B;
            ((l)=>{
                l[l.NotExecuted = 0] = "NotExecuted", l[l.Running = 1] = "Running", l[l.Done = 2] = "Done";
            })(B || (B = {}));
            const S = P("activeQueryCell"), H = P("beakerSession"), Y = ye(), U = w(()=>{
                const l = "Thinking";
                if (r.value.length < 1) return l;
                const o = r.value[r.value.length - 1];
                if (o.type === "thought") return o.content.thought;
                {
                    let y = 2, e = r.value[r.value.length - y];
                    if (e === void 0) return l;
                    for(; e.type !== "thought" && r.value.length >= y;)y += 1, e = r.value[r.value.length - y];
                    if (e.type === "thought") {
                        if (e.content.thought === "Thinking..." && o.type === "response") return "Thinking...";
                        const d = {
                            user_question: "(awaiting user input)",
                            user_answer: "(answer received, thinking)",
                            code_cell: "(code is now running)"
                        };
                        return d[o.type] ? `${e.content.thought} ${d[o.type]}` : e.content.thought;
                    } else return l;
                }
            }), z = (l, o = !1)=>{
                const y = ce(s.value);
                if (o) {
                    S.value = y;
                    return;
                }
                ce(S.value)?.id === y?.id ? S.value = null : S.value = y;
            }, Q = w(()=>{
                const l = r.value.length;
                return _.cell.status === "busy" ? 1 : l === 0 ? 0 : J(r.value) ? 2 : 1;
            });
            se(Q, (l, o)=>{
                l === 1 && o !== 1 && z(null, !0);
            });
            const A = w(()=>_.cell?.events?.filter((l)=>[
                        "user_question",
                        "user_answer"
                    ].includes(l.type)).map((l)=>{
                    var o;
                    return l.type === "user_question" ? o = "query-answer-chat query-answer-chat-override" : o = "llm-prompt-container llm-prompt-container-chat llm-prompt-text llm-prompt-text-chat", [
                        l,
                        o
                    ];
                })), O = (l)=>l.status === "busy", Z = (l)=>{
                i.value || (f.value = l.target.clientHeight, i.value = !0);
            }, ee = w(()=>A.value.some(([l])=>l.type === "user_answer")), te = (l, o)=>l.type !== "user_answer" ? !1 : !A.value.slice(o + 1).some(([e])=>e.type === "user_answer");
            return g({
                execute: m,
                enter: C,
                exit: N,
                clear: x,
                cell: s,
                editor: h
            }), _e(()=>{
                H.cellRegistry[s.value.id] = Y.vnode;
            }), ke(()=>{
                delete H.cellRegistry[s.value.id];
            }), (l, o)=>{
                const y = W("focustrap");
                return a(), v("div", Ze, [
                    p("div", {
                        class: "query query-chat",
                        onDblclick: Z
                    }, [
                        p("div", et, [
                            V(p("div", tt, [
                                n(ve, {
                                    ref_key: "textarea",
                                    ref: h,
                                    class: "prompt-input",
                                    modelValue: t(c),
                                    "onUpdate:modelValue": o[0] || (o[0] = (e)=>re(c) ? c.value = e : null),
                                    style: ie({
                                        minHeight: `${t(f)}px`
                                    })
                                }, null, 8, [
                                    "modelValue",
                                    "style"
                                ]),
                                p("div", nt, [
                                    n(t(M), {
                                        label: "Submit",
                                        onClick: t(m)
                                    }, null, 8, [
                                        "onClick"
                                    ]),
                                    n(t(M), {
                                        label: "Cancel",
                                        onClick: o[1] || (o[1] = (e)=>{
                                            c.value = t(s).source, i.value = !1;
                                        })
                                    })
                                ])
                            ], 512), [
                                [
                                    de,
                                    t(i)
                                ]
                            ]),
                            p("div", {
                                style: ie({
                                    visibility: t(i) ? "hidden" : "visible",
                                    height: t(i) ? "0px" : "auto",
                                    padding: t(i) ? "0px" : "0.5rem"
                                }),
                                class: "llm-prompt-text llm-prompt-text-chat",
                                "data-cell-id": t(s).id
                            }, ne(t(s).source), 13, st)
                        ])
                    ], 32),
                    t(r).length > 0 || t(J)(t(r)) || O(t(s)) ? (a(), v("div", ot, [
                        p("div", lt, [
                            ee.value ? I("", !0) : (a(), v("div", {
                                key: 0,
                                class: L([
                                    "expand-thoughts-button",
                                    {
                                        expanded: t(S) === t(s)
                                    }
                                ]),
                                onClick: z
                            }, [
                                p("div", at, [
                                    p("i", {
                                        class: L([
                                            "pi pi-sparkles",
                                            {
                                                "animate-sparkles": Q.value === 1
                                            }
                                        ]),
                                        style: {
                                            color: "var(--p-yellow-500)",
                                            "font-size": "1.25rem",
                                            "margin-right": "0.6rem"
                                        }
                                    }, null, 2),
                                    X(" " + ne(U.value), 1)
                                ]),
                                n(t(M), {
                                    icon: t(S) === t(s) ? "pi pi-times" : "pi pi-search",
                                    text: "",
                                    rounded: "",
                                    style: {
                                        "background-color": "var(--p-surface-c)",
                                        color: "var(--p-text-color-secondary)",
                                        width: "2rem",
                                        height: "2rem",
                                        padding: "0"
                                    }
                                }, null, 8, [
                                    "icon"
                                ])
                            ], 2)),
                            (a(!0), v(G, null, le(A.value, ([e, d], K)=>(a(), v(G, {
                                    key: e.id
                                }, [
                                    p("div", it, [
                                        n(oe, {
                                            event: e,
                                            "parent-query-cell": t(s),
                                            class: L(d)
                                        }, null, 8, [
                                            "event",
                                            "parent-query-cell",
                                            "class"
                                        ])
                                    ]),
                                    te(e, K) ? (a(), v("div", {
                                        key: 0,
                                        class: L([
                                            "expand-thoughts-button",
                                            {
                                                expanded: t(S) === t(s)
                                            }
                                        ]),
                                        onClick: z
                                    }, [
                                        p("div", rt, [
                                            p("i", {
                                                class: L([
                                                    "pi pi-sparkles",
                                                    {
                                                        "animate-sparkles": Q.value === 1
                                                    }
                                                ]),
                                                style: {
                                                    color: "var(--p-yellow-500)",
                                                    "font-size": "1.25rem",
                                                    "margin-right": "0.6rem"
                                                }
                                            }, null, 2),
                                            X(" " + ne(U.value), 1)
                                        ]),
                                        n(t(M), {
                                            icon: t(S) === t(s) ? "pi pi-times" : "pi pi-search",
                                            text: "",
                                            rounded: "",
                                            style: {
                                                "background-color": "var(--p-surface-c)",
                                                color: "var(--p-text-color-secondary)",
                                                width: "2rem",
                                                height: "2rem",
                                                padding: "0"
                                            }
                                        }, null, 8, [
                                            "icon"
                                        ])
                                    ], 2)) : I("", !0)
                                ], 64))), 128)),
                            t(J)(t(r)) ? (a(), v("div", ct, [
                                n(oe, {
                                    event: t(s)?.events[t(s)?.events.length - 1],
                                    "parent-query-cell": t(s)
                                }, null, 8, [
                                    "event",
                                    "parent-query-cell"
                                ])
                            ])) : I("", !0)
                        ])
                    ])) : I("", !0),
                    t(s).status === "awaiting_input" ? V((a(), v("div", ut, [
                        p("div", pt, [
                            n(t(pe), null, {
                                default: u(()=>[
                                        n(t(we), null, {
                                            default: u(()=>[
                                                    ...o[6] || (o[6] = [
                                                        p("i", {
                                                            class: "pi pi-exclamation-triangle"
                                                        }, null, -1)
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        n(t(be), {
                                            placeholder: "Reply to the agent",
                                            onKeydown: [
                                                D(T(t(q), [
                                                    "exact",
                                                    "prevent"
                                                ]), [
                                                    "enter"
                                                ]),
                                                o[2] || (o[2] = D(T((e)=>e.target.blur(), [
                                                    "prevent",
                                                    "stop"
                                                ]), [
                                                    "escape"
                                                ])),
                                                o[3] || (o[3] = D(T(()=>{}, [
                                                    "ctrl",
                                                    "stop"
                                                ]), [
                                                    "enter"
                                                ])),
                                                o[4] || (o[4] = D(T(()=>{}, [
                                                    "shift",
                                                    "stop"
                                                ]), [
                                                    "enter"
                                                ]))
                                            ],
                                            autoFocus: "",
                                            modelValue: t(b),
                                            "onUpdate:modelValue": o[5] || (o[5] = (e)=>re(b) ? b.value = e : null)
                                        }, null, 8, [
                                            "onKeydown",
                                            "modelValue"
                                        ]),
                                        n(t(M), {
                                            icon: "pi pi-send",
                                            onClick: t(q)
                                        }, null, 8, [
                                            "onClick"
                                        ])
                                    ]),
                                _: 1
                            })
                        ])
                    ])), [
                        [
                            y
                        ]
                    ]) : I("", !0)
                ]);
            };
        }
    });
    mt = F({
        __name: "ChatQueryCellEvent",
        props: [
            "event",
            "parentQueryCell"
        ],
        setup ($) {
            const g = k(!1), _ = $, s = (i)=>{
                i.stopPropagation(), g.value = !g.value;
            };
            return (i, f)=>(a(), E(oe, {
                    event: _.event,
                    "parent-query-cell": _.parentQueryCell,
                    "code-styles": g.value ? "" : "code-cell-collapsed",
                    "should-hide-answered-questions": !0
                }, {
                    "code-cell-controls": u(()=>[
                            n(t(M), {
                                icon: g.value ? "pi pi-window-maximize" : "pi pi-window-minimize",
                                size: "small",
                                class: "code-cell-toggle-button",
                                onClick: T(s, [
                                    "stop"
                                ]),
                                title: g.value ? "Expand code cell" : "Shrink code cell"
                            }, null, 8, [
                                "icon",
                                "title"
                            ])
                        ]),
                    _: 1
                }, 8, [
                    "event",
                    "parent-query-cell",
                    "code-styles"
                ]));
        }
    });
    ht = {
        class: "thoughts-pane"
    };
    ft = {
        key: 0
    };
    gt = {
        key: 0
    };
    _t = {
        key: 1
    };
    yt = {
        key: 1,
        class: "thoughts-pane-content"
    };
    kt = {
        class: "pane-actions"
    };
    wt = {
        class: "events-scroll-container"
    };
    bt = {
        key: 0,
        class: "no-thoughts-message"
    };
    Ct = {
        key: 0,
        class: "progress-area"
    };
    xt = F({
        __name: "AgentActivityPane",
        props: {
            isChatEmpty: {
                type: Boolean
            }
        },
        emits: [
            "scrollToMessage"
        ],
        setup ($, { emit: g }) {
            const _ = g, s = $, i = P("activeQueryCell"), f = w(()=>!J(i.value?.events || [])), c = w(()=>i.value ? i.value?.events || [] : null), b = ()=>{
                _("scrollToMessage");
            }, h = w(()=>c.value ? c.value.filter((m)=>![
                        "user_answer",
                        "response"
                    ].includes(m.type)).map((m, C, N)=>{
                    const x = C === N.length - 1;
                    return m.type === "user_question" && x && f.value ? {
                        ...m,
                        waitForUserInput: !0
                    } : m;
                }) : []), r = w(()=>{
                if (!c.value || f.value) return !1;
                const m = c.value.length === 1 && c.value[0].type === "response";
                return i.value?.status === "idle" && m;
            });
            return (m, C)=>{
                const N = W("tooltip"), x = W("autoscroll");
                return a(), v("div", ht, [
                    t(i) ? (a(), v("div", yt, [
                        p("div", kt, [
                            V(n(t(M), {
                                icon: "pi pi-arrow-circle-right",
                                text: "",
                                onClick: b
                            }, null, 512), [
                                [
                                    N,
                                    "Scroll to related user message.",
                                    void 0,
                                    {
                                        bottom: !0
                                    }
                                ]
                            ])
                        ]),
                        V((a(), v("div", wt, [
                            r.value ? (a(), v("div", bt, [
                                ...C[1] || (C[1] = [
                                    p("em", null, "No agent activity from this query.", -1)
                                ])
                            ])) : (a(!0), v(G, {
                                key: 1
                            }, le(h.value, (q, B)=>(a(), E(mt, {
                                    key: `${B}-${t(i).id}`,
                                    event: q,
                                    "parent-query-cell": t(i)
                                }, null, 8, [
                                    "event",
                                    "parent-query-cell"
                                ]))), 128))
                        ])), [
                            [
                                x
                            ]
                        ]),
                        f.value ? (a(), v("div", Ct, [
                            n(t(Ce), {
                                mode: "indeterminate"
                            })
                        ])) : I("", !0)
                    ])) : (a(), v("div", ft, [
                        s.isChatEmpty ? (a(), v("span", gt, " Start a conversation to view Beaker's activity as you interact with it. ")) : (a(), v("em", _t, [
                            ...C[0] || (C[0] = [
                                X("Select ", -1),
                                p("i", {
                                    class: "pi pi-search magnifier-reference"
                                }, null, -1),
                                X(" agent activity from the conversation to view details.", -1)
                            ])
                        ]))
                    ]))
                ]);
            };
        }
    });
    $t = Ke(xt, [
        [
            "__scopeId",
            "data-v-26c0ca7c"
        ]
    ]);
    qt = {
        class: "chat-layout"
    };
    St = {
        class: "chat-container"
    };
    Rt = [
        "innerHTML"
    ];
    It = {
        key: 0,
        class: "spacer right"
    };
    Ut = F({
        __name: "ChatInterface",
        props: [
            "config",
            "connectionSettings",
            "sessionName",
            "sessionId",
            "defaultKernel",
            "renderers"
        ],
        setup ($) {
            const g = k(), _ = k(!1), { theme: s, toggleDarkMode: i } = P("theme"), f = P("beakerAppConfig");
            f.setPage("chat");
            const c = k(), b = k(), h = k([]), r = k(null), m = k(), C = k(), N = k(!1), x = w(()=>g?.value?.beakerSession), q = k({});
            se(x, async ()=>{
                q.value = await Oe(A);
            });
            const B = w(()=>(x.value?.session?.notebook?.cells ?? []).length === 0), S = w(()=>{
                const e = x.value?.session?.notebook?.cells ?? [];
                if (e.length == 0) return !1;
                const d = e[e.length - 1];
                return d?.cell_type === "query" && d?.status === "awaiting_input";
            }), H = ()=>{
                r.value = null;
            }, Y = ()=>{
                const e = document.querySelector(`[data-cell-id="${r.value?.id}"]`);
                e && e.scrollIntoView({
                    behavior: "smooth"
                });
            };
            se(r, (e)=>{
                if (!c.value) return;
                const d = !!c.value.getSelectedPanelInfo();
                e ? c.value.selectPanel("agent-actions") : d && c.value.hidePanel();
            });
            const U = w(()=>{
                const e = [
                    {
                        type: "button",
                        command: ()=>{
                            window.confirm("This will reset your entire session, clearing the notebook and removing any updates to the environment. Proceed?") && x.value.session.reset();
                        },
                        icon: "refresh",
                        label: "Reset Session"
                    }
                ];
                if (!f?.config?.pages || Object.hasOwn(f.config.pages, "notebook")) {
                    const d = "/" + (f?.config?.pages?.notebook?.default ? "" : "notebook") + window.location.search;
                    e.push({
                        type: "link",
                        href: d,
                        component: Fe,
                        componentStyle: {
                            fill: "currentColor",
                            stroke: "currentColor",
                            height: "1rem",
                            width: "1rem"
                        },
                        label: "Navigate to notebook view"
                    });
                }
                return e.push({
                    type: "button",
                    icon: s.mode === "dark" ? "sun" : "moon",
                    command: i,
                    label: `Switch to ${s.mode === "dark" ? "light" : "dark"} mode.`
                }, {
                    type: "link",
                    href: "https://jataware.github.io/beaker-kernel",
                    label: "Beaker Documentation",
                    icon: "book",
                    rel: "noopener",
                    target: "_blank"
                }, {
                    type: "link",
                    href: "https://github.com/jataware/beaker-kernel",
                    label: "Check us out on Github",
                    icon: "github",
                    rel: "noopener",
                    target: "_blank"
                }), e;
            }), z = (e)=>{
                x.value?.session.loadNotebook(e);
            }, Q = new URLSearchParams(window.location.search), A = Q.has("session") ? Q.get("session") : "chat_dev_session", O = $, Z = [
                ...je.map((e)=>new Re(e)).map(Ie),
                qe,
                Se
            ], ee = {
                code: Be,
                markdown: Ve,
                query: vt,
                raw: Te
            }, te = k("connecting"), l = (e)=>{
                e.header.msg_type === "preview" ? b.value = e.content : e.header.msg_type === "debug_event" ? h.value.push({
                    type: e.content.event,
                    body: e.content.body,
                    timestamp: e.header.date
                }) : e.header.msg_type === "chat_history" && (m.value = e.content);
            }, o = (e)=>{
                te.value = e == "idle" ? "connected" : e;
            }, y = async ()=>{
                await x.value.session.sendBeakerMessage("reset_request", {});
            };
            return xe("activeQueryCell", r), (e, d)=>{
                const K = W("autoscroll");
                return a(), E(Me, {
                    title: e.$tmpl._("short_title", "Beaker Chat"),
                    ref_key: "beakerInterfaceRef",
                    ref: g,
                    "header-nav": U.value,
                    connectionSettings: O.config,
                    sessionId: t(A),
                    defaultKernel: "beaker_kernel",
                    renderers: Z,
                    onSessionStatusChanged: o,
                    onIopubMsg: l,
                    onOpenFile: z,
                    "style-overrides": [
                        "chat"
                    ],
                    pageClass: "chat-interface"
                }, {
                    "left-panel": u(()=>[
                            n(ue, {
                                position: "left",
                                highlight: "line",
                                expanded: !1,
                                initialWidth: "25vi",
                                maximized: _.value
                            }, {
                                default: u(()=>[
                                        n(R, {
                                            label: "Context Info",
                                            icon: "pi pi-home"
                                        }, {
                                            default: u(()=>[
                                                    n(Ae)
                                                ]),
                                            _: 1
                                        }),
                                        n(R, {
                                            id: "files",
                                            label: "Files",
                                            icon: "pi pi-folder",
                                            "no-overflow": "",
                                            lazy: !0
                                        }, {
                                            default: u(()=>[
                                                    n(Pe, {
                                                        ref: "filePanelRef",
                                                        onOpenFile: z,
                                                        onPreviewFile: d[0] || (d[0] = (j, me)=>{
                                                            C.value = {
                                                                url: j,
                                                                mimetype: me
                                                            }, N.value = !0, c.value.selectPanel("file-contents");
                                                        })
                                                    }, null, 512)
                                                ]),
                                            _: 1
                                        }),
                                        n(R, {
                                            icon: "pi pi-comments",
                                            label: "Chat History"
                                        }, {
                                            default: u(()=>[
                                                    n(t(De), {
                                                        "chat-history": m.value
                                                    }, null, 8, [
                                                        "chat-history"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        Object.keys(q.value).length > 0 ? (a(), E(R, {
                                            key: 0,
                                            id: "integrations",
                                            label: "Integrations",
                                            icon: "pi pi-database"
                                        }, {
                                            default: u(()=>[
                                                    n(Ue, {
                                                        modelValue: q.value,
                                                        "onUpdate:modelValue": d[1] || (d[1] = (j)=>q.value = j)
                                                    }, null, 8, [
                                                        "modelValue"
                                                    ])
                                                ]),
                                            _: 1
                                        })) : I("", !0),
                                        O.config.config_type !== "server" ? (a(), E(R, {
                                            key: 1,
                                            id: "config",
                                            label: `${e.$tmpl._("short_title", "Beaker")} Config`,
                                            icon: "pi pi-cog",
                                            lazy: !0,
                                            position: "bottom"
                                        }, {
                                            default: u(()=>[
                                                    n(Ne, {
                                                        ref: "configPanelRef",
                                                        onRestartSession: y
                                                    }, null, 512)
                                                ]),
                                            _: 1
                                        }, 8, [
                                            "label"
                                        ])) : I("", !0)
                                    ]),
                                _: 1
                            }, 8, [
                                "maximized"
                            ])
                        ]),
                    "right-panel": u(()=>[
                            n(ue, {
                                ref_key: "rightSideMenuRef",
                                ref: c,
                                position: "right",
                                highlight: "line",
                                expanded: !0,
                                "initial-width": "35vw",
                                onPanelHide: H
                            }, {
                                default: u(()=>[
                                        n(R, {
                                            label: "Agent Activity",
                                            id: "agent-actions",
                                            icon: "pi pi-lightbulb",
                                            position: "top",
                                            selected: !0
                                        }, {
                                            default: u(()=>[
                                                    n($t, {
                                                        onScrollToMessage: Y,
                                                        "is-chat-empty": B.value
                                                    }, null, 8, [
                                                        "is-chat-empty"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        n(R, {
                                            label: "Preview",
                                            icon: "pi pi-eye",
                                            "no-overflow": ""
                                        }, {
                                            default: u(()=>[
                                                    n(ze, {
                                                        previewData: b.value
                                                    }, null, 8, [
                                                        "previewData"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        n(R, {
                                            id: "file-contents",
                                            label: "File Contents",
                                            icon: "pi pi-file beaker-zoom",
                                            "no-overflow": ""
                                        }, {
                                            default: u(()=>[
                                                    n(He, {
                                                        url: C.value?.url,
                                                        mimetype: C.value?.mimetype
                                                    }, null, 8, [
                                                        "url",
                                                        "mimetype"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        n(R, {
                                            id: "media",
                                            label: "Graphs and Images",
                                            icon: "pi pi-chart-bar",
                                            "no-overflow": ""
                                        }, {
                                            default: u(()=>[
                                                    n(Qe)
                                                ]),
                                            _: 1
                                        }),
                                        n(R, {
                                            id: "kernel-logs",
                                            label: "Logs",
                                            icon: "pi pi-list",
                                            position: "bottom"
                                        }, {
                                            default: u(()=>[
                                                    V(n(Ee, {
                                                        entries: h.value,
                                                        onClearLogs: d[2] || (d[2] = (j)=>h.value.splice(0, h.value.length))
                                                    }, null, 8, [
                                                        "entries"
                                                    ]), [
                                                        [
                                                            K
                                                        ]
                                                    ])
                                                ]),
                                            _: 1
                                        })
                                    ]),
                                _: 1
                            }, 512)
                        ]),
                    default: u(()=>[
                            p("div", qt, [
                                p("div", St, [
                                    V((a(), E(Ye, {
                                        "cell-map": ee
                                    }, {
                                        "help-text": u(()=>[
                                                p("div", {
                                                    innerHTML: e.$tmpl._("chat_welcome_html", `
                                <p>Hi! I'm your Beaker Agent and I can help you do programming and software engineering tasks.</p>
                                <p>Feel free to ask me about whatever the context specializes in..</p>
                                <p>
                                    On top of answering questions, I can actually run code in a python environment, and evaluate the results.
                                    This lets me do some pretty awesome things like: web scraping, or plotting and exploring data.
                                    Just shoot me a message when you're ready to get started.
                                </p>
                            `)
                                                }, null, 8, Rt)
                                            ]),
                                        "notebook-background": u(()=>[
                                                ...d[3] || (d[3] = [
                                                    p("div", {
                                                        class: "welcome-placeholder"
                                                    }, null, -1)
                                                ])
                                            ]),
                                        _: 1
                                    })), [
                                        [
                                            K
                                        ]
                                    ]),
                                    V(n(Je, {
                                        class: "agent-query-container agent-query-container-chat",
                                        placeholder: e.$tmpl._("agent_query_prompt", "Message to the agent")
                                    }, null, 8, [
                                        "placeholder"
                                    ]), [
                                        [
                                            de,
                                            !S.value
                                        ]
                                    ])
                                ]),
                                _.value ? I("", !0) : (a(), v("div", It))
                            ])
                        ]),
                    _: 1
                }, 8, [
                    "title",
                    "header-nav",
                    "connectionSettings",
                    "sessionId"
                ]);
            };
        }
    });
});
export { Ut as default, __tla };
