"""Build all VBL Aquarium models.

Searches for models that subclass VBLBaseModel in the `vbl_aquarium.models` subpackage and
generates JSON schemas to the `models/schemas` directory and C# structs to the `models/csharp` directory.
JSON schemas are separated to one model per file under the `models/schemas/{module_name}` directory.
C# structs for each model are bundled together under `models/csharp/{module_name}Models.cs`.

Usage:

    python src/vbl_aquarium/build.py
"""

from importlib import import_module
from json import dumps
from os import makedirs
from os.path import abspath, dirname, exists, join
from pkgutil import iter_modules

from pydantic.alias_generators import to_pascal

from vbl_aquarium.utils.common import get_model_classes
from vbl_aquarium.utils.generate_csharp import generate_csharp

# Directories.
PACKAGE_DIRECTORY = dirname(abspath(__file__))
MODELS_DIRECTORY = join(PACKAGE_DIRECTORY, "models")
BUILT_MODELS_DIRECTORY = join(dirname(dirname(PACKAGE_DIRECTORY)), "models")
SCHEMA_DIRECTORY = join(BUILT_MODELS_DIRECTORY, "schemas")
CSHARP_DIRECTORY = join(BUILT_MODELS_DIRECTORY, "csharp")

# Ensure built directories exist.
for directory in [SCHEMA_DIRECTORY, CSHARP_DIRECTORY]:
    if not exists(directory):
        makedirs(directory)

# Look for all modules under the models subpackage.
for module in iter_modules([MODELS_DIRECTORY]):
    # Skip Unity module since it's already built into Unity.
    if module.name == "unity":
        continue

    # Collect classes.
    imported_module = import_module(f"vbl_aquarium.models.{module.name}")
    module_classes = get_model_classes(imported_module)

    # Generate JSON schemas.

    # Create a directory for the module.
    module_schema_directory = join(SCHEMA_DIRECTORY, module.name)
    if not exists(module_schema_directory):
        makedirs(module_schema_directory)

    # Write JSON schemas for each class.
    for model in module_classes:
        with open(join(module_schema_directory, f"{model.__name__}.json"), "w") as schema_file:
            _ = schema_file.write(dumps(model.model_json_schema()))

    # Generate C# structs.
    with open(join(CSHARP_DIRECTORY, f"{to_pascal(module.name)}Models.cs"), "w") as csharp_file:
        _ = csharp_file.write(generate_csharp(module_classes))
