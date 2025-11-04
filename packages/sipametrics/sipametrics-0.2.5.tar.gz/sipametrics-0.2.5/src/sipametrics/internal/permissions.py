import itertools
import pydantic
import sipametrics.internal.endpoints as _endpoints
import sipametrics.internal.clients as _clients
import sipametrics.models.permissions as permission_models


async def _check_permissions(
    client :_clients.BaseClient, 
    index_tickers: list[str], 
    metric_tickers: list[str],
    action_name: str,
):
    combinations = itertools.product(index_tickers, metric_tickers)
    permission_tuples = [
        permission_models.PermissionTuple(
            resource_ticker=combination[0], 
            metric_ticker=combination[1], 
            action_name=action_name,
        ) for combination in combinations
    ]

    try:
        request = permission_models.PermissionsRequest(permissions=permission_tuples)
    except pydantic.ValidationError as e:
        raise ValueError(f"Invalid arguments: {e}")
    
    params = request.to_dict()
    return await client._post(_endpoints.URLS[_check_permissions.__name__], data=params) 