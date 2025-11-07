# GitHub Wiki Automation Guide

This guide explains how to create and manage GitHub Wiki pages for the OpenLegislation repository.

## Overview

GitHub Wikis provide a space for project documentation, guides, and reference materials. While the GitHub API doesn't directly support wiki operations, you can manage wikis through Git operations.

## Quick Setup

### 1. Clone the Wiki Repository

```bash
# Clone the wiki (separate from main repo)
git clone https://github.com/cbwinslow/OpenLegislation-local-dev.wiki.git
cd OpenLegislation-local-dev.wiki
```

### 2. Create Wiki Pages

Wiki pages are Markdown files:

```bash
# Create a new page
echo "# My Wiki Page" > My-Wiki-Page.md
echo "Content goes here" >> My-Wiki-Page.md

# Add and commit
git add My-Wiki-Page.md
git commit -m "Add new wiki page"
git push origin master
```

## Recommended Wiki Structure

### Home Page (`Home.md`)

```markdown
# OpenLegislation Wiki

Welcome to the OpenLegislation documentation wiki!

## Quick Links

- [Getting Started](Getting-Started)
- [API Documentation](API-Documentation)
- [Developer Guide](Developer-Guide)
- [Database Schema](Database-Schema)
- [Federal Data Integration](Federal-Data-Integration)
- [Deployment Guide](Deployment-Guide)

## Resources

- [Main Repository](https://github.com/cbwinslow/OpenLegislation-local-dev)
- [API Documentation](http://legislation.nysenate.gov/static/docs/html/)
- [Issue Tracker](https://github.com/cbwinslow/OpenLegislation-local-dev/issues)

## Contributing

See our [Contributing Guide](Contributing) for details on how to contribute to this project.
```

### Getting Started (`Getting-Started.md`)

```markdown
# Getting Started with OpenLegislation

## Prerequisites

- Java 17+
- Maven 3.9+
- PostgreSQL 15+
- Elasticsearch 8+
- Docker (optional)

## Quick Start

### 1. Clone Repository

\`\`\`bash
git clone https://github.com/cbwinslow/OpenLegislation-local-dev.git
cd OpenLegislation-local-dev
\`\`\`

### 2. Setup Database

\`\`\`bash
# Create database
createdb openlegislation

# Run migrations
mvn flyway:migrate
\`\`\`

### 3. Build and Run

\`\`\`bash
# Build
mvn clean install

# Run
mvn spring-boot:run
\`\`\`

## Next Steps

- [Configuration Guide](Configuration-Guide)
- [API Documentation](API-Documentation)
- [Development Workflow](Development-Workflow)
```

### API Documentation (`API-Documentation.md`)

```markdown
# API Documentation

## Base URL

\`\`\`
https://legislation.nysenate.gov/api/3
\`\`\`

## Authentication

Most endpoints are public. Admin endpoints require authentication:

\`\`\`bash
curl -u admin:password https://legislation.nysenate.gov/api/3/admin/process/run
\`\`\`

## Endpoints

### Bills

#### Get Bill
\`\`\`
GET /api/3/bills/{session}/{billId}
\`\`\`

#### Search Bills
\`\`\`
GET /api/3/bills/search?term=education&limit=10
\`\`\`

### Laws

#### Get Law
\`\`\`
GET /api/3/laws/{lawId}
\`\`\`

### Members

#### List Members
\`\`\`
GET /api/3/members/{sessionYear}
\`\`\`

## Examples

See [API Examples](API-Examples) for detailed examples.
```

### Database Schema (`Database-Schema.md`)

```markdown
# Database Schema

## Core Tables

### Bills
- `master.bill` - Bill master data
- `master.bill_text` - Bill text content
- `master.bill_amendment` - Bill amendments
- `master.bill_sponsor` - Bill sponsors
- `master.bill_vote` - Roll call votes

### Laws
- `master.law_document` - Law documents
- `master.law_tree` - Law hierarchy

### Members
- `public.member` - Legislature members
- `public.session_member` - Member session info

### Calendar
- `master.calendar` - Floor/active calendars
- `master.calendar_entry` - Calendar entries

## Relationships

See ER diagram: [Schema Diagram](Database-Schema-Diagram)

## Migrations

Migrations are in `src/main/resources/sql/migrations/`

Run migrations:
\`\`\`bash
mvn flyway:migrate
\`\`\`
```

### Federal Data Integration (`Federal-Data-Integration.md`)

```markdown
# Federal Data Integration

## Overview

OpenLegislation integrates federal legislative data from:
- Congress.gov API
- GovInfo.gov bulk data

## Data Sources

### Congress.gov
- Bills (HR, S, HJRES, SJRES, etc.)
- Amendments
- Members
- Committees
- Votes

### GovInfo.gov
- Bill status (BILLSTATUS)
- Bill text (BILLS)
- Congressional Record (CREC)
- Federal Register (FR)

## Ingestion Process

### 1. Fetch Data

\`\`\`bash
cd tools
python fetch_govinfo_bulk.py --congress 119 --collection BILLS
\`\`\`

### 2. Process Data

\`\`\`bash
python govinfo_bill_ingestion.py
\`\`\`

### 3. Verify

\`\`\`bash
python validate_ingestion.py
\`\`\`

## Configuration

See [Federal Data Configuration](Federal-Data-Configuration)
```

