import json
import os
from pathlib import Path

class AppConfig:
    def __init__(self):
        # 💡 設定ファイルの場所は「マイドキュメント」で完全固定
        self.app_dir = Path.home() / "Documents" / "StarwardRankTracker"
        self.file_path = self.app_dir / "config.json"
        # デフォルト設定
        self.data = {
            "is_transparent": False,
            "is_all_record": False,
            "is_view_data": False,
            "save_path": str(self.app_dir / "match_log"),
            "profile_list":["default"],
            "profile":"default",
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
        # 💡 修正：ファイルを書き込む前に、親フォルダを自動作成する（すでにあればスキップされる）
        self.app_dir.mkdir(parents=True, exist_ok=True)
        """現在の設定をファイルに保存"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def update(self, key, value):
        """特定の値を更新して即座に保存"""
        self.data[key] = value
        self.save()