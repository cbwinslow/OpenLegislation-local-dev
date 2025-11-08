# OpenLegislation Ingestion TUI

A terminal user interface for managing OpenLegislation data ingestion processes built with Go and Bubbletea.

## Features

- **Data Source Management**: Configure and run all 8 ingestion sources
- **Parameter Configuration**: Dynamic forms for each data source
- **Safety First**: Always includes `--dry-run` flag for safety
- **No Restrictive Defaults**: All parameters are configurable without limiting data downloads
- **Rich Interface**: Beautiful terminal UI using Lipgloss styling
- **Keyboard Navigation**: Intuitive keyboard shortcuts and navigation

## Data Sources

1. **Congress API** - Download congressional data from Congress.gov API
2. **Federal Members** - Download information about current federal legislators  
3. **GovInfo Bills** - Download bills from GovInfo.gov
4. **Additional sources** - (Extendable framework for more sources)

## Installation

### Prerequisites

- Go 1.22 or later
- Python 3.8+ (for the ingestion scripts)

### Build from Source

```bash
cd tools/tui
go mod tidy
go build -o ingestion-tui .
```

### Usage

```bash
./ingestion-tui
```

## Navigation

### Main Menu
- `1` - Data Sources
- `2` - Configuration  
- `q` or `Ctrl+C` - Quit

### Data Source List
- `↑/k` - Move up
- `↓/j` - Move down
- `Enter` - Configure selected source
- `Esc` - Back to main menu
- `q` - Quit

### Parameter Configuration
- `↑/k` - Move to previous parameter
- `↓/j` - Move to next parameter
- `Enter` - Run ingestion with current parameters
- `Esc` - Back to data source list
- `q` - Quit

## Safety Features

- **Dry Run Mode**: All executions include `--dry-run` flag by default
- **Parameter Validation**: Help text for all parameters
- **Non-Destructive**: Safe to explore without making changes

## Configuration

Each data source has configurable parameters:

### Congress API
- `api-key`: Congress.gov API key (optional for public access)
- `start-date`: Start date for data collection (YYYY-MM-DD)
- `end-date`: End date for data collection (YYYY-MM-DD)
- `congress`: Congress number (e.g., 118)
- `bill-types`: Bill types to download (hr,s,hres,sres)
- `limit`: Maximum number of items to download
- `output-dir`: Directory to save downloaded data
- `batch-size`: Number of items per batch
- `rate-limit`: Requests per second
- `retry-count`: Number of retry attempts

### Federal Members
- `chamber`: Chamber (house, senate, or all)
- `session`: Congress session number
- `output-dir`: Directory to save member data
- `include-staff`: Include staff information
- `include-committees`: Include committee assignments
- `format`: Output format (json, csv, or xml)

### GovInfo Bills
- `collection`: GovInfo collection name
- `start-date`: Start date for bill collection
- `end-date`: End date for bill collection
- `congress`: Congress number
- `bill-type`: Bill type (hr, s, hres, sres, etc.)
- `output-dir`: Directory to save bill data
- `download-pdf`: Download PDF versions
- `download-xml`: Download XML versions
- `batch-size`: Number of bills per batch

## Integration with Python Orchestrator

The TUI integrates with the existing Python ingestion orchestrator by:

1. Building command-line arguments based on configured parameters
2. Executing Python scripts with appropriate flags
3. Providing a user-friendly interface for parameter management
4. Maintaining safety with dry-run mode

## Development

### Project Structure

```
tools/tui/
├── main.go          # Main TUI application
├── go.mod           # Go module definition
├── go.sum           # Go dependencies checksum
├── ingestion-tui    # Compiled binary
└── README.md        # This file
```

### Dependencies

- `github.com/charmbracelet/bubbletea` - TUI framework
- `github.com/charmbracelet/lipgloss` - Styling library

### Adding New Data Sources

1. Add the data source configuration to the `dataSources` slice in `main.go`
2. Define `defaultParams`, `optionalParams`, and `paramHelp`
3. The TUI will automatically generate the configuration interface

## Troubleshooting

### Build Issues

Ensure you have Go 1.22+ installed:
```bash
go version
```

### Runtime Issues

Check that Python 3.8+ is available for the ingestion scripts:
```bash
python3 --version
```

### Terminal Compatibility

The TUI works best with modern terminals that support:
- ANSI colors
- Unicode characters
- Alternative screen buffer

## License

This project is part of the OpenLegislation platform.