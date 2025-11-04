import datetime
import pydantic
import typing
import sipametrics.models.base as base_models
import sipametrics.utilities as utilities
import sipametrics.constants as CONSTANTS


class TiccsProfile(base_models.CamelCaseBaseModel):
    industrial_activities: typing.Optional[list[str]] = None
    business_risk: typing.Optional[str] = pydantic.Field(default=None, serialization_alias="businessModel")
    corporate_structure: typing.Optional[str] = None

    def to_list(self) -> list:
        entries = []
        for key,value in self.model_dump(by_alias=True, exclude_defaults=True).items():
            entries.append({ "profile": { key: value } })

        return entries
    
class FactorProfile(base_models.CamelCaseBaseModel):
    currency: typing.Optional[str] = None
    countries: typing.Optional[list[str]] = None

    # country_ids: typing.Optional[list[str]] = pydantic.Field(default=None, exclude=False, validate_default=False)

    @pydantic.field_validator("currency", mode="after")
    @classmethod
    def validate_currency(cls, v: typing.Optional[str]) -> typing.Optional[str]:
        if v and v.upper() not in CONSTANTS.CURRENCY_MAP:
            raise ValueError(f"Invalid currency code: {v}")

        return v
    
    @pydantic.field_validator("countries", mode="after")
    @classmethod
    def validate_countries(cls, v: typing.Optional[list[str]]) -> typing.Optional[list[str]]:
        if v:
            for country in v:
                if country not in CONSTANTS.COUNTRY_MAP:
                    raise ValueError(f"Invalid country code: {country}")
            
            # cls.country_ids = [ CONSTANTS.COUNTRY_MAP[country] for country in values.countries ]

        return v

class EquityFactorProfile(FactorProfile):
    size: typing.Optional[typing.Union[float, str]] = None
    leverage: typing.Optional[typing.Union[float, str]] = None
    profitability: typing.Optional[typing.Union[float, str]] = None
    investment: typing.Optional[typing.Union[float, str]] = None
    time_to_maturity: typing.Optional[typing.Union[float, str]] = None

    @pydantic.field_validator("time_to_maturity", mode="after")
    @classmethod
    def validate_time_to_maturity(cls, v: typing.Optional[typing.Union[float, str]]) -> typing.Optional[typing.Union[float, str]]:
        if isinstance(v, str) and v not in CONSTANTS.TIME_TO_MATURITY_BUCKETS:
            raise ValueError(f"Invalid time to maturity bucket: {v}")

        return v

    def to_list(self) -> list:
        entries = []

        if self.countries:
            profile = { 
                "profile": {
                    "factor": "countries",
                    "countries": [ CONSTANTS.COUNTRY_MAP[country] for country in self.countries ]
                }
            }
            entries.append(profile)

        for key,value in self.model_dump(by_alias=True, exclude_defaults=True, exclude={"currency", "countries"}).items():
            profile = { "factor": key, key: value }

            if isinstance(value, str) and len(value) > 1:
                if key == "timeToMaturity":
                    profile["timeToMaturityBucket"] = CONSTANTS.TIME_TO_MATURITY_BUCKETS[value]
                else:
                    profile["quintile"] = int(value[1:])
                profile.pop(key)

            if key in ["size"] and self.currency:
                profile["currency"] = CONSTANTS.CURRENCY_MAP[self.currency.upper()]

            entries.append({ "profile": profile })

        return entries
    
class DebtFactorProfile(FactorProfile):
    face_value: typing.Optional[typing.Union[float, str]] = None
    time_to_maturity: typing.Optional[typing.Union[float, str]] = pydantic.Field(default=None, serialization_alias="debtTimeToMaturity")

    @pydantic.field_validator("time_to_maturity", mode="after")
    @classmethod
    def validate_time_to_maturity(cls, v: typing.Optional[typing.Union[float, str]]) -> typing.Optional[typing.Union[float, str]]:
        if isinstance(v, str) and v not in CONSTANTS.TIME_TO_MATURITY_BUCKETS:
            raise ValueError(f"Invalid time to maturity bucket: {v}")

        return v

    def to_list(self) -> list:
        entries = []

        if self.countries:
            profile = { 
                "profile": {
                    "factor": "countries",
                    "countries": [ CONSTANTS.COUNTRY_MAP[country] for country in self.countries ]
                }
            }
            entries.append(profile)

        for key,value in self.model_dump(by_alias=True, exclude_defaults=True, exclude={"currency", "countries"}).items():
            profile = { "factor": key, key: value }

            if isinstance(value, str) and len(value) > 1:
                if key == "debtTimeToMaturity":
                    profile["timeToMaturityBucket"] = CONSTANTS.TIME_TO_MATURITY_BUCKETS[value]
                else:
                    profile["quintile"] = int(value[1:])
                profile.pop(key)

            if key in ["faceValue"] and self.currency:
                profile["currency"] = CONSTANTS.CURRENCY_MAP[self.currency.upper()]

            entries.append({ "profile": profile })

        return entries    

class ComparableRequest(base_models.CamelCaseBaseModel):
    metric: str
    age_in_months: typing.Optional[int] = pydantic.Field(default=None, serialization_alias="age")
    end_date: typing.Optional[datetime.date] = None
    window_in_years: typing.Optional[int] = pydantic.Field(default=None, exclude=True, gt=0)
    ticcs_profiles: typing.Optional[TiccsProfile] = None 
    factors_profiles: typing.Optional[typing.Union[EquityFactorProfile, DebtFactorProfile]] = None
    intersect_ticcs: typing.Optional[bool] = None   
    factor_weight: typing.Optional[float] = None

    start_date: typing.Optional[datetime.date] = pydantic.Field(default=None, exclude=False, validate_default=False)

    @pydantic.model_validator(mode="after")
    def compute_start_date(cls, values):
        if values.age_in_months is not None:
            values.start_date = None
            values.end_date = None

            return values
        
        if values.end_date is None or values.window_in_years is None:
            raise ValueError(
                "Either 'age_in_months' must be set, "
                "or both 'end_date' and 'window_in_years' must be provided."
            )

        values.start_date = utilities.calculate_start_date(end_date=values.end_date, window_in_years=values.window_in_years)
        return values

    def to_dict(self) -> dict:
        payload = self.model_dump(mode="json", by_alias=True, exclude={"ticcs_profiles", "factors_profiles"}, exclude_defaults=True)
        if self.ticcs_profiles:
            payload["ticcsProfiles"] = self.ticcs_profiles.to_list()
        if self.factors_profiles:
            payload["factorsProfiles"] = self.factors_profiles.to_list()

        return payload