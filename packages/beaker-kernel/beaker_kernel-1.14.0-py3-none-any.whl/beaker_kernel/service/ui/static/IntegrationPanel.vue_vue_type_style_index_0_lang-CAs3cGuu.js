import { d as O, r as g, A as b, o as f, H as u, u as i, ag as U, K as x, N as I, a2 as A, a8 as B, B as m, a9 as F, am as K, g as V, V as Z, f as j, w as X, a6 as W, G as C, j as S, J as M, ai as Y, i as ee, R as te, S as ne, W as ae, ao as oe, a1 as se } from "./primevue-BhybIXDC.js";
import { _ as G } from "./_plugin-vue_export-helper-DlAUqK2U.js";
import { _ as re } from "./jupyterlab-Bq9OOClR.js";
import { getDocument as z, __tla as __tla_0 } from "./pdfjs-B7zhfHd9.js";
import { k as N, i as ie, m as le, __tla as __tla_1 } from "./renderers-707ItvV_.js";
import { R as q, __tla as __tla_2 } from "./index-wfwXefED.js";
let et, tt, Je, Ge, Ke, Qe, Ye, de, Xe, Ze, He;
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
    const ue = (e)=>[
            e.sessionId,
            e?.integrationId,
            e?.resourceType,
            e?.resourceId
        ].filter((t)=>t).join("/");
    async function R(e, t, s) {
        const n = `/beaker/integrations/${ue(t)}`;
        console.log(`api request: ${e} ${n}`);
        const h = await fetch(n, {
            method: e,
            headers: {
                "Content-Type": "application/json"
            },
            ...s === void 0 ? {} : {
                body: JSON.stringify(s)
            }
        });
        if (!h.ok) throw new Error(h.statusText);
        return await h.json();
    }
    de = (e)=>e.provider.split(":")[0];
    Ze = async (e)=>(await R("GET", {
            sessionId: e
        })).integrations;
    Ge = async (e, t)=>await R("POST", {
            sessionId: e
        }, t);
    He = async (e, t, s)=>await R("POST", {
            sessionId: e,
            integrationId: t
        }, s);
    Je = async (e, t)=>(await R("GET", {
            sessionId: e,
            integrationId: t,
            resourceType: "all"
        })).resources;
    Qe = async (e, t, s)=>await R("POST", {
            sessionId: e,
            integrationId: t,
            resourceType: "new"
        }, s);
    Ke = async (e, t, s, n)=>await R("POST", {
            sessionId: e,
            integrationId: t,
            resourceType: "new",
            resourceId: s
        }, n);
    Xe = async (e, t, s)=>await R("DELETE", {
            sessionId: e,
            integrationId: t,
            resourceType: "any",
            resourceId: s
        });
    Ye = function(e, t) {
        return Object.fromEntries(Object.entries(e ?? {}).filter(([s, n])=>n.resource_type === t));
    };
    let ce, pe, ve, fe, me, ge, ye, we, he, _e, ke, be, xe, $e, Ce, Pe, Le, Te, Ie, Re, Ee, Se, Ve, De, je, Me, Oe, Ae, Be;
    ce = O({
        __name: "PDFControls",
        props: [
            "page",
            "scale",
            "isLoading",
            "sidebarCallback"
        ],
        emits: [
            "pdf-page-next",
            "pdf-page-prev",
            "pdf-zoom-in",
            "pdf-zoom-out"
        ],
        setup (e, { emit: t }) {
            const s = e, n = t, h = g(null), y = (d)=>`${Math.floor(d * 100)}%`;
            return (d, o)=>(f(), b("div", {
                    ref_key: "controlsContainer",
                    ref: h,
                    class: "controls-container"
                }, [
                    u(i(U), null, {
                        start: x(()=>[
                                u(i(I), {
                                    class: "pdf-ui-button",
                                    icon: "pi pi-chevron-left",
                                    onClick: o[0] || (o[0] = (l)=>n("pdf-page-prev")),
                                    disabled: e.isLoading
                                }, null, 8, [
                                    "disabled"
                                ]),
                                u(i(I), {
                                    class: "pdf-ui-button",
                                    icon: "pi pi-chevron-right",
                                    onClick: o[1] || (o[1] = (l)=>n("pdf-page-next")),
                                    disabled: e.isLoading
                                }, null, 8, [
                                    "disabled"
                                ]),
                                u(i(A), {
                                    class: "pdf-ui-inputselection"
                                }, {
                                    default: x(()=>[
                                            u(i(B), null, {
                                                default: x(()=>[
                                                        ...o[4] || (o[4] = [
                                                            m("i", {
                                                                class: "pi pi-book"
                                                            }, null, -1)
                                                        ])
                                                    ]),
                                                _: 1
                                            }),
                                            u(i(F), {
                                                placeholder: "Page",
                                                value: s?.page
                                            }, null, 8, [
                                                "value"
                                            ])
                                        ]),
                                    _: 1
                                })
                            ]),
                        center: x(()=>[
                                u(i(I), {
                                    class: "pdf-ui-button",
                                    icon: "pi pi-search-minus",
                                    onClick: o[2] || (o[2] = (l)=>n("pdf-zoom-out"))
                                }),
                                u(i(I), {
                                    class: "pdf-ui-button",
                                    icon: "pi pi-search-plus",
                                    onClick: o[3] || (o[3] = (l)=>n("pdf-zoom-in"))
                                }),
                                u(i(A), {
                                    class: "pdf-ui-inputselection"
                                }, {
                                    default: x(()=>[
                                            u(i(B), null, {
                                                default: x(()=>[
                                                        ...o[5] || (o[5] = [
                                                            m("i", {
                                                                class: "pi pi-search"
                                                            }, null, -1)
                                                        ])
                                                    ]),
                                                _: 1
                                            }),
                                            u(i(F), {
                                                placeholder: "Zoom",
                                                value: y(s?.scale)
                                            }, null, 8, [
                                                "value"
                                            ])
                                        ]),
                                    _: 1
                                })
                            ]),
                        _: 1
                    })
                ], 512));
        }
    });
    pe = G(ce, [
        [
            "__scopeId",
            "data-v-b6ee0017"
        ]
    ]);
    ve = {
        __name: "PDFPage",
        props: [
            "sidebarCallback",
            "url",
            "scale",
            "page"
        ],
        setup (e, { expose: t }) {
            const s = async function() {
                const p = await re(()=>import("./pdfjs-B7zhfHd9.js").then(async (m)=>{
                        await m.__tla;
                        return m;
                    }), []);
                p.GlobalWorkerOptions.workerSrc = new URL("/static/pdf.worker-BQQyum15.mjs", import.meta.url).toString();
            }, n = e, h = g(null), y = g(null);
            let d = null;
            const o = g(!1), l = g(null);
            let c = null;
            const k = async (p)=>{
                if (!d) return;
                o.value = !0;
                const a = await d.getPage(p), _ = a.getViewport({
                    scale: n.scale
                });
                if (!y.value) return;
                const w = y.value.getContext("2d");
                y.value.width = _.width, y.value.height = _.height;
                const T = {
                    canvasContext: w,
                    viewport: _
                };
                c = a.render(T), await c.promise, o.value = !1;
            }, P = async ()=>{
                if (typeof n.url == "object" && n.url instanceof File) {
                    const p = new FileReader;
                    p.readAsArrayBuffer(n.url), p.onload = async (a)=>{
                        d = await z({
                            data: a.target.result
                        }).promise, l.value = d?._pdfInfo?.numPages, k(n.page);
                    };
                } else typeof n.url == "string" && (d = await z(n.url).promise, l.value = d?._pdfInfo?.numPages, k(n.page));
            };
            return t({
                pages: l,
                isLoading: o,
                renderTask: c
            }), K(async ()=>{
                await s(), await P();
            }), V(()=>[
                    n.url
                ], P), V(()=>[
                    n.scale,
                    n.page
                ], ()=>k(n.page)), (p, a)=>(f(), b("div", {
                    ref_key: "pdfContainer",
                    ref: h,
                    class: "pdf-container"
                }, [
                    m("canvas", {
                        ref_key: "canvas",
                        ref: y,
                        class: "pdf-canvas"
                    }, null, 512)
                ], 512));
        }
    };
    fe = G(ve, [
        [
            "__scopeId",
            "data-v-e9dd6f42"
        ]
    ]);
    me = 4;
    ge = O({
        __name: "PDFPreview",
        props: {
            url: {}
        },
        setup (e, { expose: t }) {
            const s = [
                .25,
                .5,
                .75,
                .9,
                1,
                1.1,
                1.25,
                1.5,
                2,
                3,
                4
            ], n = (l, c, k)=>l <= c ? c : l >= k ? k : l, h = e, y = g(1), d = g(null), o = g(me);
            return t({
                pdf: d
            }), (l, c)=>(f(), b(Z, null, [
                    u(pe, {
                        onPdfPageNext: c[0] || (c[0] = ()=>{
                            y.value = n(y.value + 1, 1, d.value?.pages ?? 1);
                        }),
                        onPdfPagePrev: c[1] || (c[1] = ()=>{
                            y.value = n(y.value - 1, 1, d.value?.pages ?? 1);
                        }),
                        onPdfZoomIn: c[2] || (c[2] = ()=>{
                            o.value = n(o.value + 1, 0, s.length - 1);
                        }),
                        onPdfZoomOut: c[3] || (c[3] = ()=>{
                            o.value = n(o.value - 1, 0, s.length - 1);
                        }),
                        page: y.value,
                        scale: s[o.value]
                    }, null, 8, [
                        "page",
                        "scale"
                    ]),
                    u(fe, {
                        ref_key: "pdf",
                        ref: d,
                        url: h.url,
                        scale: s[o.value],
                        page: y.value
                    }, null, 8, [
                        "url",
                        "scale",
                        "page"
                    ])
                ], 64));
        }
    });
    ye = {
        class: "preview-container-pre"
    };
    we = {
        key: 0,
        class: "preview-standard-toolbar"
    };
    he = {
        class: "preview-under-toolbar"
    };
    _e = {
        key: 0
    };
    ke = {
        key: 1,
        class: "preview-payload"
    };
    be = {
        key: 0,
        class: "pdf-preview"
    };
    xe = {
        key: 1,
        class: "text-preview"
    };
    $e = {
        key: 2,
        class: "image-preview"
    };
    Ce = [
        "src"
    ];
    Pe = {
        key: 3,
        class: "csv-preview"
    };
    Le = 500;
    Te = 260;
    et = O({
        __name: "FileContentsPanel",
        props: [
            "url",
            "mimetype"
        ],
        setup (e) {
            const t = g(), s = g(), n = g(""), h = g(!1), y = ()=>{
                const r = ($)=>{
                    const E = window.innerWidth - ($.x - P.value / 2);
                    p.value = Math.min(Math.max(E, Te), window.innerWidth * .9);
                }, v = ()=>{
                    document.querySelector("body").removeEventListener("mousemove", r), document.querySelector("body").removeEventListener("mouseup", this);
                };
                document.querySelector("body").addEventListener("mousemove", r), document.querySelector("body").addEventListener("mouseup", v);
            }, d = (r)=>r.startsWith("image/") ? "image" : r === "application/pdf" ? "pdf" : r === "text/csv" ? "csv" : r === "text/tsv" ? "tsv" : r === "application/vnd.ms-excel" || r === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ? "excel" : "plaintext", o = {
                "application/pdf": {
                    overridesToolbar: !0,
                    skipContents: !0
                },
                "image/png": {
                    skipContents: !0
                },
                "text/csv": {
                    hasRawToggle: !0
                },
                "text/tsv": {
                    hasRawToggle: !0
                }
            }, l = g({
                isLoading: !1,
                contentLength: -1
            }), c = g(!1), k = new TextDecoder, P = g(5), p = g(614 + P.value), a = e, _ = j(()=>a.mimetype ?? n.value ?? ""), w = g(), T = j(()=>{
                const r = l.value?.contents, v = d(_.value);
                return v === "image" || v === "pdf" ? "<loaded elsewhere via url>" : r ? r.length === 0 ? "<file is 0 bytes>" : v === "excel" ? r : k.decode(r) : "";
            });
            V(()=>[
                    T.value
                ], (r, v)=>{
                t.value && (t.value.model = r[0]);
            });
            const H = j(()=>{
                const r = a.url?.split("/");
                return r === void 0 ? "No file selected." : r.length > 0 ? r[r.length - 1] : "";
            }), J = async (r)=>{
                const v = await fetch(r, {
                    method: "HEAD"
                });
                return [
                    "Content-Type",
                    "Content-Length"
                ].map(($)=>v.headers.get($));
            }, Q = async (r)=>{
                w.value = new AbortController;
                const v = await fetch(r, {
                    signal: w.value.signal
                }), $ = [];
                for await (const L of v.body)$.push(L);
                if ($.length === 0) return [];
                const E = new Uint8Array($.map((L)=>L.length).reduce((L, D)=>L + D));
                return $.reduce((L, D)=>(E.set(D, L), L + D.length), 0), E;
            };
            return V(()=>[
                    a.url,
                    a.mimetype
                ], async (r, v)=>{
                v.length >= 2 && v[1] === "application/pdf" && console.log("interrupted pdf rendering for another preview"), l.value = {
                    isLoading: !0,
                    contentLength: 0
                };
                const $ = setTimeout(()=>{
                    c.value = !0;
                }, Le), [E, L] = await J(a.url);
                a.mimetype === void 0 || a.mimetype == null ? n.value = E : n.value = void 0, l.value.contentLength = parseInt(L, 10), (o[a.mimetype] ?? {})?.skipContents || (l.value.contents = await Q(a.url)), l.value.isLoading = !1, c.value = !1, clearTimeout($);
            }), (r, v)=>(f(), b("div", ye, [
                    m("div", {
                        class: "preview-draggable",
                        style: W(`width: ${P.value}px;`),
                        onMousedown: v[0] || (v[0] = X(($)=>y(), [
                            "left",
                            "prevent"
                        ]))
                    }, null, 36),
                    m("div", {
                        class: "preview-container-main",
                        style: W(`max-width: calc(100% - ${P.value}px);`)
                    }, [
                        o[_.value]?.overridesToolbar ? C("", !0) : (f(), b("div", we, [
                            u(i(U), null, {
                                center: x(()=>[
                                        m("span", null, M(H.value), 1)
                                    ]),
                                end: x(()=>[
                                        o[_.value]?.hasRawToggle ? (f(), S(i(I), {
                                            key: 0,
                                            class: "preview-raw",
                                            onClick: v[1] || (v[1] = ($)=>h.value = !h.value),
                                            label: h.value ? "Rich View" : "Raw View"
                                        }, null, 8, [
                                            "label"
                                        ])) : C("", !0)
                                    ]),
                                _: 1
                            })
                        ])),
                        m("div", he, [
                            c.value && l.value.isLoading ? (f(), b("div", _e, [
                                u(i(I), {
                                    class: "preview-cancel",
                                    onClick: v[2] || (v[2] = ($)=>w.value.abort()),
                                    severity: "danger",
                                    label: "Cancel Preview"
                                }),
                                m("span", null, "File is " + M(l.value.contentLength / 1e6) + " MB", 1)
                            ])) : C("", !0),
                            l.value.isLoading ? C("", !0) : (f(), b("div", ke, [
                                d(_.value) === "pdf" ? (f(), b("div", be, [
                                    u(ge, {
                                        ref_key: "pdfPreviewRef",
                                        ref: s,
                                        url: e.url
                                    }, null, 8, [
                                        "url"
                                    ])
                                ])) : C("", !0),
                                d(_.value) === "plaintext" ? (f(), b("div", xe, [
                                    u(N, {
                                        readonly: !0,
                                        "display-mode": "dark",
                                        modelValue: T.value,
                                        ref_key: "codeEditorRef",
                                        ref: t,
                                        placeholder: "Loading...",
                                        language: _.value === "text/x-python" ? "python" : void 0
                                    }, null, 8, [
                                        "modelValue",
                                        "language"
                                    ])
                                ])) : C("", !0),
                                d(_.value) === "image" ? (f(), b("div", $e, [
                                    m("img", {
                                        src: e.url
                                    }, null, 8, Ce)
                                ])) : C("", !0),
                                [
                                    "csv",
                                    "tsv",
                                    "excel"
                                ].includes(d(_.value)) ? (f(), b("div", Pe, [
                                    !h.value && !l.value.isLoading ? (f(), S(ie, {
                                        key: 0,
                                        mimeBundle: {
                                            [_.value]: T.value
                                        }
                                    }, null, 8, [
                                        "mimeBundle"
                                    ])) : C("", !0),
                                    h.value ? (f(), S(N, {
                                        key: 1,
                                        "display-mode": "dark",
                                        modelValue: T.value,
                                        ref_key: "codeEditorRef",
                                        ref: t,
                                        placeholder: "Loading..."
                                    }, null, 8, [
                                        "modelValue"
                                    ])) : C("", !0)
                                ])) : C("", !0)
                            ]))
                        ])
                    ], 4)
                ]));
        }
    });
    Ie = {
        class: "integrations-panel"
    };
    Re = {
        class: "integration-header"
    };
    Ee = {
        style: {
            display: "flex",
            "flex-direction": "column",
            "padding-top": "0.25rem",
            "padding-bottom": "0.25rem",
            gap: "0.5rem",
            width: "100%"
        }
    };
    Se = {
        style: {
            display: "flex",
            "flex-direction": "column",
            "padding-top": "0.25rem",
            "padding-bottom": "0.25rem",
            gap: "0.5rem",
            width: "100%"
        }
    };
    Ve = {
        class: "integration-list"
    };
    De = {
        class: "integration-provider"
    };
    je = [
        "onMouseenter"
    ];
    Me = {
        class: "integration-card-title"
    };
    Oe = {
        class: "integration-card-title-text"
    };
    Ae = {
        key: 0
    };
    Be = [
        "innerHTML"
    ];
    tt = O({
        __name: "IntegrationPanel",
        props: {
            modelValue: {},
            modelModifiers: {}
        },
        emits: [
            "update:modelValue"
        ],
        setup (e) {
            const t = g(void 0), s = Y(e, "modelValue"), n = new URLSearchParams(window.location.search), h = n.has("session") ? `&session=${n.get("session")}` : "";
            ee("beakerSession");
            const y = (p)=>p.toSorted((a, _)=>a?.name.localeCompare(_?.name)), d = (p)=>p.filter((a)=>t?.value === void 0 || a?.name?.toLowerCase()?.includes(t?.value?.toLowerCase())), o = (p)=>p.map((a)=>({
                        ...a,
                        description: le.parse(a?.description ?? "")
                    })), l = (p)=>o(d(y(p))), c = j(()=>Object.values(s.value)), k = g(void 0), P = g(void 0);
            return V(t, ()=>{
                const p = d(c.value);
                if (p.length === 1) {
                    k.value = p[0].slug;
                    return;
                }
                k.value = void 0;
            }), (p, a)=>{
                const _ = te("tooltip");
                return f(), b("div", Ie, [
                    m("div", Re, [
                        u(i(A), null, {
                            default: x(()=>[
                                    u(i(B), null, {
                                        default: x(()=>[
                                                ...a[3] || (a[3] = [
                                                    m("i", {
                                                        class: "pi pi-search"
                                                    }, null, -1)
                                                ])
                                            ]),
                                        _: 1
                                    }),
                                    u(i(F), {
                                        placeholder: "Search Integrations...",
                                        modelValue: t.value,
                                        "onUpdate:modelValue": a[0] || (a[0] = (w)=>t.value = w)
                                    }, null, 8, [
                                        "modelValue"
                                    ]),
                                    t.value !== void 0 && t.value !== "" ? ne((f(), S(i(I), {
                                        key: 0,
                                        icon: "pi pi-times",
                                        severity: "danger",
                                        onClick: a[1] || (a[1] = ()=>{
                                            t.value = void 0;
                                        })
                                    }, null, 512)), [
                                        [
                                            _,
                                            "Clear Search"
                                        ]
                                    ]) : C("", !0)
                                ]),
                            _: 1
                        }),
                        m("div", Ee, [
                            u(i(q), {
                                to: `/integrations?selected=new${i(h)}`,
                                "aria-label": "Edit {{ integration?.name }} "
                            }, {
                                default: x(()=>[
                                        u(i(I), {
                                            style: {
                                                height: "32px"
                                            },
                                            icon: "pi pi-plus",
                                            label: "Add New Integration"
                                        })
                                    ]),
                                _: 1
                            }, 8, [
                                "to"
                            ])
                        ]),
                        m("div", Se, [
                            m("div", null, [
                                m("i", null, M(c.value.length) + " integrations available:", 1)
                            ])
                        ])
                    ]),
                    m("div", Ve, [
                        m("div", De, [
                            (f(!0), b(Z, null, ae(l(Object.values(s.value)), (w)=>(f(), b("div", {
                                    class: "integration-card",
                                    key: w?.name,
                                    onMouseleave: a[2] || (a[2] = (T)=>P.value = void 0),
                                    onMouseenter: (T)=>P.value = w.uuid
                                }, [
                                    u(i(se), {
                                        pt: {
                                            root: {
                                                style: "transition: background-color 150ms linear;" + (P.value === w.uuid ? "background-color: var(--p-surface-100); cursor: pointer;" : "")
                                            }
                                        },
                                        onClick: (T)=>{
                                            k.value = k.value === w.uuid ? void 0 : w.uuid;
                                        }
                                    }, oe({
                                        title: x(()=>[
                                                m("div", Me, [
                                                    m("span", Oe, M(w?.name), 1),
                                                    k.value === w.uuid ? (f(), b("span", Ae, [
                                                        u(i(q), {
                                                            to: `/integrations?selected=${w?.uuid}${i(h)}`,
                                                            "aria-label": "Edit {{ integration?.name }} "
                                                        }, {
                                                            default: x(()=>[
                                                                    i(de)(w) === "adhoc" ? (f(), S(i(I), {
                                                                        key: 0,
                                                                        style: {
                                                                            width: "fit-content",
                                                                            height: "32px",
                                                                            "margin-right": "0.5rem"
                                                                        },
                                                                        icon: "pi pi-pencil",
                                                                        label: "Edit"
                                                                    })) : C("", !0)
                                                                ]),
                                                            _: 2
                                                        }, 1032, [
                                                            "to"
                                                        ])
                                                    ])) : C("", !0)
                                                ])
                                            ]),
                                        _: 2
                                    }, [
                                        k.value === w.uuid ? {
                                            name: "content",
                                            fn: x(()=>[
                                                    m("div", {
                                                        class: "integration-main-content",
                                                        style: {
                                                            overflow: "hidden"
                                                        },
                                                        innerHTML: w.description
                                                    }, null, 8, Be)
                                                ]),
                                            key: "0"
                                        } : void 0
                                    ]), 1032, [
                                        "pt",
                                        "onClick"
                                    ])
                                ], 40, je))), 128))
                        ])
                    ])
                ]);
            };
        }
    });
});
export { et as _, tt as a, Je as b, Ge as c, Ke as d, Qe as e, Ye as f, de as g, Xe as h, Ze as l, He as u, __tla };
