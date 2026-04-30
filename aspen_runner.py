import win32com.client as win32
import pythoncom
import os
import time
 
BKP_PATH = r"C:\Users\s202170970\Desktop\Senior Design Project old ready file.bkp"
 
def safe_get(aspen, path):
    try:
        node = aspen.Tree.FindNode(path)
        if node is None:
            print(f"[ASPEN safe_get] Node NOT FOUND: {path}")
            return 0.0
        val = node.Value
        print(f"[ASPEN safe_get] {path.split(chr(92))[-1]} = {val}")
        return val
    except Exception as e:
        print(f"[ASPEN safe_get] EXCEPTION reading {path}: {e}")
        return 0.0
 
def run_aspen(user_input):
    pythoncom.CoInitialize()
    try:
        return _run_aspen_impl(user_input)
    finally:
        pythoncom.CoUninitialize()
 
def _run_aspen_impl(user_input):
    print(f"[ASPEN] BKP path: {BKP_PATH}")
    if not os.path.exists(BKP_PATH):
        raise FileNotFoundError(f"[ASPEN] BKP file not found at: {BKP_PATH}")
 
    aspen = win32.Dispatch("Apwn.Document")
    aspen.InitFromArchive2(BKP_PATH)
    aspen.Visible = True
    aspen.SuppressDialogs = True
 
    # Log inputs being written
    print(f"[ASPEN INPUT] ash={user_input['ash']}, c={user_input['c']}, h={user_input['h']}, "
          f"n={user_input['n']}, s={user_input['s']}, o={user_input['o']}")
    print(f"[ASPEN INPUT] moisture={user_input['moisture']}, fixed_carbon={user_input['fixed_carbon']}, "
          f"volatile_matter={user_input['volatile_matter']}")
 
    # Set inputs — each write is guarded so a wrong path is reported clearly
    def safe_set(path, value):
        try:
            node = aspen.Tree.FindNode(path)
            if node is None:
                print(f"[ASPEN safe_set] Node NOT FOUND (write skipped): {path}")
                return False
            node.Value = value
            print(f"[ASPEN safe_set] {path.split(chr(92))[-1]} <- {value}")
            return True
        except Exception as e:
            print(f"[ASPEN safe_set] EXCEPTION writing {path} = {value}: {e}")
            return False
 
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\ULTANAL\#0", user_input["ash"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\ULTANAL\#1", user_input["c"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\ULTANAL\#2", user_input["h"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\ULTANAL\#3", user_input["n"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\ULTANAL\#4", 0.0)
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\ULTANAL\#5", user_input["s"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\ULTANAL\#6", user_input["o"])
 
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\PROXANAL\#0", user_input["moisture"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\PROXANAL\#1", user_input["fixed_carbon"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\PROXANAL\#2", user_input["volatile_matter"])
    safe_set(r"\Data\Streams\ALGAE\Input\ELEM\NC\ALGAE\PROXANAL\#3", user_input["ash"])
 
    # Pyrolysis reactor temperature (decomposer block)
    safe_set(r"\Data\Blocks\DECOMPSR\Input\TEMP", user_input["temperature"])
 
    print("[ASPEN] All inputs written to Aspen tree.")
 
    # Reinitialize before run so Aspen picks up the new input values
    print("[ASPEN] Calling Engine.Reinit()...")
    aspen.Engine.Reinit()
 
    # Run and wait for completion
    aspen.Engine.Run2()
    print("[ASPEN] Simulation started, waiting for completion...")
 
    timeout = 300
    elapsed = 0
    while aspen.Engine.IsRunning and elapsed < timeout:
        time.sleep(2)
        elapsed += 2
        print(f"[ASPEN] Still running... {elapsed}s elapsed")
 
    if aspen.Engine.IsRunning:
        raise TimeoutError(f"[ASPEN] Simulation did not finish within {timeout}s")
 
    print("[ASPEN] Simulation complete. Reading outputs...")
 
    # Read outputs
    dryalgae   = safe_get(aspen, r"\Data\Streams\DRYALGAE\Output\MASSFLOW\NC\ALGAE")
    inerts_n2  = safe_get(aspen, r"\Data\Streams\INERTS\Output\MASSFLOW\MIXED\N2")
    inerts_o2  = safe_get(aspen, r"\Data\Streams\INERTS\Output\MASSFLOW\MIXED\O2")
    biochar_c  = safe_get(aspen, r"\Data\Streams\BIOCHAR\Output\MASSFLOW\MIXED\C")
    biochar_ash= safe_get(aspen, r"\Data\Streams\BIOCHAR\Output\MASSFLOW\NC\ASH")
 
    biochar_flow = biochar_c + biochar_ash
    print(f"[ASPEN OUTPUT] dryalgae={dryalgae}, biochar_flow={biochar_flow}")
 
    pyrooil_components = [
    # Light gases
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\H2O",
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\CO2",
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\CH4",
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\C2H6",
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\N2",
 
    # Sulfur / nitrogen species
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\H2S",
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\NH3",
 
    # C1 oxygenates
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\METHA-01",   # methanol
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\FORMA-01",   # formaldehyde
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\FORMI-01",   # formic acid
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\KETEN-01",   # ketene
 
    # C2 oxygenates
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\ACETA-01",   # acetaldehyde
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\ACETA-02",   # acetic acid
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\GLYCO-01",   # glycolaldehyde
 
    # Furan / pyran derivatives
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\PURULV-01",  # furfural / levulinic
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\METO-03",
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\FORM-01",
 
    # Anhydrosugars / oligomers
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\GLUA1-01",   # glucuronic acid derivative
 
    # Trace / unidentified
    r"\Data\Streams\PYRO-OIL\Output\MASSFLOW\MIXED\6-12425E-09",
    ]
    pyrogas_components = [
# Light gases
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\H2O",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\H2",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\CO",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\CO2",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\CH4",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\C2H6",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\C2H4O2",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\PROPANE",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\PROPENE",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\N2",
 
    # Sulfur / nitrogen species
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\H2S",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\NH3",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\HCN",
 
    # C1 oxygenates
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\METHA-01",   # methanol
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\FORMA-01",   # formaldehyde
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\FORMI-01",   # formic acid
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\KETEN-01",   # ketene
 
    # C2 oxygenates
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\ACETA-01",   # acetaldehyde
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\ACETA-02",   # acetic acid
 
    # Furan / pyran derivatives
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\METO-03",
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\FORM-01",
 
    # Anhydrosugars / oligomers
    r"\Data\Streams\PYRO-GAS\Output\MASSFLOW\MIXED\GLUA1-01",   # glucuronic acid derivative
    ]
 
    pyrooil_flow = sum(safe_get(aspen, p) for p in pyrooil_components)
    pyrogas_flow = sum(safe_get(aspen, p) for p in pyrogas_components) - inerts_n2 - inerts_o2
    pyrogas_flow = max(0.0, pyrogas_flow)
 
    print(f"[ASPEN OUTPUT] pyrooil_flow={pyrooil_flow}, pyrogas_flow={pyrogas_flow}, "
          f"inerts_n2={inerts_n2}, inerts_o2={inerts_o2}")
 
    if dryalgae <= 0:
        raise ValueError(
            f"[ASPEN] DRYALGAE massflow is {dryalgae} — simulation likely did not converge "
            f"or the output node path is wrong. Check stream name 'DRYALGAE' in your model."
        )
 
    result = {
        "biochar_yield_pct": round((biochar_flow / dryalgae) * 100, 2),
        "bio_oil_yield_pct": round((pyrooil_flow  / dryalgae) * 100, 2),
        "syngas_yield_pct":  round((pyrogas_flow  / dryalgae) * 100, 2),
        "temperature":       user_input["temperature"],
    }
    print(f"[ASPEN] Yields: {result}")
 
    # ── Aspen-embedded sensitivity blocks — DEBUG PRINT ONLY (no result yet) ──
    _print_sensitivities(aspen)
 
    return result
 
 
