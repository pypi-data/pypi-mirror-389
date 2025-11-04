import sipametrics.models.base as base_models


class PermissionTuple(base_models.CamelCaseBaseModel):
    resource_ticker: str
    metric_ticker: str
    action_name: str

class PermissionsRequest(base_models.CamelCaseBaseModel):
    permissions: list[PermissionTuple]

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True)