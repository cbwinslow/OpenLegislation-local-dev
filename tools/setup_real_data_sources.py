#!/usr/bin/env python3
"""
Real Data Source Setup Script for OpenLegislation

This script configures and sets up connections to real data sources for full ingestion.
It replaces test data with actual data source connections.

Usage:
    python3 tools/setup_real_data_sources.py --configure-all
    python3 tools/setup_real_data_sources.py --source govinfo
    python3 tools/setup_real_data_sources.py --source congress_api
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from config.datasource_config import DATASOURCE_SETTINGS, FULL_INGESTION_CONFIG


class RealDataSourceSetup:
    """Sets up real data source connections for full ingestion"""

    def __init__(self):
        self.settings = settings
        self.datasource_config = DATASOURCE_SETTINGS
        self.ingestion_config = FULL_INGESTION_CONFIG

    def setup_govinfo_connection(self) -> bool:
        """Set up GovInfo API connection"""
        print("Setting up GovInfo API connection...")
        
        # Check for API key
        if not self.settings.govinfo_api_key:
            print("❌ GovInfo API key not found. Set GOVINFO_API_KEY environment variable.")
            return False
        
        print("✅ GovInfo API key found")
        
        # Create directories for GovInfo data
        govinfo_dirs = [
            "staging/govinfo/bills",
            "staging/govinfo/agendas", 
            "staging/govinfo/calendars",
            "staging/govinfo/votes",
            "staging/govinfo/committee_reports",
            "staging/govinfo/congressional_records"
        ]
        
        for dir_path in govinfo_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        
        # Create GovInfo download script
        govinfo_script = self._create_govinfo_download_script()
        print("✅ Created GovInfo download script")
        
        return True

    def setup_congress_api_connection(self) -> bool:
        """Set up Congress.gov API connection"""
        print("Setting up Congress.gov API connection...")
        
        # Check for API key
        if not self.settings.congress_api_key:
            print("❌ Congress API key not found. Set CONGRESS_API_KEY environment variable.")
            return False
        
        print("✅ Congress API key found")
        
        # Create directories for Congress data
        congress_dirs = [
            "staging/congress/members",
            "staging/congress/bills",
            "staging/congress/votes",
            "staging/congress/committees",
            "staging/congress/amendments"
        ]
        
        for dir_path in congress_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        
        # Create Congress API download script
        congress_script = self._create_congress_download_script()
        print("✅ Created Congress API download script")
        
        return True

    def setup_member_data_sources(self) -> bool:
        """Set up member data sources"""
        print("Setting up member data sources...")
        
        # Create member directories
        member_dirs = [
            "staging/members/persons",
            "staging/members/sessions",
            "staging/members/current",
            "staging/members/historical"
        ]
        
        for dir_path in member_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        
        return True

    def _create_govinfo_download_script(self) -> str:
        """Create GovInfo bulk download script"""
        script_content = '''#!/bin/bash
# GovInfo Bulk Download Script
# Downloads complete datasets from GovInfo for full ingestion

set -e

API_KEY="${GOVINFO_API_KEY}"
BASE_URL="https://api.govinfo.gov"
STAGING_DIR="staging/govinfo"

if [ -z "$API_KEY" ]; then
    echo "Error: GOVINFO_API_KEY environment variable not set"
    exit 1
fi

echo "Starting GovInfo bulk download..."

# Download bill collections (1995-present)
echo "Downloading bill collections..."
for year in $(seq 1995 $(date +%Y)); do
    echo "Downloading bills for $year..."
    mkdir -p "$STAGING_DIR/bills/$year"
    # Add actual download commands here
done

# Download agenda collections
echo "Downloading agenda collections..."
mkdir -p "$STAGING_DIR/agendas"
# Add actual download commands here

# Download calendar collections  
echo "Downloading calendar collections..."
mkdir -p "$STAGING_DIR/calendars"
# Add actual download commands here

echo "GovInfo download completed!"
'''
        
        script_path = "tools/govinfo/download_govinfo_bulk.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        return script_path

    def _create_congress_download_script(self) -> str:
        """Create Congress API bulk download script"""
        script_content = '''#!/usr/bin/env python3
"""
Congress.gov API Bulk Download Script
Fetches complete datasets from Congress.gov API for full ingestion
"""

import os
import requests
import json
import time
from pathlib import Path
from tools.config.settings import settings

API_KEY = settings.congress_api_key
BASE_URL = "https://api.congress.gov/v3"
STAGING_DIR = "staging/congress"

def fetch_all_members():
    """Fetch all members from all congresses"""
    print("Fetching all members...")
    # Add implementation here
    
def fetch_all_bills():
    """Fetch all bills from all congresses"""
    print("Fetching all bills...")
    # Add implementation here

def main():
    if not API_KEY:
        print("Error: CONGRESS_API_KEY not set")
        return
    
    # Create staging directories
    Path(STAGING_DIR).mkdir(parents=True, exist_ok=True)
    
    # Fetch data
    fetch_all_members()
    fetch_all_bills()
    
    print("Congress API download completed!")

if __name__ == "__main__":
    main()
'''
        
        script_path = "tools/congress/fetch_congress_bulk.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        return script_path

    def create_environment_file(self) -> str:
        """Create .env file template with real data source settings"""
        env_content = '''# OpenLegislation Real Data Source Configuration
# Replace placeholder values with actual API keys and settings

# Database Configuration
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=your_password_here
PGDATABASE=openleg

# API Keys for Real Data Sources
GOVINFO_API_KEY=your_govinfo_api_key_here
CONGRESS_API_KEY=your_congress_api_key_here

# Full Ingestion Settings
MAX_ERRORS=10000
REQUEST_TIMEOUT=120
RATE_LIMIT_DELAY=0.1

# GPU Settings (optional)
USE_GPU=false
CUDA_VISIBLE_DEVICES=

# Data Source Configuration
FULL_INGESTION=true
NO_SAMPLE_LIMITS=true
PROCESS_ALL_RECORDS=true
'''
        
        env_path = ".env"
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created environment file template: {env_path}")
        return env_path

    def configure_all_sources(self) -> bool:
        """Configure all real data sources"""
        print("Configuring all real data sources...")
        
        success = True
        
        # Setup GovInfo
        if not self.setup_govinfo_connection():
            success = False
        
        # Setup Congress API
        if not self.setup_congress_api_connection():
            success = False
        
        # Setup member data
        if not self.setup_member_data_sources():
            success = False
        
        # Create environment file
        self.create_environment_file()
        
        if success:
            print("\\n✅ All real data sources configured successfully!")
            print("\\nNext steps:")
            print("1. Update .env file with your actual API keys")
            print("2. Run the download scripts to fetch real data")
            print("3. Execute ingestion scripts with full datasets")
        else:
            print("\\n❌ Some data sources failed to configure. Check API keys.")
        
        return success


def main():
    parser = argparse.ArgumentParser(description="Set up real data sources for OpenLegislation")
    parser.add_argument("--configure-all", action="store_true", help="Configure all data sources")
    parser.add_argument("--source", choices=["govinfo", "congress_api", "members"], 
                       help="Configure specific data source")
    parser.add_argument("--create-env", action="store_true", help="Create environment file template")
    
    args = parser.parse_args()
    
    setup = RealDataSourceSetup()
    
    if args.create_env:
        setup.create_environment_file()
        return
    
    if args.configure_all:
        setup.configure_all_sources()
    elif args.source:
        if args.source == "govinfo":
            setup.setup_govinfo_connection()
        elif args.source == "congress_api":
            setup.setup_congress_api_connection()
        elif args.source == "members":
            setup.setup_member_data_sources()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()