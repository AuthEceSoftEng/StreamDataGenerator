#!/usr/bin/env python3
"""
Plot session_time before and after the sudden drift from the onlineretail example.

This script reproduces the experiment suggested by the reviewer: it generates a
stream from ``examples_nl_descriptions/onlineretail.sdg`` (Figure 6 of the paper),
applies the sudden drift on ``session_time`` at a specified instance, and produces
a two-panel figure showing the distribution shift.

Usage:
    python scripts/plot_session_time_drift.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Generate the Python class from the DSL file (self-contained — no /tmp dep)
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DSL_FILE = os.path.join(REPO_ROOT, "examples_nl_descriptions", "onlineretail.sdg")

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
CustomerActivityStream = namespace["CustomerActivityStream"]

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
SEED = 42
TOTAL_INSTANCES = 2000
DRIFT_POINT = 1000  # Apply drift at instance 1000

# ---------------------------------------------------------------------------
# Generate stream data
# ---------------------------------------------------------------------------
gen = CustomerActivityStream(seed=SEED)

session_times = []
indices = []

for i, (X, y) in enumerate(gen.get_n_instances(TOTAL_INSTANCES)):
    if i == DRIFT_POINT:
        print(f"Applying sudden drift on session_time at instance {i}")
        gen.add_drift("session_time")
    session_times.append(X[1])  # session_time is the second feature (index 1)
    indices.append(i)

session_times = np.array(session_times)
indices = np.array(indices)

# ---------------------------------------------------------------------------
# Create the plot
# ---------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [2, 1]})
fig.subplots_adjust(hspace=0.30)

# Top panel: scatter plot of session_time over instance index
ax1.scatter(indices, session_times, s=2, alpha=0.5, c="steelblue", label="session_time")
ax1.axvline(x=DRIFT_POINT, color="red", linestyle="--", linewidth=2,
            label=f"Drift applied at instance {DRIFT_POINT}")
ax1.set_ylabel("session_time (minutes)", fontsize=12)
ax1.set_title("session_time before and after sudden drift\n"
              "(Gaussian(20,8) -> Gaussian(35,10))", fontsize=16, fontweight="bold")
ax1.tick_params(axis="x", labelbottom=False)
ax1.grid(True, alpha=0.3)

# Shaded regions for pre/post drift
ax1.axvspan(0, DRIFT_POINT, alpha=0.08, color="green", label="Pre-drift: N(20, 8)")
ax1.axvspan(DRIFT_POINT, TOTAL_INSTANCES, alpha=0.08, color="orange", label="Post-drift: N(35, 10)")
ax1.legend(fontsize=14, loc="lower right", framealpha=0.8)

# Bottom panel: rolling mean (window=50)
rolling_mean = pd.Series(session_times).rolling(window=50, min_periods=1).mean()
ax2.plot(indices, rolling_mean, color="darkred", linewidth=2,
         label="Rolling mean (window=50)")
ax2.axvline(x=DRIFT_POINT, color="red", linestyle="--", linewidth=2)
ax2.set_xlabel("Instance index", fontsize=13)
ax2.set_ylabel("Rolling mean of session_time", fontsize=12)
ax2.legend(fontsize=14, loc="lower right", framealpha=0.8)
ax2.tick_params(axis="x", labelsize=12)
ax2.grid(True, alpha=0.3)

# Statistics annotation
pre_drift = session_times[:DRIFT_POINT]
post_drift = session_times[DRIFT_POINT:]
stats_text = (
    f"Pre-drift:  mean={pre_drift.mean():.2f},  std={pre_drift.std():.2f}\n"
    f"Post-drift: mean={post_drift.mean():.2f},  std={post_drift.std():.2f}"
)
ax2.text(0.02, 0.95, stats_text, transform=ax2.transAxes, fontsize=10,
         verticalalignment="top",
         bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

plt.tight_layout()

# ---------------------------------------------------------------------------
# Save the figure
# ---------------------------------------------------------------------------
output_dir = os.path.join(REPO_ROOT, "figures")
os.makedirs(output_dir, exist_ok=True)

pdf_path = os.path.join(output_dir, "retail_example.pdf")
png_path = os.path.join(output_dir, "retail_example.png")

plt.savefig(pdf_path, dpi=150, bbox_inches="tight")
plt.savefig(png_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to: {pdf_path}")
print(f"Plot saved to: {png_path}")

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
print(f"\n=== Summary Statistics ===")
print(f"Pre-drift  (instances 0-{DRIFT_POINT-1}): "
      f"mean={pre_drift.mean():.2f}, std={pre_drift.std():.2f}")
print(f"Post-drift (instances {DRIFT_POINT}-{TOTAL_INSTANCES-1}): "
      f"mean={post_drift.mean():.2f}, std={post_drift.std():.2f}")
print(f"Expected pre-drift:  N(20, 8)  -> mean~20,  std~8")
print(f"Expected post-drift: N(35, 10) -> mean~35,  std~10")
