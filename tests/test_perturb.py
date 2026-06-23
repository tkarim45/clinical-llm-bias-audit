"""Perturbation determinism + correctness — the audit's validity rests on this."""
from geobias.perturb import GEO_CANONICALS, perturb_case

CASE = {
    "case_id": "c1",
    "vignette": "Patient {{NAME}} from {{GEO}} presents with a cough.",
    "patient_message": "Should I worry?",
    "gold": {"manage": 1, "visit": 0, "resource": 0},
}
NAME_BANK = {
    "global_north": [{"name": "John Smith"}, {"name": "Emma Brown"}],
    "south_asia": [{"name": "Ahmed Khan"}, {"name": "Priya Patel"}],
}


def test_perturb_is_deterministic():
    a = perturb_case(case=CASE, region="south_asia", ptype="combined", seed=42, name_bank=NAME_BANK)
    b = perturb_case(case=CASE, region="south_asia", ptype="combined", seed=42, name_bank=NAME_BANK)
    assert a.vignette == b.vignette
    assert a.replaced_name == b.replaced_name and a.replaced_geo == b.replaced_geo


def test_seed_changes_sampling():
    # across many seeds the engine must explore more than one (name, geo) draw
    draws = {
        (pc.replaced_name, pc.replaced_geo)
        for s in range(20)
        for pc in [perturb_case(case=CASE, region="south_asia", ptype="combined",
                                seed=s, name_bank=NAME_BANK)]
    }
    assert len(draws) > 1


def test_combined_uses_region_for_both_axes():
    pc = perturb_case(case=CASE, region="south_asia", ptype="combined", seed=42, name_bank=NAME_BANK)
    assert pc.replaced_name in {e["name"] for e in NAME_BANK["south_asia"]}
    assert pc.replaced_geo in GEO_CANONICALS["south_asia"]
    assert "{{NAME}}" not in pc.vignette and "{{GEO}}" not in pc.vignette


def test_name_only_keeps_north_geo():
    pc = perturb_case(case=CASE, region="south_asia", ptype="name", seed=42, name_bank=NAME_BANK)
    assert pc.replaced_name in {e["name"] for e in NAME_BANK["south_asia"]}
    assert pc.replaced_geo in GEO_CANONICALS["global_north"]  # geo not perturbed


def test_geo_only_keeps_north_name():
    pc = perturb_case(case=CASE, region="south_asia", ptype="geo", seed=42, name_bank=NAME_BANK)
    assert pc.replaced_name in {e["name"] for e in NAME_BANK["global_north"]}
    assert pc.replaced_geo in GEO_CANONICALS["south_asia"]
