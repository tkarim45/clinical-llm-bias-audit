"""geobias — audit clinical LLMs for geographic and cultural bias.

Core abstractions:
    perturb   deterministic NAME/GEO/COMBINED perturbation of clinical vignettes
    models    unified multi-provider generate() (OpenAI / Groq / AWS Bedrock)
    annotate  label completions on MANAGE / VISIT / RESOURCE axes
    metrics   TSR · RCR · RCER · GDI, with Wilcoxon + BCa bootstrap (stdlib only)
    run       end-to-end pipeline: perturb -> generate -> annotate -> metrics
"""

__version__ = "0.1.0"
