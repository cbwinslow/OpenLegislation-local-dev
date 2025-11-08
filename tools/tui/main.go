package main

import (
	"fmt"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Model represents the state of the TUI
type model struct {
	width          int
	height         int
	ready          bool
	currentView    view
	dataSources    []dataSource
	selectedSource int
	loading        bool
	errorMessage   string
	parameterForm  parameterForm
}

type view int

const (
	mainMenu view = iota
	dataSourceList
	parameterConfig
)

// Data source configuration
type dataSource struct {
	id             string
	name           string
	description    string
	scriptPath     string
	defaultParams  map[string]string
	optionalParams []string
	paramHelp      map[string]string
	enabled        bool
}

// Parameter form for configuring data sources
type parameterForm struct {
	dataSourceIndex int
	fields          []parameterField
	focused         int
}

type parameterField struct {
	name        string
	value       string
	description string
	isBoolean   bool
}

var (
	// Data sources configuration
	dataSources = []dataSource{
		{
			id:          "congress_api",
			name:        "Congress API",
			description: "Download congressional data from Congress.gov API",
			scriptPath:  "congress_gov.py",
			defaultParams: map[string]string{
				"api-key":     "",
				"start-date":  "2023-01-01",
				"end-date":    "2024-12-31",
				"congress":    "118",
				"bill-types":  "hr,s,hres,sres",
				"limit":       "1000",
				"output-dir":  "./data/congress",
				"batch-size":  "100",
				"rate-limit":  "10",
				"retry-count": "3",
			},
			optionalParams: []string{"api-key", "limit", "output-dir", "batch-size", "rate-limit", "retry-count"},
			paramHelp: map[string]string{
				"api-key":     "Congress.gov API key (leave empty for public access)",
				"start-date":  "Start date for data collection (YYYY-MM-DD)",
				"end-date":    "End date for data collection (YYYY-MM-DD)",
				"congress":    "Congress number (e.g., 118 for 118th Congress)",
				"bill-types":  "Bill types to download (hr,s,hres,sres,hj,sj,hcon,scon)",
				"limit":       "Maximum number of items to download",
				"output-dir":  "Directory to save downloaded data",
				"batch-size":  "Number of items per batch",
				"rate-limit":  "Requests per second",
				"retry-count": "Number of retry attempts",
			},
			enabled: true,
		},
		{
			id:          "federal_members",
			name:        "Federal Members",
			description: "Download information about current federal legislators",
			scriptPath:  "federal_members.py",
			defaultParams: map[string]string{
				"chamber":            "all",
				"session":            "118",
				"output-dir":         "./data/members",
				"include-staff":      "false",
				"include-committees": "true",
				"format":             "json",
			},
			optionalParams: []string{"output-dir", "include-staff", "include-committees", "format"},
			paramHelp: map[string]string{
				"chamber":            "Chamber: house, senate, or all",
				"session":            "Congress session number",
				"output-dir":         "Directory to save member data",
				"include-staff":      "Include staff information",
				"include-committees": "Include committee assignments",
				"format":             "Output format: json, csv, or xml",
			},
			enabled: true,
		},
		{
			id:          "govinfo_bills",
			name:        "GovInfo Bills",
			description: "Download bills from GovInfo.gov",
			scriptPath:  "govinfo_bills.py",
			defaultParams: map[string]string{
				"collection":   "BILLS",
				"start-date":   "2023-01-01",
				"end-date":     "2024-12-31",
				"congress":     "118",
				"bill-type":    "hr",
				"output-dir":   "./data/govinfo",
				"download-pdf": "false",
				"download-xml": "true",
				"batch-size":   "50",
			},
			optionalParams: []string{"output-dir", "download-pdf", "download-xml", "batch-size"},
			paramHelp: map[string]string{
				"collection":   "GovInfo collection name",
				"start-date":   "Start date for bill collection",
				"end-date":     "End date for bill collection",
				"congress":     "Congress number",
				"bill-type":    "Bill type: hr, s, hres, sres, etc.",
				"output-dir":   "Directory to save bill data",
				"download-pdf": "Download PDF versions",
				"download-xml": "Download XML versions",
				"batch-size":   "Number of bills per batch",
			},
			enabled: true,
		},
	}
)

// Styles
var (
	titleStyle    = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("13"))
	selectedStyle = lipgloss.NewStyle().Background(lipgloss.Color("12")).Foreground(lipgloss.Color("15"))
	helpStyle     = lipgloss.NewStyle().Faint(true)
	borderStyle   = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Padding(1)
)

