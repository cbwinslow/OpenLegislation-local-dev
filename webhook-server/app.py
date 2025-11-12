"""
GitHub Webhook Server for Automated PR Review and Merge
Receives webhook events and uses OpenRouter AI for code review
"""
import os
import hmac
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
AUTO_MERGE_ENABLED = os.getenv('AUTO_MERGE_ENABLED', 'false').lower() == 'true'
REVIEW_THRESHOLD_SCORE = int(os.getenv('REVIEW_THRESHOLD_SCORE', '7'))

# Initialize OpenRouter client (using OpenAI-compatible interface)
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify that the payload was sent from GitHub by validating SHA256 signature."""
    if not signature_header or not GITHUB_WEBHOOK_SECRET:
        return False
    
    hash_object = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the diff for a pull request."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def get_pr_files(owner: str, repo: str, pr_number: int) -> list:
    """Get list of files changed in a PR."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def analyze_code_with_ai(pr_data: Dict[str, Any], diff: str, files: list) -> Dict[str, Any]:
    """
    Use OpenRouter AI to analyze the code changes.
    Returns a dict with review comments, score, and recommendation.
    """
    # Prepare context for AI
    pr_title = pr_data['title']
    pr_description = pr_data['body'] or 'No description provided'
    pr_author = pr_data['user']['login']
    
    # Limit diff size to avoid token limits
    max_diff_length = 8000
    if len(diff) > max_diff_length:
        diff = diff[:max_diff_length] + "\n... [diff truncated for length]"
    
    # Build file summary
    file_summary = "\n".join([
        f"- {f['filename']} (+{f['additions']} -{f['deletions']})"
        for f in files[:20]  # Limit to first 20 files
    ])
    
    prompt = f"""You are an expert code reviewer for the OpenLegislation project, a Java/Spring-based 
legislative data platform. Review this pull request and provide detailed feedback.

PR Title: {pr_title}
Author: {pr_author}
Description: {pr_description}

Files Changed:
{file_summary}

Diff:
```diff
{diff}
```

Please provide:
1. Overall assessment (APPROVE, REQUEST_CHANGES, or COMMENT)
2. Code quality score (1-10)
3. Specific issues found (security, bugs, style, performance)
4. Positive aspects
5. Suggestions for improvement

Format your response as JSON:
{{
    "recommendation": "APPROVE|REQUEST_CHANGES|COMMENT",
    "score": 8,
    "summary": "Brief summary of changes",
    "issues": [
        {{"severity": "high|medium|low", "category": "security|bug|style|performance", "description": "Issue description", "file": "filename", "line": 123}}
    ],
    "positives": ["Positive aspect 1", "Positive aspect 2"],
    "suggestions": ["Suggestion 1", "Suggestion 2"]
}}
"""
    
    try:
        response = openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code reviewer. Provide detailed, constructive feedback in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
        )
        
        # Extract JSON from response
        content = response.choices[0].message.content
        # Try to parse JSON, handling potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        review_data = json.loads(content)
        return review_data
    
    except Exception as e:
        app.logger.error(f"Error analyzing code with AI: {e}")
        # Return a safe default
        return {
            "recommendation": "COMMENT",
            "score": 5,
            "summary": "Unable to complete AI review",
            "issues": [{"severity": "low", "category": "other", "description": f"AI review failed: {str(e)}", "file": "", "line": 0}],
            "positives": [],
            "suggestions": ["Please review manually"]
        }


def post_review_comment(owner: str, repo: str, pr_number: int, review_data: Dict[str, Any]):
    """Post the AI review as a PR comment."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Format the review comment
    comment_body = f"""## 🤖 AI-Powered Code Review

**Overall Assessment:** {review_data['recommendation']}
**Quality Score:** {review_data['score']}/10

### Summary
{review_data['summary']}