# ── Configuration: every Aspen sensitivity block to extract ──────────────────
# Path structure for each block: \SENSVAR\<row>\<col>
# To add a new block, just append one dict — no code changes needed elsewhere.
SENSITIVITY_BLOCKS = [
    {
        "key":      "cfracvsp",
        "block":    "CFRACVSP",
        "x_col":    1,
        "x_label":  "Pressure (bar)",
        "y_series": [{"col": 2, "label": "Carbon Fraction"}],
        "title":    "Carbon Fraction vs Pressure",
    },
    {
        "key":      "cfracvst",
        "block":    "CFRACVST",
        "x_col":    1,
        "x_label":  "Temperature (°C)",
        "y_series": [{"col": 2, "label": "Carbon Fraction"}],
        "title":    "Carbon Fraction vs Temperature",
    },
    {
        "key":      "yieldvst",
        "block":    "YIELDVST",
        "x_col":    1,
        "x_label":  "Temperature (°C)",
        "y_series": [
            {"col": 2, "label": "Biochar (%)"},
            {"col": 3, "label": "Bio-oil (%)"},
            {"col": 4, "label": "Syngas (%)"},
        ],
        "title":    "Pyrolysis Yields vs Temperature",
    },
    {
        "key":      "yieldvsp",
        "block":    "YIELDVSP",
        "x_col":    1,
        "x_label":  "Pressure (bar)",
        "y_series": [
            {"col": 2, "label": "Biochar (%)"},
            {"col": 3, "label": "Bio-oil (%)"},
            {"col": 4, "label": "Syngas (%)"},
        ],
        "title":    "Pyrolysis Yields vs Pressure",
    },
    {
        "key":      "yieldvsn",
        "block":    "YIELDVSN",
        "x_col":    1,
        "x_label":  "N₂ Flow Rate (mL/min)",
        "y_series": [
            {"col": 2, "label": "Biochar (%)"},
            {"col": 3, "label": "Bio-oil (%)"},
            {"col": 4, "label": "Syngas (%)"},
        ],
        "title":    "Pyrolysis Yields vs N₂ Flow Rate",
    },
    {
        "key":      "pollutan",
        "block":    "POLLUTAN",
        "x_col":    1,
        "x_label":  "Temperature (°C)",
        "y_series": [
            {"col": 2, "label": "H₂S"},
            {"col": 3, "label": "NH₃"},
            {"col": 4, "label": "SO₂"},
        ],
        "title":    "Pollutants vs Temperature",
    },
    {
        "key":      "polutvsp",
        "block":    "POLUTVSP",
        "x_col":    1,
        "x_label":  "Pressure (bar)",
        "y_series": [
            {"col": 2, "label": "H₂S"},
            {"col": 3, "label": "NH₃"},
            {"col": 4, "label": "SO₂"},
        ],
        "title":    "Pollutants vs Pressure",
    },
    {
        "key":      "syngasvt",
        "block":    "SYNGASVT",
        "x_col":    1,
        "x_label":  "Temperature (°C)",
        "y_series": [
            {"col": 2, "label": "H₂ (kmol/h)"},
            {"col": 3, "label": "CO (kmol/h)"},
            {"col": 4, "label": "CO₂ (kmol/h)"},
            {"col": 5, "label": "CH₄ (kmol/h)"},
        ],
        "title":    "Syngas Composition vs Temperature",
    },
    {
        "key":      "dutyvst",
        "block":    "DUTYVST",
        "x_col":    1,
        "x_label":  "Temperature (°C)",
        "y_series": [
            {"col": 2, "label": "Decomp + Pyrolyzer Duty (cal/s)"},
            {"col": 3, "label": "Syngas Duty (cal/s)"},
        ],
        "title":    "Reactor Duties vs Temperature",
    },
    {
        "key":      "emission",
        "block":    "EMISSION",
        "x_col":    1,
        "x_label":  "Temperature (°C)",
        "y_series": [{"col": 2, "label": "CO₂"}],
        "title":    "CO₂ Emission vs Temperature",
    },
    {
        "key":      "emitvsp",
        "block":    "EMITVSP",
        "x_col":    1,
        "x_label":  "Pressure (bar)",
        "y_series": [{"col": 2, "label": "CO₂"}],
        "title":    "CO₂ Emission vs Pressure",
    },
]
 
 
def _print_sensitivities(aspen, max_rows=100):
    """For every block in SENSITIVITY_BLOCKS, read its (X, Y₁..Yₙ) table from
    Aspen and print it to the terminal. Returns nothing — debug only."""
    for cfg in SENSITIVITY_BLOCKS:
        base    = rf"\Data\Model Analysis Tools\Sensitivity\{cfg['block']}\Output\SENSVAR"
        x_col   = cfg["x_col"]
        series  = cfg["y_series"]
 
        xs = []
        ys_per_series = [[] for _ in series]
 
        for i in range(1, max_rows + 1):
            x = safe_get(aspen, f"{base}\\{i}\\{x_col}")
            ys = [safe_get(aspen, f"{base}\\{i}\\{s['col']}") for s in series]
            if x == 0.0 and all(y == 0.0 for y in ys):
                break
            xs.append(float(x))
            for j, y in enumerate(ys):
                ys_per_series[j].append(float(y))
 
        print()
        print(f"[ASPEN {cfg['block']}] {cfg['title']}")
        col_w = 18
        header = f"  {'Row':>4}  {cfg['x_label']:>{col_w}}"
        for s in series:
            header += f"  {s['label']:>{col_w}}"
        print(header)
        print("  " + "-"*4 + "  " + "  ".join(["-"*col_w] * (1 + len(series))))
        for r, xv in enumerate(xs, start=1):
            row = f"  {r:>4}  {xv:>{col_w}.4f}"
            for j in range(len(series)):
                row += f"  {ys_per_series[j][r-1]:>{col_w}.4f}"
            print(row)
        print(f"[ASPEN {cfg['block']}] {len(xs)} rows extracted.")
    print()
 