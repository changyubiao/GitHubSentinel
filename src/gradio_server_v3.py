from datetime import datetime, timezone, timedelta

import os
import tempfile
import shutil
import pandas as pd  # 导入pandas库用于数据处理

import gradio as gr  # 导入gradio库用于创建GUI

from dotenv import load_dotenv  # 导入dotenv库用于加载环境变量

# 优先 加载环境变量，以确保在导入其他模块时可以使用这些环境变量
load_dotenv()  # 加载环境变量

from config import Config  # 导入配置管理模块
from github_client_v2 import GitHubClient  # 导入GitHub客户端的另一个版本
from report_generator import ReportGenerator  # 导入报告生成器模块
from llm import LLM  # 导入可能用于处理语言模型的LLM类
from hacknews_client import HackerNewsClient  # 导入HackerNews客户端
from subscription_manager import SubscriptionManager  # 导入订阅管理器
from logger import LOG  # 导入日志记录器

shanghai_tz = timezone(timedelta(hours=8))


""" 
使用block 来布局页面 更加灵活一点

1. 添加tab 页面  方便管理订阅列表
2. 同时修改 列表的结构 变成字典结构 
3. 添加 hacknews tab 页面, 抓取 HackerNews 中文版热点并写入


"""


def _repo_dropdown_update(value: str | None = None):
    """与 subscription_manager 同步下拉选项；若 value 仍在列表中则保留，否则选第一项。
    返回 (gr.update(...), 新选中值)，便于同时写入 gr.State（跨 Tab 时不能把 Dropdown 当作另一 Tab 事件的输入）。"""
    choices = subscription_manager.list_subscription_repos()
    if value is not None and value in choices:
        new_value = value
    else:
        new_value = choices[0] if choices else None
    return gr.update(choices=choices, value=new_value), new_value


# 1. 添加逻辑
def add_repo(repo_url, current_df, tracked_repo: str | None):
    no_change_dd = gr.update()
    if not repo_url:
        gr.Info("请输入 github 仓库地址", duration=3)
        LOG.warning(f"请输入 github 仓库地址: {repo_url!r}")
        return "", current_df, no_change_dd, tracked_repo

    try:
        # 提取仓库名称
        repo_name = github_client.get_repo_name(repo_url)
        # 重复性检查
        if not subscription_manager.add_subscription(repo_name):
            gr.Warning(f"仓库「{repo_name}」已在订阅列表中，无需重复添加。", duration=8)
            return "", current_df, no_change_dd, tracked_repo

        # repo 存在性检测
        if not github_client.check_repo_exists(repo=repo_url):
            LOG.error(f"仓库不存在: {repo_url}")
            gr.Warning(f"仓库不存在: {repo_url}", duration=8)
            return "", current_df, no_change_dd, tracked_repo

        new_data = {
            "repo_name": repo_name,
            "subscribe_time": datetime.now(tz=shanghai_tz).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "正常",
        }

    except gr.Error as e:
        LOG.error(f"Failed to save subscription to file: {e}, repo_url: {repo_url}")
        raise e  # 将错误抛出到前端显示
    except Exception as e:
        LOG.error(f"Unexpected error: {e}, repo_url: {repo_url}")
        gr.Warning(f"Unexpected error: {e}, repo_url: {repo_url}", duration=8)
        return "", current_df, no_change_dd, tracked_repo

    # 拼接 DataFrame
    if current_df is None:
        new_df = pd.DataFrame(new_data)
    else:
        new_df = pd.concat([current_df, pd.DataFrame([new_data])], ignore_index=True)

    dd_upd, new_val = _repo_dropdown_update(value=repo_name)

    LOG.debug(f"Subscription added to file: {new_data} ")
    return "", new_df, dd_upd, new_val


# 2. 删除逻辑
def delete_selected_rows(selected_index, current_df, tracked_repo: str | None):
    """
    selected_index: 从 state 中获取的单个行索引 (int or None)
    tracked_repo: 与「项目进展」下拉当前选中同步的镜像（gr.State），避免跨 Tab 取 Dropdown 时 Gradio 只传 2 个参数
    """
    no_change_dd = gr.update()
    if selected_index is None or current_df is None:
        return None, current_df, no_change_dd, tracked_repo

    # Check if index is valid
    if not (0 <= selected_index < len(current_df)):
        return None, current_df, no_change_dd, tracked_repo

    # Drop row by index
    new_df = current_df.drop(index=[selected_index]).reset_index(drop=True)
    # 从 SubscriptionManager 中删除对应的订阅项
    subscription_manager.delete_subscription(selected_index)

    dd_upd, new_val = _repo_dropdown_update(value=tracked_repo)
    return None, new_df, dd_upd, new_val


