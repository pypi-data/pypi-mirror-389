# Developing VBL Aquarium

[GitHub Actions](https://github.com/VirtualBrainLab/vbl-aquarium/actions/workflows/build-models.yml)
are used to automatically build models to the `models` directory.
To update the models, simply push changes to the underlying pydantic models in
the `vbl_aquarium/models` directory.

## Local Development Setup

1. Install [Hatch](https://hatch.pypa.io/latest/)
2. Clone the repository
3. Run `hatch shell` in the repository root directory

Use

```bash
python src/vbl_aquarium/build.py
```

to build the models locally.

Use

```bash
hatch run check
```

to run pyright type checking.
