import streamlit as st
import streamlit.components.v1 as components
import json
import sys
import pathlib

_root = str(pathlib.Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from components.styles import get_page_config, GLOBAL_CSS
from components.navbar import render_nav
from backend.pipeline import BioCharPipeline
from backend.logger import log_prediction
from backend.validation import validate_system_output
 

st.set_page_config(**get_page_config(title="BioCharAI · Setup"))
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(render_nav("simulation"), unsafe_allow_html=True)

# Load Pipeline
@st.cache_resource
def load_pipeline():
    return BioCharPipeline()

pipeline = load_pipeline()

# Helpers
def _u(key, fb):
    defaults = {"Carbon": 45.2, "Hydrogen": 6.8, "Nitrogen": 8.5, "Sulfur": 0.9, "Oxygen": 38.6}
    return defaults.get(key, fb)

def _p(key, fb):
    defaults = {"Moisture": 8.2, "Volatile Matter": 72.5, "Fixed Carbon": 14.8, "Ash": 4.5}
    return defaults.get(key, fb)

def _c(key, fb):
    defaults = {"temperature": 500, "residence_time": 60, "n2_flow_rate": 150, "heating_rate": 10}
    return defaults.get(key, fb)

def _r(key, max_val):
    ranges = {"temperature": [100, 900], "residence_time": [5, 120], "n2_flow_rate": [10, 500], "heating_rate": [1, 50]}
    return ranges.get(key, [0, 100])[max_val]


SETUP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@200;300;400;500&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{--ink:#0f1f17;--ink-mid:#2b4035;--ink-soft:#5a7a68;--ink-ghost:#a8c0b2;--bg:#f5f8f5;--white:#ffffff;--dust:#d8e5dc;--panel:#eef3ee;--algae:#1db760;--algae-d:#159149;--red:#e05252;--amber:#e8a23a;--font:'DM Sans',sans-serif;--mono:'DM Mono',monospace;}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;overflow:hidden;background:var(--bg);font-family:var(--font);color:var(--ink);-webkit-font-smoothing:antialiased;}
.workspace{display:flex;height:100%;}
/* LEFT PANEL */
.panel{width:320px;flex-shrink:0;display:flex;flex-direction:column;background:var(--bg);border-right:1px solid var(--dust);}
.panel-scroll{flex:1;overflow-y:auto;padding:12px 12px 0;display:flex;flex-direction:column;gap:8px;}
.panel-scroll::-webkit-scrollbar{width:3px;}
.panel-scroll::-webkit-scrollbar-thumb{background:var(--dust);border-radius:2px;}
/* ACCORDION */
.card{background:var(--white);border:1px solid var(--dust);border-radius:10px;overflow:hidden;}
.card-trigger{width:100%;display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:none;border:none;cursor:pointer;text-align:left;transition:background 0.1s;}
.card-trigger:hover{background:var(--panel);}
.card-left{display:flex;align-items:center;gap:10px;}
.card-idx{font-family:var(--mono);font-size:9px;letter-spacing:0.14em;color:var(--algae);width:16px;}
.card-name{font-size:13px;font-weight:500;color:var(--ink);line-height:1.2;}
.card-sub{font-family:var(--mono);font-size:8px;letter-spacing:0.1em;text-transform:uppercase;color:var(--ink-ghost);margin-top:2px;}
.card-right{display:flex;align-items:center;gap:8px;}
.card-badge{font-family:var(--mono);font-size:9px;color:var(--ink-ghost);}
.card-badge.ok{color:var(--algae);}.card-badge.err{color:var(--red);}
.chevron{transition:transform 0.22s ease;color:var(--ink-ghost);}
.card.open .chevron{transform:rotate(180deg);}
.card-body{overflow:hidden;max-height:0;transition:max-height 0.28s ease;}
.card.open .card-body{max-height:420px;border-top:1px solid var(--dust);}
.card-inner{padding:12px 14px 14px;}
/* FIELDS */
.field-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;}
.f-item{display:flex;flex-direction:column;gap:4px;}
.f-lbl{font-family:var(--mono);font-size:8px;letter-spacing:0.14em;text-transform:uppercase;color:var(--ink-ghost);}
.f-row{display:flex;align-items:stretch;}
.f-inp{flex:1;min-width:0;font-family:var(--mono);font-size:13px;color:var(--ink);background:var(--bg);border:1px solid var(--dust);border-right:none;border-radius:5px 0 0 5px;padding:7px 8px;outline:none;transition:border-color 0.15s,background 0.15s;-webkit-appearance:textfield;appearance:textfield;}
.f-inp:focus{border-color:var(--algae);background:var(--white);}
.f-inp.err{border-color:var(--red);}
input[type=number]::-webkit-inner-spin-button,input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none;margin:0;}
.f-unit{font-family:var(--mono);font-size:9px;color:var(--ink-ghost);background:var(--panel);border:1px solid var(--dust);border-left:none;border-radius:0 5px 5px 0;padding:7px 6px;display:flex;align-items:center;}
/* SUM BAR */
.total-footer{border-top:1px solid var(--dust);padding-top:8px;margin-top:2px;}
.sum-bar{height:3px;background:rgba(216,229,220,0.5);border-radius:2px;overflow:hidden;margin-bottom:6px;}
.sum-fill{height:100%;background:var(--algae);border-radius:2px;transition:width 0.25s,background 0.25s;width:0%;}
.sum-fill.close{background:var(--amber);}.sum-fill.err{background:var(--red);}
.total-row{display:flex;justify-content:space-between;align-items:baseline;}
.t-lbl{font-family:var(--mono);font-size:8px;letter-spacing:0.14em;text-transform:uppercase;color:var(--ink-ghost);}
.t-val{font-family:var(--mono);font-size:11px;color:var(--ink);}
.t-val.ok{color:var(--algae);}.t-val.err{color:var(--red);}
.t-rem{font-family:var(--mono);font-size:8px;color:var(--ink-ghost);margin-top:1px;}
.t-rem.err{color:var(--red);}
/* SLIDERS */
.slider-list{display:flex;flex-direction:column;}
.s-item{padding:9px 0;border-bottom:1px solid rgba(216,229,220,0.5);}
.s-item:last-child{border-bottom:none;}
.s-top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;}
.s-lbl{font-size:12px;font-weight:400;color:var(--ink-mid);}
.s-val{font-family:var(--mono);font-size:13px;color:var(--ink);}
.s-unit{font-size:9px;color:var(--ink-ghost);margin-left:2px;}
input[type=range]{-webkit-appearance:none;width:100%;height:2px;background:var(--dust);border-radius:1px;outline:none;cursor:pointer;}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--algae);border:2px solid #fff;box-shadow:0 0 0 1px var(--algae);cursor:pointer;transition:transform 0.1s;}
input[type=range]::-webkit-slider-thumb:active{transform:scale(1.18);}
.s-bounds{display:flex;justify-content:space-between;margin-top:4px;}
.s-bounds span{font-family:var(--mono);font-size:8px;color:var(--ink-ghost);}
/* RUN BUTTON */
.run-wrap{flex-shrink:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px 12px;gap:10px;}
.run-btn{background:none;border:none;cursor:pointer;outline:none;display:flex;flex-direction:column;align-items:center;gap:12px;padding:0;}
.run-btn:disabled{cursor:not-allowed;opacity:0.35;}
.cell-outer-ring{width:110px;height:110px;border-radius:50%;border:1px solid rgba(29,183,96,0.4);display:flex;align-items:center;justify-content:center;transition:border-color 0.3s;}
.run-btn:not(:disabled):hover .cell-outer-ring{border-color:rgba(29,183,96,0.8);}
.cell-body-btn{width:84px;height:84px;border-radius:50%;background:var(--algae);border:1.5px solid var(--algae);display:flex;align-items:center;justify-content:center;position:relative;transition:background 0.3s,transform 0.15s;overflow:hidden;}
.run-btn:not(:disabled):hover .cell-body-btn{background:var(--algae-d);transform:scale(1.03);}
.run-btn:not(:disabled):active .cell-body-btn{transform:scale(0.96);background:#107a3a;}
.run-btn:disabled .cell-body-btn{background:#131f18;border-color:rgba(29,183,96,0.12);}
.org-wrap{position:absolute;inset:0;}
.org{position:absolute;border-radius:50%;background:rgba(255,255,255,0.25);border:1px solid rgba(255,255,255,0.4);}
.run-btn:not(:disabled):hover .org{background:rgba(255,255,255,0.35);}
.run-btn:disabled .org{background:rgba(29,183,96,0.1);border-color:rgba(29,183,96,0.2);}
.org-c1{width:22px;height:11px;border-radius:6px;top:20px;left:14px;transform:rotate(-15deg);}
.org-c2{width:16px;height:9px;border-radius:5px;bottom:22px;right:16px;transform:rotate(15deg);}
.org-c3{width:13px;height:7px;border-radius:4px;top:46px;right:12px;}
.org-nucleus{width:20px;height:20px;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.4);}
@keyframes cellPulse{0%,100%{transform:scale(1);}50%{transform:scale(1.05);}}
.cell-body-btn.running{animation:cellPulse 1.2s ease-in-out infinite;}
@keyframes pulseOut{0%{transform:scale(1);opacity:0.6}100%{transform:scale(1.5);opacity:0}}
.cell-pulse-ring{position:absolute;inset:-12px;border-radius:50%;border:1px solid rgba(255,255,255,0.5);opacity:0;pointer-events:none;}
.cell-body-btn.running .cell-pulse-ring{animation:pulseOut 1.4s ease-out infinite;}
.run-lbl{font-family:var(--mono);font-size:10px;letter-spacing:0.32em;text-transform:uppercase;color:var(--ink-mid);transition:color 0.3s;}
.run-btn:not(:disabled):hover .run-lbl{color:var(--algae);}
.run-btn:disabled .run-lbl{color:var(--ink-ghost);}
.run-btn.running .run-lbl{color:var(--algae);}
.phase-ticker{font-family:var(--mono);font-size:9px;color:var(--algae);letter-spacing:0.1em;min-height:14px;text-align:center;}
/* PFD */
.pfd-panel{flex:1;display:flex;flex-direction:column;background:var(--bg);overflow:hidden;}
.pfd-head{padding:11px 20px;border-bottom:1px solid var(--dust);flex-shrink:0;display:flex;align-items:center;justify-content:space-between;}
.pfd-title{font-family:var(--mono);font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:var(--ink-ghost);}
.pfd-canvas{flex:1;display:flex;align-items:center;justify-content:center;padding:16px 20px;overflow:hidden;}
.pfd-node{transition:stroke 0.3s,fill 0.3s;}
.pfd-node.lit{stroke:var(--algae)!important;fill:rgba(29,183,96,0.06)!important;}
@keyframes flow{0%{stroke-dashoffset:24;}100%{stroke-dashoffset:0;}}
.s-line{transition:stroke 0.3s;}
.s-line.flowing{stroke-dasharray:7 3;animation:flow 0.5s linear infinite;}
@keyframes pyropulse{0%,100%{opacity:0.07}50%{opacity:0.2}}
.pyro-glow{animation:pyropulse 2.4s ease-in-out infinite;}
@keyframes biopulse{0%,100%{opacity:0.7}50%{opacity:1}}
.bio-done{animation:biopulse 1.2s ease-in-out infinite;}
.pfd-foot{padding:8px 20px;border-top:1px solid var(--dust);display:flex;gap:20px;flex-shrink:0;}
.pf-stat{display:flex;flex-direction:column;gap:1px;}
.pf-lbl{font-family:var(--mono);font-size:8px;letter-spacing:0.14em;text-transform:uppercase;color:var(--ink-ghost);}
.pf-val{font-family:var(--mono);font-size:11px;color:var(--ink);}
.guidelines{border-top:1px solid var(--dust);padding:12px 20px 16px;flex-shrink:0;}
.guide-title{font-family:var(--mono);font-size:9px;letter-spacing:0.22em;text-transform:uppercase;color:var(--ink-ghost);margin-bottom:10px;}
.guide-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px 20px;}
.guide-item{display:flex;gap:8px;align-items:flex-start;}
.guide-dot{width:4px;height:4px;border-radius:50%;background:var(--algae);flex-shrink:0;margin-top:5px;}
.guide-text{font-size:11px;font-weight:300;color:var(--ink-soft);line-height:1.5;}
.guide-text strong{font-weight:500;color:var(--ink-mid);}
</style>
</head>
<body>
<div class="workspace">
<div class="panel">
  <div class="panel-scroll">

    <!-- 01 Ultimate Analysis -->
    <div class="card open" id="c1">
      <button class="card-trigger" onclick="tog('c1')">
        <div class="card-left">
          <span class="card-idx">01</span>
          <div><div class="card-name">Ultimate Analysis</div><div class="card-sub">Elemental Composition</div></div>
        </div>
        <div class="card-right">
          <span class="card-badge" id="ub">—</span>
          <svg class="chevron" width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="#a8c0b2" stroke-width="1.5" stroke-linecap="round"/></svg>
        </div>
      </button>
      <div class="card-body"><div class="card-inner">
        <div class="field-grid">
          <div class="f-item"><span class="f-lbl">Carbon</span>
            <div class="f-row"><input class="f-inp" type="number" id="uc" value="UC_VAL" min="0" max="100" step="0.1" oninput="calcU()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Hydrogen</span>
            <div class="f-row"><input class="f-inp" type="number" id="uh" value="UH_VAL" min="0" max="100" step="0.1" oninput="calcU()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Nitrogen</span>
            <div class="f-row"><input class="f-inp" type="number" id="un" value="UN_VAL" min="0" max="100" step="0.1" oninput="calcU()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Sulfur</span>
            <div class="f-row"><input class="f-inp" type="number" id="us" value="US_VAL" min="0" max="100" step="0.1" oninput="calcU()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Oxygen</span>
            <div class="f-row"><input class="f-inp" type="number" id="uo" value="UO_VAL" min="0" max="100" step="0.1" oninput="calcU()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Ash</span>
            <div class="f-row"><input class="f-inp" type="number" id="ua" value="UA_VAL" min="0" max="100" step="0.1" oninput="calcU()"><span class="f-unit">%</span></div></div>
        </div>
        <div class="total-footer">
          <div class="sum-bar"><div class="sum-fill" id="uf"></div></div>
          <div class="total-row">
            <span class="t-lbl">Total</span>
            <div class="t-nums"><div class="t-val" id="ut">—</div><div class="t-rem" id="ur"></div></div>
          </div>
        </div>
      </div></div>
    </div>

    <!-- 02 Proximate Analysis -->
    <div class="card" id="c2">
      <button class="card-trigger" onclick="tog('c2')">
        <div class="card-left">
          <span class="card-idx">02</span>
          <div><div class="card-name">Proximate Analysis</div><div class="card-sub">Material Fractions</div></div>
        </div>
        <div class="card-right">
          <span class="card-badge" id="pb">—</span>
          <svg class="chevron" width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="#a8c0b2" stroke-width="1.5" stroke-linecap="round"/></svg>
        </div>
      </button>
      <div class="card-body"><div class="card-inner">
        <div class="field-grid">
          <div class="f-item"><span class="f-lbl">Moisture</span>
            <div class="f-row"><input class="f-inp" type="number" id="pm" value="PM_VAL" min="0" max="100" step="0.1" oninput="calcP()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Volatile Matter</span>
            <div class="f-row"><input class="f-inp" type="number" id="pv" value="PV_VAL" min="0" max="100" step="0.1" oninput="calcP()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Fixed Carbon</span>
            <div class="f-row"><input class="f-inp" type="number" id="pf" value="PF_VAL" min="0" max="100" step="0.1" oninput="calcP()"><span class="f-unit">%</span></div></div>
          <div class="f-item"><span class="f-lbl">Ash</span>
            <div class="f-row"><input class="f-inp" type="number" id="pa" value="PA_VAL" min="0" max="100" step="0.1" oninput="calcP()"><span class="f-unit">%</span></div></div>
        </div>
        <div class="total-footer">
          <div class="sum-bar"><div class="sum-fill" id="pf2"></div></div>
          <div class="total-row">
            <span class="t-lbl">Total</span>
            <div class="t-nums"><div class="t-val" id="pt">—</div><div class="t-rem" id="pr"></div></div>
          </div>
        </div>
      </div></div>
    </div>

    <!-- 03 Pyrolysis Conditions -->
    <div class="card" id="c3">
      <button class="card-trigger" onclick="tog('c3')">
        <div class="card-left">
          <span class="card-idx">03</span>
          <div><div class="card-name">Pyrolysis Conditions</div><div class="card-sub">Thermochemical Parameters</div></div>
        </div>
        <div class="card-right">
          <svg class="chevron" width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="#a8c0b2" stroke-width="1.5" stroke-linecap="round"/></svg>
        </div>
      </button>
      <div class="card-body"><div class="card-inner">
        <div class="slider-list">
          <div class="s-item">
            <div class="s-top"><span class="s-lbl">Temperature</span>
              <span class="s-val" id="vt">CT_VAL <span class="s-unit">°C</span></span></div>
            <input type="range" id="sT" min="T_MIN" max="T_MAX" value="CT_VAL" step="10"
              oninput="sv('vt',this.value,'°C');flashNode('node-pyr');sstat('st',this.value,'°C')">
            <div class="s-bounds"><span>T_MIN°C</span><span>T_MAX°C</span></div>
          </div>
          <div class="s-item">
            <div class="s-top"><span class="s-lbl">Residence Time</span>
              <span class="s-val" id="vr">CR_VAL <span class="s-unit">min</span></span></div>
            <input type="range" id="sRT" min="R_MIN" max="R_MAX" value="CR_VAL" step="1"
              oninput="sv('vr',this.value,'min');sstat('sr',this.value,'min')">
            <div class="s-bounds"><span>R_MIN min</span><span>R_MAX min</span></div>
          </div>
          <div class="s-item">
            <div class="s-top"><span class="s-lbl">Inert Flow Rate</span>
              <span class="s-val" id="vi">CN_VAL <span class="s-unit">mL/min</span></span></div>
            <input type="range" id="sN2" min="N_MIN" max="N_MAX" value="CN_VAL" step="10"
              oninput="sv('vi',this.value,'mL/min');sstat('si',this.value,'mL/min')">
            <div class="s-bounds"><span>N_MIN</span><span>N_MAX mL/min</span></div>
          </div>
          <div class="s-item">
            <div class="s-top"><span class="s-lbl">Heating Rate</span>
              <span class="s-val" id="vh">CH_VAL <span class="s-unit">°C/min</span></span></div>
            <input type="range" id="sHR" min="H_MIN" max="H_MAX" value="CH_VAL" step="1"
              oninput="sv('vh',this.value,'°C/min');sstat('sh',this.value,'°C/min')">
            <div class="s-bounds"><span>H_MIN</span><span>H_MAX °C/min</span></div>
          </div>
        </div>
      </div></div>
    </div>

  </div><!-- /panel-scroll -->

  <!-- RUN BUTTON -->
  <div class="run-wrap">
    <button class="run-btn" id="runBtn" disabled onclick="runSim()">
      <div class="cell-outer-ring">
        <div class="cell-body-btn" id="cellBody">
          <div class="cell-pulse-ring"></div>
          <div class="org-wrap">
            <div class="org org-c1"></div>
            <div class="org org-c2"></div>
            <div class="org org-c3"></div>
            <div class="org org-nucleus"></div>
          </div>
        </div>
      </div>
      <span class="run-lbl" id="runLbl">Simulate</span>
    </button>
    <div class="phase-ticker" id="phaseTicker"></div>
  </div>
