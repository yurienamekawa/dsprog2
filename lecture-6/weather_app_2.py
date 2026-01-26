import flet as ft
import requests
import datetime
import sqlite3
import os

# --- 設定 ---
DB_NAME = "weather_app.db"

BASE_ICONS = {
    "晴": "100", "曇": "200", "雨": "300", "雪": "400",
}

# --- 1. データベース設計と操作 ---

def init_db():
    """DBとテーブルの初期化"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # 予報テーブル設計
    # area_codeとdateを組み合わせてプライマリーキーにすることで、重複登録を防ぎます
    cur.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            area_code TEXT,
            date TEXT,
            weather_code TEXT,
            temp_min TEXT,
            temp_max TEXT,
            PRIMARY KEY (area_code, date)
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(area_code, forecast_map):
    """APIから取得したデータをDBに保存（既存データは更新）"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for date_str, data in forecast_map.items():
        cur.execute('''
            INSERT INTO forecasts (area_code, date, weather_code, temp_min, temp_max)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(area_code, date) DO UPDATE SET
                weather_code=excluded.weather_code,
                temp_min=excluded.temp_min,
                temp_max=excluded.temp_max
        ''', (area_code, date_str, data["code"], data["min"], data["max"]))
    conn.commit()
    conn.close()

def get_from_db(area_code, start_date, end_date):
    """DBから指定期間の予報を取得"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT date, weather_code, temp_min, temp_max FROM forecasts
        WHERE area_code = ? AND date BETWEEN ? AND ?
        ORDER BY date ASC
    ''', (area_code, start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return {row[0]: {"code": row[1], "min": row[2], "max": row[3]} for row in rows}

# --- 2. 補助関数 ---

def get_weather_info(code):
    if not code: return "不明"
    code_map = {100: "晴", 200: "曇", 300: "雨", 400: "雪"} # 簡略化
    return code_map.get(int(code) // 100 * 100, "不明")

class WeatherCard(ft.Container):
    def __init__(self, date_obj, weather_code, min_temp, max_temp, is_today=False):
        super().__init__()
        date_str = date_obj.strftime("%Y-%m-%d")
        weather_text = get_weather_info(weather_code)
        
        icon_url = f"https://www.jma.go.jp/bosai/forecast/img/{str(weather_code).zfill(3)}.png" if weather_code else ""
        
        self.content = ft.Column([
            ft.Text(date_str, size=14, weight="bold"),
            ft.Image(src=icon_url, width=60, height=60) if icon_url else ft.Icon(ft.Icons.BLOCK),
            ft.Text(weather_text, size=18, weight="bold"),
            ft.Text(f"{max_temp}℃ / {min_temp}℃", size=16),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.bgcolor = ft.Colors.WHITE
        self.padding = 15
        self.border_radius = 10
        self.border = ft.border.all(2, ft.Colors.INDIGO_400) if is_today else None
        self.width = 160
        self.shadow = ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12)

# --- 3. 地図表示用データとロジック ---

# 日本地図の境界（Wikimedia Commons: Japan_location_map.svg に準拠）
MAP_BOUNDS = {"N": 46.0, "S": 30.0, "W": 128.0, "E": 149.0} 
# ※表示領域を調整（沖縄などを考慮すると広すぎるため、本州中心にトリミングするか、
# 全体表示用の画像URLを使う必要があります。
# 今回は「Japan regions map」のような画像を使用し、簡易的な位置表示を行います。）

# 今回使用する画像の有効範囲（概算）
# 画像URL: ローカルの japan_map.svg
# この画像は N=45.6, S=24.0, W=122.5, E=154.0 程度を含みます（沖縄含む）

MAP_FILE_PATH = os.path.join(os.path.dirname(__file__), "japan_map.svg")

MAP_CONFIG = {
    "url": MAP_FILE_PATH,
    # 沖縄を含めると本州が小さくなり座標がずれるため、本州・北海道・九州・四国を基準に設定
    # N=46(稚内), S=30(屋久島付近), W=128(長崎西), E=148(根室東)
    "N": 46.0, "S": 30.0, "W": 128.0, "E": 148.0
}

# 都道府県ごとの代表座標（簡易リスト）
PREF_COORDS = {
    "宗谷地方": (45.41, 141.67), "上川・留萌地方": (43.77, 142.36), "網走・北見・紋別地方": (44.02, 144.27),
    "釧路・根室・十勝地方": (42.98, 144.38), "胆振・日高地方": (42.31, 140.97), "石狩・空知・後志地方": (43.06, 141.35),
    "渡島・檜山地方": (41.76, 140.73),
    "青森県": (40.82, 140.74), "岩手県": (39.70, 141.15), "宮城県": (38.26, 140.87),
    "秋田県": (39.72, 140.10), "山形県": (38.24, 140.36), "福島県": (37.75, 140.46),
    "茨城県": (36.34, 140.44), "栃木県": (36.56, 139.88), "群馬県": (36.39, 139.06),
    "埼玉県": (35.85, 139.64), "千葉県": (35.60, 140.12), "東京都": (35.68, 139.69),
    "神奈川県": (35.44, 139.64), "新潟県": (37.90, 139.02), "富山県": (36.69, 137.21),
    "石川県": (36.59, 136.62), "福井県": (36.06, 136.22), "山梨県": (35.66, 138.56),
    "長野県": (36.65, 138.18), "岐阜県": (35.39, 136.72), "静岡県": (34.97, 138.38),
    "愛知県": (35.18, 136.90), "三重県": (34.73, 136.50), "滋賀県": (35.00, 135.86),
    "京都府": (35.02, 135.75), "大阪府": (34.69, 135.50), "兵庫県": (34.69, 135.18),
    "奈良県": (34.68, 135.80), "和歌山県": (34.22, 135.16), "鳥取県": (35.50, 134.23),
    "島根県": (35.47, 133.05), "岡山県": (34.66, 133.93), "広島県": (34.39, 132.45),
    "山口県": (34.18, 131.47), "徳島県": (34.06, 134.55), "香川県": (34.34, 134.04),
    "愛媛県": (33.84, 132.76), "高知県": (33.56, 133.53), "福岡県": (33.60, 130.41),
    "佐賀県": (33.24, 130.29), "長崎県": (32.74, 129.87), "熊本県": (32.78, 130.74),
    "大分県": (33.23, 131.61), "宮崎県": (31.91, 131.42), "鹿児島県": (31.56, 130.55),
    "沖縄県": (26.21, 127.68)
}

def get_map_widget(area_name):
    """地図と現在地のドットを含むStackを返す"""
    coords = PREF_COORDS.get(area_name)
    
    # 座標が見つからない場合はデフォルト（東京付近）か非表示
    if not coords:
        # 名前が一致しない場合のフォールバック（「県」なしで検索など）
        for k, v in PREF_COORDS.items():
            if k in area_name or area_name in k:
                coords = v
                break
    
    markers = []
    if coords:
        lat, lon = coords
        # 緯度経度を画像の%座標に変換
        # x = (lon - W) / (E - W)
        # y = (N - lat) / (N - S)
        
        # 範囲外除外
        if MAP_CONFIG["S"] <= lat <= MAP_CONFIG["N"] and MAP_CONFIG["W"] <= lon <= MAP_CONFIG["E"]:
            x_pct = (lon - MAP_CONFIG["W"]) / (MAP_CONFIG["E"] - MAP_CONFIG["W"])
            y_pct = (MAP_CONFIG["N"] - lat) / (MAP_CONFIG["N"] - MAP_CONFIG["S"])
            
            markers.append(
                ft.Container(
                    width=15, height=15, bgcolor=ft.Colors.RED,
                    border_radius=10,
                    border=ft.border.all(2, ft.Colors.WHITE),
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK54),
                    # Absolute positioning within the Stack
                    left=x_pct * 300, # 画像幅に合わせる（後で調整）
                    top=y_pct * 300,   # 画像高さに合わせる
                )
            )

    return ft.Stack(
        [
            ft.Image(src=MAP_CONFIG["url"], width=300, height=300, fit=ft.ImageFit.CONTAIN, opacity=0.7),
        ] + markers,
        width=300, height=300
    )

# --- 4. メインアプリ ---

def main(page: ft.Page):
    init_db() # 起動時にDB準備
    page.title = "天気予報アプリ（第6回授業）"
    
    forecast_row = ft.Row(wrap=True, spacing=15)
    title_text = ft.Text("地域を選択してください", size=20, weight="bold")
    
    # 地図表示用コンテナ（初期状態はマーカーなし）
    map_container = ft.Container(content=get_map_widget(""), padding=10)

    def on_area_click(e):
        area_code = e.control.data
        area_name = e.control.title.value
        forecast_row.controls.clear()
        
        # 地図の更新
        map_container.content = get_map_widget(area_name)
        page.update()

        try:
            # ① APIから取得
            res = requests.get(f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json").json()
            forecast_map = {}
            # データの解析（簡易版）
            for entry in res:
                for ts in entry["timeSeries"]:
                    times = ts["timeDefines"]
                    areas = ts["areas"][0]
                    
                    codes = areas.get("weatherCodes", [])
                    temps = areas.get("temps", [])
                    temps_min = areas.get("tempsMin", [])
                    temps_max = areas.get("tempsMax", [])

                    for i in range(len(times)):
                        d = times[i][:10]
                        if d not in forecast_map: 
                            forecast_map[d] = {"code": None, "min": "--", "max": "--", "temp_list": []}
                        
                        # Weather Codes
                        if i < len(codes): 
                            forecast_map[d]["code"] = codes[i]
                            
                        # Temps (明日の予報など、tempsリストとして提供される場合)
                        if i < len(temps) and temps[i] != "":
                             try:
                                 forecast_map[d]["temp_list"].append(int(temps[i]))
                             except:
                                 pass

                        # Temps Min (週間予報の最低気温)
                        if i < len(temps_min) and temps_min[i] != "" and temps_min[i] != "--":
                            forecast_map[d]["min"] = temps_min[i]
                            
                        # Temps Max (週間予報の最高気温)
                        if i < len(temps_max) and temps_max[i] != "" and temps_max[i] != "--":
                            forecast_map[d]["max"] = temps_max[i]

            # 収集したtemp_listから最大・最小を補完（週間予報で欠けている場合など）
            for d, data in forecast_map.items():
                if data.get("temp_list"):
                    # minが欠けていればtemp_listの最小値を採用
                    if data["min"] == "--":
                        data["min"] = str(min(data["temp_list"]))
                    # maxが欠けていればtemp_listの最大値を採用
                    if data["max"] == "--":
                        data["max"] = str(max(data["temp_list"]))

            # ② DBに格納
            save_to_db(area_code, forecast_map)

            # ③ DBから読み出して表示
            today = datetime.date.today()
            end_day = today + datetime.timedelta(days=6)
            db_data = get_from_db(area_code, today.isoformat(), end_day.isoformat())

            for i in range(7):
                d = today + datetime.timedelta(days=i)
                f = db_data.get(d.isoformat(), {"code": None, "min": "--", "max": "--"})
                forecast_row.controls.append(WeatherCard(d, f["code"], f["min"], f["max"], is_today=(i==0)))
            
            title_text.value = f"{area_name} の予報"
        except Exception as ex:
            title_text.value = f"エラー: {ex}"
            import traceback
            traceback.print_exc()
        page.update()

    # サイドバー作成
    area_data = requests.get("https://www.jma.go.jp/bosai/common/const/area.json").json()
    sidebar = [ft.ExpansionTile(title=ft.Text(c["name"]), controls=[
        ft.ListTile(title=ft.Text(area_data["offices"][o]["name"]), on_click=on_area_click, data=o)
        for o in c["children"] if o in area_data["offices"]
    ]) for _, c in area_data["centers"].items()]

    page.add(ft.Row([
        ft.Container(content=ft.Column(sidebar, scroll=ft.ScrollMode.AUTO), width=250, bgcolor="#F5F5F5"),
        ft.Container(content=ft.Column([title_text, map_container, forecast_row], scroll=ft.ScrollMode.AUTO), expand=True, padding=20)
    ], expand=True))

if __name__ == "__main__":
    ft.app(target=main)