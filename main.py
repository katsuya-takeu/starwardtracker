
import sys
import os
import time
import threading
import flet as ft
from datetime import datetime, timedelta
from vision_engine import VisionEngine
from main_loop_manager import MainLoopManager
from data_manager import DataManager
from appconfig import AppConfig
from stats_viewer import StatsViewer
from session_chart_manager import SessionChartManager
from pathlib import Path
from profile_manager import ProfileManager

def main(page: ft.Page):
    # アプリ起動時刻を保持 (この時刻以降のデータが「今回のセッション」)
    session_start_time = datetime.now()

    # UI設定 (OBS透過用)
    page.title = "Starward Tracker"
    #page.window.always_on_top = True
    page.window.title_bar_hidden = False        # タイトルバーを消す（推奨）
    # グラフを表示するために高さを広げる (150 -> 400程度)
    page.window.width, page.window.height = 800, 800
    page.window.max_width = 800
    #page.window.bgcolor = ft.Colors.TRANSPARENT
    #page.bgcolor = ft.Colors.TRANSPARENT
    #page.window_bgcolor = ft.Colors.with_opacity(0.01, "black") # 80%の不透明度
    page.padding = 0
    page.update()

    # 実行環境におけるassetsフォルダへのパスを取得
    if getattr(sys, 'frozen', False):
        # ビルド後 (exe実行時)
        # Fletのビルドでは、assetsは通常 exeと同じ階層の "data/flutter_assets/assets" 等に展開されますが、
        # 最も安全なのは sys._MEIPASS (一時展開先) を見ることです。
        base_path = sys._MEIPASS
    else:
        # 開発時：カレントディレクトリ
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    config = AppConfig()
    config.load()
    viewer = StatsViewer(config)

    # グラフを保持するためのコンテナ
    graph_container = ft.Container(expand=True)
    lp_text = ft.Text("Searching Starward...", size=30, weight="bold", color="black")
    diff_text = ft.Text("", size=30, color="orange")
    close_button = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_size=18,
        icon_color="white54",
        # マウスを乗せた時の色（ホバー）
        hover_color=ft.Colors.RED_400,
        # クリック時の動作
        on_click=lambda _: page.run_task(page.window.destroy),
        # ボタンのサイズをコンパクトに
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=0,
        ),
    )
    # 右クリックで実行される関数
    def on_right_click(e: ft.ControlEvent):
        # 設定ダイアログを表示
        # 1. ダイアログをページのオーバーレイ（最前面レイヤー）に登録
        # すでに追加されていてもエラーにはなりません
        if settings_dialog not in page.overlay:
            page.overlay.append(settings_dialog)
        
        # 2. ダイアログを開く
        settings_dialog.open = True
        
        # 3. 反映
        page.update()

    def toggle_display(e):
        state["display_mode"] = (state["display_mode"] + 1) % 2
        update_display()
    page_switch = ft.Button(
        content="change page", 
        on_click=toggle_display
    )

    def profile_changed():
        update_display()
    pm = ProfileManager(page, config, profile_changed)
    # 💡 メイン画面用のドロップダウンをマネージャーから取得
    p_dd = pm.create_dropdown()

    # 💡 編集ボタンのクリックイベントにマネージャーのダイアログ表示関数を紐付ける
    p_edit_button = ft.Button(
        content="", icon=ft.Icons.EDIT, on_click=pm.show_management_dialog
    )

    base_content = ft.Container(
        content=ft.Column([
            #lp_text,
            ft.Row([page_switch, p_dd, p_edit_button]),
            graph_container # ここに後でグラフを入れる
        ], alignment=ft.MainAxisAlignment.CENTER),
        width=page.window.width,
        height=page.window.height,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.01, "black") if config.data["is_transparent"] else ft.Colors.WHITE,
        alignment=ft.Alignment.CENTER,
        padding=10,
        margin=0,
    )
    # これの中にLP表示やグラフなどを入れる
    # 画面全体を覆うGestureDetector
    main_content = ft.GestureDetector(
        content=base_content,
        # 右クリック（セカンダリタップ）検知
        on_secondary_tap=on_right_click,
        expand=True,
    )
    def toggle_transparency(e):
        is_trans = e.control.value # スイッチのTrue/False
        
        if is_trans:
            # 透明モード：背景を透明にする
            #page.window_bgcolor = ft.Colors.TRANSPARENT
            page.bgcolor = ft.Colors.TRANSPARENT
            base_content.bgcolor = ft.Colors.with_opacity(0.01, "black") # コンテンツ側で色調整
        else:
            # 通常モード：背景をしっかりした色にする
            #page.window_bgcolor = ft.Colors.WHITE
            page.bgcolor = ft.Colors.WHITE
            base_content.bgcolor = ft.Colors.WHITE

        # 設定を保存
        config.update("is_transparent", is_trans)
        page.update()

    def toggle_record_all(e):
        is_all = e.control.value # スイッチのTrue/False

        # 設定を保存
        config.update("is_all_record", is_all)
        page.update()
    def toggle_view_data(e):
        is_view = e.control.value # スイッチのTrue/False

        # 設定を保存
        config.update("is_view_data", is_view)
        page.update()
    def toggle_monitor(e):
        is_view = e.control.value # スイッチのTrue/False

        # 設定を保存
        state["is_monitor"] = is_view
        page.update()
    
    # 設定ダイアログの定義
    def close_dlg(e):
        settings_dialog.open = False
        page.update()
    def save_settings(e):
        try:
            # 数値への変換を安全に行う
            state["record_day"] = int(day_field.value) if day_field.value else 0
        except ValueError:
            # 数字以外が入った時の処理
            page.snack_bar = ft.SnackBar(ft.Text("数値は半角数字で入力してください"))
            page.snack_bar.open = True
            page.update()
            return
        
        settings_dialog.open = False
        page.snack_bar = ft.SnackBar(ft.Text("設定を保存しました"))
        page.snack_bar.open = True
        page.update()
    def reset_session(e):
        lp_text.value = ""
        diff_text.value = ""
        graph_container.content = "Reset Session"
        graph_container.update()
        settings_dialog.open = False
        page.update()

    # TextFieldを変数として定義しておく
    day_field = ft.TextField(label="戦績を見る過去日数", value=0, height=40)

    # 設定ダイアログ内のスイッチ
    trans_switch = ft.Switch(
        label="背景を透過する", 
        value=config.data["is_transparent"],
        on_change=toggle_transparency
    )
    record_switch = ft.Switch(
        label="全戦績を見る", 
        value=config.data["is_all_record"],
        on_change=toggle_record_all
    )
    reset_switch = ft.Button(
        content="session reset", 
        on_click=reset_session
    )
    view_data_switch = ft.Switch(
        label="データを常に表示", 
        value=config.data["is_view_data"],
        height=40,
        on_change=toggle_view_data
    )
    monitor_switch = ft.Switch(
        label="データを監視", 
        value=True,
        height=40,
        on_change=toggle_monitor
    )
    if not config.data["save_path"]:config.update("save_path", os.path.join(base_path, "match_log"))
    current_save_path = ft.Text(f"現在の保存先: {config.data['save_path']}")

    async def handle_get_directory_path(e: ft.Event[ft.Button]):
        path = await ft.FilePicker().get_directory_path()
        if path:
            config.update("save_path", path)
            current_save_path.value = f"現在の保存先: {path}"
            current_save_path.update()

    settings_dialog = ft.AlertDialog(
        title=ft.Row([
            ft.Text("詳細設定", size=25),
            ft.Text("ver 1.0.0", size=15, color=ft.Colors.GREY_500) # ここに追加
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        content=ft.Column([
            #day_field,
            #view_data_switch,
            #record_switch,
            #trans_switch,
            monitor_switch,
            #reset_switch,
            ft.Button(
                "保存フォルダを変更する",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=handle_get_directory_path,
            ),
            current_save_path
        ], tight=True),
        actions=[
            #ft.TextButton("キャンセル", on_click=close_dlg),
            ft.TextButton("保存", on_click=save_settings), # ここにconfig.updateを書く
        ],
    )

    page.add(main_content)
    chart = SessionChartManager()
    chart_container = chart.build_ui()

    def update_display():
        #print(f"Clicked! {state["display_mode"]}")
        if state["display_mode"] == 0:
            graph_container.content = chart_container
            p_edit_button.visible = True
        elif state["display_mode"] == 1:
            # セッション履歴表を表示
            graph_container.content = viewer.get_view()
            p_edit_button.visible = False
        #elif state["display_mode"] == 2:
            # キャラ別勝率を表示
            #graph_container.content = viewer.get_win_rate_by_chara(config.data["last_chara"], config.data["last_operate"], session_start_time, state["record_day"])
        #elif state["display_mode"] == 3:
            # キャラ別勝率を表示
            #graph_container.content = viewer.build_stats_view(config.data["last_chara"], config.data["last_operate"], session_start_time, state["record_day"])
        graph_container.content.expand = True
        graph_container.update()
        page.update()

    #graph_container.on_click = toggle_display
    #graph_container.mouse_cursor = ft.MouseCursor.CLICK
    graph_container.content = chart_container

    # Tesseractのパス指定例
    tesseract_exe = os.path.join(base_path, "assets", "tesseract", "tesseract.exe")

    data_manager = DataManager(config)
    engine = VisionEngine(data_manager, tesseract_exe, base_path)

    state = {
        #"is_debug": True,
        "is_debug": False,
        "is_monitor": True,
        "record_day": 0,
        "display_mode": 0,  # 0: グラフ, 1: 履歴, 2: 勝率
    }

    def monitor_loop():
        confirm_count = 0
        mismatch_count = 0
        last_check_time = time.time()  # 名前確認用のタイマー
        last_ocr_time = time.time()
        last_rect_check = 0
        cached_rect = engine.get_game_rect()
        if state["is_debug"]: cached_rect = [0, 0, 1920, 1080]
        # サイズ変更時
        #page.on_resize = on_window_event
        # 移動時
        #page.on_move = on_window_event
        
        last_log = {}
        if cached_rect:
            engine.resize_templete(cached_rect)
        manager = MainLoopManager(engine, data_manager, chart, cached_rect)
        while True:
            if not state["is_monitor"]:
                time.sleep(5)
                continue
            if cached_rect is None:
                cached_rect = engine.get_game_rect()
                time.sleep(1)
                continue
            engine.update_capture_full(cached_rect)
            if not engine.is_capture_success():
                time.sleep(0.1)
                continue
            if manager.update():
                graph_container.update()
                page.update()

    threading.Thread(target=monitor_loop, daemon=True).start()

ft.app(target=main)
    