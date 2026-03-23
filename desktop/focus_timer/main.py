# -*- coding: utf-8 -*-
"""
马上行动 - 专注计时器
使用 PySide6 实现圆角界面
"""
import sys
import time
import threading
import json
import os
from datetime import datetime
from ctypes import windll, byref, c_int
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                               QVBoxLayout, QHBoxLayout, QFrame, QLineEdit,
                               QScrollArea)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QPainterPath, QPalette

# 隐藏控制台窗口
try:
    windll.kernel32.FreeConsole()
except:
    pass

# 颜色定义
COLORS = {
    "bg": "#F1EEE7",        # 米色背景
    "card": "#E3DACB",      # 卡其色卡片
    "dark_text": "#141412", # 深色文字
    "light_text": "#FFFFFF",# 浅色文字
}


class RoundedButton(QPushButton):
    """圆角按钮"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._bg_color = COLORS["dark_text"]
        self._text_color = COLORS["light_text"]
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._bg_color};
                color: {self._text_color};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #2a2a28;
            }}
            QPushButton:pressed {{
                background-color: #000000;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #888888;
            }}
        """)


class RoundedFrame(QFrame):
    """圆角框架"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border-radius: 17px;
            }}
        """)


class FloatWindow(QWidget):
    """悬浮计时器窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedSize(100, 40)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 移动相关
        self._drag_position = QPoint()

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # 圆角矩形背景
        self.bg_frame = QFrame()
        self.bg_frame.setFixedSize(100, 40)
        self.bg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['dark_text']};
                border-radius: 20px;
            }}
        """)

        # 为bg_frame设置布局
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setContentsMargins(8, 0, 8, 0)
        bg_layout.setAlignment(Qt.AlignCenter)

        # 时间标签（白字透明背景，完全居中）
        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        font = QFont("Microsoft YaHei")
        font.setPointSize(17)
        font.setBold(True)
        self.time_label.setFont(font)
        self.time_label.setStyleSheet(f"color: {COLORS['light_text']}; background: transparent;")

        bg_layout.addWidget(self.time_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.bg_frame)

    def showEvent(self, event):
        """显示时移动到屏幕上方居中"""
        super().showEvent(event)
        if event.spontaneous() or not self._drag_position.isNull():
            return
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 3
        self.move(x, y)

    def paintEvent(self, event):
        pass

    def closeEvent(self, event):
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        # 双击显示主界面
        if hasattr(self, 'main_window'):
            self.main_window.showNormal()
            self.main_window.show_main_view()  # 更新界面状态
            self.main_window.activateWindow()
            self.hide()


