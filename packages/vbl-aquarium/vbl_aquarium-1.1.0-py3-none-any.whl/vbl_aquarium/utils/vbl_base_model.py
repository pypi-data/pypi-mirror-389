from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal


class VBLBaseModel(BaseModel):
    """Base model for all VBL models.

    Configured to use PascalCase for field names.
    """

    # noinspection PyDataclass
    model_config = ConfigDict(alias_generator=to_pascal, populate_by_name=True)  # pyright: ignore [reportUnannotatedClassAttribute]

    def to_json_string(self) -> str:
        return self.model_dump_json(by_alias=True)
