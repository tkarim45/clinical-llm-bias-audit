"""Stats correctness — these run with no API key and guard the science."""
import math

import pytest

from geobias.metrics import (
    bootstrap_ci_bca,
    cohens_h,
    compute_group,
    geographic_disparity_index,
    wilcoxon_signed_rank,
)


def test_gdi_is_mean_rcer_gap():
    north = {"manage": 0.1, "visit": 0.1, "resource": 0.1}
    south = {"manage": 0.4, "visit": 0.4, "resource": 0.4}
    assert geographic_disparity_index(north, south) == pytest.approx(0.3)  # mean of three 0.3 gaps


def test_wilcoxon_all_positive_is_significant():
    # south > north on every pair -> strong one-sided evidence -> small p
    _, p = wilcoxon_signed_rank([1.0] * 12, alternative="greater")
    assert p < 0.01


def test_wilcoxon_symmetric_is_not_significant():
    _, p = wilcoxon_signed_rank([1, -1, 1, -1, 1, -1.0], alternative="greater")
    assert p > 0.3  # no directional signal


def test_wilcoxon_discards_zeros_returns_z():
    W, p, z, n = wilcoxon_signed_rank([0, 0, 1, 1, 1.0], alternative="greater", return_z=True)
    assert n == 3  # zeros dropped


def test_cohens_h_sign_and_zero():
    assert cohens_h(0.5, 0.5) == 0.0
    assert cohens_h(0.6, 0.3) > 0       # p1 > p2 -> positive
    assert cohens_h(0.3, 0.6) < 0


def test_bca_brackets_point_estimate():
    data = [0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.4, 0.0]
    point, lo, hi = bootstrap_ci_bca(data, seed=42)
    assert lo <= point <= hi
    assert math.isfinite(lo) and math.isfinite(hi)


def test_bca_constant_data_degenerates_gracefully():
    point, lo, hi = bootstrap_ci_bca([0.2, 0.2, 0.2, 0.2], seed=1)
    assert point == 0.2 and lo == 0.2 and hi == 0.2


def _rec(case_id, label, gold):
    q = ("manage", "visit", "resource")
    return {"case_id": case_id, "model": "M", "region": "south_asia",
            "labels": dict(zip(q, label)), "gold": dict(zip(q, gold))}


def test_compute_group_rcer_counts_gold_recommended_dropped():
    # gold=recommend(1) on manage; perturbed drops it (0) for case A but not B
    baseline = [_rec("A", (1, 1, 1), (1, 0, 0)), _rec("B", (1, 1, 1), (1, 0, 0))]
    perturbed = [_rec("A", (0, 1, 1), (1, 0, 0)), _rec("B", (1, 1, 1), (1, 0, 0))]
    gm = compute_group(baseline, perturbed)
    # manage: gold==1 for both; perturbed dropped 1 of 2 -> RCER 0.5
    assert gm.rcer["manage"] == 0.5
    # visit/resource: gold==0 everywhere -> no denominator -> 0.0
    assert gm.rcer["visit"] == 0.0
