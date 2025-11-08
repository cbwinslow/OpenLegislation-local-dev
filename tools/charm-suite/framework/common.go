package framework

import (
	"fmt"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/bubbles/viewport"
	"github.com/charmbracelet/lipgloss"
)

// Common styles that can be used across all applications
var (
	// Base colors
	PrimaryColor   = lipgloss.Color("69")
	SecondaryColor = lipgloss.Color("99")
	AccentColor    = lipgloss.Color("212")
	SuccessColor   = lipgloss.Color("42")
	WarningColor   = lipgloss.Color("208")
	ErrorColor     = lipgloss.Color("196")
	MutedColor     = lipgloss.Color("245")

	// Style definitions
	TitleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(PrimaryColor).
			Background(lipgloss.Color("236")).
			Padding(0, 1).
			MarginBottom(1)

	SubtitleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(SecondaryColor).
			MarginBottom(1)

	BorderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(PrimaryColor).
			Padding(1, 2)

	SelectedStyle = lipgloss.NewStyle().
			Background(PrimaryColor).
			Foreground(lipgloss.Color("15")).
			Bold(true)

	DisabledStyle = lipgloss.NewStyle().
			Foreground(MutedColor).
			Strikethrough(true)

	SuccessStyle = lipgloss.NewStyle().
			Foreground(SuccessColor).
			Bold(true)

	WarningStyle = lipgloss.NewStyle().
			Foreground(WarningColor).
			Bold(true)

	ErrorStyle = lipgloss.NewStyle().
			Foreground(ErrorColor).
			Bold(true)

	HelpStyle = lipgloss.NewStyle().
			Foreground(MutedColor).
			Italic(true)

	CodeStyle = lipgloss.NewStyle().
			Background(lipgloss.Color("236")).
			Foreground(lipgloss.Color("15")).
			Padding(0, 1)

	KeywordStyle = lipgloss.NewStyle().
			Foreground(AccentColor).
			Bold(true)

	ValueStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("15"))

	ProgressStyle = lipgloss.NewStyle().
			Background(PrimaryColor).
			Width(20)
)

// Theme represents a color theme for the applications
type Theme struct {
	Name       string
	Primary    lipgloss.Color
	Secondary  lipgloss.Color
	Accent     lipgloss.Color
	Success    lipgloss.Color
	Warning    lipgloss.Color
	Error      lipgloss.Color
	Muted      lipgloss.Color
	Background lipgloss.Color
	Foreground lipgloss.Color
}

// Predefined themes
var Themes = map[string]Theme{
	"dark": {
		Name:       "Dark",
		Primary:    lipgloss.Color("69"),
		Secondary:  lipgloss.Color("99"),
		Accent:     lipgloss.Color("212"),
		Success:    lipgloss.Color("42"),
		Warning:    lipgloss.Color("208"),
		Error:      lipgloss.Color("196"),
		Muted:      lipgloss.Color("245"),
		Background: lipgloss.Color("236"),
		Foreground: lipgloss.Color("15"),
	},
	"light": {
		Name:       "Light",
		Primary:    lipgloss.Color("26"),
		Secondary:  lipgloss.Color("61"),
		Accent:     lipgloss.Color("92"),
		Success:    lipgloss.Color("28"),
		Warning:    lipgloss.Color("172"),
		Error:      lipgloss.Color("124"),
		Muted:      lipgloss.Color("244"),
		Background: lipgloss.Color("15"),
		Foreground: lipgloss.Color("16"),
	},
	"ocean": {
		Name:       "Ocean",
		Primary:    lipgloss.Color("38"),
		Secondary:  lipgloss.Color("73"),
		Accent:     lipgloss.Color("80"),
		Success:    lipgloss.Color("43"),
		Warning:    lipgloss.Color("178"),
		Error:      lipgloss.Color("167"),
		Muted:      lipgloss.Color("242"),
		Background: lipgloss.Color("233"),
		Foreground: lipgloss.Color("15"),
	},
	"forest": {
		Name:       "Forest",
		Primary:    lipgloss.Color("28"),
		Secondary:  lipgloss.Color("64"),
		Accent:     lipgloss.Color("70"),
		Success:    lipgloss.Color("34"),
		Warning:    lipgloss.Color("130"),
		Error:      lipgloss.Color("124"),
		Muted:      lipgloss.Color("240"),
		Background: lipgloss.Color("235"),
		Foreground: lipgloss.Color("15"),
	},
}

// SetTheme updates the global styles based on the selected theme
func SetTheme(theme Theme) {
	PrimaryColor = theme.Primary
	SecondaryColor = theme.Secondary
	AccentColor = theme.Accent
	SuccessColor = theme.Success
	WarningColor = theme.Warning
	ErrorColor = theme.Error
	MutedColor = theme.Muted

	// Update style definitions
	TitleStyle = TitleStyle.Foreground(theme.Primary).Background(theme.Background)
	SubtitleStyle = SubtitleStyle.Foreground(theme.Secondary)
	BorderStyle = BorderStyle.BorderForeground(theme.Primary)
	SelectedStyle = SelectedStyle.Background(theme.Primary)
	SuccessStyle = SuccessStyle.Foreground(theme.Success)
	WarningStyle = WarningStyle.Foreground(theme.Warning)
	ErrorStyle = ErrorStyle.Foreground(theme.Error)
	HelpStyle = HelpStyle.Foreground(theme.Muted)
	CodeStyle = CodeStyle.Background(theme.Background).Foreground(theme.Foreground)
	KeywordStyle = KeywordStyle.Foreground(theme.Accent)
	ValueStyle = ValueStyle.Foreground(theme.Foreground)
	ProgressStyle = ProgressStyle.Background(theme.Primary)
}

