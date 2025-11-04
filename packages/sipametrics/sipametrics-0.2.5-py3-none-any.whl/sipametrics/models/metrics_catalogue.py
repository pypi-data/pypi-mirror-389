import pydantic
import typing
import sipametrics.models.base as base_models
import sipametrics.constants as CONSTANTS


class MetricsCatalogueRequest(base_models.CamelCaseBaseModel):
    product: CONSTANTS.Product
    app: CONSTANTS.App
    asset_class: typing.Optional[CONSTANTS.AssetClass] = None


    @pydantic.model_validator(mode="after")
    def validate_product_and_app(self):
        if self.product == CONSTANTS.Product.PRIVATE_EQUITY and self.app == CONSTANTS.App.VALUATION:
            raise ValueError(f"Invalid combination: Product.PRIVATE_EQUITY + App.VALUATION is not supported at the moment.")
        return self

    def to_dict(self) -> dict:
        payload:dict[str, typing.Union[str, int]] = { 
            "product": self.product.value if isinstance(self.product, CONSTANTS.Product) else self.product,
        }
        
        # if self.app:
        #     payload["app"] = self.app.value if isinstance(self.app, CONSTANTS.App) else self.app
        if self.asset_class:
            payload["option"] = self.asset_class.value if isinstance(self.asset_class, CONSTANTS.AssetClass) else self.asset_class

        return payload