"""Models for Unity data types.

JSON Schema and C# models are not generated for these models since they are built-in Unity types.
"""

# pyright: reportUnnecessaryIsInstance=false, reportAny=false, reportExplicitAny=false
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# Unity models don't get generated as .cs files since they exist in UnityEngine


class Color(BaseModel):
    """RGBA color.

    Range for each component is 0 to 1.

    Attributes:
        r: Red component.
        g: Green component.
        b: Blue component.
        a: Alpha component.
    """

    r: float = Field(default=1, ge=0, le=1)
    g: float = Field(default=1, ge=0, le=1)
    b: float = Field(default=1, ge=0, le=1)
    a: float = Field(default=1, ge=0, le=1)


class Vector2(BaseModel):
    """2D vector.

    Attributes:
        x: X component.
        y: Y component.
    """

    x: float = 0.0
    y: float = 0.0


class Vector3(BaseModel):
    """3D vector.

    Attributes:
        x: X component.
        y: Y component.
        z: Z component.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Vector4(BaseModel):
    """4D vector.

    Attributes:
        x: X component.
        y: Y component.
        z: Z component.
        w: W component.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0

    def __add__(self, other: Any) -> Vector4:
        """Add two vectors together.

        Args:
            other: The other vector to add.

        Returns:
            The sum of the two vectors.

        Raises:
            TypeError: If the other object is not a Vector4.
        """
        if not isinstance(other, Vector4):
            error = f"Unsupported operand type(s) for +: 'Vector4' and '{type(other)}'"
            raise TypeError(error)
        return Vector4(x=self.x + other.x, y=self.y + other.y, z=self.z + other.z, w=self.w + other.w)

    def __sub__(self, other: Any) -> Vector4:
        """Subtract one vector from another.

        Args:
            other: The other vector to subtract.

        Returns:
            The difference of the two vectors.

        Raises:
            TypeError: If the other object is not a Vector4.
        """
        if not isinstance(other, Vector4):
            error = f"Unsupported operand type(s) for -: 'Vector4' and '{type(other)}'"
            raise TypeError(error)
        return Vector4(x=self.x - other.x, y=self.y - other.y, z=self.z - other.z, w=self.w - other.w)

    def __mul__(self, other: Any) -> Vector4:
        """Multiply a vector by a scalar.

        Args:
            other: The scalar to multiply by.

        Returns:
            The product of the vector and scalar.

        Raises:
            TypeError: If the other object is not an int or float.
        """
        if not isinstance(other, (int, float)):
            error = f"Unsupported operand type(s) for *: 'Vector4' and '{type(other)}'"
            raise TypeError(error)
        return Vector4(x=self.x * other, y=self.y * other, z=self.z * other, w=self.w * other)

    def __truediv__(self, other: Any) -> Vector4:
        """Divide a vector by a scalar.

        Args:
            other: The scalar to divide by.

        Returns:
            The quotient of the vector and scalar.

        Raises:
            TypeError: If the other object is not an int or float.
        """
        if not isinstance(other, (int, float)):
            error = f"Unsupported operand type(s) for /: 'Vector4' and '{type(other)}'"
            raise TypeError(error)
        return Vector4(x=self.x / other, y=self.y / other, z=self.z / other, w=self.w / other)
