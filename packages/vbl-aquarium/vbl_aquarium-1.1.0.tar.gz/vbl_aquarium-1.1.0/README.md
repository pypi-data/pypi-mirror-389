# Virtual Brain Lab Aquarium

![PyPI - Version](https://img.shields.io/pypi/v/vbl-aquarium)
[![Build Models](https://github.com/VirtualBrainLab/vbl-aquarium/actions/workflows/build-models.yml/badge.svg)](https://github.com/VirtualBrainLab/vbl-aquarium/actions/workflows/build-models.yml)
[![Static Analysis](https://github.com/VirtualBrainLab/vbl-aquarium/actions/workflows/static-analysis.yml/badge.svg)](https://github.com/VirtualBrainLab/vbl-aquarium/actions/workflows/static-analysis.yml)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

Collection of Pydantic models describing data objects passed between Virtual
Brain Lab projects.

Corresponding JSON schema and C# files are generated automatically and are
located in the `models` directory.

## Usage

For C# structs or JSON schemas, copy or reference whatever models you need from
the `models` directory.

To use the Pydantic models directly in Python, install the package with

```bash
pip install vbl-aquarium
```

Then import the models with

```python
from vbl_aquarium.models.module_name import ModelName
```

replacing `.module_name` and `ModelName` with the desired model.

## Further Documentation

For more information regarding updating models and each model's specification,
see the VBL
Aquarium [documentation](https://aquarium.virtualbrainlab.org).
