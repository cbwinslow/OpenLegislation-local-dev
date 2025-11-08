/**
 * Copilot PR Analysis Script
 * Provides intelligent PR analysis and suggestions
 */

async function analyzePR({ github, context }) {
  const pr = context.payload.pull_request;
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  console.log(`Analyzing PR #${pr.number}: ${pr.title}`);

  try {
    // Get PR details
    const { data: prData } = await github.rest.pulls.get({
      owner,
      repo,
      pull_number: pr.number
    });

    // Get changed files
    const { data: files } = await github.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: pr.number,
      per_page: 100
    });

    // Get commits
    const { data: commits } = await github.rest.pulls.listCommits({
      owner,
      repo,
      pull_number: pr.number,
      per_page: 50
    });

    // Analyze the changes
    const analysis = await performPRAnalysis(prData, files, commits);

    // Post analysis as a comment
    const comment = generateAnalysisComment(analysis);

    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: pr.number,
      body: comment
    });

    // Add labels based on analysis
    await addAnalysisLabels(github, context, analysis);

  } catch (error) {
    console.error('Error in PR analysis:', error);

    // Post error comment
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: pr.number,
      body: `🤖 **Copilot Analysis Error:**\\n\\nEncountered an error during analysis: ${error.message}\\n\\nPlease check the workflow logs for more details.`
    });
  }
}

async function performPRAnalysis(prData, files, commits) {
  const analysis = {
    size: 'small',
    complexity: 'low',
    risk: 'low',
    suggestions: [],
    concerns: [],
    categories: []
  };

  // Analyze size
  const additions = files.reduce((sum, file) => sum + file.additions, 0);
  const deletions = files.reduce((sum, file) => sum + file.deletions, 0);
  const totalChanges = additions + deletions;

  if (totalChanges > 1000) {
    analysis.size = 'large';
    analysis.risk = 'high';
    analysis.concerns.push('Large PR - consider breaking into smaller changes');
  } else if (totalChanges > 100) {
    analysis.size = 'medium';
    analysis.risk = 'medium';
  }

  // Analyze file types
  const fileTypes = {};
  files.forEach(file => {
    const ext = file.filename.split('.').pop();
    fileTypes[ext] = (fileTypes[ext] || 0) + 1;
  });

  // Check for test files
  const hasTests = files.some(file =>
    file.filename.includes('test') ||
    file.filename.includes('spec') ||
    file.filename.endsWith('.java') && (
      file.filename.includes('Test') ||
      file.filename.includes('IT')
    )
  );

  if (!hasTests && files.some(file => file.filename.endsWith('.java'))) {
    analysis.concerns.push('No test files detected - consider adding tests');
  }

  // Check for documentation changes
  const hasDocs = files.some(file =>
    file.filename.includes('README') ||
    file.filename.includes('docs/') ||
    file.filename.includes('.md')
  );

  if (!hasDocs && analysis.size !== 'small') {
    analysis.suggestions.push('Consider updating documentation for these changes');
  }

  // Analyze commit messages
  const commitMessages = commits.map(c => c.commit.message);
  const goodCommits = commitMessages.filter(msg =>
    msg.length > 10 &&
    !msg.toLowerCase().includes('fix') &&
    !msg.toLowerCase().includes('update') &&
    !msg.toLowerCase().includes('wip')
  );

  if (goodCommits.length < commits.length * 0.5) {
    analysis.suggestions.push('Some commit messages could be more descriptive');
  }

  // Categorize changes
  if (files.some(f => f.filename.includes('security') || f.filename.includes('auth'))) {
    analysis.categories.push('security');
    analysis.risk = 'high';
  }

  if (files.some(f => f.filename.includes('database') || f.filename.includes('migration'))) {
    analysis.categories.push('database');
    analysis.risk = 'medium';
  }

  if (files.some(f => f.filename.includes('api') || f.filename.includes('controller'))) {
    analysis.categories.push('api');
  }

  // Complexity analysis
  const complexFiles = files.filter(f =>
    f.additions > 50 ||
    f.filename.includes('service') ||
    f.filename.includes('processor')
  );

  if (complexFiles.length > 3) {
    analysis.complexity = 'high';
    analysis.concerns.push('Multiple complex files changed - thorough review recommended');
  }

  return analysis;
}

function generateAnalysisComment(analysis) {
  let comment = `🤖 **Copilot PR Analysis**\\n\\n`;

  comment += `**Size:** ${analysis.size} (${analysis.complexity} complexity)\\n`;
  comment += `**Risk Level:** ${analysis.risk}\\n`;

  if (analysis.categories.length > 0) {
    comment += `**Categories:** ${analysis.categories.join(', ')}\\n`;
  }

  if (analysis.concerns.length > 0) {
    comment += `\\n⚠️ **Concerns:**\\n`;
    analysis.concerns.forEach(concern => {
      comment += `- ${concern}\\n`;
    });
  }

  if (analysis.suggestions.length > 0) {
    comment += `\\n💡 **Suggestions:**\\n`;
    analysis.suggestions.forEach(suggestion => {
      comment += `- ${suggestion}\\n`;
    });
  }

  comment += `\\n---\\n*Analysis performed by Copilot - review and address items as needed*`;

  return comment;
}

async function addAnalysisLabels(github, context, analysis) {
  const labels = [];

  // Size labels
  if (analysis.size === 'large') labels.push('size:large');
  else if (analysis.size === 'medium') labels.push('size:medium');
  else labels.push('size:small');

  // Risk labels
  labels.push(`risk:${analysis.risk}`);

  // Category labels
  analysis.categories.forEach(cat => labels.push(`category:${cat}`));

  // Complexity
  labels.push(`complexity:${analysis.complexity}`);

  try {
    await github.rest.issues.addLabels({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: context.payload.pull_request.number,
      labels
    });
  } catch (error) {
    console.error('Error adding labels:', error);
  }
}

async function generateCopilotResponse(request, context) {
  // This would integrate with Copilot API or use GitHub's Copilot features
  // For now, return a placeholder response
  return `I've analyzed your request: "${request}". This is a placeholder for Copilot integration. In a full implementation, this would use GitHub Copilot or OpenAI to provide intelligent responses.`;
}

module.exports = {
  analyzePR,
  performPRAnalysis,
  generateAnalysisComment,
  addAnalysisLabels,
  generateCopilotResponse
};