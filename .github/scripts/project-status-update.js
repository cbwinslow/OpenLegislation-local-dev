/**
 * Project Status Update Script
 * Updates item status in Projects v2 based on GitHub events
 */

async function updateItemStatus({ github, context }) {
  console.log('Updating project item status...');

  let itemNumber, itemType, newStatus;

  if (context.eventName === 'issues') {
    itemNumber = context.payload.issue.number;
    itemType = 'issue';

    switch (context.payload.action) {
      case 'opened':
        newStatus = 'Todo';
        break;
      case 'assigned':
        newStatus = 'In Progress';
        break;
      case 'closed':
        newStatus = 'Done';
        break;
      case 'reopened':
        newStatus = 'In Progress';
        break;
      default:
        return; // No status change needed
    }
  } else if (context.eventName === 'pull_request') {
    itemNumber = context.payload.pull_request.number;
    itemType = 'pull_request';

    switch (context.payload.action) {
      case 'opened':
      case 'converted_to_draft':
        newStatus = 'In Progress';
        break;
      case 'ready_for_review':
        newStatus = 'In Review';
        break;
      case 'closed':
        newStatus = context.payload.pull_request.merged ? 'Done' : 'Cancelled';
        break;
      default:
        return;
    }
  } else {
    console.log('No item status update needed for this event');
    return;
  }

  try {
    // Find the project this item belongs to
    const projectId = await findItemProject(github, context, itemNumber, itemType);

    if (!projectId) {
      console.log(`No project found for ${itemType} #${itemNumber}`);
      return;
    }

    // Update the status
    await updateProjectStatus(github, projectId, itemNumber, itemType, newStatus);

    console.log(`Updated ${itemType} #${itemNumber} status to: ${newStatus}`);

  } catch (error) {
    console.error('Error updating project status:', error);
  }
}

async function findItemProject(github, context, itemNumber, itemType) {
  // Query to find which projects contain this item
  const query = `
    query FindItemProjects($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        ${itemType === 'issue' ? 'issue' : 'pullRequest'}(number: $number) {
          projectItems(first: 10) {
            nodes {
              project {
                id
                title
              }
            }
          }
        }
      }
    }
  `;

  try {
    const result = await github.graphql(query, {
      owner: context.repo.owner,
      repo: context.repo.repo,
      number: itemNumber
    });

    const item = result.repository[itemType === 'issue' ? 'issue' : 'pullRequest'];
    const projects = item.projectItems.nodes;

    if (projects.length === 0) {
      return null;
    }

    // Return the first project (you might want more sophisticated logic)
    return projects[0].project.id;

  } catch (error) {
    console.error('Error finding item project:', error);
    return null;
  }
}

async function updateProjectStatus(github, projectId, itemNumber, itemType, newStatus) {
  // First, get the project item ID
  const itemQuery = `
    query GetProjectItem($projectId: ID!, $owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        ${itemType === 'issue' ? 'issue' : 'pullRequest'}(number: $number) {
          projectItems(first: 1) {
            nodes {
              id
              project {
                fields(first: 20) {
                  nodes {
                    ... on ProjectV2Field {
                      id
                      name
                      dataType
                    }
                    ... on ProjectV2SingleSelectField {
                      id
                      name
                      options {
                        id
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  `;

  try {
    const result = await github.graphql(itemQuery, {
      projectId,
      owner: context.repo.owner,
      repo: context.repo.repo,
      number: itemNumber
    });

    const projectItem = result.repository[itemType === 'issue' ? 'issue' : 'pullRequest'].projectItems.nodes[0];
    if (!projectItem) {
      console.log('Project item not found');
      return;
    }

    const itemId = projectItem.id;
    const fields = projectItem.project.fields.nodes;

    // Find the status field
    const statusField = fields.find(field => field.name.toLowerCase().includes('status'));
    if (!statusField) {
      console.log('Status field not found in project');
      return;
    }

    // Find the option ID for the new status
    const statusOption = statusField.options?.find(option =>
      option.name.toLowerCase() === newStatus.toLowerCase()
    );

    if (!statusOption) {
      console.log(`Status option '${newStatus}' not found`);
      return;
    }

    // Update the field value
    const updateMutation = `
      mutation UpdateProjectField($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
        updateProjectV2ItemFieldValue(
          input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: { singleSelectOptionId: $value }
          }
        ) {
          projectV2Item {
            id
          }
        }
      }
    `;

    await github.graphql(updateMutation, {
      projectId,
      itemId,
      fieldId: statusField.id,
      value: statusOption.id
    });

    console.log(`Successfully updated status to: ${newStatus}`);

  } catch (error) {
    console.error('Error updating project status:', error);
    throw error;
  }
}

module.exports = {
  updateItemStatus,
  findItemProject,
  updateProjectStatus
};