"""
    
    # Add issues section
    if review_data['issues']:
        comment_body += "### 🔍 Issues Found\n\n"
        for issue in review_data['issues']:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue['severity'], "⚪")
            location = f" ({issue['file']}:{issue['line']})" if issue.get('file') and issue.get('line') else ""
            comment_body += f"{severity_emoji} **{issue['category'].upper()}** [{issue['severity']}]{location}\n"
            comment_body += f"   {issue['description']}\n\n"
    
    # Add positives section
    if review_data['positives']:
        comment_body += "### ✅ Positive Aspects\n\n"
        for positive in review_data['positives']:
            comment_body += f"- {positive}\n"
        comment_body += "\n"
    
    # Add suggestions section
    if review_data['suggestions']:
        comment_body += "### 💡 Suggestions\n\n"
        for suggestion in review_data['suggestions']:
            comment_body += f"- {suggestion}\n"
        comment_body += "\n"
    
    comment_body += "\n---\n*This review was generated by an AI agent. Human review is still recommended.*"
    
    # Map recommendation to GitHub review event
    event_map = {
        "APPROVE": "APPROVE",
        "REQUEST_CHANGES": "REQUEST_CHANGES",
        "COMMENT": "COMMENT"
    }
    event = event_map.get(review_data['recommendation'], 'COMMENT')
    
    review_payload = {
        "body": comment_body,
        "event": event
    }
    
    response = requests.post(url, headers=headers, json=review_payload)
    response.raise_for_status()
    return response.json()


def should_auto_merge(pr_data: Dict[str, Any], review_data: Dict[str, Any]) -> bool:
    """
    Determine if PR should be auto-merged based on review and rules.
    """
    if not AUTO_MERGE_ENABLED:
        return False
    
    # Check if PR is from Dependabot
    is_dependabot = pr_data['user']['login'] == 'dependabot[bot]'
    
    # Check AI review score
    score_acceptable = review_data['score'] >= REVIEW_THRESHOLD_SCORE
    
    # Check for high severity issues
    high_severity_issues = any(
        issue['severity'] == 'high' 
        for issue in review_data.get('issues', [])
    )
    
    # Check recommendation
    approved = review_data['recommendation'] == 'APPROVE'
    
    # Auto-merge if: (Dependabot OR high score) AND approved AND no high severity issues
    return (is_dependabot or score_acceptable) and approved and not high_severity_issues


def merge_pr(owner: str, repo: str, pr_number: int):
    """Merge the pull request."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    merge_payload = {
        "commit_title": f"Auto-merge PR #{pr_number}",
        "commit_message": "Automatically merged after AI review approval",
        "merge_method": "squash"
    }
    
    response = requests.put(url, headers=headers, json=merge_payload)
    response.raise_for_status()
    return response.json()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook endpoint for GitHub events.
    Handles pull request, issue, and project events for comprehensive automation.
    """
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        app.logger.warning("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 403

    # Get event type
    event_type = request.headers.get('X-GitHub-Event')

    payload = request.json
    action = payload.get('action')

    try:
        repo_full_name = payload['repository']['full_name']
        owner, repo = repo_full_name.split('/')

        app.logger.info(f"Processing {event_type} event ({action}) in {repo_full_name}")

        # Handle different event types
        if event_type == 'pull_request':
            return handle_pull_request_event(payload, owner, repo)
        elif event_type == 'issues':
            return handle_issue_event(payload, owner, repo)
        elif event_type == 'issue_comment':
            return handle_issue_comment_event(payload, owner, repo)
        elif event_type == 'project_card':
            return handle_project_card_event(payload, owner, repo)
        elif event_type == 'milestone':
            return handle_milestone_event(payload, owner, repo)
        else:
            return jsonify({'message': f'Ignoring {event_type} event'}), 200

    except Exception as e:
        app.logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500


def handle_pull_request_event(payload, owner, repo):
    """Handle pull request events."""
    pr_data = payload['pull_request']
    pr_number = pr_data['number']
    action = payload.get('action')

    # Handle opened and synchronize (new commits) events
    if action not in ['opened', 'synchronize', 'reopened', 'ready_for_review']:
        return jsonify({'message': f'Ignoring PR {action} action'}), 200

    app.logger.info(f"Processing PR #{pr_number} in {owner}/{repo}")

    # Skip draft PRs
    if pr_data.get('draft', False):
        app.logger.info(f"Skipping draft PR #{pr_number}")
        return jsonify({'message': 'Skipping draft PR'}), 200

    # Get PR diff and files
    diff = get_pr_diff(owner, repo, pr_number)
    files = get_pr_files(owner, repo, pr_number)

    # Analyze with AI
    app.logger.info(f"Analyzing PR #{pr_number} with AI")
    review_data = analyze_code_with_ai(pr_data, diff, files)

    # Post review comment
    app.logger.info(f"Posting review for PR #{pr_number}")
    post_review_comment(owner, repo, pr_number, review_data)

    # Add automation labels
    add_automation_labels(owner, repo, pr_number, 'pull_request', review_data)

    # Check if should auto-merge
    if should_auto_merge(pr_data, review_data):
        app.logger.info(f"Auto-merging PR #{pr_number}")
        merge_result = merge_pr(owner, repo, pr_number)
        return jsonify({
            'message': 'PR reviewed and merged',
            'review': review_data,
            'merge': merge_result
        }), 200

    return jsonify({
        'message': 'PR reviewed',
        'review': review_data
    }), 200


def handle_issue_event(payload, owner, repo):
    """Handle issue events."""
    issue = payload['issue']
    issue_number = issue['number']
    action = payload.get('action')

    if action not in ['opened', 'labeled', 'assigned', 'closed']:
        return jsonify({'message': f'Ignoring issue {action} action'}), 200

    app.logger.info(f"Processing issue #{issue_number} in {owner}/{repo}")

    # Auto-label issues based on content
    if action == 'opened':
        labels = generate_issue_labels(issue)
        if labels:
            add_labels_to_issue(owner, repo, issue_number, labels)

    # Link to projects if milestone is set
    if issue.get('milestone'):
        link_issue_to_milestone_project(owner, repo, issue, issue['milestone'])

    return jsonify({'message': 'Issue processed'}), 200


def handle_issue_comment_event(payload, owner, repo):
    """Handle issue comment events."""
    comment = payload['comment']
    issue = payload['issue']
    issue_number = issue['number']
    comment_body = comment['body']

    app.logger.info(f"Processing comment on issue #{issue_number}")

    # Check for automation commands
    if '@copilot' in comment_body.lower():
        handle_copilot_command(owner, repo, issue_number, comment_body, comment['user']['login'])
    elif any(cmd in comment_body.lower() for cmd in ['/assign', '/label', '/milestone']):
        handle_automation_command(owner, repo, issue_number, comment_body)

    return jsonify({'message': 'Comment processed'}), 200


def handle_project_card_event(payload, owner, repo):
    """Handle project card events."""
    # This would handle project board automation
    # Implementation depends on Projects v1 vs v2
    app.logger.info(f"Processing project card event in {owner}/{repo}")
    return jsonify({'message': 'Project card event processed'}), 200


def handle_milestone_event(payload, owner, repo):
    """Handle milestone events."""
    milestone = payload['milestone']
    action = payload.get('action')

    if action == 'opened':
        # Create project board for milestone
        create_milestone_project(owner, repo, milestone)

    app.logger.info(f"Processing milestone {action} event in {owner}/{repo}")
    return jsonify({'message': 'Milestone event processed'}), 200


def generate_issue_labels(issue):
    """Generate appropriate labels for an issue based on content."""
    labels = []
    title = issue['title'].lower()
    body = (issue.get('body') or '').lower()

    # Categorize by keywords
    if any(word in title + body for word in ['bug', 'error', 'fix', 'broken']):
        labels.append('bug')
    if any(word in title + body for word in ['feature', 'enhancement', 'add']):
        labels.append('enhancement')
    if any(word in title + body for word in ['docs', 'documentation', 'readme']):
        labels.append('documentation')
    if any(word in title + body for word in ['federal', 'congress', 'govinfo']):
        labels.append('federal-data')
    if any(word in title + body for word in ['database', 'postgres', 'sql']):
        labels.append('database')
    if any(word in title + body for word in ['security', 'auth', 'login']):
        labels.append('security')

    return labels


def add_labels_to_issue(owner, repo, issue_number, labels):
    """Add labels to an issue."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/labels"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.post(url, headers=headers, json={"labels": labels})
    if response.status_code == 200:
        app.logger.info(f"Added labels {labels} to issue #{issue_number}")
    else:
        app.logger.error(f"Failed to add labels to issue #{issue_number}: {response.text}")


