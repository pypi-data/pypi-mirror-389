import datetime
import pydantic
import sipametrics.models.base as base_models
import sipametrics.constants as CONSTANTS


class TermStructureRequest(base_models.CamelCaseBaseModel):
    country: str = pydantic.Field(serialization_alias="countryName")
    date: datetime.date = pydantic.Field(serialization_alias="valueDate")
    maturity_date: datetime.date

    @pydantic.field_validator("country", mode="after")
    @classmethod
    def validate_countries(cls, v: str) -> str:
        if v not in CONSTANTS.COUNTRY_MAP:
            raise ValueError(f"Invalid country code: {v}")

        return v

    def to_dict(self) -> dict:
        return self.model_dump(mode="json", by_alias=True)