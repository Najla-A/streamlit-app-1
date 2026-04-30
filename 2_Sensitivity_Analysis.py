import streamlit as st
import plotly.graph_objects as go
import sys
import pathlib
import numpy as np

_root = str(pathlib.Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from components.styles import get_page_config, GLOBAL_CSS
from components.navbar import render_nav
from backend.pipeline import BioCharPipeline

st.set_page_config(**get_page_config(title="BioCharAI · Sensitivity Analysis"))
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(render_nav("sensitivity"), unsafe_allow_html=True)

# ── Load pipeline ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_pipeline():
    return BioCharPipeline()

pipeline = load_pipeline()

# ── Page styles ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.sa-header{margin-bottom:28px;}
.sa-lbl{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.22em;
  text-transform:uppercase;color:#a8c0b2;margin-bottom:6px;}
.sa-title{font-size:28px;font-weight:200;letter-spacing:-.02em;color:#0f1f17;margin-bottom:6px;}
.sa-title strong{font-weight:500;}
.sa-sub{font-size:13px;font-weight:300;color:#5a7a68;line-height:1.7;max-width:620px;}
.sa-ctx{background:#fff;border:1px solid #d8e5dc;border-left:3px solid #1db760;
  border-radius:0 7px 7px 0;padding:10px 18px;display:flex;gap:24px;flex-wrap:wrap;
  font-family:'DM Mono',monospace;font-size:10px;color:#a8c0b2;margin-bottom:24px;}
.sa-ctx strong{color:#0f1f17;}
.sa-badge{display:inline-flex;align-items:center;gap:8px;padding:6px 16px;
  background:rgba(29,183,96,.06);border:1px solid rgba(29,183,96,.2);
  border-radius:20px;font-family:'DM Mono',monospace;font-size:9px;
  letter-spacing:.14em;text-transform:uppercase;color:#1db760;margin-bottom:22px;}
.sec-head{display:flex;align-items:center;gap:12px;margin:24px 0 12px;}
.sec-n{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.14em;color:#1db760;}
.sec-t{font-size:15px;font-weight:500;color:#0f1f17;}
.sec-s{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.12em;
  text-transform:uppercase;color:#a8c0b2;margin-left:auto;}
.sec-div{height:1px;background:#d8e5dc;margin-bottom:18px;}
.sweep-param-card{background:#fff;border:1px solid #d8e5dc;border-radius:10px;padding:18px 22px;margin-bottom:20px;}
.sweep-param-label{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.14em;
  text-transform:uppercase;color:#a8c0b2;margin-bottom:12px;}

/* ── Center content with max-width ── */
.block-container {
    max-width: 1080px !important;
    margin: 0 auto !important;
    padding-left: 56px !important;
    padding-right: 56px !important;
}

/* ── Selectbox styled to match Setup panel ── */
[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p {
  font-family: 'DM Mono', monospace !important;
  font-size: 8px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: #a8c0b2 !important;
  margin-bottom: 2px !important;
}
[data-testid="stSelectbox"] > div > div {
  font-family: 'DM Mono', monospace !important;
  font-size: 13px !important;
  color: #0f1f17 !important;
  background: #f5f8f5 !important;
  border: 1px solid #d8e5dc !important;
  border-radius: 6px !important;
  transition: border-color 0.15s !important;
}
[data-testid="stSelectbox"] > div > div:focus-within {
  border-color: #1db760 !important;
  background: #ffffff !important;
  box-shadow: none !important;
}

/* ── Slider styled to match ── */
[data-testid="stSlider"] [data-testid="stWidgetLabel"] p {
  font-family: 'DM Mono', monospace !important;
  font-size: 8px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: #a8c0b2 !important;
  margin-bottom: 2px !important;
}
[data-testid="stSlider"] [data-testid="stThumbValue"] {
  font-family: 'DM Mono', monospace !important;
  font-size: 11px !important;
  color: #0f1f17 !important;
}
[data-testid="stSlider"] [role="slider"] {
  background-color: #1db760 !important;
}

/* ── Number inputs styled to match Setup panel ── */
[data-testid="stNumberInput"] [data-testid="stWidgetLabel"] p {
  font-family: 'DM Mono', monospace !important;
  font-size: 8px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: #a8c0b2 !important;
  margin-bottom: 2px !important;
}
[data-testid="stNumberInput"] input {
  font-family: 'DM Mono', monospace !important;
  font-size: 13px !important;
  color: #0f1f17 !important;
  background: #f5f8f5 !important;
  border: 1px solid #d8e5dc !important;
  border-radius: 6px !important;
  padding: 7px 10px !important;
  transition: border-color 0.15s, background 0.15s !important;
}
[data-testid="stNumberInput"] input:focus {
  border-color: #1db760 !important;
  background: #ffffff !important;
  outline: none !important;
  box-shadow: none !important;
}
[data-testid="stNumberInput"] input::-webkit-inner-spin-button,
[data-testid="stNumberInput"] input::-webkit-outer-spin-button {
  -webkit-appearance: none !important;
  margin: 0 !important;
}
[data-testid="stNumberInput"] input[type=number] {
  -moz-appearance: textfield !important;
}
[data-testid="stNumberInput"] button {
  background: #eef3ee !important;
  border: 1px solid #d8e5dc !important;
  border-radius: 5px !important;
  color: #5a7a68 !important;
  font-size: 12px !important;
  transition: background 0.12s !important;
}
[data-testid="stNumberInput"] button:hover {
  background: #d8e5dc !important;
  border-color: #1db760 !important;
  color: #1db760 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sa-header">
  <div class="sa-lbl">Cached Aspen · ML-Only Sweep</div>
  <div class="sa-title">Sensitivity <strong>Analysis</strong></div>
  <div class="sa-sub">
    Sweeps a pyrolysis parameter using cached Aspen yields from your last Setup run —
    no additional Aspen simulations are triggered. Each point is a live ML prediction.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Gate: require a prior simulation (so we have a cached Aspen result) ──────
if "sim_result" not in st.session_state or "sim_inputs" not in st.session_state:
    st.warning(
        "No simulation has been run yet. Sensitivity analysis reuses the Aspen output "
        "from your last Setup run (no additional Aspen runs are triggered here). "
        "Please run a simulation on the **Setup** page first."
    )
    st.page_link("pages/1_Setup.py", label="→ Go to Setup", icon="⚗️")
    st.stop()

base          = dict(st.session_state["sim_inputs"])
cached_aspen  = dict(st.session_state["sim_result"]["aspen"])

# ── Context strip ─────────────────────────────────────────────────────────────
T   = base.get("temperature", 500)
RT  = base.get("residence_time_min", 60)
HR  = base.get("heating_rate_c_per_min", 10)
N2  = base.get("n2_flow_rate_ml_per_min", 150)

st.markdown(f"""
<div class="sa-ctx">
  <span>🌡 Baseline Temp: <strong>{T:.0f} °C</strong></span>
  <span>⏱ Residence: <strong>{RT:.0f} min</strong></span>
  <span>⚡ Heating Rate: <strong>{HR:.0f} °C/min</strong></span>
  <span>💨 N₂ Flow: <strong>{N2:.0f} mL/min</strong></span>
  <span>📊 Carbon: <strong>{base.get("c", 45.2):.1f} wt%</strong></span>
</div>
""", unsafe_allow_html=True)

# ── Sweep parameter selector ──────────────────────────────────────────────────
SWEEP_PARAMS = {
    "Temperature (°C)":      ("temperature",           100,  900, 50,  "°C"),
    "Residence Time (min)":  ("residence_time_min",      5,  120,  5, "min"),
    "Heating Rate (°C/min)": ("heating_rate_c_per_min",  1,   50,  2, "°C/min"),
    "N₂ Flow Rate (mL/min)": ("n2_flow_rate_ml_per_min",10,  500, 25, "mL/min"),
}

col_param, col_pts = st.columns([2, 1])
with col_param:
    sweep_label = st.selectbox("Sweep parameter", list(SWEEP_PARAMS.keys()), index=0)
with col_pts:
    n_steps = st.slider("Number of points", min_value=8, max_value=40, value=25)

param_key, p_min, p_max, p_step, p_unit = SWEEP_PARAMS[sweep_label]
sweep_values = np.linspace(p_min, p_max, n_steps).tolist()

st.markdown(f"""
<div class="sa-badge">
  ✦ &nbsp;{sweep_label}: {p_min} – {p_max} {p_unit} &nbsp;|&nbsp; {n_steps} prediction points
</div>
""", unsafe_allow_html=True)

# ── Run sweep (ML-only, cached Aspen — no re-runs) ───────────────────────────
@st.cache_data(show_spinner=False)
def run_sweep(_pipeline, base_inputs_frozen, cached_aspen_frozen, param_key, sweep_values_tuple):
    sweep_values = list(sweep_values_tuple)
    cached_aspen_dict = dict(cached_aspen_frozen)
    results = []
    for val in sweep_values:
        inp = dict(base_inputs_frozen)
        inp[param_key] = val
        try:
            r = _pipeline.run(inp, aspen_outputs=cached_aspen_dict)
            results.append(r)
        except Exception:
            results.append(None)
    return results

with st.spinner(f"Running {n_steps} ML predictions across {sweep_label}…"):
    sweep_results = run_sweep(
        pipeline,
        tuple(sorted(base.items())),
        tuple(sorted(cached_aspen.items())),
        param_key,
        tuple(sweep_values),
    )

# ── Extract series ────────────────────────────────────────────────────────────
def series(key, source="stage2"):
    vals = []
    for r in sweep_results:
        if r is None:
            vals.append(None)
            continue
        v = r[source].get(key, -1)
        vals.append(v if v >= 0 else None)
    return vals

def series_stage1(key):
    return [
        (r["stage1"].get(key) if r else None)
        for r in sweep_results
    ]

def series_aspen(key):
    return [
        (r["aspen"].get(key) if r else None)
        for r in sweep_results
    ]

x = sweep_values

# ── Shared Plotly helpers ─────────────────────────────────────────────────────
PALETTE = ["#1db760","#3ec9a7","#e8a23a","#e05252","#a8c0b2",
           "#3b82f6","#c084fc","#f97316","#06b6d4","#84cc16"]

def _layout(y_title, height=340):
    return dict(
        template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono, monospace", color="#5a7a68", size=11),
        xaxis=dict(
            title=f"{sweep_label}",
            gridcolor="rgba(216,229,220,0.6)", zeroline=False,
            title_font=dict(size=10, color="#a8c0b2"), tickfont=dict(size=9),
        ),
        yaxis=dict(
            title=y_title,
            gridcolor="rgba(216,229,220,0.6)", zeroline=False,
            title_font=dict(size=10, color="#a8c0b2"), tickfont=dict(size=9),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="rgba(216,229,220,0.5)",
            borderwidth=1, font=dict(size=10, color="#5a7a68"),
        ),
        hovermode="x unified",
        margin=dict(l=60, r=20, t=20, b=50),
        height=height,
    )

def _line(x, y, color, name, fill=False, dash=None):
    fc = color.replace("rgb(","rgba(").rstrip(")") + ",0.07)" if fill and color.startswith("rgb") else None
    if fill and color.startswith("#"):
        r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
        fc = f"rgba({r},{g},{b},0.07)"
    return go.Scatter(
        x=x, y=y, mode="lines+markers", name=name,
        line=dict(color=color, width=2, dash=dash),
        marker=dict(size=5, color=color, symbol="circle"),
        fill="tozeroy" if fill else None,
        fillcolor=fc,
        connectgaps=False,
    )

def sec(num, title, sub):
    st.markdown(f"""
<div class="sec-head">
  <span class="sec-n">{num}</span>
  <span class="sec-t">{title}</span>
  <span class="sec-s">{sub}</span>
</div>
<div class="sec-div"></div>""", unsafe_allow_html=True)

# ── Helper: scatter with colorbar coding the sweep parameter ─────────────────
def _scatter_grad(xs, ys, name, x_title, y_title, height=360):
    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers+lines",
        marker=dict(
            size=8, color=sweep_values, colorscale="Viridis",
            showscale=True,
            colorbar=dict(
                title=dict(text=sweep_label, font=dict(size=9, color="#a8c0b2")),
                tickfont=dict(size=9, color="#5a7a68"),
                thickness=10, len=0.85,
            ),
            line=dict(width=0),
        ),
        line=dict(color="rgba(168,192,178,0.35)", width=1),
        name=name, connectgaps=False,
    ))
    fig.update_layout(
        template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono, monospace", color="#5a7a68", size=11),
        xaxis=dict(title=x_title, gridcolor="rgba(216,229,220,0.6)", zeroline=False,
                   title_font=dict(size=10, color="#a8c0b2"), tickfont=dict(size=9)),
        yaxis=dict(title=y_title, gridcolor="rgba(216,229,220,0.6)", zeroline=False,
                   title_font=dict(size=10, color="#a8c0b2"), tickfont=dict(size=9)),
        margin=dict(l=60, r=20, t=20, b=50), height=height,
    )
    return fig


# ── 01 Biochar Quality & Classification ──────────────────────────────────────
sec("01", "Biochar Quality & Classification", "Van Krevelen · HHV vs Fixed Carbon")

C_series = series_stage1("c_1")
H_series = series_stage1("h_1")
O_series = series_stage1("o_1")
HHV_series = series_stage1("energy_content_mj_per_kg")
FC_series = series_stage1("fixed_carbon_output")
VM_series = series_stage1("volatile_matter_output")
ASH_series = series_stage1("ash_content")
MST_series = series_stage1("moisture_content")

def _safe_div(a, b):
    try:
        return a / b if (a is not None and b is not None and b != 0) else None
    except Exception:
        return None

# Atomic ratios for Van Krevelen (H/C and O/C)
H_over_C = [_safe_div(h/1.008, c/12.011) if (h is not None and c not in (None, 0)) else None
            for h, c in zip(H_series, C_series)]
O_over_C = [_safe_div(o/15.999, c/12.011) if (o is not None and c not in (None, 0)) else None
            for o, c in zip(O_series, C_series)]

col_vk, col_hfc = st.columns(2)
with col_vk:
    with st.container(border=True):
        st.markdown('<div class="sweep-param-label">Van Krevelen Diagram — H/C vs O/C (atomic)</div>', unsafe_allow_html=True)
        fig_vk = _scatter_grad(O_over_C, H_over_C, "biochar", "O/C (atomic)", "H/C (atomic)", height=340)
        st.plotly_chart(fig_vk, use_container_width=True, config={"displayModeBar": False})

with col_hfc:
    with st.container(border=True):
        st.markdown('<div class="sweep-param-label">HHV vs Fixed Carbon</div>', unsafe_allow_html=True)
        fig_hfc = _scatter_grad(FC_series, HHV_series, "biochar", "Fixed Carbon (wt%)", "HHV (MJ/kg)", height=340)
        st.plotly_chart(fig_hfc, use_container_width=True, config={"displayModeBar": False})


# ── 02 Composition Evolution ─────────────────────────────────────────────────
sec("02", "Composition Evolution", "Ultimate + Proximate vs sweep parameter")

col_ult, col_prox = st.columns(2)
with col_ult:
    with st.container(border=True):
        st.markdown('<div class="sweep-param-label">Ultimate analysis — C/H/N/O (wt%)</div>', unsafe_allow_html=True)
        f_ult = go.Figure()
        for key, color, label in [
            ("c_1","#1db760","C"), ("h_1","#3ec9a7","H"),
            ("n_1","#e8a23a","N"), ("o_1","#e05252","O"),
        ]:
            f_ult.add_trace(_line(x, series_stage1(key), color, label))
            f_ult.data[-1].update(hovertemplate=f"{label}: %{{y:.2f}} wt%<extra></extra>")
        f_ult.update_layout(**_layout("wt%", height=340))
        st.plotly_chart(f_ult, use_container_width=True, config={"displayModeBar": False})

with col_prox:
    with st.container(border=True):
        st.markdown('<div class="sweep-param-label">Proximate analysis — stacked %</div>', unsafe_allow_html=True)
        f_prox = go.Figure()
        prox_layers = [
            (MST_series, "#a8c0b2", "Moisture"),
            (VM_series,  "#3ec9a7", "Volatile Matter"),
            (FC_series,  "#1db760", "Fixed Carbon"),
            (ASH_series, "#e8a23a", "Ash"),
        ]
        for y, color, label in prox_layers:
            f_prox.add_trace(go.Scatter(
                x=x, y=y, mode="lines", name=label, stackgroup="one",
                line=dict(width=0.5, color=color),
                fillcolor=color.replace("#","rgba(").replace("#","") if False else color,
                hovertemplate=f"{label}: %{{y:.1f}}%<extra></extra>",
            ))
        f_prox.update_layout(**_layout("wt%", height=340))
        st.plotly_chart(f_prox, use_container_width=True, config={"displayModeBar": False})


# ── 03 Carbonization & Energy ────────────────────────────────────────────────
sec("03", "Carbonization & Energy", "HHV · FC/VM ratio")

FCVM_series = [_safe_div(fc, vm) for fc, vm in zip(FC_series, VM_series)]

col_hhv, col_cr = st.columns(2)
with col_hhv:
    with st.container(border=True):
        st.markdown('<div class="sweep-param-label">HHV vs sweep parameter</div>', unsafe_allow_html=True)
        f_hhv = go.Figure(_line(x, HHV_series, "#1db760", "HHV", fill=True))
        f_hhv.update_traces(hovertemplate=f"{sweep_label}: %{{x}}<br>HHV: %{{y:.2f}} MJ/kg<extra></extra>")
        f_hhv.update_layout(**_layout("HHV (MJ/kg)", height=340))
        st.plotly_chart(f_hhv, use_container_width=True, config={"displayModeBar": False})

with col_cr:
    with st.container(border=True):
        st.markdown('<div class="sweep-param-label">Carbonization index — Fixed Carbon / Volatile Matter</div>', unsafe_allow_html=True)
        f_cr = go.Figure(_line(x, FCVM_series, "#3ec9a7", "FC / VM", fill=True))
        f_cr.update_traces(hovertemplate=f"{sweep_label}: %{{x}}<br>FC/VM: %{{y:.2f}}<extra></extra>")
        f_cr.update_layout(**_layout("FC / VM (ratio)", height=340))
        st.plotly_chart(f_cr, use_container_width=True, config={"displayModeBar": False})


# ── 04 Adsorption Performance by Class ───────────────────────────────────────
sec("04", "Adsorption Performance by Class", "Capacity (mg/g) + Removal (%) per contaminant class")

CLASS_GROUPS = [
    ("Heavy Metals", [
        ("pb_2",           "Pb²⁺"),
        ("cu_2",           "Cu²⁺"),
        ("cr_6",           "Cr⁶⁺"),
        ("cd_2",           "Cd²⁺"),
        ("zn_2",           "Zn²⁺"),
    ]),
    ("Dyes", [
        ("methylene_blue",  "Methylene Blue"),
        ("rhodamine_b",     "Rhodamine B"),
        ("malachite_green", "Malachite Green"),
        ("congo_red",       "Congo Red"),
    ]),
    ("Nutrients", [
        ("ammonium",  "Ammonium"),
        ("phosphate", "Phosphate"),
    ]),
    ("Organic Pollutants", [
        ("phenol",       "Phenol"),
        ("tetracycline", "Tetracycline"),
    ]),
]

def _cls_block(title, members):
    with st.container(border=True):
        st.markdown(f'<div class="sweep-param-label">{title}</div>', unsafe_allow_html=True)
        c_cap, c_rem = st.columns(2)
        # Capacity (mg/g)
        with c_cap:
            f_cap = go.Figure()
            for i, (stub, label) in enumerate(members):
                y = series(f"adsorption_capacity_for_{stub}_mg_per_g")
                if any(v is not None for v in y):
                    f_cap.add_trace(_line(x, y, PALETTE[i % len(PALETTE)], label))
                    f_cap.data[-1].update(hovertemplate=f"{label}: %{{y:.1f}} mg/g<extra></extra>")
            f_cap.update_layout(**_layout("Capacity (mg/g)", height=280))
            st.plotly_chart(f_cap, use_container_width=True, config={"displayModeBar": False})
        # Removal (%)
        with c_rem:
            f_rem = go.Figure()
            for i, (stub, label) in enumerate(members):
                y = series(f"removal_efficiency_for_{stub}_mg_per_g")
                if any(v is not None for v in y):
                    f_rem.add_trace(_line(x, y, PALETTE[i % len(PALETTE)], label))
                    f_rem.data[-1].update(hovertemplate=f"{label}: %{{y:.1f}}%<extra></extra>")
            f_rem.update_layout(**_layout("Removal (%)", height=280))
            st.plotly_chart(f_rem, use_container_width=True, config={"displayModeBar": False})

for cls_title, members in CLASS_GROUPS:
    _cls_block(cls_title, members)


# ── 05 Multi-contaminant Fingerprint (radar) ─────────────────────────────────
sec("05", "Multi-contaminant Fingerprint", f"Removal profile at low · mid · high {sweep_label}")

ALL_CONTAMINANTS = [m for _, group in CLASS_GROUPS for m in group]
radar_labels = [label for _, label in ALL_CONTAMINANTS]
idx_low  = 0
idx_mid  = len(sweep_values) // 2
idx_high = len(sweep_values) - 1
radar_pts = [
    (idx_low,  f"Low ({sweep_values[idx_low]:.1f})",  "#a8c0b2"),
    (idx_mid,  f"Mid ({sweep_values[idx_mid]:.1f})",  "#3ec9a7"),
    (idx_high, f"High ({sweep_values[idx_high]:.1f})", "#1db760"),
]

def _val_at(idx, stub):
    r = sweep_results[idx]
    if r is None:
        return 0
    v = r["stage2"].get(f"removal_efficiency_for_{stub}_mg_per_g", -1)
    return max(0, v) if v >= 0 else 0

def _hex_to_rgba(hex_color, alpha=0.13):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
 
f_rad = go.Figure()
for idx, lbl, color in radar_pts:
    vals = [_val_at(idx, stub) for stub, _ in ALL_CONTAMINANTS]
    vals.append(vals[0])  # close the polygon
    theta = radar_labels + [radar_labels[0]]
    f_rad.add_trace(go.Scatterpolar(
        r=vals, theta=theta, mode="lines+markers", name=lbl,
        line=dict(color=color, width=2),
        marker=dict(size=5, color=color),
        fill="toself", fillcolor=_hex_to_rgba(color, 0.13),
    ))
f_rad.update_layout(
    template="simple_white",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono, monospace", color="#5a7a68", size=10),
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0,100], gridcolor="rgba(216,229,220,0.6)",
                        tickfont=dict(size=8, color="#a8c0b2")),
        angularaxis=dict(gridcolor="rgba(216,229,220,0.6)", tickfont=dict(size=9, color="#5a7a68")),
    ),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="#5a7a68")),
    margin=dict(l=40, r=40, t=20, b=20),
    height=520,
)
with st.container(border=True):
    st.plotly_chart(f_rad, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