# 创建各个组件的实例
config = Config(version="v3.0")  # 加载配置，指定版本为 v3.0
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
    subscriptions = subscription_manager.list_subscription_repos()
    default_value = subscriptions[0] if subscriptions else None
    # 默认值 设置第一个repo 为默认值；最后一项同步 dropdown_repo_state
    return default_value, 3, "# XXXXX 项目进展\n\n请选择项目并生成报告", None, default_value


def init_dataframe():
    # 这里可以从 subscription_manager 加载实际数据
    # 例如：subscription_manager.list_subscriptions() 返回一个列表，
    # 每个元素是一个字典，包含 repo_name, subscribe_time, status 等字段
    subscriptions = subscription_manager.list_subscriptions()

    if not subscriptions:
        return pd.DataFrame(columns=["repo_name", "subscribe_time", "status"])

    df = pd.DataFrame(subscriptions)
    return df


def _default_repo_dropdown_value() -> str | None:
    ch = subscription_manager.list_subscription_repos()
    preferred = "langchain-ai/langchain"
    if preferred in ch:
        return preferred
    return ch[0] if ch else None


# hacknews 拉取原始数据
def generate_hacknews_origin() -> tuple[str, str, str]:
    """拉取 HackerNews 原始数据

    Returns:
        str: 返回markdown 格式字符串
    """
    hacknews_client = HackerNewsClient()
    file_path, markdown_content = hacknews_client.export_hot_news()
    return markdown_content, file_path, file_path


def generate_hackernews_report(file_path: str) -> tuple[str, str]:
    """生成 HackerNews 热点报告

    Args:
        file_path (str): 文件路径

    Returns:
        tuple[str,str]: 返回markdown 格式字符串 和 文件路径
    """
    report_generator = ReportGenerator(llm)
    report, report_file_path = report_generator.generate_hacknews_report(file_path)
    return report, report_file_path, report_file_path


def clear_hacknews_form():
    """清空表单。File 组件须用 None 清空，
       空字符串会被当成路径并解析为 cwd，会
       触发 IsADirectoryError。这里需要特别注意

    Returns:
        tuple[str,str,None,str,str,None]: 返回清空后的表单
    """
    return "", "", None, "", "", None


