package main

import (
	"fmt"
	"time"

	"charm-suite/framework"
)

func main() {
	// Test the framework components
	fmt.Println("Testing Charm Suite Framework...")

	// Test theme system
	framework.SetTheme(framework.Themes["dark"])
	fmt.Println("Theme set to Dark")

	// Test styling
	styledText := framework.TitleStyle.Render("Hello, Charm Suite!")
	fmt.Println(styledText)

	// Test progress bar
	progress := framework.RenderProgressBar(7, 10, 20)
	fmt.Printf("Progress: %s\n", progress)

	// Test status rendering
	status := framework.RenderStatus("Running", true)
	fmt.Printf("Status: %s\n", status)

	// Test autocomplete
	items := []framework.AutocompleteItem{
		{Text: "option1", Description: "First option"},
		{Text: "option2", Description: "Second option"},
		{Text: "option3", Description: "Third option"},
	}

	autocomplete := framework.RenderAutocomplete(items, 0, 5)
	fmt.Println(autocomplete)

	// Test file size formatting
	size := framework.FormatFileSize(1024)
	fmt.Printf("File size: %s\n", size)

	// Test time formatting
	now := framework.FormatTime(time.Now())
	fmt.Printf("Current time: %s\n", now)

	// Test text input creation
	textInput := framework.CreateTextInput("Enter text...", true)
	fmt.Printf("Text input placeholder: %s\n", textInput.Placeholder)

	fmt.Println("Framework test completed successfully!")
}
