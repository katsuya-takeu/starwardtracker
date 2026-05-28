import os
from datetime import datetime
from pathlib import Path
import flet as ft


class ProfileManager:

    def __init__(self, page: ft.Page, config, on_profile_changed_callback):
        self.page = page
        self.config = config
        # プロファイルが切り替わったり、削除されたりした時にメイン側（グラフやViewer）を再描画するためのコールバック関数
        self.on_profile_changed_callback = on_profile_changed_callback

        # メンバ変数としてUIパーツを保持（後から値をクリアしたり参照したりするため）
        self.add_field = ft.TextField(label="追加するプロファイル名", value="", height=40)
        self.dropdown = None
        self.dialog_dropdown = None
        self.dialog = None

    def get_log_dir(self) -> Path:
        """現在の保存先パスをPathオブジェクトで返します。"""
        return Path(self.config.data.get("save_path", "match_log"))

    def create_dropdown(self, width=200) -> ft.Dropdown:
        """メイン画面などに置く、プロファイル切り替え用のドロップダウンを生成します。"""
        profile = self.config.data.get("profile", "default")
        profile_list = self.config.data.get("profile_list", ["default"])

        self.dropdown = ft.Dropdown(
            label="プロファイル",
            width=width,
            options=[ft.dropdown.Option(p) for p in profile_list],
            value=profile,
            height=40,
            on_select=self._on_dropdown_changed,  # 値が変わった時のイベント
        )
        return self.dropdown

    def _on_dropdown_changed(self, e):
        try:
            """ドロップダウンの選択が変更された時の処理"""
            new_profile = e.control.value
            self.config.update("profile", new_profile)
            # メイン側に通知して画面をリフレッシュしてもらう
            self.on_profile_changed_callback()
        except Exception as ex:
            # ⚠️ ここで PermissionError などのログが出れば確定です
            print(f"🚨 プロファイル変更中にエラーが発生しました: {ex}")

    def show_management_dialog(self, e):
        """プロファイル管理（追加・削除）のダイアログを表示します。"""
        profile_list = self.config.data.get("profile_list", ["default"])

        # ダイアログ内の削除用ドロップダウン
        self.dialog_dropdown = ft.Dropdown(
            label="削除するプロファイル",
            width=200,
            options=[ft.dropdown.Option(p) for p in profile_list],
            value="",
            height=40,
        )

        dialog = ft.AlertDialog(
            title=ft.Row(
                [ft.Text("プロファイル管理", size=25)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self.add_field,
                            ft.Button(
                                "追加",
                                icon=ft.Icons.ADD_CARD,
                                on_click=self._add_profile,
                            ),
                        ]
                    ),
                    ft.Container(height=30),
                    ft.Text(
                        "削除の操作は十分に注意の上行ってください",
                        color=ft.Colors.RED_500,
                    ),
                    ft.Row(
                        [
                            self.dialog_dropdown,
                            ft.Button(
                                "削除",
                                icon=ft.Icons.DELETE,
                                color=ft.Colors.RED_400,
                                on_click=self._delete_profile,  # 💡 バグを修正（lambdaではなくメソッドを指定）
                            ),
                        ]
                    ),
                ],
                tight=True,
            ),
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        self.dialog = dialog

    def _add_profile(self, e):
        """プロファイルを追加する処理"""
        name = self.add_field.value.strip()
        if not name:
            return

        p_list = self.config.data.get("profile_list", [])
        if name in p_list:
            return  # 重複は無視

        # 実際のフォルダを作成
        try:
            profile_dir = self.get_log_dir() / name
            profile_dir.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            print(f"フォルダ作成失敗: {ex}")
            return

        # 設定を更新
        p_list.append(name)
        self.config.update("profile_list", p_list)

        # UIの更新
        self.add_field.value = ""
        self._refresh_all_dropdowns()

        # ダイアログを閉じる
        self._close_dialog()
        self.page.pop_dialog()
        self.page.update()
        self.on_profile_changed_callback()

    def _delete_profile(self, e):
        """プロファイルを削除（論理削除）する処理"""
        target = self.dialog_dropdown.value
        if not target:
            return

        p_list = self.config.data.get("profile_list", [])

        # フォルダのリネーム（論理削除）
        success = self._trash_profile_folder(target)
        if success:
            if target in p_list:
                p_list.remove(target)

            # もし空になったらdefaultを作る
            if len(p_list) == 0:
                p_list.append("default")

            # 現在選択中のプロファイルが削除されたら、別のプロファイルに切り替える
            if self.config.data.get("profile") == target:
                self.config.update("profile", p_list[0])

            self.config.update("profile_list", p_list)

            # UIの更新
            self._close_dialog()
            self._refresh_all_dropdowns()
            self.page.pop_dialog()
            self.page.update()
            self.on_profile_changed_callback()
        else:
            # エラー通知
            self.page.dialog = ft.AlertDialog(
                title=ft.Text("削除に失敗しました"),
                content=ft.Text(
                    f"プロファイル『{target}』のログファイルが他のソフトで開かれている可能性があります。"
                ),
                actions=[
                    ft.TextButton(
                        "OK", on_click=lambda _: self.page.pop_dialog()
                    )
                ],
            )
            self.page.dialog.open = True
            self.page.update()

    def _refresh_all_dropdowns(self):
        """管理内にあるドロップダウンの選択肢を一斉に最新化します。"""
        p_list = self.config.data.get("profile_list", ["default"])
        current_p = self.config.data.get("profile", "default")

        options = [ft.dropdown.Option(p) for p in p_list]

        if self.dropdown:
            self.dropdown.options = options
            self.dropdown.value = current_p
            self.dropdown.update()

    def _trash_profile_folder(self, profile_name: str) -> bool:
        """フォルダを _trash_ 補正名にリネームします。"""
        old_folder = self.get_log_dir() / profile_name
        if not old_folder.exists() or not old_folder.is_dir():
            return True

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_folder_name = f"_trash_{profile_name}_{timestamp}"
            new_folder = old_folder.with_name(new_folder_name)
            old_folder.rename(new_folder)
            return True
        except Exception as e:
            print(f"❌ リネームエラー: {e}")
            return False
        
    def _close_dialog(self):
        if self.dialog:
            self.dialog.open = False