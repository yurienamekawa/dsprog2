import flet as ft
import requests
import datetime

BASE_ICONS = {
    "晴": "100",
    "曇": "200",
    "雨": "300",
    "雪": "400",
}

#天気コードから天気情報を取得
def get_weather_info(code):
    if not code: return ""
    c = int(code)
    code_map = {
        100: "晴", 101: "晴時々曇", 102: "晴一時雨", 103: "晴時々雨", 104: "晴一時雪", 105: "晴時々雪",
        110: "晴後曇", 111: "晴後雨", 112: "晴後雪", 113: "晴後雨", 114: "晴後雨",
        200: "曇", 201: "曇時々晴", 202: "曇一時雨", 203: "曇時々雨", 204: "曇一時雪", 205: "曇時々雪",
        210: "曇後晴", 211: "曇後雨", 212: "曇後雪",
        300: "雨", 301: "雨時々晴", 302: "雨一時晴", 303: "雨時々止む", 311: "雨後晴", 313: "雨後曇", 314: "雨後雪",
        400: "雪", 401: "雪時々晴", 402: "雪一時晴", 411: "雪後晴", 413: "雪後曇", 414: "雪後雨",
    }
    return code_map.get(c, "不明") #もし不明なコードなら「不明」を返す

#API関連の関数
def get_areas():
    url = "https://www.jma.go.jp/bosai/common/const/area.json" #気象庁のエリア情報APIのURL
    return requests.get(url).json() #

