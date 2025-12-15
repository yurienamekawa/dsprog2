import flet as ft  # PythonでGUIアプリを作るためのライブラリ
import math  # 数学関数を使うためのライブラリ

# ボタンデザインのクラス定義
class CalcButton(ft.Container):
    def __init__(self, text, button_clicked, bgcolor, color, expand=1):
        # ボタンの初期化
        # text: ボタンに表示する文字
        # button_clicked: ボタンが押されたときに呼ばれる関数
        # bgcolor: ボタンの背景色
        # color: ボタンの文字色
        # expand: ボタンの横幅の倍率（1=通常、2=2倍幅）
        
        super().__init__()  # 親クラス（ft.Container）の初期化
        self.data = text  # ボタンのデータ（計算処理で使用）
        self.expand = expand  # 横幅の倍率
        
        # ボタンに表示するテキストの設定
        button_content = ft.Text(
            text,  # 表示する文字
            size=18,  # 文字サイズ
            weight=ft.FontWeight.W_600,  # 文字の太さ
            color=color,  # 文字の色
            text_align=ft.TextAlign.CENTER,  # 中央揃え
        )
        
        # ボタンの見た目の設定
        self.content = button_content  # ボタンの中身のテキスト
        self.bgcolor = bgcolor  # 背景色
        self.border_radius = ft.border_radius.all(20)  # 角を丸くする
        self.alignment = ft.alignment.center  # 中央揃え
        self.height = 55  # ボタンの高さ
        self.width = 55 if expand == 1 else 120
        self.on_click = button_clicked  # クリック時に呼ばれる関数を設定
        
        # ボタンに影をつける
        self.shadow = ft.BoxShadow(
            spread_radius=1,  # 影の広がり
            blur_radius=6,  # 影のぼかし具合
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),  # 影の色
            offset=ft.Offset(0, 3),  # 影の位置
        )
        
        # ホバーエフェクト有効化
        self.ink = True


class DigitButton(CalcButton):
    # 数字ボタンのクラス
    # CalcButtonを継承して、色だけ変更
    
    def __init__(self, text, button_clicked, expand=1):
        super().__init__(text, button_clicked, "#F8F8F8", "#2D5016", expand)


class ActionButton(CalcButton):
    # +, −, ×, ÷, =のクラス
    
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked, "#C41E3A", ft.Colors.WHITE)


class ExtraActionButton(CalcButton):
    # AC, ±, %のクラス
    
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked, "#D4AF37", ft.Colors.WHITE)


class ScientificButton(CalcButton):
    # sin, cos, tan, ln等（科学計算）のクラス
    
    def __init__(self, text, button_clicked, expand=1):
        super().__init__(text, button_clicked, "#165B33", ft.Colors.WHITE, expand)


