import datetime
import pydantic
import typing
import sipametrics.models.base as base_models
import sipametrics.utilities as utilities
import sipametrics.constants as CONSTANTS


class PeccsCountryProfile(base_models.CamelCaseBaseModel):
    industrial_activities: typing.Optional[list[str]] = None
    revenue_models: typing.Optional[list[str]] = None
    customer_models: typing.Optional[list[str]] = None
    lifecycle_phases: typing.Optional[list[str]] = None
    value_chain_types: typing.Optional[list[str]] = None
    countries: typing.Optional[list[str]] = None

    @pydantic.field_validator("countries", mode="after")
    @classmethod
    def validate_countries(cls, v: typing.Optional[list[str]]) -> typing.Optional[list[str]]:
        if v:
            for country in v:
                if country not in CONSTANTS.COUNTRY_MAP:
                    raise ValueError(f"Invalid country code: {country}")

        return v
       
class FactorProfile(base_models.CamelCaseBaseModel):
    size: typing.Optional[typing.Union[float, str]] = None
    growth: typing.Optional[typing.Union[float, str]] = None
    leverage: typing.Optional[typing.Union[float, str]] = None
    profits: typing.Optional[typing.Union[float, str]] = None
    country_risk: typing.Optional[list[str]] = pydantic.Field(default=None, serialization_alias="termSpread")

    @pydantic.field_validator("country_risk", mode="after")
    @classmethod
    def validate_countries(cls, v: typing.Optional[list[str]]) -> typing.Optional[list[str]]:
        if v:
            for country in v:
                if country not in CONSTANTS.COUNTRY_MAP:
                    raise ValueError(f"Invalid country code: {country}")

        return v

    def to_list(self, currency: typing.Optional[str] = None) -> list:
        entries = []

        for key,value in self.model_dump(by_alias=True, exclude_defaults=True).items():
            profile = { "factorName": key.title(), key: value }

            if (key == "termSpread"):
                profile["countries"] = value
                profile.pop(key)

                entries.append(profile)
                continue

            if isinstance(value, str) and len(value) > 1:
                profile["quintile"] = int(value[1:])
                profile.pop(key)

            if (key == "size" and currency):
                profile["currency"] = currency

            entries.append(profile)

        return entries    
    
class ComparableBaseRequest(base_models.CamelCaseBaseModel):
    metric: str
    currency: typing.Optional[str] = pydantic.Field(default=None, serialization_alias="reportingCurrency")
    age_in_months: typing.Optional[int] = pydantic.Field(default=None, serialization_alias="age")
    end_date: typing.Optional[datetime.date] = None
    window_in_years: typing.Optional[int] = pydantic.Field(default=None, exclude=True, gt=0)
    universe: typing.Optional[str] = None
    factor_weight: typing.Optional[float] = None

    start_date: typing.Optional[datetime.date] = pydantic.Field(default=None, exclude=False, validate_default=False)

    @pydantic.field_validator("currency", mode="after")
    @classmethod
    def validate_currency(cls, v: typing.Optional[str]) -> typing.Optional[str]:
        if v and v.upper() not in CONSTANTS.CURRENCY_MAP:
            raise ValueError(f"Invalid currency code: {v}")

        return v

    @pydantic.model_validator(mode="after")
    def compute_start_date(cls, values):
        if values.age_in_months:
            values.start_date = None
            values.end_date = None

            return values
        
        if not (values.end_date and values.window_in_years):
            raise ValueError(
                "Either 'age_in_months' must be set, "
                "or both 'end_date' and 'window_in_years' must be provided."
            )

        values.start_date = utilities.calculate_start_date(end_date=values.end_date, window_in_years=values.window_in_years)
        return values

class ComparableRequest(ComparableBaseRequest):
    peccs_country_profile: typing.Optional[PeccsCountryProfile] = None 
    factors_profiles: typing.Optional[FactorProfile] = None
    operation: typing.Optional[str] = None
    intersect_peccs: typing.Optional[bool] = None   
   
    def to_dict(self):
        payload = self.model_dump(mode="json", by_alias=True, exclude={"factors_profiles"}, exclude_defaults=True)
        if self.factors_profiles:
            payload["factorsProfiles"] = self.factors_profiles.to_list(currency=self.currency)

        return payload

class ComparableBoundaryRequest(ComparableBaseRequest):
    factor_name: str
    peccs_country_profile: typing.Optional[PeccsCountryProfile] = None 

    def to_dict(self):
        payload = self.model_dump(mode="json", by_alias=True, exclude_defaults=True)
        return payload