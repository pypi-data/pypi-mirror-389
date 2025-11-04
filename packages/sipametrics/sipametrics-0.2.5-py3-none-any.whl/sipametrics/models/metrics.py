import pydantic
import typing
import sipametrics.models.base as base_models


class MetricsRequest(base_models.CamelCaseBaseModel):
    entity_id: typing.Union[list[str], str] = pydantic.Field(serialization_alias="indexIds")
    metric_id: typing.Union[list[str], str] = pydantic.Field(serialization_alias="typeIds")

    @pydantic.field_validator("entity_id", "metric_id", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v
    
    def to_dict(self) -> dict:
        payload = { "metrics": [ self.model_dump(by_alias=True) ] }
        return payload
