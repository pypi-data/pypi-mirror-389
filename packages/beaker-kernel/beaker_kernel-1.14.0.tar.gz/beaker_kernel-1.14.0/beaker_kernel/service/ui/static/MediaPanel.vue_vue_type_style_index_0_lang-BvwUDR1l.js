import { d as E, r as S, i as U, f, R as A, A as p, o as d, H as g, K as y, S as w, M as b, J as v, B as t, u as m, X as G, G as x, V as B, W, Q as q, O as K, j as O, a4 as J, ab as Q, ac as X, a6 as T, ad as Y, ae as Z, N as L, a2 as ee, a8 as V, af as te, ag as se } from "./primevue-BhybIXDC.js";
import { i as oe, __tla as __tla_0 } from "./renderers-707ItvV_.js";
let Be, Ke, Ve;
let __tla = Promise.all([
    (()=>{
        try {
            return __tla_0;
        } catch  {}
    })()
]).then(async ()=>{
    let ae, le, ne, re, ie, de, ue, ce, pe, me, ve, ge, ye, _e, he, fe, be, ke, we, xe, $e, Ce, He, Me, Te, Se, Pe, Ue, Le, Ee, Ne, ze, Ae;
    ae = {
        class: "info-panel-container"
    };
    le = {
        style: {
            cursor: "help",
            "border-bottom": "1px dotted var(--p-text-color-secondary)"
        }
    };
    Ke = E({
        __name: "InfoPanel",
        setup (C) {
            S(!0);
            const l = S({
                0: !0,
                1: !0,
                2: !0,
                3: !0,
                5: !0
            }), u = U("beakerSession"), c = f(()=>{
                const n = u?.activeContext, o = u?.session.kernelInfo;
                return {
                    ...n,
                    kernelInfo: o
                };
            }), _ = f(()=>{
                const n = c.value;
                if (!n) return [];
                const o = [
                    {
                        key: "0",
                        label: "Kernel",
                        icon: "pi pi-fw pi-cog",
                        expanded: !0,
                        children: [
                            {
                                key: "0-1",
                                label: `${n?.info?.subkernel} (${n?.info?.language})`
                            }
                        ]
                    }
                ];
                if (n?.info?.workflow_info && Object.keys(n?.info?.workflow_info?.workflows ?? []).length > 0) {
                    const { workflows: r, state: s } = n.info.workflow_info;
                    o.push({
                        key: "5",
                        label: "Workflows",
                        icon: "pi pi-fw pi-list-check",
                        expanded: !0,
                        children: Object.keys(r).map((a)=>({
                                key: `5-${a}`,
                                label: `${r[a].title}${s?.workflow_id === a ? " (Active)" : ""}`
                            }))
                    });
                }
                return o.push({
                    key: "3",
                    label: "Tools",
                    icon: "pi pi-fw pi-wrench",
                    expanded: !0,
                    children: Object.keys(n?.info?.agent?.tools || {}).map((r, s)=>({
                            key: `3-${s}`,
                            label: r.replace("PyPackageAgent.", ""),
                            data: n.info.agent.tools[r],
                            type: "tool"
                        }))
                }), o;
            });
            return (n, o)=>{
                const r = A("tooltip");
                return d(), p("div", ae, [
                    g(m(G), {
                        value: _.value,
                        loading: !_.value,
                        expandedKeys: l.value,
                        "onUpdate:expandedKeys": o[1] || (o[1] = (s)=>l.value = s),
                        pt: {
                            root: {
                                class: "context-tree"
                            },
                            nodeContent: {
                                style: {
                                    padding: "0"
                                }
                            }
                        }
                    }, {
                        loadingicon: y(()=>[
                                ...o[2] || (o[2] = [
                                    t("div", {
                                        class: "loading-area"
                                    }, " No Context Loaded. ", -1)
                                ])
                            ]),
                        action: y((s)=>[
                                w((d(), p("div", {
                                    onMousedown: o[0] || (o[0] = (a)=>{
                                        a.detail > 1 && a.preventDefault();
                                    }),
                                    style: {
                                        cursor: "pointer",
                                        "border-bottom": "1px dotted var(--p-text-color-secondary)"
                                    }
                                }, [
                                    b(v(s.node.label), 1)
                                ], 32)), [
                                    [
                                        r,
                                        {
                                            value: `${s.node.data}`,
                                            pt: {
                                                text: {
                                                    style: {
                                                        width: "20rem"
                                                    }
                                                },
                                                root: {
                                                    style: {
                                                        marginLeft: "1rem"
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                ])
                            ]),
                        tool: y((s)=>[
                                w((d(), p("span", le, [
                                    b(v(s.node.label), 1)
                                ])), [
                                    [
                                        r,
                                        {
                                            value: `${s.node.data}`,
                                            pt: {
                                                text: {
                                                    style: {
                                                        width: "20rem"
                                                    }
                                                },
                                                root: {
                                                    style: {
                                                        marginLeft: "1rem"
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                ])
                            ]),
                        _: 1
                    }, 8, [
                        "value",
                        "loading",
                        "expandedKeys"
                    ])
                ]);
            };
        }
    });
    ne = {
        class: "chat-history-message"
    };
    re = {
        class: "chat-history-message-title"
    };
    ie = {
        style: {
            "font-weight": "500"
        }
    };
    de = {
        key: 0,
        class: "chat-history-message-tool-use pi pi-hammer"
    };
    ue = {
        class: "chat-history-message-title-token-count"
    };
    ce = {
        key: 0,
        class: "message-text monospace"
    };
    pe = {
        key: 1,
        class: "toolcall-info"
    };
    me = {
        class: "tool-call-title"
    };
    ve = {
        class: "monospace"
    };
    ge = E({
        __name: "ChatHistoryMessage",
        props: [
            "record",
            "idx",
            "tool-call-message"
        ],
        setup (C) {
            const l = C, u = S(!0), c = f(()=>l.record?.message), _ = (n)=>n && n.replace(/(?<edge>[-_]|\b)(?<letter>.)/g, (o, r, s, a, k, $)=>s.toUpperCase());
            return (n, o)=>{
                const r = A("tooltip");
                return d(), p("div", ne, [
                    g(m(Y), {
                        class: "chat-history-message-panel",
                        toggleable: !0,
                        style: T({
                            collapsed: u.value
                        }),
                        onToggle: o[2] || (o[2] = (s)=>u.value = !u.value),
                        pt: {
                            contentContainer: ({ state: s })=>(s.d_collapsed = !1, u.value ? "collapsed" : void 0)
                        }
                    }, {
                        header: y(()=>[
                                t("div", {
                                    class: "chat-history-message-header-container",
                                    onClick: o[0] || (o[0] = (s)=>u.value = !u.value)
                                }, [
                                    t("div", re, [
                                        t("span", ie, v(_(c.value?.type)) + "Message ", 1),
                                        c.value?.type.toLowerCase() === "ai" && c.value?.tool_calls ? w((d(), p("span", de, null, 512)), [
                                            [
                                                r,
                                                `Tool${c.value.tool_calls.length > 1 ? "s" : ""} called: ` + c.value.tool_calls.map((s)=>`'${s.name}'`).join(", ")
                                            ]
                                        ]) : x("", !0)
                                    ]),
                                    t("span", ue, v((C.record?.token_count / 1e3).toFixed(2)) + "k tokens ", 1)
                                ])
                            ]),
                        togglericon: y(()=>[
                                (d(), O(J(u.value ? m(Q) : m(X))))
                            ]),
                        default: y(()=>[
                                t("div", null, [
                                    c.value.text.trim() ? (d(), p("div", ce, v(c.value?.text.trim()), 1)) : x("", !0),
                                    c.value?.type === "ai" && c.value?.tool_calls?.length > 0 ? (d(), p("div", pe, [
                                        (d(!0), p(B, null, W(c.value?.tool_calls, (s)=>(d(), p("div", {
                                                key: s.id
                                            }, [
                                                t("div", me, [
                                                    o[3] || (o[3] = b(" Tool:   ", -1)),
                                                    t("span", ve, v(s.name), 1)
                                                ]),
                                                o[4] || (o[4] = t("div", null, " Arguments: ", -1)),
                                                g(m(q), {
                                                    showGridlines: "",
                                                    stripedRows: "",
                                                    class: "chat-history-datatable",
                                                    value: Object.entries(s?.args).map(([a, k])=>({
                                                            key: a,
                                                            value: k
                                                        }))
                                                }, {
                                                    default: y(()=>[
                                                            g(m(K), {
                                                                field: "key"
                                                            }),
                                                            g(m(K), {
                                                                field: "value"
                                                            })
                                                        ]),
                                                    _: 1
                                                }, 8, [
                                                    "value"
                                                ])
                                            ]))), 128))
                                    ])) : x("", !0)
                                ]),
                                u.value ? (d(), p("div", {
                                    key: 0,
                                    class: "expand",
                                    onClick: o[1] || (o[1] = (s)=>u.value = !1)
                                }, "Click to expand")) : x("", !0)
                            ]),
                        _: 1
                    }, 8, [
                        "style",
                        "pt"
                    ])
                ]);
            };
        }
    });
    ye = {
        class: "chat-history-panel"
    };
    _e = {
        class: "chat-history-model"
    };
    he = {
        class: "model-info"
    };
    fe = {
        class: "model-specs",
        style: {
            display: "grid",
            "grid-template-columns": "max-content auto",
            "column-gap": "1rem",
            "row-gap": "0.5rem"
        }
    };
    be = {
        key: 0,
        class: "model-spec-label"
    };
    ke = {
        key: 1
    };
    we = {
        class: "context-window-usage"
    };
    xe = {
        class: "progress-bar-container"
    };
    $e = {
        class: "progress-bar"
    };
    Ce = {
        style: {
            width: "100%",
            position: "absolute",
            top: "1%",
            "text-align": "center"
        }
    };
    He = {
        class: "progress-bar-map"
    };
    Me = {
        class: "progress-bar-map-row overhead"
    };
    Te = {
        class: "progress-bar-map-row summary"
    };
    Se = {
        class: "progress-bar-map-row message"
    };
    Pe = {
        class: "progress-bar-map-row total"
    };
    Ue = {
        key: 0,
        class: "add-message-section"
    };
    Le = {
        class: "add-message-input"
    };
    Ee = {
        class: "add-message-actions"
    };
    Ne = {
        class: "chat-history-records"
    };
    Ve = E({
        __name: "ChatHistoryPanel",
        props: {
            chatHistory: {}
        },
        setup (C) {
            const l = C, u = S(!1), c = S(""), _ = U("beakerSession"), n = U("show_toast"), o = async ()=>{
                (await _.session.executeAction("set_user_preamble", {
                    message_text: ""
                }).done)?.content?.status === "ok" ? (c.value = "", n({
                    title: "Upload complete",
                    detail: "Preamble message cleared",
                    severity: "success",
                    life: 4e3
                })) : n({
                    title: "Upload complete",
                    detail: "Error clearing preamble message.",
                    severity: "error",
                    life: 4e3
                });
            }, r = async ()=>{
                if (c.value.trim() && _?.session) {
                    const e = await _.session.executeAction("set_user_preamble", {
                        message_text: c.value.trim()
                    }).done;
                    console.log({
                        response: e
                    }), e?.content?.status === "ok" ? (c.value = "", n({
                        title: "Upload complete",
                        detail: "Preamble message set.",
                        severity: "success",
                        life: 4e3
                    })) : n({
                        title: "Upload complete",
                        detail: "Error setting preamble message.",
                        severity: "error",
                        life: 4e3
                    });
                }
            }, s = f(()=>{
                const i = l.chatHistory?.model?.context_window, e = l.chatHistory?.token_estimate;
                if (i && e) {
                    const h = e / i;
                    return Math.round(h * 1e3) / 10;
                } else return null;
            }), a = f(()=>l.chatHistory?.model?.context_window), k = f(()=>Math.round(l.chatHistory?.overhead_token_count / a.value * 1e3) / 10), $ = f(()=>Math.round(l.chatHistory?.message_token_count / a.value * 1e3) / 10), N = f(()=>Math.round(l.chatHistory?.summary_token_count / a.value * 1e3) / 10), z = f({
                get () {
                    return Math.round(l.chatHistory?.summarization_threshold / a.value * 1e3) / 10;
                },
                set (i) {
                    console.log(i);
                }
            }), j = f(()=>l.chatHistory?.overhead_token_count + l.chatHistory?.message_token_count + l.chatHistory?.summary_token_count), D = f(()=>{
                const i = j.value, e = M(H(i)), h = M(H(a.value));
                return `${s.value?.toLocaleString()}% (~ ${e} / ${h})`;
            }), F = (i)=>l.chatHistory?.records?.map((e)=>e.message).find((e)=>e.type === "ai" && e.tool_calls?.map((h)=>h.id).includes(i)), I = (i)=>{
                if (i?.message?.tool_call_id) return F(i.message.tool_call_id);
            }, H = (i)=>Math.round(i / 500) * .5, M = (i)=>{
                let e = "k", h = i.toLocaleString();
                return i >= 1e3 && (e = "M", h = (i / 1e3).toFixed(2)), `${h.toLocaleString()}${e}`;
            };
            return (i, e)=>{
                const h = A("tooltip");
                return d(), p("div", ye, [
                    t("div", _e, [
                        t("div", he, [
                            e[3] || (e[3] = t("h4", null, "Current model", -1)),
                            t("div", fe, [
                                e[1] || (e[1] = t("div", {
                                    class: "model-spec-label"
                                }, "Model Provider:", -1)),
                                t("div", null, v(l.chatHistory?.model?.provider), 1),
                                e[2] || (e[2] = t("div", {
                                    class: "model-spec-label"
                                }, "Model Name:", -1)),
                                t("div", null, v(l.chatHistory?.model?.model_name), 1),
                                l.chatHistory?.model?.context_window ? (d(), p("div", be, "Context window:")) : x("", !0),
                                l.chatHistory?.model?.context_window ? (d(), p("div", ke, v(l.chatHistory?.model?.context_window.toLocaleString()) + " tokens", 1)) : x("", !0)
                            ])
                        ])
                    ]),
                    t("div", we, [
                        e[12] || (e[12] = t("h4", null, "Context window usage", -1)),
                        t("div", xe, [
                            t("div", $e, [
                                t("span", {
                                    class: "progress-bar-usage overhead",
                                    style: T({
                                        width: `${k.value}%`
                                    })
                                }, null, 4),
                                t("span", {
                                    class: "progress-bar-usage summary",
                                    style: T({
                                        width: `${N.value}%`
                                    })
                                }, null, 4),
                                t("span", {
                                    class: "progress-bar-usage message",
                                    style: T({
                                        width: `${$.value}%`
                                    })
                                }, null, 4)
                            ]),
                            t("div", {
                                style: T([
                                    {
                                        width: "2px",
                                        height: "100%",
                                        "background-color": "var(--p-orange-600)",
                                        position: "absolute",
                                        top: "0"
                                    },
                                    {
                                        left: `${z.value}%`
                                    }
                                ])
                            }, null, 4),
                            t("div", {
                                style: T([
                                    {
                                        width: "2px",
                                        height: "100%",
                                        "background-color": "var(--p-red-600)",
                                        position: "absolute",
                                        top: "0"
                                    },
                                    {
                                        left: "85%"
                                    }
                                ])
                            }),
                            t("div", Ce, v(D.value), 1)
                        ]),
                        t("div", He, [
                            w((d(), p("div", Me, [
                                e[4] || (e[4] = t("span", {
                                    class: "progress-bar-map-circle overhead"
                                }, null, -1)),
                                e[5] || (e[5] = b(" Estimated token overhead: ", -1)),
                                t("span", null, v(M(H(i.chatHistory?.overhead_token_count))), 1)
                            ])), [
                                [
                                    h,
                                    "Tokens used in tool definitions, subkernel state, etc. (estimated)"
                                ]
                            ]),
                            w((d(), p("div", Te, [
                                e[6] || (e[6] = t("span", {
                                    class: "progress-bar-map-circle summary"
                                }, null, -1)),
                                e[7] || (e[7] = b(" Estimated summarized token usage: ", -1)),
                                t("span", null, v(M(H(i.chatHistory?.summary_token_count))), 1)
                            ])), [
                                [
                                    h,
                                    "Token used by summaries. (estimated)"
                                ]
                            ]),
                            w((d(), p("div", Se, [
                                e[8] || (e[8] = t("span", {
                                    class: "progress-bar-map-circle message"
                                }, null, -1)),
                                e[9] || (e[9] = b(" Estimated message token usage: ", -1)),
                                t("span", null, v(M(H(i.chatHistory?.message_token_count))), 1)
                            ])), [
                                [
                                    h,
                                    "Tokens used by all unsummarized messages. (estimated)"
                                ]
                            ]),
                            w((d(), p("div", Pe, [
                                e[10] || (e[10] = t("span", {
                                    class: "progress-bar-map-circle total"
                                }, null, -1)),
                                e[11] || (e[11] = b(" Estimated total token usage: ", -1)),
                                t("span", null, v(M(H(j.value))), 1)
                            ])), [
                                [
                                    h,
                                    "Total tokens of current conversational history, favoring summaries. (estimated)"
                                ]
                            ])
                        ])
                    ]),
                    e[15] || (e[15] = t("h4", null, "Messages", -1)),
                    u.value ? (d(), p("div", Ue, [
                        t("div", Le, [
                            w(t("textarea", {
                                "onUpdate:modelValue": e[0] || (e[0] = (P)=>c.value = P),
                                placeholder: "Add a preamble message to chat history...",
                                rows: "3",
                                class: "message-textarea"
                            }, null, 512), [
                                [
                                    Z,
                                    c.value
                                ]
                            ])
                        ]),
                        t("div", Ee, [
                            g(m(L), {
                                onClick: o,
                                severity: "danger"
                            }, {
                                default: y(()=>[
                                        ...e[13] || (e[13] = [
                                            b(" Clear Message ", -1)
                                        ])
                                    ]),
                                _: 1
                            }),
                            g(m(L), {
                                onClick: r,
                                disabled: !c.value.trim(),
                                class: "save-message-btn",
                                severity: "success"
                            }, {
                                default: y(()=>[
                                        ...e[14] || (e[14] = [
                                            b(" Save Message ", -1)
                                        ])
                                    ]),
                                _: 1
                            }, 8, [
                                "disabled"
                            ])
                        ])
                    ])) : x("", !0),
                    t("div", Ne, [
                        (d(!0), p(B, null, W(l.chatHistory?.records, (P, R)=>(d(), O(ge, {
                                key: P.uuid,
                                record: P,
                                idx: R,
                                "tool-call-message": I(P)
                            }, null, 8, [
                                "record",
                                "idx",
                                "tool-call-message"
                            ]))), 128))
                    ])
                ]);
            };
        }
    });
    ze = {
        class: "media-focus"
    };
    Ae = {
        class: "media-mime-bundle"
    };
    Be = E({
        __name: "MediaPanel",
        setup (C) {
            const l = U("session"), u = S(0), c = [
                "image/png",
                "text/html"
            ], _ = f(()=>{
                const o = [], r = l.notebook.cells, s = (a)=>{
                    const k = [];
                    if (a.cell_type === "query" && !a.metadata?.is_flattened) for (const $ of a?.children ?? [])k.push(...s($));
                    else if (a.cell_type === "code") for (const $ of a?.outputs ?? []){
                        const N = $?.data ?? {};
                        c.forEach((z)=>{
                            N[z] && k.push($);
                        });
                    }
                    return k;
                };
                for (const a of r)o.push(...s(a));
                return o;
            }), n = f(()=>_?.value?.[u?.value]?.data);
            return (o, r)=>(d(), p("div", ze, [
                    g(m(se), {
                        class: "media-toolbar"
                    }, {
                        start: y(()=>[
                                g(m(L), {
                                    icon: "pi pi-arrow-left",
                                    class: "media-toolbar-button",
                                    onClick: r[0] || (r[0] = ()=>{
                                        u.value -= Math.min(u.value, 1);
                                    })
                                }),
                                g(m(L), {
                                    icon: "pi pi-arrow-right",
                                    class: "media-toolbar-button",
                                    onClick: r[1] || (r[1] = ()=>{
                                        u.value += u.value >= _.value.length - 1 ? 0 : 1;
                                    })
                                })
                            ]),
                        end: y(()=>[
                                g(m(ee), null, {
                                    default: y(()=>[
                                            g(m(V), {
                                                class: "media-dropdown-icon"
                                            }, {
                                                default: y(()=>[
                                                        ...r[3] || (r[3] = [
                                                            t("i", {
                                                                class: "pi pi-chart-bar"
                                                            }, null, -1)
                                                        ])
                                                    ]),
                                                _: 1
                                            }),
                                            g(m(te), {
                                                modelValue: u.value,
                                                "onUpdate:modelValue": r[2] || (r[2] = (s)=>u.value = s),
                                                options: Array.from(_.value.map((s, a)=>({
                                                        label: a + 1,
                                                        value: a
                                                    }))),
                                                "option-label": "label",
                                                "option-value": "value"
                                            }, null, 8, [
                                                "modelValue",
                                                "options"
                                            ]),
                                            g(m(V), null, {
                                                default: y(()=>[
                                                        b("/ " + v(_.value.length ?? 0), 1)
                                                    ]),
                                                _: 1
                                            })
                                        ]),
                                    _: 1
                                })
                            ]),
                        _: 1
                    }),
                    t("div", Ae, [
                        n.value !== void 0 ? (d(), O(oe, {
                            key: 0,
                            "mime-bundle": n.value,
                            class: "code-cell-output"
                        }, null, 8, [
                            "mime-bundle"
                        ])) : x("", !0)
                    ])
                ]));
        }
    });
});
export { Be as _, Ke as a, Ve as b, __tla };
