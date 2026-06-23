"""FastAPI service for the clinical-LLM bias audit.

  GET  /summary?run_dir=...   leaderboard from an existing run (default: the shipped
                              sample run — works with no credentials)
  POST /audit                 run a live audit from a config and return the GDI summary
                              (needs provider creds: OPENAI_API_KEY and/or AWS_* for Bedrock)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ALPHA = 0.005  # pre-registered Bonferroni-corrected family-wise significance
DEFAULT_RUN = os.getenv("RUN_DIR", "examples/sample_run")

app = FastAPI(title="Clinical LLM Bias Audit", version="0.1.0")


def _leaderboard(run_dir: str) -> list[dict]:
    path = Path(run_dir) / "summaries.json"
    if not path.exists():
        raise HTTPException(404, f"no summaries.json in {run_dir}")
    summaries = json.loads(path.read_text())
    rows = [{
        "model": s["model"],
        "gdi": round(s["gdi"], 4),
        "rcer_north": round(s["rcer_north_mean"], 4),
        "rcer_south": round(s["rcer_south_mean"], 4),
        "wilcoxon_p": round(s["wilcoxon_p_greater"], 4),
        "n_south_cases": s.get("n_south_cases"),
        "significant_disparity": s["wilcoxon_p_greater"] < ALPHA,
    } for s in summaries]
    return sorted(rows, key=lambda r: r["gdi"], reverse=True)


class AuditRequest(BaseModel):
    config: str = Field(..., description="path to a run config, e.g. configs/oncqa_bedrock.yaml")
    seed: int = 42
    limit: int = Field(2, ge=1, le=60, description="cases to audit (keep small for a live call)")
    parallelism: int = Field(4, ge=1, le=16)


@app.get("/health")
def health():
    return {"status": "ok", "default_run": DEFAULT_RUN, "alpha": ALPHA}


@app.get("/summary")
def summary(run_dir: str = DEFAULT_RUN):
    return {"run_dir": run_dir, "alpha": ALPHA, "leaderboard": _leaderboard(run_dir)}


@app.post("/audit")
def audit(req: AuditRequest):
    if not Path(req.config).exists():
        raise HTTPException(400, f"config not found: {req.config}")

    from geobias.run import main as run_main

    before = set(Path("runs").glob("*")) if Path("runs").exists() else set()
    rc = run_main(["--config", req.config, "--seed", str(req.seed),
                   "--limit", str(req.limit), "--parallelism", str(req.parallelism)])
    if rc != 0:
        raise HTTPException(500, "audit run failed")

    after = set(Path("runs").glob("*"))
    new = sorted(after - before, key=lambda p: p.name)
    run_dir = str(new[-1]) if new else max(after, key=lambda p: p.name)
    return {"run_dir": run_dir, "alpha": ALPHA, "leaderboard": _leaderboard(run_dir)}
