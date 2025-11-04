# import pydantic
import typing
import sipametrics.models.base as base_models
import sipametrics.constants as CONSTANTS


class IndicesCatalogueRequest(base_models.CamelCaseBaseModel):
    product: CONSTANTS.Product
    app: typing.Optional[CONSTANTS.App] = None


    # @pydantic.model_validator(mode="after")
    # def validate_product_and_app(self):
    #     if self.product == CONSTANTS.Product.PRIVATE_EQUITY and self.app == CONSTANTS.App.VALUATION:
    #         raise pydantic.ValidationError('Invalid combination: Product.PRIVATE_EQUITY + App.VALUATION is not supported at the moment.')
    #     return self

    def to_dict(self) -> dict:
        payload:dict[str, typing.Union[str, int]] = { 
            "product": self.product.value if isinstance(self.product, CONSTANTS.Product) else self.product 
        }
        
        if self.app:
            app_keys = {
                CONSTANTS.App.MARKET_INDICES: "marketIndices" if self.product == CONSTANTS.Product.PRIVATE_EQUITY else "indexApp",
                CONSTANTS.App.THEMATIC_INDICES: "peccsBenchmarks" if self.product == CONSTANTS.Product.PRIVATE_EQUITY else "ticcsResearchData",
                CONSTANTS.App.VALUATION: "analytics" if self.product == CONSTANTS.Product.PRIVATE_EQUITY else "assetValuation",
            } 
            app_key = app_keys.get(self.app)
            if app_key:
                payload[app_key] = 1

        return payload