import flet as ft
import pandas as pd
import os

# キャラクター名の英語IDから日本語へのマッピング辞書
CHARACTER_NAMES = {
    "bolzoi": "ボルゾイ",
    "briker": "ブレイカー",
    "brs": "ブラック★ロックシューター",
    "cammy": "カミ",
    "cati": "カティ",
    "catrina": "カトリーナ",
    "cavary": "カヴァリー",
    "ceilen": "セイレン",
    "celafim": "セラフィム",
    "chinni": "チニ",
    "clysta": "クリスタ",
    "darkstar": "ダークスター",
    "dead_alive": "デッド・オア・アライブ",
    "deadmaster": "デッドマスター",
    "dragner": "ドラグナー",
    "ducarion": "デュカリオン",
    "elfin": "エルフィン",
    "emika": "エミカ",
    "eva": "エヴァ",
    "ezar": "エザル",
    "feed": "フィード",
    "fiby": "フィービィ",
    "frankar": "フランカー",
    "garahad": "ガラハッド",
    "garahad_akatsuki": "ガラハッド・暁",
    "gourai": "轟雷",
    "grifin": "グリフィン",
    "haruka": "ハルカ",
    "hibiki": "ヒビキ",
    "hikari": "ヒカリ",
    "icelin": "アイスリン",
    "ine": "イネ",
    "kage": "カゲ",
    "kaze": "カゼ",
    "kelbim": "ケルビム",
    "line": "リン",
    "mumei": "無名",
    "nora": "ノラ",
    "okid": "オキッド",
    "palas": "パラス",
    "ragel": "レイジェル",
    "ranslot": "ランスロット",
    "reki": "レキ",
    "roland": "ローランド",
    "rota": "ロタ",
    "scopion": "スコーピオン",
    "sharp": "シャープ",
    "signas": "シグナス",
    "skysaber": "スカイセイバー",
    "snowwol": "スノーウルフ",
    "stilet": "スティレット",
    "suzuran": "スズラン",
    "syaolin": "シャオリン",
    "syuu": "シュウ",
    "tachiana": "タチアナ",
    "thanderbolt_otome": "サンダーボルト・乙女",
    "vache": "ヴァーチェ",
    "valkia": "ヴァルキリア",
    "yammn": "ヤマン",
    "zaharowa": "ザハロワ"
}

def get_chara_name(chara_id):
    return CHARACTER_NAMES.get(chara_id, chara_id)

