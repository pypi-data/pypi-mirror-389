"""
GitHub tool for fetching repository commits and activity data.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from agno.tools import Toolkit
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class GitHubTool(Toolkit):
    """A tool for fetching GitHub repository commits and activity data."""

    # 配置常量
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    GITHUB_API_BASE = "https://api.github.com"
    PER_PAGE = 100
    DEFAULT_MAX_PAGES = 10

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHubTool.

        Args:
            token: GitHub Personal Access Token for authentication
        """
        super().__init__(name="github_tool")
        self.token = token
        self.register(self.get_commits)
        self.register(self.get_commits_with_pagination)
        self.register(self.parse_github_url)

    def _validate_github_url(self, url: str) -> bool:
        """
        验证GitHub API URL的安全性

        Args:
            url: 待验证的URL

        Returns:
            bool: URL是否安全

        Raises:
            ValueError: URL不安全时抛出异常
        """
        try:
            parsed = urlparse(url)

            # 检查协议
            if parsed.scheme != 'https':
                raise ValueError("GitHub API仅支持HTTPS协议")

            # 检查域名
            if parsed.netloc != 'api.github.com':
                raise ValueError("仅支持GitHub官方API域名")

            return True

        except Exception as e:
            raise ValueError(f"URL验证失败: {e}")

    def _validate_datetime_format(self, date_str: str) -> bool:
        """
        验证日期时间格式是否符合ISO 8601标准

        Args:
            date_str: 日期时间字符串

        Returns:
            bool: 格式是否正确

        Raises:
            ValueError: 格式不正确时抛出异常
        """
        try:
            # 尝试解析ISO 8601格式
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except ValueError:
            raise ValueError(
                f"日期格式错误，应为ISO 8601格式，如: 2024-11-04T00:00:00Z")

    def _process_commits_data(self, commits: List[Dict]) -> Dict:
        """
        处理GitHub commits数据，按用户分组并排序

        Args:
            commits: GitHub API返回的commits数据列表

        Returns:
            Dict: 按用户名分组的commits数据
        """
        if not commits:
            logger.warning("commits数据为空")
            return {}

        user_commits = {}

        for commit in commits:
            try:
                # 提取所需字段
                commit_info = commit.get('commit', {})
                author_info = commit_info.get('author', {})

                author_name = author_info.get('name', 'Unknown')
                commit_message = commit_info.get('message', '')
                commit_date = author_info.get('date', '')

                # 初始化用户列表
                if author_name not in user_commits:
                    user_commits[author_name] = []

                # 添加commit记录
                user_commits[author_name].append({
                    'message': commit_message,
                    'date': commit_date
                })

            except Exception as e:
                logger.warning(f"处理commit数据时出错: {e}")
                continue

        # 按时间排序（从新到旧）
        for author_name in user_commits:
            user_commits[author_name].sort(
                key=lambda x: x['date'],
                reverse=True
            )

        logger.info(f"成功处理 {len(user_commits)} 个用户的commits数据")
        return user_commits

    def _get_headers(self) -> Dict:
        """构建请求头"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Neco-GitHub-Tools/1.0'
        }

        if self.token:
            headers['Authorization'] = f'token {self.token}'
            logger.info("使用GitHub token进行认证")
        else:
            logger.warning("未提供GitHub token，将使用未认证的请求（有速率限制）")

        return headers

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _fetch_github_commits(self, url: str) -> List[Dict]:
        """
        获取GitHub commits数据，支持重试机制

        Args:
            url: GitHub API URL

        Returns:
            List[Dict]: commits数据列表

        Raises:
            ValueError: 请求失败时抛出异常
        """
        logger.info(f"开始获取GitHub commits数据: {url}")

        try:
            headers = self._get_headers()
            response = requests.get(
                url,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT,
                verify=True
            )

            # 检查响应状态
            if response.status_code == 401:
                raise ValueError("GitHub API认证失败，请检查token是否有效")
            elif response.status_code == 403:
                raise ValueError("GitHub API访问被拒绝，可能超出了速率限制")
            elif response.status_code == 404:
                raise ValueError("GitHub仓库不存在或无访问权限")
            elif response.status_code >= 400:
                logger.error(
                    f"GitHub API返回错误状态: {response.status_code}, 响应: {response.text[:500]}")
                raise ValueError(
                    f"GitHub API请求失败，状态码: {response.status_code}")

            commits_data = response.json()

            logger.info(f"成功获取 {len(commits_data)} 条commits记录")
            return commits_data

        except requests.exceptions.Timeout:
            logger.error(f"GitHub API请求超时: {url}")
            raise ValueError(f"请求超时: {url}")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"GitHub API连接错误: {e}")
            raise ValueError(f"连接失败: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API请求异常: {e}")
            raise ValueError(f"请求失败: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"GitHub API响应JSON解析失败: {e}")
            raise ValueError(f"响应数据格式错误: {e}")

        except Exception as e:
            logger.error(f"获取GitHub commits时发生未知错误: {e}")
            raise ValueError(f"请求处理失败: {e}")

    def get_commits(
        self,
        owner: str,
        repo: str,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> str:
        """
        获取指定GitHub仓库的commits记录，并按用户分组处理。
        如果不指定since和until，将获取最近的commits记录（最多100条）。

        Args:
            owner: GitHub仓库所有者用户名或组织名
            repo: GitHub仓库名称
            since: 开始时间（可选），ISO 8601格式，如: 2024-11-04T00:00:00Z
            until: 结束时间（可选），ISO 8601格式，如: 2024-11-10T00:00:00Z

        Returns:
            str: 按用户分组的commits数据JSON字符串

        Raises:
            ValueError: 当参数无效或请求失败时抛出
        """
        # 参数验证
        if not owner or not isinstance(owner, str):
            raise ValueError("owner参数不能为空且必须是字符串")

        if not repo or not isinstance(repo, str):
            raise ValueError("repo参数不能为空且必须是字符串")

        # 验证日期格式（如果提供了日期参数）
        if since:
            self._validate_datetime_format(since)
        if until:
            self._validate_datetime_format(until)

        # 构建API URL
        api_url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
        params = [f"per_page={self.PER_PAGE}"]

        # 添加时间参数（如果提供）
        if since:
            params.append(f"since={since}")
        if until:
            params.append(f"until={until}")

        full_url = f"{api_url}?{'&'.join(params)}"

        # 验证URL安全性
        self._validate_github_url(full_url)

        # 记录请求信息
        time_range_str = ""
        if since and until:
            time_range_str = f" ({since} ~ {until})"
        elif since:
            time_range_str = f" (自{since}起)"
        elif until:
            time_range_str = f" (截止到{until})"
        else:
            time_range_str = " (最近100条)"

        logger.info(f"获取GitHub commits: {owner}/{repo}{time_range_str}")

        try:
            # 获取commits数据
            commits_data = self._fetch_github_commits(full_url)

            # 处理数据
            processed_data = self._process_commits_data(commits_data)

            # 转换为JSON字符串
            result_json = json.dumps(
                processed_data, ensure_ascii=False, indent=2)

            logger.info(
                f"成功获取并处理GitHub commits数据: "
                f"{len(processed_data)} 个用户, "
                f"{sum(len(commits) for commits in processed_data.values())} 条commits"
            )

            return result_json

        except Exception as e:
            logger.error(f"获取GitHub commits失败: {e}")
            raise

    def get_commits_with_pagination(
        self,
        owner: str,
        repo: str,
        since: Optional[str] = None,
        until: Optional[str] = None,
        max_pages: int = DEFAULT_MAX_PAGES
    ) -> str:
        """
        获取指定GitHub仓库的commits记录（支持分页），并按用户分组处理。

        当commits数量较多时，GitHub API会分页返回结果。此工具可以自动处理分页，获取完整的commits数据。
        如果不指定since和until，将获取仓库的所有commits记录。

        Args:
            owner: GitHub仓库所有者用户名或组织名
            repo: GitHub仓库名称
            since: 开始时间（可选），ISO 8601格式，如: 2024-11-04T00:00:00Z。不指定则从仓库创建开始
            until: 结束时间（可选），ISO 8601格式，如: 2024-11-10T00:00:00Z。不指定则到当前时间
            max_pages: 最大获取页数，默认10页，避免请求过多数据

        Returns:
            str: 按用户分组的commits数据JSON字符串

        Raises:
            ValueError: 当参数无效或请求失败时抛出
        """
        # 参数验证
        if not owner or not isinstance(owner, str):
            raise ValueError("owner参数不能为空且必须是字符串")

        if not repo or not isinstance(repo, str):
            raise ValueError("repo参数不能为空且必须是字符串")

        if not isinstance(max_pages, int) or max_pages < 1:
            raise ValueError("max_pages必须是正整数")

        # 验证日期格式（如果提供了日期参数）
        if since:
            self._validate_datetime_format(since)
        if until:
            self._validate_datetime_format(until)

        time_range_str = ""
        if since and until:
            time_range_str = f" ({since} ~ {until})"
        elif since:
            time_range_str = f" (自{since}起)"
        elif until:
            time_range_str = f" (截止到{until})"
        else:
            time_range_str = " (所有历史记录)"

        logger.info(
            f"开始分页获取GitHub commits: {owner}/{repo}"
            f"{time_range_str}, max_pages={max_pages}"
        )

        all_commits = []
        page = 1

        try:
            while page <= max_pages:
                # 构建API URL
                api_url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
                params = [f"per_page={self.PER_PAGE}", f"page={page}"]

                # 添加时间参数（如果提供）
                if since:
                    params.append(f"since={since}")
                if until:
                    params.append(f"until={until}")

                full_url = f"{api_url}?{'&'.join(params)}"

                # 验证URL安全性
                self._validate_github_url(full_url)

                logger.info(f"获取第 {page} 页数据")

                # 获取当前页数据
                page_commits = self._fetch_github_commits(full_url)

                # 如果当前页没有数据，说明已经获取完毕
                if not page_commits:
                    logger.info(f"第 {page} 页无数据，停止分页获取")
                    break

                all_commits.extend(page_commits)
                logger.info(f"第 {page} 页获取到 {len(page_commits)} 条记录")

                # 如果返回的记录数少于100，说明这是最后一页
                if len(page_commits) < self.PER_PAGE:
                    logger.info(f"第 {page} 页数据不足{self.PER_PAGE}条，为最后一页")
                    break

                page += 1

            logger.info(f"分页获取完成，总共获取 {len(all_commits)} 条commits记录")

            # 处理数据
            processed_data = self._process_commits_data(all_commits)

            # 转换为JSON字符串
            result_json = json.dumps(
                processed_data, ensure_ascii=False, indent=2)

            logger.info(
                f"成功获取并处理GitHub commits数据（分页）: "
                f"获取{page-1}页, {len(processed_data)}个用户, "
                f"{sum(len(commits) for commits in processed_data.values())}条commits"
            )

            return result_json

        except Exception as e:
            logger.error(f"分页获取GitHub commits失败: {e}")
            raise

    def parse_github_url(self, url: str) -> str:
        """
        解析GitHub仓库URL，提取owner和repo信息。

        支持的URL格式：
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git

        Args:
            url: GitHub仓库URL

        Returns:
            str: JSON字符串，包含owner和repo信息

        Raises:
            ValueError: URL格式不正确时抛出
        """
        if not url or not isinstance(url, str):
            raise ValueError("url参数不能为空且必须是字符串")

        url = url.strip()

        try:
            # 处理 git@ 格式
            if url.startswith('git@github.com:'):
                # git@github.com:owner/repo.git
                path = url.replace('git@github.com:', '').replace('.git', '')
                parts = path.split('/')
                if len(parts) == 2:
                    owner, repo = parts
                    result = {"owner": owner.strip(), "repo": repo.strip()}
                    logger.info(f"解析GitHub URL成功: {result}")
                    return json.dumps(result, ensure_ascii=False)

            # 处理 https:// 格式
            elif url.startswith('http://') or url.startswith('https://'):
                parsed = urlparse(url)

                # 验证是 github.com
                if 'github.com' not in parsed.netloc:
                    raise ValueError("仅支持GitHub仓库URL")

                # 提取路径部分: /owner/repo 或 /owner/repo.git
                path = parsed.path.strip('/').replace('.git', '')
                parts = path.split('/')

                if len(parts) >= 2:
                    owner = parts[0].strip()
                    repo = parts[1].strip()

                    if owner and repo:
                        result = {"owner": owner, "repo": repo}
                        logger.info(f"解析GitHub URL成功: {result}")
                        return json.dumps(result, ensure_ascii=False)

            raise ValueError(
                f"无法解析的GitHub URL格式: {url}。"
                "支持的格式: https://github.com/owner/repo 或 git@github.com:owner/repo.git"
            )

        except Exception as e:
            logger.error(f"解析GitHub URL失败: {e}")
            raise ValueError(f"解析GitHub URL失败: {e}")
