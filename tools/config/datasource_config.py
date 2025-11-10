# Data Source Configuration for Full Ingestion
# This file contains configuration for connecting to real data sources

# GovInfo API Configuration
GOVINFO_API_BASE_URL = "https://api.govinfo.gov"
GOVINFO_DATA_PACKAGE_BASE_URL = "https://www.govinfo.gov/content/pkg"

# Congress.gov API Configuration  
CONGRESS_API_BASE_URL = "https://api.congress.gov/v3"

# Default data directories for full ingestion
STAGING_BASE_DIR = "/home/cbwinslow/OpenLegislation-local-dev/staging"
GOVINFO_STAGING_DIR = f"{STAGING_BASE_DIR}/govinfo"
MEMBERS_STAGING_DIR = f"{STAGING_BASE_DIR}/members"

# Ingestion configuration for full datasets
FULL_INGESTION_CONFIG = {
    "process_all_records": True,
    "no_sample_limits": True,
    "batch_size": 1000,
    "max_retries": 5,
    "enable_parallel_processing": True,
    "continue_on_error": True
}

# Data source specific settings
DATASOURCE_SETTINGS = {
    "govinfo": {
        "download_all_packages": True,
        "include_historical": True,
        "start_year": 1995,  # GovInfo start date
        "end_year": None,    # Current
        "package_types": ["BILLS", "CRPT", "CREC", "GAO", "HOB", "HSD", "STATUTE"]
    },
    "congress_api": {
        "fetch_all_congresses": True,
        "start_congress": 104,  # 1995-1996
        "end_congress": None,   # Current
        "include_members": True,
        "include_bills": True,
        "include_votes": True,
        "include_committees": True
    },
    "members": {
        "include_historical": True,
        "update_current": True,
        "fetch_all_sessions": True
    }
}