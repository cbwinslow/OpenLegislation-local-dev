# Data Ingestion Web Platform

This is the Next.js-based web interface for managing the OpenLegislation data ingestion platform.

## Features

- **Data Ingestion Management**: Trigger and monitor data ingestion from various sources (Congress.gov, GovInfo, OpenStates)
- **Parameter-based Filtering**: Download datasets filtered by dates, bill numbers, congress numbers, states, and more
- **Data Viewer**: Browse and filter ingested data from the database
- **Real-time Monitoring**: Track ingestion progress and view logs
- **AI-Enhanced Processing**: Optional AI RAG and vectorization features

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for ingestion scripts)
- PostgreSQL database (optional for data viewing)

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables (optional)
cp .env.example .env
# Edit .env with your database credentials
```

### Development

```bash
# Run the development server
npm run dev

# Open http://localhost:3000 in your browser
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

Create a `.env.local` file with the following variables:

```
# Database configuration (optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=openleg
DB_USER=postgres
DB_PASSWORD=your_password

# API Keys (optional)
CONGRESS_API_KEY=your_congress_api_key
OPENSTATES_API_KEY=your_openstates_api_key
```

## Usage

### Triggering Ingestion

1. Navigate to the "Ingestion" tab
2. Select data sources and types to ingest
3. Configure parameters (congress number, dates, batch size, etc.)
4. Click "Start AI Ingestion" to begin

### Viewing Data

1. Navigate to the "Database" tab
2. Select a table to query
3. Apply filters (congress number, state, dates, text search)
4. Execute the query to view results

### SQL Query Builder

1. Click "SQL Writer" button
2. Enter a natural language query description
3. Generate SQL with AI assistance (simulated)
4. Execute the generated query

## API Routes

The platform provides the following API endpoints:

- `POST /api/ingest` - Trigger a new ingestion job
- `GET /api/ingest?jobId=<id>` - Get job status
- `GET /api/data?table=<name>&filters...` - Query ingested data
- `GET /api/logs` - Fetch ingestion logs

## Architecture

- **Frontend**: Next.js 14 with React and TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Database**: PostgreSQL (via pg library)
- **Ingestion Scripts**: Python scripts in `../tools/`

## Development Notes

- The platform currently simulates AI features (RAG, vectorization) for demonstration
- Database connectivity is optional - the UI works without a database connection
- Ingestion jobs are spawned as detached Python processes
- Job status tracking can be enhanced with a proper job queue (e.g., Bull, Redis)

## Integration with Existing Tools

The web platform integrates with existing Python ingestion scripts:

- `tools/ingest_congress_api.py` - Congress.gov API ingestion
- `tools/govinfo_bill_ingestion.py` - GovInfo XML ingestion
- `tools/fetch_govinfo_bulk.py` - Bulk data fetching
- And more...

## Future Enhancements

- Real-time WebSocket updates for job progress
- Advanced SQL query builder with syntax highlighting
- Data export functionality (CSV, JSON)
- Enhanced AI RAG integration
- Multi-user support with authentication
- Job scheduling and automation
