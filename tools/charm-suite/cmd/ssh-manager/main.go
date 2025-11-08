package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"

	"charm-suite/framework"
)

type SSHKey struct {
	Filename  string
	Path      string
	Size      int64
	ModTime   time.Time
	Content   string
	PublicKey string
}

type model struct {
	keys         []SSHKey
	selected     int
	width        int
	height       int
	loading      bool
	error        string
	showHelp     bool
	keyDetails   *SSHKey
	confirmIndex int
}

func initialModel() model {
	return model{
		keys:       []SSHKey{},
		selected:   0,
		loading:    true,
		showHelp:   false,
		keyDetails: nil,
	}
}

func (m model) Init() tea.Cmd {
	return loadSSHKeys
}

type sshKeysLoadedMsg []SSHKey
type errorMsg error

func loadSSHKeys() tea.Msg {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return errorMsg(fmt.Errorf("failed to get home directory: %v", err))
	}

	sshDir := filepath.Join(homeDir, ".ssh")
	keys := []SSHKey{}

	entries, err := os.ReadDir(sshDir)
	if err != nil {
		if os.IsNotExist(err) {
			return sshKeysLoadedMsg(keys) // Return empty if .ssh doesn't exist
		}
		return errorMsg(fmt.Errorf("failed to read .ssh directory: %v", err))
	}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		path := filepath.Join(sshDir, entry.Name())
		info, err := entry.Info()
		if err != nil {
			continue
		}

		content, err := os.ReadFile(path)
		if err != nil {
			continue
		}

		key := SSHKey{
			Filename: entry.Name(),
			Path:     path,
			Size:     info.Size(),
			ModTime:  info.ModTime(),
			Content:  string(content),
		}

		// Try to get public key for private keys
		if strings.HasSuffix(entry.Name(), ".pub") {
			key.PublicKey = string(content)
		} else if !strings.Contains(entry.Name(), ".pub") && !strings.Contains(entry.Name(), "config") && !strings.Contains(entry.Name(), "known_hosts") {
			// Try to extract public key from private key
			if pubKey, err := getPublicKey(path); err == nil {
				key.PublicKey = pubKey
			}
		}

		keys = append(keys, key)
	}

	return sshKeysLoadedMsg(keys)
}

func getPublicKey(privateKeyPath string) (string, error) {
	cmd := exec.Command("ssh-keygen", "-y", "-f", privateKeyPath)
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(output)), nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case sshKeysLoadedMsg:
		m.keys = []SSHKey(msg)
		m.loading = false
		return m, nil

	case errorMsg:
		m.error = msg.Error()
		m.loading = false
		return m, nil

	case tea.KeyMsg:
		if m.keyDetails != nil {
			return m.updateKeyDetails(msg)
		}

		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit

		case "up", "k":
			if m.selected > 0 {
				m.selected--
			}

		case "down", "j":
			if m.selected < len(m.keys)-1 {
				m.selected++
			}

		case "enter", " ":
			if len(m.keys) > 0 {
				m.keyDetails = &m.keys[m.selected]
			}

		case "n":
			return m, generateNewKey

		case "r":
			return m, loadSSHKeys

		case "d":
			if len(m.keys) > 0 {
				m.confirmIndex = m.selected
			}

		case "y":
			if m.confirmIndex >= 0 && m.confirmIndex < len(m.keys) {
				return m, deleteKey(m.confirmIndex)
			}

		case "?":
			m.showHelp = !m.showHelp

		default:
			if m.confirmIndex >= 0 {
				m.confirmIndex = -1
			}
		}
	}

	return m, nil
}

func (m model) updateKeyDetails(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "q", "esc", "enter":
		m.keyDetails = nil
	}
	return m, nil
}

type keyGeneratedMsg SSHKey
type keyDeletedMsg int

func generateNewKey() tea.Msg {
	// For now, return a placeholder - in a real implementation,
	// you'd want to prompt for key type, name, etc.
	return errorMsg(fmt.Errorf("key generation not implemented yet"))
}

func deleteKey(index int) tea.Cmd {
	return func() tea.Msg {
		// Placeholder for key deletion
		return errorMsg(fmt.Errorf("key deletion not implemented yet"))
	}
}

