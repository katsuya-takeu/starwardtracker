
import time
from datetime import datetime, timedelta
from vision_engine import VisionEngine
from data_manager import DataManager
from collections import Counter
from session_chart_manager import SessionChartManager

"""
0:マップ取得まで
1:キャラ取得まで
2:ゲーム開始　ジャンプ
3:非戦闘状態
4:戦闘状態
5:リスボーン待機
6:リザルト
"""
class LoopState:
    def __init__(self):
        self.STATE_INIT = 0
        self.STATE_MENU = 1
        self.STATE_MATCHING = 2
        self.STATE_MATCH_CHARA = 3
        self.STATE_MATCH = 4
        self.STATE_RESULT_EFFECT = 5
        self.STATE_RESULT = 6
        self.STATE_DEBUG = 10

class MainLoopManager:
    def __init__(self, vision_engine:VisionEngine, data_manager, chart:SessionChartManager, rect):
        self.state = 0
        self.engine:VisionEngine = vision_engine
        self.rect = rect
        self.data_manager:DataManager = data_manager
        self.chart:SessionChartManager = chart
        self.map = ""
        self.loop_state = LoopState()
        self.readings = []
        self.is_page_update = False

        return
        self.state = self.loop_state.STATE_DEBUG

    def update(self):
        start_time = time.time()
        wait = 0.5
        if True:
            if self.state == self.loop_state.STATE_MATCH\
                or self.state == self.loop_state.STATE_RESULT:\
                #or self.state == self.loop_state.STATE_MATCH_BATTLE:  #
                wait = 1
            #開始前の画面でmapがどれか判断
            match self.state:
                case self.loop_state.STATE_INIT:#マップ取得まで
                    wait = 1
                    self.state = self.loop_state.STATE_MENU

                case self.loop_state.STATE_MENU:#マップ取得まで
                    wait = 1
                    self.is_rank = self.engine.get_match_start()
                    if self.is_rank:
                        self.state = self.loop_state.STATE_MATCHING
                    
                case self.loop_state.STATE_MATCHING:  # ゲーム開始　ジャンプ
                    wait = 1
                    is_match = self.engine.get_player_side()
                    #rank = self.engine.get_rank_point()
                    if is_match:
                        self.state = self.loop_state.STATE_MATCH_CHARA
                        
                        print('matching end')

                case self.loop_state.STATE_MATCH_CHARA:#キャラ表示
                    #print(f'')
                    wait = 0.8
                    rank = self.engine.get_rank_point()
                    print(f'rank_point:{rank}')
                    confirm = self.confirm_rank_point(rank)
                    if confirm > 0:
                        self.readings = []
                        self.data_manager.save_rank(rank)
                        self.state = self.loop_state.STATE_MATCH
                        self.update_chart(rank)
                        print(f'rank:{rank}')

                case self.loop_state.STATE_MATCH:#戦闘状態
                    wait = 1
                    match_result = self.engine.get_match_result()
                    if match_result != "":
                        self.data_manager.save_match_result(match_result)
                        self.state = self.loop_state.STATE_RESULT_EFFECT
                        self.engine.capture_game_area_from_cache(datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"result.png", 0, 0, 1, 1)
                        
                        print(f'match end {match_result}')
                        self.update_chart_result(match_result)
                        wait = 8
                case self.loop_state.STATE_RESULT_EFFECT:#リザルト
                    #print(f'')
                    wait = 0.5
                    result = self.engine.is_result()
                    if result:
                        wait = 0
                        self.state = self.loop_state.STATE_RESULT
                        print('result start')
                case self.loop_state.STATE_RESULT:#リザルト
                    #print(f'')
                    wait = 0.5
                    result = self.engine.get_result()
                    if result:
                        self.state = self.loop_state.STATE_MENU
                        print('result end')
                case self.loop_state.STATE_DEBUG:#
                    wait = 1
                    #point = self.engine.get_player_side()
                    
                    match_result = self.engine.get_result()

                    #print(f'point:{point}')

                #case _:
        elif menu.upper() == "RESULT":
            if self.engine.get_end() == "end":
                #gameset
                self.data_manager.save_game_end(self.total_move, self.weapon_history, self.heal_history)
                
                self.total_move = 0
                self.heal_history = {}
                self.weapon_history = {}
                self.state = self.loop_state.STATE_MAP
                print('end match')
        

        elapsed = time.time() - start_time
        wait_time = max(0, wait - elapsed) 
        time.sleep(wait_time)

        if self.is_page_update:
            self.is_page_update = False
            return True
        else:
            return False

    def confirm_rank_point(self, rank):
        if rank < 0 or rank >= 100000:
            return -1
        
        self.readings.append(rank)
        
        if len(self.readings) > 5:
            self.readings.pop(0)
        
        counts = Counter(self.readings)
        most_common_val, count = counts.most_common(1)[0]
        
        if count >= 3:
            return most_common_val
        
        return -1
    
    def update_chart(self, current_rp):
        # 1. グラフのスタート地点がまだ決まっていなければ（本当に最初の1回目）
        if self.chart.start_point is None:
            self.chart.set_initial_point(current_rp)
            return

        self.chart.add_match_trigger(current_rp)

    def update_chart_result(self, result):
        self.chart.add_match_result(result)