</div><!-- /panel -->

<!-- PFD RIGHT -->
<div class="pfd-panel">
  <div class="pfd-head">
    <span class="pfd-title">Process Flow Diagram · Aspen Plus Equilibrium Model</span>
  </div>
  <div class="pfd-canvas">
    <svg id="pfd" viewBox="0 0 980 420" width="100%" height="100%" style="max-height:100%;max-width:100%;">
      <defs>
        <marker id="mp" markerWidth="7" markerHeight="7" refX="6" refY="2.5" orient="auto"><path d="M0,0 L0,5 L6,2.5z" fill="#c084fc"/></marker>
        <marker id="mg" markerWidth="7" markerHeight="7" refX="6" refY="2.5" orient="auto"><path d="M0,0 L0,5 L6,2.5z" fill="#1db760"/></marker>
        <marker id="mb" markerWidth="7" markerHeight="7" refX="6" refY="2.5" orient="auto"><path d="M0,0 L0,5 L6,2.5z" fill="#3b82f6"/></marker>
        <marker id="mc" markerWidth="7" markerHeight="7" refX="6" refY="2.5" orient="auto"><path d="M0,0 L0,5 L6,2.5z" fill="#06b6d4"/></marker>
        <marker id="mr" markerWidth="7" markerHeight="7" refX="6" refY="2.5" orient="auto"><path d="M0,0 L0,5 L6,2.5z" fill="#ef4444"/></marker>
        <marker id="mk" markerWidth="7" markerHeight="7" refX="6" refY="2.5" orient="auto"><path d="M0,0 L0,5 L6,2.5z" fill="#0f1f17"/></marker>
      </defs>
      <rect x="30" y="102" width="52" height="98" rx="4" fill="rgba(29,183,96,0.04)" stroke="rgba(29,183,96,0.18)" stroke-width="1" stroke-dasharray="3,2"/>
      <text x="56" y="98" font-family="DM Mono,monospace" font-size="7" fill="#1db760" text-anchor="middle">INPUTS</text>
      <line class="s-line" x1="36" y1="122" x2="84" y2="122" stroke="#c084fc" stroke-width="1.8" marker-end="url(#mp)"/>
      <text x="30" y="118" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">ALGAE</text>
      <line class="s-line" x1="36" y1="156" x2="84" y2="156" stroke="#c084fc" stroke-width="1.8" marker-end="url(#mp)"/>
      <text x="32" y="152" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">D-AIR</text>
      <rect id="node-dry" class="pfd-node" x="84" y="104" width="84" height="88" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <line x1="98" y1="104" x2="98" y2="192" stroke="#d8e5dc" stroke-width="0.7"/><line x1="112" y1="104" x2="112" y2="192" stroke="#d8e5dc" stroke-width="0.7"/><line x1="126" y1="104" x2="126" y2="192" stroke="#d8e5dc" stroke-width="0.7"/><line x1="140" y1="104" x2="140" y2="192" stroke="#d8e5dc" stroke-width="0.7"/><line x1="154" y1="104" x2="154" y2="192" stroke="#d8e5dc" stroke-width="0.7"/>
      <text x="126" y="146" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Dryer</text>
      <text x="126" y="160" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">Moisture &amp;</text>
      <text x="126" y="171" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">air removal</text>
      <line class="s-line" x1="126" y1="104" x2="126" y2="74" stroke="#c084fc" stroke-width="1.4" stroke-dasharray="3,2"/>
      <text x="130" y="68" font-family="DM Mono,monospace" font-size="7" fill="#a8c0b2">AIR-H2O</text>
      <line class="s-line" x1="168" y1="148" x2="186" y2="148" stroke="#1db760" stroke-width="1.8"/><line class="s-line" x1="186" y1="148" x2="186" y2="132" stroke="#1db760" stroke-width="1.8"/><line class="s-line" x1="186" y1="132" x2="208" y2="132" stroke="#1db760" stroke-width="1.8" marker-end="url(#mg)"/>
      <text x="188" y="126" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">1</text>
      <rect id="node-dec" class="pfd-node" x="208" y="88" width="84" height="88" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <line x1="222" y1="88" x2="222" y2="176" stroke="#d8e5dc" stroke-width="0.7"/><line x1="236" y1="88" x2="236" y2="176" stroke="#d8e5dc" stroke-width="0.7"/><line x1="250" y1="88" x2="250" y2="176" stroke="#d8e5dc" stroke-width="0.7"/><line x1="264" y1="88" x2="264" y2="176" stroke="#d8e5dc" stroke-width="0.7"/><line x1="278" y1="88" x2="278" y2="176" stroke="#d8e5dc" stroke-width="0.7"/>
      <text x="250" y="128" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Decomposer</text>
      <text x="250" y="142" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">DECOMPSR</text>
      <line class="s-line" x1="36" y1="188" x2="208" y2="188" stroke="#c084fc" stroke-width="1.4" stroke-dasharray="4,2"/><line class="s-line" x1="208" y1="188" x2="208" y2="176" stroke="#c084fc" stroke-width="1.4" stroke-dasharray="4,2" marker-end="url(#mp)"/>
      <text x="38" y="184" font-family="DM Mono,monospace" font-size="7" fill="#a8c0b2">Temp.</text>
      <line class="s-line" x1="292" y1="132" x2="314" y2="132" stroke="#1db760" stroke-width="1.8"/><line class="s-line" x1="314" y1="132" x2="314" y2="172" stroke="#1db760" stroke-width="1.8"/><line class="s-line" x1="314" y1="172" x2="334" y2="172" stroke="#1db760" stroke-width="1.8" marker-end="url(#mg)"/>
      <text x="316" y="126" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">2</text>
      <rect id="node-pyr" class="pfd-node" x="334" y="128" width="84" height="88" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <line x1="348" y1="128" x2="348" y2="216" stroke="#d8e5dc" stroke-width="0.7"/><line x1="362" y1="128" x2="362" y2="216" stroke="#d8e5dc" stroke-width="0.7"/><line x1="376" y1="128" x2="376" y2="216" stroke="#d8e5dc" stroke-width="0.7"/><line x1="390" y1="128" x2="390" y2="216" stroke="#d8e5dc" stroke-width="0.7"/><line x1="404" y1="128" x2="404" y2="216" stroke="#d8e5dc" stroke-width="0.7"/>
      <text x="376" y="168" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Pyrolysis</text>
      <text x="376" y="182" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">PYROLZR</text>
      <line class="s-line" x1="360" y1="250" x2="360" y2="216" stroke="#1db760" stroke-width="1.4" stroke-dasharray="3,2" marker-end="url(#mg)"/>
      <text x="364" y="262" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">INERTS</text>
      <rect class="pyro-glow" x="334" y="128" width="84" height="88" rx="5" fill="#1db760" pointer-events="none"/>
      <line class="s-line" x1="418" y1="172" x2="438" y2="172" stroke="#1db760" stroke-width="1.8"/><line class="s-line" x1="438" y1="172" x2="438" y2="144" stroke="#1db760" stroke-width="1.8"/><line class="s-line" x1="438" y1="144" x2="458" y2="144" stroke="#1db760" stroke-width="1.8" marker-end="url(#mg)"/>
      <text x="440" y="138" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">3</text>
      <rect id="node-sep" class="pfd-node" x="458" y="100" width="80" height="88" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <text x="498" y="140" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Solid</text>
      <text x="498" y="154" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Separator</text>
      <text x="498" y="168" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">S-SEP</text>
      <line id="bio-line" class="s-line" x1="498" y1="188" x2="498" y2="224" stroke="#0f1f17" stroke-width="2.2" marker-end="url(#mk)"/>
      <rect x="472" y="224" width="52" height="16" rx="3" fill="#0f1f17"/>
      <text x="498" y="236" font-family="DM Mono,monospace" font-size="7.5" fill="#fff" text-anchor="middle">BIOCHAR</text>
      <line class="s-line" x1="538" y1="144" x2="556" y2="144" stroke="#3b82f6" stroke-width="1.8"/><line class="s-line" x1="556" y1="144" x2="556" y2="174" stroke="#3b82f6" stroke-width="1.8"/><line class="s-line" x1="556" y1="174" x2="574" y2="174" stroke="#3b82f6" stroke-width="1.8" marker-end="url(#mb)"/>
      <text x="558" y="138" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">4</text>
      <rect id="node-cool" class="pfd-node" x="574" y="140" width="78" height="68" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <text x="613" y="176" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Cooler</text>
      <text x="613" y="190" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">COOLER</text>
      <line class="s-line" x1="652" y1="174" x2="672" y2="174" stroke="#06b6d4" stroke-width="1.8"/><line class="s-line" x1="672" y1="174" x2="672" y2="152" stroke="#06b6d4" stroke-width="1.8"/><line class="s-line" x1="672" y1="152" x2="692" y2="152" stroke="#06b6d4" stroke-width="1.8" marker-end="url(#mc)"/>
      <rect id="node-cli" class="pfd-node" x="692" y="112" width="78" height="68" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <text x="731" y="148" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Clinch</text>
      <text x="731" y="162" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">CLINCH</text>
      <line class="s-line" x1="770" y1="152" x2="790" y2="152" stroke="#06b6d4" stroke-width="1.8"/><line class="s-line" x1="790" y1="152" x2="790" y2="169" stroke="#06b6d4" stroke-width="1.8"/><line class="s-line" x1="790" y1="169" x2="808" y2="169" stroke="#06b6d4" stroke-width="1.8" marker-end="url(#mc)"/>
      <rect id="node-gl" class="pfd-node" x="808" y="125" width="78" height="88" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <text x="847" y="161" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Gas-liquid</text>
      <text x="847" y="175" font-family="DM Sans,sans-serif" font-size="10" font-weight="500" fill="#2b4035" text-anchor="middle">Separator</text>
      <text x="847" y="189" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">GL-SEP</text>
      <line class="s-line" x1="847" y1="213" x2="847" y2="246" stroke="#06b6d4" stroke-width="1.8" marker-end="url(#mc)"/>
      <text x="851" y="258" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">PYRO-OIL</text>
      <line id="lpg" class="s-line" x1="886" y1="155" x2="912" y2="155" stroke="#ef4444" stroke-width="1.8" stroke-dasharray="5,2"/><line class="s-line" x1="912" y1="155" x2="912" y2="132" stroke="#ef4444" stroke-width="1.8" stroke-dasharray="5,2" marker-end="url(#mr)"/>
      <text x="888" y="149" font-family="DM Mono,monospace" font-size="7" fill="#a8c0b2">PYRO-GAS</text>
      <rect id="node-fur" class="pfd-node" x="912" y="88" width="56" height="88" rx="5" fill="#ffffff" stroke="#d8e5dc" stroke-width="1.8"/>
      <line x1="926" y1="88" x2="926" y2="176" stroke="#d8e5dc" stroke-width="0.7"/><line x1="940" y1="88" x2="940" y2="176" stroke="#d8e5dc" stroke-width="0.7"/><line x1="954" y1="88" x2="954" y2="176" stroke="#d8e5dc" stroke-width="0.7"/>
      <text x="940" y="128" font-family="DM Sans,sans-serif" font-size="9.5" font-weight="500" fill="#2b4035" text-anchor="middle">Syngas</text>
      <text x="940" y="141" font-family="DM Sans,sans-serif" font-size="9.5" font-weight="500" fill="#2b4035" text-anchor="middle">Furnace</text>
      <text x="940" y="154" font-family="DM Mono,monospace" font-size="7" fill="#a8c0b2" text-anchor="middle">FURNACE</text>
      <line class="s-line" x1="940" y1="58" x2="940" y2="88" stroke="#ef4444" stroke-width="1.8" stroke-dasharray="5,2" marker-end="url(#mr)"/>
      <text x="944" y="72" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2">F-AIR</text>
      <line class="s-line" x1="940" y1="176" x2="940" y2="210" stroke="#ef4444" stroke-width="1.4" stroke-dasharray="3,2"/>
      <circle cx="940" cy="220" r="10" fill="none" stroke="#d8e5dc" stroke-width="1.6"/>
      <text x="940" y="224" font-family="DM Mono,monospace" font-size="9" fill="#a8c0b2" text-anchor="middle">&#x2295;</text>
      <line class="s-line" x1="950" y1="220" x2="972" y2="220" stroke="#ef4444" stroke-width="1.4" stroke-dasharray="3,2" marker-end="url(#mr)"/>
      <rect x="972" y="210" width="46" height="20" rx="3" fill="none" stroke="#ef4444" stroke-width="1" stroke-dasharray="3,2"/>
      <text x="995" y="223" font-family="DM Mono,monospace" font-size="7.5" fill="#ef4444" text-anchor="middle">ENERGY</text>
      <line class="s-line" x1="940" y1="230" x2="940" y2="258" stroke="#ef4444" stroke-width="1.4" stroke-dasharray="3,2"/>
      <rect x="912" y="258" width="56" height="20" rx="3" fill="none" stroke="#d8e5dc" stroke-width="1.2"/>
      <text x="940" y="271" font-family="DM Mono,monospace" font-size="7.5" fill="#a8c0b2" text-anchor="middle">0DUTY</text>
      <line x1="30" y1="310" x2="52" y2="310" stroke="#c084fc" stroke-width="2"/>
      <text x="56" y="314" font-family="DM Mono,monospace" font-size="8" fill="#a8c0b2">Drying</text>
      <line x1="110" y1="310" x2="132" y2="310" stroke="#1db760" stroke-width="2"/>
      <text x="136" y="314" font-family="DM Mono,monospace" font-size="8" fill="#a8c0b2">Pyrolysis</text>
      <line x1="200" y1="310" x2="222" y2="310" stroke="#3b82f6" stroke-width="2"/>
      <text x="226" y="314" font-family="DM Mono,monospace" font-size="8" fill="#a8c0b2">Solid-Vapor Sep.</text>
      <line x1="370" y1="310" x2="392" y2="310" stroke="#06b6d4" stroke-width="2"/>
      <text x="396" y="314" font-family="DM Mono,monospace" font-size="8" fill="#a8c0b2">Liquid-Vapor Sep.</text>
      <line x1="530" y1="310" x2="552" y2="310" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,2"/>
      <text x="556" y="314" font-family="DM Mono,monospace" font-size="8" fill="#a8c0b2">Heat Integration</text>
    </svg>
  </div>
  <div class="pfd-foot">
    <div class="pf-stat"><span class="pf-lbl">Temperature</span><span class="pf-val" id="st">CT_VAL °C</span></div>
    <div class="pf-stat"><span class="pf-lbl">Residence Time</span><span class="pf-val" id="sr">CR_VAL min</span></div>
    <div class="pf-stat"><span class="pf-lbl">Inert Flow Rate</span><span class="pf-val" id="si">CN_VAL mL/min</span></div>
    <div class="pf-stat"><span class="pf-lbl">Heating Rate</span><span class="pf-val" id="sh">CH_VAL °C/min</span></div>
  </div>
  <div class="guidelines">
    <div class="guide-title">Parameter Guidelines</div>
    <div class="guide-grid">
      <div class="guide-item"><div class="guide-dot"></div>
        <div class="guide-text"><strong>Temperature</strong> — Higher temps (500–700°C) favour carbonisation. Lower temps favour char yield.</div></div>
      <div class="guide-item"><div class="guide-dot"></div>
        <div class="guide-text"><strong>Heating Rate</strong> — Lower rates (5–15°C/min) favour char; higher rates shift toward bio-oil and syngas.</div></div>
      <div class="guide-item"><div class="guide-dot"></div>
        <div class="guide-text"><strong>Residence Time</strong> — Longer durations increase carbonisation.</div></div>
      <div class="guide-item"><div class="guide-dot"></div>
        <div class="guide-text"><strong>N₂ Flow Rate</strong> — Maintains inert atmosphere. Typical 50–300 mL/min.</div></div>
    </div>
  </div>
