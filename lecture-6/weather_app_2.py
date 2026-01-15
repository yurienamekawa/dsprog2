import flet as ft
import requests
import datetime
import sqlite3
import os

# --- 設定 ---
FOLDER_NAME = "lecture-6"
DB_NAME = os.path.join(FOLDER_NAME, "weather_app.db")

# フォルダがない場合は作成
if not os.path.exists(FOLDER_NAME):
    os.makedirs(FOLDER_NAME)

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

# --- 3. メインアプリ ---

def main(page: ft.Page):
    init_db() # 起動時にDB準備
    page.title = "天気予報アプリ（第6回授業）"
    
    forecast_row = ft.Row(wrap=True, spacing=15)
    title_text = ft.Text("地域を選択してください", size=20, weight="bold")

    def on_area_click(e):
        area_code = e.control.data
        area_name = e.control.title.value
        forecast_row.controls.clear()
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
                    temps = areas.get("temps", ["--"] * 14)
                    for i in range(len(times)):
                        d = times[i][:10]
                        if d not in forecast_map: forecast_map[d] = {"code": None, "min": "--", "max": "--"}
                        if i < len(codes): forecast_map[d]["code"] = codes[i]

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
        page.update()

    # サイドバー作成
    area_data = requests.get("https://www.jma.go.jp/bosai/common/const/area.json").json()
    sidebar = [ft.ExpansionTile(title=ft.Text(c["name"]), controls=[
        ft.ListTile(title=ft.Text(area_data["offices"][o]["name"]), on_click=on_area_click, data=o)
        for o in c["children"] if o in area_data["offices"]
    ]) for _, c in area_data["centers"].items()]

    page.add(ft.Row([
        ft.Container(content=ft.Column(sidebar, scroll=ft.ScrollMode.AUTO), width=250, bgcolor="#F5F5F5"),
        ft.Container(content=ft.Column([title_text, forecast_row], scroll=ft.ScrollMode.AUTO), expand=True, padding=20)
    ], expand=True))

if __name__ == "__main__":
    ft.app(target=main)