import os
import textwrap

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("API_YI_KEY")
base_url = os.getenv("API_YI_BASE_URL")

deep_seek_api_key = os.getenv("DEEPSEEK_API_KEY")
deep_seek_base_url = os.getenv("DEEPSEEK_API_BASE_URL")

api_yi_key = os.getenv("API_YI_KEY")
api_yi_base_url = os.getenv("API_YI_BASE_URL")



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
        if hasattr(self, '_initialized'):
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
        }

    def get_model(self, factory_name="apiyi"):
        """
        Returns a cached OpenAI client instance for the given model name.
        If not cached, creates a new one, caches it, and returns it.
        """
        if factory_name in self._clients_cache:
            print(f"Using cached model: {factory_name}")
            return self._clients_cache[factory_name]

        print(f"Creating new client for model: {factory_name}")

        # Get config, fallback to apiyi config if model_name unknown but try to be safe
        config = self.configs.get(factory_name)

        if not config:
            # Fallback logic similar to original code
            print(f"Warning: Model '{factory_name}' not found in configs. Falling back to 'apiyi'.")
            config = self.configs["apiyi"]

        try:
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
            )
            self._clients_cache[factory_name] = client
            return client
        except Exception as e:
            print(f"Error creating client for {factory_name}: {e}")
            raise


class LLM:
    def __init__(self, facotry_name="apiyi", model_name: str = 'gpt-3.5-turbo'):
        self.model_factory = ModelFactory()
        self.client = self.model_factory.get_model(facotry_name)
        self.model_name = model_name

        self.system_prompt = """
        你是一名资深技术文档工程师和项目信息汇总专家。
        你的任务是将开发项目的每日进展（Issues、Pull Requests 等）合并同类项，提炼成一份结构清晰、重点突出的简报。
        输出必须包含三个部分：1）新增功能；2）主要改进；3）修复问题。每个要点用一句话概括，按重要性或逻辑顺序排列。避免冗余，不添加原文没有的信息。
        """

        # Use textwrap.dedent to remove common leading whitespace for cleaner prompt
        self.user_prompt_template = textwrap.dedent("""\
            以下是项目的最新进展，根据功能合并同类项，形成一份简报。
            每日进展原始数据（包含 Issues 和 Pull Requests）。请根据你作为信息汇总专家的能力，完成以下任务：
            1. 合并同类项（例如多个相关的 bug 修复、同一模块的改进）。
            2. 输出一份简报，严格包含三个部分：
            - 新增功能
            - 主要改进
            - 修复问题
            3. 对于“修复问题”，请简要描述现象（如“修复 xxx 场景下的超时错误”），而不是只写“修复 bug”。
            4. 如果某类变更数量过多，合并为 1-10 条最具代表性的条目。
            请确保输出内容结构清晰、重点突出，避免冗余信息，不添加原文没有的信息。
            
            每日原始数据:

            {markdown_content}
        """)

    def generate_daily_report(self, markdown_content, dry_run=False):
        # prompt = f"以下是项目的最新进展，根据功能合并同类项，形成一份简报，至少包含：1）新增功能；2）主要改进；3）修复问题；:\n\n{markdown_content}"
        prompt = self.user_prompt_template.format(markdown_content=markdown_content)
        if dry_run:
            with open("daily_progress/prompt.txt", "w+") as f:
                f.write(prompt)
            return "DRY RUN"

        print("Before call GPT")
        # Note: Ensure the model name passed here matches what you want to use. 
        # Currently hardcoded to gpt-3.5-turbo in the API call, but the client might be for Yi/DeepSeek.
        # You might want to make the model name dynamic too.
        messages= [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        response = self.client.chat.completions.create(
            model=self.model_name, messages=messages
        )
        print("After call GPT")
        print(response)
        return response.choices[0].message.content