## Automation Script

Create `tools/create_wiki_pages.sh`:

```bash
#!/bin/bash
# Create standard wiki pages

WIKI_DIR="OpenLegislation-local-dev.wiki"

# Clone wiki if not exists
if [ ! -d "$WIKI_DIR" ]; then
  git clone https://github.com/cbwinslow/OpenLegislation-local-dev.wiki.git
fi

cd "$WIKI_DIR"

# Create pages
cat > Home.md << 'EOF'
# OpenLegislation Wiki

[Content as shown above]
EOF

cat > Getting-Started.md << 'EOF'
# Getting Started with OpenLegislation

[Content as shown above]
EOF

# Add more pages...

# Commit and push
git add *.md
git commit -m "Create standard wiki pages"
git push origin master

echo "Wiki pages created successfully!"
```

## Using the Automation Script

```bash
chmod +x tools/create_wiki_pages.sh
./tools/create_wiki_pages.sh
```

## Python Script for Wiki Management

Create `tools/wiki_manager.py`:

```python
#!/usr/bin/env python3
"""
Wiki Manager for OpenLegislation
Automates creation and updating of wiki pages
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List

class WikiManager:
    def __init__(self, wiki_url: str):
        self.wiki_url = wiki_url
        self.wiki_dir = Path("OpenLegislation-local-dev.wiki")
    
    def clone_wiki(self):
        """Clone the wiki repository"""
        if not self.wiki_dir.exists():
            subprocess.run(["git", "clone", self.wiki_url, str(self.wiki_dir)])
        else:
            # Pull latest changes
            subprocess.run(["git", "pull"], cwd=self.wiki_dir)
    
    def create_page(self, filename: str, content: str):
        """Create a wiki page"""
        filepath = self.wiki_dir / filename
        filepath.write_text(content)
        print(f"✓ Created page: {filename}")
    
    def commit_and_push(self, message: str):
        """Commit and push changes"""
        subprocess.run(["git", "add", "."], cwd=self.wiki_dir)
        subprocess.run(["git", "commit", "-m", message], cwd=self.wiki_dir)
        subprocess.run(["git", "push"], cwd=self.wiki_dir)
        print("✓ Changes pushed to wiki")
    
    def create_standard_pages(self):
        """Create standard wiki structure"""
        pages = {
            "Home.md": self._get_home_content(),
            "Getting-Started.md": self._get_getting_started_content(),
            "API-Documentation.md": self._get_api_docs_content(),
            # Add more pages...
        }
        
        for filename, content in pages.items():
            self.create_page(filename, content)
        
        self.commit_and_push("Create standard wiki pages")
    
    def _get_home_content(self) -> str:
        return """# OpenLegislation Wiki

Welcome to the OpenLegislation documentation wiki!

[Add full content here]
"""
    
    def _get_getting_started_content(self) -> str:
        return """# Getting Started

[Add full content here]
"""
    
    def _get_api_docs_content(self) -> str:
        return """# API Documentation

[Add full content here]
"""

def main():
    wiki_url = "https://github.com/cbwinslow/OpenLegislation-local-dev.wiki.git"
    manager = WikiManager(wiki_url)
    
    print("Cloning wiki repository...")
    manager.clone_wiki()
    
    print("Creating standard pages...")
    manager.create_standard_pages()
    
    print("✓ Wiki setup complete!")

if __name__ == "__main__":
    main()
```

## Usage

```bash
# Make executable
chmod +x tools/wiki_manager.py

# Run
python3 tools/wiki_manager.py
```

## Best Practices

1. **Keep it organized**: Use clear page names and hierarchy
2. **Link extensively**: Cross-reference related pages
3. **Update regularly**: Keep wiki in sync with code
4. **Use templates**: Create templates for common page types
5. **Include examples**: Provide code examples and use cases
6. **Version control**: Commit wiki changes with meaningful messages

## Wiki Maintenance

### Update Existing Page

```bash
cd OpenLegislation-local-dev.wiki
# Edit page
vim Getting-Started.md
# Commit
git add Getting-Started.md
git commit -m "Update getting started guide"
git push
```

### Delete Page

```bash
cd OpenLegislation-local-dev.wiki
git rm Obsolete-Page.md
git commit -m "Remove obsolete page"
git push
```

### Rename Page

```bash
cd OpenLegislation-local-dev.wiki
git mv Old-Name.md New-Name.md
git commit -m "Rename page"
git push
```

## Automated Updates

You can automate wiki updates in GitHub Actions:

```yaml
name: Update Wiki
on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
jobs:
  update-wiki:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Update wiki
      run: |
        git clone https://github.com/cbwinslow/OpenLegislation-local-dev.wiki.git
        cd OpenLegislation-local-dev.wiki
        # Copy docs to wiki
        cp ../docs/API-Guide.md API-Documentation.md
        git add .
        git commit -m "Sync from main repo" || exit 0
        git push
```

## Resources

- [GitHub Wiki Documentation](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [Markdown Guide](https://www.markdownguide.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

---

For questions or issues, create an issue in the main repository.