def add_automation_labels(owner, repo, item_number, item_type, review_data=None):
    """Add automation-related labels."""
    labels = []

    if item_type == 'pull_request' and review_data:
        # Add based on AI review score
        score = review_data.get('score', 5)
        if score >= 8:
            labels.append('ai-review:approved')
        elif score >= 6:
            labels.append('ai-review:needs-improvement')
        else:
            labels.append('ai-review:requires-changes')

        # Add based on issues found
        issues = review_data.get('issues', [])
        high_issues = [i for i in issues if i.get('severity') == 'high']
        if high_issues:
            labels.append('priority:high')
        elif issues:
            labels.append('priority:medium')

    if labels:
        endpoint = 'issues' if item_type == 'pull_request' else 'issues'
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/{endpoint}/{item_number}/labels"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.post(url, headers=headers, json={"labels": labels})
        if response.status_code == 200:
            app.logger.info(f"Added automation labels {labels} to {item_type} #{item_number}")


def handle_copilot_command(owner, repo, issue_number, comment_body, user):
    """Handle @copilot commands in comments."""
    # Extract command after @copilot
    command = comment_body.lower().split('@copilot')[1].strip()

    response = f"🤖 Copilot command received from @{user}: `{command}`\\n\\n"

    if 'analyze' in command:
        response += "I'll analyze this issue/PR and provide insights.\\n"
        # Add logic to trigger analysis
    elif 'review' in command:
        response += "I'll perform a detailed code review.\\n"
        # Add logic to trigger review
    elif 'test' in command:
        response += "I'll generate or run tests for this.\\n"
        # Add logic to trigger testing
    else:
        response += "Available commands: analyze, review, test\\n"

    # Post response comment
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    requests.post(url, headers=headers, json={"body": response})


