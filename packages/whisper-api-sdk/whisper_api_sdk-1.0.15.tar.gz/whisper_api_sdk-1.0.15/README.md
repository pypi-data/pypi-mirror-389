<div align="center">
  <img src="Whisper_Logo.png" alt="Whisper Logo" width="400"/>

  # Whisper API SDK - Python

[![CI](https://github.com/whisper-sec/sdk-python/actions/workflows/python.yml/badge.svg)](https://github.com/whisper-sec/sdk-python/actions/workflows/python.yml)
[![Publish](https://github.com/whisper-sec/sdk-python/actions/workflows/publish.yml/badge.svg)](https://github.com/whisper-sec/sdk-python/actions/workflows/publish.yml)
[![PyPI version](https://badge.fury.io/py/whisper_api_sdk.svg)](https://badge.fury.io/py/whisper_api_sdk)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/whisper_api_sdk)](https://pepy.tech/project/whisper_api_sdk)

> **Official Python SDK for Whisper API** - Comprehensive intelligence and monitoring capabilities for domains, IPs, and web infrastructure.

**[Website](https://www.whisper.security)** • **[Documentation](https://docs.whisper.security)** • **[API Reference](https://developer.whisper.security)** • **[API Playground](https://dash.whisper.security/playground)** • **[Contact Us](https://www.whisper.security/contactus)**

</div>

## Whisper API v1 - Python SDK

**The Foundational Intelligence Layer for the Internet**

Gain deep visibility into any internet asset with Whisper's comprehensive intelligence platform. Access powerful APIs for threat intelligence, domain monitoring, network security analysis, WHOIS data, DNS records, geolocation, BGP routing, and more - all through a single, unified interface.

The Whisper API provides comprehensive, real-time intelligence on any internet asset. By connecting billions of data points across live internet routing, historical registration records, and deep resolution data, our API moves beyond simple enrichment to deliver predictive, context-rich insights.

This Python SDK provides a fully-typed client for the Whisper API v1, designed for security experts, developers, and automated systems.

---

## 🚀 Quick Start

### 1. Installation

```bash
pip install whisper_api_sdk
```

### 2. Get Your API Key

Sign up at [dash.whisper.security](https://dash.whisper.security) to get your API key. Visit our [API Playground](https://dash.whisper.security/playground) to test the API interactively.

### 3. Make Your First Request

```python
import whisper_api_sdk
from whisper_api_sdk.rest import ApiException
from pprint import pprint

# Configure Bearer token authentication
configuration = whisper_api_sdk.Configuration(
    host = "https://api.whisper.security",
    access_token = "YOUR_API_KEY"  # Replace with your actual API key
)

# Create API client
with whisper_api_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the Indicators API
    api_instance = whisper_api_sdk.IndicatorsApi(api_client)

    try:
        # Enrich an IP address
        response = api_instance.get_indicator("ip", "8.8.8.8")
        print(f"Organization: {response.summary.organization}")
        print(f"Location: {response.summary.location}")
        print(f"Risk Score: {response.reputation.risk_score}")
    except ApiException as e:
        print(f"API Error: {e}")
```

---

## 🎯 Key Features

- **Unified & Simple**: Small set of powerful, resource-oriented endpoints
- **Performant by Design**: Asynchronous-first with strategic caching (<500ms typical response)
- **Workflow-Oriented**: Built for real-world security operations, not just data dumps
- **Comprehensive**: IP, Domain, DNS, WHOIS, Routing, Geolocation, Screenshots, Monitoring
- **Fully Typed**: Complete type hints for IDE autocomplete and type checking
- **Async Support**: Built-in support for async/await patterns

---

## 📋 Common Use Cases

### IP Address Enrichment
```python
# Get comprehensive IP intelligence
ip_data = api_instance.get_indicator("ip", "8.8.8.8", include="routing,rpki")
```

### Domain Analysis
```python
# Analyze a domain with WHOIS and DNS data
domain_data = api_instance.get_indicator("domain", "example.com", include="whois,dns_details")
```

### Bulk Lookups (Asynchronous)
```python
# Process multiple indicators
bulk_request = whisper_api_sdk.BulkRequest(
    indicators=["8.8.8.8", "example.com"],
    include=["basic", "reputation"]
)
job_response = api_instance.bulk_enrichment(bulk_request)

# Poll for results
job_id = job_response.job_id
# Use the Operations API to check job status
```

### Geolocation Lookup
```python
location_api = whisper_api_sdk.LocationApi(api_client)
location = location_api.get_ip_location("8.8.8.8")
print(f"Country: {location.country}")
print(f"City: {location.city}")
```

---

## 🔐 Authentication

All API endpoints require Bearer token authentication. Set your API key when configuring the client:

```python
configuration = whisper_api_sdk.Configuration(
    host = "https://api.whisper.security",
    access_token = "YOUR_API_KEY"
)
```

You can also use environment variables:

```python
import os
configuration = whisper_api_sdk.Configuration(
    host = "https://api.whisper.security",
    access_token = os.getenv("WHISPER_API_KEY")
)
```

---

## 📚 SDK Documentation

### Package Structure

```
whisper_api_sdk/
├── api/
│   ├── indicators_api.py      # Indicator enrichment endpoints
│   ├── location_api.py         # Geolocation endpoints
│   └── operations_api.py       # Async job management
├── models/                     # Data models and types
├── configuration.py            # SDK configuration
├── api_client.py              # Core API client
└── exceptions.py              # Exception classes
```

### API Classes

The SDK provides three main API classes:

#### IndicatorsApi
Comprehensive indicator enrichment for IPs and domains.

**Methods:**
- `get_indicator(type, value, include=None)` - Enrich a single indicator
- `get_indicator_history(type, value, limit=None)` - Get historical data
- `get_indicator_graph(type, value)` - Get relationship graph
- `get_subdomains(domain, limit=None)` - Get domain subdomains
- `generate_similar_domains_get(domain, type=None, limit=None)` - Generate similar domains (GET)
- `generate_similar_domains_post(domain, similar_domains_request)` - Generate similar domains (POST)
- `bulk_enrichment(bulk_request)` - Bulk enrichment (async job)
- `search_indicators(search_request)` - Search indicators (async job)

**Example:**
```python
from whisper_api_sdk.api import IndicatorsApi

api = IndicatorsApi(api_client)
response = api.get_indicator("ip", "8.8.8.8", include="routing,rpki")
```

[View Full IndicatorsApi Documentation](docs/IndicatorsApi.md)

#### LocationApi
Geolocation lookups and searches.

**Methods:**
- `get_ip_location(ip)` - Get IP geolocation
- `search_location(field, value, limit=None)` - Search by location attributes

**Example:**
```python
from whisper_api_sdk.api import LocationApi

api = LocationApi(api_client)
location = api.get_ip_location("8.8.8.8")
print(f"Country: {location.country}, City: {location.city}")
```

[View Full LocationApi Documentation](docs/LocationApi.md)

#### OperationsApi
Manage asynchronous jobs and operations.

**Methods:**
- `get_job(job_id)` - Get job status and results
- `list_jobs(status=None, limit=None)` - List user jobs
- `create_screenshot(screenshot_request)` - Capture screenshot (async job)
- `create_scan(infra_scan_request)` - Infrastructure scan (async job)

**Example:**
```python
from whisper_api_sdk.api import OperationsApi

api = OperationsApi(api_client)
job = api.get_job("job-uuid-here")
print(f"Status: {job.status}, Progress: {job.progress}")
```

[View Full OperationsApi Documentation](docs/OperationsApi.md)

---

## 📦 Data Models & Types

The SDK includes comprehensive type definitions for all API responses and requests. All models support:
- Type hints for IDE autocomplete
- JSON serialization/deserialization
- Validation
- Dictionary conversion

### Core Response Models

#### IndicatorResponse
Comprehensive intelligence for an IP or domain.

**Properties:**
- `query` (QueryInfo) - Query metadata
- `summary` (SummaryInfo) - Quick summary
- `geolocation` (dict) - Geographic data
- `network` (dict) - Network information
- `isp` (dict) - ISP details
- `registration` (dict) - WHOIS registration
- `dns` (DnsInfo) - DNS records
- `relationships` (RelationshipInfo) - Related infrastructure
- `reputation` (ReputationInfo) - Risk and reputation scores
- `security` (dict) - Security context
- `metadata` (MetadataInfo) - Response metadata

[View Full Model Documentation](docs/IndicatorResponse.md)

#### LocationResponse
Geolocation data for an IP address.

**Properties:**
- `ip` (str) - IP address
- `country` (str) - Country name
- `country_code` (str) - ISO country code
- `city` (str) - City name
- `latitude` (float) - Latitude
- `longitude` (float) - Longitude
- `timezone` (str) - Timezone
- `isp` (str) - ISP name
- `asn` (int) - Autonomous System Number

[View Full Model Documentation](docs/LocationResponse.md)

#### JobResponse
Asynchronous job status and results.

**Properties:**
- `job_id` (str) - Unique job identifier
- `status` (str) - Job status (pending, in_progress, completed, failed)
- `progress` (JobProgress) - Progress information
- `result` (dict) - Job results (when completed)
- `error` (JobError) - Error details (when failed)
- `created_at` (datetime) - Creation timestamp
- `updated_at` (datetime) - Last update timestamp

[View Full Model Documentation](docs/JobResponse.md)

### Request Models

#### BulkRequest
Request for bulk indicator enrichment.

**Properties:**
- `indicators` (List[str]) - List of IPs/domains (max 100)
- `include` (List[str]) - Data modules to include
- `options` (BulkOptions) - Processing options

[View Full Model Documentation](docs/BulkRequest.md)

#### SearchRequest
Request for indicator search.

**Properties:**
- `query` (str) - Search query
- `field` (str) - Field to search (registrantName, registrarName, etc.)
- `limit` (int) - Maximum results (default: 100)

[View Full Model Documentation](docs/SearchRequest.md)

#### ScreenshotRequest
Request for website screenshot.

**Properties:**
- `url` (str) - Target URL
- `options` (ScreenshotOptions) - Capture options (fullPage, format, etc.)

[View Full Model Documentation](docs/ScreenshotRequest.md)

#### InfraScanRequest
Request for infrastructure scanning.

**Properties:**
- `domain` (str) - Target domain
- `type` (str) - Scan type (subdomains, ports, dns)
- `config` (dict) - Type-specific configuration

[View Full Model Documentation](docs/InfraScanRequest.md)

### Complete Model Reference

For a complete list of all data models and their properties, see:

**Core Models:**
- [IndicatorResponse](docs/IndicatorResponse.md) - Main enrichment response
- [LocationResponse](docs/LocationResponse.md) - Geolocation data
- [JobResponse](docs/JobResponse.md) - Async job status
- [HistoryResponse](docs/HistoryResponse.md) - Historical data

**Request Models:**
- [BulkRequest](docs/BulkRequest.md) - Bulk enrichment
- [SearchRequest](docs/SearchRequest.md) - Search parameters
- [ScreenshotRequest](docs/ScreenshotRequest.md) - Screenshot options
- [InfraScanRequest](docs/InfraScanRequest.md) - Scan configuration
- [SimilarDomainsRequest](docs/SimilarDomainsRequest.md) - Similar domain generation

**Nested Models:**
- [QueryInfo](docs/QueryInfo.md) - Query metadata
- [SummaryInfo](docs/SummaryInfo.md) - Quick summary
- [DnsInfo](docs/DnsInfo.md) - DNS records
- [RelationshipInfo](docs/RelationshipInfo.md) - Infrastructure relationships
- [ReputationInfo](docs/ReputationInfo.md) - Reputation scores
- [MetadataInfo](docs/MetadataInfo.md) - Response metadata
- [JobProgress](docs/JobProgress.md) - Job progress details
- [JobError](docs/JobError.md) - Job error information

**Configuration Models:**
- [BulkOptions](docs/BulkOptions.md) - Bulk processing options
- [ScreenshotOptions](docs/ScreenshotOptions.md) - Screenshot settings
- [DnsEnumConfig](docs/DnsEnumConfig.md) - DNS enumeration config
- [PortScanConfig](docs/PortScanConfig.md) - Port scanning config
- [SubdomainEnumConfig](docs/SubdomainEnumConfig.md) - Subdomain enumeration config

**Security Models:**
- [BlacklistScores](docs/BlacklistScores.md) - Blacklist check results
- [DomainReputationScores](docs/DomainReputationScores.md) - Domain reputation
- [DomainReputationDetails](docs/DomainReputationDetails.md) - Detailed reputation data

**View All Models:** See the [docs/](docs/) directory for complete model documentation.

---

## 🔧 Advanced Usage

### Error Handling

The SDK provides structured exception handling:

```python
from whisper_api_sdk.rest import ApiException

try:
    response = api_instance.get_indicator("ip", "8.8.8.8")
except ApiException as e:
    print(f"Status: {e.status}")
    print(f"Reason: {e.reason}")
    print(f"Body: {e.body}")
```

### Custom Configuration

```python
from whisper_api_sdk import Configuration, ApiClient

config = Configuration(
    host="https://api.whisper.security",
    access_token=os.getenv("WHISPER_API_KEY")
)

# Custom timeout
config.timeout = 60

# Custom user agent
config.user_agent = "MyApp/1.0"

# Enable debugging
config.debug = True

# Disable SSL verification (not recommended for production)
config.verify_ssl = False
```

### Working with Async Jobs

```python
import time
from whisper_api_sdk.api import IndicatorsApi, OperationsApi
from whisper_api_sdk.models import BulkRequest

indicators_api = IndicatorsApi(api_client)
ops_api = OperationsApi(api_client)

# Submit bulk job
bulk_request = BulkRequest(
    indicators=["8.8.8.8", "1.1.1.1", "example.com"],
    include=["basic", "reputation"]
)
job_response = indicators_api.bulk_enrichment(bulk_request)

# Poll for completion
while True:
    job = ops_api.get_job(job_response.job_id)
    print(f"Status: {job.status}, Progress: {job.progress.percentage}%")

    if job.status in ["completed", "failed"]:
        break

    time.sleep(2)

# Get results
if job.status == "completed":
    results = job.result
    print(f"Processed {len(results)} indicators")
```

### Type Hints & IDE Support

The SDK is fully typed for excellent IDE support:

```python
from whisper_api_sdk.api import IndicatorsApi
from whisper_api_sdk.models import IndicatorResponse, LocationResponse

def enrich_ip(api: IndicatorsApi, ip: str) -> IndicatorResponse:
    """Enrich an IP address with full type hints."""
    response: IndicatorResponse = api.get_indicator("ip", ip)

    # IDE autocomplete works perfectly
    if response.reputation and response.reputation.risk_score:
        risk = response.reputation.risk_score
        print(f"Risk score: {risk}")

    return response
```

---

## 📚 External Documentation

For detailed API documentation, visit:
- **Website**: [whisper.security](https://www.whisper.security)
- **Full Documentation**: [docs.whisper.security](https://docs.whisper.security)
- **API Reference**: [developer.whisper.security](https://developer.whisper.security)
- **API Playground**: [dash.whisper.security/playground](https://dash.whisper.security/playground)
- **Quick Start Guide**: [docs.whisper.security/quickstart](https://docs.whisper.security/quickstart)

---

## 📊 Rate Limits

| Category | Limit |
|----------|-------|
| Standard Enrichment | 100 req/min |
| Bulk Operations | 10 req/min |
| Search/Discovery | 5 req/min |
| Screenshots | 10 req/min |

Rate limits return HTTP 429. Retry after the time specified in the `Retry-After` header.

---

## 🆘 Support

- **Email**: [support@whisper.security](mailto:support@whisper.security)
- **Website**: [whisper.security](https://www.whisper.security)
- **Documentation**: [docs.whisper.security](https://docs.whisper.security)
- **Contact Us**: [whisper.security/contactus](https://www.whisper.security/contactus)
- **Issues**: https://github.com/whisper-sec/sdk-python/issues

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

*Generated with ❤️ by Whisper Security*
