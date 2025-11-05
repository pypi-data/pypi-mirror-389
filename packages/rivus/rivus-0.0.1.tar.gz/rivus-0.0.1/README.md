# Rivus

Rivus is an orchestration control plane for portable runs across local and cloud backends.
This seed release exists to reserve the PyPI name and establish packaging. APIs are subject to change.

Features (roadmap):
- Deterministic packaging and execution
- Per-run artifacts, manifests, attempts, and summaries
- Backend adapters (Ray, AWS Batch), observability, and reproducibility

Quick start

```
# Build
python -m pip install --upgrade build
python -m build

# Publish to TestPyPI first
python -m pip install --upgrade twine
python -m twine upload --repository testpypi dist/*

# Verify on TestPyPI, then publish to PyPI
python -m twine upload dist/*

# Run CLI
python -m pip install rivus
rivus
```

License

Proprietary. © Your Org.

