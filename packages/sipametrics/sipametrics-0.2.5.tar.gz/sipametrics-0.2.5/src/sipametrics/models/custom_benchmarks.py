import datetime
import pydantic
import typing
import sipametrics.models.base as base_models
import sipametrics.constants as CONSTANTS


class ColumnAndValue(base_models.CamelCaseBaseModel):
    column: str
    value: str

class Constraint(base_models.CamelCaseBaseModel):
    criteria: list[typing.Union["EqualityConstraint", "RangeConstraint", ColumnAndValue, "Constraint"]] = pydantic.Field(min_length=1)
    type: CONSTANTS.CriteriaAggregationType = CONSTANTS.CriteriaAggregationType.AND
    start_date: typing.Optional[datetime.date] = None

    def to_dict(self) -> dict:
        payload = self.model_dump(mode="json", by_alias=True, exclude_defaults=True)
        return payload

class EqualityConstraint(Constraint):
    target: float

class RangeConstraint(Constraint):
    lower: float
    upper: float

class CustomBenchmarkRequest(base_models.CamelCaseBaseModel):
    external_ticker: str
    start_date: typing.Optional[datetime.date] = None
    end_date: typing.Optional[datetime.date] = None
    currency: typing.Optional[str] = pydantic.Field(default=None, serialization_alias="currencyCode")
    constraints: typing.Optional[list[typing.Union[Constraint, EqualityConstraint, RangeConstraint]]] = None
    initial_index_value: typing.Optional[float] = None
    allocations: typing.Optional[bool] = None
    risk_profiles: typing.Optional[bool] = None
    include_constituents: typing.Optional[bool] = None

    @pydantic.field_validator("currency", mode="after")
    @classmethod
    def validate_currency(cls, v: typing.Optional[str]) -> typing.Optional[str]:
        if v and v.upper() not in CONSTANTS.CURRENCY_MAP:
            raise ValueError(f"Invalid currency code: {v}")

        return v

    def to_dict(self) -> dict:
        payload = self.model_dump(mode="json", by_alias=True, exclude={"constraints"}, exclude_defaults=True)
        if self.constraints:
            constraints = []
            for constraint in self.constraints:
                constraints.append(constraint.to_dict())
            payload["constraints"] = constraints

        return payload