def get_forecast(area_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json" #気象庁の天気予報APIのURL
    return requests.get(url).json() #

#天気カード
class WeatherCard(ft.Container):
    def __init__(self, date_obj, weather_code, min_temp, max_temp, is_today=False):
        super().__init__()
        # 日付と曜日の取得
        date_str = date_obj.strftime("%Y-%m-%d")
        w_day = date_obj.weekday()
        
        # 土日の配色
        bg_color = ft.Colors.WHITE
        text_color = ft.Colors.BLACK
        if w_day == 5: bg_color = "#EBF5FB"
        elif w_day == 6: bg_color = "#FDF2F2"
        # 今日の強調表示
        border = ft.border.all(2, ft.Colors.INDIGO_400) if is_today else None

        # 天気情報の解析
        weather_text = get_weather_info(weather_code)
        
        # 表示用ビジュアルの構築
        if not weather_code:
            weather_visual = ft.Icon(ft.Icons.BLOCK, size=60, color=ft.Colors.GREY_300)
        elif "後" in weather_text:
            # もし「後」が含まれる場合
            parts = weather_text.split("後")
            icon1_code = BASE_ICONS.get(parts[0], "100")
            icon2_code = BASE_ICONS.get(parts[1], "200")
            # 2つのアイコンを矢印でつなぐ表示
            weather_visual = ft.Row(
                [
                    ft.Image(src=f"https://www.jma.go.jp/bosai/forecast/img/{icon1_code}.png", width=50, height=50),
                    ft.Icon(ft.Icons.ARROW_RIGHT_ALT, color=ft.Colors.RED_400, size=30),
                    ft.Image(src=f"https://www.jma.go.jp/bosai/forecast/img/{icon2_code}.png", width=50, height=50),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5
            )
        else:
            # 通常の場合
            icon_url = f"https://www.jma.go.jp/bosai/forecast/img/{str(weather_code).zfill(3)}.png"
            weather_visual = ft.Image(src=icon_url, width=75, height=75)

        self.content = ft.Column([ 
            ft.Text(date_str, size=14, weight="bold", color=text_color),
            ft.Container(content=weather_visual, height=80, alignment=ft.alignment.center),
            ft.Text(weather_text, size=20, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.Row([
                ft.Text(f"{max_temp}℃", color=ft.Colors.RED if max_temp != "--" else ft.Colors.GREY_400, size=18, weight="bold"),
                ft.Text("/", size=14, color=ft.Colors.GREY_400),
                ft.Text(f"{min_temp}℃", color=ft.Colors.BLUE if min_temp != "--" else ft.Colors.GREY_400, size=18, weight="bold"),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        self.bgcolor = bg_color
        self.padding = 15
        self.border_radius = 15
        self.border = border
        self.width = 190
        self.height = 260
        self.shadow = ft.BoxShadow(blur_radius=8, color=ft.Colors.BLACK12)

def main(page: ft.Page):
    page.title = "7日間天気予報"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    # メインコンテンツエリア
    forecast_row = ft.Row(wrap=True, spacing=20, run_spacing=20)
    main_content = ft.Container(
        content=ft.Column([
            ft.Text("地域を選択してください", size=20, weight="bold", color="white"),
            forecast_row
        ], scroll=ft.ScrollMode.AUTO),
        expand=True, padding=30, bgcolor="#BDC3C7"
    )

    # エリア選択時の処理
    def on_area_click(e):
        area_code = e.control.data
        area_name = e.control.title.value
        main_content.content.controls[0].value = f"{area_name} の天気予報"
        forecast_row.controls.clear()
        page.update()

        # 天気予報データの取得と表示
        try:
            today = datetime.date.today()
            target_dates = [today + datetime.timedelta(days=i) for i in range(7)]
            data = get_forecast(area_code)
            forecast_map = {}

            # 短期と週間の統合
            for d_idx in range(len(data)):
                ts_list = data[d_idx]["timeSeries"]
                w_times = ts_list[0]["timeDefines"]
                w_codes = ts_list[0]["areas"][0]["weatherCodes"]
                # 気温データの抽出
                t_min_list, t_max_list = [], []
                for ts in ts_list:
                    a = ts["areas"][0]
                    if "temps" in a:
                        t_min_list, t_max_list = a["temps"][0::2], a["temps"][1::2]
                        break
                    elif "tempsMin" in a:
                        t_min_list, t_max_list = a["tempsMin"], a["tempsMax"]
                        break
                # データのマッピング
                for i in range(len(w_times)):
                    d_key = w_times[i][:10]
                    if d_key not in forecast_map:
                        forecast_map[d_key] = {"code": None, "min": "--", "max": "--"}
                    if i < len(w_codes) and w_codes[i]:
                        forecast_map[d_key]["code"] = w_codes[i]
                    if i < len(t_min_list) and t_min_list[i] != "":
                        forecast_map[d_key]["min"] = t_min_list[i]
                    if i < len(t_max_list) and t_max_list[i] != "":
                        forecast_map[d_key]["max"] = t_max_list[i]
            # 天気カードの追加
            for d in target_dates:
                d_str = d.strftime("%Y-%m-%d")
                f = forecast_map.get(d_str)
                forecast_row.controls.append(
                    WeatherCard(d, f["code"] if f else None, 
                                f["min"] if f else "--", f["max"] if f else "--", is_today=(d == today))
                )
        except Exception:
            main_content.content.controls[0].value = "エラーが発生しました"
        
        page.update()

    # サイドバー
    area_data = get_areas()
    sidebar_items = []
    for _, c in area_data["centers"].items():
        sidebar_items.append(
            ft.ExpansionTile( #
                title=ft.Text(c["name"]),
                controls=[
                    ft.ListTile( #
                        title=ft.Text(area_data["offices"][o]["name"], size=13),
                        on_click=on_area_click, data=o
                    ) for o in c["children"] if o in area_data["offices"]
                ]
            )
        )
    # ページレイアウト
    page.add(
        ft.AppBar(title=ft.Text("7日間天気予報", color="white"), bgcolor=ft.Colors.INDIGO_900),
        ft.Row([
            ft.Container(content=ft.Column(sidebar_items, scroll=ft.ScrollMode.AUTO), width=260, bgcolor="#F0F3F4"),
            ft.VerticalDivider(width=1),
            main_content
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
    )
# アプリ起動
if __name__ == "__main__":
    ft.app(target=main)