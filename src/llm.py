import os
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

    def get_model(self, model_name="apiyi"):
        """
        Returns a cached OpenAI client instance for the given model name.
        If not cached, creates a new one, caches it, and returns it.
        """
        if model_name in self._clients_cache:
            print(f"Using cached model: {model_name}")
            return self._clients_cache[model_name]

        print(f"Creating new client for model: {model_name}")
        
        # Get config, fallback to apiyi config if model_name unknown but try to be safe
        config = self.configs.get(model_name)
        
        if not config:
            # Fallback logic similar to original code
            print(f"Warning: Model '{model_name}' not found in configs. Falling back to 'apiyi'.")
            config = self.configs["apiyi"]
            
        try:
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
            )
            self._clients_cache[model_name] = client
            return client
        except Exception as e:
            print(f"Error creating client for {model_name}: {e}")
            raise


class LLM:
    def __init__(self):
        self.model_factory = ModelFactory()
        self.client = self.model_factory.get_model("apiyi")
        
    def generate_daily_report(self, markdown_content, dry_run=False):
        prompt = f"以下是项目的最新进展，根据功能合并同类项，形成一份简报，至少包含：1）新增功能；2）主要改进；3）修复问题；:\n\n{markdown_content}"
        if dry_run:
            with open("daily_progress/prompt.txt", "w+") as f:
                f.write(prompt)
            return "DRY RUN"

        print("Before call GPT")
        # Note: Ensure the model name passed here matches what you want to use. 
        # Currently hardcoded to gpt-3.5-turbo in the API call, but the client might be for Yi/DeepSeek.
        # You might want to make the model name dynamic too.
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
        )
        print("After call GPT")
        print(response)
        return response.choices[0].message.content