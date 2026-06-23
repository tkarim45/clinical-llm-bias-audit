PY  ?= ~/miniconda3/envs/personal/bin/python
PIP ?= ~/miniconda3/envs/personal/bin/pip

.PHONY: install test run audit ablation api dashboard figures docker

install:
	$(PIP) install -e ".[all]"

test:
	$(PY) -m pytest -q

# live audit (needs creds): make audit CONFIG=configs/oncqa_bedrock.yaml
audit:
	$(PY) -m geobias.cli run --config $(CONFIG) --seed 42 --parallelism 8

# NAME vs GEO vs COMBINED ablation decomposition
ablation:
	$(PY) -m geobias.cli run --config configs/pilot_name_only_bedrock.yaml --seed 42 --parallelism 8
	$(PY) -m geobias.cli run --config configs/pilot_geo_only_bedrock.yaml  --seed 42 --parallelism 8
	$(PY) -m geobias.cli run --config configs/pilot_combined_bedrock.yaml  --seed 42 --parallelism 8

api:
	$(PY) -m uvicorn api.main:app --reload --port 8000

dashboard:
	$(PY) -m streamlit run app/dashboard.py

# regenerate publication figures from a run: make figures RUN=examples/sample_run
figures:
	$(PY) scripts/make_figures.py --run-dir $(RUN) --out-dir paper/figs

docker:
	docker build -t clinical-llm-bias-audit . && docker run -p 8000:8000 clinical-llm-bias-audit
