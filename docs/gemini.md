# Gemini AI Agent Configuration

## Role
Gemini AI serves as the multimodal AI assistant for the OpenLegislation project, specializing in advanced reasoning, code generation, and creative problem-solving.

## Capabilities
- Advanced multimodal understanding (text, code, diagrams)
- Complex reasoning and planning
- Creative solution generation
- Code review and optimization
- Documentation synthesis
- Technical architecture design

## Configuration
- **Model**: Gemini 1.5 Pro / Gemini 1.5 Flash
- **Temperature**: 0.7 for creative tasks, 0.3 for technical tasks
- **Max Tokens**: 8192 for detailed responses
- **Safety Settings**: Standard (block harmful content)

## Integration Points
- GitHub Copilot integration for code suggestions
- VS Code extension for real-time assistance
- Webhook server for automated PR reviews
- Documentation generation from codebase analysis

## Workflows
1. **Code Generation**: Generate Java classes, SQL migrations, React components
2. **Architecture Review**: Analyze system design and suggest improvements
3. **Documentation**: Create comprehensive technical documentation
4. **Testing**: Generate unit tests and integration test scenarios
5. **Debugging**: Analyze error logs and suggest fixes

## Best Practices
- Use structured prompts for complex tasks
- Provide context from existing codebase
- Validate generated code against project standards
- Maintain consistency with existing patterns
- Document assumptions and decisions

## Memory and Context
- Persistent context across sessions
- Project-specific knowledge base
- Codebase understanding and patterns
- Historical decisions and implementations

## Collaboration
- Works alongside other AI agents (Claude, Qwen, Codex)
- Integrates with human developers
- Provides explanations for all suggestions
- Accepts feedback for continuous improvement