</div><!-- /pfd-panel -->
</div><!-- /workspace -->

<script>
const ok = {u:false, p:false};
window.addEventListener('load', () => { calcU(); calcP(); });

function tog(id) {
  const was = document.getElementById(id).classList.contains('open');
  ['c1','c2','c3'].forEach(c => document.getElementById(c).classList.remove('open'));
  if (!was) document.getElementById(id).classList.add('open');
}

function calcSum(ids, prefix) {
  const vals = ids.map(id => parseFloat(document.getElementById(id).value)||0);
  const total = vals.reduce((a,b)=>a+b,0);
  const remain = 100-total;
  const isOk = Math.abs(total-100)<=5;
  const isClose = Math.abs(total-100)<=2;
  const barId = prefix==='p'?'pf2':prefix+'f';
  const bar=document.getElementById(barId), badge=document.getElementById(prefix==='u'?'ub':'pb');
  const tv=document.getElementById(prefix+'t'), rv=document.getElementById(prefix+'r');
  if(bar){bar.style.width=Math.min(total,100)+'%';bar.className='sum-fill'+(isOk?'':isClose?' close':' err');}
  if(tv){tv.textContent=total.toFixed(2)+'%';tv.className='t-val'+(total===0?'':isOk?' ok':' err');}
  if(rv){rv.textContent=remain>=0?'Remaining: '+remain.toFixed(2)+'%':'Over by: '+Math.abs(remain).toFixed(2)+'%';rv.className='t-rem'+(isOk?'':' err');}
  if(badge){badge.textContent=total===0?'—':total.toFixed(1)+'%';badge.className='card-badge'+(isOk?' ok':total>0?' err':'');}
  return isOk;
}
function calcU(){ok.u=calcSum(['uc','uh','un','us','uo','ua'],'u');gate();}
function calcP(){ok.p=calcSum(['pm','pv','pf','pa'],'p');gate();}

