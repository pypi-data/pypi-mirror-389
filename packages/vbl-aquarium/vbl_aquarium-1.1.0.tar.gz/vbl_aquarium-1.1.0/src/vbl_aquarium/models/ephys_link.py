"""Models for the Ephys Link Socket.IO API.

Used by Ephys Link and Pinpoint.
"""

from __future__ import annotations

from pydantic import Field

from vbl_aquarium.models.unity import Vector3, Vector4
from vbl_aquarium.utils.vbl_base_model import VBLBaseModel


class EphysLinkOptions(VBLBaseModel):
    """Options for running Ephys Link.

    Attributes:
        background: Whether to skip the GUI and run using CLI arguments.
        ignore_updates: Whether to ignore updates.
        type: Type of manipulator platform to use.
        debug: Whether to print debug messages.
        use_proxy: Whether to use VBL proxy service.
        proxy_address: Address of the proxy service.
        mpm_port: Port for New Scale MPM HTTP server.
        serial: Serial port for emergency stop.
    """

    background: bool = False
    ignore_updates: bool = False
    type: str = "ump-4"
    debug: bool = False
    use_proxy: bool = False
    proxy_address: str = "proxy2.virtualbrainlab.org"
    mpm_port: int = Field(default=8080, ge=1024, le=49151)
    parallax_port: int = Field(default=8081, ge=1024, le=49151)
    serial: str = "no-e-stop"


class PlatformInfo(VBLBaseModel):
    """General metadata information about the manipulator platform

    Attributes:
        name: Name of the manipulator platform.
        cli_name: CLI identifier for the manipulator platform (for the `-t` flag).
        axes_count: Number of axes on a manipulator.
        dimensions: Dimensions of the manipulators (3-axis manipulators should set w to 0).
    """

    name: str = Field(min_length=1)
    cli_name: str = Field(min_length=1)
    axes_count: int = Field(default=0, ge=-1)
    dimensions: Vector4 = Vector4()


class SetPositionRequest(VBLBaseModel):
    """Position to set a manipulator to.

    These are the absolute positions of the manipulator stages.

    Attributes:
        manipulator_id: ID of the manipulator to move.
        position: Position to move to in mm (X, Y, Z, W).
        speed: Speed to move at in mm/s.
    """

    manipulator_id: str = Field(min_length=1)
    position: Vector4
    speed: float = Field(gt=0)


class SetInsideBrainRequest(VBLBaseModel):
    """Set the "inside brain" state of a manipulator.

    Attributes:
        manipulator_id: ID of the manipulator to move.
        inside: Whether the manipulator is inside the brain.
    """

    manipulator_id: str = Field(min_length=1)
    inside: bool


class SetDepthRequest(VBLBaseModel):
    """Depth to drive a manipulator to.

    These are the absolute positions of the manipulator stages.

    Attributes:
        manipulator_id: ID of the manipulator to move.
        depth: Depth to drive to in mm.
        speed: Speed to drive at in mm/s.
    """

    manipulator_id: str = Field(min_length=1)
    depth: float
    speed: float = Field(gt=0)


class GetManipulatorsResponse(VBLBaseModel):
    """List the IDs of available manipulators from the active platform.

    Attributes:
        manipulators: List of manipulators by ID.
        error: Error message if any.
    """

    # noinspection PyDataclass
    manipulators: list[str] = Field(default_factory=list)
    error: str = ""


class PositionalResponse(VBLBaseModel):
    """Position of a manipulator.

    Attributes:
        position: Position of the manipulator.
        error: Error message if any.
    """

    position: Vector4 = Vector4()
    error: str = ""


class AngularResponse(VBLBaseModel):
    """Manipulator axis angles.

    This is not very standardized and its usage is platform-specific.

    Attributes:
        angles: Position of the manipulator.
        error: Error message if any.
    """

    angles: Vector3 = Vector3()
    error: str = ""


class ShankCountResponse(VBLBaseModel):
    """Number of electrode shanks on a manipulator.

    Attributes:
        shank_count: Number of shanks.
        error: Error message if any.
    """

    shank_count: int = Field(default=1, ge=1)
    error: str = ""


class SetDepthResponse(VBLBaseModel):
    """Final depth a manipulator is at after a drive.

    Attributes:
        depth: Depth the manipulator is at in mm.
        error: Error message if any.
    """

    depth: float = 0
    error: str = ""


class BooleanStateResponse(VBLBaseModel):
    """Boolean state from an event.

    Attributes:
        state: State of the event.
        error: Error message if any.
    """

    state: bool = False
    error: str = ""
