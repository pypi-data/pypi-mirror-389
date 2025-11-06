import { d as O, i as P, f as R, x as X, y as Y, z as Z, R as ee, A as o, o as l, B as n, G as c, S as g, a5 as S, u as e, H as i, a6 as te, a7 as T, N as q, J as M, j as m, aq as se, I as k, K as v, V as N, W as A, ar as ne, M as re, a9 as le, a as h, w as _, a2 as ae } from "./primevue-BhybIXDC.js";
import { i as D, _ as x, __tla as __tla_0 } from "./cellOperations-C51nPkhh.js";
import { d as oe, __tla as __tla_1 } from "./BeakerRawCell.vue_vue_type_style_index_0_lang-OdsdCFW2.js";
import { T as I } from "./BrainIcon-Cg6sqKva.js";
import { u as ie } from "./BaseQueryCell-5qJKeHAI.js";
import { h as ue, __tla as __tla_2 } from "./renderers-707ItvV_.js";
let Te;
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
    })()
]).then(async ()=>{
    let ce, pe, de, ye, me, ve, he, _e, fe, ge, qe, ke, xe, we, Ce, be;
    ce = {
        class: "llm-query-cell"
    };
    pe = {
        class: "llm-prompt-container"
    };
    de = {
        class: "prompt-input-container"
    };
    ye = {
        class: "prompt-controls",
        style: {}
    };
    me = {
        key: 0,
        class: "event-container"
    };
    ve = {
        class: "events"
    };
    he = {
        key: 0,
        class: "query-steps"
    };
    _e = {
        class: "query-header-content"
    };
    fe = {
        class: "font-bold white-space-nowrap"
    };
    ge = {
        style: {
            display: "flex",
            "flex-direction": "column"
        }
    };
    qe = {
        key: 2,
        class: "query-answer"
    };
    ke = {
        key: 1,
        class: "thinking-indicator"
    };
    xe = {
        class: "thought-icon",
        style: {
            "margin-right": "0.25rem"
        }
    };
    we = {
        key: 2,
        class: "input-request"
    };
    Ce = {
        class: "input-request-wrapper"
    };
    be = {
        modelClass: ue,
        icon: "pi pi-sparkles"
    };
    Te = O({
        ...be,
        __name: "BeakerQueryCell",
        props: [
            "index",
            "cell"
        ],
        setup (Q, { expose: U }) {
            const w = Q, { cell: a, isEditing: p, promptEditorMinHeight: C, promptText: d, response: f, textarea: b, events: u, execute: V, enter: H, exit: K, clear: z, respond: $ } = ie(w), F = {
                code_cell: "pi pi-code",
                thought: "thought-icon",
                user_answer: "pi pi-reply",
                user_question: "pi pi-question-circle"
            }, B = P("beakerSession"), j = Y(), L = R(()=>w.cell?.events?.filter((r)=>[
                        "user_question",
                        "user_answer"
                    ].includes(r.type)).map((r)=>{
                    let t;
                    return r.type === "user_question" ? t = "query-answer-chat query-answer-chat-override" : t = "llm-prompt-container llm-prompt-container-chat llm-prompt-text llm-prompt-text-chat", [
                        r,
                        t
                    ];
                })), E = R({
                get () {
                    const r = u.value.length;
                    return r === 0 ? [] : r === 1 ? [
                        0
                    ] : [
                        r - 2,
                        r - 1
                    ];
                },
                set (r) {}
            }), G = {
                thought: "Thought",
                response: "Final Response",
                code_cell: "Code",
                user_answer: "Answer",
                user_question: "Question",
                error: "Error",
                abort: "Abort"
            }, J = (r)=>{
                p.value || (C.value = r.target.clientHeight, p.value = !0);
            };
            return U({
                execute: V,
                enter: H,
                exit: K,
                clear: z,
                cell: a,
                editor: b
            }), X(()=>{
                B.cellRegistry[a.value.id] = j.vnode;
            }), Z(()=>{
                delete B.cellRegistry[a.value.id];
            }), (r, t)=>{
                const W = ee("focustrap");
                return l(), o("div", ce, [
                    n("div", {
                        class: "query",
                        onDblclick: J
                    }, [
                        t[7] || (t[7] = n("div", {
                            class: "query-steps"
                        }, "User Query:", -1)),
                        n("div", pe, [
                            g(n("div", de, [
                                i(oe, {
                                    ref_key: "textarea",
                                    ref: b,
                                    class: "prompt-input",
                                    modelValue: e(d),
                                    "onUpdate:modelValue": t[0] || (t[0] = (s)=>T(d) ? d.value = s : null),
                                    style: te({
                                        minHeight: `${e(C)}px`
                                    })
                                }, null, 8, [
                                    "modelValue",
                                    "style"
                                ]),
                                n("div", ye, [
                                    i(e(q), {
                                        label: "Submit",
                                        onClick: e(V)
                                    }, null, 8, [
                                        "onClick"
                                    ]),
                                    i(e(q), {
                                        label: "Cancel",
                                        onClick: t[1] || (t[1] = (s)=>{
                                            d.value = e(a).source, p.value = !1;
                                        })
                                    })
                                ])
                            ], 512), [
                                [
                                    S,
                                    e(p)
                                ]
                            ]),
                            g(n("div", {
                                class: "llm-prompt-text"
                            }, M(e(a).source), 513), [
                                [
                                    S,
                                    !e(p)
                                ]
                            ])
                        ])
                    ], 32),
                    e(u).length > 0 || e(D)(e(u)) ? (l(), o("div", me, [
                        n("div", ve, [
                            e(u).length > 0 ? (l(), o("div", he, " Agent actions: ")) : c("", !0),
                            e(u).length > 0 ? (l(), m(e(se), {
                                key: 1,
                                multiple: !0,
                                class: k("query-accordion"),
                                "active-index": E.value,
                                "onUpdate:activeIndex": t[2] || (t[2] = (s)=>E.value = s)
                            }, {
                                default: v(()=>[
                                        (l(!0), o(N, null, A(e(u), (s, y)=>(l(), m(e(ne), {
                                                key: y,
                                                pt: {
                                                    header: {
                                                        class: [
                                                            "query-tab",
                                                            `query-tab-${s.type}`
                                                        ]
                                                    },
                                                    headerAction: {
                                                        class: [
                                                            "query-tab-headeraction",
                                                            `query-tab-headeraction-${s.type}`
                                                        ]
                                                    },
                                                    content: {
                                                        class: [
                                                            `query-tab-content-${s.type}`
                                                        ]
                                                    },
                                                    headerIcon: {
                                                        class: [
                                                            `query-tab-icon-${s.type}`
                                                        ]
                                                    }
                                                }
                                            }, {
                                                header: v(()=>[
                                                        n("span", _e, [
                                                            n("span", {
                                                                class: k(F[s.type])
                                                            }, [
                                                                s.type === "thought" ? (l(), m(I, {
                                                                    key: 0,
                                                                    class: "thought-icon"
                                                                })) : c("", !0)
                                                            ], 2),
                                                            n("span", fe, M(G[s.type]), 1)
                                                        ])
                                                    ]),
                                                default: v(()=>[
                                                        (l(), m(x, {
                                                            key: y,
                                                            event: s,
                                                            "parent-query-cell": e(a)
                                                        }, null, 8, [
                                                            "event",
                                                            "parent-query-cell"
                                                        ]))
                                                    ]),
                                                _: 2
                                            }, 1032, [
                                                "pt"
                                            ]))), 128))
                                    ]),
                                _: 1
                            }, 8, [
                                "active-index"
                            ])) : c("", !0),
                            (l(!0), o(N, null, A(L.value, ([s, y])=>(l(), o("div", {
                                    key: s.id
                                }, [
                                    n("div", ge, [
                                        i(x, {
                                            event: s,
                                            "parent-query-cell": e(a),
                                            class: k(y)
                                        }, null, 8, [
                                            "event",
                                            "parent-query-cell",
                                            "class"
                                        ])
                                    ])
                                ]))), 128)),
                            e(D)(e(u)) ? (l(), o("div", qe, [
                                t[8] || (t[8] = n("h3", {
                                    class: "query-steps"
                                }, "Result", -1)),
                                i(x, {
                                    event: e(a)?.events[e(a)?.events.length - 1],
                                    "parent-query-cell": e(a)
                                }, null, 8, [
                                    "event",
                                    "parent-query-cell"
                                ])
                            ])) : c("", !0)
                        ])
                    ])) : c("", !0),
                    e(a).status === "busy" ? (l(), o("div", ke, [
                        n("span", xe, [
                            i(I)
                        ]),
                        t[9] || (t[9] = re(" Thinking ", -1)),
                        t[10] || (t[10] = n("span", {
                            class: "thinking-animation"
                        }, null, -1))
                    ])) : c("", !0),
                    e(a).status === "awaiting_input" ? g((l(), o("div", we, [
                        n("div", Ce, [
                            i(e(ae), null, {
                                default: v(()=>[
                                        i(e(le), {
                                            placeholder: "Reply to the agent",
                                            onKeydown: [
                                                h(_(e($), [
                                                    "exact",
                                                    "prevent"
                                                ]), [
                                                    "enter"
                                                ]),
                                                t[3] || (t[3] = h(_((s)=>s.target.blur(), [
                                                    "prevent",
                                                    "stop"
                                                ]), [
                                                    "escape"
                                                ])),
                                                t[4] || (t[4] = h(_(()=>{}, [
                                                    "ctrl",
                                                    "stop"
                                                ]), [
                                                    "enter"
                                                ])),
                                                t[5] || (t[5] = h(_(()=>{}, [
                                                    "shift",
                                                    "stop"
                                                ]), [
                                                    "enter"
                                                ]))
                                            ],
                                            autoFocus: "",
                                            modelValue: e(f),
                                            "onUpdate:modelValue": t[6] || (t[6] = (s)=>T(f) ? f.value = s : null)
                                        }, null, 8, [
                                            "onKeydown",
                                            "modelValue"
                                        ]),
                                        i(e(q), {
                                            icon: "pi pi-send",
                                            onClick: e($)
                                        }, null, 8, [
                                            "onClick"
                                        ])
                                    ]),
                                _: 1
                            })
                        ])
                    ])), [
                        [
                            W
                        ]
                    ]) : c("", !0)
                ]);
            };
        }
    });
});
export { Te as _, __tla };
