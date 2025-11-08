/**
 * Copilot Review Summary Script
 * Generates comprehensive review summary from all Copilot analyses
 */

async function generateSummary({ github, context }) {
  const pr = context.payload.pull_request;
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  console.log(`Generating review summary for PR #${pr.number}`);

  try {
    // Get all comments on the PR
    const { data: comments } = await github.rest.issues.listComments({
      owner,
      repo,
      issue_number: pr.number,
      per_page: 100
    });

    // Filter Copilot comments
    const copilotComments = comments.filter(comment =>
      comment.body.includes('🤖 **Copilot') ||
      comment.user.login === 'github-actions' // Assuming Copilot runs as actions
    );

    // Analyze the PR status
    const { data: prData } = await github.rest.pulls.get({
      owner,
      repo,
      pull_number: pr.number
    });

    // Get check runs
    const { data: checks } = await github.rest.checks.listForRef({
      owner,
      repo,
      ref: pr.head.sha,
      per_page: 100
    });

    // Generate summary
    const summary = await createComprehensiveSummary(prData, copilotComments, checks);

    // Post summary comment
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: pr.number,
      body: summary
    });

    // Update PR labels based on summary
    await updateSummaryLabels(github, context, summary);

  } catch (error) {
    console.error('Error generating summary:', error);
  }
}

async function createComprehensiveSummary(prData, copilotComments, checks) {
  let summary = '🤖 **Copilot Comprehensive Review Summary**\\n\\n';

  // PR Overview
  summary += `## 📋 PR Overview\\n`;
  summary += `- **Title:** ${prData.title}\\n`;
  summary += `- **Author:** @${prData.user.login}\\n`;
  summary += `- **Changes:** +${prData.additions} -${prData.deletions}\\n`;
  summary += `- **Files:** ${prData.changed_files}\\n`;
  summary += `- **Commits:** ${prData.commits}\\n\\n`;

  // CI/CD Status
  summary += `## 🔄 CI/CD Status\\n`;
  const checkSummary = analyzeChecks(checks);
  summary += checkSummary.status + '\\n\\n';

  // Copilot Analysis Summary
  summary += `## 🤖 Copilot Analysis\\n`;

  if (copilotComments.length === 0) {
    summary += 'No Copilot analyses found.\\n\\n';
  } else {
    const analyses = extractAnalysesFromComments(copilotComments);
    summary += analyses.summary + '\\n\\n';
  }

  // Risk Assessment
  summary += `## ⚠️ Risk Assessment\\n`;
  const riskLevel = assessOverallRisk(prData, checks, copilotComments);
  summary += riskLevel + '\\n\\n';

  // Recommendations
  summary += `## 💡 Recommendations\\n`;
  const recommendations = generateRecommendations(prData, checks, copilotComments);
  summary += recommendations + '\\n\\n';

  // Next Steps
  summary += `## 🚀 Next Steps\\n`;
  const nextSteps = determineNextSteps(checkSummary, riskLevel);
  summary += nextSteps + '\\n\\n';

  summary += '---\\n*This summary was generated automatically. Please review all feedback before merging.*';

  return summary;
}

function analyzeChecks(checks) {
  const checkRuns = checks.check_runs || [];
  const total = checkRuns.length;
  const successful = checkRuns.filter(run => run.conclusion === 'success').length;
  const failed = checkRuns.filter(run => run.conclusion === 'failure').length;
  const pending = checkRuns.filter(run => run.status === 'in_progress' || run.status === 'queued').length;

  let status = `✅ **${successful}/${total}** checks passed`;

  if (failed > 0) {
    status = `❌ **${failed}** checks failed, **${successful}/${total}** passed`;
  } else if (pending > 0) {
    status = `⏳ **${pending}** checks pending, **${successful}/${total}** passed`;
  }

  return { status, successful, failed, pending, total };
}

