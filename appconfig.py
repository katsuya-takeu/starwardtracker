import json
import os

class AppConfig:
    def __init__(self, file_path="config.json"):
        self.file_path = file_path
        # デフォルト設定
        self.data = {
            "is_transparent": False,
            "is_all_record": False,
            "is_view_data": False,
            "save_path": "",
            "window_width": 350,
            "window_height": 600,
            "window_top": 100,
            "window_left": 100,
        }
        self.load()

    def load(self):
        """ファイルを読み込む。存在しない場合はデフォルトで作成"""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data.update(json.load(f))
        else:
            self.save()

    def save(self):
        """現在の設定をファイルに保存"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def update(self, key, value):
        """特定の値を更新して即座に保存"""
        self.data[key] = value
        self.save()