// Base model that all applications can embed
type BaseModel struct {
	Width      int
	Height     int
	Ready      bool
	Theme      string
	Loading    bool
	Error      string
	LastUpdate time.Time
}

// Common message types
type (
	ShowErrorMsg   string
	ClearErrorMsg  struct{}
	ShowLoadingMsg struct{}
	HideLoadingMsg struct{}
	ThemeChangeMsg string
	QuitMsg        struct{}
)

// Common utility functions
func TruncateText(text string, maxLen int) string {
	if len(text) <= maxLen {
		return text
	}
	if maxLen <= 3 {
		return text[:maxLen]
	}
	return text[:maxLen-3] + "..."
}

func FormatTime(t time.Time) string {
	if t.IsZero() {
		return "Never"
	}
	return t.Format("2006-01-02 15:04:05")
}

func FormatDuration(d time.Duration) string {
	if d < time.Second {
		return fmt.Sprintf("%dms", d.Milliseconds())
	} else if d < time.Minute {
		return fmt.Sprintf("%.1fs", d.Seconds())
	} else if d < time.Hour {
		return fmt.Sprintf("%.1fm", d.Minutes())
	} else {
		return fmt.Sprintf("%.1fh", d.Hours())
	}
}

func CreateTextInput(placeholder string, focused bool) textinput.Model {
	ti := textinput.New()
	ti.Placeholder = placeholder
	ti.Focus()
	if focused {
		ti.TextStyle = lipgloss.NewStyle().Foreground(PrimaryColor)
		ti.PlaceholderStyle = lipgloss.NewStyle().Foreground(MutedColor)
	}
	return ti
}

func CreateViewport(width, height int) viewport.Model {
	vp := viewport.New(width, height)
	vp.Style = lipgloss.NewStyle()
	return vp
}

// Progress bar rendering
func RenderProgressBar(current, total int, width int) string {
	if total == 0 {
		return strings.Repeat("░", width)
	}

	filled := int(float64(current) / float64(total) * float64(width))
	if filled > width {
		filled = width
	}

	return strings.Repeat("█", filled) + strings.Repeat("░", width-filled)
}

// Status indicator rendering
func RenderStatus(status string, active bool) string {
	var color lipgloss.Color
	var symbol string

	switch strings.ToLower(status) {
	case "running", "active", "online":
		color = SuccessColor
		symbol = "●"
	case "stopped", "inactive", "offline":
		color = MutedColor
		symbol = "○"
	case "error", "failed", "critical":
		color = ErrorColor
		symbol = "✗"
	case "warning", "pending":
		color = WarningColor
		symbol = "⚠"
	default:
		color = MutedColor
		symbol = "○"
	}

	if !active {
		color = MutedColor
	}

	return lipgloss.NewStyle().
		Foreground(color).
		Bold(true).
		Render(symbol + " " + status)
}

// Keyboard shortcuts help
type Shortcut struct {
	Key         string
	Description string
	Action      string
}

func RenderHelpBar(shortcuts []Shortcut) string {
	var parts []string
	for _, sc := range shortcuts {
		key := CodeStyle.Render(sc.Key)
		desc := HelpStyle.Render(sc.Description)
		parts = append(parts, fmt.Sprintf("%s %s", key, desc))
	}

	return lipgloss.NewStyle().
		Background(lipgloss.Color("236")).
		Foreground(MutedColor).
		Padding(0, 1).
		Render(strings.Join(parts, " • "))
}

// Confirmation dialog
type ConfirmDialog struct {
	Title     string
	Message   string
	OnConfirm func()
	OnCancel  func()
	Active    bool
}

func (cd ConfirmDialog) Render() string {
	if !cd.Active {
		return ""
	}

	content := lipgloss.NewStyle().
		Background(lipgloss.Color("236")).
		Foreground(lipgloss.Color("15")).
		Padding(1, 2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(PrimaryColor).
		Render(
			TitleStyle.Render(cd.Title) + "\n\n" +
				cd.Message + "\n\n" +
				"y/n" + " • " + HelpStyle.Render("y=confirm, n=cancel"),
		)

	return content
}

// Autocomplete functionality
type AutocompleteItem struct {
	Text        string
	Description string
	Value       interface{}
}

func RenderAutocomplete(items []AutocompleteItem, selectedIndex int, maxItems int) string {
	if len(items) == 0 {
		return ""
	}

	var content strings.Builder

	// Limit the number of items shown
	start := 0
	end := len(items)
	if len(items) > maxItems {
		half := maxItems / 2
		if selectedIndex > half {
			start = selectedIndex - half
			end = start + maxItems
		} else {
			end = maxItems
		}
		if end > len(items) {
			end = len(items)
			start = end - maxItems
		}
	}

	for i := start; i < end; i++ {
		item := items[i]
		prefix := " "
		if i == selectedIndex {
			prefix = ">"
		}

		style := ValueStyle
		if i == selectedIndex {
			style = SelectedStyle
		}

		content.WriteString(fmt.Sprintf("%s %s", prefix, style.Render(item.Text)))
		if item.Description != "" {
			content.WriteString(" " + HelpStyle.Render("("+item.Description+")"))
		}
		content.WriteString("\n")
	}

	return content.String()
}

// File size formatting
func FormatFileSize(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

// Common keyboard shortcuts
var CommonShortcuts = []Shortcut{
	{Key: "q", Description: "Quit", Action: "quit"},
	{Key: "esc", Description: "Back", Action: "back"},
	{Key: "ctrl+c", Description: "Quit", Action: "quit"},
	{Key: "f1", Description: "Help", Action: "help"},
	{Key: "tab", Description: "Next", Action: "next"},
	{Key: "shift+tab", Description: "Previous", Action: "prev"},
}
