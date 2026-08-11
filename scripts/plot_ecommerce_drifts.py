#!/usr/bin/env python3
"""
Plot all four drift types from ecommerce_activity.sdg in a single unified
stream.  One generator instance produces the entire stream; drifts are
activated sequentially at different points so the reader can see how each
type manifests within the same data stream.

Panels (one per affected variable):
    1. session_time  — sudden drift   (instance 1000)
    2. response_time — incremental    (instance 1500)
                       + recurring    (instance 2500, periodic)
    3. purchase      — gradual drift  (instance 3500)

Usage:
    conda activate datagenerator
    python scripts/plot_ecommerce_drifts.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Generate the Python class from the DSL file (self-contained)
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DSL_FILE = os.path.join(REPO_ROOT, "examples", "ecommerce_activity.sdg")

# Import the SDG code generation pipeline
sys.path.insert(0, REPO_ROOT)
from sdg.lang import parse_file
from sdg.utils.model_converter import convert_model_to_dict
from sdg.generator.codegenerator import generate

model = parse_file(DSL_FILE)
dataset_dict = convert_model_to_dict(model)
code = generate(dataset_dict)

# Execute the generated code in a local namespace to obtain the class
namespace = {}
exec(code, namespace)
ECommerceAnalyticsGenerator = namespace["ECommerceAnalyticsGenerator"]

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
SEED = 42
TOTAL_INSTANCES = 5000

# Drift activation points — spread across the stream so each type is visible
SUDDEN_DRIFT_POINT = 1000
INCREMENTAL_DRIFT_POINT = [1500, 3000]
RECURRING_DRIFT_POINT = 1100
GRADUAL_DRIFT_POINT = 3500

TRANSITION_STEPS = 200          # For incremental and gradual drifts
RECURRING_INTERVAL = 500        # Instances between recurring activations
RECURRING_DURATION = 150        # Instances each recurring activation lasts

ROLLING_WINDOW = 80

# Feature indices (order from the DSL: age=0, session_time=1,
# browsing_depth=2, response_time=3, device_type=4)
SESSION_TIME_IDX = 1
RESPONSE_TIME_IDX = 3

# ---------------------------------------------------------------------------
# Generate a single unified stream
# ---------------------------------------------------------------------------
print("Generating unified e-commerce stream ...")
gen = ECommerceAnalyticsGenerator(seed=SEED)

session_time_values = []
response_time_values = []
purchase_values = []

# Pre-compute recurring windows for plot annotations
recurring_activation_points = []
t = RECURRING_DRIFT_POINT
while t < TOTAL_INSTANCES:
    recurring_activation_points.append(t)
    t += RECURRING_INTERVAL

for i, (X, y) in enumerate(gen.get_n_instances(TOTAL_INSTANCES)):
    # -- Activate sudden drift on session_time --
    if i == SUDDEN_DRIFT_POINT:
        print(f"  [instance {i}] activating SUDDEN drift on session_time")
        gen.add_drift("session_time", "sudden")

    # -- Activate incremental drift on response_time --
    if i == INCREMENTAL_DRIFT_POINT[0]:
        print(f"  [instance {i}] activating INCREMENTAL drift on response_time → formula 1")
        gen.add_drift("response_time", "incremental", scenario_idx=1,
                      transition_steps=TRANSITION_STEPS)
    elif i == INCREMENTAL_DRIFT_POINT[1]:
        print(f"  [instance {i}] REVERTING incremental drift on response_time → formula 0")
        gen.add_drift("response_time", "incremental", scenario_idx=0,
                      transition_steps=TRANSITION_STEPS)

    # -- Activate recurring drift on response_time (auto-cycles from here) --
    if i == RECURRING_DRIFT_POINT:
        print(f"  [instance {i}] activating RECURRING drift on response_time "
              f"(interval={RECURRING_INTERVAL}, duration={RECURRING_DURATION})")
        gen.add_drift("response_time", "recurring", 2,  # scenario index for recurring drift
                      interval=RECURRING_INTERVAL,
                      duration=RECURRING_DURATION,)

    # -- Activate gradual drift on purchase (target) --
    if i == GRADUAL_DRIFT_POINT:
        print(f"  [instance {i}] activating GRADUAL drift on purchase")
        gen.add_drift("purchase", "gradual",
                      transition_steps=TRANSITION_STEPS)

    session_time_values.append(X[SESSION_TIME_IDX])
    response_time_values.append(X[RESPONSE_TIME_IDX])
    purchase_values.append(y)

session_time_values = np.array(session_time_values)
response_time_values = np.array(response_time_values)
purchase_values = np.array(purchase_values)

print(f"Stream generated: {TOTAL_INSTANCES} instances\n")

# ---------------------------------------------------------------------------
# Build the 3x1 figure
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(3, 1, figsize=(14, 18), sharex=False)
fig.subplots_adjust(hspace=0.55)

# -- Panel 1: session_time — sudden drift --
ax1 = axes[0]
ax1.scatter(range(TOTAL_INSTANCES), session_time_values, s=2, alpha=0.12,
            c="steelblue", label="session_time (raw)")
rolling_st = pd.Series(session_time_values).rolling(
    window=ROLLING_WINDOW, min_periods=1).mean()
ax1.plot(range(TOTAL_INSTANCES), rolling_st, color="darkred", linewidth=2,
         label=f"Rolling mean (w={ROLLING_WINDOW})")
ax1.axvline(x=SUDDEN_DRIFT_POINT, color="red", linestyle="--", linewidth=1.5,
            label=f"Sudden drift @ {SUDDEN_DRIFT_POINT}")
ax1.axhline(y=20, color="green", linestyle=":", linewidth=1, alpha=0.7,
            label="Pre-drift mean (mu=20)")
ax1.axhline(y=35, color="orange", linestyle=":", linewidth=1, alpha=0.7,
            label="Post-drift mean (mu=35)")
ax1.set_ylabel("session_time (min)", fontsize=12)
ax1.set_title("Sudden Drift - session_time\n"
              "N(20, 8)  ->  N(35, 10)  .  platform redesign",
              fontsize=14, fontweight="bold")
ax1.legend(fontsize=14, loc="lower right", ncol=2, framealpha=0.8)
ax1.tick_params(axis="x", labelsize=12)
ax1.grid(True, alpha=0.3)

# -- Panel 2: response_time — incremental + recurring --
ax2 = axes[1]
ax2.scatter(range(TOTAL_INSTANCES), response_time_values, s=2, alpha=0.12,
            c="seagreen", label="response_time (raw)")
rolling_rt = pd.Series(response_time_values).rolling(
    window=ROLLING_WINDOW, min_periods=1).mean()
ax2.plot(range(TOTAL_INSTANCES), rolling_rt, color="darkred", linewidth=2,
         label=f"Rolling mean (w={ROLLING_WINDOW})")
for j, pt in enumerate(INCREMENTAL_DRIFT_POINT):
    ax2.axvline(x=pt, color="blue", linestyle="--", linewidth=1.5,
                label="Incremental drift" if j == 0 else None)
for j, pt in enumerate(recurring_activation_points):
    ax2.axvspan(pt, pt + RECURRING_DURATION, alpha=0.10, color="red",
                zorder=0)
    ax2.axvline(x=pt, color="red", linestyle="-", linewidth=1.5, alpha=0.8,
                label="Recurring drift start" if j == 0 else None)
    ax2.axvline(x=pt + RECURRING_DURATION, color="darkred", linestyle="--",
                linewidth=1.5, alpha=0.8,
                label="Recurring drift end" if j == 0 else None)
ax2.axvspan(0, 0, alpha=0.10, color="red", label="Recurring active window")
ax2.axhline(y=2.0, color="green", linestyle=":", linewidth=1, alpha=0.7,
            label="Baseline mu=2.0")
ax2.axhline(y=4.5, color="blue", linestyle=":", linewidth=1, alpha=0.5,
            label="Post-incremental mu=4.5")
ax2.axhline(y=6.0, color="orange", linestyle=":", linewidth=1, alpha=0.7,
            label="Recurring spike mu=6.0")
ax2.set_ylabel("response_time (s)", fontsize=12)
ax2.set_title("Incremental + Recurring Drift - response_time\n"
              "mu: 2.0 -> 4.5 (incremental)  .  periodic spikes to 6.0 "
              "(recurring)  .  server load / holiday surge",
              fontsize=14, fontweight="bold")
ax2.legend(fontsize=14, loc="lower right", ncol=2, framealpha=0.8)
ax2.tick_params(axis="x", labelsize=12)
ax2.grid(True, alpha=0.3)

# -- Panel 3: purchase — gradual drift (binary target) --
ax3 = axes[2]
ax3.scatter(range(TOTAL_INSTANCES), purchase_values, s=2, alpha=0.15,
            c="purple", label="purchase (raw)")
rolling_pv = pd.Series(purchase_values).rolling(
    window=ROLLING_WINDOW, min_periods=1).mean()
ax3.plot(range(TOTAL_INSTANCES), rolling_pv, color="darkred", linewidth=2,
         label=f"Rolling purchase rate (w={ROLLING_WINDOW})")
ax3.axvline(x=GRADUAL_DRIFT_POINT, color="green", linestyle="--",
            linewidth=1.5,
            label=f"Gradual drift @ {GRADUAL_DRIFT_POINT}")
ax3.axhline(y=0.459, color="green", linestyle=":", linewidth=1, alpha=0.7,
            label="Pre-drift purchase rate (~46%)")
ax3.axhline(y=0.160, color="orange", linestyle=":", linewidth=1, alpha=0.7,
            label="Post-drift purchase rate (~16%)")
ax3.set_xlabel("Instance", fontsize=13)
ax3.set_ylabel("purchase (0/1)", fontsize=12)
ax3.set_title("Gradual Drift - purchase (target)\n"
              "session_time>15 & age<60  ->  session_time>25 & age<55  "
              ".  seasonal tightening",
              fontsize=14, fontweight="bold")
ax3.set_yticks([0, 1])
ax3.legend(fontsize=14, loc="lower right", ncol=2, framealpha=0.8)
ax3.tick_params(axis="x", labelsize=12)
ax3.grid(True, alpha=0.3)

# ---------------------------------------------------------------------------
# Save figure
# ---------------------------------------------------------------------------
output_dir = os.path.join(REPO_ROOT, "..", "SoftwareXSDG", "figures")
os.makedirs(output_dir, exist_ok=True)

pdf_path = os.path.join(output_dir, "ecommerce_drifts.pdf")
png_path = os.path.join(output_dir, "ecommerce_drifts.png")

plt.tight_layout()
plt.savefig(png_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to: {png_path}")
try:
    plt.savefig(pdf_path, dpi=150, bbox_inches="tight")
    print(f"Plot saved to: {pdf_path}")
except Exception as e:
    print(f"\n(PDF save skipped: {e})")
plt.close(fig)

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f" Summary Statistics  (single unified stream, {TOTAL_INSTANCES} instances)")
print(f"{'='*60}")

pre_st = session_time_values[:SUDDEN_DRIFT_POINT]
post_st = session_time_values[SUDDEN_DRIFT_POINT + TRANSITION_STEPS:]
print(f"\nsession_time (sudden drift @ {SUDDEN_DRIFT_POINT}):")
print(f"  Pre-drift  (0-{SUDDEN_DRIFT_POINT-1}): "
      f"mean={pre_st.mean():.2f}, std={pre_st.std():.2f}")
print(f"  Post-drift ({SUDDEN_DRIFT_POINT+TRANSITION_STEPS}-{TOTAL_INSTANCES-1}): "
      f"mean={post_st.mean():.2f}, std={post_st.std():.2f}")

pre_rt = response_time_values[:INCREMENTAL_DRIFT_POINT[0]]
mid_rt = response_time_values[INCREMENTAL_DRIFT_POINT[0] + TRANSITION_STEPS:
                              INCREMENTAL_DRIFT_POINT[1]]
post_rt = response_time_values[INCREMENTAL_DRIFT_POINT[1] + TRANSITION_STEPS:]
print(f"\nresponse_time:")
print(f"  Pre-incremental (0-{INCREMENTAL_DRIFT_POINT[0]-1}): "
      f"mean={pre_rt.mean():.2f}")
print(f"  Post-formula-1 ({INCREMENTAL_DRIFT_POINT[0]+TRANSITION_STEPS}-"
      f"{INCREMENTAL_DRIFT_POINT[1]-1}): mean={mid_rt.mean():.2f}")
print(f"  Post-formula-0 ({INCREMENTAL_DRIFT_POINT[1]+TRANSITION_STEPS}-"
      f"{TOTAL_INSTANCES-1}): mean={post_rt.mean():.2f}")

pre_pv = purchase_values[:GRADUAL_DRIFT_POINT]
post_pv = purchase_values[GRADUAL_DRIFT_POINT + TRANSITION_STEPS:]
print(f"\npurchase (gradual drift @ {GRADUAL_DRIFT_POINT}):")
print(f"  Pre-drift  (0-{GRADUAL_DRIFT_POINT-1}): "
      f"positive rate={pre_pv.mean():.3f}")
print(f"  Post-drift ({GRADUAL_DRIFT_POINT+TRANSITION_STEPS}-{TOTAL_INSTANCES-1}): "
      f"positive rate={post_pv.mean():.3f}")

print(f"\n{'='*60}")
