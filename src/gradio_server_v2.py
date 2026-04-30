import os
import tempfile
import shutil

import gradio as gr  # 导入gradio库用于创建GUI

from dotenv import load_dotenv  # 导入dotenv库用于加载环境变量

# 优先 加载环境变量，以确保在导入其他模块时可以使用这些环境变量
load_dotenv()  # 加载环境变量

from config import Config  # 导入配置管理模块
from github_client_v2 import GitHubClient  # 导入GitHub客户端的另一个版本
from report_generator import ReportGenerator  # 导入报告生成器模块
from llm import LLM  # 导入可能用于处理语言模型的LLM类
from subscription_manager import SubscriptionManager  # 导入订阅管理器
from logger import LOG  # 导入日志记录器

""" 
使用block 来布局页面 更加灵活一点

"""


# 创建各个组件的实例
config = Config()
github_client = GitHubClient(config.github_token)


# llm = LLM(model_name="deepseek-v3-2-251201", factory_name="ark")
# llm = LLM(model_name="doubao-seed-2-0-lite-260215", factory_name="ark")
llm = LLM(factory_name="ark", model_name="doubao-seed-2-0-mini-260215")

report_generator = ReportGenerator(llm)
subscription_manager = SubscriptionManager(config.subscriptions_file)


def generate_report(repo: str, days: int = 3):
    filepath = github_client.export_progress_by_date_range(repo, days=days)

    report, report_file_path = report_generator.generate_report_by_date_range(filepath, days)

    daily_dir, repo_name, filename = report_file_path.split("/")

    full_filename = "_".join([repo_name, filename])

    new_full_filename = os.path.join(tempfile.gettempdir(), full_filename)
    # 复制到 temp 目录下，并使用新的文件名
    shutil.copy(report_file_path, new_full_filename)

    LOG.info(f"Generated report: {report_file_path}, copy to: {new_full_filename!r}")

    return report, new_full_filename


def clear_form():
    """清空表单"""
    subscriptions = subscription_manager.list_subscriptions()
    default_value = subscriptions[0] if subscriptions else None
    # 默认值 设置第一个repo 为默认值
    return default_value, 3, "# XXXXX 项目进展\n\n请选择项目并生成报告", None


subscription_manager.list_subscriptions()

# UI 组件创建
with gr.Blocks(title="GitHubSentinel") as demo:
    gr.Markdown("# GitHubSentinel", elem_id="main-title")

    with gr.Row(equal_height=True):
        # 左侧表单区域
        with gr.Column(scale=1, elem_id="left-column"):
            # 订阅列表模块 - 使用 Dropdown 的 label 和 info 参数
            repo_dropdown = gr.Dropdown(
                choices=subscription_manager.list_subscriptions(),
                label="订阅列表",
                info="已订阅GitHub项目",
                value="langchain-ai/langchain",  # 默认选中项
            )

            # 报告周期模块 - 使用 Slider 的 label 和 info 参数
            period_slider = gr.Slider(minimum=1, maximum=30, value=3, step=1, label="报告周期", info="生成项目过去一段时间进展，单位：天")

            with gr.Row():
                btn_clear = gr.Button("清空表单", variant="secondary")
                btn_submit = gr.Button("生成报告", variant="primary")

        # 右侧内容展示区域
        with gr.Column(scale=2, elem_id="right-column"):
            report_markdown = gr.Markdown(value="# XXXXX 项目进展\n\n请选择项目并生成报告", elem_id="report-content")
            report_file = gr.File(label="下载报告", file_types=[".md"], height=40)

    # 绑定事件
    btn_submit.click(fn=generate_report, inputs=[repo_dropdown, period_slider], outputs=[report_markdown, report_file])

    btn_clear.click(fn=clear_form, inputs=None, outputs=[repo_dropdown, period_slider, report_markdown, report_file])


if __name__ == "__main__":
    demo.launch(debug=True, share=False, css_paths=["src/css/gr_server_v2.css"])