func (m model) View() string {
	if m.loading {
		return framework.TitleStyle.Render("SSH Key Manager") + "\n\n" +
			framework.HelpStyle.Render("Loading SSH keys...")
	}

	if m.error != "" {
		return framework.TitleStyle.Render("SSH Key Manager") + "\n\n" +
			framework.ErrorStyle.Render("Error: "+m.error) + "\n\n" +
			framework.HelpStyle.Render("Press 'r' to retry or 'q' to quit")
	}

	if m.keyDetails != nil {
		return m.renderKeyDetails()
	}

	content := framework.TitleStyle.Render("SSH Key Manager") + "\n\n"

	if len(m.keys) == 0 {
		content += framework.HelpStyle.Render("No SSH keys found in ~/.ssh directory\n\n") +
			framework.HelpStyle.Render("Press 'n' to generate a new key")
	} else {
		// Render key list
		for i, key := range m.keys {
			prefix := " "
			style := framework.ValueStyle
			if i == m.selected {
				prefix = ">"
				style = framework.SelectedStyle
			}

			if i == m.confirmIndex {
				content += framework.ErrorStyle.Render(fmt.Sprintf("%s Delete %s? (y/n)", prefix, key.Filename))
			} else {
				keyInfo := fmt.Sprintf("%s %s", key.Filename, framework.FormatFileSize(key.Size))
				content += fmt.Sprintf("%s %s\n", prefix, style.Render(keyInfo))
				content += fmt.Sprintf("  %s\n", framework.HelpStyle.Render(framework.FormatTime(key.ModTime)))
			}
		}
	}

	// Render help bar
	shortcuts := []framework.Shortcut{
		{Key: "↑↓/jk", Description: "Navigate"},
		{Key: "Enter", Description: "View details"},
		{Key: "n", Description: "New key"},
		{Key: "d", Description: "Delete"},
		{Key: "r", Description: "Refresh"},
		{Key: "?", Description: "Help"},
		{Key: "q", Description: "Quit"},
	}

	content += "\n" + framework.RenderHelpBar(shortcuts)

	if m.showHelp {
		content += "\n\n" + framework.BorderStyle.Render(
			framework.SubtitleStyle.Render("SSH Key Manager Help\n\n")+
				"• Navigate through your SSH keys using arrow keys or j/k\n"+
				"• Press Enter to view detailed information about a key\n"+
				"• Press 'n' to generate a new SSH key pair\n"+
				"• Press 'd' to delete the selected key (with confirmation)\n"+
				"• Press 'r' to refresh the key list\n"+
				"• Press '?' to toggle this help screen\n"+
				"• Press 'q' to quit the application\n\n"+
				framework.HelpStyle.Render("SSH keys are loaded from ~/.ssh directory"),
		)
	}

	return content
}

func (m model) renderKeyDetails() string {
	key := *m.keyDetails
	content := framework.TitleStyle.Render("SSH Key Details") + "\n\n"
	content += fmt.Sprintf("%s %s\n", framework.SubtitleStyle.Render("Filename:"), framework.ValueStyle.Render(key.Filename))
	content += fmt.Sprintf("%s %s\n", framework.SubtitleStyle.Render("Path:"), framework.ValueStyle.Render(key.Path))
	content += fmt.Sprintf("%s %s\n", framework.SubtitleStyle.Render("Size:"), framework.ValueStyle.Render(framework.FormatFileSize(key.Size)))
	content += fmt.Sprintf("%s %s\n", framework.SubtitleStyle.Render("Modified:"), framework.ValueStyle.Render(framework.FormatTime(key.ModTime)))

	if key.PublicKey != "" {
		content += fmt.Sprintf("\n%s\n", framework.SubtitleStyle.Render("Public Key:"))
		content += framework.CodeStyle.Render(key.PublicKey) + "\n"
	}

	content += fmt.Sprintf("\n%s\n", framework.SubtitleStyle.Render("Press Enter/ESC to return to list"))

	return framework.BorderStyle.Width(m.width - 4).Render(content)
}

func main() {
	framework.SetTheme(framework.Themes["dark"])

	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error running SSH Key Manager: %v", err)
		os.Exit(1)
	}
}