# 計算機アプリケーションのメインクラス
class CalculatorApp(ft.Container):
    # 計算機全体を管理するクラス
    
    def __init__(self):
        # 計算機の初期化
        super().__init__()  # 親クラスの初期化
        self.reset()  # 計算状態をリセット

        # 計算結果を表示するテキスト
        self.result = ft.Text(
            value="0",  # 初期値は0
            color="#2D2D2D",  # 文字色
            size=42,  # 文字サイズ
            weight=ft.FontWeight.W_500,  # 文字の太さ
            text_align=ft.TextAlign.RIGHT,  # 右揃え
        )
        
        # 計算機全体の設定
        self.width = 320  # 幅
        self.bgcolor = ft.Colors.WHITE  # 背景色
        self.border_radius = ft.border_radius.all(25)  # 角を丸くする
        self.padding = 18  # 内側の余白
        
        # 計算機全体に影をつける
        self.shadow = ft.BoxShadow(
            spread_radius=3,
            blur_radius=12,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 6),
        )
        
        # 計算機のレイアウト（縦に並べる）
        self.content = ft.Column(
            spacing=10,  # ボタン行の間隔
            controls=[
                ft.Container(
                    content=self.result,  # 結果テキスト
                    alignment=ft.alignment.center_right,  # 右揃え
                    padding=ft.padding.only(top=15, bottom=15, right=12, left=12),
                    bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),  # 半透明の白背景
                    border_radius=ft.border_radius.all(15),
                    height=80,
                ),
                
                # 指数対数
                ft.Row(
                    spacing=10,  # ボタン間の間隔
                    alignment=ft.MainAxisAlignment.CENTER,  # 中央揃え
                    controls=[
                        ScientificButton(text="ln", button_clicked=self.button_clicked),  # 自然対数
                        ScientificButton(text="10ˣ", button_clicked=self.button_clicked),  # 10のx乗
                        ScientificButton(text="eˣ", button_clicked=self.button_clicked),  # eのx乗
                        ScientificButton(text="|x|", button_clicked=self.button_clicked),  # 絶対値
                    ]
                ),

                # 三角関数
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ScientificButton(text="sin", button_clicked=self.button_clicked),  # サイン
                        ScientificButton(text="cos", button_clicked=self.button_clicked),  # コサイン
                        ScientificButton(text="tan", button_clicked=self.button_clicked),  # タンジェント
                        ScientificButton(text="π", button_clicked=self.button_clicked),  # 円周率
                    ]
                ),

                # AC, ±, %, ÷
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),  # オールクリア
                        ExtraActionButton(text="±", button_clicked=self.button_clicked),  # 正負反転
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),  # パーセント
                        ActionButton(text="÷", button_clicked=self.button_clicked),  # 割り算
                    ]
                ),
                
                # 7, 8, 9, ×
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="×", button_clicked=self.button_clicked),  # 掛け算
                    ]
                ),
                
                # 4, 5, 6, −
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="−", button_clicked=self.button_clicked),  # 引き算
                    ]
                ),
                
                # 1, 2, 3, +
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),  # 足し算
                    ]
                ),
                
                # 0, ., =
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),  # 0は2倍幅
                        DigitButton(text=".", button_clicked=self.button_clicked),  # 小数点
                        ActionButton(text="=", button_clicked=self.button_clicked),  # イコール
                    ]
                ),
            ]
        )
        
    # 科学計算の関数リスト
    SCIENTIFIC_ACTIONS = ("sin", "cos", "tan", "ln", "10ˣ", "eˣ", "|x|")
    # 定数のリスト
    CONSTANTS = ("π",)

    def button_clicked(self, e):
        # ボタンがクリックされたときに呼ばれる関数
        # e: イベント情報（どのボタンが押されたか等）
        
        data = e.control.data  # 押されたボタンのデータを取得
        
        # エラー表示中またはACボタンが押された場合
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"  # 表示を0に戻す
            self.reset()  # 計算状態をリセット
            
        #  数字または小数点が押された場合
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                # 現在0が表示されているか、新しい数字の入力開始の場合
                self.result.value = data  # 押された数字を表示
                self.new_operand = False  # 新しい数字入力フラグをオフ
            elif data == "." and "." in self.result.value:
                # すでに小数点がある場合は何もしない
                pass
            else:
                # 数字を追加（15桁まで）
                if len(str(self.result.value).replace('.', '')) < 15: 
                    self.result.value = self.result.value + data
        
        # π
        elif data in self.CONSTANTS:
            if data == "π":
                self.result.value = str(self.format_number(math.pi))  # 円周率を表示
            self.new_operand = True  # 次は新しい数字の入力

        # +, −, ×, ÷
        elif data in ("+", "−", "×", "÷"):
            # 表示用の記号を内部処理用の記号に変換
            operator_map = {"÷": "/", "×": "*", "−": "-"}
            internal_op = operator_map.get(data, data)
            
            # 前の計算があれば実行
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.operator = internal_op  # 新しい演算子を保存
            if self.result.value == "Error":
                self.operand1 = 0
            else:
                self.operand1 = float(self.result.value)  # 計算結果を次の計算の第1オペランドに
            self.new_operand = True  # 次は新しい数字の入力
            
        # 科学計算ボタンが押された場合
        elif data in self.SCIENTIFIC_ACTIONS:
            try:
                # 科学計算を実行
                self.result.value = self.calculate_scientific(float(self.result.value), data)
                self.new_operand = True
            except Exception:
                # エラーが発生した場合
                self.result.value = "Error"
                self.reset()

        # イコールボタンが押された場合
        elif data == "=":
            # 計算を実行して結果を表示
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.reset()  # 計算状態をリセット

        # パーセントボタンが押された場合
        elif data == "%":
            try:
                # 現在の値を100で割る
                self.result.value = self.format_number(float(self.result.value) / 100)
                self.new_operand = True
            except ValueError:
                self.result.value = "Error"
                self.reset()

        # 正負反転ボタンが押された場合
        elif data == "±":
            try:
                current_value = float(self.result.value)
                # 符号を反転（正→負、負→正）
                self.result.value = self.format_number(-current_value)
            except ValueError:
                self.result.value = "Error"
                self.reset()

        # 画面を更新して変更を反映
        self.update()

    def format_number(self, num):
        # 数値を見やすい形式にフォーマットする関数

        # num: フォーマットする数値？
        # 戻り値: フォーマットされた数値（整数または小数）
        
        # 整数に非常に近い場合は整数として表示
        if abs(num - round(num)) < 1e-9:
            return int(round(num))
        else:
            # 非常に大きいまたは小さい数は指数表記
            if abs(num) >= 1e12 or abs(num) < 1e-6 and num != 0:
                return f"{num:.6e}" 
            return num

    def calculate(self, operand1, operand2, operator):
        # 基本的な四則演算を実行する関数
        # operand1: 第1オペランド（左側の数）
        # operand2: 第2オペランド（右側の数）
        # operator: 演算子（+, -, *, /）
        # 戻り値: 計算結果またはエラー
        
        try:
            if operator == "+":
                result = operand1 + operand2  # 足し算
            elif operator == "-":
                result = operand1 - operand2  # 引き算
            elif operator == "*":
                result = operand1 * operand2  # 掛け算
            elif operator == "/":
                if operand2 == 0:
                    return "Error"  # 0で割ることはできない
                result = operand1 / operand2  # 割り算
            else:
                result = operand2  # 演算子がない場合は第2オペランドをそのまま返す
                
            return self.format_number(result)  # 結果をフォーマットして返す
            
        except Exception:
            return "Error"  # エラーが発生した場合
            
    def calculate_scientific(self, operand, operator):
        # 科学計算を実行する関数
        # operand: 計算対象の数値
        # operator: 科学計算の種類（sin, cos, ln等）
        # 戻り値: 計算結果またはエラー
        
        try:
            if operator == "sin":
                # サイン（度数法で計算）
                return self.format_number(math.sin(math.radians(operand)))
            elif operator == "cos":
                # コサイン（度数法で計算）
                return self.format_number(math.cos(math.radians(operand)))
            elif operator == "tan":
                # タンジェント（度数法で計算）
                return self.format_number(math.tan(math.radians(operand)))
            elif operator == "ln":
                # 自然対数（正の数のみ）
                if operand <= 0: return "Error"
                return self.format_number(math.log(operand))
            elif operator == "10ˣ":
                # 10のx乗
                return self.format_number(math.pow(10, operand))
            elif operator == "eˣ":
                # eのx乗（指数関数）
                return self.format_number(math.exp(operand))
            elif operator == "|x|":
                # 絶対値
                return self.format_number(abs(operand))
                
        except Exception:
            return "Error"  # エラーが発生した場合


    def reset(self):
        # 計算状態をリセットする関数
        # 新しい計算を始めるときに呼ばれる
        
        self.operator = "+"  # 演算子を初期化
        self.operand1 = 0  # 第1オペランドを0に
        self.new_operand = True  # 新しい数字入力フラグをオン

# メイン関数

def main(page: ft.Page):
    # アプリケーションのメイン関数
    # page: Fletのページオブジェクト？
    
    page.title = "🎄 クリスマス計算機 ✨"  # ウィンドウのタイトル
    page.vertical_alignment = ft.MainAxisAlignment.CENTER  # 縦方向中央揃え
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER  # 横方向中央揃え
    
    # ページ全体の背景色
    page.bgcolor = "#FFF9F0"
    
    # 計算機アプリを作成
    calc = CalculatorApp()
    # ページに計算機を追加
    page.add(calc)


# アプリケーションを起動
ft.app(main)