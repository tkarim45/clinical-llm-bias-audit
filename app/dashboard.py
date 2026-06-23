"""Streamlit dashboard for an audit run: leaderboard, GDI with CIs, per-question forest.

Loads any run directory's summaries.json (defaults to the shipped sample run, so it works
with no credentials and no prior run).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

ALPHA = 0.005
DEFAULT_RUN = "examples/sample_run"
QUESTIONS = ("manage", "visit", "resource")

st.set_page_config(page_title="Clinical LLM Bias Audit", layout="wide")
st.title("🩺 Clinical LLM Bias Audit — Geographic Disparity Index")
st.caption("Does a clinical LLM change its care recommendation when only patient "
           "geography/name is perturbed?")

run_dir = st.text_input("Run directory", DEFAULT_RUN)
sj = Path(run_dir) / "summaries.json"
if not sj.exists():
    st.error(f"No summaries.json in {run_dir}. Run `geobias run --config ...` first.")
    st.stop()

summaries = json.loads(sj.read_text())
manifest = json.loads((Path(run_dir) / "manifest.json").read_text()) if (Path(run_dir) / "manifest.json").exists() else {}

c1, c2, c3 = st.columns(3)
c1.metric("models audited", len(summaries))
c2.metric("Global-South cases / model", summaries[0].get("n_south_cases", "?") if summaries else "?")
c3.metric("pre-registered α", ALPHA)

st.subheader("Leaderboard")
rows = [{
    "model": s["model"],
    "GDI": round(s["gdi"], 4),
    "GDI 95% CI": f"[{s['gdi_ci_lo_bca']:+.3f}, {s['gdi_ci_hi_bca']:+.3f}]",
    "RCER North": f"{s['rcer_north_mean']*100:.1f}%",
    "RCER South": f"{s['rcer_south_mean']*100:.1f}%",
    "Wilcoxon p": round(s["wilcoxon_p_greater"], 4),
    "significant?": "⚠️ yes" if s["wilcoxon_p_greater"] < ALPHA else "no",
} for s in sorted(summaries, key=lambda s: s["gdi"], reverse=True)]
st.dataframe(rows, use_container_width=True, hide_index=True)

st.subheader("GDI by model (with BCa 95% CI)")
fig, ax = plt.subplots(figsize=(7, 0.6 * len(summaries) + 1))
labels = [s["model"] for s in summaries]
gdis = [s["gdi"] for s in summaries]
los = [s["gdi"] - s["gdi_ci_lo_bca"] for s in summaries]
his = [s["gdi_ci_hi_bca"] - s["gdi"] for s in summaries]
ax.barh(labels, gdis, xerr=[los, his], color="#b5651d", alpha=0.85, capsize=4)
ax.axvline(0, color="grey", lw=1)
ax.set_xlabel("GDI  (RCER_south − RCER_north;  > 0 means worse care for Global South)")
st.pyplot(fig)

st.subheader("Per-question disparity (forest)")
model = st.selectbox("model", labels)
s = next(s for s in summaries if s["model"] == model)
fig2, ax2 = plt.subplots(figsize=(7, 3))
for i, q in enumerate(QUESTIONS):
    pq = s["per_question"][q]
    lo, hi = pq.get("delta_ci_lo"), pq.get("delta_ci_hi")
    ax2.plot([lo, hi], [i, i], color="#444", lw=2)
    ax2.plot(pq["delta"], i, "o", color="#b5651d")
ax2.axvline(0, color="grey", lw=1)
ax2.set_yticks(range(len(QUESTIONS)))
ax2.set_yticklabels([q.upper() for q in QUESTIONS])
ax2.set_xlabel("RCER_south − RCER_north (per care axis)")
st.pyplot(fig2)

if manifest:
    with st.expander("Run provenance (manifest)"):
        st.json({k: manifest[k] for k in ("run_ts_utc", "seed", "perturb_mode",
                 "conditions", "cases_sha256", "name_bank_sha256") if k in manifest})
