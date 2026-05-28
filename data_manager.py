
import time
import csv
import os
import pandas as pd
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta
"""
0: 試合中
1: リザルト
2: 試合完了
3: 試合途中終了
"""
class DataManager:
    def __init__(self, path):
        self.current_match = ""
        # 文字列のpathをPathオブジェクトに変換
        base_path = Path(path)
        self.data_path = base_path / "match_log"
        
        # parents=Trueで中間ディレクトリも作成、exist_ok=Trueで既存でもエラーにしない
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.reset_match()

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

    def log_to_csv(self, damage, kill, death, lock):
        datetime_now = datetime.now()
        id = int(datetime_now.timestamp())
        now = datetime_now.strftime("%Y-%m-%d %H:%M:%S")
        # 年を100倍して月を足す（一番高速でスマートな方法）
        year_month = (datetime_now.year * 100) + datetime_now.month  # 202405 (int)
        file_name = self.data_path / f"log_{year_month}.csv"
        file_name.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = file_name.exists()
        chara, our, enemy1, enemy2 = "", "", "", ""
        if len(self.chara_list) == 4:
            chara = self.chara_list[0]
            our = self.chara_list[1]
            enemy1 = self.chara_list[2]
            enemy2 = self.chara_list[3]

        with open(file_name, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "ID",
                    "DateTime", 
                    "RankPoint",       # 勝敗
                    "Chara",        # 使用キャラ
                    "OurChara",        # 相方キャラ
                    "EnemyChara1",         # 敵使用キャラ1
                    "EnemyChara2",    # 敵使用キャラ2
                    "Result",       # 勝敗
                    "Damage",        #ダメージ
                    "Kill",
                    "Death",
                    "LockRate",     #被ロック率
                ])
            writer.writerow([id, now, self.rank_point, chara, our, enemy1, enemy2, self.result, damage, kill, death, lock])

        self.reset_match()
        
    def use_item(self, item, num):
        self.log_to_csv("ItemUse", num, item, "", "")
    
    def use_weapon(self, weapon, num):
        self.log_to_csv("WeaponUse", num, weapon, "", "")
    
    def save_move(self, dist, weapon):
        self.log_to_csv("Move", dist, weapon, "", "")

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


    # =====================================================================
    # 2. 読み込み用の関数 (Pandasで一発でデータフレーム化する)
    # =====================================================================
    def load_match_log_jsonl(file_path):
        """JSON Linesファイルを読み込んでPandasのDataFrameを返す"""
        if not os.path.exists(file_path):
            print(f"ファイルが見つかりません: {file_path}")
            return pd.DataFrame()

        # lines=True を指定するのが最大のポイントです
        df = pd.read_json(file_path, lines=True)
        return df


    # =====================================================================
    # 動作テスト用のメイン処理
    # =====================================================================
    if __name__ == "__main__":
        FILE_NAME = "battle_log_v2.jsonl"

        # 今回保存したい「4人分のデータ ＋ 自分の立ち位置」の構造サンプル
        sample_match_1 = {
            "id": 1779877248,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": "win",
            "my_team": {
                "player1": {
                    "chara": "gourai",
                    "damage": 4946,
                    "kill": 1,
                    "death": 1,
                    "lock_rate": 46,
                    "is_me": True,
                },
                "player2": {
                    "chara": "hikari",
                    "damage": 3200,
                    "kill": 2,
                    "death": 0,
                    "lock_rate": 34,
                    "is_me": False,
                },
            },
            "enemy_team": {
                "player1": {
                    "chara": "kelbim",
                    "damage": 2800,
                    "kill": 1,
                    "death": 2,
                    "lock_rate": 52,
                },
                "player2": {
                    "chara": "valkia",
                    "damage": 1500,
                    "kill": 0,
                    "death": 2,
                    "lock_rate": 48,
                },
            },
            "my_position": {
                "damage_share": 60.7,  # 4946 / (4946 + 3200)
                "death_share": 100.0,  # 1 / (1 + 0)
                "damage_rank_in_match": 1,  # 4人の中で1位
                "role_type": "Carry",  # 与ダメもヘイトも高いエース
            },
        }

        # 1. 試合データを追記保存してみる（2回実行して2試合分にする）
        append_match_log_jsonl(FILE_NAME, sample_match_1)
        print("試合ログを追記しました。")

        # 2. Pandasで読み込んでみる
        df = load_match_log_jsonl(FILE_NAME)

        print("\n--- Pandas DataFrame の概要 ---")
        print(df.head())

        # 3. JSONの深い階層（ネスト）をフラットな表に展開したい場合
        print("\n--- データをフラットに展開（json_normalize） ---")
        # dfの辞書列を展開して1つの綺麗な表にする
        flat_df = pd.json_normalize(df.to_dict(orient="records"))
        print(flat_df[["id", "result", "my_position.role_type", "my_position.damage_share"]])