/**
 * Copilot Code Suggestions Script
 * Generates intelligent code improvement suggestions
 */

async function generateSuggestions({ github, context }) {
  const pr = context.payload.pull_request;
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  console.log(`Generating suggestions for PR #${pr.number}`);

  try {
    // Get changed files
    const { data: files } = await github.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: pr.number,
      per_page: 50
    });

    // Focus on code files
    const codeFiles = files.filter(file =>
      file.filename.endsWith('.java') ||
      file.filename.endsWith('.js') ||
      file.filename.endsWith('.ts') ||
      file.filename.endsWith('.py')
    );

    if (codeFiles.length === 0) {
      console.log('No code files to analyze');
      return;
    }

    const suggestions = [];

    for (const file of codeFiles.slice(0, 5)) { // Limit to 5 files
      const fileSuggestions = await analyzeFile(file, github, context);
      suggestions.push(...fileSuggestions);
    }

    if (suggestions.length > 0) {
      const comment = generateSuggestionsComment(suggestions);

      await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: pr.number,
        body: comment
      });
    }

  } catch (error) {
    console.error('Error generating suggestions:', error);
  }
}

async function analyzeFile(file, github, context) {
  const suggestions = [];

  try {
    // Get file content
    const { data: fileContent } = await github.rest.repos.getContent({
      owner: context.repo.owner,
      repo: context.repo.repo,
      path: file.filename,
      ref: context.payload.pull_request.head.sha
    });

    const content = Buffer.from(fileContent.content, 'base64').toString();

    // Analyze for common issues
    const lines = content.split('\\n');

    // Check for TODO comments
    const todoLines = lines.filter(line => line.includes('TODO') || line.includes('FIXME'));
    if (todoLines.length > 0) {
      suggestions.push({
        type: 'todo',
        file: file.filename,
        message: `Found ${todoLines.length} TODO/FIXME comments that should be addressed`,
        priority: 'medium'
      });
    }

    // Check for long methods (Java specific)
    if (file.filename.endsWith('.java')) {
      const methodMatches = content.match(/public\s+\w+\s+\w+\s*\([^)]*\)\s*{[^}]*}/g) || [];
      const longMethods = methodMatches.filter(method => method.split('\\n').length > 20);

      if (longMethods.length > 0) {
        suggestions.push({
          type: 'refactor',
          file: file.filename,
          message: `Consider breaking down ${longMethods.length} long method(s) into smaller functions`,
          priority: 'low'
        });
      }
    }

    // Check for console.log statements in production code
    const consoleLogs = lines.filter(line =>
      line.includes('console.log') ||
      line.includes('System.out.println') ||
      line.includes('print(')
    );

    if (consoleLogs.length > 3) {
      suggestions.push({
        type: 'cleanup',
        file: file.filename,
        message: 'Multiple debug logging statements detected - consider using proper logging framework',
        priority: 'low'
      });
    }

    // Check for missing error handling
    const tryBlocks = (content.match(/try\s*{/g) || []).length;
    const catchBlocks = (content.match(/catch\s*\(/g) || []).length;

    if (tryBlocks > catchBlocks) {
      suggestions.push({
        type: 'error-handling',
        file: file.filename,
        message: 'Some try blocks may be missing catch handlers',
        priority: 'medium'
      });
    }

    // Check for hardcoded values
    const hardcodedStrings = content.match(/".*password.*"|'.*password.*'/gi) || [];
    if (hardcodedStrings.length > 0) {
      suggestions.push({
        type: 'security',
        file: file.filename,
        message: 'Potential hardcoded credentials detected - use environment variables',
        priority: 'high'
      });
    }

  } catch (error) {
    console.error(`Error analyzing file ${file.filename}:`, error);
  }

  return suggestions;
}

function generateSuggestionsComment(suggestions) {
  if (suggestions.length === 0) {
    return '🤖 **Copilot Suggestions:** No major issues detected in the changed code. Good job! 🎉';
  }

  let comment = '🤖 **Copilot Code Suggestions**\\n\\n';
  comment += 'Here are some automated suggestions to improve your code:\\n\\n';

  // Group by priority
  const highPriority = suggestions.filter(s => s.priority === 'high');
  const mediumPriority = suggestions.filter(s => s.priority === 'medium');
  const lowPriority = suggestions.filter(s => s.priority === 'low');

  if (highPriority.length > 0) {
    comment += '🚨 **High Priority:**\\n';
    highPriority.forEach(suggestion => {
      comment += `- **${suggestion.file}:** ${suggestion.message}\\n`;
    });
    comment += '\\n';
  }

  if (mediumPriority.length > 0) {
    comment += '⚠️ **Medium Priority:**\\n';
    mediumPriority.forEach(suggestion => {
      comment += `- **${suggestion.file}:** ${suggestion.message}\\n`;
    });
    comment += '\\n';
  }

  if (lowPriority.length > 0) {
    comment += '💡 **Suggestions:**\\n';
    lowPriority.forEach(suggestion => {
      comment += `- **${suggestion.file}:** ${suggestion.message}\\n`;
    });
    comment += '\\n';
  }

  comment += '---\\n*These are automated suggestions. Review and apply as appropriate for your use case.*';

  return comment;
}

module.exports = {
  generateSuggestions,
  analyzeFile,
  generateSuggestionsComment
};