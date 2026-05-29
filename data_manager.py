import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta
from appconfig import AppConfig
"""
0: 試合中
1: リザルト
2: 試合完了
3: 試合途中終了
"""
class DataManager:
    def __init__(self, config:AppConfig):
        self.current_match = ""
        self.config = config
        
        # parents=Trueで中間ディレクトリも作成、exist_ok=Trueで既存でもエラーにしない
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.reset_match()

    @property
    def data_path(self) -> Path:
        """他のメソッドから self.data_path として呼ばれた瞬間に、

        常に最新のconfigを元にパスを計算して返す魔法の関数
        """
        base_path = Path(self.config.data["save_path"])
        current_profile = self.config.data.get("profile", "default")
        return base_path / current_profile

    def reset_match(self):
        self.chara_list = {}
        self.pos = -1
        self.rank_point = -1
        self.result = ""

    def save_match_metadata(self, pos, chara_list):
        self.pos = pos
        self.chara_list = chara_list
        
    def save_rank(self, rank):
        self.rank_point = rank
    def save_match_result(self, result):
        self.result = result
    def get_pos(self):
        return self.pos

    # =====================================================================
    # 1. 保存用の関数 (ログを1行ずつ追記する)
    # =====================================================================
    def append_match_log_jsonl(self, match_data:dict):
        """1試合分の辞書データをJSON Lines形式(.jsonl)でファイルの末尾に追記する"""
        datetime_now = datetime.now()
        id = int(datetime_now.timestamp())
        now = datetime_now.strftime("%Y-%m-%d %H:%M:%S")
        # 年を100倍して月を足す（一番高速でスマートな方法）
        year_month = (datetime_now.year * 100) + datetime_now.month  # 202405 (int)
        file_name = self.data_path / f"log_{year_month}.jsonl"
        file_name.parent.mkdir(parents=True, exist_ok=True)

        match_data["id"] = id
        match_data["datetime"] = now
        match_data["result"] = self.result
        match_data["rank_point"] = self.rank_point

        # ensure_ascii=False にすることで日本語（キャラ名など）がサニタイズされずそのまま保存されます
        json_string = json.dumps(match_data, ensure_ascii=False)

        # mode="a" (Append) で開き、末尾に改行コード(\n)を足して書き込む
        with open(file_name, mode="a", encoding="utf-8") as f:
            f.write(json_string + "\n")

        self.reset_match()
