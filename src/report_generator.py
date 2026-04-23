# src/report_generator.py

import os
from datetime import date, timedelta
from logger import LOG  # 导入日志模块，用于记录日志信息
from llm import LLM
class ReportGenerator:
    def __init__(self, llm: LLM):
        self.llm = llm  # 初始化时接受一个LLM实例，用于后续生成报告

    def export_daily_progress(self, repo, updates):
        # 构建仓库的日志文件目录
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))
        os.makedirs(repo_dir, exist_ok=True)  # 如果目录不存在则创建
        
        # 创建并写入日常进展的Markdown文件
        file_path = os.path.join(repo_dir, f'{date.today()}.md')
        with open(file_path, 'w') as file:
            file.write(f"# Daily Progress for {repo} ({date.today()})\n\n")
            file.write("\n## Issues\n")
            for issue in updates['issues']:
                file.write(f"- {issue['title']} #{issue['number']}\n")
        return file_path

    def export_progress_by_date_range(self, repo, updates, days):
        # 构建目录并写入特定日期范围的进展Markdown文件
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))
        os.makedirs(repo_dir, exist_ok=True)

        today = date.today()
        since = today - timedelta(days=days)  # 计算起始日期
        
        date_str = f"{since}_to_{today}"  # 格式化日期范围字符串
        file_path = os.path.join(repo_dir, f'{date_str}.md')
        
        with open(file_path, 'w') as file:
            file.write(f"# Progress for {repo} ({since} to {today})\n\n")
            file.write("\n## Issues Closed in the Last {days} Days\n")
            for issue in updates['issues']:
                file.write(f"- {issue['title']} #{issue['number']}\n")
        
        LOG.info(f"Exported time-range progress to {file_path}")  # 记录导出日志
        return file_path

    def generate_daily_report(self, markdown_file_path) -> tuple[str, str]:
        """生成指定当天范围内的报告

        Args:
            markdown_file_path (_type_): _description_

        Returns:
            tuple[str, str]: 原始report Markdown 格式字符串, 报告改名后的文件路径
        """
        # 读取Markdown文件并使用LLM生成日报
        with open(markdown_file_path, 'r') as file:
            markdown_content = file.read()

        report = self.llm.generate_daily_report(markdown_content)  # 调用LLM生成报告

        report_file_path = os.path.splitext(markdown_file_path)[0] + "_report.md"
        with open(report_file_path, 'w+') as report_file:
            report_file.write(report)  # 写入生成的报告

        LOG.info(f"Generated report saved to {report_file_path!r}")  # 记录生成报告日志
        
        return report, report_file_path


    def generate_report_by_date_range(self, markdown_file_path, days) -> tuple[str, str]:
        """_summary_
            生成指定日期范围内的报告

        Args:
            markdown_file_path (str): 文件路径
            days (int ): 天数 

        Returns:
            tuple[str, str]: 原始report markdown 内容字符串 ,报告改名后的文件路径
            
        """
        
        return self.generate_daily_report(markdown_file_path)
        

