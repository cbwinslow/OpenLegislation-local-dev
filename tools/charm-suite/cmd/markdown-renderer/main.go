package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/glamour"

	"charm-suite/framework"
)

type MarkdownFile struct {
	Name     string
	Path     string
	Size     int64
	Content  string
	IsDir    bool
	Children []MarkdownFile
}

type model struct {
	files           []MarkdownFile
	selected        int
	width           int
	height          int
	loading         bool
	error           string
	showHelp        bool
	currentFile     *MarkdownFile
	renderedContent string
	directory       string
	history         []string // Navigation history
	historyIndex    int
}

func initialModel() model {
	homeDir, _ := os.UserHomeDir()
	return model{
		files:        []MarkdownFile{},
		selected:     0,
		loading:      true,
		showHelp:     false,
		directory:    homeDir,
		history:      []string{homeDir},
		historyIndex: 0,
	}
}

func (m model) Init() tea.Cmd {
	return loadMarkdownFiles(m.directory)
}

type markdownFilesLoadedMsg struct {
	files []MarkdownFile
	dir   string
}

type errorMsg error

func loadMarkdownFiles(dir string) tea.Cmd {
	return func() tea.Msg {
		files := []MarkdownFile{}

		entries, err := os.ReadDir(dir)
		if err != nil {
			return errorMsg(fmt.Errorf("failed to read directory: %v", err))
		}

		for _, entry := range entries {
			name := entry.Name()
			path := filepath.Join(dir, name)

			if entry.IsDir() {
				// Check if directory contains markdown files
				if hasMarkdownFiles(path) {
					files = append(files, MarkdownFile{
						Name:  name,
						Path:  path,
						Size:  0,
						IsDir: true,
					})
				}
			} else if strings.HasSuffix(strings.ToLower(name), ".md") {
				info, err := entry.Info()
				if err != nil {
					continue
				}

				content, err := os.ReadFile(path)
				if err != nil {
					continue
				}

				files = append(files, MarkdownFile{
					Name:    name,
					Path:    path,
					Size:    info.Size(),
					Content: string(content),
					IsDir:   false,
				})
			}
		}

		return markdownFilesLoadedMsg{files: files, dir: dir}
	}
}

func hasMarkdownFiles(dir string) bool {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return false
	}

	for _, entry := range entries {
		if !entry.IsDir() && strings.HasSuffix(strings.ToLower(entry.Name()), ".md") {
			return true
		}
	}
	return false
}

func renderMarkdown(content string) (string, error) {
	// Create a glamour renderer with dark theme
	r, err := glamour.NewTermRenderer(
		glamour.WithAutoStyle(),
		glamour.WithWordWrap(120),
	)
	if err != nil {
		return "", err
	}

	return r.Render(content)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case markdownFilesLoadedMsg:
		m.files = msg.files
		m.directory = msg.dir
		m.loading = false
		return m, nil

	case errorMsg:
		m.error = msg.Error()
		m.loading = false
		return m, nil

	case tea.KeyMsg:
		if m.currentFile != nil {
			return m.updateFileViewer(msg)
		}

		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit

		case "up", "k":
			if m.selected > 0 {
				m.selected--
			}

		case "down", "j":
			if m.selected < len(m.files)-1 {
				m.selected++
			}

		case "enter", " ":
			if len(m.files) > 0 {
				selected := m.files[m.selected]
				if selected.IsDir {
					// Navigate into directory
					m.history = append(m.history[:m.historyIndex+1], selected.Path)
					m.historyIndex++
					m.directory = selected.Path
					m.selected = 0
					return m, loadMarkdownFiles(selected.Path)
				} else {
					// View markdown file
					m.currentFile = &selected
					rendered, err := renderMarkdown(selected.Content)
					if err != nil {
						m.error = fmt.Sprintf("Failed to render markdown: %v", err)
					} else {
						m.renderedContent = rendered
					}
				}
			}

		case "left", "h":
			// Go back in history
			if m.historyIndex > 0 {
				m.historyIndex--
				m.directory = m.history[m.historyIndex]
				m.selected = 0
				return m, loadMarkdownFiles(m.directory)
			}

		case "r":
			return m, loadMarkdownFiles(m.directory)

		case "g":
			// Go to directory (simplified - in real app would prompt for input)
			homeDir, _ := os.UserHomeDir()
			m.history = append(m.history[:m.historyIndex+1], homeDir)
			m.historyIndex++
			m.directory = homeDir
			m.selected = 0
			return m, loadMarkdownFiles(homeDir)

		case "?":
			m.showHelp = !m.showHelp
		}
	}

	return m, nil
}

