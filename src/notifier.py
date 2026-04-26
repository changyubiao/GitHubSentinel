import smtplib
import markdown2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from logger import LOG

class Notifier:
    def __init__(self, email_settings):
        self.email_settings = email_settings
    
    def notify(self, repo, report):
        if self.email_settings:
            self.send_email(repo, report)
        else:
            LOG.warning("邮件设置未配置正确，无法发送通知")
    
    def send_email(self, repo, report):
        LOG.info("准备发送邮件")
        msg = MIMEMultipart()
        
        # 提取配置，避免重复访问字典
        sender = self.email_settings['from']
        receiver = self.email_settings['to']
        
        # 使用 Header 对象处理邮件头，确保非 ASCII 字符（如中文）正确编码
        msg['From'] = Header(sender)
        msg['To'] = Header(receiver)
        msg['Subject'] = Header(f"[GitHubSentinel]{repo} 进展简报", 'utf-8')
        
        # 将Markdown内容转换为HTML
        html_report = markdown2.markdown(report)
        msg.attach(MIMEText(html_report, 'html'))
        
        try:
            with smtplib.SMTP_SSL(self.email_settings['smtp_server'], self.email_settings['smtp_port']) as server:
                LOG.debug("登录SMTP服务器")
                # 使用明确的 sender 变量登录，而不是 msg['From']
                server.login(sender, self.email_settings['password'])
                # 收件人使用列表格式
                server.sendmail(sender, [receiver], msg.as_string())
                LOG.info("邮件发送成功！")
        except Exception as e:
            LOG.error(f"发送邮件失败：{str(e)}")

if __name__ == '__main__':
    from config import Config
    config = Config()
    # config = {
    #     # 修改为阿里云企业邮箱服务器
    #     'smtp_server': 'smtp.qiye.aliyun.com',
    #     'smtp_port': 465,
    #     'from': 'changyubiao@zhihe.com',
    #     'password': '9tSXJS04tCWggyti',
    #     'to': 'changyubiao@zhihe.com'
    # }
    notifier = Notifier(email_settings=config.email)
    from datetime import datetime
    test_repo = "DjangoPeng/openai-quickstart"
    test_report = f"""
# DjangoPeng/openai-quickstart 项目进展 

## 时间周期：2024-08-26 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 新增功能
- Assistants API 代码与文档

## 主要改进
- 适配 LangChain 新版本

## 修复问题
- 关闭了一些未解决的问题。

"""
    notifier.notify(test_repo, test_report)
