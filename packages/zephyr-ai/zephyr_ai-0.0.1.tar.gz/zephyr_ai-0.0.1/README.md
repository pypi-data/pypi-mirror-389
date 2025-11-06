# Zephyr AI

`zephyr-ai` is the distribution name reserved for the Zephyr orchestration toolkit. Installing it will expose the `zephyr` Python package and the `zephyr` CLI stub.

## Quick start

```bash
pip install zephyr-ai
zephyr --version
python -c "import zephyr; print(zephyr.__version__)"
```

## Project layout

```text
zephyr-ai/
├─ pyproject.toml
└─ src/
   └─ zephyr/
      ├─ __init__.py
      └─ cli.py
```

This repository currently ships placeholder implementations so we can secure the package namespace on PyPI. Extend the modules in `src/zephyr/` as functionality evolves.
