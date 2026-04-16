# src/github_client.py

import requests
import datetime

class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",  # 使用最新的 API 版本
            "User-Agent": "Python-GitHub-Script"  # GitHub API 强制要求 User-Agent
        }



    def fetch_updates(self, repo):
        # 获取特定 repo 的更新（commits, issues, pull requests）
        updates = {
            'commits': self.fetch_commits(repo),
            'issues': self.fetch_issues(repo),
            'pull_requests': self.fetch_pull_requests(repo)
        }
        return updates

    def fetch_commits(self, repo, count=100):
        url = f'https://api.github.com/repos/{repo}/commits'
        per_page = min(count, 100)
        params = {
            "per_page": per_page,
            "page": 1
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def fetch_issues(self, repo, count=100):
        url = f'https://api.github.com/repos/{repo}/issues'
        per_page = min(count, 100)
        params = {
            "sort": "created",
            "direction": "desc",
            "per_page": per_page,
            "page": 1,
            "state": "all"
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def fetch_pull_requests(self, repo, count=100):
        url = f'https://api.github.com/repos/{repo}/pulls'
        per_page = min(count, 100)
        params = {
            "sort": "created",
            "direction": "desc",
            "per_page": per_page,
            "page": 1,
            "state": "all"
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()


    def export_daily_progress(self, repo):
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        issues = self.fetch_issues(repo)
        pull_requests = self.fetch_pull_requests(repo)
        filename = f'daily_progress/{repo.replace("/", "_")}_{date_str}.md'
        with open(filename, 'w') as f:
            f.write(f"# {repo} Daily Progress - {date_str}\n\n")
            f.write("## Issues\n")
            for issue in issues:
                f.write(f"- {issue['title']} #{issue['number']}\n")
            f.write("\n## Pull Requests\n")
            for pr in pull_requests:
                f.write(f"- {pr['title']} #{pr['number']}\n")

        print(f"Exported daily progress to {filename}")

        return filename


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN') or 'your_github_token_here'
    
    print(f"Testing GitHubClient... {token}")
    client = GitHubClient(token=token)
    # #
    # issues = client.fetch_issues('langchain-ai/langchain', count=10)
    # print(issues)
    #
    # for issue in issues:
    #     print(issue['title'], issue['number'])
    #     print(f"title: {issue['title']} - number: {issue['number']}")
    #
    #
    filename = client.export_daily_progress('langchain-ai/langchain')
    print(f"Generated report: {filename}")
    
    # repo = 'langchain-ai/langchain'
    # updates = client.fetch_updates(repo)
    # print(updates)