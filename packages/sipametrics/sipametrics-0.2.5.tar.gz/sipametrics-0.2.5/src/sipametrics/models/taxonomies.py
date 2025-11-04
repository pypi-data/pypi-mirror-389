import pydantic
import typing
import sipametrics.models.base as base_models
import sipametrics.constants as CONSTANTS


class TaxonomiesRequest(base_models.CamelCaseBaseModel):
    taxonomy: CONSTANTS.Taxonomy
    pillar: typing.Optional[typing.Union[CONSTANTS.Ticcs, CONSTANTS.Peccs]] = None

    model_config = pydantic.ConfigDict(use_enum_values=True)


    @pydantic.model_validator(mode="after")
    def validate_pillar_in_taxonomy(cls, values):
        if values.pillar:
            if values.taxonomy in [CONSTANTS.Taxonomy.TICCS_TO_NACE, CONSTANTS.Taxonomy.TICCS_TO_EU]:
                raise ValueError("Pillar is not supported for TICCS-to-NACE or TICCS-to-EU taxonomy.")
            if values.taxonomy == CONSTANTS.Taxonomy.TICCS and values.pillar not in {pillar for pillar in CONSTANTS.Ticcs}:
                raise ValueError("For TICCS taxonomy, pillar has to be one of the values in CONSTANTS.Ticcs.")
            if values.taxonomy == CONSTANTS.Taxonomy.PECCS and values.pillar not in {pillar for pillar in CONSTANTS.Peccs}:
                raise ValueError("For PECCS taxonomy, pillar has to be one of the values in CONSTANTS.Peccs.")
            if values.taxonomy == CONSTANTS.Taxonomy.TICCS_PLUS and values.pillar not in {pillar for pillar in CONSTANTS.TiccsPlus}:
                raise ValueError("For TICCS+ taxonomy, pillar has to be one of the values in CONSTANTS.TiccsPlus.")
            
        return values

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True)