func (m model) updateFileViewer(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "q", "esc", "enter":
		m.currentFile = nil
		m.renderedContent = ""
	}
	return m, nil
}

func (m model) View() string {
	if m.loading {
		return framework.TitleStyle.Render("Markdown Repository Renderer") + "\n\n" +
			framework.HelpStyle.Render("Loading markdown files...")
	}

	if m.error != "" {
		return framework.TitleStyle.Render("Markdown Repository Renderer") + "\n\n" +
			framework.ErrorStyle.Render("Error: "+m.error) + "\n\n" +
			framework.HelpStyle.Render("Press 'r' to retry or 'q' to quit")
	}

	if m.currentFile != nil {
		return m.renderFileViewer()
	}

	content := framework.TitleStyle.Render("Markdown Repository Renderer") + "\n\n"

	// Breadcrumb navigation
	breadcrumb := m.renderBreadcrumb()
	content += framework.HelpStyle.Render(breadcrumb) + "\n\n"

	if len(m.files) == 0 {
		content += framework.HelpStyle.Render("No markdown files found in this directory\n\n") +
			framework.HelpStyle.Render("Press 'g' to go to home directory")
	} else {
		// Render file list
		for i, file := range m.files {
			prefix := " "
			style := framework.ValueStyle
			if i == m.selected {
				prefix = ">"
				style = framework.SelectedStyle
			}

			icon := "📄"
			if file.IsDir {
				icon = "📁"
			}

			fileInfo := fmt.Sprintf("%s %s %s", icon, file.Name, framework.HelpStyle.Render(framework.FormatFileSize(file.Size)))
			content += fmt.Sprintf("%s %s\n", prefix, style.Render(fileInfo))
		}
	}

	// Render help bar
	shortcuts := []framework.Shortcut{
		{Key: "↑↓/jk", Description: "Navigate"},
		{Key: "Enter", Description: fileActionText(m.files, m.selected)},
		{Key: "←/h", Description: "Back"},
		{Key: "g", Description: "Go home"},
		{Key: "r", Description: "Refresh"},
		{Key: "?", Description: "Help"},
		{Key: "q", Description: "Quit"},
	}

	content += "\n" + framework.RenderHelpBar(shortcuts)

	if m.showHelp {
		content += "\n\n" + framework.BorderStyle.Render(
			framework.SubtitleStyle.Render("Markdown Repository Renderer Help\n\n")+
				"• Navigate through files and directories using arrow keys or j/k\n"+
				"• Press Enter to view a markdown file or enter a directory\n"+
				"• Press ←/h to go back to the previous directory\n"+
				"• Press 'g' to go to your home directory\n"+
				"• Press 'r' to refresh the current directory\n"+
				"• Press '?' to toggle this help screen\n"+
				"• Press 'q' to quit the application\n\n"+
				framework.HelpStyle.Render("Only directories containing markdown files are shown"),
		)
	}

	return content
}

func (m model) renderBreadcrumb() string {
	if len(m.history) == 0 {
		return "/"
	}

	parts := []string{}
	for i := 0; i <= m.historyIndex && i < len(m.history); i++ {
		path := m.history[i]
		if i == 0 {
			parts = append(parts, "~")
		} else {
			parts = append(parts, filepath.Base(path))
		}
	}

	return strings.Join(parts, " / ")
}

func fileActionText(files []MarkdownFile, selected int) string {
	if len(files) == 0 {
		return "View"
	}

	if files[selected].IsDir {
		return "Enter"
	}
	return "View"
}

func (m model) renderFileViewer() string {
	file := *m.currentFile
	content := framework.TitleStyle.Render(file.Name) + "\n\n"
	content += framework.HelpStyle.Render("Path: "+file.Path) + "\n\n"

	if m.renderedContent != "" {
		// Use viewport for long content
		viewport := framework.CreateViewport(m.width-4, m.height-10)
		viewport.SetContent(m.renderedContent)
		content += viewport.View()
	} else {
		content += framework.ErrorStyle.Render("Failed to render markdown content")
	}

	content += fmt.Sprintf("\n\n%s", framework.HelpStyle.Render("Press q/ESC/Enter to return to list"))

	return framework.BorderStyle.Width(m.width - 4).Render(content)
}

func main() {
	framework.SetTheme(framework.Themes["dark"])

	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error running Markdown Repository Renderer: %v", err)
		os.Exit(1)
	}
}
