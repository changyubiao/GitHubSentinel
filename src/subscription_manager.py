import json
from datetime import datetime, timezone, timedelta

from logger import LOG


class SubscriptionManager:
    def __init__(self, subscriptions_file):
        self.subscriptions_file = subscriptions_file
        self.subscriptions = self.load_subscriptions()
        self.cur_id = self.length

    def load_subscriptions(self):
        with open(self.subscriptions_file, "r") as f:
            return json.load(f)

    def save_subscriptions(self):
        with open(self.subscriptions_file, "w") as f:
            json.dump(self.subscriptions, f, indent=4, ensure_ascii=False)

    def list_subscriptions(self) -> list:
        return self.subscriptions

    @property
    def length(self):
        """获取当前的列表的长度

        Returns:
            _type_: _description_
        """
        return len(self.subscriptions)

    def list_subscription_repos(self):
        """返回仓库名称列表

        按照顺序返回

        Returns:
            _type_: _description_
        """
        return [sub["repo_name"] for sub in self.subscriptions]

    def add_subscription(self, repo) -> bool:
        """按 repo_name 去重；已存在则不入库并返回 False。支持 dict（UI）或 str（CLI）。"""
        if isinstance(repo, str):
            name = repo.strip()
            if not name:
                return False

            # 重复性检查
            if name in self.list_subscription_repos():
                LOG.warning(f"仓库「{name}」已在订阅列表中，无需重复添加。")
                return False

            item = {
                "repo_name": name,
                "subscribe_time": datetime.now(tz=timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "正常",
            }
        elif isinstance(repo, dict) and repo.get("repo_name"):
            repo_name = repo.get("repo_name").strip()
            if repo_name in self.list_subscription_repos():
                return False
            item = dict(repo)
            item["repo_name"] = str(item["repo_name"]).strip()
        else:
            LOG.warning(f"add_subscription: invalid payload {repo!r}")
            return False

        # if any(str(s.get("repo_name", "")).strip() == name for s in self.subscriptions):
        #     return False
        self.subscriptions.append(item)
        self.save_subscriptions()
        return True

    def remove_subscription(self, repo):
        if repo in self.subscriptions:
            self.subscriptions.remove(repo)
            self.save_subscriptions()

    # 根据索引下标删除
    def delete_subscription(self, index: int):
        """
            删除下标的数据项

        Args:
            index (int): 删除下标
        """
        if index >= 0 and index < len(self.subscriptions):
            del self.subscriptions[index]
            self.save_subscriptions()
            return True
        LOG.warning(f"Index {index} out of range for subscriptions list.")
        return False
