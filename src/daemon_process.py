import schedule  # 导入 schedule 实现定时任务执行器
import time  # 导入time库，用于控制时间间隔
import signal  # 导入signal库，用于信号处理
import sys  # 导入sys库，用于执行系统相关的操作

# 先加载环境变量，以确保在导入其他模块时可以使用这些环境变量
from dotenv import load_dotenv  # 导入dotenv库，用于加载环境变量

load_dotenv()  # 加载环境变量


from config import Config  # 导入配置管理类
from github_client import GitHubClient  # 导入GitHub客户端类，处理GitHub API请求
from hacknews_client import (
    HackerNewsClient,
)  # 导入HackerNews客户端类，处理HackerNews API请求
from notifier import Notifier  # 导入通知器类，用于发送通知
from report_generator import ReportGenerator  # 导入报告生成器类
from llm import LLM  # 导入语言模型类，可能用于生成报告内容
from subscription_manager import (
    SubscriptionManager,
)  # 导入订阅管理器类，管理GitHub仓库订阅
from logger import LOG  # 导入日志记录器


def graceful_shutdown(signum, frame):
    # 优雅关闭程序的函数，处理信号时调用
    LOG.info("[优雅退出]守护进程接收到终止信号")
    sys.exit(0)  # 安全退出程序


def github_job(subscription_manager, github_client, report_generator, notifier, days):
    LOG.info("[开始执行定时任务]")
    subscriptions = subscription_manager.list_subscriptions()  # 获取当前所有订阅
    LOG.info(f"订阅列表：{subscriptions}")
    for repo in subscriptions:
        # 遍历每个订阅的仓库，执行以下操作
        markdown_file_path = github_client.export_progress_by_date_range(repo, days)
        # 从Markdown文件自动生成进展简报
        report, report_file_path = report_generator.generate_report_by_date_range(markdown_file_path, days)
        notifier.notify(repo, report)
    LOG.info(f"[定时任务执行完毕]")


def hacknews_job(
    hacknews_client: HackerNewsClient,
    report_generator: ReportGenerator,
    notifier: Notifier,
):
    LOG.info("[开始执行定时任务]")
    file_path,markdown_content = hacknews_client.export_hot_news()
    report, report_file_path = report_generator.generate_hacknews_report(file_path)
    notifier.notify("HackerNews", report)
    LOG.info(f"[定时任务执行完毕]")


def main():
    # 设置信号处理器
    signal.signal(signal.SIGTERM, graceful_shutdown)

    config = Config(version="v3.0")  # 创建配置实例

    github_client = GitHubClient(config.github_token)  # 创建GitHub客户端实例
    hacknews_client = HackerNewsClient()  # 创建HackerNews客户端实例
    notifier = Notifier(config.email)  # 创建通知器实例
    llm = LLM(factory_name="ark", model_name="deepseek-v3-2-251201")  # 创建语言模型实例
    report_generator = ReportGenerator(llm)  # 创建报告生成器实例
    subscription_manager = SubscriptionManager(config.subscriptions_file)  # 创建订阅管理器实例

    # 启动时立即执行（如不需要可注释）
    # github_job(subscription_manager, github_client, report_generator, notifier, config.freq_days)

    # 启动时立即执行 hackernews 热点报告  （如不需要可注释）
    hacknews_job(hacknews_client, report_generator, notifier)

    # 安排每天的定时任务  github 进度报告 和 hackernews 热点报告
    schedule.every(config.freq_days).days.at(config.exec_time).do(
        github_job,
        subscription_manager,
        github_client,
        report_generator,
        notifier,
        config.freq_days,
    )

    schedule.every(config.hacknews_frequency_days).days.at(config.hacknews_execution_time).do(
        hacknews_job, hacknews_client, report_generator, notifier
    )

    try:
        # 在守护进程中持续运行
        while True:
            schedule.run_pending()
            time.sleep(1)  # 短暂休眠以减少 CPU 使用
    except Exception as e:
        LOG.error(f"主进程发生异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