def main(page: ft.Page):
    page.title = "星の翼 - スタッツビューアー"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 900
    page.window_height = 800

    csv_path = "log_202605.csv"

    if not os.path.exists(csv_path):
        page.add(ft.Text(f"エラー: {csv_path} が見つかりません。データログと同じフォルダに配置してください。", color="red", size=16))
        return

    # データの読み込みと加工
    df = pd.read_csv(csv_path)
    df['is_win'] = df['Result'].astype(str).str.lower() == 'win'

    # 総合サマリーの計算
    total_matches = len(df)
    total_wins = df['is_win'].sum()
    total_losses = total_matches - total_wins
    total_win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

    # 画面ヘッダー
    header = ft.Container(
        content=ft.Column([
            ft.Text("星の翼 戦績アナリティクス", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200),
            ft.Text("キャラクター別 & 相方別 詳細スタッツ", size=14, color=ft.colors.GREY_400),
        ]),
        margin=ft.margin.only(bottom=20)
    )

    # サマリーカード
    summary_card = ft.Card(
        content=ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("総試合数", size=12, color=ft.colors.GREY_400), ft.Text(f"{total_matches}", size=24, weight="bold")]),
                ft.Column([ft.Text("勝敗", size=12, color=ft.colors.GREY_400), ft.Text(f"{total_wins}勝 - {total_losses}敗", size=24, weight="bold", color=ft.colors.GREEN_400)]),
                ft.Column([ft.Text("総合勝率", size=12, color=ft.colors.GREY_400), ft.Text(f"{total_win_rate:.1f}%", size=24, weight="bold", color=ft.colors.BLUE_400)]),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            padding=20
        ),
        color=ft.colors.SURFACE_VARIANT
    )

    # アコーディオン（キャラクター別）の作成
    stats_list = ft.Column(spacing=15)
    
    # 自分が使ったキャラ(Chara)ごとにグループ化
    chara_groups = df.groupby('Chara')

    for chara_id, c_df in chara_groups:
        c_matches = len(c_df)
        c_wins = c_df['is_win'].sum()
        c_losses = c_matches - c_wins
        c_win_rate = (c_wins / c_matches * 100)
        c_avg_dmg = c_df['Damage'].mean()
        c_avg_kill = c_df['Kill'].mean()
        c_avg_death = c_df['Death'].mean()

        chara_name_jp = get_chara_name(chara_id)

        # 相方(OurChara)別の集集計用テーブルデータ
        partner_rows = []
        partner_groups = c_df.groupby('OurChara')
        
        # 勝率の高い順に並び替えるためのリスト
        partner_stats_list = []
        for p_id, p_df in partner_groups:
            p_matches = len(p_df)
            p_wins = p_df['is_win'].sum()
            p_losses = p_matches - p_wins
            p_win_rate = (p_wins / p_matches * 100)
            p_avg_dmg = p_df['Damage'].mean()
            p_avg_kill = p_df['Kill'].mean()
            p_avg_death = p_df['Death'].mean()
            
            partner_stats_list.append({
                'id': p_id,
                'name': get_chara_name(p_id),
                'matches': p_matches,
                'win_loss': f"{p_wins}W - {p_losses}L",
                'win_rate': p_win_rate,
                'avg_dmg': p_avg_dmg,
                'avg_kill': p_avg_kill,
                'avg_death': p_avg_death
            })
        
        # 試合数 or 勝率順にソート (ここでは試合数が多い順)
        partner_stats_list.sort(key=lambda x: x['matches'], reverse=True)

        for p in partner_stats_list:
            rate_color = ft.colors.GREEN_400 if p['win_rate'] >= 50 else ft.colors.RED_400
            partner_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p['name'], weight="bold")),
                        ft.DataCell(ft.Text(f"{p['matches']}戦")),
                        ft.DataCell(ft.Text(p['win_loss'])),
                        ft.DataCell(ft.Text(f"{p['win_rate']:.1f}%", color=rate_color, weight="bold")),
                        ft.DataCell(ft.Text(f"{p['avg_dmg']:.0f}")),
                        ft.DataCell(ft.Text(f"{p['avg_kill']:.1f} / {p['avg_death']:.1f}")),
                    ]
                )
            )

        # 相方スタッツを表示するDataTable
        partner_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("相方キャラ")),
                ft.DataColumn(ft.Text("試合数")),
                ft.DataColumn(ft.Text("勝敗")),
                ft.DataColumn(ft.Text("勝率")),
                ft.DataColumn(ft.Text("平均DMG")),
                ft.DataColumn(ft.Text("平均K / D")),
            ],
            rows=partner_rows,
            heading_row_color=ft.colors.BLACK26,
            column_spacing=25
        )

        # アコーディオン(ExpansionTile)の組み立て
        chara_color = ft.colors.BLUE_300 if c_win_rate >= 50 else ft.colors.ORANGE_300
        
        tile = ft.ExpansionTile(
            title=ft.Row([
                ft.Text(chara_name_jp, size=18, weight=ft.FontWeight.BOLD, width=200),
                ft.Text(f"{c_win_rate:.1f}%", size=18, weight="bold", color=chara_color, width=90),
                ft.Text(f"({c_wins}勝 - {c_losses}敗 / 計 {c_matches}戦)", size=14, color=ft.colors.GREY_400),
            ], alignment=ft.MainAxisAlignment.START),
            subtitle=ft.Row([
                ft.Text(f"平均ダメージ: {c_avg_dmg:.0f}", size=12, color=ft.colors.GREY, margin=ft.margin.only(right=15)),
                ft.Text(f"平均K/D: {c_avg_kill:.1f} / {c_avg_death:.1f}", size=12, color=ft.colors.GREY),
            ]),
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("▼ 相方別の詳細相性スタッツ", size=13, color=ft.colors.BLUE_200, weight="bold"),
                        partner_table
                    ], spacing=10),
                    padding=ft.padding.all(15),
                    bgcolor=ft.colors.BLACK12,
                    border_radius=8,
                    margin=ft.margin.all(10)
                )
            ],
            initially_expanded=False,
            collapsed_text_color=ft.colors.WHITE,
            text_color=ft.colors.BLUE_200
        )
        
        stats_list.controls.append(ft.Card(content=tile, elevation=2))

    # ページ全体のレイアウト
    page.add(
        ft.Container(
            content=ft.Column([
                header,
                summary_card,
                ft.Container(height=10),
                ft.Text("キャラクター別スタッツ (クリックで相方別分岐を展開)", size=16, weight="bold"),
                stats_list
            ]),
            padding=20
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
