/**
 * Projects v2 Automation Scripts for OpenLegislation
 * Handles syncing issues and PRs to project boards
 */

async function syncItemsToProjects({ github, context }) {
  console.log('Starting project sync...');

  try {
    // Get all open issues
    const { data: issues } = await github.rest.issues.listForRepo({
      owner: context.repo.owner,
      repo: context.repo.repo,
      state: 'open',
      per_page: 100
    });

    // Get all open PRs
    const { data: pulls } = await github.rest.pulls.list({
      owner: context.repo.owner,
      repo: context.repo.repo,
      state: 'open',
      per_page: 100
    });

    console.log(`Found ${issues.length} open issues and ${pulls.length} open PRs`);

    // Get user's projects (you'll need to configure which projects to sync to)
    // This is a simplified example - you'd want to configure specific project IDs

    // For each issue/PR, determine which project it should be in based on labels, milestones, etc.
    for (const issue of issues) {
      await categorizeAndAddToProject(github, context, issue, 'issue');
    }

    for (const pr of pulls) {
      await categorizeAndAddToProject(github, context, pr, 'pull_request');
    }

  } catch (error) {
    console.error('Error in project sync:', error);
    throw error;
  }
}

async function categorizeAndAddToProject(github, context, item, itemType) {
  const labels = item.labels?.map(l => l.name) || [];
  const milestone = item.milestone;

  // Determine project based on labels and milestone
  let targetProjectId = null;
  let status = 'Todo';

  // Example categorization logic
  if (labels.includes('bug')) {
    // Add to bug fixes project
    targetProjectId = process.env.BUG_FIXES_PROJECT_ID;
    status = 'In Progress';
  } else if (labels.includes('enhancement')) {
    // Add to features project
    targetProjectId = process.env.FEATURES_PROJECT_ID;
    status = 'In Progress';
  } else if (milestone) {
    // Add to milestone-specific project
    targetProjectId = await getMilestoneProjectId(github, context, milestone.title);
  }

  if (targetProjectId) {
    await addItemToProject(github, context, item, itemType, targetProjectId, status);
  }
}

async function getMilestoneProjectId(github, context, milestoneTitle) {
  // Query projects to find one matching the milestone
  // This is a simplified version - you'd need to implement proper project lookup
  const projectTitle = `Sprint: ${milestoneTitle}`;

  try {
    const projectsQuery = `
      query GetProjects($owner: String!) {
        user(login: $owner) {
          projectsV2(first: 20) {
            nodes {
              id
              title
              number
            }
          }
        }
      }
    `;

    const result = await github.graphql(projectsQuery, {
      owner: context.repo.owner
    });

    const projects = result.user?.projectsV2?.nodes || [];
    const project = projects.find(p => p.title === projectTitle);

    return project?.id || null;
  } catch (error) {
    console.error('Error finding milestone project:', error);
    return null;
  }
}

async function addItemToProject(github, context, item, itemType, projectId, status) {
  try {
    // First, get the item ID for the project
    const itemIdQuery = `
      query GetItemId($owner: String!, $repo: String!, $number: Int!) {
        repository(owner: $owner, name: $repo) {
          ${itemType === 'issue' ? 'issue' : 'pullRequest'}(number: $number) {
            id
          }
        }
      }
    `;

    const itemResult = await github.graphql(itemIdQuery, {
      owner: context.repo.owner,
      repo: context.repo.repo,
      number: item.number
    });

    const itemId = itemResult.repository[itemType === 'issue' ? 'issue' : 'pullRequest'].id;

    // Add item to project
    const addItemMutation = `
      mutation AddItemToProject($projectId: ID!, $itemId: ID!) {
        addProjectV2ItemById(input: { projectId: $projectId, contentId: $itemId }) {
          item {
            id
          }
        }
      }
    `;

    await github.graphql(addItemMutation, {
      projectId,
      itemId
    });

    console.log(`Added ${itemType} #${item.number} to project`);

    // Update status if needed
    if (status !== 'Todo') {
      await updateProjectItemStatus(github, projectId, itemId, status);
    }

  } catch (error) {
    console.error(`Error adding ${itemType} #${item.number} to project:`, error);
  }
}

async function updateProjectItemStatus(github, projectId, itemId, status) {
  // This would require knowing the field IDs for your project
  // Implementation depends on your specific project configuration
  console.log(`Would update status to: ${status}`);
}

module.exports = {
  syncItemsToProjects,
  categorizeAndAddToProject,
  getMilestoneProjectId,
  addItemToProject,
  updateProjectItemStatus
};