def handle_automation_command(owner, repo, issue_number, comment_body):
    """Handle automation commands like /assign, /label, etc."""
    # Implementation for handling automation commands
    app.logger.info(f"Automation command detected in comment on issue #{issue_number}")


def link_issue_to_milestone_project(owner, repo, issue, milestone):
    """Link issue to milestone-specific project."""
    # Implementation for Projects v2 integration
    app.logger.info(f"Would link issue #{issue['number']} to milestone {milestone['title']} project")


def create_milestone_project(owner, repo, milestone):
    """Create a project board for a milestone."""
    # Implementation for creating milestone projects
    app.logger.info(f"Would create project for milestone {milestone['title']}")


# Original webhook route (keeping for backward compatibility)
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook endpoint for GitHub events.
    Handles pull request, issue, and project events for comprehensive automation.
    """
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        app.logger.warning("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 403

    # Get event type
    event_type = request.headers.get('X-GitHub-Event')

    payload = request.json
    action = payload.get('action')

    try:
        repo_full_name = payload['repository']['full_name']
        owner, repo = repo_full_name.split('/')

        app.logger.info(f"Processing {event_type} event ({action}) in {repo_full_name}")

        # Handle different event types
        if event_type == 'pull_request':
            return handle_pull_request_event(payload, owner, repo)
        elif event_type == 'issues':
            return handle_issue_event(payload, owner, repo)
        elif event_type == 'issue_comment':
            return handle_issue_comment_event(payload, owner, repo)
        elif event_type == 'project_card':
            return handle_project_card_event(payload, owner, repo)
        elif event_type == 'milestone':
            return handle_milestone_event(payload, owner, repo)
        else:
            return jsonify({'message': f'Ignoring {event_type} event'}), 200

    except Exception as e:
        app.logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service info."""
    return jsonify({
        'service': 'OpenLegislation PR Automation Webhook',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'webhook': '/webhook (POST)'
        },
        'status': 'running'
    })


if __name__ == '__main__':
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
