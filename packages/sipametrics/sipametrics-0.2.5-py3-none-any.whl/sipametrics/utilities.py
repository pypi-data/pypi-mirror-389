import datetime
import dateutil.relativedelta
import typing


def calculate_start_date(end_date: typing.Optional[datetime.date], window_in_years: typing.Optional[int]) -> typing.Optional[datetime.date]:
    if not end_date or not window_in_years:
        return None

    start_date = end_date - dateutil.relativedelta.relativedelta(years=window_in_years)
    return start_date
