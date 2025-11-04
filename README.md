OpenLegislation
====================

`From the New York State Senate`

Dual BSD/GPL License. See the NYSenate licensing page http://www.nysenate.gov/Open-Source-Software-Licenses.

Open Legislation is an open source web service developed in-house by the New York State Senate to provide access to NYS legislative data including bills, resolutions, and laws. Developers can request a free key for the JSON API at http://legislation.nysenate.gov/. The JSON API is documented at http://legislation.nysenate.gov/static/docs/html/.

Updates to legislative data are distributed by the Legislative Bill drafting Commission (LBDC) in a raw, plain text format. Open Legislation parses the updates in real time and redistributes the data through the JSON API for integration with various web applications. It is developed and run using several open-source technologies and frameworks including:

* Java 17
* Spring 5 Framework
* PostgreSQL
* Elasticsearch 8
* React
* Tomcat 9

![Bill page demo](https://raw.githubusercontent.com/nysenate/OpenLegislation/dev/src/main/webapp/static/img/bill-page.png)

## 🤖 PR Automation

This repository includes comprehensive automated PR management:

### GitHub Actions (Built-in)
- Auto-merges safe Dependabot updates
- Provides automated code review feedback
- Automatically labels and categorizes PRs
- Generates weekly PR dashboards
- Manages stale PRs

**📚 [Learn More](docs/pr-automation-README.md)** | **🚀 [Setup Guide](docs/pr-automation-setup.md)**

### AI Webhook Server (Self-hosted)
New! Deploy your own AI-powered code review webhook server:
- Uses OpenRouter AI agents (Claude, GPT-4, etc.) for intelligent code review
- Provides detailed analysis: security, bugs, style, performance
- Auto-merge capability based on AI review scores
- Designed for homelab deployment with Docker

**🚀 [Webhook Server Guide](webhook-server/README.md)** | **⚙️ [Setup Instructions](webhook-server/SETUP.md)**

Current Senate Developers
---------------------------

* Kevin Caseiras <caseiras@nysenate.gov>
* Ken Zalewski <zalewski@nysenate.gov>
* Anthony Calabrese <calabres@nysenate.gov>
* Jacob Keegan <keegan@nysenate.gov>

Past Developers
--------------------

* Nathan Freitas <nathanfreitas@gmail.com>
* Jared Williams <jared.mi.williams@gmail.com>
* Graylin Kim <kim@nysenate.gov>
* Ash Islam <islam@nysenate.gov>
* Sam Stouffer <stouffer@nysenate.gov>
