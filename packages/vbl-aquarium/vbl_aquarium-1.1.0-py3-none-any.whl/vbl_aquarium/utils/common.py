"""Common utility functions for building VBL Aquarium models."""

from __future__ import annotations

from inspect import getmembers, isclass
from typing import TYPE_CHECKING

from pydantic import BaseModel

from vbl_aquarium.models import unity
from vbl_aquarium.utils.vbl_base_model import VBLBaseModel

if TYPE_CHECKING:
    from types import ModuleType


def get_model_classes(module: ModuleType) -> list[type[VBLBaseModel]]:
    """Get all VBL models in a module.

    Looks for all classes in a module that subclass VBLBaseModel (excluding VBLBaseModel itself).

    Args:
        module: The module to search for models in.

    Returns:
        A list of all model classes in the module.
    """
    return [
        class_type
        for _, class_type in getmembers(module, isclass)
        if issubclass(class_type, VBLBaseModel) and class_type != VBLBaseModel
    ]


def get_unity_model_class_names() -> set[str]:
    """Get the names of all Unity models.

    Looks for all classes in the unity_models module that subclass BaseModel (excluding BaseModel itself).

    Returns:
        The names of all Unity models.
    """
    return {
        model_name
        for model_name, class_object in getmembers(unity, isclass)
        if issubclass(class_object, BaseModel) and class_object != BaseModel
    }