function extractAnalysesFromComments(comments) {
  const analyses = {
    concerns: [],
    suggestions: [],
    categories: new Set(),
    riskLevels: []
  };

  comments.forEach(comment => {
    const body = comment.body;

    // Extract concerns
    const concernMatches = body.match(/⚠️ \*\*Concerns:\*\*([\s\S]*?)(?=\\n\\n|\*\*|$)/);
    if (concernMatches) {
      analyses.concerns.push(...concernMatches[1].split('\\n').filter(line => line.trim()));
    }

    // Extract suggestions
    const suggestionMatches = body.match(/💡 \*\*Suggestions:\*\*([\s\S]*?)(?=\\n\\n|\*\*|$)/);
    if (suggestionMatches) {
      analyses.suggestions.push(...suggestionMatches[1].split('\\n').filter(line => line.trim()));
    }

    // Extract risk levels
    const riskMatches = body.match(/Risk Level: (\w+)/);
    if (riskMatches) {
      analyses.riskLevels.push(riskMatches[1]);
    }
  });

  let summary = '';
  if (analyses.concerns.length > 0) {
    summary += `**Concerns:** ${analyses.concerns.length} items identified\\n`;
  }
  if (analyses.suggestions.length > 0) {
    summary += `**Suggestions:** ${analyses.suggestions.length} improvements proposed\\n`;
  }
  if (analyses.riskLevels.length > 0) {
    const avgRisk = analyses.riskLevels.includes('high') ? 'high' :
                   analyses.riskLevels.includes('medium') ? 'medium' : 'low';
    summary += `**Overall Risk:** ${avgRisk}\\n`;
  }

  return { summary: summary || 'No major issues detected', analyses };
}

function assessOverallRisk(prData, checks, copilotComments) {
  let riskScore = 0;

  // Size risk
  const totalChanges = prData.additions + prData.deletions;
  if (totalChanges > 1000) riskScore += 3;
  else if (totalChanges > 100) riskScore += 2;
  else if (totalChanges > 50) riskScore += 1;

  // CI risk
  const checkAnalysis = analyzeChecks(checks);
  if (checkAnalysis.failed > 0) riskScore += 3;
  else if (checkAnalysis.pending > 0) riskScore += 1;

  // Copilot risk
  const analyses = extractAnalysesFromComments(copilotComments);
  if (analyses.analyses.riskLevels.includes('high')) riskScore += 2;
  else if (analyses.analyses.riskLevels.includes('medium')) riskScore += 1;

  // Determine level
  if (riskScore >= 5) return '🔴 **High Risk** - Requires careful review';
  else if (riskScore >= 3) return '🟡 **Medium Risk** - Review recommended';
  else return '🟢 **Low Risk** - Ready for merge';
}

function generateRecommendations(prData, checks, copilotComments) {
  const recommendations = [];

  const checkAnalysis = analyzeChecks(checks);
  if (checkAnalysis.failed > 0) {
    recommendations.push('- Address failing CI/CD checks before merging');
  }

  const analyses = extractAnalysesFromComments(copilotComments);
  if (analyses.analyses.concerns.length > 0) {
    recommendations.push('- Review and address Copilot-identified concerns');
  }

  if (analyses.analyses.suggestions.length > 0) {
    recommendations.push('- Consider implementing Copilot suggestions for code quality');
  }

  if (prData.changed_files > 20) {
    recommendations.push('- Large number of files changed - consider thorough testing');
  }

  return recommendations.length > 0 ?
    recommendations.map(rec => `- ${rec}`).join('\\n') :
    '- No specific recommendations - PR appears ready';
}

function determineNextSteps(checkSummary, riskLevel) {
  const steps = [];

  if (checkSummary.includes('❌')) {
    steps.push('- Fix failing CI/CD checks');
  }

  if (riskLevel.includes('High Risk')) {
    steps.push('- Schedule thorough code review');
    steps.push('- Consider breaking into smaller PRs');
  } else if (riskLevel.includes('Medium Risk')) {
    steps.push('- Address any outstanding concerns');
    steps.push('- Ensure adequate test coverage');
  } else {
    steps.push('- Ready for final review and merge');
  }

  return steps.map(step => `- ${step}`).join('\\n');
}

async function updateSummaryLabels(github, context, summary) {
  const labels = [];

  if (summary.includes('High Risk')) labels.push('review:required');
  else if (summary.includes('Medium Risk')) labels.push('review:recommended');
  else labels.push('review:optional');

  if (summary.includes('checks failed')) labels.push('ci:failed');
  else if (summary.includes('checks pending')) labels.push('ci:pending');
  else labels.push('ci:passed');

  try {
    await github.rest.issues.addLabels({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: context.payload.pull_request.number,
      labels
    });
  } catch (error) {
    console.error('Error updating summary labels:', error);
  }
}

module.exports = {
  generateSummary,
  createComprehensiveSummary,
  analyzeChecks,
  extractAnalysesFromComments,
  assessOverallRisk,
  generateRecommendations,
  determineNextSteps,
  updateSummaryLabels
};