function sv(id,val,unit){document.getElementById(id).innerHTML=val+' <span class="s-unit">'+unit+'</span>';}
function sstat(id,val,unit){document.getElementById(id).textContent=val+' '+unit;}
function flashNode(id){const el=document.getElementById(id);el.classList.add('lit');setTimeout(()=>el.classList.remove('lit'),900);}
function gate(){document.getElementById('runBtn').disabled=!(ok.u&&ok.p);}

let running=false;
function runSim(){
  if(running)return; running=true;
  const lbl=document.getElementById('runLbl'), cell=document.getElementById('cellBody'), ticker=document.getElementById('phaseTicker');
  cell.classList.add('running'); lbl.textContent='· Simulating ·';
  document.querySelectorAll('.s-line').forEach(l=>l.classList.add('flowing'));
  const phases=['· Initializing Aspen Plus ·','· Decomposing feedstock ·','· Running pyrolysis ·','· Separating products ·','· ML prediction ·','· Finalizing results ·'];
  let i=0; const tick=setInterval(()=>{if(i<phases.length)ticker.textContent=phases[i++];else clearInterval(tick);},300);
  const data={
    C:parseFloat(document.getElementById('uc').value)||0,
    H:parseFloat(document.getElementById('uh').value)||0,
    N:parseFloat(document.getElementById('un').value)||0,
    S:parseFloat(document.getElementById('us').value)||0,
    O:parseFloat(document.getElementById('uo').value)||0,
    Ash:parseFloat(document.getElementById('ua').value)||0,
    Moisture:parseFloat(document.getElementById('pm').value)||0,
    Volatile_Matter:parseFloat(document.getElementById('pv').value)||0,
    Fixed_Carbon:parseFloat(document.getElementById('pf').value)||0,
    Ash_prox:parseFloat(document.getElementById('pa').value)||0,
    temperature:parseFloat(document.getElementById('sT').value)||500,
    residence_time:parseFloat(document.getElementById('sRT').value)||30,
    n2_flow_rate:parseFloat(document.getElementById('sN2').value)||200,
    heating_rate:parseFloat(document.getElementById('sHR').value)||10,
  };
  const payloadStr = JSON.stringify(data);
  try {
    const formEl = window.parent.document.querySelector('[data-testid="stForm"]');
    if (!formEl) { console.warn('[BioCharAI] stForm not found in parent'); running=false; return; }
    const inp = formEl.querySelector('input');
    if (!inp) { console.warn('[BioCharAI] input not found inside stForm'); running=false; return; }

    // React controls input value — must use the native setter then fire both
    // 'input' and 'change' events so React's synthetic event system picks it up
    const nativeSetter = Object.getOwnPropertyDescriptor(
      window.parent.HTMLInputElement.prototype, 'value'
    ).set;
    nativeSetter.call(inp, payloadStr);
    inp.dispatchEvent(new window.parent.Event('input',  { bubbles: true }));
    inp.dispatchEvent(new window.parent.Event('change', { bubbles: true }));
    console.log('[BioCharAI] Payload injected:', payloadStr.slice(0, 80));

    // Give React ~200 ms to process the state update before the button click
    setTimeout(() => {
      const btn = formEl.querySelector('button');
      if (btn) { btn.click(); console.log('[BioCharAI] Submit button clicked'); }
      else { console.warn('[BioCharAI] Submit button not found'); }
    }, 200);
  } catch(e) { console.warn('Streamlit bridge error:', e); }

  setTimeout(()=>{
    cell.classList.remove('running'); lbl.textContent='· Complete ·';
    ticker.textContent='· Scroll down for results ·';
    document.querySelectorAll('.s-line').forEach(l=>l.classList.remove('flowing'));
    document.getElementById('bio-line').classList.add('bio-done');
    document.getElementById('node-pyr').classList.add('lit');
    running=false;
  }, 2200);
}
</script>
</body></html>
""".replace("UC_VAL", str(_u("Carbon",45.2))).replace("UH_VAL", str(_u("Hydrogen",6.8)))\
   .replace("UN_VAL", str(_u("Nitrogen",8.5))).replace("US_VAL", str(_u("Sulfur",0.9)))\
   .replace("UO_VAL", str(_u("Oxygen",38.6))).replace("UA_VAL", "0.0")\
   .replace("PM_VAL", str(_p("Moisture",8.2))).replace("PV_VAL", str(_p("Volatile Matter",72.5)))\
   .replace("PF_VAL", str(_p("Fixed Carbon",14.8))).replace("PA_VAL", str(_p("Ash",4.5)))\
   .replace("CT_VAL", str(int(_c("temperature",500)))).replace("CR_VAL", str(int(_c("residence_time",60))))\
   .replace("CN_VAL", str(int(_c("n2_flow_rate",150)))).replace("CH_VAL", str(int(_c("heating_rate",10))))\
   .replace("T_MIN", str(_r("temperature",0))).replace("T_MAX", str(_r("temperature",1)))\
   .replace("R_MIN", str(_r("residence_time",0))).replace("R_MAX", str(_r("residence_time",1)))\
   .replace("N_MIN", str(_r("n2_flow_rate",0))).replace("N_MAX", str(_r("n2_flow_rate",1)))\
   .replace("H_MIN", str(_r("heating_rate",0))).replace("H_MAX", str(_r("heating_rate",1)))

# ── Render the setup iframe ───────────────────────────────────────────────────
components.html(SETUP_HTML, height=780, scrolling=False)

# ── Hidden form — receives JSON payload from iframe; form-submit triggers rerun
# NOTE: must NOT use display:none — that removes the form from React's render
# cycle and the input value is lost before the button click registers.
st.markdown('''<style>
[data-testid="stForm"]{
    position:fixed!important;
    left:-10000px!important;
    top:-10000px!important;
    width:1px!important;
    height:1px!important;
    overflow:hidden!important;
    opacity:0!important;
}
</style>''', unsafe_allow_html=True)
with st.form("_sim_form", clear_on_submit=True):
    payload_json = st.text_input(
        "payload_hidden", value="", key="_payload",
        label_visibility="collapsed",
    )
    _submitted = st.form_submit_button("Run")

# ── Backend execution — only runs when the user explicitly clicks Simulate ────
# Do NOT auto-run on page load (the old "or sim_result not in session_state"
# condition caused a concurrent default run that disconnected the Aspen COM object)
d = None
if payload_json and payload_json.strip().startswith("{"):
    d = None
    try:
        d = json.loads(payload_json)
    except Exception:
        pass

    if d:
        print(f"[SETUP] Raw payload received from UI: {d}")
        user_inputs = {
            "microalgae_encoded": 0,
            "c": d["C"], "h": d["H"], "n": d["N"], "s": d["S"], "o": d["O"],
            "ash": d["Ash"] if d["Ash"] > 0 else d["Ash_prox"],
            "moisture": d["Moisture"], "volatile_matter": d["Volatile_Matter"], "fixed_carbon": d["Fixed_Carbon"],
            "temperature": float(d["temperature"]),
            "residence_time_min": float(d["residence_time"]),
            "n2_flow_rate_ml_per_min": float(d["n2_flow_rate"]),
            "heating_rate_c_per_min": float(d["heating_rate"]),
        }
        print(f"[SETUP] Using USER inputs: {user_inputs}")
    else:
        print("[SETUP] ERROR: payload_json present but JSON parse failed — skipping run.")
        d = None

if d:
    import time
    start_t = time.time()
    with st.spinner("Running Aspen Plus + ML pipeline…"):
        result = pipeline.run(user_inputs)
    inference_ms = (time.time() - start_t) * 1000.0

    # Diagnostic — confirm what landed in result["aspen"]. If the Sensitivity page
    # later shows "no sensitivity tables," the terminal here is the ground truth.
    _aspen_keys = sorted(result["aspen"].keys())
    print(f"[SETUP] pipeline.run done in {inference_ms:.0f} ms. aspen keys: {_aspen_keys}")
    _sens = result["aspen"].get("sensitivities") or {}
    if _sens:
        _populated = sum(1 for b in _sens.values() if isinstance(b, dict) and b.get("xs"))
        print(f"[SETUP] sensitivities: {len(_sens)} blocks declared, {_populated} populated.")
    else:
        print("[SETUP] sensitivities: MISSING from aspen result — Sensitivity page will gate.")

    st.session_state["sim_result"] = result
    st.session_state["sim_inputs"] = user_inputs

    try:
      stg2 = result["stage2"]
      predictions = {
        "surface": {
          "BET Surface Area (m²/g)": stg2.get("bet_surface_area_m_2_per_g", 0.0),
          "Pore Volume (cm³/g)": stg2.get("pore_volume_cm_3_per_g", 0.0),
        },
        "adsorption": {k.replace("adsorption_capacity_for_", "").replace("_mg_per_g", ""): v for k, v in stg2.items() if "adsorption" in k},
        "removal": {k.replace("removal_efficiency_for_", "").replace("_mg_per_g", ""): v for k, v in stg2.items() if "removal" in k},
      }

      log_prediction(
        species="Unknown Microalgae", # Dummy since UI only gives encoded value
        conditions={"temperature": user_inputs['temperature'],
              "residence_time": user_inputs['residence_time_min'],
              "heating_rate": user_inputs['heating_rate_c_per_min'],
              "n2_flow_rate": user_inputs['n2_flow_rate_ml_per_min']},
        ultimate={"Carbon": user_inputs['c'], "Hydrogen": user_inputs['h'], "Nitrogen": user_inputs['n'], "Sulfur": user_inputs['s'], "Oxygen": user_inputs['o']},
        proximate={"Moisture": user_inputs['moisture'], "Volatile Matter": user_inputs['volatile_matter'], "Fixed Carbon": user_inputs['fixed_carbon'], "Ash": user_inputs.get('ash', 0)},
        predictions=predictions,
        model_info={"dummy": {"r2_cv": 0.8}}, # Passing status
        inference_ms=inference_ms
      )
    except Exception:
      pass # Failsafe

# ── DISPLAY RESULTS ──
if "sim_result" in st.session_state:
    result = st.session_state["sim_result"]
    user = result["user"]
    aspen = result["aspen"]
    stg1 = result["stage1"]
    stg2 = result["stage2"]
    
    T  = user.get("temperature", 500)
    RT = user.get("residence_time_min", 60)
    N2 = user.get("n2_flow_rate_ml_per_min", 150)
    HR = user.get("heating_rate_c_per_min", 10)

    # ── Results CSS (scoped, no conflicts with Streamlit) ─────────────────
    st.markdown("""
    <style>
    .rp{padding:24px 0 60px;}
    .rs{background:#fff;border:1px solid #d8e5dc;border-radius:10px;padding:14px 22px;
      display:flex;gap:28px;align-items:center;flex-wrap:wrap;margin-bottom:24px;}
    .rp-l{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.14em;
      text-transform:uppercase;color:#a8c0b2;margin-bottom:2px;}
    .rp-v{font-family:'DM Mono',monospace;font-size:12px;color:#0f1f17;}
    .rp-d{width:1px;height:24px;background:#d8e5dc;flex-shrink:0;}
    .rp-b{margin-left:auto;font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.14em;
      text-transform:uppercase;color:#1db760;background:rgba(29,183,96,.08);padding:5px 12px;border-radius:20px;}
    .rsh{display:flex;align-items:center;gap:12px;margin:0 0 12px;}
    .rsn{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.14em;color:#1db760;}
    .rst{font-size:15px;font-weight:500;color:#0f1f17;}
    .rss{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.14em;text-transform:uppercase;color:#a8c0b2;margin-left:auto;}
    .rsd{height:1px;background:#d8e5dc;margin-bottom:16px;}
    .mc{background:#fff;border:1px solid #d8e5dc;border-radius:10px;padding:16px 18px;}
    .mc.hl{border-color:#1db760;background:rgba(29,183,96,.08);}
    .mc.hl-c{border-color:#3ec9a7;background:rgba(62,201,167,.06);}
    .mc-l{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.14em;text-transform:uppercase;color:#a8c0b2;margin-bottom:8px;}
    .mc-v{font-family:'DM Mono',monospace;font-size:22px;color:#0f1f17;letter-spacing:-.02em;line-height:1;}
    .mc-v.g{color:#1db760;}.mc-v.c{color:#3ec9a7;}.mc-v.a{color:#e8a23a;}
    .mc-u{font-family:'DM Mono',monospace;font-size:10px;color:#a8c0b2;margin-left:3px;}
    .mc-n{margin-top:6px;font-size:11px;font-weight:300;color:#5a7a68;}
    .t3g{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;}
    .t3c{background:#fff;border:1px solid #d8e5dc;border-radius:10px;padding:18px;border-top:3px solid #1db760;}
    .t3r{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.16em;text-transform:uppercase;color:#a8c0b2;margin-bottom:6px;}
    .t3n{font-size:14px;font-weight:500;color:#0f1f17;margin-bottom:12px;}
    .t3m{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
    .t3ml{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.1em;text-transform:uppercase;color:#a8c0b2;margin-bottom:3px;}
    .t3mv{font-family:'DM Mono',monospace;font-size:15px;letter-spacing:-.01em;}
    .t3mu{font-size:9px;color:#a8c0b2;margin-left:2px;}
    .mbb{margin-top:12px;}
    .mbl{display:flex;justify-content:space-between;margin-bottom:4px;}
    .mbl span{font-family:'DM Mono',monospace;font-size:8px;color:#a8c0b2;}
    .mbt{height:3px;background:#d8e5dc;border-radius:2px;overflow:hidden;}
    .mbf{height:100%;border-radius:2px;}
    .mcg6{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin-bottom:4px;}
    .mcg4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:4px;}
    @media (max-width:1200px){.mcg6{grid-template-columns:repeat(3,minmax(0,1fr));}.mcg4{grid-template-columns:repeat(2,minmax(0,1fr));}}
    @media (max-width:760px){.mcg6,.mcg4{grid-template-columns:repeat(1,minmax(0,1fr));}}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border:0;border-top:1px solid var(--dust);margin:30px 0;">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="rp">
    <div class="rs">
      <div><div class="rp-l">Temperature</div><div class="rp-v">{T:.0f} °C</div></div>
      <div class="rp-d"></div>
      <div><div class="rp-l">Residence Time</div><div class="rp-v">{RT:.0f} min</div></div>
      <div class="rp-d"></div>
      <div><div class="rp-l">Inert Flow Rate</div><div class="rp-v">{N2:.0f} mL/min</div></div>
      <div class="rp-d"></div>
      <div><div class="rp-l">Heating Rate</div><div class="rp-v">{HR:.0f} °C/min</div></div>
      <div class="rp-b">· Simulation complete ·</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # 01 Ultimate
    st.markdown('<div class="rsh"><span class="rsn">01</span><span class="rst">Biochar Ultimate Analysis</span><span class="rss">Stage 1 AI Prediction</span></div><div class="rsd"></div>', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="mcg6">
      <div class="mc"><div class="mc-l">C</div><div class="mc-v">{stg1.get("c_1", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">H</div><div class="mc-v">{stg1.get("h_1", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">N</div><div class="mc-v">{stg1.get("n_1", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">O</div><div class="mc-v">{stg1.get("o_1", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">S</div><div class="mc-v">{user.get("s", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">Ash</div><div class="mc-v">{stg1.get("ash_content", 0):.2f}<span class="mc-u">wt%</span></div></div>
    </div>
    ''', unsafe_allow_html=True)

    # 02 Proximate
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rsh"><span class="rsn">02</span><span class="rst">Biochar Proximate Analysis</span><span class="rss">Stage 1 AI Prediction (Normalized)</span></div><div class="rsd"></div>', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="mcg4">
      <div class="mc"><div class="mc-l">Moisture</div><div class="mc-v">{stg1.get("moisture_content", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">Volatile Matter</div><div class="mc-v">{stg1.get("volatile_matter_output", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">Fixed Carbon</div><div class="mc-v">{stg1.get("fixed_carbon_output", 0):.2f}<span class="mc-u">wt%</span></div></div>
      <div class="mc"><div class="mc-l">Ash</div><div class="mc-v">{stg1.get("ash_content", 0):.2f}<span class="mc-u">wt%</span></div></div>
    </div>
    ''', unsafe_allow_html=True)

    # 03 Pyrolysis outputs
    bc = aspen.get("biochar_yield_pct", 36.6)
    bo = aspen.get("bio_oil_yield_pct", 21.5)
    sg = aspen.get("syngas_yield_pct",  38.6)
    hv = stg1.get("energy_content_mj_per_kg", 20.1)
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rsh"><span class="rsn">03</span><span class="rst">Pyrolysis Outputs</span><span class="rss">Aspen Plus · Equilibrium Model</span></div><div class="rsd"></div>', unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1: st.markdown(f'<div class="mc hl"><div class="mc-l">Biochar Yield</div><div class="mc-v g">{bc:.1f}<span class="mc-u">wt%</span></div><div class="mc-n">Primary solid product</div></div>', unsafe_allow_html=True)
    with r2: st.markdown(f'<div class="mc"><div class="mc-l">Bio-oil Yield</div><div class="mc-v">{bo:.1f}<span class="mc-u">wt%</span></div><div class="mc-n">Liquid condensate</div></div>', unsafe_allow_html=True)
    with r3: st.markdown(f'<div class="mc"><div class="mc-l">Syngas Yield</div><div class="mc-v">{sg:.1f}<span class="mc-u">wt%</span></div><div class="mc-n">Non-condensable gas</div></div>', unsafe_allow_html=True)
    with r4: st.markdown(f'<div class="mc"><div class="mc-l">Biochar HHV</div><div class="mc-v">{hv:.1f}<span class="mc-u">MJ/kg</span></div><div class="mc-n">Higher heating value</div></div>', unsafe_allow_html=True)

    # 04 Biochar properties
    bet  = stg2.get("bet_surface_area_m_2_per_g", 0.0)
    pore = stg2.get("pore_volume_cm_3_per_g", 0.0)
    bet_str  = f"{bet:.1f} m²/g"  if bet  >= 0 else "N/A"
    pore_str = f"{pore:.4f} cm³/g" if pore >= 0 else "N/A"
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="rsh"><span class="rsn">04</span><span class="rst">Biochar Microstructural Properties</span><span class="rss">Stage 2 AI Prediction</span></div><div class="rsd"></div>', unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1: st.markdown(f'<div class="mc hl"><div class="mc-l">BET Surface Area</div><div class="mc-v g">{bet_str}</div><div class="mc-n">Predicted specific surface area at {T:.0f}°C.</div></div>', unsafe_allow_html=True)
    with s2: st.markdown(f'<div class="mc hl-c"><div class="mc-l">Pore Volume</div><div class="mc-v c">{pore_str}</div><div class="mc-n">Total pore volume for contaminant uptake.</div></div>', unsafe_allow_html=True)

    # 05 Adsorption
    def _clean_name(k):
        name = k.replace("adsorption_capacity_for_", "").replace("removal_efficiency_for_", "")
        name = name.replace("_mg_per_g", "").replace("_pct", "")
        name = name.replace("pb_2", "Pb²⁺").replace("cr_6", "Cr⁶⁺").replace("cu_2", "Cu²⁺")
        name = name.replace("cd_2", "Cd²⁺").replace("zn_2", "Zn²⁺")
        return name.replace("_", " ").title()

    # -1 means out-of-range / unreliable — exclude from display
    ads_keys = {k: v for k, v in stg2.items() if k.startswith("adsorption") and v >= 0}
    rem_keys = {k: v for k, v in stg2.items() if k.startswith("removal") and v >= 0}
    top_ads = sorted(ads_keys.items(), key=lambda x: x[1], reverse=True)

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rsh"><span class="rsn">05</span><span class="rst">Adsorption Performance</span><span class="rss">{len(top_ads)} active contaminants · Stage 2 AI</span></div><div class="rsd"></div>', unsafe_allow_html=True)

    # ── Build top-3 cards + full bar chart as one HTML block ─────────────────
    top3_colors = ["#1db760", "#3ec9a7", "#e8a23a"]
    top3_ranks  = ["· Top performer ·", "· 2nd ·", "· 3rd ·"]

    # top-3 cards HTML
    top3_html = ""
    for i, ((k, cap_val), color, rank) in enumerate(zip(top_ads[:3], top3_colors, top3_ranks)):
        rem_k   = k.replace("adsorption_capacity", "removal_efficiency")
        rem_val = rem_keys.get(rem_k, 0)
        name    = _clean_name(k)
        bar_pct = min(rem_val, 100)
        nth_fill = f"background:{color}"
        top3_html += f"""
        <div class="top3-card" style="border-top:3px solid {color}">
          <div class="top3-rank">{rank}</div>
          <div class="top3-name">{name}</div>
          <div class="top3-metrics">
            <div>
              <div class="top3-m-lbl">Adsorption Cap.</div>
              <div class="top3-m-val" style="color:{color}">{cap_val:.1f}<span class="top3-m-unit">mg/g</span></div>
            </div>
            <div>
              <div class="top3-m-lbl">Removal Eff.</div>
              <div class="top3-m-val" style="color:{color}">{rem_val:.1f}<span class="top3-m-unit">%</span></div>
            </div>
          </div>
          <div class="mini-bar-wrap">
            <div class="mini-bar-lbl">
              <span>Removal efficiency</span>
              <span style="color:{color}">{rem_val:.1f}%</span>
            </div>
            <div class="mini-bar-track"><div class="mini-bar-fill" style="width:{bar_pct:.1f}%;{nth_fill}"></div></div>
          </div>
        </div>"""

    # full dataset JSON for JS
    import json as _json
    bar_colors = ["#1db760","#18a854","#159149","#127a3e","#0f6433",
                  "#3ec9a7","#2db896","#26a585","#1e9274",
                  "#e8a23a","#d4923a","#c07e30","#aa6a26"]
    cap_data = _json.dumps([
        {"name": _clean_name(k), "val": round(v, 2),
         "max": max((v2 for _, v2 in top_ads), default=1),
         "color": bar_colors[i % len(bar_colors)]}
        for i, (k, v) in enumerate(top_ads)
    ])
    rem_data = _json.dumps([
        {"name": _clean_name(k), "val": round(rem_keys.get(k.replace("adsorption_capacity","removal_efficiency"), 0), 2),
         "max": 100,
         "color": bar_colors[i % len(bar_colors)]}
        for i, (k, _) in enumerate(top_ads)
    ])

    chart_height = 60 + len(top_ads) * 36  # approx px for bar rows

    # Top-3 cards (no JS, safe for st.markdown)
    top3_cards_html = f"""
<style>
.top3-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px;}}
.top3-card{{background:#fff;border:1px solid #d8e5dc;border-radius:10px;padding:20px;}}
.top3-rank{{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.16em;text-transform:uppercase;color:#a8c0b2;margin-bottom:8px;}}
.top3-name{{font-size:14px;font-weight:500;color:#0f1f17;margin-bottom:14px;}}
.top3-metrics{{display:grid;grid-template-columns:1fr 1fr;gap:8px;}}
.top3-m-lbl{{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.1em;text-transform:uppercase;color:#a8c0b2;margin-bottom:3px;}}
.top3-m-val{{font-family:'DM Mono',monospace;font-size:16px;color:#0f1f17;letter-spacing:-.01em;}}
.top3-m-unit{{font-size:9px;color:#a8c0b2;margin-left:2px;}}
.mini-bar-wrap{{margin-top:14px;}}
.mini-bar-lbl{{display:flex;justify-content:space-between;margin-bottom:4px;}}
.mini-bar-lbl span{{font-family:'DM Mono',monospace;font-size:8px;color:#a8c0b2;}}
.mini-bar-track{{height:3px;background:#d8e5dc;border-radius:2px;overflow:hidden;}}
.mini-bar-fill{{height:100%;border-radius:2px;}}
</style>
<div class="top3-grid">{top3_html}</div>
"""
    st.markdown(top3_cards_html, unsafe_allow_html=True)

    # Bar chart — must use components.html so <script> executes
    chart_rows = len(top_ads)
    chart_iframe_height = 120 + chart_rows * 36  # header + rows

    chart_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#f5f8f5;font-family:'DM Sans',sans-serif;padding:0;}}
.chart-card{{background:#fff;border:1px solid #d8e5dc;border-radius:10px;padding:24px;}}
.chart-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:8px;}}
.chart-title{{font-size:13px;font-weight:500;color:#0f1f17;}}
.chart-toggle{{display:flex;}}
.chart-tab{{font-family:'DM Mono',monospace;font-size:8px;letter-spacing:.12em;text-transform:uppercase;padding:5px 12px;border:1px solid #d8e5dc;cursor:pointer;color:#a8c0b2;background:#f5f8f5;transition:all .15s;}}
.chart-tab:first-child{{border-radius:5px 0 0 5px;}}
.chart-tab:last-child{{border-radius:0 5px 5px 0;border-left:none;}}
.chart-tab.active{{background:#fff;color:#0f1f17;}}
.bars-wrap{{display:flex;flex-direction:column;gap:10px;}}
.bar-row{{display:flex;align-items:center;gap:12px;}}
.bar-name{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.06em;color:#2b4035;width:130px;flex-shrink:0;text-align:right;}}
.bar-track{{flex:1;height:20px;background:#eef3ee;border-radius:4px;overflow:hidden;}}
.bar-fill{{height:100%;border-radius:4px;display:flex;align-items:center;justify-content:flex-end;padding-right:6px;transition:width .9s ease;}}
.bar-fill-val{{font-family:'DM Mono',monospace;font-size:8px;color:rgba(255,255,255,0.92);white-space:nowrap;}}
</style>
</head><body>
<div class="chart-card">
  <div class="chart-head">
    <span class="chart-title">All {len(top_ads)} Contaminants</span>
    <div class="chart-toggle">
      <div class="chart-tab active" id="tab-cap" onclick="switchTab('cap')">Adsorption Capacity</div>
      <div class="chart-tab" id="tab-rem" onclick="switchTab('rem')">Removal Efficiency</div>
    </div>
  </div>
  <div class="bars-wrap" id="barsWrap"></div>
</div>
<script>
var datasets = {{ "cap": {cap_data}, "rem": {rem_data} }};
function renderBars(key) {{
  var wrap = document.getElementById('barsWrap');
  wrap.innerHTML = '';
  var items = datasets[key];
  var maxVal = 0;
  for (var i=0;i<items.length;i++) if(items[i].val > maxVal) maxVal = items[i].val;
  if (maxVal === 0) maxVal = 1;
  items.forEach(function(d) {{
    var pct = (d.val / maxVal * 100).toFixed(1);
    var unit = key === 'cap' ? ' mg/g' : '%';
    var row = document.createElement('div');
    row.className = 'bar-row';
    row.innerHTML = '<div class="bar-name">' + d.name + '</div>' +
      '<div class="bar-track"><div class="bar-fill" style="width:0%;background:' + d.color + '" data-pct="' + pct + '">' +
      '<span class="bar-fill-val">' + d.val + unit + '</span></div></div>';
    wrap.appendChild(row);
  }});
  requestAnimationFrame(function() {{
    document.querySelectorAll('.bar-fill').forEach(function(b) {{
      b.style.width = b.dataset.pct + '%';
    }});
  }});
}}
function switchTab(key) {{
  document.getElementById('tab-cap').classList.toggle('active', key === 'cap');
  document.getElementById('tab-rem').classList.toggle('active', key === 'rem');
  renderBars(key);
}}
renderBars('cap');
</script>
</body></html>"""
    components.html(chart_html, height=chart_iframe_height, scrolling=False)

    # ── Out-of-range / inaccurate predictions warning ──────────────────────
    # Collect every Stage-2 key that was flagged -1 (outside STAGE2_RANGES)
    _OOR_LABELS = {
        "bet_surface_area_m_2_per_g":                        "BET Surface Area",
        "pore_volume_cm_3_per_g":                            "Pore Volume",
        "adsorption_capacity_for_pb_2_mg_per_g":             "Adsorption – Pb²⁺",
        "adsorption_capacity_for_cu_2_mg_per_g":             "Adsorption – Cu²⁺",
        "adsorption_capacity_for_cr_6_mg_per_g":             "Adsorption – Cr⁶⁺",
        "adsorption_capacity_for_cd_2_mg_per_g":             "Adsorption – Cd²⁺",
        "adsorption_capacity_for_zn_2_mg_per_g":             "Adsorption – Zn²⁺",
        "adsorption_capacity_for_methylene_blue_mg_per_g":   "Adsorption – Methylene Blue",
        "adsorption_capacity_for_rhodamine_b_mg_per_g":      "Adsorption – Rhodamine B",
        "adsorption_capacity_for_malachite_green_mg_per_g":  "Adsorption – Malachite Green",
        "adsorption_capacity_for_congo_red_mg_per_g":        "Adsorption – Congo Red",
        "adsorption_capacity_for_ammonium_mg_per_g":         "Adsorption – Ammonium",
        "adsorption_capacity_for_phosphate_mg_per_g":        "Adsorption – Phosphate",
        "adsorption_capacity_for_phenol_mg_per_g":           "Adsorption – Phenol",
        "adsorption_capacity_for_tetracycline_mg_per_g":     "Adsorption – Tetracycline",
        "removal_efficiency_for_pb_2_mg_per_g":              "Removal Eff. – Pb²⁺",
        "removal_efficiency_for_cu_2_mg_per_g":              "Removal Eff. – Cu²⁺",
        "removal_efficiency_for_cr_6_mg_per_g":              "Removal Eff. – Cr⁶⁺",
        "removal_efficiency_for_cd_2_mg_per_g":              "Removal Eff. – Cd²⁺",
        "removal_efficiency_for_zn_2_mg_per_g":              "Removal Eff. – Zn²⁺",
        "removal_efficiency_for_methylene_blue_mg_per_g":    "Removal Eff. – Methylene Blue",
        "removal_efficiency_for_rhodamine_b_mg_per_g":       "Removal Eff. – Rhodamine B",
        "removal_efficiency_for_malachite_green_mg_per_g":   "Removal Eff. – Malachite Green",
        "removal_efficiency_for_congo_red_mg_per_g":         "Removal Eff. – Congo Red",
        "removal_efficiency_for_ammonium_mg_per_g":          "Removal Eff. – Ammonium",
        "removal_efficiency_for_phosphate_mg_per_g":         "Removal Eff. – Phosphate",
        "removal_efficiency_for_phenol_mg_per_g":            "Removal Eff. – Phenol",
        "removal_efficiency_for_tetracycline_mg_per_g":      "Removal Eff. – Tetracycline",
    }
    oor_items = [
        _OOR_LABELS.get(k, k)
        for k, v in stg2.items()
        if v == -1.0 and k in _OOR_LABELS
    ]

    if oor_items:
        pills_html = "".join(
            f'<span style="display:inline-block;font-family:\'DM Mono\',monospace;font-size:10px;'
            f'background:#fff8ed;border:1px solid #e8a23a;color:#a06010;border-radius:20px;'
            f'padding:3px 10px;margin:3px 4px 3px 0;">{name}</span>'
            for name in oor_items
        )
        st.markdown(f"""
<style>
.oor-box{{margin-top:20px;background:#fffdf7;border:1px solid #f0c060;border-left:4px solid #e8a23a;
  border-radius:10px;padding:18px 22px;}}
.oor-head{{display:flex;align-items:center;gap:10px;margin-bottom:8px;}}
.oor-icon{{font-size:16px;line-height:1;}}
.oor-title{{font-size:13px;font-weight:500;color:#7a4d00;}}
.oor-body{{font-size:12px;font-weight:300;color:#7a5a20;line-height:1.6;margin-bottom:12px;}}
.oor-pills{{line-height:2.2;}}
</style>
<div class="oor-box">
  <div class="oor-head">
    <span class="oor-icon">⚠</span>
    <span class="oor-title">Some predictions are outside validated ranges and may be inaccurate</span>
  </div>
  <div class="oor-body">
    The following {len(oor_items)} predictions fell outside the model's validated output ranges
    and have been flagged as unreliable. They are excluded from the charts above and should not
    be used for engineering decisions without additional experimental validation.
  </div>
  <div class="oor-pills">{pills_html}</div>
</div>
""", unsafe_allow_html=True)
    
    
    # Explore further
    st.markdown("""
    <div style="margin-top:40px;padding-top:32px;border-top:1px solid #d8e5dc;">
      <div style="font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.24em;text-transform:uppercase;color:#a8c0b2;margin-bottom:8px;">Want to explore further?</div>
      <div style="font-size:20px;font-weight:200;letter-spacing:-.02em;color:#0f1f17;margin-bottom:6px;">Go deeper with your <strong style="font-weight:500">current inputs.</strong></div>
      <p style="font-size:13px;font-weight:300;color:#5a7a68;line-height:1.7;max-width:560px;margin-bottom:20px;">Run a sensitivity analysis to explore parameter effects or validate this run's mass and energy balance</p>
    </div>
    """, unsafe_allow_html=True)

    ec1, ec2 = st.columns(2)
    with ec1:
        if st.button("Sensitivity Analysis →", use_container_width=True, key="go_sens"):
            st.switch_page("pages/2_Sensitivity_Analysis.py")
    with ec2:
        if st.button("Validation →", use_container_width=True, key="go_val"):
            st.switch_page("pages/4_Validation.py")

