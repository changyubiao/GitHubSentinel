import os
from openai import OpenAI  # 导入OpenAI库用于访问GPT模型
from logger import LOG  # 导入日志模块
from dotenv import load_dotenv

load_dotenv()



api_key = os.getenv("API_YI_KEY")
base_url = os.getenv("API_YI_BASE_URL")

deep_seek_api_key = os.getenv("DEEPSEEK_API_KEY")
deep_seek_base_url = os.getenv("DEEPSEEK_API_BASE_URL")

api_yi_key = os.getenv("API_YI_KEY")
api_yi_base_url = os.getenv("API_YI_BASE_URL")


ark_api_key = os.getenv("ARK_API_KEY")
ark_base_url = os.getenv("ARK_API_BASE_URL")



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
            "ark":{
                "api_key": ark_api_key,
                "base_url": ark_base_url,
            }
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
    def __init__(self,factory_name="apiyi", model_name: str = 'gpt-3.5-turbo'):
        
        self.model_factory = ModelFactory()
        self.client = self.model_factory.get_model(factory_name)
        self.model_name = model_name
        self.factory_name = factory_name
        # 配置日志文件，当文件大小达到1MB时自动轮转，日志级别为DEBUG
        LOG.add("daily_progress/llm_logs.log", rotation="1 MB", level="DEBUG")

    def generate_daily_report(self, markdown_content, dry_run=False):
        # 构建一个用于生成报告的提示文本，要求生成的报告包含新增功能、主要改进和问题修复
        prompt = f"以下是项目的最新进展，根据功能合并同类项，形成一份简报，至少包含：1）新增功能；2）主要改进；3）修复问题；:\n\n{markdown_content}"
        
        if dry_run:
            # 如果启用了dry_run模式，将不会调用模型，而是将提示信息保存到文件中
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/prompt.txt", "w+") as f:
                f.write(prompt)
            LOG.debug("Prompt saved to daily_progress/prompt.txt")
            return "DRY RUN"

        # 日志记录开始生成报告
        LOG.info("Starting report generation using GPT model.")
        
        try:
            # 调用OpenAI GPT模型生成报告
            response = self.client.chat.completions.create(
                model=self.model_name,  # 指定使用的模型版本
                messages=[
                    {"role": "user", "content": prompt}  # 提交用户角色的消息
                ]
            )
            LOG.debug("GPT response: {}", response)
            # 返回模型生成的内容
            return response.choices[0].message.content
        except Exception as e:
            # 如果在请求过程中出现异常，记录错误并抛出
            LOG.error("An error occurred while generating the report: {}", e)
            raise


if __name__ == "__main__":
    
    # 火山 没有 gpt 模型，可以使用 deepseek 模型，或者 apiyi 模型
    # deepseek-v3-2-251201   chat 模型 
    llm = LLM(factory_name="ark",model_name="deepseek-v3-2-251201")

    # 火山豆包模型  doubao-seed-2-0-pro-260215  
    llm2 = LLM(factory_name="ark",model_name="doubao-seed-2-0-pro-260215")

    # doubao-seed-2-0-lite-260215  
    llm3 = LLM(factory_name="ark",model_name="doubao-seed-2-0-lite-260215")