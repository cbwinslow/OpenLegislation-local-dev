#!/usr/bin/env python3
"""
GitHub Automation Script for OpenLegislation

This script automates various GitHub operations including:
- Issue creation and management
- Project board (Projects v2) management
- Milestone creation and tracking
- Label management
- Wiki page creation
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import json


class GitHubAutomation:
    """Automation for GitHub repository management"""
    
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to GitHub API"""
        url = f"{self.base_url}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=self.headers)
        elif method == "POST":
            response = requests.post(url, headers=self.headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=self.headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=self.headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    def _graphql_request(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Make a GraphQL request to GitHub API"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(
            self.graphql_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Issue Management ====================
    
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None
    ) -> Dict:
        """Create a new issue"""
        data = {
            "title": title,
            "body": body
        }
        
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        if milestone:
            data["milestone"] = milestone
        
        endpoint = f"repos/{self.owner}/{self.repo}/issues"
        return self._make_request("POST", endpoint, data)
    
    def bulk_create_issues(self, issues: List[Dict]) -> List[Dict]:
        """Create multiple issues from a list"""
        results = []
        for issue_data in issues:
            try:
                result = self.create_issue(**issue_data)
                results.append(result)
                print(f"✓ Created issue: {result['title']} (#{result['number']})")
            except Exception as e:
                print(f"✗ Failed to create issue: {issue_data['title']} - {e}")
                results.append({"error": str(e), "issue": issue_data})
        
        return results
    
    def link_issues(self, issue_number: int, related_issues: List[int]) -> None:
        """Link related issues by adding comments"""
        links = "\n".join([f"- Related to #{num}" for num in related_issues])
        body = f"🔗 **Related Issues:**\n{links}"
        
        endpoint = f"repos/{self.owner}/{self.repo}/issues/{issue_number}/comments"
        self._make_request("POST", endpoint, {"body": body})
    
    # ==================== Label Management ====================
    
    def create_label(self, name: str, color: str, description: str = "") -> Dict:
        """Create a new label"""
        data = {
            "name": name,
            "color": color,
            "description": description
        }
        
        endpoint = f"repos/{self.owner}/{self.repo}/labels"
        return self._make_request("POST", endpoint, data)
    
    def create_standard_labels(self) -> List[Dict]:
        """Create a standard set of labels for the repository"""
        labels = [
            # Type labels
            {"name": "type: bug", "color": "d73a4a", "description": "Something isn't working"},
            {"name": "type: feature", "color": "a2eeef", "description": "New feature or request"},
            {"name": "type: enhancement", "color": "84b6eb", "description": "Improvement to existing feature"},
            {"name": "type: documentation", "color": "0075ca", "description": "Documentation improvements"},
            {"name": "type: refactor", "color": "fbca04", "description": "Code refactoring"},
            
            # Priority labels
            {"name": "priority: critical", "color": "b60205", "description": "Critical priority"},
            {"name": "priority: high", "color": "d93f0b", "description": "High priority"},
            {"name": "priority: medium", "color": "fbca04", "description": "Medium priority"},
            {"name": "priority: low", "color": "0e8a16", "description": "Low priority"},
            
            # Status labels
            {"name": "status: in-progress", "color": "d4c5f9", "description": "Work in progress"},
            {"name": "status: needs-review", "color": "c5def5", "description": "Needs review"},
            {"name": "status: blocked", "color": "d93f0b", "description": "Blocked by other issues"},
            {"name": "status: ready", "color": "0e8a16", "description": "Ready to be worked on"},
            
            # Domain labels
            {"name": "domain: federal-data", "color": "1d76db", "description": "Federal data integration"},
            {"name": "domain: database", "color": "5319e7", "description": "Database related"},
            {"name": "domain: api", "color": "0e8a16", "description": "API related"},
            {"name": "domain: frontend", "color": "bfdadc", "description": "Frontend related"},
            {"name": "domain: ci-cd", "color": "ededed", "description": "CI/CD and automation"},
            
            # Size labels
            {"name": "size: xs", "color": "c2e0c6", "description": "Extra small change"},
            {"name": "size: s", "color": "7fc97f", "description": "Small change"},
            {"name": "size: m", "color": "fdc086", "description": "Medium change"},
            {"name": "size: l", "color": "f46d43", "description": "Large change"},
            {"name": "size: xl", "color": "d73027", "description": "Extra large change"},
        ]
        
        results = []
        for label in labels:
            try:
                result = self.create_label(**label)
                results.append(result)
                print(f"✓ Created label: {label['name']}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 422:
                    print(f"⊙ Label already exists: {label['name']}")
                else:
                    print(f"✗ Failed to create label: {label['name']} - {e}")
        
        return results
    
    # ==================== Milestone Management ====================
    
    def create_milestone(
        self,
        title: str,
        description: str = "",
        due_on: Optional[str] = None,
        state: str = "open"
    ) -> Dict:
        """Create a new milestone"""
        data = {
            "title": title,
            "description": description,
            "state": state
        }
        
        if due_on:
            data["due_on"] = due_on
        
        endpoint = f"repos/{self.owner}/{self.repo}/milestones"
        return self._make_request("POST", endpoint, data)
    
    def create_project_milestones(self) -> List[Dict]:
        """Create standard project milestones"""
        milestones = [
            {
                "title": "Q1 2025 - Federal Data Integration",
                "description": "Complete federal data integration from Congress.gov and GovInfo",
                "due_on": "2025-03-31T23:59:59Z"
            },
            {
                "title": "Q2 2025 - API Enhancements",
                "description": "Enhance REST API with new endpoints and improved documentation",
                "due_on": "2025-06-30T23:59:59Z"
            },
            {
                "title": "Q3 2025 - Performance Optimization",
                "description": "Database and search performance improvements",
                "due_on": "2025-09-30T23:59:59Z"
            },
            {
                "title": "Q4 2025 - Documentation & Testing",
                "description": "Comprehensive documentation and test coverage improvements",
                "due_on": "2025-12-31T23:59:59Z"
            }
        ]
        
        results = []
        for milestone in milestones:
            try:
                result = self.create_milestone(**milestone)
                results.append(result)
                print(f"✓ Created milestone: {milestone['title']}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 422:
                    print(f"⊙ Milestone already exists: {milestone['title']}")
                else:
                    print(f"✗ Failed to create milestone: {milestone['title']} - {e}")
        
        return results
    
    # ==================== Projects v2 Management ====================
    
    def get_user_id(self) -> str:
        """Get the user ID for creating projects"""
        query = """
        query {
            viewer {
                id
                login
            }
        }
        """
        result = self._graphql_request(query)
        return result["data"]["viewer"]["id"]
    
    def create_project_v2(self, title: str, description: str = "") -> Dict:
        """Create a new Projects v2 board"""
        user_id = self.get_user_id()
        
        mutation = """
        mutation($userId: ID!, $title: String!) {
            createProjectV2(input: {ownerId: $userId, title: $title}) {
                projectV2 {
                    id
                    title
                    url
                }
            }
        }
        """
        
        variables = {
            "userId": user_id,
            "title": title
        }
        
        result = self._graphql_request(mutation, variables)
        return result["data"]["createProjectV2"]["projectV2"]
    
    def create_standard_projects(self) -> List[Dict]:
        """Create standard project boards"""
        projects = [
            {
                "title": "OpenLegislation Development",
                "description": "Main development board for OpenLegislation"
            },
            {
                "title": "Federal Data Integration Sprint",
                "description": "Sprint board for federal data integration work"
            },
            {
                "title": "Bug Triage & Fixes",
                "description": "Board for tracking and fixing bugs"
            },
            {
                "title": "Documentation Improvement",
                "description": "Board for documentation tasks"
            }
        ]
        
        results = []
        for project in projects:
            try:
                result = self.create_project_v2(**project)
                results.append(result)
                print(f"✓ Created project: {project['title']}")
            except Exception as e:
                print(f"✗ Failed to create project: {project['title']} - {e}")
        
        return results
    
    # ==================== Wiki Management ====================
    
    def create_wiki_page(self, title: str, content: str) -> bool:
        """
        Create a wiki page
        Note: GitHub API doesn't directly support wiki operations.
        This would require git operations on the wiki repository.
        """
        # Wiki pages are managed through git
        # This is a placeholder for the actual implementation
        print(f"Wiki page creation for '{title}' requires git operations")
        print("Use: git clone https://github.com/{owner}/{repo}.wiki.git")
        return False


def create_initial_project_structure(token: str, owner: str, repo: str):
    """Create initial project structure with issues, labels, milestones, etc."""
    
    automation = GitHubAutomation(token, owner, repo)
    
    print("=" * 80)
    print("Creating Standard Labels...")
    print("=" * 80)
    automation.create_standard_labels()
    
    print("\n" + "=" * 80)
    print("Creating Project Milestones...")
    print("=" * 80)
    automation.create_project_milestones()
    
    print("\n" + "=" * 80)
    print("Creating Project Boards...")
    print("=" * 80)
    try:
        automation.create_standard_projects()
    except Exception as e:
        print(f"Note: Projects v2 creation may require additional permissions: {e}")
    
    print("\n" + "=" * 80)
    print("Creating Sample Issues...")
    print("=" * 80)
    
    sample_issues = [
        {
            "title": "Set up automated code quality checks",
            "body": "Configure automated code quality tools including PMD, Checkstyle, and Spotless",
            "labels": ["type: enhancement", "domain: ci-cd", "priority: high"]
        },
        {
            "title": "Improve federal data ingestion error handling",
            "body": "Add better error handling and retry logic for federal data ingestion processes",
            "labels": ["type: enhancement", "domain: federal-data", "priority: medium"]
        },
        {
            "title": "Document API endpoints",
            "body": "Create comprehensive API documentation with examples",
            "labels": ["type: documentation", "domain: api", "priority: medium"]
        }
    ]
    
    automation.bulk_create_issues(sample_issues)
    
    print("\n" + "=" * 80)
    print("✓ Project structure setup complete!")
    print("=" * 80)


def main():
    """Main entry point"""
    
    # Get configuration from environment variables
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_REPOSITORY_OWNER", "cbwinslow")
    repo = os.getenv("GITHUB_REPOSITORY_NAME", "OpenLegislation-local-dev")
    
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Usage: export GITHUB_TOKEN=your_token_here")
        sys.exit(1)
    
    # Create initial structure
    create_initial_project_structure(token, owner, repo)


if __name__ == "__main__":
    main()