class ReminderWindow(QWidget):
    """提醒窗口"""
    def __init__(self, minutes, parent=None):
        super().__init__(parent)
        self.main_window = parent  # 保存主窗口引用
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 380)

        # 居中
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 400) // 2, (screen.height() - 380) // 2)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 背景卡片
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg']};
                border-radius: 20px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 50, 30, 30)
        card_layout.addStretch()  # 顶部间距

        # 成功图标
        icon_label = QLabel("✓")
        icon_font = QFont("Microsoft YaHei")
        icon_font.setPointSize(32)
        icon_font.setBold(True)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            color: {COLORS['light_text']};
            background-color: {COLORS['dark_text']};
            border-radius: 40px;
            padding: 15px;
        """)
        icon_label.setFixedSize(80, 80)
        icon_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        # 完成文字
        done_label = QLabel("专注完成！")
        done_font = QFont("Microsoft YaHei")
        done_font.setPointSize(20)
        done_font.setBold(True)
        done_label.setFont(done_font)
        done_label.setAlignment(Qt.AlignCenter)
        done_label.setStyleSheet(f"color: {COLORS['dark_text']}; background: transparent; padding: 10px;")
        card_layout.addWidget(done_label, alignment=Qt.AlignCenter)

        # 时长文字
        time_label = QLabel(f"您已完成了 {minutes} 分钟的专注")
        time_font = QFont("Microsoft YaHei")
        time_font.setPointSize(12)
        time_label.setFont(time_font)
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setStyleSheet("color: #888888; background: transparent; padding: 5px;")
        card_layout.addWidget(time_label, alignment=Qt.AlignCenter)

        card_layout.addStretch()  # 中间弹性空间

        # 确认按钮
        confirm_btn = RoundedButton("太棒了，继续加油！")
        confirm_btn.setFixedSize(200, 42)
        confirm_btn.clicked.connect(self.on_confirm)
        card_layout.addWidget(confirm_btn, alignment=Qt.AlignCenter)

        main_layout.addWidget(card)

    def on_confirm(self):
        """确认按钮点击：显示主窗口并关闭弹窗"""
        if self.main_window:
            self.main_window.show()
            self.main_window.activateWindow()
        self.close()


class FocusTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("马上行动")
        self.setFixedSize(400, 380)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 变量
        self.selected_minutes = None  # 定时任务时长（分钟），不选则正计时
        self.is_running = False
        self.has_started = False  # 是否已经开始过计时
        self.start_time = None
        self.total_elapsed = 0
        self.countdown_seconds = 0  # 倒计时剩余秒数
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        # 悬浮窗
        self.float_window = None

        # 历史记录文件路径
        if getattr(sys, 'frozen', False):
            # 打包后的 exe 运行时
            self.history_file = os.path.join(os.path.dirname(sys.executable), "history.json")
        else:
            # 开发时
            self.history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
        self.history = self.load_history()

        # 是否显示历史界面
        self.showing_history = False

        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 400) // 2, (screen.height() - 380) // 2)

        self.setup_ui()

    def load_history(self):
        """加载历史记录（优先从外部文件读取，否则使用内置默认记录）"""
        # 先尝试从外部文件读取
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:
                        return data
            except:
                pass
        # 如果没有外部文件，使用内置默认记录（打包在程序中）
        return [
            {"task_name": "写代码项目", "minutes": 60, "date": "2026-03-20"},
            {"task_name": "阅读技术书籍", "minutes": 30, "date": "2026-03-19"},
            {"task_name": "学习英语", "minutes": 45, "date": "2026-03-18"}
        ]

    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass

    def save_task_record(self, elapsed_minutes):
        """保存任务记录（超过15分钟）"""
        # 不足15分钟不记录
        if elapsed_minutes < 15:
            return

        record = {
            "task_name": self.current_task if self.current_task else "马上行动",
            "minutes": elapsed_minutes,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        self.history.insert(0, record)
        self.save_history()

    def setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 背景框架
        self.bg_frame = QFrame()
        self.bg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg']};
                border-radius: 25px;
            }}
        """)

        self.bg_layout = QVBoxLayout(self.bg_frame)
        self.bg_layout.setContentsMargins(25, 5, 25, 25)
        self.bg_layout.setSpacing(15)

        # 标题栏
        self.title_bar = QFrame()
        self.title_bar.setStyleSheet("background: transparent;")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(0, 8, 0, 0)

        # 关闭按钮
        close_btn = QLabel("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setAlignment(Qt.AlignCenter)
        close_btn.setStyleSheet(f"""
            color: {COLORS['dark_text']};
            font: 14px;
            background-color: transparent;
            border-radius: 15px;
        """)
        close_btn.setCursor(Qt.PointingHandCursor)

        def on_close_clicked(e):
            self.close()
        close_btn.mousePressEvent = on_close_clicked

        def on_close_enter(e):
            close_btn.setStyleSheet(f"""
                color: {COLORS['dark_text']};
                font: 14px;
                background-color: {COLORS['card']};
                border-radius: 15px;
            """)
        close_btn.enterEvent = on_close_enter

        def on_close_leave(e):
            close_btn.setStyleSheet(f"""
                color: {COLORS['dark_text']};
                font: 14px;
                background-color: transparent;
                border-radius: 15px;
            """)
        close_btn.leaveEvent = on_close_leave

        title_bar_layout.addWidget(close_btn)

        # 标题 - 居中（使用stretch让标题真正居中）
        title_bar_layout.addStretch(1)

        title_label = QLabel("专注计时器")
        title_label.setStyleSheet(f"""
            color: {COLORS['dark_text']};
            font: bold 13px;
            background: transparent;
        """)
        title_bar_layout.addWidget(title_label, alignment=Qt.AlignCenter)

        title_bar_layout.addStretch(1)

        # 最小化按钮
        min_btn = QLabel("─")
        min_btn.setFixedSize(30, 30)
        min_btn.setAlignment(Qt.AlignCenter)
        min_btn.setStyleSheet(f"""
            color: {COLORS['dark_text']};
            font: 16px;
            background-color: transparent;
            border-radius: 15px;
        """)
        min_btn.setCursor(Qt.PointingHandCursor)

        def on_min_clicked(e):
            # 如果正在计时，显示悬浮窗并最小化主界面
            if self.is_running and self.float_window:
                self.float_window.show()
                self.showMinimized()
            else:
                self.showMinimized()
        min_btn.mousePressEvent = on_min_clicked

        def on_min_enter(e):
            min_btn.setStyleSheet(f"""
                color: {COLORS['dark_text']};
                font: 16px;
                background-color: {COLORS['card']};
                border-radius: 15px;
            """)
        min_btn.enterEvent = on_min_enter

        def on_min_leave(e):
            min_btn.setStyleSheet(f"""
                color: {COLORS['dark_text']};
                font: 16px;
                background-color: transparent;
                border-radius: 15px;
            """)
        min_btn.leaveEvent = on_min_leave

        title_bar_layout.addWidget(min_btn, alignment=Qt.AlignRight)

        self.bg_layout.addWidget(self.title_bar)

        # 任务名称输入框
        self.task_container = QFrame()
        self.task_container.setFixedHeight(50)
        self.task_container.setStyleSheet("background: transparent;")
        task_layout = QVBoxLayout(self.task_container)
        task_layout.setContentsMargins(0, 0, 0, 0)

        # 任务名称输入框（始终显示）
        self.task_input = QLineEdit()
        self.task_input.setAlignment(Qt.AlignCenter)
        input_font = QFont("Microsoft YaHei")
        input_font.setPointSize(18)
        input_font.setBold(True)
        self.task_input.setFont(input_font)
        # 设置选中文本的调色板
        palette = self.task_input.palette()
        palette.setColor(QPalette.Highlight, QColor("#C4B8A4"))
        palette.setColor(QPalette.HighlightedText, QColor(COLORS['dark_text']))
        self.task_input.setPalette(palette)
        self.task_input.setStyleSheet(f"""
            QLineEdit {{
                color: {COLORS['dark_text']};
                background-color: transparent;
                border: 2px solid #E3DACB;
                border-radius: 10px;
                padding: 8px 15px;
            }}
            QLineEdit::placeholder {{
                color: #E3DACB;
            }}
            QLineEdit::selection {{
                background-color: #C4B8A4;
                color: {COLORS['dark_text']};
            }}
        """)
        self.task_input.setMaxLength(8)
        self.task_input.returnPressed.connect(self.save_task)
        task_layout.addWidget(self.task_input)

        # 保存任务名称用于显示（默认值）
        self.current_task = "今天最重要的事是"
        self.task_input.setText(self.current_task)
        self.task_label = QLabel(self.current_task)
        self.task_label.setAlignment(Qt.AlignCenter)
        task_font = QFont("Microsoft YaHei")
        task_font.setPointSize(18)
        task_font.setBold(True)
        self.task_label.setFont(task_font)
        self.task_label.setStyleSheet(f"color: {COLORS['dark_text']}; background: transparent;")
        self.task_label.setCursor(Qt.PointingHandCursor)
        self.task_label.mouseDoubleClickEvent = self.edit_task
        # 默认显示确认状态（task_label），隐藏输入框
        self.task_input.hide()
        self.task_label.show()
        task_layout.addWidget(self.task_label)

        self.bg_layout.addWidget(self.task_container)

        # 计时显示
        self.timer_card = RoundedFrame()
        timer_layout = QVBoxLayout(self.timer_card)
        timer_layout.setContentsMargins(30, 12, 30, 12)

        self.timer_display = QLabel("00:00")
        timer_font = QFont("Microsoft YaHei")
        timer_font.setPointSize(52)
        timer_font.setBold(True)
        self.timer_display.setFont(timer_font)
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setStyleSheet("color: #141412; background: transparent;")
        timer_layout.addWidget(self.timer_display)

        self.bg_layout.addWidget(self.timer_card)

        # 时长选择
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.duration_buttons = {}
        durations = [15, 30, 45, 60]

        for dur in durations:
            btn = QPushButton(str(dur))
            btn.setFixedSize(65, 38)
            btn_font = QFont("Microsoft YaHei")
            btn_font.setPointSize(13)
            btn_font.setBold(True)
            btn.setFont(btn_font)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['card']};
                    color: {COLORS['dark_text']};
                    border: none;
                    border-radius: 15px;
                }}
                QPushButton:hover {{
                    background-color: #d0c8b8;
                }}
            """)
            btn.clicked.connect(lambda checked, d=dur: self.select_duration(d))
            self.duration_buttons[dur] = btn
            btn_layout.addWidget(btn)

        self.bg_layout.addLayout(btn_layout)

        # 开始/喝口水按钮区域
        self.btn_area_container = QFrame()
        self.btn_area_container.setStyleSheet("background: transparent;")
        btn_area_layout = QVBoxLayout(self.btn_area_container)
        btn_area_layout.setContentsMargins(0, 0, 0, 0)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # 归零按钮（圆形）
        self.reset_button = QPushButton("☰")
        self.reset_button.setFixedSize(50, 50)
        reset_font = QFont("Microsoft YaHei")
        reset_font.setPointSize(20)
        reset_font.setBold(True)
        self.reset_button.setFont(reset_font)
        self.reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['card']};
                color: {COLORS['dark_text']};
                border: none;
                border-radius: 25px;
            }}
            QPushButton:hover {{
                background-color: #d0c8b8;
            }}
        """)
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.clicked.connect(self.on_reset_button_clicked)
        buttons_layout.addWidget(self.reset_button)

        # 开始/喝口水按钮
        self.start_button = RoundedButton("马上开始")
        self.start_button.setFixedSize(240, 50)
        self.start_button.clicked.connect(self.toggle_timer)
        buttons_layout.addWidget(self.start_button)

        btn_area_layout.addLayout(buttons_layout)
        self.bg_layout.addWidget(self.btn_area_container)

        main_layout.addWidget(self.bg_frame)

        # 初始化归零按钮图标
        self.update_reset_button()

        # 移动事件
        self._drag_position = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def highlight_selected(self, selected):
        for dur, btn in self.duration_buttons.items():
            if dur == selected:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['dark_text']};
                        color: {COLORS['light_text']};
                        border: none;
                        border-radius: 15px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['card']};
                        color: {COLORS['dark_text']};
                        border: none;
                        border-radius: 15px;
                    }}
                """)

    def edit_task(self, event):
        """双击任务名称进入编辑模式"""
        self.task_label.hide()
        self.task_input.show()
        self.task_input.setFocus()
        self.task_input.selectAll()

    def save_task(self):
        """保存任务名称"""
        task_text = self.task_input.text().strip()
        if task_text:
            self.current_task = task_text
            self.task_label.setText(task_text)
            self.task_label.setStyleSheet(f"color: {COLORS['dark_text']}; background: transparent;")
            self.task_input.hide()
            self.task_label.show()
        else:
            # 如果没有输入，恢复显示输入框
            self.task_input.show()
            self.task_label.hide()

    def select_duration(self, duration):
        """选择定时时长（互斥，只能选一个）"""
        # 如果点击的是已选中的按钮，则取消选择
        if self.selected_minutes == duration:
            self.selected_minutes = None
            self.update_duration_button_style(duration, False)
            # 恢复显示为00:00
            self.timer_display.setText("00:00")
            if self.float_window:
                self.float_window.time_label.setText("00:00")
        else:
            # 取消之前选中的按钮
            for dur in self.duration_buttons:
                if dur != duration:
                    self.update_duration_button_style(dur, False)
            # 选中新的按钮
            self.selected_minutes = duration
            self.update_duration_button_style(duration, True)
            # 显示倒计时时间
            time_str = f"{duration}:00"
            self.timer_display.setText(time_str)
            if self.float_window:
                self.float_window.time_label.setText(time_str)

    def update_duration_button_style(self, duration, enabled):
        """更新时长按钮样式"""
        btn = self.duration_buttons[duration]
        if enabled:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['dark_text']};
                    color: {COLORS['light_text']};
                    border: none;
                    border-radius: 15px;
                }}
                QPushButton:hover {{
                    background-color: #2a2a28;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['card']};
                    color: {COLORS['dark_text']};
                    border: none;
                    border-radius: 15px;
                }}
                QPushButton:hover {{
                    background-color: #d0c8b8;
                }}
            """)

    def update_reset_button(self):
        """更新归零按钮"""
        if self.has_started:
            # 已开始过计时，显示"下马"
            self.reset_button.setText("下马")
            # 与开始按钮一致的样式，常规体
            self.reset_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['card']};
                    color: {COLORS['dark_text']};
                    border: none;
                    border-radius: 25px;
                    font-size: 16px;
                    font-weight: normal;
                }}
                QPushButton:hover {{
                    background-color: #d0c8b8;
                }}
            """)
        else:
            # 未开始计时，显示历史记录图标
            self.reset_button.setText("≡")
            self.reset_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['card']};
                    color: {COLORS['dark_text']};
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                }}
                QPushButton:hover {{
                    background-color: #d0c8b8;
                }}
            """)

    def on_reset_button_clicked(self):
        """归零按钮点击事件"""
        if self.has_started:
            # 已开始过计时，执行下马
            self.end_timer()
        else:
            # 没有计时，显示历史记录
            self.toggle_history_view()

    def end_timer(self):
        """下马计时，存档并回到主页"""
        # 计算已经过的时间
        elapsed_seconds = 0

        if self.selected_minutes:
            # 倒计时模式：初始秒数 - 剩余秒数
            initial_seconds = self.selected_minutes * 60
            elapsed_seconds = initial_seconds - self.countdown_seconds
        else:
            # 正计时模式
            elapsed_seconds = self.total_elapsed
            if self.start_time:
                current_elapsed = int(time.time() - self.start_time)
                elapsed_seconds += current_elapsed

        elapsed_minutes = elapsed_seconds // 60

        # 保存历史记录（超过15分钟）
        self.save_task_record(elapsed_minutes)

        # 无论是否在运行或喝口水，都重置所有计时相关变量
        self.is_running = False
        self.has_started = False  # 重置开始标志
        self.timer.stop()
        self.start_time = None
        self.total_elapsed = 0  # 始终重置为0
        self.countdown_seconds = 0

        # 重置显示
        self.timer_display.setText("00:00")
        if self.float_window:
            self.float_window.time_label.setText("00:00")

        # 重置按钮
        self.start_button.setText("马上开始")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['dark_text']};
                color: {COLORS['light_text']};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #2a2a28;
            }}
        """)

        # 恢复时长选择
        for btn in self.duration_buttons.values():
            btn.setEnabled(True)

        # 更新按钮状态
        self.update_reset_button()

        # 关闭悬浮窗
        if self.float_window:
            self.float_window.hide()

        # 显示主界面
        self.show_main_view()

        # 后台保存记录（只记录实际计时15分钟及以上的）
        if elapsed_minutes >= 15 * 60:  # 15分钟 = 900秒
            record = {
                "task_name": self.current_task if self.current_task else "马上行动",
                "minutes": self.selected_minutes,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            self.history.insert(0, record)
            self.save_history()

    def toggle_history_view(self):
        """切换历史记录视图"""
        if self.showing_history:
            self.show_main_view()
        else:
            self.show_history_view()

    def show_history_view(self):
        """显示历史记录界面"""
        self.showing_history = True
        self.update_reset_button()

        # 隐藏主界面元素
        self.title_bar.hide()
        self.task_container.hide()
        self.timer_card.hide()
        for btn in self.duration_buttons.values():
            btn.hide()
        self.btn_area_container.hide()

        # 显示历史记录
        if not hasattr(self, 'history_container') or self.history_container is None:
            self.create_history_overlay()
        self.history_container.show()

    def show_main_view(self):
        """显示主界面"""
        self.showing_history = False

        # 如果计时未运行且没有实际计时时间，重置为未开始状态
        if not self.is_running and self.total_elapsed == 0 and self.countdown_seconds == 0:
            self.has_started = False

        self.update_reset_button()

        # 隐藏历史记录
        if hasattr(self, 'history_container') and self.history_container:
            self.history_container.hide()

        # 显示主界面元素
        self.title_bar.show()
        self.task_container.show()
        self.timer_card.show()
        for btn in self.duration_buttons.values():
            btn.show()
        self.btn_area_container.show()

    def create_history_overlay(self):
        """创建历史记录覆盖层"""
        # 历史记录容器
        self.history_container = QFrame()
        self.history_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg']};
                border-radius: 17px;
            }}
        """)

        # 标题
        title_label = QLabel("历史记录")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei")
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['dark_text']}; background: transparent; padding: 10px;")

        # 列表外层容器（圆角矩形背景）
        list_container = QFrame()
        list_container.setStyleSheet("""
            QFrame {
                background-color: #E3DACB;
                border-radius: 17px;
            }
        """)
        list_container.setFixedHeight(240)

        # 历史记录列表容器（使用ScrollArea）
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 0px;
            }
            QScrollBar::handle:vertical {
                background: transparent;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        scroll_area.setWidgetResizable(True)

        # 历史记录内容
        scroll_content = QFrame()
        scroll_content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(8)  # 行间距
        content_layout.setContentsMargins(10, 5, 10, 5)  # 左右留有空间

        if not self.history:
            empty_label = QLabel("暂无历史记录")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"color: #888888; background: transparent; padding: 30px;")
            content_layout.addWidget(empty_label)
        else:
            content_layout.addSpacing(5)  # 第一条任务往下移5px
            for i, record in enumerate(self.history):
                item = self.create_history_item(record, i)
                content_layout.addWidget(item)

        content_layout.addStretch()  # 让列表项向上集中

        scroll_area.setWidget(scroll_content)

        # 将scroll_area添加到list_container
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(scroll_area)

        # 返回按钮
        back_btn = QPushButton("返回")
        back_btn.setFixedSize(100, 36)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['dark_text']};
                color: {COLORS['light_text']};
                border: none;
                border-radius: 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #2a2a28;
            }}
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.show_main_view)

        # 布局
        container_layout = QVBoxLayout(self.history_container)
        container_layout.setContentsMargins(15, 10, 15, 0)
        container_layout.addWidget(title_label)
        container_layout.addWidget(list_container, 1)  # stretch=1 让列表区域伸展
        container_layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        # 添加到主界面
        self.bg_layout.addWidget(self.history_container)
        self.history_container.hide()

    def create_history_item(self, record, index):
        """创建历史记录项（无框架列表形式）"""
        item = QWidget()
        item.setFixedHeight(28)
        item.setStyleSheet("background: transparent;")
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(15, 2, 15, 2)  # 左右留有空间

        # 任务信息
        info_label = QLabel(f"{record['task_name']} - {record['minutes']}分钟")
        info_label.setStyleSheet(f"color: {COLORS['dark_text']}; background: transparent; font-size: 14px;")
        item_layout.addWidget(info_label)

        # 日期
        date_label = QLabel(record['date'])
        date_label.setStyleSheet("color: #888888; background: transparent; font-size: 12px;")
        item_layout.addWidget(date_label)

        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #ff4444;
            }
        """)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda checked, i=index: self.delete_history_item(i))
        item_layout.addWidget(delete_btn)

        return item

    def delete_history_item(self, index):
        """删除历史记录项"""
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self.save_history()
            # 重新显示历史记录
            self.history_container.hide()
            self.create_history_overlay()
            if self.showing_history:
                self.history_container.show()

    def reset_timer(self):
        """归零：重置计时器"""
        self.is_running = False
        self.timer.stop()
        self.start_time = None
        self.total_elapsed = 0
        self.countdown_seconds = 0

        # 重置显示
        self.timer_display.setText("00:00")
        if self.float_window:
            self.float_window.time_label.setText("00:00")

        # 重置按钮文字和状态
        self.start_button.setText("马上开始")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['dark_text']};
                color: {COLORS['light_text']};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #2a2a28;
            }}
        """)

        # 恢复时长选择
        for btn in self.duration_buttons.values():
            btn.setEnabled(True)

        # 更新归零按钮图标
        self.update_reset_button()

    def toggle_timer(self):
        if not self.is_running:
            self.start_timer()
        else:
            self.pause_timer()

    def start_timer(self):
        self.is_running = True
        self.has_started = True  # 标记已开始计时

        # 如果选择了倒计时，初始化倒计时秒数（只在首次开始时初始化）
        if self.selected_minutes and self.countdown_seconds == 0:
            self.countdown_seconds = self.selected_minutes * 60
            self.start_time = None  # 倒计时不需要记录start_time
        elif not self.selected_minutes:
            # 正计时模式
            if self.start_time is None:
                # 首次开始计时
                self.start_time = time.time()

        self.start_button.setText("喝口水")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['card']};
                color: {COLORS['dark_text']};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #d0c8b8;
            }}
        """)

        # 禁用时长选择
        for btn in self.duration_buttons.values():
            btn.setEnabled(False)

        # 创建悬浮窗（不显示，等待最小化时显示）
        if not self.float_window:
            self.float_window = FloatWindow()
            self.float_window.main_window = self
        else:
            # 恢复悬浮窗正常样式
            self.float_window.bg_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['dark_text']};
                    border-radius: 20px;
                }}
            """)
            self.float_window.time_label.setStyleSheet(f"color: {COLORS['light_text']}; background: transparent;")

        # 启动计时器
        self.timer.start(1000)
        self.update_timer()  # 立即更新显示，避免延迟

        # 更新归零按钮图标
        self.update_reset_button()

    def pause_timer(self):
        self.is_running = False
        self.timer.stop()

        # 保存当前已用时间
        if self.start_time:
            current_elapsed = int(time.time() - self.start_time)
            self.total_elapsed += current_elapsed
            self.start_time = None  # 重置，以便上马时重新计算

        self.start_button.setText("上马")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['dark_text']};
                color: {COLORS['light_text']};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #2a2a28;
            }}
        """)

    def update_timer(self):
        if self.is_running:
            # 倒计时模式
            if self.selected_minutes:
                self.countdown_seconds -= 1

                if self.countdown_seconds <= 0:
                    self.reach_target_time()
                    return

                # 计算倒计时显示
                remaining = self.countdown_seconds
                hours = remaining // 3600
                mins = (remaining % 3600) // 60
                secs = remaining % 60

                if hours > 0:
                    time_part = f"{hours}:{mins:02d}"
                else:
                    time_part = f"{mins:02d}:{secs:02d}"
            else:
                # 正计时模式
                current_run = int(time.time() - self.start_time)
                elapsed = self.total_elapsed + current_run

                # 计算正计时显示
                if elapsed >= 3600:
                    hours = elapsed // 3600
                    mins = (elapsed % 3600) // 60
                    time_part = f"{hours}:{mins:02d}"
                else:
                    mins = elapsed // 60
                    secs = elapsed % 60
                    time_part = f"00:{mins:02d}"

            # 冒号闪烁效果
            if not hasattr(self, 'colon_visible'):
                self.colon_visible = True
            self.colon_visible = not self.colon_visible

            if self.colon_visible:
                time_str = time_part
            else:
                # 冒号换成空格
                time_str = time_part.replace(":", " ")

            self.timer_display.setText(time_str)

            if self.float_window:
                self.float_window.time_label.setText(time_str)

    def reach_target_time(self):
        """达到设定的定时时间，暂停计时并显示主界面"""
        # 暂停计时
        self.is_running = False
        self.timer.stop()

        # 保存当前已用时间
        elapsed_minutes = self.total_elapsed
        if self.start_time:
            current_elapsed = int(time.time() - self.start_time)
            elapsed_minutes += current_elapsed
            self.total_elapsed = elapsed_minutes
            self.start_time = None

        # 保存历史记录
        self.save_task_record(elapsed_minutes)

        # 重置计时相关变量
        self.has_started = False  # 重置开始标志
        self.total_elapsed = 0
        self.countdown_seconds = 0
        self.selected_minutes = None  # 清除定时选择

        # 恢复时长按钮显示（不选中任何按钮）
        for dur, btn in self.duration_buttons.items():
            btn.setEnabled(True)
            self.update_duration_button_style(dur, False)

        # 悬浮窗变红提醒
        if self.float_window:
            self.float_window.bg_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: #ff4444;
                    border-radius: 20px;
                }}
            """)
            self.float_window.time_label.setStyleSheet(f"""
                color: #141412;
                background: transparent;
            """)

        # 重置显示
        self.timer_display.setText("00:00")
        if self.float_window:
            self.float_window.time_label.setText("00:00")

        # 按钮显示"马上开始"
        self.start_button.setText("马上开始")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['dark_text']};
                color: {COLORS['light_text']};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #2a2a28;
            }}
        """)

        # 隐藏主窗口（如果存在悬浮窗则保持隐藏）
        if self.float_window:
            self.hide()

    def timer_complete(self):
        self.is_running = False
        self.timer.stop()
        self.start_time = None
        self.total_elapsed = 0
        self.countdown_seconds = 0
        self.has_started = False  # 重置为未开始状态
        self.selected_minutes = None  # 清除定时选择

        # 重置计时显示
        self.timer_display.setText("00:00")
        if self.float_window:
            self.float_window.time_label.setText("00:00")

        self.start_button.setText("马上开始")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['dark_text']};
                color: {COLORS['light_text']};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #2a2a28;
            }}
        """)

        # 恢复时长按钮显示（不选中任何按钮）
        for dur, btn in self.duration_buttons.items():
            btn.setEnabled(True)
            self.update_duration_button_style(dur, False)

        # 更新归零按钮为历史任务按钮
        self.update_reset_button()

        # 关闭悬浮窗
        if self.float_window:
            self.float_window.hide()
            self.float_window = None

        # 计时完成时写入历史记录
        record = {
            "task_name": self.current_task if self.current_task else "马上行动",
            "minutes": self.selected_minutes,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        self.history.insert(0, record)
        self.save_history()

        # 显示提醒窗口（不显示主界面，等待用户确认后再显示）
        self.reminder = ReminderWindow(self.selected_minutes, self)
        self.reminder.show()

    def closeEvent(self, event):
        # 如果正在计时，保存历史记录
        if self.is_running or self.has_started:
            # 计算已经过的时间
            elapsed_seconds = 0

            if self.selected_minutes:
                # 倒计时模式：初始秒数 - 剩余秒数
                initial_seconds = self.selected_minutes * 60
                elapsed_seconds = initial_seconds - self.countdown_seconds
            else:
                # 正计时模式
                elapsed_seconds = self.total_elapsed
                if self.start_time:
                    current_elapsed = int(time.time() - self.start_time)
                    elapsed_seconds += current_elapsed

            elapsed_minutes = elapsed_seconds // 60
            self.save_task_record(elapsed_minutes)

        # 关闭悬浮窗
        if self.float_window:
            self.float_window.close()
        event.accept()


if __name__ == "__main__":
    # 先列出所有窗口看看有什么
    try:
        user32 = windll.user32
        GetWindowText = user32.GetWindowTextW
        GetWindowTextLength = user32.GetWindowTextLengthW
        IsWindowVisible = user32.IsWindowVisible
        GetWindowRect = user32.GetWindowRect

        print("=== 启动前的窗口 ===")

        def enum_callback(hwnd, lParam):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buffer = c_int(length + 1)
                    GetWindowText(hwnd, byref(buffer), length + 1)
                    title = buffer.value
                    if isinstance(title, int):
                        title = ""
                    if title:
                        rect = c_int * 4
                        r = rect()
                        if GetWindowRect(hwnd, byref(r)):
                            width = r[2] - r[0]
                            height = r[3] - r[1]
                            print(f"窗口: '{title}' 大小: {width}x{height}")
            return True

        user32.EnumWindows(enum_callback, 0)
        print("=== 窗口列表结束 ===\n")
    except Exception as e:
        print(f"枚举窗口错误: {e}")

    app = QApplication(sys.argv)

    # 创建QApplication后再列一次
    try:
        user32 = windll.user32
        GetWindowText = user32.GetWindowTextW
        GetWindowTextLength = user32.GetWindowTextLengthW
        IsWindowVisible = user32.IsWindowVisible
        GetWindowRect = user32.GetWindowRect

        print("=== QApplication创建后的窗口 ===")

        def enum_callback2(hwnd, lParam):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buffer = c_int(length + 1)
                    GetWindowText(hwnd, byref(buffer), length + 1)
                    title = buffer.value
                    if isinstance(title, int):
                        title = ""
                    if title:
                        rect = c_int * 4
                        r = rect()
                        if GetWindowRect(hwnd, byref(r)):
                            width = r[2] - r[0]
                            height = r[3] - r[1]
                            print(f"窗口: '{title}' 大小: {width}x{height}")
            return True

        user32.EnumWindows(enum_callback2, 0)
        print("=== 窗口列表结束 ===\n")
    except Exception as e:
        print(f"枚举窗口错误: {e}")

    window = FocusTimer()

    # 显示主窗口后再次列出
    from PySide6.QtCore import QTimer

    def list_windows_after_show():
        try:
            user32 = windll.user32
            GetWindowText = user32.GetWindowTextW
            GetWindowTextLength = user32.GetWindowTextLengthW
            IsWindowVisible = user32.IsWindowVisible
            GetWindowRect = user32.GetWindowRect

            print("=== 主窗口显示后的窗口 ===")

            def enum_callback3(hwnd, lParam):
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLength(hwnd)
                    if length > 0:
                        buffer = c_int(length + 1)
                        GetWindowText(hwnd, byref(buffer), length + 1)
                        title = buffer.value
                        if isinstance(title, int):
                            title = ""
                        if title:
                            rect = c_int * 4
                            r = rect()
                            if GetWindowRect(hwnd, byref(r)):
                                width = r[2] - r[0]
                                height = r[3] - r[1]
                                print(f"窗口: '{title}' 大小: {width}x{height}")
                return True

            user32.EnumWindows(enum_callback3, 0)
            print("=== 窗口列表结束 ===\n")
        except Exception as e:
            print(f"枚举窗口错误: {e}")

    QTimer.singleShot(2000, list_windows_after_show)

    window.show()
    sys.exit(app.exec())
