import datetime
import typing
import sipametrics.models.base as base_models


class FundDatapoint(base_models.CamelCaseBaseModel):
    contribution: float
    distribution: float
    date: datetime.date

class FundData(base_models.CamelCaseBaseModel):
    cashflows: list[FundDatapoint]
    final_nav: float
    fund_name: typing.Optional[str]

class IndexBenchmarkDatapoint(base_models.CamelCaseBaseModel):
    level: float
    date: datetime.date

class IndexBenchmarkData(base_models.CamelCaseBaseModel):
    index_benchmark_data: list[IndexBenchmarkDatapoint]
    index_name: typing.Optional[str] = None

class IndexBenchmarkTicker(base_models.CamelCaseBaseModel):
    ticker: str
    index_name: typing.Optional[str] = None

class FundAlphaData(base_models.CamelCaseBaseModel):
    fund_data: FundData
    market_index_data: typing.Union[IndexBenchmarkData, IndexBenchmarkTicker]
    benchmark_data: typing.Optional[typing.Union[IndexBenchmarkData, IndexBenchmarkTicker]] = None
    weight: typing.Optional[float] = None

class AlphaRequest(base_models.CamelCaseBaseModel):
    fund_alpha_data: list[FundAlphaData]

    def to_dict(self):
        return self.model_dump(mode="json", by_alias=True, exclude_defaults=True)