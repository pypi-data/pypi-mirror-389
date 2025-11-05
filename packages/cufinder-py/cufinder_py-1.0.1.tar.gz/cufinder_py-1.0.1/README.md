# CUFinder Python SDK

[![](https://img.shields.io/badge/repo%20status-Active-28a745)](https://github.com/cufinder/cufinder-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-514BEE.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/cufinder-py.svg)](https://badge.fury.io/py/cufinder-py)

A Python SDK for the CUFinder API that provides access to all company and person enrichment services.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Types](#types)
- [Support](#support)

## Installation

```bash
pip install cufinder-py
```

## Usage

```python
from cufinder import Cufinder

# Initialize the client
client = Cufinder('your-api-key-here')

# Initialize with more options
client = Cufinder('your-api-key-here', timeout=60)
```

## API Reference

This SDK covers all 20 Cufinder API (v2) endpoints:

- **CUF** - Company Name to Domain API
- **LCUF** - Company LinkedIn URL Finder API
- **DTC** - Domain to Company Name API
- **DTE** - Company Email Finder API
- **NTP** - Company Phone Finder API
- **REL** - Reverse Email Lookup API
- **FCL** - Company Lookalikes Finder API
- **ELF** - Company Fundraising API
- **CAR** - Company Revenue Finder API
- **FCC** - Company Subsidiaries Finder API
- **FTS** - Company Tech Stack Finder API
- **EPP** - LinkedIn Profile Enrichment API
- **FWE** - LinkedIn Profile Email Finder API
- **TEP** - Person Enrichment API
- **ENC** - Company Enrichment API
- **CEC** - Company Employee Count API
- **CLO** - Company Locations API
- **CSE** - Company Search API
- **PSE** - Person Search API
- **LBS** - Local Business Search API (Google Maps Search API)


**CUF - Company Name to Domain API**

Returns the official website URL of a company based on its name.

```python
result = client.cuf('cufinder', 'US')
print(result)
```

**LCUF - Company LinkedIn URL Finder API**

Finds the official LinkedIn company profile URL from a company name.

```python
result = client.lcuf('cufinder')
print(result)
```

**DTC - Domain to Company Name API**

Retrieves the registered company name associated with a given website domain.

```python
result = client.dtc('cufinder.io')
print(result)
```

**DTE - Company Email Finder API**

Returns up to five general or role-based business email addresses for a company.

```python
result = client.dte('cufinder.io')
print(result)
```

**NTP - Company Phone Finder API**

Returns up to two verified phone numbers for a company.

```python
result = client.ntp('apple')
print(result)
```

**REL - Reverse Email Lookup API**

Enriches an email address with detailed person and company information.

```python
result = client.rel('iain.mckenzie@stripe.com')
print(result)
```

**FCL - Company Lookalikes Finder API**

Provides a list of similar companies based on an input company's profile.

```python
result = client.fcl('apple')
print(result)
```

**ELF - Company Fundraising API**

Returns detailed funding information about a company.

```python
result = client.elf('cufinder')
print(result)
```

**CAR - Company Revenue Finder API**

Estimates a company's annual revenue based on name.

```python
result = client.car('apple')
print(result)
```

**FCC - Company Subsidiaries Finder API**

Identifies known subsidiaries of a parent company.

```python
result = client.fcc('amazon')
print(result)
```

**FTS - Company Tech Stack Finder API**

Detects the technologies a company uses.

```python
result = client.fts('cufinder')
print(result)
```

**EPP - LinkedIn Profile Enrichment API**

Takes a LinkedIn profile URL and returns enriched person and company data.

```python
result = client.epp('linkedin.com/in/iain-mckenzie')
print(result)
```

**FWE - LinkedIn Profile Email Finder API**

Extracts a verified business email address from a LinkedIn profile URL.

```python
result = client.fwe('linkedin.com/in/iain-mckenzie')
print(result)
```

**TEP - Person Enrichment API**

Returns enriched person data based on full name and company name.

```python
result = client.tep('iain mckenzie', 'stripe')
print(result)
```

**ENC - Company Enrichment API**

Provides a complete company profile from a company name.

```python
result = client.enc('cufinder')
print(result)
```

**CEC - Company Employee Count API**

Returns an estimated number of employees for a company.

```python
result = client.cec('cufinder')
print(result)
```

**CLO - Company Locations API**

Returns the known physical office locations of a company.

```python
result = client.clo('apple')
print(result)
```

**CSE - Company Search API**

Search for companies by keyword, partial name, industry, location, or other filters.

```python
result = client.cse(
    name='cufinder',
    country='germany',
    state='hamburg',
    city='hamburg'
)
print(result)
```

**PSE - Person Search API**

Search for people by name, company, job title, location, or other filters.

```python
result = client.pse(
    full_name='iain mckenzie',
    company_name='stripe'
)
print(result)
```

**LBS - Local Business Search API (Google Maps Search API)**

Search for local businesses by location, industry, or name.

```python
result = client.lbs(
    country='united states',
    state='california',
    page=1
)
print(result)
```

## Error Handling

The SDK provides comprehensive error handling with custom error types:

```python
from cufinder import (
    CufinderError,
    AuthenticationError,
    CreditLimitError,
    NotFoundError,
    PayloadError,
    RateLimitError,
    ServerError,
    NetworkError
)

try:
    result = client.cuf('cufinder', 'US')
except AuthenticationError as error:
    # 401 - Invalid API key
    print('Authentication failed:', error.message)
except CreditLimitError as error:
    # 400 - Not enough credit
    print('Not enough credit:', error.message)
except NotFoundError as error:
    # 404 - Not found result
    print('Not found result:', error.message)
except PayloadError as error:
    # 422 - Error in the payload
    print('Payload error:', error.message, error.details)
except RateLimitError as error:
    # 429 - Rate limit exceeded
    print('Rate limit exceeded. Retry after:', error.details.get('retry_after'))
except ServerError as error:
    # 500, 501, ... - Server errors
    print('Server error:', error.message, 'Status:', error.status_code)
except NetworkError as error:
    print('Network error:', error.message)
except CufinderError as error:
    print('Unknown error:', error.message)
```

## Types

The SDK exports comprehensive Python types:

```python
from cufinder import (
    # Client types
    BaseApiClient,
    CufinderClientConfig,
    RequestConfig,
    Response,

    # Request types
    CseParams,
    PseParams,
    LbsParams,

    # Response types
    BaseResponse,
    ApiResponse,

    # Model types
    Company,
    Person,
    LookalikeCompany,
    FundraisingInfo,
    CompanyLocation,
    TepPerson,
    CloCompanyLocation,
    CompanySearchResult,
    PersonSearchResult,
    LocalBusinessResult,

    # Error types
    CufinderError,
    AuthenticationError,
    CreditLimitError,
    NotFoundError,
    PayloadError,
    RateLimitError,
    ServerError,
    NetworkError
)
```

## Support

For support, please open an issue on the [GitHub repository](https://github.com/cufinder/cufinder-py/issues).