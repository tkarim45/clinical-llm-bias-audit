FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[api]"

COPY api ./api
COPY configs ./configs
COPY datasets ./datasets
COPY examples ./examples

ENV RUN_DIR=examples/sample_run
EXPOSE 8000
# Serves /summary over the shipped sample run with no credentials;
# POST /audit needs OPENAI_API_KEY and/or AWS_* mounted at runtime.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
