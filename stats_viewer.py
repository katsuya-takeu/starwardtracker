import flet as ft
import pandas as pd
import os
import glob
from pathlib import Path
from datetime import datetime, timedelta
from appconfig import AppConfig


class StatsViewer:
    def __init__(self, config):
        self.config = config
        self.full_df = None       # 全データ保持用
        self.filtered_df = None   # フィルター後のデータ保持用
        self.built_tabs = {}      # タブのビルド状態管理
        self.tabs_container = None # タブコントロールの参照保持用

    def get_error_text(self, text):
        return ft.Text(text,
            width=350,
            height=500,
        )
    
    # キャラクター名の英語IDから日本語へのマッピング辞書
    CHARACTER_NAMES = {
        "18gou": "18号",
        "aida": "アイーダ",
        "akatsuki": "アカツキ",
        "akigumo": "秋雲",
        "alice": "アリス",
        "anjeris": "アンジェリス",
        "barzerald": "バーゼラルド",
        "beta": "ベータ",
        "bolzoi": "ボルゾイ",
        "briker": "ブリーカー",
        "brs": "ブラック★ロックシューター",  # コラボキャラ
        "cammy": "キャミィ",
        "cati": "キャッティ",
        "catrina": "カタリナ",
        "cavary": "キャヴァリー",
        "ceilen": "セイレン",
        "celafim": "セラフィム",
        "chinni": "チンニ",
        "clysta": "クリスタ",
        "darkstar": "ダークスター",
        "dead_alive": "デッド・アライブ",
        "deadmaster": "デッドマスター",  # コラボキャラ
        "dragner": "ドラグナー",
        "ducarion": "デュカリオン",
        "elfin": "エルフィン",
        "emika": "エミカ",
        "eva": "エヴァ",
        "ezar": "イーザー",
        "fiby": "フィービー",
        "frankar": "フランカー",
        "freed": "フリード",
        "garahad": "ガラハッド",
        "garahad_akatsuki": "ガラハッド・暁",  # あるいは「黎明」など機体バリエーション
        "gourai": "轟雷改",  # コラボキャラ
        "grifin": "グリフィン",
        "haruka": "ハルカ",
        "hibiki": "ヒビキ",
        "hikari": "ヒカリ",
        "icelin": "アイスリン",
        "ine": "稲",
        "kage": "影",
        "kaze": "カゼ",
        "kelbim": "ケルビム",
        "line": "ライン",
        "mumei": "無銘",  # コラボキャラ
        "nora": "ノーラ",
        "okid": "オーキッド",
        "palas": "パラス",
        "ragel": "ラジエル",
        "ranslot": "ランスロット",
        "reki": "レキ",
        "roland": "ローランド",
        "rota": "ロタ",
        "scopion": "スコーピオン",
        "sharp": "シャープ",
        "signas": "シグナス",
        "skysaber": "スカイセーバー",
        "snowwol": "スノーウォル",
        "stilet": "スティレット",  # コラボキャラ
        "suzuran": "スズラン",
        "syaolin": "シャオリン",
        "syuu": "シュウウ",
        "tachiana": "タチアナ",
        "thanderbolt_otome": "サンダーボルト・乙女",  # 「雷電・乙女」など
        "vache": "ヴァーチェ",
        "valkia": "ヴァルキア",
        "yammn": "ヤミン",
        "zaharowa": "ザハロワ",
        "voidsaber": "ヴォイドセーバー",
        
        "Rbeta": "ロンギヌスベータ",
    }
    # キャラクター名の英語IDから日本語へのマッピング辞書
    CHARACTER_COSTS = {
        "18gou": 2.5,
        "aida": 2.0,
        "akatsuki": 3.0,
        "akigumo": 3.0,
        "alice": 2.5,
        "anjeris": 2.5,
        "barzerald": 2.5,
        "beta": 2.0,
        "bolzoi": 2.0,
        "briker": 2.0,
        "brs": 2.5,  # コラボキャラ
        "cammy": 3.0,
        "cati": 2.0,
        "catrina": 1.5,
        "cavary": 3.0,
        "ceilen": 3.0,
        "celafim": 2.0,
        "chinni": 2.0,
        "clysta": 2.0,
        "darkstar": 2.0,
        "dead_alive": 2.5,
        "deadmaster": 2.5,  # コラボキャラ
        "dragner": 2.5,
        "ducarion": 2.0,
        "elfin": 3.0,
        "emika": 2.0,
        "eva": 2.5,
        "ezar": 3.0,
        "fiby": 2.0,
        "frankar": 2.0,
        "freed": 2.5,
        "garahad": 2.0,
        "garahad_akatsuki": 2.5,  # あるいは「黎明」など機体バリエーション
        "gourai": 2.5,  # コラボキャラ
        "grifin": 3.0,
        "haruka": 2.5,
        "hibiki": 2.0,
        "hikari": 3.0,
        "icelin": 2.0,
        "ine": 2.5,
        "kage": 3.0,
        "kaze": 2.5,
        "kelbim": 3.0,
        "line": 3.0,
        "mumei": 3.0,  # コラボキャラ
        "nora": 2.5,
        "okid": 1.5,
        "palas": 2.0,
        "ragel": 3.0,
        "ranslot": 2.5,
        "reki": 3.0,
        "roland": 1.5,
        "rota": 3.0,
        "scopion": 2.0,
        "sharp": 2.5,
        "signas": 2.5,
        "skysaber": 2.5,
        "snowwol": 1.5,
        "stilet": 2.0,  # コラボキャラ
        "suzuran": 3.0,
        "syaolin": 2.5,
        "syuu": 3.0,
        "tachiana": 2.0,
        "thanderbolt_otome": 2.5,  # 「雷電・乙女」など
        "vache": 2.0,
        "valkia": 2.5,
        "yammn": 1.5,
        "zaharowa": 2.0,
        "voidsaber": 3.0,
        
        "Rbeta": 3.0,
    }

    def get_chara_name(self, chara_id):
        return self.CHARACTER_NAMES.get(chara_id, chara_id)
    
    def get_chara_cost(self, chara_id):
        # 定義にないキャラはデフォルトで2.0コストとして処理
        return self.CHARACTER_COSTS.get(chara_id, 2.0)

    def get_view(self, jsonl_paths="log_*.jsonl"):
        # 💡 ベースの保存先パスを取得
        base_save_path = Path(self.config.data["save_path"])
        # 💡 現在選択中のプロファイル名を取得（なければ default）
        current_profile = self.config.data.get("profile", "default")
        
        # 💡 パスを「保存先 / プロファイル名」にする (例: match_log/default/)
        save_path = base_save_path / current_profile
        
        if isinstance(jsonl_paths, str):
            if "*" in jsonl_paths:
                files = glob.glob(str(save_path / jsonl_paths))
            else:
                files = [str(save_path / jsonl_paths)]
        elif isinstance(jsonl_paths, list):
            files = [str(save_path / p) for p in jsonl_paths]
        else:
            files = []

        valid_files = [f for f in files if os.path.exists(f)]

        if not valid_files:
            return ft.Container(
                content=ft.Text(f"エラー: 有効なJSON Linesファイルが見つかりません。({jsonl_paths})", color="red", size=16),
                padding=20
            )

        try:
            df_list = [pd.read_json(f, lines=True) for f in valid_files]
            raw_df = pd.concat(df_list, ignore_index=True)
            self.full_df = pd.json_normalize(raw_df.to_dict(orient="records"))
            
            # 基本フラット化マッピング
            self.full_df['is_win'] = self.full_df['result'].astype(str).str.lower() == 'win'
            self.full_df['Chara'] = self.full_df['player_team.player.chara']
            self.full_df['OurChara'] = self.full_df['player_team.player2.chara']
            self.full_df['Damage'] = self.full_df['player_team.player.damage']
            self.full_df['Kill'] = self.full_df['player_team.player.kill']
            self.full_df['Death'] = self.full_df['player_team.player.death']
            self.full_df['LockRate'] = self.full_df['player_team.player.lock']
            
            # チーム内ダメージシェア
            self.full_df['team_total_damage'] = self.full_df['player_team.player.damage'] + self.full_df['player_team.player2.damage']
            self.full_df['my_damage_share'] = (self.full_df['Damage'] / self.full_df['team_total_damage'] * 100).fillna(0)

            # コスト計算ロジック
            my_c = self.full_df['Chara'].apply(self.get_chara_cost)
            our_c = self.full_df['OurChara'].apply(self.get_chara_cost)
            self.full_df['my_team_cost'] = [f"{max(m, o):.1f} + {min(m, o):.1f}" for m, o in zip(my_c, our_c)]

            e1_c = self.full_df['enemy_team.enemy.chara'].apply(self.get_chara_cost)
            e2_c = self.full_df['enemy_team.enemy2.chara'].apply(self.get_chara_cost)
            self.full_df['enemy_team_cost'] = [f"{max(e1, e2):.1f} + {min(e1, e2):.1f}" for e1, e2 in zip(e1_c, e2_c)]

        except Exception as e:
            return ft.Container(
                content=ft.Text(f"JSON Linesの読み込み・展開中にエラーが発生しました:\n{e}", color="red", size=14),
                padding=20
            )
        
        # データのdatetime列をパース（文字列からTimestampオブジェクトへ）
        self.full_df['datetime'] = pd.to_datetime(self.full_df['datetime'])
        
        # 最初は全データをフィルター用データに入れておく
        self.filtered_df = self.full_df.copy()

        # ----------------------------------------------------
        # フィルター処理のコアロジック
        # ----------------------------------------------------
        def apply_filter(filter_value):
            now = datetime.now()
            df = self.full_df.copy()
            
            if filter_value == "3days":
                three_days_ago = now - timedelta(days=3)
                self.filtered_df = df[df['datetime'] >= three_days_ago]
            elif filter_value == "week":
                one_week_ago = now - timedelta(days=7)
                self.filtered_df = df[df['datetime'] >= one_week_ago]
            elif filter_value == "month":
                this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                self.filtered_df = df[df['datetime'] >= this_month_start]
            else:
                self.filtered_df = df  # 「すべて」

        enemy_cols = ['enemy_team.enemy.chara', 'enemy_team.enemy2.chara']

        # 総合サマリー
        total_matches = len(self.filtered_df)
        total_wins = self.filtered_df['is_win'].sum()
        total_losses = total_matches - total_wins
        total_win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

        # ----------------------------------------------------
        # フィルターが変更された時のイベントハンドラ
        # ----------------------------------------------------
        def on_filter_changed(e):
            # 1. 選択された条件でデータを絞り込む
            apply_filter(filter_dropdown.value)
            
            # 2. 現在アクティブなタブだけをその場で再ビルドする
            current_idx = self.tabs_container.selected_index
            
            # 一旦すべてのタブのビルドフラグをリセット（今見ているタブ以外は未ビルド状態にする）
            self.built_tabs = {0: False, 1: False, 2: False, 3: False}
            
            # 今見ているタブだけその場で即時生成
            if current_idx == 0:
                build_stats_ui()
            elif current_idx == 1:
                build_enemy_stats_ui()
            elif current_idx == 2:
                build_cost_stats_ui()
            elif current_idx == 3:
                build_history_ui()
                
            # 今見ているタブのフラグだけTrueにして更新
            self.built_tabs[current_idx] = True
            self.tabs_container.update()

        # ----------------------------------------------------
        # フィルターUI（Dropdown）の作成
        # ----------------------------------------------------
        filter_dropdown = ft.Dropdown(
            label="集計期間",
            value="all",  # 初期値
            width=200,
            options=[
                ft.dropdown.Option("all", "すべての期間"),
                ft.dropdown.Option("3days", "直近 3 日間"),
                ft.dropdown.Option("week", "直近 1 週間"),
                ft.dropdown.Option("month", "今月のログ"),
            ],
            on_select=on_filter_changed # 変更時に走る
        )

        header = ft.Row([
            ft.Column([
                ft.Text("星の翼 戦績アナリティクス", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                ft.Text("キャラスタッツ・コスト編成シナジー・対戦履歴の一元管理", size=13, color=ft.Colors.GREY_400),
            ]),
            filter_dropdown
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        summary_card = ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Column([ft.Text("総試合数", size=11, color=ft.Colors.GREY_400), ft.Text(f"{total_matches}", size=20, weight="bold")]),
                    ft.Column([ft.Text("勝敗", size=11, color=ft.Colors.GREY_400), ft.Text(f"{total_wins}勝 - {total_losses}敗", size=20, weight="bold", color=ft.Colors.GREEN_400)]),
                    ft.Column([ft.Text("総合勝率", size=11, color=ft.Colors.GREY_400), ft.Text(f"{total_win_rate:.1f}%", size=20, weight="bold", color=ft.Colors.BLUE_400)]),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                padding=15
            ),
            bgcolor=ft.Colors.SURFACE_BRIGHT
        )

        # ドロップダウンが変更された時の処理
        def on_filter_changed(e):
            # 1. 選択された条件（例: 勝率50%以上のキャラがいる試合、など任意の条件）で self.full_df を絞り込む
            # ここでは例として、Dropdownの値に応じて処理を分岐させます
            if filter_dropdown.value == "win_only":
                self.filtered_df = self.full_df[self.full_df['is_win']].copy()
            else:
                self.filtered_df = self.full_df.copy() # 「すべて」なら全コピー

            # 2. 今見ているアクティブなタブを再ビルド
            if self.tabs_container.selected_index == 0:
                build_stats_ui()
            else:
                build_enemy_stats_ui()
                
            # 3. 画面（タブ）を更新
            self.tabs_container.update()

        # フィルター用ドロップダウン
        filter_dropdown = ft.Dropdown(
            label="データフィルター",
            value="all",
            options=[
                ft.dropdown.Option("all", "すべての試合"),
                ft.dropdown.Option("win_only", "勝利試合のみ"),
            ],
            on_select=on_filter_changed
        )

        # ----------------------------------------------------
        # 各タブの内容を保持するプレースホルダー（最初は空、またはLoading）
        # ----------------------------------------------------
        stats_list_container = ft.Column(spacing=10)
        enemy_list_container = ft.Column(controls=[ft.ProgressRing(), ft.Text("読み込み中...")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        cost_list_container = ft.Column(controls=[ft.ProgressRing(), ft.Text("読み込み中...")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        history_list_container = ft.Column(controls=[ft.ProgressRing(), ft.Text("読み込み中...")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # 状態管理フラグ（すでに生成したか）
        self.built_tabs = {0: True, 1: False, 2: False, 3: False}

        # ----------------------------------------------------
        # 【機能1】マイキャラ軸スタッツ (常に総合スタッツを表示)
        # ----------------------------------------------------
        def build_stats_ui():
            stats_list_container.controls.clear()
            df = self.filtered_df.copy()

            if df.empty:
                stats_list_container.controls.append(ft.Text("該当する対戦データがありません。", color=ft.Colors.GREY_500, italic=True))
                return

            chara_summary_list = []
            for chara_id, c_df in df.groupby('Chara'):
                c_matches = len(c_df)
                c_wins = c_df['is_win'].sum()
                chara_summary_list.append({
                    'id': chara_id, 'df': c_df, 'matches': c_matches, 'wins': c_wins,
                    'losses': c_matches - c_wins, 'win_rate': (c_wins / c_matches * 100),
                    'avg_dmg': c_df['Damage'].mean(), 'avg_kill': c_df['Kill'].mean(),
                    'avg_death': c_df['Death'].mean(), 'avg_lock': c_df['LockRate'].mean(),
                    'avg_share': c_df['my_damage_share'].mean()
                })

            # 使用試合数順にソート
            chara_summary_list.sort(key=lambda x: x['matches'], reverse=True)

            for c in chara_summary_list:
                partner_rows = []
                partner_stats_list = []
                for p_id, p_df in c['df'].groupby('OurChara'):
                    p_matches = len(p_df)
                    p_wins = p_df['is_win'].sum()
                    partner_stats_list.append({
                        'name': self.get_chara_name(p_id), 'matches': p_matches, 'wins': p_wins,
                        'losses': p_matches - p_wins, 'win_rate': (p_wins / p_matches * 100),
                        'avg_dmg': p_df['Damage'].mean(), 'avg_kill': p_df['Kill'].mean(),
                        'avg_death': p_df['Death'].mean(), 'avg_lock': p_df['LockRate'].mean(),
                        'avg_share': p_df['my_damage_share'].mean()
                    })
                
                # 相方との試合数順にソート
                partner_stats_list.sort(key=lambda x: x['matches'], reverse=True)

                for p in partner_stats_list:
                    rate_color = ft.Colors.GREEN_400 if p['win_rate'] >= 50 else ft.Colors.RED_400
                    partner_rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(p['name'], weight="bold")), ft.DataCell(ft.Text(f"{p['matches']}戦")),
                        ft.DataCell(ft.Text(f"{p['wins']}W - {p['losses']}L")), ft.DataCell(ft.Text(f"{p['win_rate']:.1f}%", color=rate_color, weight="bold")),
                        ft.DataCell(ft.Text(f"{p['avg_dmg']:.0f}")), ft.DataCell(ft.Text(f"{p['avg_share']:.1f}%", color=ft.Colors.BLUE_100)),
                        ft.DataCell(ft.Text(f"{p['avg_kill']:.1f} / {p['avg_death']:.1f}")), ft.DataCell(ft.Text(f"{p['avg_lock']:.1f}")),
                    ]))

                partner_table = ft.DataTable(
                    columns=[ft.DataColumn(ft.Text("相方キャラ")), ft.DataColumn(ft.Text("試合数")), ft.DataColumn(ft.Text("勝敗")),
                             ft.DataColumn(ft.Text("勝率")), ft.DataColumn(ft.Text("平均DMG")),
                             ft.DataColumn(ft.Text("ダメシェア")), ft.DataColumn(ft.Text("平均K / D")), ft.DataColumn(ft.Text("平均ロック率"))],
                    rows=partner_rows, heading_row_color=ft.Colors.BLACK26, column_spacing=20
                )

                badge_text = f"{c['win_rate']:.1f}%"
                badge_color = ft.Colors.BLUE_300 if c['win_rate'] >= 50 else ft.Colors.ORANGE_300

                tile = ft.ExpansionTile(
                    title=ft.Row([ft.Text(self.get_chara_name(c['id']), size=16, weight=ft.FontWeight.BOLD, width=180),
                                  ft.Text(badge_text, size=16, weight="bold", color=badge_color, width=110),
                                  ft.Text(f"({c['wins']}勝 - {c['losses']}敗 / 計 {c['matches']}戦)", size=13, color=ft.Colors.GREY_400)]),
                    subtitle=ft.Row([ft.Text(f"平均ダメージ: {c['avg_dmg']:.0f} ({c['avg_share']:.1f}%)", size=11, color=ft.Colors.GREY, margin=15),
                                     ft.Text(f"平均K/D: {c['avg_kill']:.1f} / {c['avg_death']:.1f}", size=11, color=ft.Colors.GREY),
                                     ft.Text(f"平均ロック率: {c['avg_lock']:.1f}", size=11, color=ft.Colors.GREY, margin=15)]),
                    controls=[ft.Container(content=ft.Column([ft.Text("▼ 相方別の詳細相性スタッツ", size=12, color=ft.Colors.BLUE_200, weight="bold"), ft.Container(content=partner_table)], spacing=8),
                                           padding=12, bgcolor=ft.Colors.BLACK12, border_radius=8, margin=5)],
                    text_color=ft.Colors.BLUE_200
                )
                stats_list_container.controls.append(ft.Card(content=tile, elevation=2))

        # ----------------------------------------------------
        # 【機能2】対戦相手軸分析
        # ----------------------------------------------------
        def build_enemy_stats_ui():
            enemy_list_container.controls.clear()
            if self.filtered_df.empty:
                enemy_list_container.controls.append(ft.Text("対戦データがありません。", color=ft.Colors.GREY_500, italic=True))
                return

            melted_records = []
            for _, row in self.filtered_df.iterrows():
                enemies = set([row[c] for c in enemy_cols if c in self.filtered_df.columns and pd.notna(row[c]) and str(row[c]).strip() != ""])
                for enemy_id in enemies:
                    rec = row.to_dict(); rec['EnemyCharaID'] = enemy_id; melted_records.append(rec)

            if not melted_records:
                enemy_list_container.controls.append(ft.Text("相手キャラのキーが見つかりません。", color=ft.Colors.GREY_500))
                return

            enemy_match_df = pd.DataFrame(melted_records)
            enemy_summary = []
            for enemy_id, e_df in enemy_match_df.groupby('EnemyCharaID'):
                enemy_summary.append({'id': enemy_id, 'df': e_df, 'matches': len(e_df), 'rate': (len(e_df) / len(self.filtered_df) * 100), 'win_rate': e_df['is_win'].sum() / len(e_df) * 100})
            
            enemy_summary.sort(key=lambda x: x['matches'], reverse=True)
            
            for e in enemy_summary:
                my_chara_rows = []
                combo_stats = []
                for (my_chara_id, partner_id), c_df in e['df'].groupby(['Chara', 'OurChara']):
                    m_matches = len(c_df); m_wins = c_df['is_win'].sum()
                    combo_stats.append({
                        'my_id': my_chara_id, 'partner_id': partner_id, 'matches': m_matches, 'wins': m_wins, 'losses': m_matches - m_wins,
                        'win_rate': (m_wins / m_matches * 100), 'avg_dmg': c_df['Damage'].mean(), 'avg_kill': c_df['Kill'].mean(),
                        'avg_death': c_df['Death'].mean(), 'avg_lock': c_df['LockRate'].mean(), 'avg_share': c_df['my_damage_share'].mean()
                    })
                
                combo_stats.sort(key=lambda x: x['matches'], reverse=True)
                for m in combo_stats:
                    rate_color = ft.Colors.GREEN_400 if m['win_rate'] >= 50 else ft.Colors.RED_400
                    my_chara_rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(self.get_chara_name(m['my_id']), weight="bold")), ft.DataCell(ft.Text(self.get_chara_name(m['partner_id']))),
                        ft.DataCell(ft.Text(f"{m['matches']}戦")), ft.DataCell(ft.Text(f"{m['wins']}W - {m['losses']}L")),
                        ft.DataCell(ft.Text(f"{m['win_rate']:.1f}%", color=rate_color, weight="bold")), ft.DataCell(ft.Text(f"{m['avg_dmg']:.0f}")),
                        ft.DataCell(ft.Text(f"{m['avg_share']:.1f}%", color=ft.Colors.BLUE_100)), ft.DataCell(ft.Text(f"{m['avg_kill']:.1f} / {m['avg_death']:.1f}")),
                        ft.DataCell(ft.Text(f"{m['avg_lock']:.1f}")),
                    ]))
                    
                my_chara_table = ft.DataTable(
                    columns=[ft.DataColumn(ft.Text("使用キャラ")), ft.DataColumn(ft.Text("相方キャラ")), ft.DataColumn(ft.Text("試合数")),
                             ft.DataColumn(ft.Text("勝敗")), ft.DataColumn(ft.Text("対面勝率")), ft.DataColumn(ft.Text("平均DMG")),
                             ft.DataColumn(ft.Text("ダメシェア")), ft.DataColumn(ft.Text("平均K / D")), ft.DataColumn(ft.Text("平均ロック率")),],
                    rows=my_chara_rows, heading_row_color=ft.Colors.BLACK26, column_spacing=15
                )
                
                tile = ft.ExpansionTile(
                    title=ft.Row([ft.Text(self.get_chara_name(e['id']), size=16, weight=ft.FontWeight.BOLD, width=180),
                                  ft.Text(f"採用率 {e['rate']:.1f}%", size=15, weight="bold", color=ft.Colors.BLUE_200, width=110),
                                  ft.Text(f"(総遭遇: {e['matches']}回)", size=13, color=ft.Colors.GREY_400),
                                  ft.Text(f"勝率 {e['win_rate']:.1f}%", size=13, color=ft.Colors.GREY_400)]),
                    subtitle=ft.Text("このキャラが相手チームにいた時の、自分×相方の組み合わせ別スタッツ", size=11, color=ft.Colors.GREY),
                    controls=[ft.Container(content=ft.Column([ft.Text("▼ 詳細相性スタッツ", size=12, color=ft.Colors.BLUE_200, weight="bold"), ft.Container(content=my_chara_table)], spacing=8),
                                           padding=12, bgcolor=ft.Colors.BLACK12, border_radius=8, margin=5)],
                    text_color=ft.Colors.BLUE_200
                )
                enemy_list_container.controls.append(ft.Card(content=tile, elevation=2))

        # ----------------------------------------------------
        # 【機能3】コスト編成分析
        # ----------------------------------------------------
        def build_cost_stats_ui():
            cost_list_container.controls.clear()
            if self.filtered_df.empty:
                cost_list_container.controls.append(ft.Text("対戦データがありません。", color=ft.Colors.GREY_500, italic=True))
                return

            my_cost_summary = []
            for cost_pair, c_df in self.filtered_df.groupby('my_team_cost'):
                c_matches = len(c_df); c_wins = c_df['is_win'].sum()
                avg_my_death = c_df['Death'].mean()
                avg_our_death = c_df['player_team.player2.death'].mean() if 'player_team.player2.death' in c_df.columns else 0
                
                my_cost_summary.append({
                    'pair': cost_pair, 'matches': c_matches, 'wins': c_wins, 'losses': c_matches - c_wins,
                    'win_rate': (c_wins / c_matches * 100), 'avg_dmg': c_df['Damage'].mean(),
                    'total_death': avg_my_death + avg_our_death, 'my_death': avg_my_death, 'our_death': avg_our_death
                })
            my_cost_summary.sort(key=lambda x: x['matches'], reverse=True)

            my_cost_rows = []
            for item in my_cost_summary:
                rate_color = ft.Colors.GREEN_400 if item['win_rate'] >= 50 else ft.Colors.RED_400
                my_cost_rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item['pair'], weight="bold", color=ft.Colors.BLUE_100)),
                    ft.DataCell(ft.Text(f"{item['matches']}戦")),
                    ft.DataCell(ft.Text(f"{item['wins']}W - {item['losses']}L")),
                    ft.DataCell(ft.Text(f"{item['win_rate']:.1f}%", color=rate_color, weight="bold")),
                    ft.DataCell(ft.Text(f"{item['avg_dmg']:.0f}")),
                    ft.DataCell(ft.Text(f"{item['total_death']:.1f}回 (自:{item['my_death']:.1f}/相:{item['our_death']:.1f})")),
                ]))

            enemy_cost_summary = []
            for cost_pair, c_df in self.filtered_df.groupby('enemy_team_cost'):
                c_matches = len(c_df); c_wins = c_df['is_win'].sum()
                e_total_dmg = (c_df['enemy_team.enemy.damage'] + c_df['enemy_team.enemy2.damage']).mean() if 'enemy_team.enemy.damage' in c_df.columns else 0
                
                enemy_cost_summary.append({
                    'pair': cost_pair, 'matches': c_matches, 'wins': c_wins, 'losses': c_matches - c_wins,
                    'win_rate': (c_wins / c_matches * 100), 'avg_enemy_dmg': e_total_dmg
                })
            enemy_cost_summary.sort(key=lambda x: x['matches'], reverse=True)

            enemy_cost_rows = []
            for item in enemy_cost_summary:
                rate_color = ft.Colors.GREEN_400 if item['win_rate'] >= 50 else ft.Colors.RED_400
                enemy_cost_rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item['pair'], weight="bold", color=ft.Colors.RED_100)),
                    ft.DataCell(ft.Text(f"{item['matches']}戦")),
                    ft.DataCell(ft.Text(f"{item['wins']}W - {item['losses']}L")),
                    ft.DataCell(ft.Text(f"{item['win_rate']:.1f}%", color=rate_color, weight="bold")),
                    ft.DataCell(ft.Text(f"{item['avg_enemy_dmg']:.0f}")),
                ]))

            my_table = ft.DataTable(
                columns=[ft.DataColumn(ft.Text("自チーム編成")), ft.DataColumn(ft.Text("試合数")), ft.DataColumn(ft.Text("勝敗")),
                         ft.DataColumn(ft.Text("勝率")), ft.DataColumn(ft.Text("平均DMG")), ft.DataColumn(ft.Text("平均被撃墜(合計)")), ],
                rows=my_cost_rows, heading_row_color=ft.Colors.BLACK26
            )
            
            enemy_table = ft.DataTable(
                columns=[ft.DataColumn(ft.Text("敵チーム編成")), ft.DataColumn(ft.Text("遭遇数")), ft.DataColumn(ft.Text("勝敗")),
                         ft.DataColumn(ft.Text("対面勝率")), ft.DataColumn(ft.Text("敵チーム平均総DMG")), ],
                rows=enemy_cost_rows, heading_row_color=ft.Colors.BLACK26
            )

            cost_list_container.controls.append(
                ft.Column([
                    ft.Text("▼ 自チームのコスト編成別勝率 (運用シナジー)", size=14, weight="bold", color=ft.Colors.BLUE_200),
                    ft.Card(content=ft.Container(content=my_table, padding=10)),
                    ft.Container(height=15),
                    ft.Text("▼ 敵チームのコスト編成別相性 (対面勝率)", size=14, weight="bold", color=ft.Colors.RED_200),
                    ft.Card(content=ft.Container(content=enemy_table, padding=10)),
                ])
            )

        # ----------------------------------------------------
        # 【機能4】試合履歴（1戦毎のログ詳細）
        # ----------------------------------------------------
        def build_history_ui():
            history_list_container.controls.clear()
            if self.filtered_df.empty:
                history_list_container.controls.append(ft.Text("対戦データがありません。", color=ft.Colors.GREY_500, italic=True))
                return

            sorted_df = self.filtered_df.sort_values(by='datetime', ascending=False)

            for _, row in sorted_df.iterrows():
                is_win = row['is_win']
                result_text = "WIN" if is_win else "LOSE"
                result_color = ft.Colors.GREEN_400 if is_win else ft.Colors.RED_400
                
                my_chara = self.get_chara_name(row['Chara'])
                our_chara = self.get_chara_name(row['OurChara'])
                e1_chara = self.get_chara_name(row.get('enemy_team.enemy.chara', '不明'))
                e2_chara = self.get_chara_name(row.get('enemy_team.enemy2.chara', '不明'))
                
                stats_rows = [
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("あなた(自分)", color=ft.Colors.BLUE_200, weight="bold")),
                        ft.DataCell(ft.Text(my_chara)),
                        ft.DataCell(ft.Text(f"{row['Damage']:.0f} ({row['my_damage_share']:.1f}%)", weight="bold")),
                        ft.DataCell(ft.Text(f"{row['Kill']} / {row['Death']}")),
                        ft.DataCell(ft.Text(f"{row['LockRate']:.1f}%")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("相方(味方)", color=ft.Colors.BLUE_100)),
                        ft.DataCell(ft.Text(our_chara)),
                        ft.DataCell(ft.Text(f"{row.get('player_team.player2.damage', 0):.0f}")),
                        ft.DataCell(ft.Text(f"{row.get('player_team.player2.kill', 0)} / {row.get('player_team.player2.death', 0)}")),
                        ft.DataCell(ft.Text(f"{row.get('player_team.player2.lock', 0):.1f}%")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("敵1(対面)", color=ft.Colors.RED_200)),
                        ft.DataCell(ft.Text(e1_chara)),
                        ft.DataCell(ft.Text(f"{row.get('enemy_team.enemy.damage', 0):.0f}")),
                        ft.DataCell(ft.Text(f"{row.get('enemy_team.enemy.kill', 0)} / {row.get('enemy_team.enemy.death', 0)}")),
                        ft.DataCell(ft.Text(f"{row.get('enemy_team.enemy.lock', 0):.1f}%")),
                    ]),
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("敵2(対面)", color=ft.Colors.RED_100)),
                        ft.DataCell(ft.Text(e2_chara)),
                        ft.DataCell(ft.Text(f"{row.get('enemy_team.enemy2.damage', 0):.0f}")),
                        ft.DataCell(ft.Text(f"{row.get('enemy_team.enemy2.kill', 0)} / {row.get('enemy_team.enemy2.death', 0)}")),
                        ft.DataCell(ft.Text(f"{row.get('enemy_team.enemy2.lock', 0):.1f}%")),
                    ]),
                ]
                
                details_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("プレイヤー")), ft.DataColumn(ft.Text("使用キャラ")),
                        ft.DataColumn(ft.Text("与ダメージ (シェア)")), ft.DataColumn(ft.Text("K / D")),
                        ft.DataColumn(ft.Text("平均ロック率")),
                    ],
                    rows=stats_rows, heading_row_color=ft.Colors.BLACK26, column_spacing=15
                )

                tile = ft.ExpansionTile(
                    title=ft.Row([
                        ft.Text(result_text, size=15, weight="bold", color=result_color, width=55),
                        ft.Text(f"{my_chara} & {our_chara}", size=14, weight="bold", width=190, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text("vs", size=12, color=ft.Colors.GREY_500, width=30),
                        ft.Text(f"{e1_chara} & {e2_chara}", size=14, weight="bold", expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ]),
                    subtitle=ft.Row([
                        ft.Text(str(row['datetime']), size=11, color=ft.Colors.GREY_400),
                        ft.Text(f"個人スコア: {row['Kill']}K / {row['Death']}D  |  DMG: {row['Damage']:.0f}", size=11, color=ft.Colors.GREY),
                    ], spacing=15),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("▼ 試合詳細フルスタッツ", size=12, color=ft.Colors.BLUE_200, weight="bold"),
                                ft.Container(content=details_table)
                            ], spacing=5),
                            padding=12, bgcolor=ft.Colors.BLACK12, border_radius=8, margin=5
                        )
                    ],
                    text_color=result_color
                )
                history_list_container.controls.append(ft.Card(content=tile, elevation=2))

        # ----------------------------------------------------
        # 初期表示データのビルド
        # ----------------------------------------------------
        build_stats_ui()

        # 各タブのコンテンツ組み立て
        my_chara_tab_content = ft.Column([
            ft.Text("キャラクター別 総合スタッツ", size=14, weight="bold", color=ft.Colors.BLUE_200),
            stats_list_container
        ], scroll=ft.ScrollMode.AUTO)

        enemy_chara_tab_content = ft.Column([
            ft.Container(height=5),
            ft.Text("対戦時の相手チーム内キャラクター採用率（遭遇回数順）", size=14, weight="bold", color=ft.Colors.BLUE_200),
            enemy_list_container
        ], scroll=ft.ScrollMode.AUTO)

        cost_tab_content = ft.Column([
            ft.Container(height=5),
            ft.Text("チームのコスト組み合わせに特化したシナジー・運用分析", size=13, color=ft.Colors.GREY_400),
            ft.Container(height=5),
            cost_list_container
        ], scroll=ft.ScrollMode.AUTO)

        history_tab_content = ft.Column([
            ft.Container(height=5),
            ft.Text("直近の対戦ログ（クリックで試合内の全プレイヤー詳細を展開）", size=13, color=ft.Colors.GREY_400),
            ft.Container(height=5),
            history_list_container
        ], scroll=ft.ScrollMode.AUTO)

        # ----------------------------------------------------
        # タブ切り替え時の遅延読み込み（Lazy Load）処理
        # ----------------------------------------------------
        def on_tab_changed(e):
            idx = self.tabs_container.selected_index
            
            # 既に生成済みのタブなら何もしない
            if self.built_tabs.get(idx, False):
                return
            
            # クリックされたタブに応じて初めて重いUIをビルド
            if idx == 1:
                build_enemy_stats_ui()
            elif idx == 2:
                build_cost_stats_ui()
            elif idx == 3:
                build_history_ui()
            
            # 生成フラグをTrueにして再描画
            self.built_tabs[idx] = True
            self.tabs_container.update()

        # Tabsコントロール
        self.tabs_container = ft.Tabs(
            length=4,
            selected_index=0,
            animation_duration=300,
            expand=True,
            on_change=on_tab_changed,  # イベントをフック
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="マイキャラ軸スタッツ"),
                            ft.Tab(label="対戦相手軸分析"),
                            ft.Tab(label="コスト編成分析"),
                            ft.Tab(label="試合履歴"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            my_chara_tab_content,
                            enemy_chara_tab_content,
                            cost_tab_content,
                            history_tab_content,
                        ],
                    ),
                ],
            ),
        )

        return ft.Container(
            content=ft.Column([
                header, summary_card, ft.Container(height=10), self.tabs_container
            ]),
            padding=15
        )