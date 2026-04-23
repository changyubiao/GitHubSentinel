import json
import os

class Config:
    def __init__(self,version:str="v1.0"):
        self.version = version
        
        self.load_config()


    def load_config(self):
        # 从环境变量获取GitHub Token
        self.github_token = os.getenv('GITHUB_TOKEN')
        # print(f"GitHub Token from environment: {self.github_token}")
        
        config_file = self.map_version_config_file_name(self.version)  
        with open(config_file, 'r') as f:
            config = json.load(f)
            
            # 如果环境变量中没有GitHub Token，则从配置文件中读取
            if not self.github_token:
                self.github_token = config.get('github_token')
                
            self.notification_settings = config.get('notification_settings')
            self.subscriptions_file = config.get('subscriptions_file')
            self.update_interval = config.get('update_interval', 24 * 60 * 60)  # 默认24小时
    
    
    
    
    def map_version_config_file_name(self,version: str) -> str:
        """
        处理 version 配置文件名
        :param version: 版本号字符串，例如 "v1.0", "v2.0", "v3.0" 等
        :return: 对应的配置文件名，例如 "config.json", "config_v3.json" 等
         - 如果 version 以 "v1" 或 "v2" 开头，返回 "config.json"
         - 如果 version 以 "v3" 开头，返回 "config_v3.json"
         - 其他情况默认返回 "config.json"
         - 版本号处理逻辑：去掉前缀 "v"，获取主版本号（第一个数字），根据主版本号判断配置文件名
         - 例如 "v1.0" -> "config.json", 
         "v2.5" -> "config.json", 
         "v3.0" -> "config_v3.json", "v3.1" -> "config_v3.json", 
         "v4.0" -> "config.json"
   
        """
    
        if not version:
            version = self.version if hasattr(self, 'version') else "v1.0"

        # 去除空格并转为小写，统一处理大小写问题
        version = version.strip().lower()
        
        # 如果以 v 开头，去掉 v 前缀,去掉版本号前面的 v 字母
        if version.startswith("v"):
            version = version[1:]
        
        # 获取主版本号（第一个数字）
        if version.startswith("1") or version.startswith("2"):
            return "config.json"
        elif version.startswith("3"):
            return "config_v3.json"
        else:
            return "config.json"  # 默认使用 config.json