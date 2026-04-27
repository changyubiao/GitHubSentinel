import json
import os

class Config:
    def __init__(self,version:str="v1.0"):
        self.version = version
        
        self.load_config()


    def load_config(self):
        
        config_file = self.map_version_config_file_name(self.version)  
        with open(config_file, 'r') as f:
            config = json.load(f)
            
            # 使用环境变量或配置文件的 GitHub Token
            self.github_token = os.getenv('GITHUB_TOKEN', config.get('github_token'))

            # 初始化电子邮件设置
            self.email = config.get('email', {})
            # 使用环境变量或配置文件中的电子邮件密码
            self.email['password'] = os.getenv('EMAIL_PASSWORD', self.email.get('password', ''))

            self.subscriptions_file = config.get('subscriptions_file')
            # 默认每天执行
            self.freq_days = config.get('github_progress_frequency_days', 1)
            # 默认早上8点更新 (操作系统默认时区是 UTC +0，08点刚好对应北京时间凌晨12点)
            self.exec_time = config.get('github_progress_execution_time', "08:00") 

    
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
        elif version.startswith("4"):
            return "config_v3.json"
        elif version.startswith("5"):
            return "config_v3.json"
        else:
            return "config.json"  # 默认使用 config.json