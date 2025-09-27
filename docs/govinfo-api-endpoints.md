# GovInfo API Endpoints & Reverse Engineering

## Base URL
- https://api.govinfo.gov (REST JSON API)

## Key Endpoints (Tested with curl -H "User-Agent: OpenLegislation/1.0")
- **GET /v1/collections?api_key={key}**: List all collections (BILLS, BILLSTATUS, FR, CFR, CREC, etc.). Response: {"collections": [{"name": "BILLS", "description": "Bill Text", "formats": ["XML", "PDF", "TXT"], "years": [113-119]}]}.
- **GET /v1/collections/{collection}?api_key={key}**: Details for one (e.g., /BILLS → years, formats).
- **GET /v1/search?q={term}&collection={collection}&api_key={key}**: Search (e.g., q="HR 1" collection=BILLS → hits with title, url, metadata).
- **GET /v1/package/{pkgid}?api_key={key}**: Retrieve full package (e.g., /GOVDOC-2025-1 → {"package": {"documents": [{"format": "XML", "text": "Bill text"}]}}).
- **GET /v1/links?q={query}&collection={collection}&api_key={key}**: Related docs (e.g., q=congress=119 collection=BILLS → status/summaries).
- **GET /v1/rss/collections/{collection}**: RSS for new items (no key).
- **GET /sitemaps/collections/{collection}.xml**: Sitemap for crawling (no key).

## Rate Limits
- 1000 calls/day free key.
- Pagination: ?offset=0&limit=50.

## Sample Responses (Public Metadata, No Key)
- Collections: [{"name": "BILLS", "description": "Congressional bills", "years": [113,114,...]}].
- Search BILLS: {"search": {"results": [{"title": "H.R.1 - For the People Act", "pkgid": "GOVDOC-2025-1", "metadata": {"congress": 119}}]}}.

## Usage in Java
Use RestTemplate with ?api_key=${GOVINFO_API_KEY} from .env.

Test: curl "https://api.govinfo.gov/v1/collections/BILLS" (metadata only).