func initialModel() model {
	return model{
		dataSources: dataSources,
		currentView: mainMenu,
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.ready = true
		return m, nil

	case tea.KeyMsg:
		switch m.currentView {
		case mainMenu:
			switch msg.String() {
			case "q", "ctrl+c":
				return m, tea.Quit
			case "1":
				m.currentView = dataSourceList
				return m, nil
			case "2":
				m.currentView = parameterConfig
				return m, nil
			}
		case dataSourceList:
			switch msg.String() {
			case "q", "ctrl+c":
				return m, tea.Quit
			case "esc":
				m.currentView = mainMenu
				return m, nil
			case "up", "k":
				if m.selectedSource > 0 {
					m.selectedSource--
				}
				return m, nil
			case "down", "j":
				if m.selectedSource < len(m.dataSources)-1 {
					m.selectedSource++
				}
				return m, nil
			case "enter":
				m.currentView = parameterConfig
				m.setupParameterForm()
				return m, nil
			}
		case parameterConfig:
			switch msg.String() {
			case "q", "ctrl+c":
				return m, tea.Quit
			case "esc":
				m.currentView = dataSourceList
				return m, nil
			case "up", "k":
				if m.parameterForm.focused > 0 {
					m.parameterForm.focused--
				}
				return m, nil
			case "down", "j":
				if m.parameterForm.focused < len(m.parameterForm.fields)-1 {
					m.parameterForm.focused++
				}
				return m, nil
			case "enter":
				m.runIngestion()
				return m, nil
			}
		}
	}
	return m, nil
}

func (m model) View() string {
	if !m.ready {
		return "Loading..."
	}

	switch m.currentView {
	case mainMenu:
		return m.renderMainMenu()
	case dataSourceList:
		return m.renderDataSourceList()
	case parameterConfig:
		return m.renderParameterConfig()
	default:
		return "Unknown view"
	}
}

func (m model) renderMainMenu() string {
	var content strings.Builder

	content.WriteString(titleStyle.Render("OpenLegislation Ingestion Orchestrator"))
	content.WriteString("\n\n")
	content.WriteString("Select an option:\n\n")
	content.WriteString("1. Data Sources\n")
	content.WriteString("2. Configuration\n\n")
	content.WriteString(helpStyle.Render("Press 1-2 to select, q to quit"))

	return borderStyle.Render(content.String())
}

func (m model) renderDataSourceList() string {
	var content strings.Builder

	content.WriteString(titleStyle.Render("Data Sources"))
	content.WriteString("\n\n")

	for i, ds := range m.dataSources {
		prefix := " "
		if i == m.selectedSource {
			prefix = ">"
			content.WriteString(selectedStyle.Render(fmt.Sprintf("%s %s - %s", prefix, ds.name, ds.description)))
		} else {
			content.WriteString(fmt.Sprintf("%s %s - %s", prefix, ds.name, ds.description))
		}
		content.WriteString("\n")
	}

	content.WriteString("\n")
	content.WriteString(helpStyle.Render("↑↓ Navigate | Enter: Configure | Esc: Back | q: Quit"))

	return borderStyle.Render(content.String())
}

func (m model) renderParameterConfig() string {
	var content strings.Builder

	if m.selectedSource < len(m.dataSources) {
		ds := m.dataSources[m.selectedSource]
		content.WriteString(titleStyle.Render(fmt.Sprintf("Configure: %s", ds.name)))
		content.WriteString("\n\n")

		for i, field := range m.parameterForm.fields {
			prefix := " "
			if i == m.parameterForm.focused {
				prefix = ">"
			}

			content.WriteString(fmt.Sprintf("%s %s: %s", prefix, field.name, field.value))
			if field.description != "" {
				content.WriteString(fmt.Sprintf(" (%s)", field.description))
			}
			content.WriteString("\n")
		}
	}

	content.WriteString("\n")
	content.WriteString(helpStyle.Render("↑↓ Navigate | Enter: Run Ingestion | Esc: Back | q: Quit"))

	return borderStyle.Render(content.String())
}

func (m *model) setupParameterForm() {
	if m.selectedSource >= len(m.dataSources) {
		return
	}

	ds := m.dataSources[m.selectedSource]
	var fields []parameterField

	// Add all parameters from defaultParams
	for name, value := range ds.defaultParams {
		fields = append(fields, parameterField{
			name:        name,
			value:       value,
			description: ds.paramHelp[name],
			isBoolean:   strings.ToLower(value) == "true" || strings.ToLower(value) == "false",
		})
	}

	m.parameterForm = parameterForm{
		dataSourceIndex: m.selectedSource,
		fields:          fields,
		focused:         0,
	}
}

func (m *model) runIngestion() {
	if m.selectedSource >= len(m.dataSources) {
		return
	}

	ds := m.dataSources[m.selectedSource]

	// Build command arguments
	var args []string
	args = append(args, ds.scriptPath, "--dry-run")

	// Add parameters
	for _, field := range m.parameterForm.fields {
		if field.value != "" {
			args = append(args, "--"+field.name, field.value)
		}
	}

	fmt.Printf("Would run: python3 %s\n", strings.Join(args, " "))
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error: %v", err)
		os.Exit(1)
	}
}
