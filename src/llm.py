import os
import json
from openai import OpenAI  # 导入OpenAI库用于访问GPT模型
from logger import LOG  # 导入日志模块
import textwrap
from datetime import datetime
import httpx

api_key = os.getenv("API_YI_KEY")
base_url = os.getenv("API_YI_BASE_URL")

deep_seek_api_key = os.getenv("DEEPSEEK_API_KEY")
deep_seek_base_url = os.getenv("DEEPSEEK_API_BASE_URL")

api_yi_key = os.getenv("API_YI_KEY")
api_yi_base_url = os.getenv("API_YI_BASE_URL")


ark_api_key = os.getenv("ARK_API_KEY")
ark_base_url = os.getenv("ARK_API_BASE_URL")

# httpx / httpcore require numeric timeouts; os.getenv always returns str when set.
_LLM_TIMEOUT_SEC = float(os.getenv("LLM_TIMEOUT")) if os.getenv("LLM_TIMEOUT") else 900.0

LLM_TIMEOUT = httpx.Timeout(timeout=_LLM_TIMEOUT_SEC, connect=10.0)


class ModelFactory:
    _instance = None
    _clients_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelFactory, cls).__new__(cls)
            # Initialize cache in __new__ or __init__
            cls._clients_cache = {}
        return cls._instance

    def __init__(self):
        # Prevent re-initialization if already initialized
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        # Store configuration for lazy initialization or immediate init
        self.configs = {
            "gpt": {
                "api_key": api_key,
                "base_url": base_url,
            },
            "deepseek": {
                "api_key": deep_seek_api_key,
                "base_url": deep_seek_base_url,
            },
            "apiyi": {
                "api_key": api_yi_key,
                "base_url": api_yi_base_url,
            },
            "ark": {
                "api_key": ark_api_key,
                "base_url": ark_base_url,
            },
        }

    def get_model(self, factory_name="apiyi"):
        """
        Returns a cached OpenAI client instance for the given model name.
        If not cached, creates a new one, caches it, and returns it.
        """
        if factory_name in self._clients_cache:
            LOG.info(f"Using cached model: {factory_name}")
            return self._clients_cache[factory_name]

        LOG.info(f"Creating new client for model: {factory_name}")

        # Get config, fallback to apiyi config if model_name unknown but try to be safe
        config = self.configs.get(factory_name)

        if not config:
            # Fallback logic similar to original code
            LOG.warning(f"Warning: Model '{factory_name}' not found in configs. Falling back to 'apiyi'.")
            config = self.configs["apiyi"]

        try:
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
                timeout=LLM_TIMEOUT,
            )
            self._clients_cache[factory_name] = client
            return client
        except Exception as e:
            LOG.error(f"Error creating client for {factory_name}: {e}")
            raise


class LLM:
    def __init__(self, factory_name="apiyi", model_name: str = "gpt-4o"):
        # 创建一个OpenAI客户端实例
        # self.client = OpenAI()

        self.model_factory = ModelFactory()
        self.client = self.model_factory.get_model(factory_name)
        self.model_name = model_name
        self.factory_name = factory_name
        # 配置日志文件，当文件大小达到1MB时自动轮转，日志级别为DEBUG
        LOG.add("daily_progress/llm_logs.log", rotation="1 MB", level="DEBUG")
        # 从TXT文件加载提示信息
        with open("prompts/report_prompt.txt", "r", encoding="utf-8") as file:
            self.system_prompt = file.read()

        with open("prompts/hacknews_prompt_v2.txt", "r", encoding="utf-8") as file:
            self.hacknews_system_prompt = file.read()

    def generate_daily_report(self, markdown_content, dry_run=False):
        # 使用从TXT文件加载的提示信息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": markdown_content},
        ]

        if dry_run:
            # 如果启用了dry_run模式，将不会调用模型，而是将提示信息保存到文件中
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/prompt.txt", "w+") as f:
                # 格式化JSON字符串的保存
                json.dump(messages, f, indent=4, ensure_ascii=False)
            LOG.debug("Prompt已保存到 daily_progress/prompt.txt")

            return "DRY RUN"

        # 日志记录开始生成报告
        LOG.info(f"Starting report generation using {self.model_name!r} model, {self.factory_name!r} factory.")

        try:
            # 调用OpenAI GPT模型生成报告
            response = self.client.chat.completions.create(model=self.model_name, messages=messages)  # 指定使用的模型版本
            LOG.debug("GPT response: {}", response)
            # 返回模型生成的内容
            return response.choices[0].message.content
        except Exception as e:
            # 如果在请求过程中出现异常，记录错误并抛出
            LOG.error(f"生成报告时发生错误：{e}")
            raise

    def generate_hacknews_report(self, hacknews_content_markdown: str, dry_run=False) -> str:
        """
        生成 Hacker News 技术洞察报告

        Args:
            hacknews_content: Hacker News 内容, markdown 格式

        Returns:
            Hacker News 技术洞察报告


        """

        # import textwrap
        # 用户提示词
        user_prompt = textwrap.dedent(f"""
        请基于以下HackerNews热点数据，生成一份《技术热点洞察报告》。

        **数据来源**：HackerNews中文站 (hn.aimaker.dev)
        **时间范围**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}（最新数据包含过去24小时、过去一周及最新提交的话题）

        ### 数据
        {hacknews_content_markdown}
        """).format(hacknews_content_markdown=hacknews_content_markdown)

        messages = [
            {"role": "system", "content": self.hacknews_system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if dry_run:
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/hacknews_prompt.txt", "w+") as f:
                json.dump(messages, f, indent=4, ensure_ascii=False)
            LOG.debug("Prompt已保存到 daily_progress/hacknews_prompt_test.txt")
            return "DRY RUN"

        LOG.info(f"Starting hacknews report generation using {self.model_name!r} model, {self.factory_name!r} factory.")

        try:
            response = self.client.chat.completions.create(model=self.model_name, messages=messages)
        except Exception as e:
            LOG.error(f"生成 Hacker News 技术洞察报告时发生错误：{e}")
            raise
        return response.choices[0].message.content
