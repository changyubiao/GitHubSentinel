# src/github_client_v2.py

import requests
import time
from datetime import datetime, date, timedelta
import os
from logger import LOG
from urllib.parse import urlparse


class GitHubClient:
    """
    GitHub Client V2 - 基于 GitHub Search API 实现
    与 GitHubClient 保持接口一致性，但使用搜索API获取更精确的结果
    """
    
    def __init__(self, token):
        self.token = token  # GitHub API令牌
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = "https://api.github.com/search/issues"

    def fetch_updates(self, repo, since=None, until=None):
        """
        获取指定仓库的更新，可以指定开始和结束日期
        
        参数:
            repo: 仓库名称 (格式: "owner/repo")
            since: 开始日期 (格式: "YYYY-MM-DD")
            until: 结束日期 (格式: "YYYY-MM-DD")
        
        返回:
            dict: 包含 commits, issues, pull_requests 的字典
        """
        updates = {
            'commits': self.fetch_commits(repo, since, until),
            'issues': self.fetch_issues(repo, since, until),
            'pull_requests': self.fetch_pull_requests(repo, since, until)
        }
        return updates

    def _search_github_items(self, repo, since=None, until=None, item_type="issue", state="all"):
        """
        使用 GitHub Search API 搜索 Issues/PRs
        
        参数:
            repo: 仓库名称
            since: 开始日期
            until: 结束日期
            item_type: "issue" 或 "pr"
            state: "open", "closed", "all"
        
        返回:
            list: 搜索结果列表
        """
        # 构造查询语句
        query_parts = [f"repo:{repo}"]
        
        if item_type == "issue":
            query_parts.append("type:issue")
        elif item_type == "pr":
            query_parts.append("type:pr")
        
        # 添加日期范围
        if since and until:
            query_parts.append(f"created:{since}..{until}")
        elif since:
            query_parts.append(f"created:>={since}")
        elif until:
            query_parts.append(f"created:<={until}")
        
        # 添加状态筛选
        if state and state != "all":
            query_parts.append(f"state:{state}")
        
        query = " ".join(query_parts)
        
        all_items = []
        page = 1
        
        LOG.info(f"Searching GitHub {item_type}s in {repo}, query: {query}")
        
        while True:
            params = {
                "q": query,
                "per_page": 100,  # 每页最大100条
                "page": page
            }
            LOG.info(f"Fetching page {page}...")
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                error_msg = response.json().get('message', 'Unknown error')
                LOG.error(f"Error {response.status_code}: {error_msg}, page: {page}")
                break
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                LOG.info(f"No more issues found, page: {page}, item_type: {item_type}, repo: {repo}")
                break
                
            all_items.extend(items)
            LOG.debug(f"Fetched page {page}, got {len(items)} items")
            
            # 检查是否还有更多页面
            if len(items) < 100:
                LOG.info(f"No more issues found, page: {page}, total items: {len(all_items)},item_type: {item_type},repo: {repo}")
                break
            
            page += 1
            time.sleep(0.5)  # 避免触发限流
        
        LOG.info(f"Total found: {len(all_items)} {item_type}(s)")
        return all_items

    def fetch_commits(self, repo, since=None, until=None):
        """
        获取提交记录
        注意: Search API 不直接支持搜索 commits，这里返回空列表
        如需获取 commits，建议使用原有的 GitHubClient
        """
        LOG.warning("GitHubClientV2 does not support fetching commits via Search API. Returning empty list.")
        return []

    def fetch_issues(self, repo, since=None, until=None, state="closed"):
        """
        获取问题列表
        
        参数:
            repo: 仓库名称
            since: 开始日期
            until: 结束日期
            state: 问题状态 ("open", "closed", "all")，默认 "closed"
        
        返回:
            list: Issues 列表
        """
        return self._search_github_items(repo, since, until, item_type="issue", state=state)

    def fetch_pull_requests(self, repo, since=None, until=None, state="closed"):
        """
        获取拉取请求列表
        
        参数:
            repo: 仓库名称
            since: 开始日期
            until: 结束日期
            state: PR状态 ("open", "closed", "all")，默认 "closed"
        
        返回:
            list: Pull Requests 列表
        """
        return self._search_github_items(repo, since, until, item_type="pr", state=state)

    def export_daily_progress(self, repo):
        """
        导出每日进展报告
        
        参数:
            repo: 仓库名称
        
        返回:
            str: 生成的文件路径
        """
        today = datetime.now().date().isoformat()
        updates = self.fetch_updates(repo, since=today)
        
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))
        os.makedirs(repo_dir, exist_ok=True)
        
        file_path = os.path.join(repo_dir, f'{today}.md')
        with open(file_path, 'w') as file:
            file.write(f"# Daily Progress for {repo} ({today})\n\n")
            file.write("\n## Issues Closed Today\n")
            for issue in updates['issues']:
                file.write(f"- {issue['title']} #{issue['number']}\n")
            file.write("\n## Pull Requests Merged Today\n")
            for pr in updates['pull_requests']:
                file.write(f"- {pr['title']} #{pr['number']}\n")
        
        LOG.info(f"Exported daily progress to {file_path}")
        return file_path

    def export_progress_by_date_range(self, repo, days:int=1):
        """
        导出指定日期范围内的进展报告
        
        参数:
            repo: 仓库名称
            days: 天数（从今天往前推） 默认1 天
        
        返回:
            str: 生成的文件路径
        """
        today = date.today()
        since = today - timedelta(days=days)
        
        updates = self.fetch_updates(
            repo, 
            since=since.isoformat(), 
            until=today.isoformat()
        )
        
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))
        os.makedirs(repo_dir, exist_ok=True)
        
        # 更新文件名以包含日期范围
        date_str = f"{since}_to_{today}"
        file_path = os.path.join(repo_dir, f'{date_str}.md')
        
        with open(file_path, 'w') as file:
            file.write(f"# Progress for {repo} ({since} to {today})\n\n")
            file.write(f"\n## Issues Closed in the Last {days} Days\n")
            for issue in updates['issues']:
                file.write(f"- {issue['title']} #{issue['number']}\n")
            file.write(f"\n## Pull Requests Merged in the Last {days} Days\n")
            for pr in updates['pull_requests']:
                file.write(f"- {pr['title']} #{pr['number']}\n")
        
        LOG.info(f"Exported time-range progress to {file_path}")
        return file_path


    
    # 写一个方法，入参是 repo ,校验这个repo 是否存在，返回 True/False
    def check_repo_exists(self, repo):
        """
        检验仓库是否存在
        参数：repo
        存在 返回 True
        不存在 返回 False
        
        """
        url = f"https://api.github.com/repos/{repo}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            LOG.error(f"Error checking repo existence: {response.status_code} - {response.text}")
            return False

    
    def get_repo_name(self, repo_address: str):
        """
        Extract repository name from repository URL or address.
        
        Examples:
            https://github.com/fastapi/fastapi -> fastapi/fastapi
            git@github.com:fastapi/fastapi.git -> fastapi/fastapi
            fastapi/fastapi -> fastapi/fastapi
        
        Args:
            repo_address: Repository URL or owner/repo string
            
        Returns:
            str: Formatted owner/repo string
        """
        # If it's already in owner/repo format and not a URL
        if not repo_address.startswith(('http://', 'https://', 'git@')):
            # Remove .git suffix if present
            if repo_address.endswith('.git'):
                repo_address = repo_address[:-4]
            # Validate basic format
            if '/' in repo_address:
                return repo_address
            else:
                raise ValueError(f"Invalid repo address format: {repo_address}")

        parsed_url = urlparse(repo_address)
        path = parsed_url.path
        
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
            
        # Remove .git suffix
        if path.endswith('.git'):
            path = path[:-4]
            
        parts = path.split('/')
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            return f"{owner}/{repo}"
        else:
            raise ValueError(f"Could not extract owner/repo from URL: {repo_address}")
