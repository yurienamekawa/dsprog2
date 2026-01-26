import sqlite3
import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import os

class TransitScraper:
    def __init__(self, db_name="transit_data.db"):
        # 実行ファイルと同じディレクトリにDBを作成する設定
        base_dir = os.path.dirname(__file__)
        self.db_path = os.path.join(base_dir, db_name)
        self._create_table()

    def _create_table(self):
        """DBにテーブルを作成する """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS travel_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin TEXT,
                    destination TEXT,
                    fare INTEGER,
                    travel_time INTEGER,
                    route_type TEXT
                )
            ''')

    def save_data(self, origin, destination, fare, travel_time, route_type):
        """収集したデータをDBに格納する """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO travel_results (origin, destination, fare, travel_time, route_type) VALUES (?, ?, ?, ?, ?)",
                (origin, destination, fare, travel_time, route_type)
            )

    def scrape(self, origin, destination):
        """Yahoo!路線情報をスクレイピングする [cite: 19]"""
        origin_enc = urllib.parse.quote(origin)
        dest_enc = urllib.parse.quote(destination)
        url = f"https://transit.yahoo.co.jp/search/result?from={origin_enc}&to={dest_enc}"
        
        # サーバ負荷に配慮し1秒待機 
        time.sleep(1) 
        
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        routes = soup.select(".routeSummary")
        
        for route in routes:
            try:
                # 料金の抽出（数字以外を削除）
                fare_text = route.select_one(".fare").get_text(strip=True)
                fare = int(re.sub(r'\D', '', fare_text))
                
                # 所要時間の抽出（括弧内の数字のみ抽出）
                time_text = route.select_one(".time").get_text(strip=True)
                duration_match = re.search(r'（(.*?)）', time_text)
                if duration_match:
                    d_str = duration_match.group(1)
                    h_match = re.search(r'(\d+)時間', d_str)
                    m_match = re.search(r'(\d+)分', d_str)
                    h = int(h_match.group(1)) if h_match else 0
                    m = int(m_match.group(1)) if m_match else 0
                    duration = h * 60 + m if (h_match or m_match) else int(re.sub(r'\D', '', d_str))
                else:
                    duration = 0
                
                status_tags = route.select(".status dfn")
                status = ",".join([s.get_text(strip=True) for s in status_tags])
                
                self.save_data(origin, destination, fare, duration, status)
                print(f"保存成功: {origin}->{destination} ({duration}分, {fare}円, {status})")
                
            except Exception as e:
                print(f"解析エラー: {e}")

if __name__ == "__main__":
    scraper = TransitScraper()
    origin = "新宿"
    # 近・中・遠距離を網羅する目的地リスト [cite: 23, 25]
    destinations = [
        "中野", "吉祥寺", "立川", "三鷹", "登戸", 
        "横浜", "大宮", "八王子", "成田空港", "小田原", 
        "名古屋", "新大阪", "仙台", "金沢", "広島"
    ]
    for dest in destinations:
        scraper.scrape(origin, dest)
    print("すべてのデータの保存が完了しました。")