# UI 组件创建
with gr.Blocks(title="GitHubSentinel") as demo:
    _default_repo = _default_repo_dropdown_value()
    # 放在任意 Tab 外，保证「订阅管理」里触发事件时也会带上当前值（嵌套在别 Tab 里可能仍不传参）
    dropdown_repo_state = gr.State(_default_repo)

    # 第一个标签页 项目进展
    with gr.Tab("项目进展"):
        gr.Markdown("# GitHubSentinel", elem_id="main-title")

        with gr.Row(equal_height=True):
            # 左侧表单区域
            with gr.Column(scale=1, elem_id="left-column"):
                # 订阅列表模块 - 使用 Dropdown 的 label 和 info 参数
                repo_dropdown = gr.Dropdown(
                    choices=subscription_manager.list_subscription_repos(),
                    label="订阅列表",
                    info="已订阅GitHub项目",
                    value=_default_repo,
                )
                repo_dropdown.change(lambda v: v, inputs=repo_dropdown, outputs=dropdown_repo_state)

                # 报告周期模块 - 使用 Slider 的 label 和 info 参数
                period_slider = gr.Slider(
                    minimum=1, maximum=30, value=3, step=1, label="报告周期", info="生成项目过去一段时间进展，单位：天"
                )

                with gr.Row():
                    btn_clear = gr.Button("清空表单", variant="secondary")
                    btn_submit = gr.Button("生成报告", variant="primary")

            # 右侧内容展示区域
            with gr.Column(scale=2, elem_id="right-column"):
                report_markdown = gr.Markdown(
                    value="# XXXXX 项目进展\n\n请选择项目并生成报告", elem_id="report-content"
                )
                report_file = gr.File(label="下载报告", file_types=[".md"], height=40)

        # 绑定事件
        btn_submit.click(
            fn=generate_report, inputs=[repo_dropdown, period_slider], outputs=[report_markdown, report_file]
        )

        btn_clear.click(
            fn=clear_form,
            inputs=None,
            outputs=[repo_dropdown, period_slider, report_markdown, report_file, dropdown_repo_state],
        )

    # 第二个标签页 订阅管理
    with gr.Tab("订阅管理"):

        with gr.Column(variant="panel", elem_id="main-card"):
            gr.Markdown("## 订阅管理")

            # --- 顶部输入区 ---
            with gr.Row():
                repo_input = gr.Textbox(label="github repo 地址", placeholder="请输入仓库地址", scale=85)
                add_btn = gr.Button("添加", variant="primary", scale=15)

            # --- 表格区 ---
            data_table = gr.Dataframe(
                value=init_dataframe(),  # 使用 init_dataframe() 来生成初始数据
                # headers=["仓库名称", "订阅时间", "状态"],
                datatype=["str", "str", "str"],
                interactive=False,
                label="已订阅列表 (点击行选中)",
                type="pandas",
                max_height=800,
            )

            # 这是一个隐藏的状态组件，用来存储当前选中的行索引 (单个整数)
            selected_row_state = gr.State(None)

            # --- 底部操作区 ---
            with gr.Row():
                # 这里的 variant="stop" 会显示为红色（取决于 Gradio 版本和主题）
                del_btn = gr.Button("删除选中项", variant="stop")

            # ================= 事件绑定 =================
            # 1. 添加事件（同步更新「项目进展」里的订阅下拉框 + 选中镜像 State）
            add_btn.click(
                fn=add_repo,
                inputs=[repo_input, data_table, dropdown_repo_state],
                outputs=[repo_input, data_table, repo_dropdown, dropdown_repo_state],
            )

            # 2. 选中行事件 (单选逻辑)
            # 当用户点击表格某一行时触发
            def on_select(evt: gr.SelectData, pre_selected) -> int | None:
                # evt.index is a tuple (row, col) for Dataframe
                if evt is None or evt.index is None:
                    return None

                row_index = evt.index[0]
                LOG.info(f"Row index selected: {row_index}, pre Row index selected: {pre_selected}")

                # If clicking the already selected row, optionally deselect it (set to None)
                # Or just keep it selected. Here we implement: click new row -> select new row.
                # If you want toggle behavior:
                if pre_selected == row_index:
                    return None
                else:
                    return row_index

            data_table.select(fn=on_select, inputs=[selected_row_state], outputs=selected_row_state)

            # 3. 删除事件（必须用本 Tab 内的 State 表示当前选中仓库；跨 Tab 的 Dropdown 作 inputs 时请求里会缺参）
            del_btn.click(
                fn=delete_selected_rows,
                inputs=[selected_row_state, data_table, dropdown_repo_state],
                outputs=[selected_row_state, data_table, repo_dropdown, dropdown_repo_state],
            )

    # 第三个标签页 HackerNews
    with gr.Tab("HackerNews热点"):
        gr.Markdown("## HackerNews热点", elem_id="hackernews-tab-title")
        gr.Markdown("本报告基于对 HackerNews 数据来源：https://hn.aimaker.dev/ 进行分析总结,生成热点总结报告", elem_id="hackernews-tab-description")

        with gr.Row(equal_height=False):

            with gr.Column(scale=1, elem_id="left-column"):

                with gr.Row():
                    hacknews_pull_btn = gr.Button("拉取原始数据", variant="secondary", scale=1)
                    hackernews_btn = gr.Button("生成HackNews热点总结", variant="primary", scale=2)
                    hackernews_btn_clear = gr.Button("清空", variant="stop", scale=1)

                # 我希望展示 完整的路径 名称
                hacknews_origin_file_path = gr.Textbox(label="原始文件路径", value="", interactive=False)
                hacknews_origin_file = gr.File(label="下载原始数据", file_types=[".md"], height=40)

                with gr.Row():
                    hacknews_origin_reusult = gr.Markdown(
                        value="", label="原始数据", elem_id="hackernews-origin-result"
                    )

            with gr.Column(scale=1, elem_id="right-column"):
                # 结果展示
                text_result = gr.Textbox(label="结果文件路径", value="", interactive=False)
                hackernews_file = gr.File(label="下载分析报告", file_types=[".md"], height=40)
                hackernews_result = gr.Markdown(value="", elem_id="hackernews-result")

        # 绑定事件
        hacknews_pull_btn.click(
            fn=generate_hacknews_origin,
            inputs=None,
            outputs=[hacknews_origin_reusult, hacknews_origin_file_path, hacknews_origin_file],
        )

        # 生成结果的事件
        hackernews_btn.click(
            fn=generate_hackernews_report,
            inputs=[hacknews_origin_file_path],
            outputs=[hackernews_result, hackernews_file, text_result],
        )

        # 清空事件
        hackernews_btn_clear.click(
            fn=clear_hacknews_form,
            inputs=None,
            outputs=[
                hacknews_origin_reusult,
                hacknews_origin_file_path,
                hacknews_origin_file,
                text_result,
                hackernews_result,
                hackernews_file,
            ],
        )


if __name__ == "__main__":
    demo.queue().launch(debug=True, share=False, css_paths=["src/css/gr_server_v3.css"])
