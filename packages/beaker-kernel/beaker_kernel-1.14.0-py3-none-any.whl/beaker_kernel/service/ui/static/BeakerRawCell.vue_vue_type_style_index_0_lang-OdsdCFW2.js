import { ay as ve, r as b, j as R, o as c, I as w, a as W, w as F, u as m, az as fe, d as P, A as p, aq as ne, K as S, W as L, ar as se, V as z, ak as me, H as h, N as oe, B as g, J as N, i as A, f as $, x as q, y as U, z as K, g as _e, R as ye, S as X, a5 as ge, G as O, aA as be, n as ke } from "./primevue-BhybIXDC.js";
import { i as E, l as he, k as Y, B as we, m as Z, p as Ce, __tla as __tla_0 } from "./renderers-707ItvV_.js";
import { g as re } from "./jupyterlab-Bq9OOClR.js";
import { f as G, __tla as __tla_1 } from "./index-wfwXefED.js";
let st, ct, rt, ot, nt, $e, ze;
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
    let xe;
    nt = {
        __name: "ContainedTextArea",
        props: {
            maxHeight: {
                type: [
                    Number,
                    String
                ],
                default: "12rem"
            }
        },
        emits: [
            "submit"
        ],
        setup (f, { emit: d }) {
            ve((l)=>({
                    fd6f281e: v.maxHeight
                }));
            const v = f, n = d, e = (l)=>{
                t.value = l.target.offsetHeight >= 180;
            }, t = b(!1);
            return (l, a)=>(c(), R(m(fe), {
                    onKeyup: e,
                    onKeydown: [
                        a[0] || (a[0] = W(F((s)=>n("submit"), [
                            "exact",
                            "prevent"
                        ]), [
                            "enter"
                        ])),
                        a[1] || (a[1] = W(F((s)=>s.target.blur(), [
                            "prevent"
                        ]), [
                            "escape"
                        ]))
                    ],
                    autoResize: "",
                    rows: "1",
                    class: w([
                        {
                            "scroll-input": t.value
                        },
                        "resizeable-textarea"
                    ])
                }, null, 8, [
                    "class"
                ]));
        }
    };
    xe = {
        key: 1
    };
    st = P({
        __name: "PreviewPanel",
        props: {
            previewData: {}
        },
        setup (f) {
            const d = f;
            return (v, n)=>d.previewData ? (c(), R(m(ne), {
                    key: 0,
                    multiple: "",
                    activeIndex: [
                        ...Array(d.previewData.length).keys()
                    ],
                    class: "preview-accordion"
                }, {
                    default: S(()=>[
                            (c(!0), p(z, null, L(d.previewData, (e, t)=>(c(), R(m(se), {
                                    key: t,
                                    header: t.toString(),
                                    class: "preview-accordion-tab"
                                }, {
                                    default: S(()=>[
                                            (c(!0), p(z, null, L(e, (l, a)=>(c(), R(m(me), {
                                                    class: "preview-container",
                                                    key: a,
                                                    legend: a.toString(),
                                                    toggleable: !0
                                                }, {
                                                    default: S(()=>[
                                                            h(E, {
                                                                class: "contextpreview-mime-bundle code-cell-output preview-container-table-wrapper",
                                                                mimeBundle: l
                                                            }, null, 8, [
                                                                "mimeBundle"
                                                            ])
                                                        ]),
                                                    _: 2
                                                }, 1032, [
                                                    "legend"
                                                ]))), 128))
                                        ]),
                                    _: 2
                                }, 1032, [
                                    "header"
                                ]))), 128))
                        ]),
                    _: 1
                }, 8, [
                    "activeIndex"
                ])) : (c(), p("div", xe, "No preview yet"));
        }
    });
    $e = P({
        __name: "AnnotationButton",
        props: {
            action: {
                type: Function,
                async default () {
                    console.log("no action defined");
                }
            }
        },
        setup (f) {
            const d = f, v = b(!1), n = async ()=>{
                v.value = !0;
                try {
                    await d.action();
                } finally{
                    v.value = !1;
                }
            };
            return (e, t)=>(c(), R(m(oe), {
                    onClick: n,
                    size: "small",
                    disabled: v.value,
                    loading: v.value
                }, {
                    icon: S(()=>[
                            ...t[0] || (t[0] = [
                                g("span", {
                                    class: "pi pi-search pi-exclamation-triangle"
                                }, null, -1)
                            ])
                        ]),
                    _: 1
                }, 8, [
                    "disabled",
                    "loading"
                ]));
        }
    });
    var D, ee;
    function Ae() {
        if (ee) return D;
        ee = 1, D = t;
        var f = /(?:(?:\u001b\[)|\u009b)(?:(?:[0-9]{1,3})?(?:(?:;[0-9]{0,3})*)?[A-M|f-m])|\u001b[A-M]/, d = {
            reset: [
                "fff",
                "000"
            ],
            black: "000",
            red: "ff0000",
            green: "209805",
            yellow: "e8bf03",
            blue: "0000ff",
            magenta: "ff00ff",
            cyan: "00ffee",
            lightgrey: "f0f0f0",
            darkgrey: "888"
        }, v = {
            30: "black",
            31: "red",
            32: "green",
            33: "yellow",
            34: "blue",
            35: "magenta",
            36: "cyan",
            37: "lightgrey"
        }, n = {
            1: "font-weight:bold",
            2: "opacity:0.5",
            3: "<i>",
            4: "<u>",
            8: "display:none",
            9: "<del>"
        }, e = {
            23: "</i>",
            24: "</u>",
            29: "</del>"
        };
        [
            0,
            21,
            22,
            27,
            28,
            39,
            49
        ].forEach(function(a) {
            e[a] = "</span>";
        });
        function t(a) {
            if (!f.test(a)) return a;
            var s = [], u = a.replace(/\033\[(\d+)m/g, function(k, i) {
                var _ = n[i];
                if (_) return ~s.indexOf(i) ? (s.pop(), "</span>") : (s.push(i), _[0] === "<" ? _ : '<span style="' + _ + ';">');
                var C = e[i];
                return C ? (s.pop(), C) : "";
            }), o = s.length;
            return o > 0 && (u += Array(o + 1).join("</span>")), u;
        }
        t.setColors = function(a) {
            if (typeof a != "object") throw new Error("`colors` parameter must be an Object.");
            var s = {};
            for(var u in d){
                var o = a.hasOwnProperty(u) ? a[u] : null;
                if (!o) {
                    s[u] = d[u];
                    continue;
                }
                if (u === "reset") {
                    if (typeof o == "string" && (o = [
                        o
                    ]), !Array.isArray(o) || o.length === 0 || o.some(function(i) {
                        return typeof i != "string";
                    })) throw new Error("The value of `" + u + "` property must be an Array and each item could only be a hex string, e.g.: FF0000");
                    var k = d[u];
                    o[0] || (o[0] = k[0]), (o.length === 1 || !o[1]) && (o = [
                        o[0]
                    ], o.push(k[1])), o = o.slice(0, 2);
                } else if (typeof o != "string") throw new Error("The value of `" + u + "` property must be a hex string, e.g.: FF0000");
                s[u] = o;
            }
            l(s);
        }, t.reset = function() {
            l(d);
        }, t.tags = {}, Object.defineProperty ? (Object.defineProperty(t.tags, "open", {
            get: function() {
                return n;
            }
        }), Object.defineProperty(t.tags, "close", {
            get: function() {
                return e;
            }
        })) : (t.tags.open = n, t.tags.close = e);
        function l(a) {
            n[0] = "font-weight:normal;opacity:1;color:#" + a.reset[0] + ";background:#" + a.reset[1], n[7] = "color:#" + a.reset[1] + ";background:#" + a.reset[0], n[90] = "color:#" + a.darkgrey;
            for(var s in v){
                var u = v[s], o = a[u] || "000";
                n[s] = "color:#" + o, s = parseInt(s), n[(s + 10).toString()] = "background:#" + o;
            }
        }
        return t.reset(), D;
    }
    var Re = Ae();
    const te = re(Re);
    var I, ae;
    function He() {
        if (ae) return I;
        ae = 1;
        var f = /["'&<>]/;
        I = d;
        function d(v) {
            var n = "" + v, e = f.exec(n);
            if (!e) return n;
            var t, l = "", a = 0, s = 0;
            for(a = e.index; a < n.length; a++){
                switch(n.charCodeAt(a)){
                    case 34:
                        t = "&quot;";
                        break;
                    case 38:
                        t = "&amp;";
                        break;
                    case 39:
                        t = "&#39;";
                        break;
                    case 60:
                        t = "&lt;";
                        break;
                    case 62:
                        t = "&gt;";
                        break;
                    default:
                        continue;
                }
                s !== a && (l += n.substring(s, a)), s = a + 1, l += t;
            }
            return s !== a ? l + n.substring(s, a) : l;
        }
        return I;
    }
    var Se = He();
    let le, Be, Pe, Me, Ee, Ve, je, Te, Le, De, Ie, Fe, Ne, Oe, qe, Ue, Ke, Ye, Ge, Je, Qe, We, Xe;
    le = re(Se);
    Be = {
        key: 0
    };
    Pe = {
        class: "code-cell-output-box-dropdown"
    };
    Me = [
        "innerHTML"
    ];
    Ee = {
        key: 3
    };
    Ve = {
        key: 1
    };
    je = [
        "onClickCapture"
    ];
    Te = [
        "innerHTML"
    ];
    Le = {
        key: 3
    };
    ze = P({
        __name: "BeakerCodeCellOutput",
        props: [
            "outputs",
            "busy",
            "dropdownLayout"
        ],
        setup (f) {
            const d = f, v = (e)=>{
                const t = b(e?.metadata || (e.metadata = {}));
                t.value.collapsed = !t.value.collapsed;
            }, n = (e)=>{
                const t = Array.isArray(e.traceback) ? e.traceback?.join(`
`) : e.traceback?.toString();
                return {
                    "application/vnd.jupyter.error": e,
                    "application/vnd.jupyter.stderr": t || `${e.ename}: ${e.evalue}`
                };
            };
            return (e, t)=>(c(), p("div", {
                    class: w([
                        "code-cell-output",
                        {
                            "code-cell-output-dropdown": d.dropdownLayout
                        }
                    ])
                }, [
                    f.dropdownLayout ? (c(), p("div", Be, [
                        g("div", Pe, [
                            h(m(ne), null, {
                                default: S(()=>[
                                        h(m(se), {
                                            class: "code-cell-output-dropdown-tab",
                                            pt: {
                                                header: {
                                                    class: [
                                                        "code-cell-output-dropdown-header"
                                                    ]
                                                },
                                                headerAction: {
                                                    class: [
                                                        "code-cell-output-dropdown-headeraction"
                                                    ]
                                                },
                                                content: {
                                                    class: [
                                                        "code-cell-output-dropdown-content"
                                                    ]
                                                },
                                                headerIcon: {
                                                    class: [
                                                        "code-cell-output-dropdown-icon"
                                                    ]
                                                }
                                            }
                                        }, {
                                            header: S(()=>[
                                                    ...t[0] || (t[0] = [
                                                        g("span", {
                                                            class: "flex align-items-center gap-2 w-full",
                                                            style: {
                                                                "font-weight": "normal"
                                                            }
                                                        }, [
                                                            g("span", null, "Outputs")
                                                        ], -1)
                                                    ])
                                                ]),
                                            default: S(()=>[
                                                    (c(!0), p(z, null, L(d.outputs, (l)=>(c(), p("div", {
                                                            class: "code-cell-dropdown-content",
                                                            key: `${l}-dropdown`
                                                        }, [
                                                            l.output_type == "stream" ? (c(), p("div", {
                                                                key: 0,
                                                                class: w(l.output_type),
                                                                innerHTML: m(te)(m(le)(l.text))
                                                            }, null, 10, Me)) : [
                                                                "display_data",
                                                                "execute_result"
                                                            ].includes(l.output_type) ? (c(), R(E, {
                                                                key: 1,
                                                                "mime-bundle": l.data,
                                                                class: "mime-bundle",
                                                                collapse: "true"
                                                            }, null, 8, [
                                                                "mime-bundle"
                                                            ])) : l.output_type == "error" ? (c(), p("div", {
                                                                key: 2,
                                                                class: w(l.output_type)
                                                            }, [
                                                                h(E, {
                                                                    "mime-bundle": n(l),
                                                                    collapse: "true"
                                                                }, null, 8, [
                                                                    "mime-bundle"
                                                                ])
                                                            ], 2)) : (c(), p("div", Ee, N(l), 1))
                                                        ]))), 128))
                                                ]),
                                            _: 1
                                        })
                                    ]),
                                _: 1
                            })
                        ])
                    ])) : (c(), p("div", Ve, [
                        (c(!0), p(z, null, L(d.outputs, (l)=>(c(), p("div", {
                                class: w([
                                    "code-cell-output-box",
                                    {
                                        "collapsed-output": l.metadata?.collapsed
                                    }
                                ]),
                                key: l
                            }, [
                                g("div", {
                                    class: "output-collapse-box",
                                    onClickCapture: F((a)=>v(l), [
                                        "stop",
                                        "prevent"
                                    ])
                                }, null, 40, je),
                                l.output_type == "stream" ? (c(), p("div", {
                                    key: 0,
                                    class: w(l.output_type),
                                    innerHTML: m(te)(m(le)(l.text))
                                }, null, 10, Te)) : [
                                    "display_data",
                                    "execute_result"
                                ].includes(l.output_type) ? (c(), R(E, {
                                    key: 1,
                                    "mime-bundle": l.data,
                                    class: "mime-bundle",
                                    collapse: "true"
                                }, null, 8, [
                                    "mime-bundle"
                                ])) : l.output_type == "error" ? (c(), p("div", {
                                    key: 2,
                                    class: w(l.output_type)
                                }, [
                                    h(E, {
                                        "mime-bundle": n(l),
                                        collapse: "true"
                                    }, null, 8, [
                                        "mime-bundle"
                                    ])
                                ], 2)) : (c(), p("div", Le, N(l), 1))
                            ], 2))), 128))
                    ]))
                ], 2));
        }
    });
    De = {
        class: "code-cell"
    };
    Ie = {
        class: "code-cell-grid"
    };
    Fe = {
        class: "code-output"
    };
    Ne = {
        class: "state-info"
    };
    Oe = {
        key: 0,
        class: "pi pi-spin pi-spinner busy-icon"
    };
    qe = {
        modelClass: he,
        icon: "pi pi-code"
    };
    ot = P({
        ...qe,
        __name: "BeakerCodeCell",
        props: [
            "cell",
            "hideOutput",
            "codeStyles"
        ],
        emits: [
            "blur"
        ],
        setup (f, { expose: d, emit: v }) {
            const n = f, e = b(n.cell), { theme: t } = A("theme"), l = A("session"), a = b(), s = A("beakerSession"), u = A("notebook"), o = U(), k = b([]);
            let i;
            ((r)=>{
                r.Success = "ok", r.Modified = "modified", r.Error = "error", r.Pending = "pending", r.None = "none";
            })(i || (i = {}));
            const _ = $(()=>typeof e.value?.last_execution?.checkpoint_index < "u"), C = ()=>e.value.rollback(l), B = $(()=>e.value?.busy), J = async ()=>{
                const r = {
                    notebook_id: u.id,
                    cells: [
                        {
                            cell_id: e.value.id,
                            content: e.value.source
                        }
                    ]
                };
                await l.executeAction("lint_code", r).done;
            }, V = $(()=>{
                const r = "secondary";
                return {
                    ok: "success",
                    modified: "warning",
                    error: "danger",
                    pending: r,
                    none: r
                }[e.value?.last_execution?.status] || r;
            }), y = (r)=>{
                u && u.selectCell(e.value), r.stopPropagation();
            };
            function H() {
                e.value.reset_execution_state();
            }
            const j = $(()=>s.activeContext?.language?.slug || void 0), ce = (r)=>{
                n.cell.execute(l), Q();
            }, ie = (r)=>{
                a.value?.focus(), r === "start" ? r = 0 : r === "end" && (r = a.value?.view?.state?.doc?.length), r !== void 0 && a.value?.view?.dispatch({
                    selection: {
                        anchor: r,
                        head: r
                    }
                });
            }, Q = ()=>{
                a.value?.blur();
                const r = o.vnode.el;
                G(r)?.focus();
            };
            d({
                execute: ce,
                enter: ie,
                exit: Q,
                clear: ()=>{
                    e.value.source = "", e.value.outputs.splice(0, e.value.outputs.length);
                },
                cell: e,
                editor: a,
                lintAnnotations: k
            }), q(()=>{
                s.cellRegistry[e.value.id] = o.vnode;
            }), K(()=>{
                delete s.cellRegistry[e.value.id];
            });
            const ue = $(()=>e.value.metadata?.source_cell_id && e.value.metadata?.beaker_cell_type === "code"), de = $(()=>ue.value && (e.value.execution_count === null || e.value.execution_count === void 0));
            return _e(()=>{
                if (!de.value) return null;
                const r = e.value.metadata?.source_cell_id, x = e.value.metadata?.parent_query_cell;
                if (r && x) {
                    const M = s.session.notebook.cells.find((T)=>T.id === x);
                    if (M && M.children) return M.children.find((pe)=>pe.id === r)?.execution_count;
                }
                return null;
            }, (r)=>{
                r != null && (e.value.execution_count = r);
            }), (r, x)=>{
                const M = ye("tooltip");
                return c(), p("div", De, [
                    g("div", Ie, [
                        g("div", {
                            class: w([
                                "code-data",
                                {
                                    "dark-mode": m(t).mode === "dark",
                                    [f.codeStyles]: n.codeStyles
                                }
                            ])
                        }, [
                            h(Y, {
                                "display-mode": "dark",
                                language: j.value,
                                modelValue: e.value.source,
                                "onUpdate:modelValue": x[0] || (x[0] = (T)=>e.value.source = T),
                                ref_key: "codeEditorRef",
                                ref: a,
                                placeholder: "Your code...",
                                disabled: B.value,
                                onChange: H,
                                onClick: y,
                                annotations: k.value,
                                "annotation-provider": "linter"
                            }, null, 8, [
                                "language",
                                "modelValue",
                                "disabled",
                                "annotations"
                            ])
                        ], 2),
                        g("div", Fe, [
                            X(h(ze, {
                                outputs: e.value.outputs,
                                busy: B.value,
                                "dropdown-layout": !1
                            }, null, 8, [
                                "outputs",
                                "busy"
                            ]), [
                                [
                                    ge,
                                    !f.hideOutput && e.value.outputs.length
                                ]
                            ])
                        ]),
                        g("div", Ne, [
                            g("div", null, [
                                h(m(be), {
                                    class: w([
                                        "execution-count-badge",
                                        {
                                            secondary: V.value === "secondary"
                                        }
                                    ]),
                                    severity: V.value,
                                    value: e.value.execution_count || " "
                                }, null, 8, [
                                    "class",
                                    "severity",
                                    "value"
                                ])
                            ]),
                            B.value ? (c(), p("i", Oe)) : O("", !0),
                            X(h($e, {
                                action: J,
                                text: ""
                            }, null, 512), [
                                [
                                    M,
                                    {
                                        value: "Analyze this code.",
                                        showDelay: 300
                                    },
                                    void 0,
                                    {
                                        bottom: !0
                                    }
                                ]
                            ]),
                            _.value ? (c(), R(m(oe), {
                                key: 1,
                                class: "rollback-button",
                                severity: V.value,
                                icon: "pi pi-undo",
                                size: "small",
                                onClick: C
                            }, null, 8, [
                                "severity"
                            ])) : O("", !0)
                        ])
                    ])
                ]);
            };
        }
    });
    Ue = [
        "innerHTML"
    ];
    Ke = {
        key: 1
    };
    Ye = {
        class: "markdown-edit-cell-grid"
    };
    Ge = {
        modelClass: we,
        icon: "pi pi-pencil"
    };
    rt = P({
        ...Ge,
        __name: "BeakerMarkdownCell",
        props: [
            "cell"
        ],
        setup (f, { expose: d }) {
            const v = f, n = U(), e = A("beakerSession"), t = b(v.cell), { theme: l } = A("theme"), a = b(!1), s = b(null), u = b(null), o = A("notebook"), k = b(t.value.source), i = $(()=>Z.parse(v.cell?.source || "")), _ = (y)=>{
                o.selectCell(t.value), y.stopPropagation();
            }, C = ()=>{
                a.value = !1, t.value.source = k.value;
            }, B = (y)=>{
                a.value || (a.value = !0), ke(()=>{
                    u.value?.focus(), y === "start" ? y = 0 : y === "end" && (y = u.value?.view?.state?.doc?.length), y !== void 0 && u.value?.view?.dispatch({
                        selection: {
                            anchor: y,
                            head: y
                        }
                    });
                });
            };
            return d({
                execute: C,
                enter: B,
                exit: ()=>{
                    if (k.value === t.value.source) a.value = !1;
                    else {
                        u.value?.blur();
                        const y = n.vnode.el;
                        G(y)?.focus();
                    }
                },
                clear: ()=>{
                    t.value.source = "";
                },
                model: t,
                editor: u
            }), q(()=>{
                Z.setOptions({}), e.cellRegistry[t.value.id] = n.vnode;
            }), K(()=>{
                delete e.cellRegistry[t.value.id];
            }), (y, H)=>(c(), p("div", {
                    class: "markdown-cell",
                    onDblclick: H[1] || (H[1] = (j)=>B())
                }, [
                    a.value ? (c(), p("div", Ke, [
                        g("div", Ye, [
                            g("div", {
                                class: w([
                                    "markdown-edit-data",
                                    {
                                        "dark-mode": m(l).mode === "dark"
                                    }
                                ]),
                                ref: s.value
                            }, [
                                h(Y, {
                                    modelValue: k.value,
                                    "onUpdate:modelValue": H[0] || (H[0] = (j)=>k.value = j),
                                    placeholder: "Your markdown...",
                                    ref_key: "codeEditorRef",
                                    ref: u,
                                    autofocus: !1,
                                    language: "markdown",
                                    "display-mode": "dark",
                                    onClick: _
                                }, null, 8, [
                                    "modelValue"
                                ])
                            ], 2)
                        ])
                    ])) : (c(), p("div", {
                        key: 0,
                        innerHTML: i.value
                    }, null, 8, Ue))
                ], 32));
        }
    });
    Je = {
        class: "raw-cell"
    };
    Qe = {
        class: "raw-cell-header"
    };
    We = {
        key: 0
    };
    Xe = {
        modelClass: Ce,
        icon: "pi pi-question-circle"
    };
    ct = P({
        ...Xe,
        __name: "BeakerRawCell",
        props: [
            "cell"
        ],
        setup (f, { expose: d }) {
            const v = f, n = U(), e = b(v.cell), t = b(null), l = A("beakerSession");
            let a;
            ((i)=>{
                i.Success = "success", i.Modified = "modified", i.Error = "error", i.Pending = "pending";
            })(a || (a = {})), $(()=>[]);
            const s = (i)=>{
                o();
            }, u = (i)=>{
                t.value?.focus(), i === "start" ? i = 0 : i === "end" && (i = t.value?.view?.state?.doc?.length), i !== void 0 && t.value?.view?.dispatch({
                    selection: {
                        anchor: i,
                        head: i
                    }
                });
            }, o = ()=>{
                t.value.blur();
                const i = n.vnode.el;
                G(i)?.focus();
            };
            return d({
                execute: s,
                enter: u,
                exit: o,
                clear: ()=>{
                    e.value.source = "";
                },
                model: e,
                editor: t
            }), q(()=>{
                l.cellRegistry[e.value.id] = n.vnode;
            }), K(()=>{
                delete l.cellRegistry[e.value.id];
            }), (i, _)=>(c(), p("div", Je, [
                    g("div", Qe, [
                        _[1] || (_[1] = g("span", {
                            class: "raw-cell-title"
                        }, "Raw cell", -1)),
                        v.cell.cell_type !== "raw" ? (c(), p("span", We, " - (Unrenderable cell type '" + N(v.cell.cell_type) + "')", 1)) : O("", !0)
                    ]),
                    h(Y, {
                        "display-mode": "dark",
                        language: "julia",
                        modelValue: e.value.source,
                        "onUpdate:modelValue": _[0] || (_[0] = (C)=>e.value.source = C),
                        ref_key: "codeEditorRef",
                        ref: t,
                        placeholder: "Raw cell content...",
                        autofocus: !1
                    }, null, 8, [
                        "modelValue"
                    ])
                ]));
        }
    });
});
export { st as _, ct as a, rt as b, ot as c, nt as d, $e as e, ze as f, __tla };
