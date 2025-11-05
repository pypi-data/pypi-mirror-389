"""
Website scraper tool for extracting HTML content from web pages using requests and BeautifulSoup.
"""
from typing import Optional
from agno.tools import Toolkit
from loguru import logger
import requests
from bs4 import BeautifulSoup
import random
import time


class WebsiteScraper(Toolkit):
    """A tool for scraping website content using requests and BeautifulSoup."""

    # 常见的 User-Agent 列表
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]

    def __init__(self):
        """Initialize the WebsiteScraper."""
        super().__init__(name="website_scraper")
        self.register(self.scrape_website)

    def _get_headers(self, url: str, user_agent: Optional[str] = None) -> dict:
        """Generate request headers to mimic a real browser."""
        return {
            'User-Agent': user_agent or random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    def _extract_text(self, html: str) -> str:
        """Extract clean text from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, and other unwanted tags
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript', 'iframe', 'header', 'footer', 'nav']):
            tag.decompose()

        # Get text content
        text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)

        return clean_text

    def scrape_website(
        self,
        url: str,
        user_agent: Optional[str] = None,
        cookies: Optional[dict] = None,
        timeout: int = 30
    ) -> str:
        """
        Scrape clean text content from a website using requests and BeautifulSoup.

        Args:
            url: The URL of the website to scrape
            user_agent: Optional custom User-Agent string
            cookies: Optional cookies dict
            timeout: Request timeout in seconds (default: 30)

        Returns:
            The clean text content of the website (without HTML tags, scripts, styles)
        """
        try:
            logger.info(f'正在使用 requests 抓取网站: [{url}]')

            # Add random delay to avoid being detected as bot
            time.sleep(random.uniform(1, 3))

            # Prepare headers
            headers = self._get_headers(url, user_agent)

            # Create session for better connection handling
            session = requests.Session()

            # Make request
            response = session.get(
                url,
                headers=headers,
                cookies=cookies or {},
                timeout=timeout,
                allow_redirects=True,
                verify=True
            )

            # Check if request was successful
            response.raise_for_status()

            # Extract text content
            text_content = self._extract_text(response.text)

            # Limit content length to avoid token overflow
            max_chars = 50000  # ~12500 tokens approximately
            if len(text_content) > max_chars:
                logger.warning(
                    f"内容过长 ({len(text_content)} 字符)，截断到 {max_chars} 字符")
                text_content = text_content[:max_chars] + "\n\n[内容已截断...]"

            logger.info(
                f"成功抓取网站，HTTP 状态码: {response.status_code}, 文本长度: {len(text_content)} 字符")
            return text_content

        except requests.exceptions.Timeout:
            error_msg = f"请求超时: {url}"
            logger.error(error_msg)
            return f"错误: {error_msg}"
        except requests.exceptions.ConnectionError:
            error_msg = f"连接错误，无法访问: {url}"
            logger.error(error_msg)
            return f"错误: {error_msg}"
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP 错误 {e.response.status_code}: {url}"
            logger.error(error_msg)
            return f"错误: {error_msg}"
        except Exception as e:
            error_msg = f"抓取网站时发生错误: {str(e)}"
            logger.error(error_msg)
            return f"错误: {error_msg}"
