# SIPAMetrics Service

A Python package for interacting with the SIPAMetrics API to fetch metrics and other relevant data. This package simplifies integration by providing an easy-to-use interface for developers.


## Python Versions

> **ℹ️ Note**: Please note that we will be removing support for Python 3.9 once it is deemed end of life (October 2025).


## Installation

Install the package via pip:

```
pip install sipametrics
```


## Usage
Here's how you can use the sipametrics package in your Python projects.

### Example 1: Simple Usage
This example demonstrates a basic way to initialize the service and fetch metrics using an `async` function.

```
import asyncio
from sipametrics import SipaMetricsService

async def main():
    service = SipaMetricsService(api_key='your_api_key', api_secret='your_api_secret')
    response = await service.metrics(entity_id='INFRBGWX', metric_id='T01414')
    print(response)
    await service.close()

if __name__ == '__main__':
    asyncio.run(main())
```

### Example 2: Using Context Manager
This example uses a context manager `async with` for better resource management.

```
import asyncio
from sipametrics import SipaMetricsService

async def main():
    async with SipaMetricsService(api_key='your_api_key', api_secret='your_api_secret') as session:
        response = await session.metrics(entity_id='INFRBGWX', metric_id='T01414')
        print(response)

asyncio.run(main())
```


## API Reference
**Service Initialization**

- `SipaMetricsService(api_key: str, api_secret: str)`: Initializes the service with your API credentials.

**Methods**

- Please kindly refer to https://docs.sipametrics.com/docs/2-3-python for the full list of supported functions.


## License Terms & Conditions
The utilization of the sipametrics Python package entails accessing certain data from Scientific Infra and Private Assets ("SIPA"). Your access and utilization of SIPA, including its sipametrics Python package and associated data, are governed by the terms and conditions set forth in your organization's agreement with SIPA. To align with the workflow demands of a single user, sipametrics package imposes restrictions to safeguard the overall platform’s capacity to support the usage levels of all individual SIPA users accessing data via APIs. These restrictions are subject to modification at our sole discretion, without prior notice. It is your sole responsibility to furnish all necessary support pertaining to any applications developed utilizing the sipametrics Python package. Kindly take note that if you have intentions to resell or distribute any applications or data developed using the sipametrics Python package to third parties, it is imperative to engage in a distribution license agreement with us. Please contact your Customer Success Manager or Sales Representative at SIPA for further information.

