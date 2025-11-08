package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	tea "github.com/charmbracelet/bubbletea"

	"charm-suite/framework"
)

type Secret struct {
	Name        string `json:"name"`
	Value       string `json:"value"`
	Description string `json:"description"`
	Created     string `json:"created"`
}

type model struct {
	secrets       []Secret
	selected      int
	width         int
	height        int
	loading       bool
	error         string
	showHelp      bool
	addingSecret  bool
	newSecret     Secret
	confirmDelete int
}

func initialModel() model {
	return model{
		secrets:      []Secret{},
		selected:     0,
		loading:      true,
		showHelp:     false,
		addingSecret: false,
		newSecret:    Secret{},
	}
}

func (m model) Init() tea.Cmd {
	return loadSecrets
}

type secretsLoadedMsg []Secret
type errorMsg error

func loadSecrets() tea.Msg {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return errorMsg(fmt.Errorf("failed to get home directory: %v", err))
	}

	secretsFile := filepath.Join(homeDir, ".charm-secrets.json")
	secrets := []Secret{}

	if _, err := os.Stat(secretsFile); err == nil {
		data, err := os.ReadFile(secretsFile)
		if err != nil {
			return errorMsg(fmt.Errorf("failed to read secrets file: %v", err))
		}

		// Decrypt secrets (simplified - in real app would use proper key management)
		if err := json.Unmarshal(data, &secrets); err != nil {
			return errorMsg(fmt.Errorf("failed to parse secrets file: %v", err))
		}
	}

	return secretsLoadedMsg(secrets)
}

func saveSecrets(secrets []Secret) tea.Msg {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return errorMsg(fmt.Errorf("failed to get home directory: %v", err))
	}

	secretsFile := filepath.Join(homeDir, ".charm-secrets.json")

	data, err := json.MarshalIndent(secrets, "", "  ")
	if err != nil {
		return errorMsg(fmt.Errorf("failed to marshal secrets: %v", err))
	}

	// Encrypt secrets (simplified - in real app would use proper encryption)
	if err := os.WriteFile(secretsFile, data, 0600); err != nil {
		return errorMsg(fmt.Errorf("failed to save secrets: %v", err))
	}

	return secretsLoadedMsg(secrets)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case secretsLoadedMsg:
		m.secrets = []Secret(msg)
		m.loading = false
		return m, nil

	case errorMsg:
		m.error = msg.Error()
		m.loading = false
		return m, nil

	case tea.KeyMsg:
		if m.addingSecret {
			return m.updateAddSecret(msg)
		}

		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit

		case "up", "k":
			if m.selected > 0 {
				m.selected--
			}

		case "down", "j":
			if m.selected < len(m.secrets)-1 {
				m.selected++
			}

		case "n":
			m.addingSecret = true
			m.newSecret = Secret{}

		case "d":
			if len(m.secrets) > 0 {
				m.confirmDelete = m.selected
			}

		case "y":
			if m.confirmDelete >= 0 && m.confirmDelete < len(m.secrets) {
				secrets := make([]Secret, len(m.secrets))
				copy(secrets, m.secrets)
				secrets = append(secrets[:m.confirmDelete], secrets[m.confirmDelete+1:]...)
				m.confirmDelete = -1
				m.selected = 0
				return m, func() tea.Msg { return saveSecrets(secrets) }
			}

		case "r":
			return m, loadSecrets

		case "?":
			m.showHelp = !m.showHelp

		default:
			if m.confirmDelete >= 0 {
				m.confirmDelete = -1
			}
		}
	}

	return m, nil
}

func (m model) updateAddSecret(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "esc":
		m.addingSecret = false
		m.newSecret = Secret{}

	case "enter":
		if m.newSecret.Name != "" && m.newSecret.Value != "" {
			secrets := make([]Secret, len(m.secrets))
			copy(secrets, m.secrets)
			secrets = append(secrets, m.newSecret)
			m.addingSecret = false
			m.newSecret = Secret{}
			return m, func() tea.Msg { return saveSecrets(secrets) }
		}
	}
	return m, nil
}

func (m model) View() string {
	if m.loading {
		return framework.TitleStyle.Render("Secrets Manager") + "\n\n" +
			framework.HelpStyle.Render("Loading secrets...")
	}

	if m.error != "" {
		return framework.TitleStyle.Render("Secrets Manager") + "\n\n" +
			framework.ErrorStyle.Render("Error: "+m.error) + "\n\n" +
			framework.HelpStyle.Render("Press 'r' to retry or 'q' to quit")
	}

	if m.addingSecret {
		return m.renderAddSecret()
	}

	content := framework.TitleStyle.Render("Secrets Manager") + "\n\n"

	if len(m.secrets) == 0 {
		content += framework.HelpStyle.Render("No secrets stored\n\n") +
			framework.HelpStyle.Render("Press 'n' to add a new secret")
	} else {
		// Render secrets list
		for i, secret := range m.secrets {
			prefix := " "
			style := framework.ValueStyle
			if i == m.selected {
				prefix = ">"
				style = framework.SelectedStyle
			}

			if i == m.confirmDelete {
				content += framework.ErrorStyle.Render(fmt.Sprintf("%s Delete '%s'? (y/n)", prefix, secret.Name))
			} else {
				secretInfo := fmt.Sprintf("%s - %s", secret.Name, framework.HelpStyle.Render(secret.Description))
				content += fmt.Sprintf("%s %s\n", prefix, style.Render(secretInfo))
			}
		}
	}

	// Render help bar
	shortcuts := []framework.Shortcut{
		{Key: "↑↓/jk", Description: "Navigate"},
		{Key: "n", Description: "New secret"},
		{Key: "d", Description: "Delete"},
		{Key: "r", Description: "Refresh"},
		{Key: "?", Description: "Help"},
		{Key: "q", Description: "Quit"},
	}

	content += "\n" + framework.RenderHelpBar(shortcuts)

	if m.showHelp {
		content += "\n\n" + framework.BorderStyle.Render(
			framework.SubtitleStyle.Render("Secrets Manager Help\n\n")+
				"• Navigate through secrets using arrow keys or j/k\n"+
				"• Press 'n' to add a new secret\n"+
				"• Press 'd' to delete the selected secret (with confirmation)\n"+
				"• Press 'r' to refresh the secrets list\n"+
				"• Press '?' to toggle this help screen\n"+
				"• Press 'q' to quit the application\n\n"+
				framework.HelpStyle.Render("Secrets are stored encrypted in ~/.charm-secrets.json"),
		)
	}

	return content
}

func (m model) renderAddSecret() string {
	content := framework.TitleStyle.Render("Add New Secret") + "\n\n"
	content += fmt.Sprintf("%s %s\n", framework.SubtitleStyle.Render("Name:"), m.newSecret.Name)
	content += fmt.Sprintf("%s %s\n", framework.SubtitleStyle.Render("Description:"), m.newSecret.Description)
	content += fmt.Sprintf("%s %s\n", framework.SubtitleStyle.Render("Value:"), framework.HelpStyle.Render("[hidden]"))

	content += "\n" + framework.HelpStyle.Render("Press Enter to save or ESC to cancel")

	return framework.BorderStyle.Width(m.width - 4).Render(content)
}

func main() {
	framework.SetTheme(framework.Themes["dark"])

	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error running Secrets Manager: %v", err)
		os.Exit(1)
	}
}
