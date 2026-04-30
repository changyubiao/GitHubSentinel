import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

from logger import LOG


class HackerNewsClient:
    """HackerNews 中文版爬虫客户端

    args:
        url: HackerNews 中文版 URL, 默认 https://hn.aimaker.dev
    """

    def __init__(self, url="https://hn.aimaker.dev"):
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_html(self) -> str:
        resp = requests.get(self.url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return resp.text

    def parse_html(self, html) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        result = {"24小时热榜": [], "一周热榜": [], "最新": []}

        cards = soup.find_all("div", class_="backdrop-blur-md")
        for card in cards:
            h2 = card.find("h2")
            if not h2:
                continue
            section = h2.get_text(strip=True)
            if section not in result:
                continue

            for article in card.find_all("article"):
                a_tag = article.find("a", href=True)
                if not a_tag:
                    continue

                item = {
                    "title": a_tag.get_text(strip=True),
                    "link": a_tag["href"] if a_tag["href"].startswith("http") else f"https://hn.aimaker.dev{a_tag['href']}",
                }

                def get_text_after_dot(color_class):
                    dot = article.find("span", class_=f"inline-block w-1 h-1 rounded-full {color_class}")
                    if dot:
                        parent = dot.find_parent("span")
                        if parent:
                            return parent.get_text(strip=True)
                    return None

                # 分数 – 直接使用提取到的文本，不再拼接“分”
                score = get_text_after_dot("bg-blue-500")
                item["score"] = score if score else "未知"

                # 作者
                author = get_text_after_dot("bg-green-500")
                item["author"] = author if author else "未知"

                # 时间
                time = get_text_after_dot("bg-purple-500")
                item["time"] = time if time else "未知"

                # 原帖链接
                original = article.find("a", href=lambda h: h and "news.ycombinator.com" in h)
                item["original_post"] = original["href"] if original else item["link"]

                result[section].append(item)
        return result

    def _get_hot_news(self) -> dict:
        html = self.fetch_html()
        return self.parse_html(html)

    def export_hot_news(self) -> tuple[str,str]:
        """
        导出HackerNews热点数据到markdown文件
        """
        hot_data = self._get_hot_news()
        file_path,markdown_content = self._json_to_markdown(hot_data)
        LOG.info(f"Exported HackerNews hot news to {file_path}")
        return file_path,markdown_content

    def _json_to_markdown(self, hot_data: dict) -> str:
        """
        将HackerNews热点数据转换为结构化Markdown文本格式
        """

        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        hacknews_hot_dir = os.path.join("daily_progress", "hacknews")
        os.makedirs(hacknews_hot_dir, exist_ok=True)
        file_path = os.path.join(hacknews_hot_dir, f"hacknews_{now}.md")

        markdown_content = "# HackerNews 技术热点分析报告\n\n"
        markdown_content += "> 本报告基于对 HackerNews 24小时热榜、一周热榜及最新话题的实时数据分析。\n\n"

        for section, items in hot_data.items():
            markdown_content += f"## {section}\n"
            markdown_content += f"本板块共采集 {len(items)} 个热点话题。\n\n"

            for idx, item in enumerate(items, 1):
                markdown_content += f"### {idx}. {item['title']}\n"
                markdown_content += f"- **热度**: {item['score']}\n"
                markdown_content += f"- **作者**: {item['author']}\n"
                markdown_content += f"- **时间**: {item['time']}\n"
                markdown_content += f"- **讨论**: {item['original_post']}\n"
                if item.get("link"):
                    markdown_content += f"- **原文链接**: {item['link']}\n"
                markdown_content += "\n"

        # 删除末尾多余的空行
        markdown_content = markdown_content.strip()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return file_path,markdown_content


if __name__ == "__main__":
    client = HackerNewsClient()
    # data = client._get_hot_news()
    file_path ,markdown_content = client.export_hot_news()
    print(f"✅ HackerNews热点数据已保存至 {file_path}")
    # for section, items in data.items():
    #     print(f"\n{'='*20} {section} {'='*20}")
    #     for i, item in enumerate(items, 1):
    #         print(f"{i}. {item['title']}")
    #         print(f"   分数: {item['score']}  作者: {item['author']}  时间: {item['time']}")
    #         print(f"   链接: {item['link']}")
    #         print(f"   原帖: {item['original_post']}")
    #         print("-" * 60)

    # with open('hn_hot-v3.json', 'w', encoding='utf-8') as f:
    #     json.dump(data, f, ensure_ascii=False, indent=2)
    # print("\n✅ 数据已保存至 hn_hot-v3.json")
