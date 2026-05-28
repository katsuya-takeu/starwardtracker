import flet as ft
import flet_charts as fch

class SessionChartManager:
    def __init__(self): # jsonlの最終行の数値を想定
        self.start_point = None
        
        # 内部管理用のリスト（差分計算やサマリー用）
        self.points_history = []
        self.results_history = []  # "win" または "lose" を溜める

        # Fletコントロールの参照用
        self.chart = None
        self.chart_data = None
        self.text_summary = None

    def build_ui(self):
        """初期状態の空のグラフUIを組み立てる"""
        # 最初はデータポイントを空にしておく
        self.chart_data = fch.LineChartData(
            points=[],
            stroke_width=3,
            color=ft.Colors.BLUE_400,
            curved=True,
            #point_shape=ft.ChartPointShape.CIRCLE,
            below_line_gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[ft.Colors.with_opacity(0.15, ft.Colors.BLUE_400), ft.Colors.TRANSPARENT],
            ),
        )
        self.label = fch.ChartAxisLabel(
            value=0,
            label=ft.Text("0", size=50, weight=ft.FontWeight.BOLD),
        )
        self.chart = fch.LineChart(
            data_series=[self.chart_data],
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
            horizontal_grid_lines=fch.ChartGridLines(
                interval=100,
                color=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE)
            ),
            left_axis=fch.ChartAxis(label_spacing=100),
            interactive=True,
            expand=True,
        )
        
        self.text_summary = ft.Text("本日のセッション: マッチ画面待ち...", size=13, color=ft.Colors.GREY_400)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📈 リアルタイム・セッション推移", size=16, weight="bold", color=ft.Colors.BLUE_200),
                    self.text_summary
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(content=self.chart, height=300, padding=50)
            ]),
            padding=15,
            bgcolor=ft.Colors.SURFACE_BRIGHT,
            border_radius=8
        )
    
    def set_initial_point(self, current_rp):
        """【1試合目のマッチ画面】でのみ呼ばれる初期化処理"""
        self.start_point = current_rp
        self.points_history.append(current_rp)
        
        # グラフに「0戦目」として最初の点を打つ
        self.chart_data.points.append(
            fch.LineChartDataPoint(x=0, y=current_rp, tooltip=f"セッション開始時\n{current_rp} pt")
        )
        self.text_summary.value = f"セッション開始: {current_rp} pt"
        
        if self.chart and self.chart.page:
            self.chart.update()
            self.text_summary.update()

    def add_match_trigger(self, current_rp: int):
        """試合終了時に、メモリとグラフをダイレクトに超高速更新する"""
        if len(self.results_history) == 0:
            self.set_initial_point(current_rp)
            return
        
        # 1. 変動値を計算（直前のポイントとの差分）
        prev_rp = self.points_history[-1]
        diff = current_rp - prev_rp
        result = self.results_history[-1]
        
        # 2. 履歴リストに追記
        self.points_history.append(current_rp)
        
        match_count = len(self.results_history)
        
        # 3. ツールチップに表示したいテキストをその場で作成（改行「\n」も使えます）
        res_color = "🟢" if result.lower() == "win" else "🔴"
        tooltip_str = (
            f"{match_count}戦目 ({res_color} {result.upper()})\n"
            f"現在のRP: {current_rp} pt\n"
            f"今回変動: {diff:+d} pt"
        )
        
        # 4. ★ポイント：LineChartDataPointに直接 tooltip 文字列を持たせて追加するだけ！
        self.chart_data.points.append(
            fch.LineChartDataPoint(x=match_count, y=current_rp, tooltip=tooltip_str)
        )
        
        # 5. サマリーテキストの更新
        wins = self.results_history.count("win")
        losses = match_count - wins
        win_rate = (wins / match_count * 100) if match_count > 0 else 0
        total_session_diff = current_rp - self.start_point
        
        self.text_summary.value = (
            f"{match_count}戦 {wins}勝 {losses}敗 (勝率 {win_rate:.1f}%) | "
            f"セッション増減: {total_session_diff:+} pt"
        )

        self.label = fch.ChartAxisLabel(
            value=current_rp,
            label=ft.Text(str(current_rp), size=30, weight=ft.FontWeight.BOLD),
        )
        
        # 6. FletのUIを部分更新
        if self.chart and self.chart.page:
            self.chart.update()
            self.text_summary.update()
            self.chart.page.update()

    def add_match_result(self, result: str):
        """試合終了時に、更新する"""
        
        # 1. 変動値を計算（直前のポイントとの差分）
        prev_rp = self.points_history[-1]
        
        # 2. 履歴リストに追記
        self.results_history.append(result.lower())
        
        match_count = len(self.results_history)
        
        # 3. ツールチップに表示したいテキストをその場で作成（改行「\n」も使えます）
        res_color = "🟢" if result.lower() == "win" else "🔴"
        tooltip_str = (
            f"{match_count}戦目 ({res_color} {result.upper()})\n"
            f"現在のRP: {prev_rp} pt\n"
        )
        
        # 5. サマリーテキストの更新
        wins = self.results_history.count("win")
        losses = match_count - wins
        win_rate = (wins / match_count * 100) if match_count > 0 else 0
        total_session_diff = prev_rp - self.start_point
        
        self.text_summary.value = (
            f"{match_count}戦 {wins}勝 {losses}敗 (勝率 {win_rate:.1f}%) | "
            f"セッション増減: {total_session_diff:+} pt"
        )
        
        # 6. FletのUIを部分更新
        if self.chart and self.chart.page:
            self.chart.update()
            self.text_summary.update()
            self.chart.page.update()
