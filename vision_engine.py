import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import pygetwindow as gw
import mss
from collections import Counter
import os
import re
from data_manager import DataManager

class VisionEngine:
    def __init__(self, data_manager:DataManager, tesseract_path, base_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.data_m:DataManager = data_manager
        
        self.map_path = os.path.join(base_path, "assets", "map")
        chara_name_path = os.path.join(base_path, "assets", "chara_name")
        #chara_icon_path = os.path.join(base_path, "assets", "chara_icon")
        menu_path = os.path.join(base_path, "assets", "menu")
        match_path = os.path.join(base_path, "assets", "match")
        result_num_path = os.path.join(base_path, "assets", "result_num")
        rank_num_path = os.path.join(base_path, "assets", "rank_num")
        cost_path = os.path.join(base_path, "assets", "cost")
        # テンプレート読み込み（文字だけ切り抜いたもの）
        self.base_w, self.base_h = 1920, 1080
        self.chara_name_templates = {}
        #self.chara_icon_templates = {}
        self.menu_templates = {}
        self.match_templates = {}
        self.result_num_templates = {}
        self.rank_num_templates = {}
        self.cost_templates = {}
        self.vision_rario = 1.0
        # 起動時に一括でメモリへ読み込む
        self._load_icon_templates(chara_name_path, self.chara_name_templates)
        #self._load_icon_templates(chara_icon_path, self.chara_icon_templates)
        self._load_icon_templates(match_path, self.match_templates)
        self._load_icon_templates(menu_path, self.menu_templates)
        self._load_icon_templates(result_num_path, self.result_num_templates, True, 3.0)
        self._load_icon_templates(rank_num_path, self.rank_num_templates, True, 3.0)
        self._load_icon_templates(cost_path, self.cost_templates, True)

        self.chara_list = {}
        self.pos = -1

    def _load_icon_templates(self, directory, icon_list, is_ = False, resize = 1.0, is_digit_only = True):
        if not os.path.exists(directory):
            print(f"警告: {directory} が見つかりません。")
            return

        for filename in os.listdir(directory):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                # ファイル名から取得
                char_name = os.path.splitext(filename)[0]
                
                # 画像を読み込んで辞書に保存
                path = os.path.join(directory, filename)
                img = cv2.imread(path) # 照合用に白黒で読み込む
                # 3. 【新兵器】Cannyエッジ検出 (形だけを抽出)
                # これにより背景の暗さや派手な色に左右されなくなります
                # 閾値は50/150程度が安定します
                #img = cv2.Canny(img, 100, 200)
                if is_:
                    gray_item = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    if resize > 1.0:
                        scale_factor = resize
                        width = int(gray_item.shape[1] * scale_factor)
                        height = int(gray_item.shape[0] * scale_factor)
                        gray_item = cv2.resize(gray_item, (width, height), interpolation=cv2.INTER_CUBIC)
                    _, img = cv2.threshold(gray_item, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                if img is not None:
                    has_digit = any(char.isdigit() for char in char_name)
                    if has_digit and is_digit_only:char_name = re.sub(r"\D", "", char_name)
                    icon_list[char_name] = img
                    print(f"Loaded: {char_name}")

    def resize_templete(self, rect):

        resized = {}
        # ウィンドウサイズがどうあれ、常に「高さ1080相当」の密度に直す
        ratio = 1080 / rect[3] 
        if self.vision_rario == ratio:
            return
        self.vision_rario = ratio
    
    def get_game_rect(self):
        """ウィンドウ座標を取得"""
        wins = gw.getWindowsWithTitle('星之翼')
        if wins and not wins[0].isMinimized:
            win = wins[0]
            return (win.left, win.top, win.width, win.height)
        return None

    def capture_game_area(self, rect, rel_x, rel_y, rel_w, rel_h):
        win_x, win_y, win_w, win_h = rect
        
        # スレッドごとに個別のインスタンスを使用する（エラー回避）
        with mss.mss() as sct:
            monitor = {
                "top": win_y + int(win_h * rel_y),
                "left": win_x + int(win_w * rel_x),
                "width": int(win_w * rel_w),
                "height": int(win_h * rel_h)
            }
            try:
                # キャプチャ実行
                sct_img = sct.grab(monitor)
                # 変換
                img_cv = np.array(sct_img)
                # capture_sf6_area の return 直前に追加
                #cv2.imwrite("debug_last_capture.png", img_cv)
            except mss.exception.ScreenShotError:
                # ゲームが最小化されている時や、画面ロック時にここに来る
                #print("画面キャプチャに失敗しました。再試行します...")
                return None
            
            return cv2.cvtColor(img_cv, cv2.COLOR_BGRA2BGR)
        
    def is_capture_success(self):
        return self.full_img is not None
    
    def update_capture_full(self, rect):
        if rect :
            self.full_img = self.capture_game_area(rect, 0, 0, 1.0, 1.0)
        
    def get_area_from_cache(self, x_rel, y_rel, w_rel, h_rel):
        """
        update_capture_fullで更新されたself.full_imgから
        指定範囲を切り出すだけの超軽量メソッド
        """
        if self.full_img is None: return None
        h, w = self.full_img.shape[:2]
        x1, y1 = int(w * x_rel), int(h * y_rel)
        x2, y2 = int(w * (x_rel + w_rel)), int(h * (y_rel + h_rel))
        return self.full_img[y1:y2, x1:x2] # OpenCVのクロップは一瞬
    
    def capture_game_area_from_cache(self, name, rel_x, rel_y, rel_w, rel_h):
        img = self.get_area_from_cache(rel_x, rel_y, rel_w, rel_h)
        cv2.imwrite(name, img)

    def get_point(self):
        img = self.get_area_from_cache(0.88, 0.1, 0.1, 0.05)
        #cv2.imwrite("debug_point.png", img)

    def get_match_mode(self):
        img = self.get_area_from_cache(0.8, 0.7, 0.2, 0.1)
        #cv2.imwrite("debug_match_mode.png", img)
        res = cv2.matchTemplate(img, self.menu_templates["mode_rank"], cv2.TM_CCOEFF_NORMED)
        _, val, _, pos = cv2.minMaxLoc(res)
        return val > 0.6
    
    def get_match_start(self):
        img = self.get_area_from_cache(0.4, 0.4, 0.2, 0.2)
        #cv2.imwrite("debug_match_mode.png", img)
        res = cv2.matchTemplate(img, self.menu_templates["match_start"], cv2.TM_CCOEFF_NORMED)
        _, val, _, pos = cv2.minMaxLoc(res)
        return val > 0.6

    def get_player_side(self):
        player_pos = {}
        img1 = self.get_area_from_cache(0, 0.35, 0.2, 0.035)
        player_pos[0] = self.get_player_val(img1)
        #cv2.imwrite("debug_player_side.png", img1)
        img2 = self.get_area_from_cache(0, 0.82, 0.2, 0.035)
        player_pos[1] = self.get_player_val(img2)
        #cv2.imwrite("debug_player_side2.png", img2)
        img3 = self.get_area_from_cache(0.8, 0.35, 0.2, 0.035)
        player_pos[2] = self.get_player_val(img3)
        #cv2.imwrite("debug_player_side3.png", img3)
        img4 = self.get_area_from_cache(0.8, 0.82, 0.2, 0.035)
        player_pos[3] = self.get_player_val(img4)
        #cv2.imwrite("debug_player_side4.png", img4)
        pos = max(player_pos, key=player_pos.get)

        # 安全対策：もし全部のエリアが「0（黄色なし）」だった場合の処理
        # 背景の誤判定を防ぐため、最大値がある程度の閾値（例: 50ピクセル）を超えているかチェックすると確実です
        if player_pos[pos] == 0:
            return None
        
        chara_list = self.get_chara_name_list()
        result_list = []
        match pos:
            case 0:
                result_list = [chara_list[pos], chara_list[1], chara_list[2], chara_list[3]]
            case 1:
                result_list = [chara_list[pos], chara_list[0], chara_list[2], chara_list[3]]
            case 2:
                result_list = [chara_list[pos], chara_list[3], chara_list[0], chara_list[1]]
            case 3:
                result_list = [chara_list[pos], chara_list[2], chara_list[0], chara_list[1]]
        self.data_m.save_match_metadata(pos, result_list)
        self.chara_list = chara_list
        self.pos = pos
        return True

    def get_player_val(self, img):
        # 1. 画像を読み込む
        if img is None:
            return 0

        # 2. RGBからHSV色空間に変換（色の判別がしやすくなる）
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 3. 黄色の範囲を定義 (HSV)
        # 黄色はH(色相)が15〜30付近。S(彩度)とV(明度)を高めにして背景のノイズを防ぐ
        lower_yellow = np.array([15, 100, 100])
        upper_yellow = np.array([35, 255, 255])

        # 4. 画像内から黄色のピクセルだけを抽出するマスクを作成
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # 5. 黄色と判定されたピクセルの数を数える
        yellow_pixel_count = cv2.countNonZero(yellow_mask)

        return yellow_pixel_count


    def get_chara_name_list(self):
        chara_name_list = {}
        img1 = self.get_area_from_cache(0, 0.39, 0.2, 0.05)
        
        chara_name_list[0] = self.get_chara(img1, 0)
        #cimg1 = self.get_area_from_cache(0.22, 0.39, 0.1, 0.05)
        #cv2.imwrite("debug_chara_name.png", img1)
        #cv2.imwrite("debug_chara_name1.png", cimg1)
        img2 = self.get_area_from_cache(0, 0.865, 0.2, 0.05)
        #cimg2 = self.get_area_from_cache(0.22, 0.865, 0.1, 0.05)
        chara_name_list[1] = self.get_chara(img2, 1)
        #cv2.imwrite("debug_chara_name2.png", img2)
        #cv2.imwrite("debug_chara_name2.png", cimg2)
        img3 = self.get_area_from_cache(0.8, 0.39, 0.2, 0.05)
        #cimg3 = self.get_area_from_cache(0.68, 0.39, 0.1, 0.05)
        chara_name_list[2] = self.get_chara(img3, 2)
        #cv2.imwrite("debug_chara_name3.png", img3)
        #cv2.imwrite("debug_chara_name3.png", cimg3)
        img4 = self.get_area_from_cache(0.8, 0.865, 0.2, 0.05)
        #cimg4 = self.get_area_from_cache(0.68, 0.865, 0.1, 0.05)
        chara_name_list[3] = self.get_chara(img4, 3)
        #cv2.imwrite("debug_chara_name4.png", cimg4)
        #cv2.imwrite("debug_chara_name4.png", img4)
        
        return chara_name_list
    
    def get_match_rank_point(self):
        img = self.get_area_from_cache(0.8, 0.1, 0.18, 0.05)
        #cv2.imwrite("debug_match_rank_pointp.png", img)
        gray_item = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, img = cv2.threshold(gray_item, 200, 255, cv2.THRESH_BINARY)
        #cv2.imwrite("debug_match_rank_point_.png", img)
        #for name, tmp in self.rank_num_templates.items():
            #cv2.imwrite(f"debug_match_rank_point_{name}.png", tmp)
        return self.recognize_centered_number_strict(img, self.rank_num_templates, -1)
    
    def get_rank_point(self):
        #img1 = self.get_area_from_cache(0.07, 0.02, 0.1, 0.05)
        #cv2.imwrite("debug_rp.png", img1)
        #img2 = self.get_area_from_cache(0.07, 0.5, 0.1, 0.05)
        #cv2.imwrite("debug_rp2.png", img2)
        #img3 = self.get_area_from_cache(0.83, 0.02, 0.1, 0.05)
        #cv2.imwrite("debug_rp3.png", img3)
        #img4 = self.get_area_from_cache(0.83, 0.5, 0.1, 0.05)
        #cv2.imwrite("debug_rp4.png", img4)
        pos = self.data_m.get_pos()
        if pos < 0:
            return -1
        pos_list = [(0.07, 0.02, 0.1, 0.05),
                    (0.07, 0.5, 0.1, 0.05),
                    (0.83, 0.02, 0.1, 0.05),
                    (0.83, 0.5, 0.1, 0.05)]
        
        img = self.get_area_from_cache(pos_list[pos][0], pos_list[pos][1], pos_list[pos][2], pos_list[pos][3])
        #for name, tmp in self.rank_num_templates.items():
            #cv2.imwrite(f"debug_match_rank_point_{name}.png", tmp)
        #cv2.imwrite("debug_rp.png", img)
        gray_item = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        scale_factor = 3.0
        width = int(gray_item.shape[1] * scale_factor)
        height = int(gray_item.shape[0] * scale_factor)
        gray_item = cv2.resize(gray_item, (width, height), interpolation=cv2.INTER_CUBIC)
        _, img = cv2.threshold(gray_item, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        #cv2.imwrite("debug_rp_th.png", img)
        return self.recognize_centered_number_strict(img, self.rank_num_templates, -1)
        

    def get_chara(self, img, pos):
        h, w = img.shape[:2]
        #cv2.imwrite('debug_ult.jpg', ult)

        # 最も似ている場所を探す
        max_val, max_name = -1, ""

        for name, template in self.chara_name_templates.items():
            # アイコンを探す（閾値は少し高めの0.8〜0.9がおすすめ）
            res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)

            if val > max_val:
                max_name = name
                max_val = val

            if val > 0.8:
                break
        #print(f'name:{max_name} val:{max_val}')

        pos_list = [(0.22, 0.39, 0.1, 0.05),
                    (0.22, 0.865, 0.1, 0.05),
                    (0.68, 0.39, 0.1, 0.05),
                    (0.68, 0.865, 0.1, 0.05)]
        if max_name == "beta" and 0 <= pos <= 3:
            img = self.get_area_from_cache(pos_list[pos][0], pos_list[pos][1], pos_list[pos][2], pos_list[pos][3])
            #for name, tmp in self.rank_num_templates.items():
                #cv2.imwrite(f"debug_match_rank_point_{name}.png", tmp)
            #cv2.imwrite("debug_rp.png", img)
            gray_item = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, img = cv2.threshold(gray_item, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            cname, c_val = "", -1
            for name, template in self.cost_templates.items():
                # アイコンを探す（閾値は少し高めの0.8〜0.9がおすすめ）
                res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                _, val, _, _ = cv2.minMaxLoc(res)

                if val > c_val:
                    cname = name
                    c_val = val

                if val > 0.8:
                    break
            if cname == "30":
                max_name = "Rbeta"
        
        return max_name if max_val > 0.55 else ""
    
    def get_match_result(self):
        img = self.get_area_from_cache(0.25, 0.3, 0.5, 0.4)
        #cv2.imwrite("debug_result_allow.png", img)
        max_name, max_val = "", -1
        templetes = {"win":self.match_templates["win"], "lose":self.match_templates["lose"]}
        for name, template in templetes.items():
            # アイコンを探す（閾値は少し高めの0.8〜0.9がおすすめ）
            res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)

            if val > max_val:
                max_name = name
                max_val = val

            if val > 0.8:
                break
        #print(f'name:{max_name} val:{max_val}')
        
        return max_name if max_val > 0.55 else ""
    
    def is_result(self):
        img = self.get_area_from_cache(0, 0, 0.5, 0.2)
        #cv2.imwrite("debug_result_allow.png", img)
        max_name, max_val = "", -1
        templetes = {"result_win":self.match_templates["result_win"], "result_lose":self.match_templates["result_lose"]}
        for name, template in templetes.items():
            # アイコンを探す（閾値は少し高めの0.8〜0.9がおすすめ）
            res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)

            if val > max_val:
                max_name = name
                max_val = val

            if val > 0.8:
                break
        #print(f'name:{max_name} val:{max_val}')
        
        result = max_name if max_val > 0.6 else ""
        return result in ("result_win", "result_lose")
    
    def get_result(self):
        img = self.get_area_from_cache(0.2, 0.2, 0.1, 0.6)
        #cv2.imwrite("debug_result_allow.png", img)
        res = cv2.matchTemplate(img, self.menu_templates["result_arrow"], cv2.TM_CCOEFF_NORMED)
        _, val, _, pos = cv2.minMaxLoc(res)

        pos_ = 0
        if val > 0.8:
            pos_y = pos[1]
            print(f'pos_y: {pos_y}')
            if pos_y < 160:
                pos_ = 0
            elif pos_y < 320:
                pos_ = 1
            elif pos_y < 480:
                pos_ = 2
            else:
                pos_ = 3
        else:
            return False
        result_dict = {"player_team":{}, "enemy_team":{},}
        result_dict["player_team"]["player"] = self.get_result_stats(pos_)
        result_dict["player_team"]["player"]["chara"] = self.chara_list[self.pos]
        our_pos, enemy1_pos, enemy2_pos = self.get_other_pos(pos_)
        
        our_cpos, enemy1_cpos, enemy2_cpos = self.get_other_pos(self.pos)

        result_dict["player_team"]["player2"] = self.get_result_stats(our_pos)
        result_dict["player_team"]["player2"]["chara"] = self.chara_list[our_cpos]
        result_dict["enemy_team"]["enemy"] = self.get_result_stats(enemy1_pos)
        result_dict["enemy_team"]["enemy"]["chara"] = self.chara_list[enemy1_cpos]
        result_dict["enemy_team"]["enemy2"] = self.get_result_stats(enemy2_pos)
        result_dict["enemy_team"]["enemy2"]["chara"] = self.chara_list[enemy2_cpos]

        self.data_m.append_match_log_jsonl(result_dict)
        return True
    
    def get_other_pos(self, pos):
        
        our_pos, enemy1_pos, enemy2_pos = -1, -1, -1
        match pos:
            case 0:
                our_pos, enemy1_pos, enemy2_pos = 1, 2, 3
            case 1:
                our_pos, enemy1_pos, enemy2_pos = 0, 2, 3
            case 2:
                our_pos, enemy1_pos, enemy2_pos = 3, 0, 1
            case 3:
                our_pos, enemy1_pos, enemy2_pos = 2, 0, 1
        return our_pos, enemy1_pos, enemy2_pos
    
    def get_result_stats(self, pos):
        img = self.get_area_from_cache(0.4, 0.285 + 0.147 * pos, 0.4, 0.06)
        gray_item = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        scale_factor = 3.0
        width = int(gray_item.shape[1] * scale_factor)
        height = int(gray_item.shape[0] * scale_factor)
        gray_item = cv2.resize(gray_item, (width, height), interpolation=cv2.INTER_CUBIC)
        _, img = cv2.threshold(gray_item, 200, 255, cv2.THRESH_BINARY)
        cv2.imwrite("debug_result_row.png", img)
        h, w = img.shape[:2]
        damage_img = img[0:h, 0:int(w * 0.2)]
        kd_img = img[0:h, int(w * 0.28):int(w * 0.36)]
        lock_img = img[0:h, int(w * 0.932):int(w * 0.98)]
        #cv2.imwrite("debug_result_row_d.png", damage_img)
        #cv2.imwrite("debug_result_row_k.png", kd_img)
        #cv2.imwrite("debug_result_row_l.png", lock_img)
        damage = self.recognize_centered_number_strict(damage_img, self.result_num_templates, 0, 0.65)
        black_bar = np.zeros((h, 10), dtype=np.uint8) # 10ピクセル幅の黒帯
        kill_img, death_img = self.divide_img(kd_img)
        kill_img = cv2.hconcat([black_bar, kill_img, black_bar])
        kill, kill_val = self.match_result_num(kill_img)
        if kill_val < 0.6:
            kill = 0
        death_img = cv2.hconcat([black_bar, death_img, black_bar])
        death, death_val = self.match_result_num(death_img)
        if death_val < 0.6:
            death = 0
        
        lock_img = cv2.hconcat([black_bar, lock_img, black_bar])
        lock = self.recognize_centered_number_strict(lock_img, self.result_num_templates)
        return {
            "damage":damage,
            "kill":kill,
            "death":death,
            "lock":lock,
        }

    def divide_img(self, img):
        h, w = img.shape[:2]
        img1 = img[0:h, 0:int(w * 0.5)]
        img2 = img[0:h, int(w * 0.5):w]
        return img1, img2
    
    def match_result_num(self, img):
        max_name, max_val = "", -1
        for name, template in self.result_num_templates.items():
            # アイコンを探す（閾値は少し高めの0.8〜0.9がおすすめ）
            res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)

            if val > max_val:
                max_name = name
                max_val = val

            if val > 0.8:
                break
        return int(max_name), max_val

    def recognize_centered_number_strict(self, roi_img, templates:dict, _return = 0, th = 0.7, distance = 10):
            
        candidates = []
        threshold = th  # 閾値。誤検知が多い場合は0.90などに上げる

        # 1. 候補リストを作るときに、テンプレートの「横幅(w)」も一緒に保存しておく
        for digit, tpl in templates.items():
            if tpl is None: continue
            
            # テンプレート画像の幅(w)と高さ(h)を取得 (※2値化済みのグレースケール画像前提)
            h, w = tpl.shape 
            
            res = cv2.matchTemplate(roi_img, tpl, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            
            for pt in zip(*loc[::-1]): 
                x_pos = pt[0]
                score = res[pt[1], pt[0]]
                # 横幅 'w' も候補データに含める
                candidates.append({'x': x_pos, 'digit': digit, 'score': score, 'w': w})
                #print(f'x: {x_pos}, digit: {digit}, score: {score}, w: {w}')

        # 2. スコア順に並び替え
        candidates.sort(key=lambda item: item['score'], reverse=True)

        final_digits = []

        # 3. 場所の確定（陣取りゲーム）を「文字の幅」ベースで行う
        for cand in candidates:
            is_overlapping = False
            
            for final_d in final_digits:
                # 確定済みの文字の左端と右端
                f_left = final_d['x']
                f_right = final_d['x'] + final_d['w']
                
                # 今回チェックする候補の文字の左端と右端
                c_left = cand['x']
                c_right = cand['x'] + cand['w']
                
                # 【完全な重なり判定】にお互い数ピクセル食い込んでてもセーフにする「遊び」を入れる
                overlap_pixel = int(cand['w'] * 0.15)
                
                if f_left < (c_right - overlap_pixel) and c_left < (f_right - overlap_pixel):
                    is_overlapping = True
                    break
                    
            if not is_overlapping:
                final_digits.append(cand)

        # 4. 最後に「X座標の順（左から右）」に並び替えて結合
        if not final_digits:
            return _return
            
        final_digits.sort(key=lambda item: item['x'])
        number_str = "".join([str(d['digit']) for d in final_digits])
        
        return int(number_str)
    
    def debug_name(self):
        #img1 = self.get_area_from_cache(0.07, 0.02, 0.1, 0.05)
        #cv2.imwrite("debug_rp.png", img1)
        #img2 = self.get_area_from_cache(0.07, 0.5, 0.1, 0.05)
        #cv2.imwrite("debug_rp2.png", img2)
        img3 = self.get_area_from_cache(0, 0.865, 0.2, 0.05)
        cv2.imwrite("debug_cname.png", img3)
        #img4 = self.get_area_from_cache(0.83, 0.5, 0.1, 0.05)
        #cv2.imwrite("debug_rp4.png", img4)