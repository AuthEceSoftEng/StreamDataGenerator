#!/usr/bin/env python3
"""
Plot gradual, incremental, and recurring drift types from the drift_types_demo
example.

This script generates a three-panel figure demonstrating all three non-sudden
drift types supported by the SDG DSL.  Each panel shows the raw stream values
as a semi-transparent scatter plot with a rolling-mean overlay, plus reference
and drift-activation lines.

Usage:
    python scripts/plot_drift_types_demo.py
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
DSL_FILE = os.path.join(REPO_ROOT, "examples", "drift_types_demo.sdg")

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
DriftTypesDemo = namespace["DriftTypesDemo"]

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
SEED = 42
TRANSITION_STEPS = 100        # Default gradual / incremental transition
RECURRING_INTERVAL = 500      # Instances between recurring-drift activations
RECURRING_DURATION = 200      # Instances each recurring activation lasts

# Panel-specific instance counts
GRADUAL_INSTANCES = 2000
INCREMENTAL_INSTANCES = 2000
RECURRING_INSTANCES = 3000

# Drift activation points
GRADUAL_DRIFT_POINT = 500
INCREMENTAL_DRIFT_POINT = 500
RECURRING_DRIFT_POINT = 200

ROLLING_WINDOW = 50

# ---------------------------------------------------------------------------
# Panel 1 — Gradual drift on sensor_a
# ---------------------------------------------------------------------------
print("Generating stream data for gradual drift (sensor_a)...")
gen_gradual = DriftTypesDemo(seed=SEED)

sensor_a_values = []
for i, (X, y) in enumerate(gen_gradual.get_n_instances(GRADUAL_INSTANCES)):
    if i == GRADUAL_DRIFT_POINT:
        gen_gradual.add_drift("sensor_a", "gradual",
                              transition_steps=TRANSITION_STEPS)
    sensor_a_values.append(X[0])  # sensor_a is the first feature

sensor_a_values = np.array(sensor_a_values)

# ---------------------------------------------------------------------------
# Panel 2 — Incremental drift on sensor_b
# ---------------------------------------------------------------------------
print("Generating stream data for incremental drift (sensor_b)...")
gen_incremental = DriftTypesDemo(seed=SEED)

sensor_b_values = []
for i, (X, y) in enumerate(gen_incremental.get_n_instances(INCREMENTAL_INSTANCES)):
    if i == INCREMENTAL_DRIFT_POINT:
        gen_incremental.add_drift("sensor_b", "incremental",
                                  transition_steps=TRANSITION_STEPS)
    sensor_b_values.append(X[1])  # sensor_b is the second feature

sensor_b_values = np.array(sensor_b_values)

# ---------------------------------------------------------------------------
# Panel 3 — Recurring drift on status (binary target)
# ---------------------------------------------------------------------------
print("Generating stream data for recurring drift (status)...")
gen_recurring = DriftTypesDemo(seed=SEED)

status_values = []
recurring_activation_points = []
recurring_active = False
next_activation = RECURRING_DRIFT_POINT
next_deactivation = RECURRING_DRIFT_POINT + RECURRING_DURATION
for i, (X, y) in enumerate(gen_recurring.get_n_instances(RECURRING_INSTANCES)):
    # Activate recurring drift at the configured point
    if i == next_activation and not recurring_active:
        gen_recurring.add_drift(
            "status", "recurring",
            interval=RECURRING_INTERVAL,
            duration=RECURRING_DURATION,
        )
        recurring_activation_points.append(i)
        recurring_active = True
    # Deactivate and schedule next activation
    if recurring_active and i == next_deactivation:
        recurring_active = False
        next_activation = i + (RECURRING_INTERVAL - RECURRING_DURATION)
        next_deactivation = next_activation + RECURRING_DURATION
    status_values.append(y)

status_values = np.array(status_values)

# ---------------------------------------------------------------------------
# Create the 3×1 figure
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(3, 1, figsize=(12, 14), sharex=False)
fig.subplots_adjust(hspace=0.60)

# ── Panel 1: sensor_a — gradual drift ──────────────────────────────────────
ax1 = axes[0]
ax1.scatter(range(GRADUAL_INSTANCES), sensor_a_values, s=3, alpha=0.15,
            c="steelblue", label="sensor_a (raw)")
rolling_a = pd.Series(sensor_a_values).rolling(window=ROLLING_WINDOW,
                                                min_periods=1).mean()
ax1.plot(range(GRADUAL_INSTANCES), rolling_a, color="darkred", linewidth=2,
         label=f"Rolling mean (w={ROLLING_WINDOW})")
ax1.axvline(x=GRADUAL_DRIFT_POINT, color="red", linestyle="--", linewidth=1.5,
            label=f"Drift activated at {GRADUAL_DRIFT_POINT}")
# Reference lines
ax1.axhline(y=50, color="green", linestyle=":", linewidth=1, alpha=0.7,
            label="Pre-drift mean (50)")
ax1.axhline(y=70, color="orange", linestyle=":", linewidth=1, alpha=0.7,
            label="Post-drift mean (70)")
ax1.set_ylabel("sensor_a", fontsize=12)
ax1.set_title("Gradual Drift — sensor_a\n"
              "N(50, 5)  →  N(70, 5)  "
              f"(transition over {TRANSITION_STEPS} steps)",
              fontsize=14, fontweight="bold")
ax1.legend(fontsize=14, loc="upper left")
ax1.tick_params(axis="x", labelbottom=False)
ax1.grid(True, alpha=0.3)

# ── Panel 2: sensor_b — incremental drift ──────────────────────────────────
ax2 = axes[1]
ax2.scatter(range(INCREMENTAL_INSTANCES), sensor_b_values, s=3, alpha=0.15,
            c="darkorange", label="sensor_b (raw)")
rolling_b = pd.Series(sensor_b_values).rolling(window=ROLLING_WINDOW,
                                                min_periods=1).mean()
ax2.plot(range(INCREMENTAL_INSTANCES), rolling_b, color="darkred", linewidth=2,
         label=f"Rolling mean (w={ROLLING_WINDOW})")
ax2.axvline(x=INCREMENTAL_DRIFT_POINT, color="red", linestyle="--",
            linewidth=1.5,
            label=f"Drift activated at {INCREMENTAL_DRIFT_POINT}")
ax2.axhline(y=30, color="green", linestyle=":", linewidth=1, alpha=0.7,
            label="Pre-drift mean (30)")
ax2.axhline(y=50, color="orange", linestyle=":", linewidth=1, alpha=0.7,
            label="Post-drift mean (50)")
ax2.set_ylabel("sensor_b", fontsize=12)
ax2.set_title("Incremental Drift — sensor_b\n"
              "μ: 30  →  50  "
              f"(linear interpolation over {TRANSITION_STEPS} steps)",
              fontsize=14, fontweight="bold")
ax2.legend(fontsize=14, loc="upper left")
ax2.tick_params(axis="x", labelbottom=False)
ax2.grid(True, alpha=0.3)

# ── Panel 3: status — recurring drift ──────────────────────────────────────
ax3 = axes[2]
# Plot binary target as a scatter
ax3.scatter(range(RECURRING_INSTANCES), status_values, s=3, alpha=0.2,
            c="purple", label="status (binary)")
# Rolling proportion of positive class as an overlay
rolling_s = pd.Series(status_values).rolling(window=ROLLING_WINDOW,
                                              min_periods=1).mean()
ax3.plot(range(RECURRING_INSTANCES), rolling_s, color="darkred", linewidth=2,
         label=f"Rolling mean (w={ROLLING_WINDOW})")
# Mark recurring drift activation points
for j, pt in enumerate(recurring_activation_points):
    ax3.axvspan(pt, pt + RECURRING_DURATION, alpha=0.10, color="red", zorder=0)
    ax3.axvline(x=pt, color="red", linestyle="-", linewidth=1.5, alpha=0.8,
                label="Drift start" if j == 0 else None)
    ax3.axvline(x=pt + RECURRING_DURATION, color="darkred", linestyle="--",
                linewidth=1.5, alpha=0.8,
                label="Drift end" if j == 0 else None)
# Faux handles for legend (span already plotted above)
ax3.axvspan(0, 0, alpha=0.10, color="red", label="Drift active window")
# Reference lines for the two classification boundaries
ax3.axhline(y=0.5, color="gray", linestyle=":", linewidth=1, alpha=0.5,
            label="Decision boundary (0.5)")
ax3.set_xlabel("Instance", fontsize=13)
ax3.set_ylabel("status (0/1)", fontsize=12)
ax3.set_title("Recurring Drift — status (binary target)\n"
              f"Boundary alternates every {RECURRING_INTERVAL} instances "
              f"(active for {RECURRING_DURATION})",
              fontsize=14, fontweight="bold")
ax3.set_yticks([0, 1])
ax3.legend(fontsize=14, loc="upper right")
ax3.tick_params(axis="x", labelsize=12)
ax3.grid(True, alpha=0.3)

# ---------------------------------------------------------------------------
# Save figure
# ---------------------------------------------------------------------------
output_dir = os.path.join(REPO_ROOT, "..", "SoftwareXSDG", "figures")
os.makedirs(output_dir, exist_ok=True)

pdf_path = os.path.join(output_dir, "drift_types_demo.pdf")
png_path = os.path.join(output_dir, "drift_types_demo.png")

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(pdf_path, dpi=150, bbox_inches="tight")
plt.savefig(png_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"\nPlot saved to: {pdf_path}")
print(f"Plot saved to: {png_path}")

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
print(f"\n=== Summary Statistics ===")
print(f"sensor_a (gradual):")
print(f"  Pre-drift  (instances 0-{GRADUAL_DRIFT_POINT-1}): "
      f"mean={sensor_a_values[:GRADUAL_DRIFT_POINT].mean():.2f}, "
      f"std={sensor_a_values[:GRADUAL_DRIFT_POINT].std():.2f}")
print(f"  Post-drift (instances {GRADUAL_DRIFT_POINT+TRANSITION_STEPS}-"
      f"{GRADUAL_INSTANCES-1}): "
      f"mean={sensor_a_values[GRADUAL_DRIFT_POINT+TRANSITION_STEPS:].mean():.2f}, "
      f"std={sensor_a_values[GRADUAL_DRIFT_POINT+TRANSITION_STEPS:].std():.2f}")

print(f"\nsensor_b (incremental):")
print(f"  Pre-drift  (instances 0-{INCREMENTAL_DRIFT_POINT-1}): "
      f"mean={sensor_b_values[:INCREMENTAL_DRIFT_POINT].mean():.2f}, "
      f"std={sensor_b_values[:INCREMENTAL_DRIFT_POINT].std():.2f}")
print(f"  Post-drift (instances {INCREMENTAL_DRIFT_POINT+TRANSITION_STEPS}-"
      f"{INCREMENTAL_INSTANCES-1}): "
      f"mean={sensor_b_values[INCREMENTAL_DRIFT_POINT+TRANSITION_STEPS:].mean():.2f}, "
      f"std={sensor_b_values[INCREMENTAL_DRIFT_POINT+TRANSITION_STEPS:].std():.2f}")

print(f"\nstatus (recurring):")
print(f"  Positive rate (instances 0-{RECURRING_DRIFT_POINT-1}): "
      f"{status_values[:RECURRING_DRIFT_POINT].mean():.3f}")
print(f"  Positive rate (overall): {status_values.mean():.3f}")
