import { d as ke, i as ue, r as u, f as h, x as he, y as xe, z as $e, A as X, o as C, B as M, G as O, H as c, I as Re, J as fe, j, K as p, u as i, L as Me, M as _e, N as de, O as me, Q as Se, g as Y, n as pe, R as ce, S as oe, p as Ne } from "./primevue-BhybIXDC.js";
import { B as Pe, m as ge, J as Be, a as Ae, L as Ie, M as Te, T as Ee, b as qe, w as Fe, _ as ze, u as Qe, c as ve, d as B, e as He, f as De, g as je, __tla as __tla_0 } from "./renderers-707ItvV_.js";
import { B as Ve, _ as Le, a as Oe, S as Ue, b as Ke, __tla as __tla_1 } from "./BeakerNotebookPanel.vue_vue_type_style_index_0_lang-BpwiRAGL.js";
import { _ as We, a as Je, b as Ge, __tla as __tla_2 } from "./MediaPanel.vue_vue_type_style_index_0_lang-BvwUDR1l.js";
import { _ as Xe, a as Ye, l as Ze, __tla as __tla_3 } from "./IntegrationPanel.vue_vue_type_style_index_0_lang-CAs3cGuu.js";
import { _ as et, a as tt, b as ot, c as nt, __tla as __tla_4 } from "./BeakerRawCell.vue_vue_type_style_index_0_lang-OdsdCFW2.js";
import { _ as lt, a as st, b as at, __tla as __tla_5 } from "./WorkflowOutputPanel.vue_vue_type_style_index_0_lang-BSXV8XAI.js";
import { _ as it } from "./NextBeakerQueryCell.vue_vue_type_style_index_0_lang-DJ_z8t0w.js";
import { T as rt } from "./BrainIcon-Cg6sqKva.js";
import { a as ct, b as ut, __tla as __tla_6 } from "./index-wfwXefED.js";
import { s as dt } from "./jupyterlab-Bq9OOClR.js";
import "./_plugin-vue_export-helper-DlAUqK2U.js";
import "./codemirror-CEJpu35t.js";
import "./xlsx-C3u7rb2R.js";
import { __tla as __tla_7 } from "./pdfjs-B7zhfHd9.js";
import "./BaseQueryCell-5qJKeHAI.js";
let Kt;
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
    })()
]).then(async ()=>{
    const pt = {
        class: "agent-cell"
    }, ft = {
        class: "agent-cell-header"
    }, _t = {
        class: "agent-cell-title"
    }, mt = {
        key: 0,
        class: "agent-cell-icon brain-icon"
    }, gt = {
        class: "agent-cell-label"
    }, vt = {
        class: "agent-cell-actions"
    }, kt = [
        "innerHTML"
    ], ht = {
        key: 0,
        class: "tool-info-display"
    }, bt = {
        class: "tool-info-header"
    }, yt = {
        style: {
            "font-family": "monospace",
            "margin-left": "4rem"
        }
    }, wt = {
        class: "tool-info-arguments"
    }, Ct = {
        modelClass: Pe,
        icon: "pi pi-pencil"
    }, xt = ke({
        ...Ct,
        __name: "BeakerAgentCell",
        props: [
            "cell"
        ],
        setup (s, { expose: A }) {
            const d = s, b = xe(), I = ue("beakerSession"), S = u(d.cell), g = u(!1), F = [
                "run_code",
                "ask_user"
            ], x = h(()=>d.cell?.metadata?.beaker_cell_type), z = h(()=>({
                    thought: "Beaker Agent",
                    response: "Beaker Agent",
                    user_question: "Beaker Agent",
                    error: "Error",
                    abort: "Aborted"
                })[x.value] || "Beaker Agent"), v = h(()=>{
                const o = S.value?.metadata?.thought;
                return o?.tool_name ? {
                    toolName: o.tool_name,
                    toolInput: o.tool_input
                } : null;
            }), T = h(()=>({
                    thought: "pi pi-sparkles",
                    response: "pi pi-sparkles",
                    user_question: "pi pi-question-circle",
                    error: "pi pi-times-circle",
                    abort: "pi pi-ban"
                })[x.value] || "pi pi-comment"), U = h(()=>!1), V = h(()=>!1), y = h(()=>{
                if (typeof d.cell == "object" && d.cell) {
                    const { source: o } = d.cell, l = (Array.isArray(o) ? o.join("") : o).replace(/^\*\*[^*]+\*\*\n\n/, "");
                    return ge.parse(l);
                }
                return "";
            }), L = ()=>{};
            return A({
                execute: ()=>{},
                enter: (o)=>{},
                exit: ()=>{},
                clear: ()=>{},
                model: S
            }), he(()=>{
                ge.setOptions({}), I.cellRegistry[S.value.id] = b.vnode;
            }), $e(()=>{
                delete I.cellRegistry[S.value.id];
            }), (o, t)=>(C(), X("div", pt, [
                    M("div", ft, [
                        M("div", _t, [
                            U.value ? (C(), X("div", mt, [
                                c(rt)
                            ])) : (C(), X("i", {
                                key: 1,
                                class: Re([
                                    T.value,
                                    "agent-cell-icon"
                                ])
                            }, null, 2)),
                            M("span", gt, fe(z.value), 1)
                        ]),
                        M("div", vt, [
                            v.value && !F.includes(v.value.toolName) ? (C(), j(i(Me), {
                                key: 0,
                                class: "agent-cell-toolcall-toggle execution-badge",
                                modelValue: g.value,
                                "onUpdate:modelValue": t[0] || (t[0] = (l)=>g.value = l)
                            }, {
                                default: p(()=>[
                                        ...t[1] || (t[1] = [
                                            M("span", {
                                                class: "pi pi-wrench"
                                            }, null, -1)
                                        ])
                                    ]),
                                _: 1
                            }, 8, [
                                "modelValue"
                            ])) : O("", !0),
                            V.value ? (C(), j(i(de), {
                                key: 1,
                                onClick: L,
                                size: "small",
                                severity: "secondary",
                                text: ""
                            }, {
                                default: p(()=>[
                                        ...t[2] || (t[2] = [
                                            _e(" More Details ", -1)
                                        ])
                                    ]),
                                _: 1
                            })) : O("", !0)
                        ])
                    ]),
                    M("div", {
                        class: "agent-cell-content",
                        innerHTML: y.value
                    }, null, 8, kt),
                    g.value ? (C(), X("div", ht, [
                        M("div", bt, [
                            t[3] || (t[3] = _e("Tool name: ", -1)),
                            M("span", yt, fe(v.value.toolName), 1)
                        ]),
                        M("div", wt, [
                            t[4] || (t[4] = M("div", {
                                class: "tool-info-header"
                            }, "Tool arguments:", -1)),
                            c(i(Se), {
                                showGridlines: "",
                                stripedRows: "",
                                size: "small",
                                class: "tool-info-argument-datatable",
                                value: Object.entries(v.value.toolInput).map(([l, r])=>({
                                        key: l,
                                        value: r
                                    }))
                            }, {
                                default: p(()=>[
                                        c(i(me), {
                                            field: "key",
                                            header: "Parameter"
                                        }),
                                        c(i(me), {
                                            field: "value",
                                            header: "Value"
                                        })
                                    ]),
                                _: 1
                            }, 8, [
                                "value"
                            ])
                        ])
                    ])) : O("", !0)
                ]));
        }
    });
    function $t() {
        const s = u(), A = u(), d = u(), b = u(), I = u(), S = u(), g = u(), F = u(), x = u("connecting"), z = u([]), v = u([]), T = u(null), U = u(!1), V = u(), y = u([]), L = u(), Q = {}, J = u(null), { theme: K, toggleDarkMode: n } = ue("theme"), o = ue("beakerAppConfig"), t = h(()=>A?.value?.beakerSession), l = h(()=>t.value?.session?.notebook?.cells ? t.value.session.notebook.cells.filter((e)=>e.cell_type === "query").map((e)=>({
                    id: e.id,
                    source: e.source,
                    status: e.status
                })) : []), r = h(()=>(t.value?.session?.notebook?.cells ?? []).find((a)=>a.cell_type === "query" && a.status === "awaiting_input") || null), _ = h(()=>r.value ? [
                ...r.value.events || []
            ].reverse().find((N)=>N.type === "user_question")?.content || "The agent is waiting for your response." : null), $ = [
            ...dt.map((e)=>new qe(e)).map(Fe),
            Be,
            Ae,
            Ie,
            Te,
            Ee
        ], E = (e)=>{
            const a = [];
            return e !== "chat" && a.push({
                type: "link",
                href: "/chat" + window.location.search,
                icon: "comment",
                label: "Navigate to chat view"
            }), e !== "notebook" && a.push({
                type: "link",
                href: "/notebook" + window.location.search,
                icon: "sparkles",
                label: "Navigate to notebook view"
            }), a.push({
                type: "button",
                icon: K.mode === "dark" ? "sun" : "moon",
                command: n,
                label: `Switch to ${K.mode === "dark" ? "light" : "dark"} mode.`
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
            }), a;
        }, H = ()=>{
            s.value?.selectPrevCell();
        }, f = ()=>{
            const e = s.value.notebook.cells[s.value.notebook.cells.length - 1];
            s.value.selectedCell().cell.id === e.id ? g.value.$el.querySelector("textarea")?.focus() : s.value?.selectNextCell();
        }, R = (e)=>{
            const a = document.querySelector(`[cell-id="${e}"]`);
            a && (a.scrollIntoView({
                behavior: "smooth",
                block: "center"
            }), s.value?.selectCell(e));
        }, Z = ()=>({
                "keydown.enter.ctrl.prevent.capture.in-cell": ()=>{
                    s.value?.selectedCell().execute(), s.value?.selectedCell().exit();
                },
                "keydown.enter.shift.prevent.capture.in-cell": ()=>{
                    const e = s.value?.selectedCell();
                    e.execute(), s.value?.selectNextCell() || (s.value?.insertCellAfter(e, void 0, !0), pe(()=>{
                        s.value?.selectedCell().enter();
                    }));
                },
                "keydown.enter.exact.prevent.stop.!in-editor": ()=>{
                    s.value?.selectedCell().enter();
                },
                "keydown.esc.exact.prevent": ()=>{
                    s.value?.selectedCell().exit();
                },
                "keydown.up.!in-editor.prevent": H,
                "keydown.up.in-editor.capture": (e)=>{
                    const a = e.target, q = a.closest(".beaker-cell")?.getAttribute("cell-id");
                    if (q !== void 0) {
                        const w = t.value.findNotebookCellById(q);
                        if (ut(w.editor)) {
                            const P = s.value.prevCell();
                            P && (w.exit(), s.value.selectCell(P.cell.id, !0, "end"), e.preventDefault(), e.stopImmediatePropagation());
                        }
                    } else a.closest(".agent-query-container") && (a.blur(), s.value.selectCell(s.value.notebook.cells[s.value.notebook.cells.length - 1].id, !0, "end"), e.preventDefault(), e.stopImmediatePropagation());
                },
                "keydown.down.in-editor.capture": (e)=>{
                    const q = e.target.closest(".beaker-cell")?.getAttribute("cell-id");
                    if (q !== void 0) {
                        const w = t.value.findNotebookCellById(q);
                        if (ct(w.editor)) {
                            const P = s.value.nextCell();
                            if (P) w.exit(), s.value.selectCell(P.cell.id, !0, "start"), e.preventDefault(), e.stopImmediatePropagation();
                            else {
                                const G = s.value.notebook.cells[s.value.notebook.cells.length - 1];
                                s.value.selectedCell().cell.id === G.id && (w.exit(), g.value.$el.querySelector("textarea")?.focus(), e.preventDefault(), e.stopImmediatePropagation());
                            }
                        }
                    }
                },
                "keydown.k.!in-editor": H,
                "keydown.down.!in-editor.prevent": f,
                "keydown.j.!in-editor": f,
                "keydown.a.prevent.!in-editor": ()=>{
                    const e = s.value;
                    e?.selectedCell().exit(), e?.insertCellBefore();
                },
                "keydown.b.prevent.!in-editor": ()=>{
                    const e = s.value;
                    e?.selectedCell().exit(), e?.insertCellAfter();
                },
                "keydown.d.!in-editor": ()=>{
                    const e = s.value, a = e.selectedCell(), N = ()=>{
                        delete Q.d;
                    };
                    if (Q.d === void 0) {
                        const w = setTimeout(N, 1e3);
                        Q.d = {
                            cell_id: a.id,
                            timeout: w
                        };
                    } else {
                        const { cell_id: w, timeout: P } = Q.d;
                        w === a.id && (e?.removeCell(a), J.value = a.cell, delete Q.d), P && window.clearTimeout(P);
                    }
                }
            }), ne = ()=>(e)=>{
                if (e.header.msg_type === "preview") L.value = e.content;
                else if (e.header.msg_type === "kernel_state_info") F.value = e.content;
                else if (e.header.msg_type === "debug_event") z.value.push({
                    type: e.content.event,
                    body: e.content.body,
                    timestamp: e.header.date
                });
                else if (e.header.msg_type === "update_workflow_state") {
                    const a = t?.value?.activeContext?.info?.workflow_info;
                    a && (a.state = e.content, I.value.selectPanel("workflow-steps"), S.value.selectPanel("workflow-output"));
                } else if (e.header.msg_type === "chat_history") V.value = e.content, console.log(e.content);
                else if (e.header.msg_type === "context_setup_response" || e.header.msg_type === "context_info_response") {
                    let a;
                    e.header.msg_type === "context_setup_response" ? a = e.content.integrations : e.header.msg_type === "context_info_response" && (a = e.content.info.integrations), a === void 0 && (a = []), y.value.splice(0, y.value.length, ...a);
                } else e.header.msg_type === "lint_code_result" && e.content.forEach((a)=>{
                    t.value.findNotebookCellById(a.cell_id).lintAnnotations.push(a);
                });
            }, le = (e, a)=>{
            v.value.push({
                type: a,
                body: e,
                timestamp: e.header.date
            });
        }, D = (e)=>{
            console.log("Unhandled message received", e);
        }, ee = (e)=>{
            x.value = e == "idle" ? "connected" : e;
        }, se = (e, a)=>{
            console.log("Loading notebook", e);
            const N = s.value;
            t.value?.session.loadNotebook(e), e?.metadata?.chat_history && t.value?.session.executeAction("set_agent_history", e?.metadata?.chat_history), T.value = a;
            const q = N.notebook.cells.map((w)=>w.id);
            q.includes(N.selectedCellId) || pe(()=>{
                N.selectCell(q[0]);
            });
        }, ae = async (e)=>{
            T.value = e, e && (I.value?.selectPanel("Files"), await d.value.refresh(), await d.value.flashFile(e));
        }, ie = async ()=>{
            await t.value.session.sendBeakerMessage("reset_request", {});
        };
        return Y(()=>s?.value?.notebook.cells, (e)=>{
            e?.length === 0 && s.value.insertCellBefore();
        }, {
            deep: !0
        }), {
            beakerNotebookRef: s,
            beakerInterfaceRef: A,
            filePanelRef: d,
            configPanelRef: b,
            sideMenuRef: I,
            rightSideMenuRef: S,
            agentQueryRef: g,
            connectionStatus: x,
            debugLogs: z,
            rawMessages: v,
            saveAsFilename: T,
            isMaximized: U,
            chatHistory: V,
            integrations: y,
            contextPreviewData: L,
            kernelStateInfo: F,
            copiedCell: J,
            activeQueryCells: l,
            awaitingInputCell: r,
            awaitingInputQuestion: _,
            beakerSession: t,
            defaultRenderers: $,
            createHeaderNav: E,
            createNotebookKeyBindings: Z,
            createIopubMessageHandler: ne,
            anyMessageHandler: le,
            unhandledMessageHandler: D,
            statusChangedHandler: ee,
            loadNotebook: se,
            handleNotebookSaved: ae,
            scrollToCell: R,
            restartSession: ie,
            theme: K,
            toggleDarkMode: n,
            beakerApp: o
        };
    }
    function Rt(s, A) {
        const d = u(new Map), b = (n, o, t)=>s().session.notebook.cells.find((r)=>r.metadata?.parent_query_cell === n && r.metadata?.query_event_index === o && r.metadata?.beaker_cell_type === t), I = ()=>{
            const n = s()?.session?.notebook;
            if (n) {
                d.value.clear();
                for (const o of n.cells)if (o.metadata?.parent_query_cell && o.metadata?.query_event_index !== void 0) {
                    const t = o.metadata.parent_query_cell, l = o.metadata.query_event_index;
                    d.value.has(t) || d.value.set(t, new Set), d.value.get(t).add(l);
                }
            }
        }, S = (n)=>{
            const o = s().session.notebook, t = o.cells.findIndex((r)=>r.id === n);
            if (t === -1) return o.cells.length;
            let l = t + 1;
            for(; l < o.cells.length && o.cells[l].metadata?.parent_query_cell === n;)l++;
            return l;
        }, g = (n, o, t, l = {})=>({
                beaker_cell_type: n,
                parent_query_cell: o,
                query_event_index: t,
                ...l
            });
        function F(n, o) {
            n !== o && s().session.notebook.moveCell(n, o);
        }
        const x = (n, o, t)=>{
            const l = S(o), r = s().session.addMarkdownCell(n, t);
            return F(s().session.notebook.cells.length - 1, l), r;
        }, z = (n, o, t, l = [])=>{
            const r = S(o), _ = s().session.addCodeCell(n, t, l);
            return F(s().session.notebook.cells.length - 1, r), _;
        }, v = (n, o, t)=>{
            if (b(o, t, "thought") || n?.thought === null || n?.thought.length === 0 || n.thought === "Thinking...") return;
            const l = g("thought", o, t, {
                thought: n
            }), r = `**Beaker Agent:**

${n.thought}`;
            return x(r, o, l);
        }, T = (n, o, t)=>{
            if (b(o, t, "response")) return;
            let l = "";
            typeof n == "string" ? l = `**Beaker Agent:**

${n}` : n && typeof n == "object" && (l = `\`\`\`json
${JSON.stringify(n, null, 2)}
\`\`\``);
            const r = g("response", o, t);
            return x(l, o, r);
        }, U = (n, o, t, l)=>{
            const r = A.value;
            if (b(t, l, "code")) return;
            const _ = o.children?.find((f)=>f.id === n);
            if (!_) return;
            const E = g("code", t, l, {
                source_cell_id: n,
                collapsed: r === !0
            }), H = z(_.source, t, E, _.outputs || []);
            return H.execution_count = _.execution_count, _.last_execution ? H.last_execution = {
                ..._.last_execution,
                status: "ok"
            } : _.outputs && _.outputs.length > 0 && (H.last_execution = {
                status: "ok",
                checkpoint_index: void 0
            }), H;
        }, V = (n, o, t)=>{
            if (b(o, t, "error")) return;
            let l = "";
            typeof n == "string" ? l = `**Error:**

${n}` : n && typeof n == "object" && (n.ename && n.evalue ? (l = `**Error:**

**${n.ename}:** ${n.evalue}`, n.traceback && n.traceback.length > 0 && (l += `

\`\`\`
${n.traceback.join(`
`)}
\`\`\``)) : l = `**Error:**

\`\`\`json
${JSON.stringify(n, null, 2)}
\`\`\``);
            const r = g("error", o, t);
            return x(l, o, r);
        }, y = (n, o, t)=>{
            if (b(o, t, "user_question")) return;
            const l = `**Agent Question:**

${n}`, r = g("user_question", o, t);
            return x(l, o, r);
        }, L = (n, o, t)=>{
            let l = null, r = t - 1;
            for(; r >= 0 && !l;)l = b(o, r, "user_question"), r--;
            if (l) {
                const _ = l.source;
                if (!_.includes("**User Response:**")) {
                    const E = `${_}

**User Response:**

${n}`;
                    l.source = E;
                }
                return l;
            } else return Q(n, o, t);
        }, Q = (n, o, t)=>{
            if (b(o, t, "user_answer")) return;
            const l = `**User Response:**

${n}`, r = g("user_answer", o, t);
            return x(l, o, r);
        };
        return {
            processedQueryEvents: d,
            setupQueryCellFlattening: (n)=>{
                Y(n, (o)=>{
                    if (o) {
                        d.value.size === 0 && I();
                        for (const t of o)if (t.cell_type === "query") {
                            const l = t.metadata?.query_status, r = l === "in-progress" || l === "pending";
                            if (l === "success" || l === "failed" || l === "aborted") continue;
                            r && (t.metadata || (t.metadata = {}), t.metadata.is_flattened = !0, d.value.has(t.id) || d.value.set(t.id, new Set), Y(()=>t.events, ($)=>{
                                if (!$ || $.length === 0) return;
                                const E = d.value.get(t.id);
                                $.length > 0 && [
                                    "response",
                                    "error",
                                    "abort"
                                ].includes($[$.length - 1].type) && E.size === $.length || $.forEach((f, R)=>{
                                    E.has(R) || (E.add(R), f.type === "thought" && f.content?.thought ? v(f.content, t.id, R) : f.type === "code_cell" && f.content?.cell_id ? pe(()=>{
                                        U(f.content.cell_id, t, t.id, R);
                                    }) : f.type === "response" ? T(f.content, t.id, R) : f.type === "error" ? V(f.content, t.id, R) : f.type === "user_question" ? y(f.content, t.id, R) : f.type === "user_answer" && L(f.content, t.id, R));
                                });
                            }, {
                                deep: !0,
                                immediate: !0
                            }));
                        }
                    }
                }, {
                    deep: !0,
                    immediate: !0
                });
            },
            resetProcessedEvents: ()=>{
                d.value.clear();
            },
            initializeProcessedEvents: I
        };
    }
    let Mt, St, Nt, Pt;
    Mt = {
        class: "next-notebook-container"
    };
    St = {
        class: "welcome-placeholder"
    };
    Nt = {
        key: 0,
        class: "follow-scroll-agent"
    };
    Pt = {
        class: "agent-input-section"
    };
    Kt = ke({
        __name: "NextNotebookInterface",
        props: [
            "config",
            "connectionSettings",
            "sessionName",
            "sessionId",
            "defaultKernel",
            "renderers"
        ],
        setup (s) {
            const A = s, { beakerNotebookRef: d, beakerInterfaceRef: b, filePanelRef: I, configPanelRef: S, sideMenuRef: g, rightSideMenuRef: F, agentQueryRef: x, saveAsFilename: z, isMaximized: v, debugLogs: T, contextPreviewData: U, kernelStateInfo: V, beakerSession: y, defaultRenderers: L, awaitingInputCell: Q, awaitingInputQuestion: J, createHeaderNav: K, createNotebookKeyBindings: n, createIopubMessageHandler: o, anyMessageHandler: t, unhandledMessageHandler: l, statusChangedHandler: r, loadNotebook: _, handleNotebookSaved: $, beakerApp: E, restartSession: H, chatHistory: f } = $t();
            E.setPage("notebook");
            const R = new URLSearchParams(window.location.search), Z = R.has("session") ? R.get("session") : "nextgen_notebook_dev_session", ne = h(()=>A.sessionId), le = h(()=>A.renderers), D = u(!1), ee = h(()=>Qe(y.value).attachedWorkflow.value);
            he(()=>{
                const m = localStorage.getItem("beaker-truncate-agent-code-cells");
                m !== null && (D.value = JSON.parse(m));
            });
            const se = ()=>{
                localStorage.setItem("beaker-truncate-agent-code-cells", JSON.stringify(D.value)), y.value?.session?.notebook?.cells && y.value.session.notebook.cells.forEach((m)=>{
                    m.cell_type === "query" && m.metadata && (m.metadata.auto_collapse_code_cells = D.value);
                });
            };
            Y(D, ()=>{
                se();
            }), Ne("truncateAgentCodeCells", D);
            const ae = (m)=>{
                const k = {
                    code: nt,
                    markdown: ot,
                    raw: tt
                };
                if (!m) return k;
                if (m.cell_type === "query") return it;
                if (m.cell_type === "markdown" && m.metadata?.beaker_cell_type) {
                    const te = m.metadata.beaker_cell_type;
                    if ([
                        "thought",
                        "response",
                        "user_question",
                        "error",
                        "abort"
                    ].includes(te)) return xt;
                }
                return k[m.cell_type] || k.code;
            }, ie = h(()=>K("notebook")), e = n(), a = o(), N = h(()=>!1), { setupQueryCellFlattening: q, resetProcessedEvents: w } = Rt(()=>y.value, D);
            q(()=>y.value?.session?.notebook?.cells);
            const P = (m, k)=>{
                w(), _(m, k);
            }, G = u({}), be = u(!1), re = u();
            return Y(y, async ()=>{
                G.value = await Ze(Z);
            }), (m, k)=>{
                const te = ce("autoscroll"), ye = ce("tooltip"), we = ce("keybindings");
                return C(), j(ze, {
                    title: m.$tmpl._("short_title", "Beaker Notebook"),
                    "title-extra": i(z),
                    "header-nav": ie.value,
                    ref_key: "beakerInterfaceRef",
                    ref: b,
                    connectionSettings: A.config,
                    defaultKernel: "beaker_kernel",
                    sessionId: ne.value || i(Z),
                    renderers: le.value || i(L),
                    savefile: i(z),
                    onIopubMsg: i(a),
                    onUnhandledMsg: i(l),
                    onAnyMsg: i(t),
                    onSessionStatusChanged: i(r),
                    onOpenFile: P,
                    pageClass: "next-notebook-interface"
                }, {
                    "left-panel": p(()=>[
                            c(ve, {
                                ref_key: "sideMenuRef",
                                ref: g,
                                position: "left",
                                highlight: "line",
                                expanded: !0,
                                initialWidth: "25vi",
                                maximized: i(v)
                            }, {
                                default: p(()=>[
                                        ee.value ? (C(), j(B, {
                                            key: 0,
                                            id: "workflow-steps",
                                            label: "Workflow Steps",
                                            icon: "pi pi-list-check"
                                        }, {
                                            default: p(()=>[
                                                    c(at)
                                                ]),
                                            _: 1
                                        })) : O("", !0),
                                        c(B, {
                                            label: "Context Info",
                                            icon: "pi pi-home"
                                        }, {
                                            default: p(()=>[
                                                    c(Je)
                                                ]),
                                            _: 1
                                        }),
                                        c(B, {
                                            id: "files",
                                            label: "Files",
                                            icon: "pi pi-folder",
                                            "no-overflow": "",
                                            lazy: !0
                                        }, {
                                            default: p(()=>[
                                                    c(De, {
                                                        ref_key: "filePanelRef",
                                                        ref: I,
                                                        onOpenFile: P,
                                                        onPreviewFile: k[2] || (k[2] = (W, Ce)=>{
                                                            re.value = {
                                                                url: W,
                                                                mimetype: Ce
                                                            }, be.value = !0, i(F).selectPanel("file-contents");
                                                        })
                                                    }, null, 512)
                                                ]),
                                            _: 1
                                        }),
                                        c(B, {
                                            icon: "pi pi-comments",
                                            label: "Chat History"
                                        }, {
                                            default: p(()=>[
                                                    c(i(Ge), {
                                                        "chat-history": i(f)
                                                    }, null, 8, [
                                                        "chat-history"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        Object.keys(G.value).length > 0 ? (C(), j(B, {
                                            key: 1,
                                            id: "integrations",
                                            label: "Integrations",
                                            icon: "pi pi-database"
                                        }, {
                                            default: p(()=>[
                                                    c(Ye, {
                                                        modelValue: G.value,
                                                        "onUpdate:modelValue": k[3] || (k[3] = (W)=>G.value = W)
                                                    }, null, 8, [
                                                        "modelValue"
                                                    ])
                                                ]),
                                            _: 1
                                        })) : O("", !0),
                                        A.config.config_type !== "server" ? (C(), j(B, {
                                            key: 2,
                                            id: "config",
                                            label: `${m.$tmpl._("short_title", "Beaker")} Config`,
                                            icon: "pi pi-cog",
                                            lazy: !0,
                                            position: "bottom"
                                        }, {
                                            default: p(()=>[
                                                    c(je, {
                                                        ref_key: "configPanelRef",
                                                        ref: S,
                                                        onRestartSession: i(H)
                                                    }, null, 8, [
                                                        "onRestartSession"
                                                    ])
                                                ]),
                                            _: 1
                                        }, 8, [
                                            "label"
                                        ])) : O("", !0)
                                    ]),
                                _: 1
                            }, 8, [
                                "maximized"
                            ])
                        ]),
                    "right-panel": p(()=>[
                            c(ve, {
                                ref_key: "rightSideMenuRef",
                                ref: F,
                                position: "right",
                                highlight: "line",
                                expanded: !0,
                                initialWidth: "25vi",
                                maximized: i(v)
                            }, {
                                default: p(()=>[
                                        ee.value ? (C(), j(B, {
                                            key: 0,
                                            id: "workflow-output",
                                            label: "Workflow Output",
                                            icon: "pi pi-list-check"
                                        }, {
                                            default: p(()=>[
                                                    c(lt)
                                                ]),
                                            _: 1
                                        })) : O("", !0),
                                        c(B, {
                                            label: "Preview",
                                            icon: "pi pi-eye",
                                            "no-overflow": ""
                                        }, {
                                            default: p(()=>[
                                                    c(et, {
                                                        previewData: i(U)
                                                    }, null, 8, [
                                                        "previewData"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        c(B, {
                                            id: "file-contents",
                                            label: "File Contents",
                                            icon: "pi pi-file beaker-zoom",
                                            "no-overflow": ""
                                        }, {
                                            default: p(()=>[
                                                    c(Xe, {
                                                        url: re.value?.url,
                                                        mimetype: re.value?.mimetype
                                                    }, null, 8, [
                                                        "url",
                                                        "mimetype"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        c(B, {
                                            id: "media",
                                            label: "Graphs and Images",
                                            icon: "pi pi-chart-bar",
                                            "no-overflow": ""
                                        }, {
                                            default: p(()=>[
                                                    c(We)
                                                ]),
                                            _: 1
                                        }),
                                        c(B, {
                                            id: "kernel-state",
                                            label: "Kernel State",
                                            icon: "pi pi-server",
                                            "no-overflow": ""
                                        }, {
                                            default: p(()=>[
                                                    c(st, {
                                                        data: i(V)
                                                    }, null, 8, [
                                                        "data"
                                                    ])
                                                ]),
                                            _: 1
                                        }),
                                        c(B, {
                                            id: "kernel-logs",
                                            label: "Logs",
                                            icon: "pi pi-list",
                                            position: "bottom"
                                        }, {
                                            default: p(()=>[
                                                    oe(c(He, {
                                                        entries: i(T),
                                                        onClearLogs: k[4] || (k[4] = (W)=>i(T).splice(0, i(T).length))
                                                    }, null, 8, [
                                                        "entries"
                                                    ]), [
                                                        [
                                                            te
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
                    default: p(()=>[
                            M("div", Mt, [
                                oe((C(), j(Ve, {
                                    ref_key: "beakerNotebookRef",
                                    ref: d,
                                    "cell-map": ae
                                }, {
                                    default: p(()=>[
                                            c(Le, {
                                                "default-severity": "",
                                                saveAvailable: !0,
                                                "save-as-filename": i(z),
                                                "truncate-agent-code-cells": D.value,
                                                onUpdateTruncatePreference: k[1] || (k[1] = (W)=>{
                                                    D.value = W;
                                                }),
                                                onNotebookSaved: i($),
                                                onOpenFile: P
                                            }, {
                                                "end-extra": p(()=>[
                                                        c(i(de), {
                                                            onClick: k[0] || (k[0] = (W)=>{
                                                                v.value = !i(v), i(b).setMaximized(i(v));
                                                            }),
                                                            icon: `pi ${i(v) ? "pi-window-minimize" : "pi-window-maximize"}`,
                                                            size: "small",
                                                            text: ""
                                                        }, null, 8, [
                                                            "icon"
                                                        ])
                                                    ]),
                                                _: 1
                                            }, 8, [
                                                "save-as-filename",
                                                "truncate-agent-code-cells",
                                                "onNotebookSaved"
                                            ]),
                                            oe((C(), j(Oe, {
                                                "selected-cell": i(d)?.selectedCellId
                                            }, {
                                                "notebook-background": p(()=>[
                                                        M("div", St, [
                                                            c(Ue)
                                                        ])
                                                    ]),
                                                _: 1
                                            }, 8, [
                                                "selected-cell"
                                            ])), [
                                                [
                                                    te
                                                ]
                                            ]),
                                            N.value ? (C(), X("div", Nt, [
                                                oe(c(i(de), {
                                                    size: "large",
                                                    icon: "pi pi-arrow-down",
                                                    severity: "secondary",
                                                    rounded: "",
                                                    class: "scroll-agent-button",
                                                    "aria-label": "Follow scroll as agent creates cells"
                                                }, null, 512), [
                                                    [
                                                        ye,
                                                        "Select to toggle auto-scroll when the assistant is working and creating cells"
                                                    ]
                                                ])
                                            ])) : O("", !0),
                                            M("div", Pt, [
                                                c(Ke, {
                                                    ref_key: "agentQueryRef",
                                                    ref: x,
                                                    class: "agent-query-container",
                                                    "awaiting-input-cell": i(Q),
                                                    "awaiting-input-question": i(J)
                                                }, null, 8, [
                                                    "awaiting-input-cell",
                                                    "awaiting-input-question"
                                                ])
                                            ])
                                        ]),
                                    _: 1
                                })), [
                                    [
                                        we,
                                        i(e),
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
                    "renderers",
                    "savefile",
                    "onIopubMsg",
                    "onUnhandledMsg",
                    "onAnyMsg",
                    "onSessionStatusChanged"
                ]);
            };
        }
    });
});
export { Kt as default, __tla };
