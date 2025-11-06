import { J as fe, a as pe, L as ve, M as me, T as ke, b as _e, w as be, _ as ge, c as E, d, e as we, f as ye, g as he, __tla as __tla_0 } from "./renderers-707ItvV_.js";
import { B as Ce, _ as xe, a as Ie, S as $e, b as Re, __tla as __tla_1 } from "./BeakerNotebookPanel.vue_vue_type_style_index_0_lang-BpwiRAGL.js";
import { a as Se, b as Ne, __tla as __tla_2 } from "./index-wfwXefED.js";
import { d as Pe, r as i, i as L, f as w, g as J, j as p, K as s, u as P, R as U, o as v, B as W, S as M, H as n, N as Me, G as y, n as G, U as Be } from "./primevue-BhybIXDC.js";
import { _ as Fe, a as ze, b as Ae, __tla as __tla_3 } from "./MediaPanel.vue_vue_type_style_index_0_lang-BvwUDR1l.js";
import { _ as De, a as Oe, l as Te, __tla as __tla_4 } from "./IntegrationPanel.vue_vue_type_style_index_0_lang-CAs3cGuu.js";
import { a as je, b as Ve, c as Ke, _ as qe, __tla as __tla_5 } from "./BeakerRawCell.vue_vue_type_style_index_0_lang-OdsdCFW2.js";
import { _ as Ee, __tla as __tla_6 } from "./BeakerQueryCell.vue_vue_type_style_index_0_lang-CBmbDJ2l.js";
import { _ as Le, a as Je, b as Ue, __tla as __tla_7 } from "./WorkflowOutputPanel.vue_vue_type_style_index_0_lang-BSXV8XAI.js";
import { s as We } from "./jupyterlab-Bq9OOClR.js";
import "./_plugin-vue_export-helper-DlAUqK2U.js";
import "./codemirror-CEJpu35t.js";
import "./xlsx-C3u7rb2R.js";
import { __tla as __tla_8 } from "./pdfjs-B7zhfHd9.js";
import { __tla as __tla_9 } from "./cellOperations-C51nPkhh.js";
import "./BrainIcon-Cg6sqKva.js";
import "./BaseQueryCell-5qJKeHAI.js";
let pt;
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
    })(),
    (()=>{
        try {
            return __tla_7;
        } catch  {}
    })(),
    (()=>{
        try {
            return __tla_8;
        } catch  {}
    })(),
    (()=>{
        try {
            return __tla_9;
        } catch  {}
    })()
]).then(async ()=>{
    let Ge, He;
    Ge = {
        class: "notebook-container"
    };
    He = {
        class: "welcome-placeholder"
    };
    pt = Pe({
        __name: "NotebookInterface",
        props: [
            "config",
            "connectionSettings",
            "sessionName",
            "sessionId",
            "defaultKernel",
            "renderers"
        ],
        setup (H) {
            const l = i(), h = i(), C = i(), Q = i(), x = i(), I = i(), $ = i(), X = i(!1), B = new URLSearchParams(window.location.search), F = B.has("session") ? B.get("session") : "notebook_dev_session", z = H, Y = [
                ...We.map((e)=>new _e(e)).map(be),
                fe,
                pe,
                ve,
                me,
                ke
            ], Z = {
                code: Ke,
                markdown: Ve,
                query: Ee,
                raw: je
            }, ee = i("connecting"), _ = i([]), te = i([]);
            i();
            const R = i(null), k = i(null), A = i();
            i(!1);
            const m = i(!1);
            i();
            const { theme: D, toggleDarkMode: le } = L("theme"), b = L("beakerAppConfig");
            b.setPage("legacy-notebook");
            const O = i(), T = i(), S = i(), oe = w(()=>{
                const e = [];
                if (!b?.config?.pages || Object.hasOwn(b.config.pages, "chat")) {
                    const t = "/" + (b?.config?.pages?.chat?.default ? "" : "chat") + window.location.search;
                    e.push({
                        type: "link",
                        href: t,
                        icon: "comment",
                        label: "Navigate to chat view"
                    });
                }
                return e.push({
                    type: "button",
                    icon: D.mode === "dark" ? "sun" : "moon",
                    command: le,
                    label: `Switch to ${D.mode === "dark" ? "light" : "dark"} mode.`
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
            }), f = w(()=>h?.value?.beakerSession), j = w(()=>f?.value?.activeContext?.info?.workflow_info), V = w(()=>j.value?.workflows[j?.value?.state?.workflow_id]), g = i({});
            J(f, async ()=>{
                g.value = await Te(F);
            }), J(()=>l?.value?.notebook.cells, (e)=>{
                e?.length === 0 && l.value.insertCellBefore();
            }, {
                deep: !0
            });
            const ne = (e)=>{
                if (e.header.msg_type === "preview") O.value = e.content;
                else if (e.header.msg_type === "kernel_state_info") T.value = e.content;
                else if (e.header.msg_type === "update_workflow_state") {
                    const t = f?.value?.activeContext?.info?.workflow_info;
                    t && (t.state = e.content, x.value.selectPanel("workflow-steps"), I.value.selectPanel("workflow-output"));
                } else e.header.msg_type === "debug_event" ? _.value.push({
                    type: e.content.event,
                    body: e.content.body,
                    timestamp: e.header.date
                }) : e.header.msg_type === "chat_history" ? (A.value = e.content, console.log(e.content)) : e.header.msg_type === "lint_code_result" && e.content.forEach((t)=>{
                    f.value.findNotebookCellById(t.cell_id).lintAnnotations.push(t);
                });
            }, ae = (e, t)=>{
                te.value.push({
                    type: t,
                    body: e,
                    timestamp: e.header.date
                });
            }, ie = (e)=>{
                console.log("Unhandled message recieved", e);
            }, se = (e)=>{
                ee.value = e == "idle" ? "connected" : e;
            }, re = async ()=>{
                await f.value.session.sendBeakerMessage("reset_request", {});
            }, N = (e, t)=>{
                const a = l.value;
                f.value?.session.loadNotebook(e), k.value = t;
                const c = a.notebook.cells.map((o)=>o.id);
                c.includes(a.selectedCellId) || G(()=>{
                    a.selectCell(c[0]);
                });
            }, ce = async (e)=>{
                k.value = e, e && (x.value?.selectPanel("Files"), await C.value.refresh(), await C.value.flashFile(e));
            }, K = ()=>{
                l.value?.selectPrevCell();
            }, q = ()=>{
                const e = l.value.notebook.cells[l.value.notebook.cells.length - 1];
                l.value.selectedCell().cell.id === e.id ? $.value.$el.querySelector("textarea")?.focus() : l.value?.selectNextCell();
            }, u = {}, de = {
                "keydown.enter.ctrl.prevent.capture.in-cell": ()=>{
                    l.value?.selectedCell().execute(), l.value?.selectedCell().exit();
                },
                "keydown.enter.shift.prevent.capture.in-cell": ()=>{
                    const e = l.value?.selectedCell();
                    e.execute(), l.value?.selectNextCell() || (l.value?.insertCellAfter(e, void 0, !0), G(()=>{
                        l.value?.selectedCell().enter();
                    }));
                },
                "keydown.enter.exact.prevent.stop.!in-editor": ()=>{
                    l.value?.selectedCell().enter();
                },
                "keydown.esc.exact.prevent": ()=>{
                    l.value?.selectedCell().exit();
                },
                "keydown.up.!in-editor.prevent": K,
                "keydown.up.in-editor.capture": (e)=>{
                    const t = e.target, c = t.closest(".beaker-cell")?.getAttribute("cell-id");
                    if (c !== void 0) {
                        const o = f.value.findNotebookCellById(c);
                        if (Ne(o.editor)) {
                            const r = l.value.prevCell();
                            r && (o.exit(), l.value.selectCell(r.cell.id, !0, "end"), e.preventDefault(), e.stopImmediatePropagation());
                        }
                    } else t.closest(".agent-query-container") && (t.blur(), l.value.selectCell(l.value.notebook.cells[l.value.notebook.cells.length - 1].id, !0, "end"), e.preventDefault(), e.stopImmediatePropagation());
                },
                "keydown.down.in-editor.capture": (e)=>{
                    const c = e.target.closest(".beaker-cell")?.getAttribute("cell-id");
                    if (c !== void 0) {
                        const o = f.value.findNotebookCellById(c);
                        if (Se(o.editor)) {
                            const r = l.value.nextCell();
                            if (r) o.exit(), l.value.selectCell(r.cell.id, !0, "start"), e.preventDefault(), e.stopImmediatePropagation();
                            else {
                                const ue = l.value.notebook.cells[l.value.notebook.cells.length - 1];
                                l.value.selectedCell().cell.id === ue.id && (o.exit(), $.value.$el.querySelector("textarea")?.focus(), e.preventDefault(), e.stopImmediatePropagation());
                            }
                        }
                    }
                },
                "keydown.k.!in-editor": K,
                "keydown.down.!in-editor.prevent": q,
                "keydown.j.!in-editor": q,
                "keydown.a.prevent.!in-editor": (e)=>{
                    const t = l.value;
                    t?.selectedCell().exit(), t?.insertCellBefore();
                },
                "keydown.b.prevent.!in-editor": ()=>{
                    const e = l.value;
                    e?.selectedCell().exit(), e?.insertCellAfter();
                },
                "keydown.d.!in-editor": ()=>{
                    const e = l.value, t = e.selectedCell(), a = ()=>{
                        delete u.d;
                    };
                    if (u.d === void 0) {
                        const o = setTimeout(a, 1e3);
                        u.d = {
                            cell_id: t.id,
                            timeout: o
                        };
                    } else {
                        const { cell_id: o, timeout: r } = u.d;
                        o === t.id && (e?.removeCell(t), R.value = t.cell, delete u.d), r && window.clearTimeout(r);
                    }
                },
                "keydown.y.!in-editor": ()=>{
                    const t = l.value.selectedCell(), a = ()=>{
                        delete u.y;
                    };
                    if (u.y === void 0) {
                        const o = setTimeout(a, 1e3);
                        u.y = {
                            cell_id: t.id,
                            timeout: o
                        };
                    } else {
                        const { cell_id: o, timeout: r } = u.y;
                        o === t.id && (R.value = t.cell, delete u.y), r && window.clearTimeout(r);
                    }
                },
                "keydown.p.!in-editor": (e)=>{
                    const t = l.value;
                    let a = Be(R.value);
                    if (a !== null) {
                        if (t.notebook.cells.map((o)=>o.id).includes(a.id)) {
                            const o = a.constructor, r = {
                                ...a,
                                id: void 0,
                                executionCount: void 0,
                                busy: void 0,
                                last_execution: void 0
                            };
                            a = new o(r);
                        }
                        e.key === "p" ? t?.insertCellAfter(t.selectedCell(), a) : e.key === "P" && t?.insertCellBefore(t.selectedCell(), a), a.value = null;
                    }
                }
            };
            return (e, t)=>{
                const a = U("autoscroll"), c = U("keybindings");
                return v(), p(ge, {
                    title: e.$tmpl._("short_title", "Beaker Notebook"),
                    "title-extra": k.value,
                    "header-nav": oe.value,
                    ref_key: "beakerInterfaceRef",
                    ref: h,
                    connectionSettings: z.config,
                    defaultKernel: "beaker_kernel",
                    sessionId: P(F),
                    renderers: Y,
                    savefile: k.value,
                    onIopubMsg: ne,
                    onUnhandledMsg: ie,
                    onAnyMsg: ae,
                    onSessionStatusChanged: se,
                    onOpenFile: N
                }, {
                    "left-panel": s(()=>[
                            n(E, {
                                ref_key: "sideMenuRef",
                                ref: x,
                                position: "left",
                                highlight: "line",
                                expanded: !0,
                                initialWidth: "25vi",
                                maximized: m.value
                            }, {
                                default: s(()=>[
                                        V.value ? (v(), p(d, {
                                            key: 0,
                                            id: "workflow-steps",
                                            label: "Workflow Steps",
                                            icon: "pi pi-list-check"
                                        }, {
                                            default: s(()=>[
                                                    n(Ue)
                                                ]),
                                            _: 1
                                        })) : y("", !0),
                                        n(d, {
                                            label: "Context Info",
                                            icon: "pi pi-home"
                                        }, {
                                            default: s(()=>[
                                                    n(ze)
                                                ]),
                                            _: 1
                                        }),
                                        n(d, {
                                            id: "files",
                                            label: "Files",
                                            icon: "pi pi-folder",
                                            "no-overflow": "",
                                            lazy: !0
                                        }, {
                                            default: s(()=>[
                                                    n(ye, {
                                                        ref_key: "filePanelRef",
                                                        ref: C,
                                                        onOpenFile: N,
                                                        onPreviewFile: t[1] || (t[1] = (o, r)=>{
                                                            S.value = {
                                                                url: o,
                                                                mimetype: r
                                                            }, X.value = !0, I.value.selectPanel("file-contents");
                                                        })
                                                    }, null, 512)
                                                ]),
                                            _: 1
                                        }),
                                        n(d, {
                                            icon: "pi pi-comments",
                                            label: "Chat History"
                                        }, {
                                            default: s(()=>[
                                                    n(P(Ae), {
                                                        "chat-history": A.value
                                                    }, null, 8, [
                                                        "chat-history"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        Object.keys(g.value).length > 0 ? (v(), p(d, {
                                            key: 1,
                                            id: "integrations",
                                            label: "Integrations",
                                            icon: "pi pi-database"
                                        }, {
                                            default: s(()=>[
                                                    n(Oe, {
                                                        modelValue: g.value,
                                                        "onUpdate:modelValue": t[2] || (t[2] = (o)=>g.value = o)
                                                    }, null, 8, [
                                                        "modelValue"
                                                    ])
                                                ]),
                                            _: 1
                                        })) : y("", !0),
                                        z.config.config_type !== "server" ? (v(), p(d, {
                                            key: 2,
                                            id: "config",
                                            label: `${e.$tmpl._("short_title", "Beaker")} Config`,
                                            icon: "pi pi-cog",
                                            lazy: !0,
                                            position: "bottom"
                                        }, {
                                            default: s(()=>[
                                                    n(he, {
                                                        ref_key: "configPanelRef",
                                                        ref: Q,
                                                        onRestartSession: re
                                                    }, null, 512)
                                                ]),
                                            _: 1
                                        }, 8, [
                                            "label"
                                        ])) : y("", !0)
                                    ]),
                                _: 1
                            }, 8, [
                                "maximized"
                            ])
                        ]),
                    "right-panel": s(()=>[
                            n(E, {
                                ref_key: "rightSideMenuRef",
                                ref: I,
                                position: "right",
                                highlight: "line",
                                expanded: !0,
                                initialWidth: "25vi",
                                maximized: m.value
                            }, {
                                default: s(()=>[
                                        V.value ? (v(), p(d, {
                                            key: 0,
                                            id: "workflow-output",
                                            label: "Workflow Output",
                                            icon: "pi pi-list-check"
                                        }, {
                                            default: s(()=>[
                                                    n(Le)
                                                ]),
                                            _: 1
                                        })) : y("", !0),
                                        n(d, {
                                            label: "Preview",
                                            icon: "pi pi-eye",
                                            "no-overflow": ""
                                        }, {
                                            default: s(()=>[
                                                    n(qe, {
                                                        previewData: O.value
                                                    }, null, 8, [
                                                        "previewData"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        n(d, {
                                            id: "file-contents",
                                            label: "File Contents",
                                            icon: "pi pi-file beaker-zoom",
                                            "no-overflow": ""
                                        }, {
                                            default: s(()=>[
                                                    n(De, {
                                                        url: S.value?.url,
                                                        mimetype: S.value?.mimetype
                                                    }, null, 8, [
                                                        "url",
                                                        "mimetype"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        n(d, {
                                            id: "media",
                                            label: "Graphs and Images",
                                            icon: "pi pi-chart-bar",
                                            "no-overflow": ""
                                        }, {
                                            default: s(()=>[
                                                    n(Fe)
                                                ]),
                                            _: 1
                                        }),
                                        n(d, {
                                            id: "kernel-state",
                                            label: "Kernel State",
                                            icon: "pi pi-server",
                                            "no-overflow": ""
                                        }, {
                                            default: s(()=>[
                                                    n(Je, {
                                                        data: T.value
                                                    }, null, 8, [
                                                        "data"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        n(d, {
                                            id: "kernel-logs",
                                            label: "Logs",
                                            icon: "pi pi-list",
                                            position: "bottom"
                                        }, {
                                            default: s(()=>[
                                                    M(n(we, {
                                                        entries: _.value,
                                                        onClearLogs: t[3] || (t[3] = (o)=>_.value.splice(0, _.value.length))
                                                    }, null, 8, [
                                                        "entries"
                                                    ]), [
                                                        [
                                                            a
                                                        ]
                                                    ])
                                                ]),
                                            _: 1
                                        })
                                    ]),
                                _: 1
                            }, 8, [
                                "maximized"
                            ])
                        ]),
                    default: s(()=>[
                            W("div", Ge, [
                                M((v(), p(Ce, {
                                    ref_key: "beakerNotebookRef",
                                    ref: l,
                                    "cell-map": Z
                                }, {
                                    default: s(()=>[
                                            n(xe, {
                                                "default-severity": "",
                                                saveAvailable: !0,
                                                "save-as-filename": k.value,
                                                onNotebookSaved: ce,
                                                onOpenFile: N
                                            }, {
                                                "end-extra": s(()=>[
                                                        n(P(Me), {
                                                            onClick: t[0] || (t[0] = (o)=>{
                                                                m.value = !m.value, h.value.setMaximized(m.value);
                                                            }),
                                                            icon: `pi ${m.value ? "pi-window-minimize" : "pi-window-maximize"}`,
                                                            size: "small",
                                                            text: ""
                                                        }, null, 8, [
                                                            "icon"
                                                        ])
                                                    ]),
                                                _: 1
                                            }, 8, [
                                                "save-as-filename"
                                            ]),
                                            M((v(), p(Ie, {
                                                "selected-cell": l.value?.selectedCellId
                                            }, {
                                                "notebook-background": s(()=>[
                                                        W("div", He, [
                                                            n($e)
                                                        ])
                                                    ]),
                                                _: 1
                                            }, 8, [
                                                "selected-cell"
                                            ])), [
                                                [
                                                    a
                                                ]
                                            ]),
                                            n(Re, {
                                                ref_key: "agentQueryRef",
                                                ref: $,
                                                class: "agent-query-container"
                                            }, null, 512)
                                        ]),
                                    _: 1
                                })), [
                                    [
                                        c,
                                        de,
                                        void 0,
                                        {
                                            top: !0
                                        }
                                    ]
                                ])
                            ])
                        ]),
                    _: 1
                }, 8, [
                    "title",
                    "title-extra",
                    "header-nav",
                    "connectionSettings",
                    "sessionId",
                    "savefile"
                ]);
            };
        }
    });
});
export { pt as default, __tla };
