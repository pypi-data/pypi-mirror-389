from functools import partial
import json
import os
from pprint import pprint
from typing import Any, Dict, Optional, Type, TypedDict, cast
import inspect
import signal
import sys
from astropy.time import Time as AstroTime
from . import sequencer_validator as Validator
from .sequencer import Sequencer
from datetime import date, datetime, time, timedelta
from dataclasses import dataclass
from enum import Enum, auto
import pandas as pd
from .sequencer_common import DateTimes, ValidatorContext, raDecToAltAz, getMoonAltAz

from PyQt6.QtWidgets import QApplication,QMainWindow,QFormLayout,QWidget,QVBoxLayout,QHBoxLayout,QFrame,QLabel,QComboBox,QTableWidget,QTableWidgetItem,QPushButton,QLineEdit,QButtonGroup,QSizePolicy,QFileDialog,QScrollArea,QGridLayout, QGraphicsDropShadowEffect, QMenu, QGraphicsOpacityEffect, QSlider, QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsScene, QGraphicsView, QGraphicsSceneMouseEvent, QGraphicsItem
from PyQt6.QtCore import Qt,QTimer,pyqtSignal,QPropertyAnimation,QPoint,QItemSelection,QItemSelectionModel,QSize, QObject, QRectF, QPointF
from PyQt6.QtGui import QIcon, QResizeEvent, QStandardItemModel, QStandardItem, QIntValidator, QFont, QPainter, QColor, QLinearGradient, QPolygon, QPen, QBrush
import pyqtgraph as pg
import qtawesome as qta

class AttributeDict(TypedDict):
    type: str
    category: str
    description: str
    position: int
    display_name: str
    duration: str
    validators: dict[str, Type[Validator.BaseClass]]
    timeline_name: str
    
ActionsDict = Dict[str, AttributeDict]

class InputEntry(TypedDict):
    label_widget: QWidget
    icon: QLabel
    input_widget: QWidget
    validator: Validator.BaseClass

class ViewType(Enum):
    TABLE = auto()
    TIMELINE = auto()

def getActionRegistry() -> ActionsDict:
    actions: ActionsDict = {}
    for name, func in inspect.getmembers(Sequencer, predicate=inspect.isfunction):
        if getattr(func, "__is_action_method__", False):
            # Get all attributes of the function except built-ins
            attributes = cast(AttributeDict, {k: v for k, v in func.__dict__.items() if not k.startswith('__')})
            actions[attributes['type']] = attributes
    return actions

ACTION_REGISTRY = getActionRegistry()

@dataclass
class TimelineEntry:
    telescope: int
    start_time: datetime
    end_time: datetime
    row_index: int
    details: dict

class Schedule(QObject):
    changed = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.data: list[dict] = []
        self.dates: DateTimes = DateTimes(date.today())
        self.timeline: list[TimelineEntry] = []
        self.changed.connect(self.update_timeline)
        self.durations = {action['type']: action['duration'] for action in ACTION_REGISTRY.values()}
        self.clipboard: Optional[dict] = None

    def has_clipboard(self):
        return self.clipboard is not None
    
    def get_clipboard(self):
        return self.clipboard
    
    def set_clipboard(self, data):
        self.clipboard = data

    def get(self) -> list[dict]:
        return self.data
    
    def getRow(self, row: int) -> Optional[dict]:
        if 0 <= row < len(self.data):
            return self.data[row]
        return None
    
    def getRowValue(self, row: int, key: str) -> Any:
        if 0 <= row < len(self.data):
            return self.data[row].get(key, None)
        return None
    
    def on_row_edit(self, row: int, new_data: dict):
        if 0 <= row < len(self.data):
            self.data[row] = new_data
            self.changed.emit()
        
    def on_row_value_edit(self, row: int, key: str, value: Any):
        if 0 <= row < len(self.data):
            self.data[row][key] = value
            self.changed.emit()

    def on_row_delete(self, row: int):
        if 0 <= row < len(self.data):
            del self.data[row]
            self.changed.emit()

    def on_row_insert(self, row: int, new_data: dict):
        if 0 <= row <= len(self.data):
            self.data.insert(row, new_data)
            self.changed.emit()

    def on_row_add(self, new_data: dict):
        self.data.append(new_data)
        self.changed.emit()

    def on_row_move(self, old_index: int, new_index: int):
        if 0 <= old_index < len(self.data) and 0 <= new_index < len(self.data):
            item = self.data.pop(old_index)
            self.data.insert(new_index, item)
            self.changed.emit()

    def on_row_move_up(self, row: int):
        if 0 < row < len(self.data):
            self.data[row - 1], self.data[row] = self.data[row], self.data[row - 1]
            self.changed.emit()

    def on_row_move_down(self, row: int):
        if 0 <= row < len(self.data) - 1:
            self.data[row + 1], self.data[row] = self.data[row], self.data[row + 1]
            self.changed.emit()

    def new_schedule(self):
        self.data = []
        self.changed.emit()

    def load_schedule(self, filepath: str):
        df = pd.read_csv(filepath, index_col=False)
        df = df.replace(["", " ", "nan", "NaN", "None"], pd.NA)
        for col in df.columns:
            if df[col].dtype == float and all(
                df[col].dropna().apply(lambda x: float(x).is_integer())
            ):
                df[col] = df[col].astype("Int64")
        records = [
            {k: v for k, v in row.items() if pd.notna(v)}
            for _, row in df.iterrows()
        ]
        self.data = records
        self.changed.emit()
    
    def save_schedule(self, filepath: str):
        if not filepath.lower().endswith('.csv'):
            filepath += '.csv'
        try:
            df = pd.DataFrame(self.data)
            df.to_csv(filepath, index=False)
        except Exception as e:
            print(f"Failed to save CSV: {e}")

    def getTimelineEntry(self, row_index: int) -> TimelineEntry:
        for entry in self.timeline:
            if entry.row_index == row_index:
                return entry
        raise ValueError(f"TimelineEntry not found for row index: {row_index}")

    def find_all_unique_start_times(self) -> list[datetime]:
        unique_times = set()
        for entry in self.timeline:
            unique_times.add(entry.start_time)
        return sorted(unique_times)

    def update_timeline(self):
        self.timeline = []

        current_times: dict[int, datetime] = {i+1: datetime.combine(self.dates._date, time(0,0,0)) for i in range(4)}

        for i, d in enumerate(self.data):
            telescope = d.get('telescope', 0)
            start_time = max(current_times.values()) if telescope == 0 else current_times[telescope]
            end_time = self.calculate_end_time(start_time, d)

            if end_time is None:
                raise ValueError(f"Failed to evaluate duration for {d['type']}")

            entry = TimelineEntry(
                telescope=telescope,
                start_time=start_time,
                end_time=end_time,
                details=d,
                row_index=i
            )

            self.timeline.append(entry)

            if telescope == 0:
                for t in current_times.keys():
                    current_times[t] = end_time
            else:
                current_times[telescope] = end_time

        self.timeline.sort(key=lambda x: x.start_time)


    def calculate_end_time(self, start_time: datetime, d: dict) -> Optional[datetime]:
        # if type == new then return 300 seconds later end time
        if d['type'] == "NEW":
            return start_time + timedelta(seconds=300)
        duration_expr = self.durations[d['type']]
        for k, v in d.items():
            duration_expr = duration_expr.replace(k, str(v))
        duration_expr = duration_expr.strip() or '0'
        # Safely evaluate duration
        try:
            duration_seconds = float(eval(duration_expr))
        except Exception as e:
            return None
        # Determine new end time
        if 'until_timestamp' in d and d['until_timestamp']:
            until_time = datetime.strptime(d['until_timestamp'], "%Y-%m-%d %H:%M:%S")
            new_end_time = min(start_time + timedelta(seconds=duration_seconds), max((start_time, until_time)))
        elif 'wait_timestamp' in d and d['wait_timestamp']:
            wait_time = datetime.strptime(d['wait_timestamp'], "%Y-%m-%d %H:%M:%S")
            new_end_time = max(start_time, wait_time) + timedelta(seconds=duration_seconds)
        else:
            new_end_time = start_time + timedelta(seconds=duration_seconds)
        return new_end_time

class ToastNotification(QFrame):
    """Toast notification widget that appears temporarily at the top of the window."""

    class Type(Enum):
        SUCCESS = auto()
        ERROR = auto()
        WARNING = auto()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._parent = parent
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # Icon Label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
        """)
        self.message_label.setWordWrap(False)
        
        main_layout.addWidget(self.icon_label)
        main_layout.addWidget(self.message_label)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        
        # Timer for auto-hide
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)
        
        # Initially hidden
        self.hide()
    

    def show_message(self, message: str, notification_type: Type = Type.SUCCESS):
        """Show a toast notification with the given message and type."""
        # Set icon and color based on type
        if notification_type == ToastNotification.Type.SUCCESS:
            self.icon_label.setText("✓")
            self.icon_label.setStyleSheet("""
                font-size: 22px;
                font-weight: bold;
                color: #28a745;
            """)
            icon_color = "#28a745"
        elif notification_type == ToastNotification.Type.ERROR:
            self.icon_label.setText("✖")
            self.icon_label.setStyleSheet("""
                font-size: 20px;
                font-weight: bold;
                color: #dc3545;
            """)
            icon_color = "#dc3545"
        else:  # WARNING
            self.icon_label.setText("⚠")
            self.icon_label.setStyleSheet("""
                font-size: 22px;
                font-weight: bold;
                color: #ffc107;
            """)
            icon_color = "#ffc107"
        
        # Set message
        self.message_label.setText(message)
        
        # Update container styling
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: white;
                border: 2px solid {icon_color};
                border-radius: 10px;
            }}
        """)
        
        # Position and show
        self.adjustSize()

        # Position at horizontal center, 20px from top
        x = (self._parent.width() - self.width()) // 2
        y = 20
        
        self.move(x, y)
        self.show()
        self.raise_()
        
        # Auto-hide after 3 seconds
        self.hide_timer.start(3000)

class AppContext:
    """Global application context for shared services."""
    _instance = None
    
    def __init__(self):
        self.schedule: Optional[Schedule] = None
        self.toast: Optional[ToastNotification] = None
    
    @classmethod
    def get(cls) -> 'AppContext':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = AppContext()
        return cls._instance
    
    @classmethod
    def initialize(cls, schedule: Schedule, toast: ToastNotification):
        """Initialize the context with services."""
        ctx = cls.get()
        ctx.schedule = schedule
        ctx.toast = toast
    
    @classmethod
    def getSchedule(cls) -> Schedule:
        """Get the schedule instance."""
        ctx = cls.get()
        if ctx.schedule is None:
            raise RuntimeError("AppContext not initialized. Call AppContext.initialize() first.")
        return ctx.schedule
    
    @classmethod
    def getToast(cls) -> ToastNotification:
        """Get the toast notification instance."""
        ctx = cls.get()
        if ctx.toast is None:
            raise RuntimeError("AppContext not initialized. Call AppContext.initialize() first.")
        return ctx.toast

class SettingsModal(QWidget):
    """Closed modal overlay with centered dialog."""

    closed = pyqtSignal()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        self.toast = AppContext.getToast()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Modal dialog frame
        self.dialog = QFrame()
        self.dialog.setFixedSize(1000, 700)
        self.dialog.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #dee2e6;
            }
        """)
        
        # Dialog layout
        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.setSpacing(0)
        
        # Header with close button
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("background-color: #f8f9fa; border-radius: 12px 12px 0 0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 10, 10)
        
        title_label = QLabel("Settings")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_button = QPushButton()
        close_button.setIcon(qta.icon('fa6s.xmark', color='#6c757d'))
        close_button.setIconSize(QSize(20, 20))
        close_button.setFixedSize(30, 30)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                color: "#fff";
                background-color: #e9ecef;
            }
        """)
        close_button.clicked.connect(self.close_modal)
        header_layout.addWidget(close_button)
        
        dialog_layout.addWidget(header)
        
        # Content area with sidebar and content panels
        content_container = QWidget()
        content_container.setStyleSheet("background-color: white;")
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar (250px)
        self.sidebar = SettingsSidebar()
        self.sidebar.option_clicked.connect(self._on_option_changed)
        content_layout.addWidget(self.sidebar)
        
        # Content area (750px)
        self.content = SettingsContent()
        content_layout.addWidget(self.content, stretch=1)
        
        dialog_layout.addWidget(content_container)
        
        main_layout.addWidget(self.dialog)
        
        # Animation for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.finished.connect(self._on_animation_finished)
        
        self._closing = False

        self.hide()
    
    def _on_option_changed(self, option_name: str):
        """Handle sidebar option selection."""
        self.content.show_panel(option_name)

    def paintEvent(self, event):
        """Paint semi-transparent overlay background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Semi-transparent black background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 127))  # 50% opacity
    
    def mousePressEvent(self, event):
        """Close modal when clicking outside the dialog."""
        # Check if click is outside dialog bounds
        dialog_rect = self.dialog.geometry()
        click_pos = event.pos()
        
        if not dialog_rect.contains(click_pos):
            self.close_modal()
    
    def keyPressEvent(self, event):
        """Handle ESC key to close modal."""
        if event.key() == Qt.Key.Key_Escape:
            self.close_modal()
        else:
            super().keyPressEvent(event)
    
    def show_modal(self):
        """Show the modal with fade-in animation."""
        self.resize()
        self.show()
        self.raise_()
        
        # Fade in
        self.opacity_effect.setOpacity(0)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
    
    def resize(self):
        """Resize the window. Also gets triggered when mainwindow resizes."""
        if self.parent():
            # Resize to parent size
            parent_rect = self.parent().rect()  # type: ignore
            self.setGeometry(parent_rect)
            
            # Calculate dialog size: 90% of parent, but minimum 1000x700 if possible
            parent_width = parent_rect.width()
            parent_height = parent_rect.height()
            
            # Desired size
            desired_width = 1000
            desired_height = 700
            
            # Maximum size (90% of parent)
            max_width = int(parent_width * 0.9)
            max_height = int(parent_height * 0.9)
            
            # Use minimum of desired and maximum
            dialog_width = min(desired_width, max_width)
            dialog_height = min(desired_height, max_height)
            
            self.dialog.setFixedSize(dialog_width, dialog_height)

    def close_modal(self):
        """Close the modal with fade-out animation."""
        if self._closing:
            return
        
        self._closing = True
        
        # Fade out
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()
    
    def _on_animation_finished(self):
        """Handle animation completion."""
        if self._closing:
            self.hide()
            self.closed.emit()
            self._closing = False

class SettingsSidebar(QWidget):
    """Navigation sidebar for settings modal."""
    
    option_clicked = pyqtSignal(str)  # Emits option name when clicked
    
    def __init__(self):
        super().__init__()

        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #f8f9fa;")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Navigation items
        self.buttons: dict[str, QPushButton] = {}
        self.current_selection: Optional[str] = None
        
        # Add navigation options
        options = ["Object Names"]
        
        for option_name in options:
            button = self._create_nav_button(option_name)
            self.buttons[option_name] = button
            layout.addWidget(button)
        
        layout.addStretch()
        
        # Select first option by default
        if options:
            self.select_option(options[0])
    
    def _create_nav_button(self, text: str) -> QPushButton:
        """Create a navigation button with icon and text."""
        button = QPushButton()
        button.setText(text)
        button.setFixedHeight(50)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Default style
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        
        button.clicked.connect(lambda: self._on_button_clicked(text))
        return button
    
    def _on_button_clicked(self, option_name: str):
        """Handle button click."""
        self.select_option(option_name)
        self.option_clicked.emit(option_name)
    
    def select_option(self, option_name: str):
        """Visually select an option."""
        if option_name not in self.buttons:
            return
        
        # Reset all buttons to default style
        for name, button in self.buttons.items():
            if name == option_name:
                # Selected style
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #2196f3;
                        border: none;
                        text-align: left;
                        padding-left: 20px;
                        font-size: 14px;
                        color: white;
                        font-weight: bold;
                    }
                """)
            else:
                # Default style
                button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        text-align: left;
                        padding-left: 20px;
                        font-size: 14px;
                        color: #495057;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                    }
                """)
        
        self.current_selection = option_name

class SettingsContent(QWidget):
    """Content area that switches between different settings panels."""
    
    def __init__(self):
        super().__init__()
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Store panels
        self.panels: dict[str, QWidget] = {}
        self.current_panel: Optional[QWidget] = None
        
        # Create panels
        self.panels["Object Names"] = ObjectNamesPanel()
        
        # Show default panel
        self.show_panel("Object Names")
    
    def show_panel(self, panel_name: str):
        """Switch to a different panel."""
        if panel_name not in self.panels:
            return
        
        # Remove current panel
        if self.current_panel:
            self.main_layout.removeWidget(self.current_panel)
            self.current_panel.hide()
        
        # Show new panel
        new_panel = self.panels[panel_name]
        self.main_layout.addWidget(new_panel)
        new_panel.show()
        self.current_panel = new_panel

class ObjectNamesPanel(QWidget):
    """Panel for editing the OBJECT_CATALOG."""
    
    def __init__(self):
        super().__init__()

        self.toast = AppContext.getToast()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Object Catalog")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #212529;")
        main_layout.addWidget(title)
        
        # Description
        description = QLabel("Manage astronomical objects in your catalog. RADEC can be auto filled by objectname.")
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 13px; color: #6c757d; margin-bottom: 10px;")
        main_layout.addWidget(description)
        
        # Button bar
        button_bar = QWidget()
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        add_button = QPushButton("Add Object")
        add_button.setIcon(qta.icon('fa6s.plus', color='white'))
        add_button.setIconSize(QSize(16, 16))
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_button.clicked.connect(self._on_add_object)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.setIcon(qta.icon('fa6s.trash', color='white'))
        remove_button.setIconSize(QSize(16, 16))
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_button.clicked.connect(self._on_remove_object)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        
        main_layout.addWidget(button_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Object Name", "RA", "DEC"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QHeaderView::section {
                padding-left: 15px;
                padding-right: 15px;
            }
        """)
        
        main_layout.addWidget(self.table)
        
        # Load data
        self._load_catalog()
        
        # Save button at bottom
        save_button = QPushButton("Save Changes")
        save_button.setIcon(qta.icon('fa6s.floppy-disk', color='white'))
        save_button.setIconSize(QSize(16, 16))
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        save_button.clicked.connect(self._on_save)
        
        button_container = QWidget()
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.addStretch()
        button_container_layout.addWidget(save_button)
        
        main_layout.addWidget(button_container)
    
    def _load_catalog(self):
        """Load into the table."""
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "object_catalog.json")
        
        catalog = {}
        
        # Try to load from JSON file, fall back to empty catalog if file doesn't exist
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    catalog = json.load(f)
            except Exception as e:
                if self.toast:
                    self.toast.show_message(f"Failed to load catalog: {str(e)}", ToastNotification.Type.ERROR)
                catalog = {}
        
        self.table.setRowCount(len(catalog))
        
        for row, (name, coords) in enumerate(sorted(catalog.items())):
            # Object name
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, name_item)
            
            # RA
            ra_item = QTableWidgetItem(str(coords["RA"]))
            self.table.setItem(row, 1, ra_item)
            
            # DEC
            dec_item = QTableWidgetItem(str(coords["DEC"]))
            self.table.setItem(row, 2, dec_item)
        
        self.table.resizeColumnsToContents()
    
    def _on_add_object(self):
        """Add a new row to the table."""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        # Set default values
        self.table.setItem(row_count, 0, QTableWidgetItem("NEW_OBJECT"))
        self.table.setItem(row_count, 1, QTableWidgetItem("0.0"))
        self.table.setItem(row_count, 2, QTableWidgetItem("0.0"))
        
        # Select the new row for editing
        self.table.selectRow(row_count)
        self.table.editItem(self.table.item(row_count, 0))
    
    def _on_remove_object(self):
        """Remove selected rows from the table."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        # Remove rows in reverse order to avoid index issues
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
    
    def _on_save(self):
        """Save the table data."""
        
        new_catalog = {}
        
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            ra_item = self.table.item(row, 1)
            dec_item = self.table.item(row, 2)
            
            if not name_item or not ra_item or not dec_item:
                return
            
            name = name_item.text().strip()
            if not name:
                return
            
            try:
                ra = ra_item.text()
                dec = dec_item.text()
                ra_parsed = Validator.Ra._parse(ra)
                dec_parsed = Validator.Dec._parse(dec)
                if ra_parsed is None or dec_parsed is None:
                    raise ValueError("Ra Dec invalid")
            except ValueError:
                # Show error for invalid values
                self._show_toast(f"Invalid RA/DEC values for {name}", ToastNotification.Type.ERROR)
                return
            
            new_catalog[name] = {"RA": ra, "DEC": dec}
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "object_catalog.json")

        try:
            with open(json_path, 'w') as f:
                json.dump(new_catalog, f, indent=2)

            self.toast.show_message(f"Saved {len(new_catalog)} object names to {os.path.basename(json_path)}", ToastNotification.Type.SUCCESS)
        except Exception as e:
            self.toast.show_message(f"Failed to save: {str(e)}", ToastNotification.Type.ERROR)

        # Show success message
        if self.toast:
            self.toast.show_message(f"Saved {len(new_catalog)} objects to catalog", ToastNotification.Type.SUCCESS)

    
    def _show_toast(self, message: str, toast_type: ToastNotification.Type = ToastNotification.Type.SUCCESS):
        """Show a toast notification."""
        AppContext.getToast().show_message(message, toast_type)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sequence Maker")
        self.setGeometry(0,0,1000,1360)

        self.schedule = Schedule()
        self.toast = ToastNotification(self)
        AppContext.initialize(self.schedule, self.toast)


        # Central widget in vertical layout
        central_widget = QWidget()
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)


        toolBar = ToolBar()
        self.actionPanel = ActionPanel()
        self.viewPanel = ViewPanel()

        self.viewPanel.set_view(ViewType.TIMELINE)
        toolBar.view_type_changed.connect(self.viewPanel.set_view)

        self.viewPanel.edit_requested.connect(self.actionPanel.load_entry)

        toolBar.settings_requested.connect(self.open_settings)

        root_layout.addWidget(self.actionPanel)
        self.actionPanel.setMinimumWidth(450)
        root_layout.addLayout(content_layout, stretch=1)

        content_layout.addWidget(toolBar)
        content_layout.addWidget(self.viewPanel, stretch=1)
        
        self.setCentralWidget(central_widget)

        self.settings_modal = SettingsModal(central_widget)
        self.settings_modal.closed.connect(self._on_settings_closed)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        if self.settings_modal and self.settings_modal.isVisible():
            self.settings_modal.resize()

    def open_settings(self):
        """Open the settings modal."""
        self.settings_modal.show_modal()

    def _on_settings_closed(self):
        """When modal closes this part will be triggered to maybe reload data or ui stuff"""
        pass

class ToolBar(QFrame):
    view_type_changed = pyqtSignal(ViewType)
    settings_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.schedule = AppContext.getSchedule()

        self.main_layout = QHBoxLayout()

        buttons_size = QSize(32,32)

        new_icon = qta.icon('fa6.file')
        new_button = QPushButton()
        new_button.setIcon(new_icon)
        new_button.setIconSize(buttons_size)
        new_button.clicked.connect(self.on_new)

        load_icon = qta.icon('fa6.folder-open')
        load_button = QPushButton()
        load_button.setIcon(load_icon)
        load_button.setIconSize(buttons_size)
        load_button.clicked.connect(self.on_load)

        save_icon = qta.icon('fa6.floppy-disk')
        save_button = QPushButton()
        save_button.setIcon(save_icon)
        save_button.setIconSize(buttons_size)
        save_button.clicked.connect(self.on_save)

        settings_icon = qta.icon('fa6s.gear')
        settings_button = QPushButton()
        settings_button.setIcon(settings_icon)
        settings_button.setIconSize(buttons_size)
        settings_button.clicked.connect(self.open_settings)

        view_toggle = SegmentedControl(ViewType.TIMELINE)
        view_toggle.view_type_changed.connect(self.view_type_changed.emit)

        timesShower = DateTimeGradient()

        self.main_layout.addWidget(timesShower)
        self.main_layout.addStretch()
        self.main_layout.addWidget(view_toggle)
        self.main_layout.addStretch()
        self.main_layout.addWidget(new_button)
        self.main_layout.addWidget(load_button)
        self.main_layout.addWidget(save_button)
        self.main_layout.addWidget(settings_button)

        self.setLayout(self.main_layout)

    def clear_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def refresh(self):
        self.clear_layout()

    def on_new(self):
        self.schedule.new_schedule()

    def on_load(self):
        filepath, _ = QFileDialog.getOpenFileName(
            None,
            "Open CSV",
            "",
            "CSV Files (*.csv)"
        )
        if filepath:
            self.schedule.load_schedule(filepath)

    def on_save(self):
        filepath, _ = QFileDialog.getSaveFileName(
            None,
            "Save CSV",
            "",
            "CSV Files (*.csv)"
        )
        if filepath:
            self.schedule.save_schedule(filepath)

    def open_settings(self):
        """Emit signal to request settings modal to open."""
        self.settings_requested.emit()

class ViewPanel(QFrame):
    edit_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.schedule = AppContext.getSchedule()

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.current_view = None

    def clear_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def set_view(self, view_type: ViewType):
        self.clear_layout()

        if view_type == ViewType.TIMELINE:
            self.current_view = TimelineViewer()
            self.current_view.edit_requested.connect(self.edit_requested)
        else:
            self.current_view = TableViewer()

        self.main_layout.addWidget(self.current_view)

class ActionPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.setFixedWidth(400)

        self.schedule = AppContext.getSchedule()
        self.toast = AppContext.getToast()

        # Main Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)
        self.setLayout(self.main_layout)

        # Action Picker at the top
        self.action_picker = ActionPicker()
        font = self.action_picker.font()
        font.setPointSize(18)
        self.action_picker.setFont(font)
        self.action_picker.actionTypeChanged.connect(self._on_action_type_changed)
        self.main_layout.addWidget(self.action_picker)

        # Container for dynamic content
        self.content_widget: Optional[QWidget] = None

        self.action_key: Optional[str] = None
        self.row_index: Optional[int] = None
        self.scheduleEntry: Optional[dict] = None

        # Add action buttons at bottom
        self.button_container = QWidget()
        button_layout = QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        self.insert_button = QPushButton("Insert New")
        self.insert_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.insert_button.clicked.connect(self._on_insert_clicked)
        self.insert_button.hide() # Hidden by default

        self.save_button = QPushButton("Save Changes")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.hide()  # Hidden by default

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.cancel_button.hide()  # Hidden by default

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.insert_button)
        button_layout.addWidget(self.save_button)

        self.main_layout.addWidget(self.button_container)

        self.refresh()


    def _on_action_type_changed(self, action_key: str):
        self.action_key = action_key
        self.refresh()

    def clear_content(self):
        if self.content_widget:
            self.main_layout.removeWidget(self.content_widget)
            self.content_widget.deleteLater()
            self.content_widget = None

    def refresh(self):
        self.clear_content()

        # Update button visibility based on action selection and edit mode
        if self.action_key and self.row_index is None:
            # Action selected, not editing -> show insert button
            self.insert_button.show()
            self.save_button.hide()
            self.cancel_button.hide()
        elif self.action_key and self.row_index is not None:
            # Action selected, editing -> show save/cancel buttons
            self.insert_button.hide()
            self.save_button.show()
            self.cancel_button.show()
        else:
            # No action selected -> hide all buttons
            self.insert_button.hide()
            self.save_button.hide()
            self.cancel_button.hide()

        if not self.action_key:
            label = QLabel("Select an action from the dropdown above.")
            label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_widget = label
            self.main_layout.addWidget(self.content_widget)
            return
        
        if self.action_key not in ACTION_REGISTRY:
            label = QLabel(f"Action '{self.action_key}' not found in registry.")
            label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_widget = label
            self.main_layout.addWidget(self.content_widget)
            return

        attrs = ACTION_REGISTRY[self.action_key]

        timelineEntry = self.schedule.getTimelineEntry(self.row_index) if self.row_index is not None else None

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        content.setLayout(content_layout)

        # Show edit text if editing
        if self.row_index is not None:
            edit_label = QLabel(f"Editing Entry #{self.row_index}")
            edit_label.setStyleSheet("""
                background-color: #fff3cd;
                color: #856404;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                border: 1px solid #ffeaa7;
            """)
            content_layout.addWidget(edit_label)


        self.input_form = InputForm(attrs, self.scheduleEntry)
        content_layout.addWidget(self.input_form)

        action_description = ActionDescription(attrs['description'])
        content_layout.addWidget(action_description)

        if self.action_key == 'OBSERVE':
            observe_graph = ObserveGraph(self.input_form.context, timelineEntry)
            content_layout.addWidget(observe_graph)

        content_layout.addStretch()

        self.content_widget = content
        self.main_layout.addWidget(self.content_widget)

    def load_entry(self, row_index: int):
        """Load an existing entry for editing."""
        if 0 <= row_index < len(self.schedule.data):
            entry_data = self.schedule.data[row_index]
            
            self.row_index = row_index
            self.action_key = entry_data.get('type')
            self.scheduleEntry = entry_data.copy()
            
            self.action_picker.setCurrentAction(self.action_key)
            
            self.refresh()
            
        else:
            print(f"Invalid row index: {row_index}")

    def _on_insert_clicked(self):
        """Handle insert new entry."""
        if not self.input_form:
            return
        
        if not self.input_form.validate_all():
            self._show_validation_error()
            return
        
        new_entry = self.input_form.context.get_full_all()
        new_entry['type'] = self.action_key
        new_entry['done'] = Validator.StatusValue.WAITING
        
        self._show_toast(f"Inserted new {self.action_key} entry")
        self.schedule.on_row_add(new_entry)
        
        self.scheduleEntry = None
        self.refresh()

    def _on_save_clicked(self):
        """Handle save changes to existing entry."""
        if self.row_index is None or not self.input_form:
            return
        
        if not self.input_form.validate_all():
            self._show_validation_error()
            return
        
        updated_entry = self.input_form.context.get_full_all()
        updated_entry['type'] = self.action_key
        updated_entry['done'] = self.scheduleEntry.get('done', Validator.StatusValue.WAITING) # type: ignore
        
        self.schedule.on_row_edit(self.row_index, updated_entry)
        
        self._show_toast(f"Saved changes to entry #{self.row_index}")

        self._reset_to_insert_mode()

    def _on_cancel_clicked(self):
        """Cancel editing and return to insert mode."""
        self._show_toast("Edit cancelled")
        self._reset_to_insert_mode()

    def _reset_to_insert_mode(self):
        """Reset panel to insert mode."""
        self.row_index = None
        self.scheduleEntry = None
        
        self.refresh()

    def _show_validation_error(self):
        """Show validation error feedback."""
        # Shake animation for button
        button = self.save_button if self.row_index is not None else self.insert_button
        original_text = button.text()

        button.setText("Fix Invalid")
        button.adjustSize()

        button.setDisabled(True)
        QTimer.singleShot(1500, lambda: (button.setText(original_text), button.adjustSize(), button.setDisabled(False)))

        original_geometry = button.geometry()
        
        self._shake_anim = QPropertyAnimation(button, b"geometry")
        self._shake_anim.setDuration(500)
        self._shake_anim.setKeyValueAt(0, original_geometry)
        self._shake_anim.setKeyValueAt(0.1, original_geometry.translated(-20, 0))
        self._shake_anim.setKeyValueAt(0.2, original_geometry.translated(00, 0))
        self._shake_anim.setKeyValueAt(0.3, original_geometry.translated(-20, 0))
        self._shake_anim.setKeyValueAt(0.4, original_geometry.translated(00, 0))
        self._shake_anim.setKeyValueAt(0.5, original_geometry)
        self._shake_anim.setEndValue(original_geometry)
        self._shake_anim.start()

    def _show_toast(self, message: str, toast_type: ToastNotification.Type = ToastNotification.Type.SUCCESS):
        """Show a toast notification."""
        AppContext.getToast().show_message(message, toast_type)

class InputForm(QWidget):
    """Manages form fields, validation icons, and input widgets for action parameters."""

    # emit a signal when an input changes
    value_changed = pyqtSignal(str, bool) # (field name, is valid)

    def __init__(
            self,
            attrs: AttributeDict,
            scheduleEntry: Optional[dict] = None
    ):
        super().__init__()
        self.attrs = attrs
        self.schedule = AppContext.getSchedule()
        self.scheduleEntry: Optional[dict] = scheduleEntry

        self.context = ValidatorContext(dates=self.schedule.dates)

        self.inputs: dict[str, InputEntry] = {}

        self._create_validators()
        self._build_layout()

    def _create_validators(self) -> None:
        """Create validators and associated widgets for each attribute."""

        for name, validator_class in self.attrs['validators'].items():
            # Validation icon
            icon = QLabel()
            icon.setFixedWidth(20)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Initial value
            value = self.scheduleEntry.get(name) if self.scheduleEntry else None

            # Create validator instance
            validator = validator_class(name=name, value=value, context=self.context)

            # Create label with text and icon
            label_widget = self._create_label_widget(name, icon)

            # Create input widget with change handler
            input_widget = validator.input_widget(lambda name=name: self._handle_input_change(name))

            # Store entry
            self.inputs[name] = InputEntry(
                icon=icon,
                validator=validator,
                label_widget=label_widget,
                input_widget=input_widget
            )

    def _create_label_widget(self, name: str, icon: QLabel) -> QWidget:
        """Create a label widget with text and an associated icon."""
        label = QLabel(name)
        label.setStyleSheet("font-weight: normal;")

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(icon)

        return container

    def _build_layout(self) -> None:
        """Build the form layout with all input fields."""
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form_layout.setSpacing(10)

        for entry in self.inputs.values():
            entry['label_widget'].setFixedWidth(150)
            entry['label_widget'].setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Preferred
            )

            entry['input_widget'].setFixedWidth(250)
            entry['input_widget'].setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred
            )

            form_layout.addRow(entry['label_widget'], entry['input_widget'])

        self.setLayout(form_layout)

    def _handle_input_change(self, name: str) -> None:
        """Handle input changes by emitting a signal."""
        is_valid = self.inputs[name]['validator'].isValid()
        self._update_validation_icon(name, is_valid)
        self.value_changed.emit(name, is_valid)

    def _update_validation_icon(self, name: str, is_valid: bool) -> None:
        """Update the validation icon for a specific input field."""
        if name not in self.inputs:
            return

        icon = self.inputs[name]['icon']

        if is_valid:
            icon.setStyleSheet("color: #28a745; font-weight: bold;")
            icon.setText("✔")
            icon.setToolTip("Valid input")
        else:
            icon.setStyleSheet("color: #dc3545; font-weight: bold;")
            icon.setText("✖")
            icon.setToolTip(f"Invalid input {self.inputs[name]['validator'].expected()}")

    def validate_all(self) -> bool:
        """Validate all input fields and update their icons."""
        all_valid = True
        
        for name, entry in self.inputs.items():
            is_valid = entry['validator'].isValid()
            self._update_validation_icon(name, is_valid)
            if not is_valid:
                all_valid = False
        return all_valid

class ActionDescription(QWidget):
    """Displays the description of the selected action."""

    def __init__(self, description: str):
        super().__init__()
        
        label = QLabel(description)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        label.setStyleSheet("font-size: 14px;")

        label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        self.setLayout(layout)

class ObserveGraph(QWidget):
    """Real-time altitude graph for 'OBSERVE' action."""

    def __init__(
            self,
            context: ValidatorContext,
            timeline_entry: Optional[TimelineEntry]
    ):
        super().__init__()
        self.schedule = AppContext.getSchedule()
        self.context = context
        self.timeline_entry = timeline_entry

        # Create the plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.setInteractive(False)
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.setFixedHeight(250)

        # Store plot items for later updates
        self.altitude_moon_curve = None
        self.altitude_curve = None
        self.start_marker = None
        self.end_marker = None
        self.min_limit_line = None
        self.max_limit_line = None
        self.observable_regions = []
        self.twilight_regions = []

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        # Configure axes
        self._configure_axes()

        # Subscribe to context changes
        self.context.watch('RA', self._on_coordinate_changed)
        self.context.watch('DEC', self._on_coordinate_changed)

        self.context.watch('telescope', self._on_telescope_changed)

        self.context.watch('exp_time', self._on_timing_changed)
        self.context.watch('exp_number', self._on_timing_changed)
        self.context.watch('until_timestamp', self._on_timing_changed)

        # Connect to schedule changes
        self.schedule.changed.connect(self._on_schedule_changed)

        # Initial draws
        self._on_coordinate_changed()
        self._on_telescope_changed()
        self._on_timing_changed()
        self._on_schedule_changed()

    def _on_coordinate_changed(self, *args) -> None:
        """RA or DEC changed -> Update curve and observable range."""
        ra = self.context.get('RA')
        dec = self.context.get('DEC')

        ra_hours = self._validate_and_parse_ra(ra)
        dec_degrees = self._validate_and_parse_dec(dec)

        if ra_hours is not None and dec_degrees is not None:
            self._draw_altitude_curve(ra_hours, dec_degrees)
            self._update_observable_range_if_possible()

    def _on_telescope_changed(self, *args) -> None:
        """Telescope changed -> Update limits and observable range."""
        telescope_idx = self.context.get('telescope')
        if telescope_idx is not None:
            self._draw_horizon_limits(telescope_idx)
            self._update_observable_range_if_possible()
        
    def _on_timing_changed(self, *args) -> None:
        """Timing params changed -> Update markers and observable range."""
        start_time, end_time = self._calculate_times()
        self._draw_time_markers(start_time, end_time)
        self._update_observable_range_if_possible()


    def _on_schedule_changed(self) -> None:
        """Schedule changed -> Redraw static elements."""
        self._draw_twilight_zones()
        self._add_legend()
        self._draw_moon_curve()
        # Also trigger timing changes
        self._on_timing_changed()

    def _update_observable_range_if_possible(self) -> None:
        """Only update observable range if we have all required data."""
        telescope_idx = self.context.get('telescope')
        ra = self.context.get('RA')
        dec = self.context.get('DEC')

        if telescope_idx is None:
            return
        
        ra_hours = self._validate_and_parse_ra(ra)
        dec_degrees = self._validate_and_parse_dec(dec)

        if ra_hours is None or dec_degrees is None:
            return

        self._highlight_observable_range(ra_hours, dec_degrees, telescope_idx)

    def _calculate_times(self) -> tuple[datetime, Optional[datetime]]:
        """Calculate start and end times for the observation period."""
        start_time = self.schedule.dates.astronomical_dark_start
        if self.timeline_entry:
            start_time = self.timeline_entry.start_time
        else:
            start_time = max([entry.end_time for entry in self.schedule.timeline if entry.telescope == self.context.get('telescope')], default=start_time)
        
        d = self.context._full_values
        d['type'] = "OBSERVE"
        end_time = self.schedule.calculate_end_time(start_time, d)

        return start_time, end_time

    def _generate_time_points(self, start: datetime, end: datetime, interval_minutes: int = 5) -> list[datetime]:
        """Generate time points between start and end at specified intervals."""
        step = timedelta(minutes=interval_minutes)
        num_points = int((end - start).total_seconds() / step.total_seconds()) + 1
        return [start + i * step for i in range(num_points)]
    
    def _calculate_altazs(self, ra_hours: float, dec_degrees: float, timestamps: list[datetime]) -> list[tuple[float, float]]:
        """Calculate altitudes for given RA/DEC at specified times."""
        altitudes = []
        for t in timestamps:
            astro_time = AstroTime(t)
            alt, az = raDecToAltAz(ra_hours, dec_degrees, astro_time)  # type: ignore
            altitudes.append((alt, az))

        return altitudes
    
    def _calculate_moon_altazs(self, timestamps: list[datetime]) -> list[tuple[float, float]]:
        """Calculate altitudes for moon at specified times."""
        altitudes = []
        for t in timestamps:
            astro_time = AstroTime(t)
            alt, az = getMoonAltAz(astro_time)
            altitudes.append((alt, az))
        return altitudes

    def _configure_axes(self) -> None:
        """Configure plot axes with labels and ranges."""
        # Y axis (altitude)
        self.plot_widget.setLabel('left', 'Altitude', units='°')
        self.plot_widget.setYRange(0, 90, padding=0) # type: ignore

        altitude_axis = AltitudeAxisItem(orientation='left')
        self.plot_widget.setAxisItems({'left': altitude_axis})

        self.plot_widget.setLabel('bottom', 'Time')

        # X axis (time)
        dates = self.schedule.dates
        start_time = dates.civil_dark_start - timedelta(hours=1)
        end_time = dates.civil_dark_end + timedelta(hours=1)

        x_min = self._datetime_to_plot_x(start_time)
        x_max = self._datetime_to_plot_x(end_time)

        # Custom time axis formatting
        time_axis = TimeAxisItem(start_time, end_time, orientation='bottom')
        self.plot_widget.setAxisItems({'bottom': time_axis})

        self.plot_widget.setXRange(x_min, x_max, padding=0) # type: ignore

        self.plot_widget.enableAutoRange(enable=False)

    #########################
    #                       #
    #   Conversion Methods  #
    #                       #
    #########################

    def _datetime_to_plot_x(self, dt: datetime) -> float:
        """Convert datetime to plot x-coordinate (timestamp)."""
        return dt.timestamp()

    def _plot_x_to_datetime(self, x: float) -> datetime:
        """Convert plot x-coordinate (timestamp) back to datetime."""
        return datetime.fromtimestamp(x)

    def _validate_and_parse_ra(self, ra: Any) -> Optional[float]:
        """Parse and validate RA value."""
        ra_parsed = Validator.Ra._parse(ra)
        return float(ra_parsed) if ra_parsed is not None else None

    def _validate_and_parse_dec(self, dec: Any) -> Optional[float]:
        """Parse and validate DEC value."""
        dec_parsed = Validator.Dec._parse(dec)
        return float(dec_parsed) if dec_parsed is not None else None

    #####################
    #                   #
    #   Drawing Methods #
    #                   #
    #####################

    def _draw_moon_curve(self):
        """Draw the altitude curve on the plot for the moon."""

        dates = self.schedule.dates
        start_time = dates.civil_dark_start - timedelta(hours=1)
        end_time = dates.civil_dark_end + timedelta(hours=1)

        timestamps = self._generate_time_points(start_time, end_time)
        altazs = self._calculate_moon_altazs(timestamps)
        altitudes = [alt for alt,az in altazs]

        x_values = [self._datetime_to_plot_x(t) for t in timestamps]

        if self.altitude_moon_curve:
            self.plot_widget.removeItem(self.altitude_moon_curve)

        pen = pg.mkPen(color="#516F7B", width=2)
        self.altitude_moon_curve = self.plot_widget.plot(
            x=x_values,
            y=altitudes,
            pen=pen,
            name="Altitude Moon Curve"
        )


    def _draw_altitude_curve(self, ra_hours: float, dec_degrees: float):
        """Draw the altitude curve on the plot."""

        dates = self.schedule.dates
        start_time = dates.civil_dark_start - timedelta(hours=1)
        end_time = dates.civil_dark_end + timedelta(hours=1)

        timestamps = self._generate_time_points(start_time, end_time)
        altazs = self._calculate_altazs(ra_hours, dec_degrees, timestamps)
        altitudes = [alt for alt,az in altazs]

        x_values = [self._datetime_to_plot_x(t) for t in timestamps]

        if self.altitude_curve:
            self.plot_widget.removeItem(self.altitude_curve)

        pen = pg.mkPen(color='#3A86FF', width=2)
        self.altitude_curve = self.plot_widget.plot(
            x=x_values,
            y=altitudes,
            pen=pen,
            name="Altitude Curve"
        )

    def _draw_time_markers(self, start_time: datetime, end_time: Optional[datetime]):
        """Draw start and end time markers on the plot."""
        if self.start_marker:
            self.plot_widget.removeItem(self.start_marker)
        if self.end_marker:
            self.plot_widget.removeItem(self.end_marker)

        start_x = self._datetime_to_plot_x(start_time)
        pen_start = pg.mkPen('#6A4C93', width=1, style=pg.QtCore.Qt.PenStyle.DashLine)
        self.start_marker = pg.InfiniteLine(
            pos=start_x,
            angle=90,
            pen=pen_start,
            label="Start",
            labelOpts={'position': 0.9, 'color': '#6A4C93', 'fill': '#FFFFFF'}
        )
        self.plot_widget.addItem(self.start_marker)

        if end_time is None:
            return

        end_x = self._datetime_to_plot_x(end_time)
        pen_end = pg.mkPen('#FF6F61', width=1, style=pg.QtCore.Qt.PenStyle.DashLine)
        self.end_marker = pg.InfiniteLine(
            pos=end_x,
            angle=90,
            pen=pen_end,
            label="End",
            labelOpts={'position': 0.9, 'color': '#FF6F61', 'fill': '#FFFFFF'}
        )
        self.plot_widget.addItem(self.end_marker)

    def _draw_horizon_limits(self, telescope_idx: int):
        """Draw horizontal lines for telescope horizon limits."""
        
        if self.min_limit_line:
            self.plot_widget.removeItem(self.min_limit_line)
        if self.max_limit_line:
            self.plot_widget.removeItem(self.max_limit_line)
        
        telescope_config = Validator.TELESCOPES[telescope_idx]
        min_alt = telescope_config.TELESCOPE.MIN_ALTITUDE
        max_alt = telescope_config.TELESCOPE.MAX_ALTITUDE

        pen_min = pg.mkPen("#3A2909", width=1, style=pg.QtCore.Qt.PenStyle.DotLine)
        self.min_limit_line = pg.InfiniteLine(
            pos=min_alt,
            angle=0,
            pen=pen_min,
            label="Min Altitude",
            labelOpts={'position': 0.9, 'color': '#FFA500', 'fill': '#FFFFFF'}
        )
        self.plot_widget.addItem(self.min_limit_line)

        pen_max = pg.mkPen("#3F3109", width=1, style=pg.QtCore.Qt.PenStyle.DotLine)
        self.max_limit_line = pg.InfiniteLine(
            pos=max_alt,
            angle=0,
            pen=pen_max,
            label="Max Altitude",
            labelOpts={'position': 0.9, 'color': '#32CD32', 'fill': '#FFFFFF'}
        )
        self.plot_widget.addItem(self.max_limit_line)
    
    def _draw_twilight_zones(self) -> None:
        """Shade twilight zones on the plot."""
        for region in self.twilight_regions:
            self.plot_widget.removeItem(region)
        self.twilight_regions.clear()

        dates = self.schedule.dates

        evening_start = self._datetime_to_plot_x(dates.civil_dark_start)
        evening_end = self._datetime_to_plot_x(dates.astronomical_dark_start)
        evening_region = pg.LinearRegionItem(
            values=(evening_start, evening_end),
            brush=pg.mkBrush(QColor(200, 200, 255, 50)),
            movable=False
        )
        self.plot_widget.addItem(evening_region)
        self.twilight_regions.append(evening_region)

        morning_start = self._datetime_to_plot_x(dates.astronomical_dark_end)
        morning_end = self._datetime_to_plot_x(dates.civil_dark_end)
        morning_region = pg.LinearRegionItem(
            values=(morning_start, morning_end),
            brush=pg.mkBrush(QColor(200, 200, 255, 50)),
            movable=False
        )
        self.plot_widget.addItem(morning_region)
        self.twilight_regions.append(morning_region)

    def _highlight_observable_range(
            self,
            ra_hours: float,
            dec_degrees: float,
            telescope_idx: int
        ) -> None:
        """Highlight the observable range on the plot."""
        for region in self.observable_regions:
            self.plot_widget.removeItem(region)
        self.observable_regions = []
        
        telescope_config = Validator.TELESCOPES[telescope_idx]
        min_alt = telescope_config.TELESCOPE.MIN_ALTITUDE
        max_alt = telescope_config.TELESCOPE.MAX_ALTITUDE

        dates = self.schedule.dates
        start_time = dates.civil_dark_start - timedelta(hours=1)
        end_time = dates.civil_dark_end + timedelta(hours=1)

        if end_time is None:
            return
        
        timestamps = self._generate_time_points(start_time, end_time)
        altazs = self._calculate_altazs(ra_hours, dec_degrees, timestamps)
        altitudes = [alt for alt,az in altazs]

        observable_segments = []
        segment_start = None

        for i, alt in enumerate(altitudes):
            # Check if altitude is within limits
            is_observable = min_alt <= alt
            
            if is_observable and segment_start is None:
                segment_start = i
                
            elif not is_observable and segment_start is not None:
                observable_segments.append((segment_start, i))
                segment_start = None

        if segment_start is not None:
            observable_segments.append((segment_start, len(timestamps)))

        for seg_start_idx, seg_end_idx in observable_segments:
            segment_times = timestamps[seg_start_idx: seg_end_idx]
            segment_alts = altitudes[seg_start_idx: seg_end_idx]

            x_values = [self._datetime_to_plot_x(t) for t in segment_times]
            y_values = [min(alt, max_alt) for alt in segment_alts]

            fill_item = pg.PlotDataItem(
                x=x_values,
                y=y_values,
                pen=None,
                brush=pg.mkBrush(QColor(100, 255, 100, 100)),
                fillLevel=min_alt  # ✅ Fill down to min_alt
            )

            self.plot_widget.addItem(fill_item)
            self.observable_regions.append(fill_item)
        
    def _add_legend(self) -> None:
        """Add a legend to the plot."""
        legend = pg.LegendItem((100, 60), offset=(70, 20))
        legend.setParentItem(self.plot_widget.graphicsItem())

    def clear_plot(self) -> None:
        """Clear all plot items."""
        if self.altitude_moon_curve:
            self.plot_widget.removeItem(self.altitude_moon_curve)
            self.altitude_moon_curve = None
        if self.altitude_curve:
            self.plot_widget.removeItem(self.altitude_curve)
            self.altitude_curve = None
        if self.start_marker:
            self.plot_widget.removeItem(self.start_marker)
            self.start_marker = None
        if self.end_marker:
            self.plot_widget.removeItem(self.end_marker)
            self.end_marker = None
        if self.min_limit_line:
            self.plot_widget.removeItem(self.min_limit_line)
            self.min_limit_line = None
        if self.max_limit_line:
            self.plot_widget.removeItem(self.max_limit_line)
            self.max_limit_line = None
        for region in self.observable_regions:
            self.plot_widget.removeItem(region)
        self.observable_regions.clear()
        for region in self.twilight_regions:
            self.plot_widget.removeItem(region)
        self.twilight_regions.clear()

class AltitudeAxisItem(pg.AxisItem):
    """Custom axis item for displaying altitude labels."""
    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            strings.append(f"{v:.0f}°")
        return strings
    
    def tickValues(self, minVal, maxVal, size):
        """Generate ticks at every 20 degrees."""
        ticks = []
        current = (minVal // 20) * 20
        if current < minVal:
            current += 20
        while current <= maxVal:
            ticks.append(current)
            current += 20
        return [(20, ticks)]

class TimeAxisItem(pg.AxisItem):
    """Custom axis item for displaying time labels."""
    def __init__(self, start_time: datetime, end_time: datetime, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = start_time
        self.end_time = end_time

    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            dt = datetime.fromtimestamp(v)
            strings.append(dt.strftime("%H"))
        return strings

    def tickValues(self, minVal, maxVal, size):
        """Generate ticks at even hours only."""
        # Convert timestamps to datetime
        start_dt = datetime.fromtimestamp(minVal)
        end_dt = datetime.fromtimestamp(maxVal)
        
        # Round start to next even hour
        start_hour = start_dt.hour
        if start_hour % 2 != 0:
            start_hour += 1
        
        # Create first tick at even hour
        first_tick = start_dt.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        if first_tick < start_dt:
            first_tick += timedelta(hours=2)
        
        # Generate ticks every 2 hours
        ticks = []
        current = first_tick
        
        while current <= end_dt:
            ticks.append(current.timestamp())
            current += timedelta(hours=2)
        
        return [(2 * 3600, ticks)]

























class ClickableCellWidget(QFrame):
    edit_requested = pyqtSignal(int)           # row_index
    copy_requested = pyqtSignal(int)           # row_index
    delete_requested = pyqtSignal(int)         # row_index
    insert_above_requested = pyqtSignal(int)   # row_index
    insert_below_requested = pyqtSignal(int)   # row_index
    insert_copied_above_requested = pyqtSignal(int)  # row_index
    insert_copied_below_requested = pyqtSignal(int)  # row_index

    def __init__(self, data: TimelineEntry):
        super().__init__()
        self.data = data
        self.schedule = AppContext.getSchedule()
        self.setObjectName("cellFrame")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(8, 3, 8, 3)

        # Set normal stylesheet initially
        self._set_normal_stylesheet()

        # Build the content
        self._build_content()

        # Optional shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        self.setToolTip(f"{self.data.start_time.strftime('%H:%M:%S')} - {self.data.end_time.strftime('%H:%M:%S')}")

    def set_copied_highlight(self, is_copied: bool):
        """Set whether this cell should be highlighted as copied."""
        self._set_copied_stylesheet()

    def _set_normal_stylesheet(self):
        self.setStyleSheet("""
            QFrame#cellFrame {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 8px;
            }
            QFrame#cellFrame:hover {
                background-color: #e2e6ea;
                border: 1px solid #adb5bd;
            }
        """)
    
    def _set_copied_stylesheet(self):
        self.setStyleSheet("""
            QFrame#cellFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
            }
            QFrame#cellFrame:hover {
                background-color: #ffe8a1;
                border: 2px solid #ffb300;
            }
        """)

    def _build_content(self):
        # Status
        status = self.data.details['done']
        if status == Validator.StatusValue.WAITING:
            color = "#ffc107"
            symbol = "⧗"
        elif status == Validator.StatusValue.DONE:
            color = "#28a745"
            symbol = "✔"
        elif status == Validator.StatusValue.FAILED:
            color = "#dc3545"
            symbol = "✘"
        elif status == Validator.StatusValue.BUSY:
            color = "#007bff"
            symbol = "⧖"

        done_label = QLabel(symbol)
        done_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        done_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")

        # Title
        title_label = QLabel(self.parse_timeline_name(self.data.details))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold;")

        # Duration
        # dur_label = QLabel(self.data.end_time.strftime("%H:%M:%S"))

        self.main_layout.addWidget(done_label)
        self.main_layout.addWidget(title_label)
        # self.main_layout.addWidget(dur_label)

    def parse_timeline_name(self, details: dict) -> str:
        if details['type'] == "NEW":
            timeline_name = "NEW"
        else:
            timeline_name = ACTION_REGISTRY[details['type']]['timeline_name']
            for k, v in details.items():
                timeline_name = timeline_name.replace(f"<{k}>", str(v))
        return timeline_name
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        menu = QMenu(self)

        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #adb5bd;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #e2e6ea;
            }
            QMenu::separator {
                height: 1px;
                background-color: #ced4da;
                margin: 5px 10px;
            }
        """)

        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.data.row_index)) # type: ignore
        
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(lambda: self.copy_requested.emit(self.data.row_index)) # type: ignore
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.data.row_index)) # type: ignore
        
        menu.addSeparator()
        
        insert_above_action = menu.addAction("Insert Above")
        insert_above_action.triggered.connect(lambda: self.insert_above_requested.emit(self.data.row_index)) # type: ignore
        
        insert_below_action = menu.addAction("Insert Below")
        insert_below_action.triggered.connect(lambda: self.insert_below_requested.emit(self.data.row_index)) # type: ignore
        
        # (only if clipboard has data)
        if self.schedule.has_clipboard():
            menu.addSeparator()
            
            insert_copied_above_action = menu.addAction("Insert Copied Above")
            insert_copied_above_action.triggered.connect(  # type: ignore
                lambda: self.insert_copied_above_requested.emit(self.data.row_index)
            )
            
            insert_copied_below_action = menu.addAction("Insert Copied Below")
            insert_copied_below_action.triggered.connect(  # type: ignore
                lambda: self.insert_copied_below_requested.emit(self.data.row_index)
            )
        
        # Show menu at cursor position
        menu.exec(event.globalPos())

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.data.start_time >= self.data.end_time:
            # Draw a red triangle on the left edge
            triangle_size = 12
            offset = 0  # outside the card
            points = [
                QPoint(offset, self.height() // 2 - triangle_size),
                QPoint(offset, self.height() // 2 + triangle_size),
                QPoint(offset + triangle_size, self.height() // 2)
            ]
            triangle = QPolygon(points)
            painter.setBrush(QColor("#dc3545"))  # red warning color
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(triangle)

class TimelineViewer1(QWidget):
    edit_requested = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.schedule = AppContext.getSchedule()
        self.schedule.changed.connect(self.refresh)
        self.copied_row_index: Optional[int] = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()

        self.grid_layout = QGridLayout(container)
        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.refresh()

        self.grid_layout.setRowStretch(self.grid_layout.rowCount()+1, 1)

    def clear_layout(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def refresh(self):
        self.clear_layout()
        self.current_rows = {}
        self.current_row = 0
        self.populate_header()
        self.populate_body()

    def populate_header(self):
        for i in range(0, 4):
            l = QLabel("Telescope: " + str(i+1))
            l.setStyleSheet("font-weight: bold;")
            self.grid_layout.addWidget(l, 0, i+1, alignment=Qt.AlignmentFlag.AlignCenter)
            self.current_rows[i+1] = 0
        self.grid_layout.addWidget(QLabel("Sun Telescope"), 0, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        self.current_rows[5] = 0

    def populate_body(self):
        unique_times = []
        for index, entry in enumerate(self.schedule.timeline):
            past_value = self.current_row
            if entry.telescope == 0:
                self.current_row += 1
                for i in range(1, 5):
                    widget = self._create_clickableCellWidget(entry)
                    
                    self.grid_layout.addWidget(widget, self.current_row, i, alignment=Qt.AlignmentFlag.AlignCenter)
            
            else:
                widget = self._create_clickableCellWidget(entry)
                
                if index > 0 and self.schedule.timeline[index-1].telescope != entry.telescope:
                    if self.schedule.timeline[index].start_time != self.schedule.timeline[index-1].start_time:
                        self.current_row += 1
                else:
                    self.current_row += 1
                    
                self.grid_layout.addWidget(widget, self.current_row, entry.telescope, alignment=Qt.AlignmentFlag.AlignCenter)

            if self.current_row != past_value and entry.start_time not in unique_times:
                time_label = QLabel(entry.start_time.strftime("%H:%M:%S"))
                self.grid_layout.addWidget(time_label, self.current_row, 0, alignment=Qt.AlignmentFlag.AlignCenter)
                unique_times.append(entry.start_time)

    def _create_clickableCellWidget(self, entry: TimelineEntry) -> QWidget:
        widget = ClickableCellWidget(entry)
                    
        if self.copied_row_index == entry.row_index:
            widget.set_copied_highlight(True)

        widget.edit_requested.connect(self._handle_edit)
        widget.copy_requested.connect(self._handle_copy)
        widget.delete_requested.connect(self._handle_delete)
        widget.insert_above_requested.connect(self._handle_insert_above)
        widget.insert_below_requested.connect(self._handle_insert_below)
        widget.insert_copied_above_requested.connect(self._handle_insert_copied_above)
        widget.insert_copied_below_requested.connect(self._handle_insert_copied_below)

        return widget


    def _handle_edit(self, row_index: int):
        """Handle edit request."""
        self.edit_requested.emit(row_index)

    def _handle_copy(self, row_index: int):
        """Copy the entry at row_index to clipboard."""
        if 0 <= row_index < len(self.schedule.data):
            entry_data = self.schedule.data[row_index].copy()
            self.schedule.set_clipboard(entry_data)

            self.copied_row_index = row_index
            
            entry_type = entry_data.get('type', 'Unknown')
            self._show_toast(f"Copied {entry_type} entry")
            
            self.refresh()
        else:
            print(f"Invalid row index: {row_index}")

    def _handle_delete(self, row_index: int):
        """Delete the entry at row_index."""
        if 0 <= row_index < len(self.schedule.data):
            entry_type = self.schedule.data[row_index].get('type', 'Unknown')
            self.schedule.on_row_delete(row_index)

            if self.copied_row_index == row_index:
                self.copied_row_index = None
            elif self.copied_row_index is not None and self.copied_row_index > row_index:
                self.copied_row_index -= 1
            
            self._show_toast(f"Deleted {entry_type} entry")
        else:
            print(f"Invalid row index: {row_index}")

    def _handle_insert_above(self, row_index: int):
        """Insert a new blank entry above row_index."""
        if 0 <= row_index <= len(self.schedule.data):
            telescope = self.schedule.data[row_index].get('telescope', 0)
            new_entry = self._create_default_entry(telescope)
            self.schedule.on_row_insert(row_index, new_entry)

            if self.copied_row_index is not None and self.copied_row_index >= row_index:
                self.copied_row_index += 1
            
            self._show_toast(f"Inserted blank entry above")
        else:
            print(f"Invalid row index: {row_index}")

    def _handle_insert_below(self, row_index: int):
        """Insert a new blank entry below row_index."""
        if 0 <= row_index < len(self.schedule.data):
            telescope = self.schedule.data[row_index].get('telescope', 0)
            new_entry = self._create_default_entry(telescope)
            self.schedule.on_row_insert(row_index + 1, new_entry)
            
            if self.copied_row_index is not None and self.copied_row_index > row_index:
                self.copied_row_index += 1
            
            self._show_toast(f"Inserted blank entry below")
        else:
            print(f"Invalid row index: {row_index}")

    def _handle_insert_copied_above(self, row_index: int):
        """Insert copied entry above row_index."""
        if not self.schedule.has_clipboard():
            return
        
        if 0 <= row_index <= len(self.schedule.data):
            copied_entry = self.schedule.get_clipboard()
            self.schedule.on_row_insert(row_index, copied_entry)  # type: ignore

            self.copied_row_index = None
            
            entry_type = copied_entry.get('type', 'Unknown') if copied_entry else 'Unknown'
            self._show_toast(f"Pasted {entry_type} entry above")
            self.schedule.set_clipboard(None)
            self.refresh()
        else:
            print(f"Invalid row index: {row_index}")

    def _handle_insert_copied_below(self, row_index: int):
        """Insert copied entry below row_index."""
        if not self.schedule.has_clipboard():
            return
        
        if 0 <= row_index < len(self.schedule.data):
            copied_entry = self.schedule.get_clipboard()
            self.schedule.on_row_insert(row_index + 1, copied_entry)  # type: ignore
            
            self.copied_row_index = None
            
            entry_type = copied_entry.get('type', 'Unknown') if copied_entry else 'Unknown'
            self._show_toast(f"Pasted {entry_type} entry below")
            self.schedule.set_clipboard(None)
            self.refresh()
        else:
            print(f"Invalid row index: {row_index}")

    def _create_default_entry(self, telescope: int) -> dict:
        """Create a default blank entry with minimal required fields."""        
        return {
            'type': 'NEW',
            'telescope': telescope,
            'done': Validator.StatusValue.WAITING
        }

    def _show_toast(self, message: str, toast_type: ToastNotification.Type = ToastNotification.Type.SUCCESS):
        """Show a toast notification."""
        AppContext.getToast().show_message(message, toast_type)









































class TimelineControlBar(QWidget):
    zoom_changed = pyqtSignal(float) # pixels per second scale
    
    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # Time range display
        self.time_range_label = QLabel("Time Range: --:-- to --:--")
        self.time_range_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.time_range_label)

        layout.addStretch()

        # Zoom controls
        zoom_label = QLabel("Zoom:")
        layout.addWidget(zoom_label)
        
        self.zoom_out_btn = QPushButton()
        self.zoom_out_btn.setIcon(qta.icon('fa6s.magnifying-glass-minus'))
        self.zoom_out_btn.setFixedSize(30, 30)
        self.zoom_out_btn.clicked.connect(self._on_zoom_out)
        layout.addWidget(self.zoom_out_btn)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(2)
        self.zoom_slider.setMaximum(150)
        self.zoom_slider.setValue(2)
        self.zoom_slider.setFixedWidth(300)
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider)
        layout.addWidget(self.zoom_slider)
        
        self.zoom_in_btn = QPushButton()
        self.zoom_in_btn.setIcon(qta.icon('fa6s.magnifying-glass-plus'))
        self.zoom_in_btn.setFixedSize(30, 30)
        self.zoom_in_btn.clicked.connect(self._on_zoom_in)
        layout.addWidget(self.zoom_in_btn)

    def _on_zoom_slider(self, value: int):
        """Set zoom to value"""
        self.zoom_changed.emit(value / 100)

    def _on_zoom_in(self):
        """Increase zoom."""
        current = self.zoom_slider.value()
        self.zoom_slider.setValue(min(current + 5, self.zoom_slider.maximum()))
    
    def _on_zoom_out(self):
        """Decrease zoom."""
        current = self.zoom_slider.value()
        self.zoom_slider.setValue(max(current - 5, self.zoom_slider.minimum()))
    
    def update_time_range(self, start_time: datetime, end_time: datetime):
        """Update the time range display."""
        start_str = start_time.strftime("%H:%M")
        end_str = end_time.strftime("%H:%M")
        self.time_range_label.setText(f"Time Range: {start_str} to {end_str}")
    
    def set_zoom_value(self, pixels_per_second: float):
        """Set zoom slider to specific value."""
        slider_value = int(pixels_per_second * 10)
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(slider_value)
        self.zoom_slider.blockSignals(False)

class TimeRulerWidget(QWidget):
    """Vertical time axis showing hours and grid lines."""
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(80)
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.pixels_per_second = 0.02
        self.scroll_offset = 0
        
        self.setStyleSheet("background-color: #f8f9fa; border-right: 1px solid #dee2e6;")
    
    def update_time_range(self, start_time: datetime, end_time: datetime):
        """Update the time range."""
        self.start_time = start_time
        self.end_time = end_time
        self.update()
    
    def update_zoom(self, pixels_per_second: float):
        """Update zoom level."""
        self.pixels_per_second = pixels_per_second
        self.update()
    
    def set_scroll_offset(self, offset: int):
        """Update scroll position."""
        self.scroll_offset = offset
        self.update()
    
    def time_to_y(self, dt: datetime) -> float:
        """Convert datetime to Y coordinate."""
        if not self.start_time:
            return 0
        delta_seconds = (dt - self.start_time).total_seconds()
        return delta_seconds * self.pixels_per_second - self.scroll_offset
    
    def paintEvent(self, event):
        """Draw time ruler."""
        super().paintEvent(event)
        
        if not self.start_time or not self.end_time:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate time range
        current_time = self.start_time
        
        # Draw time labels and grid lines
        while current_time <= self.end_time:
            y = self.time_to_y(current_time)
            
            # Only draw if visible
            if -20 <= y <= self.height() + 20:
                # Draw time label
                time_str = current_time.strftime("%H:%M")
                
                # Major hour lines
                if current_time.minute == 0:
                    painter.setPen(QPen(QColor("#495057"), 2))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QPen(QColor("#6c757d"), 1))
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
                
                # Draw text
                text_rect = QRectF(5, y - 10, 50, 20)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, time_str)
            
            # Increment by 30 minutes
            current_time += timedelta(minutes=30)
        
        painter.end()

class TelescopeHeaderWidget(QWidget):
    """Horizontal header showing telescope names."""
    
    COLUMN_COUNT = 5
    COLUMN_SPACING = 10
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self.telescope_names = ["Telescope 1", "Telescope 2", "Telescope 3", "Telescope 4", "Sun Telescope"]
        self.setStyleSheet("background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;")
    
    def get_column_width(self) -> float:
        """Calculate dynamic column width based on widget width."""
        widget_width = self.width()
        available_width = max(widget_width, 1000)
        
        total_spacing = self.COLUMN_SPACING * (self.COLUMN_COUNT - 1)
        column_width = (available_width - total_spacing) / self.COLUMN_COUNT
        
        return column_width
    
    def paintEvent(self, event):
        """Draw telescope headers."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        font = painter.font()
        font.setBold(True)
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(QColor("#212529"))
        
        column_width = self.get_column_width()
        
        for i, name in enumerate(self.telescope_names):
            x = i * (column_width + self.COLUMN_SPACING)
            rect = QRectF(x, 0, column_width, self.height())
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, name)
        
        painter.end()

class TimelineViewer(QWidget):
    """Time-proportional timeline viewer showing tasks with accurate duration representation."""
    edit_requested = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.schedule = AppContext.getSchedule()
        self.schedule.changed.connect(self.refresh)
        self.copied_row_index: Optional[int] = None
        
        self.grid_layout = QGridLayout(self)

        # Initialize the sub widgets
        self.control_bar = TimelineControlBar()
        self.header_widget = TelescopeHeaderWidget()
        self.ruler_widget = TimeRulerWidget()
        self.graphics_widget = TimelineGraphicsWidget()
        
        self.grid_layout.addWidget(self.control_bar, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.header_widget, 1, 1, 1, 1)
        self.grid_layout.addWidget(self.ruler_widget, 2, 0, 1, 1)
        self.grid_layout.addWidget(self.graphics_widget, 2, 1, 1, 1)

        self.control_bar.zoom_changed.connect(self._on_zoom_changed)
    
        # Graphics scene signals
        self.graphics_widget.task_context_menu.connect(self._on_task_context_menu)
        
        # Scroll sync
        self.graphics_widget.verticalScrollBar().valueChanged.connect(self._sync_ruler_scroll) # type: ignore
        
        # Initial update
        self.refresh()
    
    def refresh(self):
        """Refresh the timeline from schedule data."""
        # Update graphics
        self.graphics_widget.update_from_schedule(self.schedule)

        # Sync copied state
        if self.copied_row_index is not None:
            self.graphics_widget.set_copied_task(self.copied_row_index)
        
        # Update ruler
        if self.schedule.dates:

            start_raw = self.schedule.dates.civil_dark_start - timedelta(hours=1)
            start_time = start_raw.replace(minute=0, second=0, microsecond=0)
            end_raw = self.schedule.dates.civil_dark_end + timedelta(hours=1)
            end_time = end_raw.replace(minute=0, second=0, microsecond=0)
            
            self.ruler_widget.update_time_range(start_time, end_time)
            self.ruler_widget.update_zoom(self.graphics_widget.pixels_per_second)
            self.control_bar.update_time_range(start_time, end_time)
    
    def _on_zoom_changed(self, pixels_per_second: float):
        """Handle zoom change."""
        self.graphics_widget.update_zoom(pixels_per_second)
        self.ruler_widget.update_zoom(pixels_per_second)
    
    def _sync_ruler_scroll(self, value: int):
        """Sync ruler widget with view scroll."""
        self.ruler_widget.set_scroll_offset(value)
    
    def _on_task_context_menu(self, row_index: int, pos: QPoint):
        """Show context menu for task."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #adb5bd;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #e2e6ea;
            }
            QMenu::separator {
                height: 1px;
                background-color: #ced4da;
                margin: 5px 10px;
            }
        """)
        
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self._handle_edit(row_index)) # type: ignore
        
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(lambda: self._handle_copy(row_index)) # type: ignore
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._handle_delete(row_index)) # type: ignore
        
        menu.addSeparator()
        
        insert_above_action = menu.addAction("Insert Above")
        insert_above_action.triggered.connect(lambda: self._handle_insert_above(row_index)) # type: ignore
        
        insert_below_action = menu.addAction("Insert Below")
        insert_below_action.triggered.connect(lambda: self._handle_insert_below(row_index)) # type: ignore
        
        if self.schedule.has_clipboard():
            menu.addSeparator()
            
            insert_copied_above_action = menu.addAction("Insert Copied Above")
            insert_copied_above_action.triggered.connect(lambda: self._handle_insert_copied_above(row_index)) # type: ignore
            
            insert_copied_below_action = menu.addAction("Insert Copied Below")
            insert_copied_below_action.triggered.connect(lambda: self._handle_insert_copied_below(row_index)) # type: ignore
        
        menu.exec(pos)
        
    def _handle_edit(self, row_index: int):
        """Handle edit request."""
        self.edit_requested.emit(row_index)

    def _handle_copy(self, row_index: int):
        """Copy the entry at row_index to clipboard."""
        if 0 <= row_index < len(self.schedule.data):
            entry_data = self.schedule.data[row_index].copy()
            self.schedule.set_clipboard(entry_data)
            self.copied_row_index = row_index
            entry_type = entry_data.get('type', 'Unknown')
            self._show_toast(f"Copied {entry_type} entry")
            self.refresh()

    def _handle_delete(self, row_index: int):
        """Delete the entry at row_index."""
        if 0 <= row_index < len(self.schedule.data):
            entry_type = self.schedule.data[row_index].get('type', 'Unknown')
            self.schedule.on_row_delete(row_index)
            if self.copied_row_index == row_index:
                self.copied_row_index = None
            elif self.copied_row_index is not None and self.copied_row_index > row_index:
                self.copied_row_index -= 1
            self._show_toast(f"Deleted {entry_type} entry")

    def _handle_insert_above(self, row_index: int):
        """Insert a new blank entry above row_index."""
        if 0 <= row_index <= len(self.schedule.data):
            telescope = self.schedule.data[row_index].get('telescope', 0)
            new_entry = self._create_default_entry(telescope)
            self.schedule.on_row_insert(row_index, new_entry)
            if self.copied_row_index is not None and self.copied_row_index >= row_index:
                self.copied_row_index += 1
            self._show_toast(f"Inserted blank entry above")

    def _handle_insert_below(self, row_index: int):
        """Insert a new blank entry below row_index."""
        if 0 <= row_index < len(self.schedule.data):
            telescope = self.schedule.data[row_index].get('telescope', 0)
            new_entry = self._create_default_entry(telescope)
            self.schedule.on_row_insert(row_index + 1, new_entry)
            if self.copied_row_index is not None and self.copied_row_index > row_index:
                self.copied_row_index += 1
            self._show_toast(f"Inserted blank entry below")

    def _handle_insert_copied_above(self, row_index: int):
        """Insert copied entry above row_index."""
        if not self.schedule.has_clipboard():
            return
        if 0 <= row_index <= len(self.schedule.data):
            copied_entry = self.schedule.get_clipboard()
            self.schedule.on_row_insert(row_index, copied_entry) # type: ignore
            self.copied_row_index = None
            entry_type = copied_entry.get('type', 'Unknown') if copied_entry else 'Unknown'
            self._show_toast(f"Pasted {entry_type} entry above")
            self.schedule.set_clipboard(None)
            self.refresh()

    def _handle_insert_copied_below(self, row_index: int):
        """Insert copied entry below row_index."""
        if not self.schedule.has_clipboard():
            return
        if 0 <= row_index < len(self.schedule.data):
            copied_entry = self.schedule.get_clipboard()
            self.schedule.on_row_insert(row_index + 1, copied_entry) # type: ignore
            self.copied_row_index = None
            entry_type = copied_entry.get('type', 'Unknown') if copied_entry else 'Unknown'
            self._show_toast(f"Pasted {entry_type} entry below")
            self.schedule.set_clipboard(None)
            self.refresh()

    def _create_default_entry(self, telescope: int) -> dict:
        """Create a default blank entry with minimal required fields."""        
        return {
            'type': 'NEW',
            'telescope': telescope,
            'done': Validator.StatusValue.WAITING
        }

    def _show_toast(self, message: str, toast_type: ToastNotification.Type = ToastNotification.Type.SUCCESS):
        """Show a toast notification."""
        AppContext.getToast().show_message(message, toast_type)

class TaskRectItem(QGraphicsRectItem):
    """Visual representation of a single scheduled task."""
    
    def __init__(self, timeline_entry: TimelineEntry, x: float, y: float, width: float, height: float):
        super().__init__(x, y, width, height)
        
        self.timeline_entry = timeline_entry
        self.is_copied = False
        self.is_hovered = False
        
        self.setAcceptHoverEvents(True)

        # Set appearance based on status
        self._update_appearance()
        
        # Add text label
        self.text_item = QGraphicsTextItem(self)
        self.symbol_item = QGraphicsTextItem(self)

        # Show tooltip
        start_str = self.timeline_entry.start_time.strftime("%H:%M:%S")
        end_str = self.timeline_entry.end_time.strftime("%H:%M:%S")
        duration = self.timeline_entry.end_time - self.timeline_entry.start_time
        self.setToolTip(f"{start_str} - {end_str}\nDuration: {duration}")
    
    def _update_appearance(self):
        """Update the visual appearance based on hover and copied state."""
        if self.is_copied:
            # Yellow highlight for copied items
            border_color = QColor("#ffc107")
            fill_color = QColor("#fff3cd")
            border_width = 2
        elif self.is_hovered:
            # Hover colors
            border_color = QColor("#adb5bd")
            fill_color = QColor("#e2e6ea")
            border_width = 1
        else:
            # Normal colors
            border_color = QColor("#81868c")
            fill_color = QColor("#ffffff")
            border_width = 1
        
        if self.timeline_entry.start_time == self.timeline_entry.end_time:
            border_color = QColor("#dc3545")
            border_width = 2
        
        # Set pen and brush
        pen = QPen(border_color, border_width)
        self.setPen(pen)
        self.setBrush(QBrush(fill_color))

    def set_is_copied(self, is_copied: bool):
        self.is_copied = is_copied
        self._update_appearance()

    def hoverEnterEvent(self, event):
        """Handle mouse hover enter."""
        self.is_hovered = True
        self._update_appearance()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave."""
        self.is_hovered = False
        self._update_appearance()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        # Called whenever the item is added/removed/moved in a scene
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged and value is not None:
            # Defer update until next event loop tick (scene is fully ready)
            QTimer.singleShot(0, self._update_text)
        return super().itemChange(change, value)
    
    def _update_text(self):
        """Update text label."""
        parent_rect = self.rect()


        # --- Hide text entirely if rect is too small ---
        if parent_rect.width() < 10 or parent_rect.height() < 10:
            self.text_item.setVisible(False)
            self.symbol_item.setVisible(False)
            return
        else:
            self.text_item.setVisible(True)
            self.symbol_item.setVisible(True)
            
        display_text = self._get_display_text()
        status_symbol, status_symbol_color = self._get_status_symbol_text()

        # Set symbol text and color
        self.symbol_item.setPlainText(status_symbol)
        self.symbol_item.setDefaultTextColor(QColor(status_symbol_color))
        symbol_font = self.symbol_item.font()
        symbol_font.setBold(True)
        symbol_font.setPointSize(9)
        self.symbol_item.setFont(symbol_font)
        
        # Set display text and color
        self.text_item.setPlainText(display_text)
        self.text_item.setDefaultTextColor(QColor("#212529"))
        text_font = self.text_item.font()
        text_font.setBold(True)
        text_font.setPointSize(9)
        self.text_item.setFont(text_font)      

        # Get dimensions
        symbol_rect = self.symbol_item.boundingRect()
        text_rect = self.text_item.boundingRect()
        spacing = 5  # Space between symbol and text

        # Compute total content width and height
        total_width = symbol_rect.width() + spacing + text_rect.width()
        total_height = max(symbol_rect.height(), text_rect.height())

        # Compute top-left starting point for centering
        start_x = parent_rect.left() + (parent_rect.width() - total_width) / 2
        start_y = parent_rect.top() + (parent_rect.height() - total_height) / 2

        # --- Optional visible-portion adjustment ---
        if self.scene() and self.scene().views(): # type: ignore
            view = self.scene().views()[0]# type: ignore
            visible_scene_rect = view.mapToScene(view.viewport().rect()).boundingRect()# type: ignore
            item_scene_rect = self.mapToScene(parent_rect).boundingRect()
            visible_part = visible_scene_rect.intersected(item_scene_rect)

            # Only adjust vertically if there's a visible overlap
            if visible_part.isValid() and visible_part.height() >= 30:
                visible_top_left = self.mapFromScene(visible_part.topLeft())
                visible_bottom_right = self.mapFromScene(visible_part.bottomRight())
                visible_height = visible_bottom_right.y() - visible_top_left.y()
                start_y = visible_top_left.y() + (visible_height - total_height) / 2


        # Adjust for each item's own local bounding rect offset
        symbol_x = start_x - symbol_rect.left()
        symbol_y = start_y - symbol_rect.top()
        text_x = symbol_x + symbol_rect.width() + spacing - text_rect.left()
        text_y = start_y - text_rect.top()

        # Apply positions
        self.symbol_item.setPos(symbol_x, symbol_y)
        self.text_item.setPos(text_x, text_y)
    
    def _get_display_text(self) -> str:
        """Get formatted display name for task."""
        details = self.timeline_entry.details
        if details['type'] == "NEW":
            return "NEW"
        else:
            timeline_name = ACTION_REGISTRY[details['type']]['timeline_name']
            for k, v in details.items():
                timeline_name = timeline_name.replace(f"<{k}>", str(v))
            return timeline_name
        
    def _get_status_symbol_text(self) -> tuple[str, str]:
        status = self.timeline_entry.details['done']
        if status == Validator.StatusValue.WAITING:
            color = "#ffc107"
            symbol = "⧗"
        elif status == Validator.StatusValue.DONE:
            color = "#28a745"
            symbol = "✔"
        elif status == Validator.StatusValue.FAILED:
            color = "#dc3545"
            symbol = "✘"
        elif status == Validator.StatusValue.BUSY:
            color = "#007bff"
            symbol = "⧖"
        else:
            color = "#555555"
            symbol = "-"
        return symbol, color
    
    def update_geometry(self, x: float, y: float, width: float, height: float):
        """Update position and size."""
        self.setRect(x, y, width, height)
        self._update_text()

class TimelineGraphicsWidget(QGraphicsView):
    """Custom graphics view for timeline with scroll and zoom."""
    
    task_context_menu = pyqtSignal(int, QPoint)  # row_index, Position
    
    COLUMN_COUNT = 5
    COLUMN_SPACING = 10
    
    def __init__(self):
        self._scene = QGraphicsScene()
        super().__init__(self._scene)
        
        self.pixels_per_second = 0.02

        self.start_datetime: Optional[datetime] = None
        self.end_datetime: Optional[datetime] = None
        
        self.task_items: dict[int, TaskRectItem] = {}  # row_index -> TaskRectItem        
        self.copied_row_index: Optional[int] = None

        # View settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("""
            
            /* Chrome-style scrollbar */
            QScrollBar:vertical {
                background: transparent;
                width: 14px;
                margin: 0px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background: #5f6368;
                min-height: 30px;
                margin: 2px 2px 2px 2px;
                border-radius: 7px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #80868b;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            
            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical {
                background: none;
            }
        """)
        
        # Mouse tracking
        self.setMouseTracking(True)
    
    def get_column_width(self) -> float:
        view_width = self.viewport().width() #type: ignore
        available_width = max(view_width, 1000) # Minimum 1000px

        total_spacing = self.COLUMN_SPACING * (self.COLUMN_COUNT - 1)
        column_width = (available_width - total_spacing) / self.COLUMN_COUNT

        return column_width
    
    def time_to_y_coordinate(self, dt: datetime) -> float:
        """Convert datetime to Y coordinate."""
        if not self.start_datetime:
            return 0
        delta_seconds = (dt - self.start_datetime).total_seconds()
        return delta_seconds * self.pixels_per_second
    
    def y_coordinate_to_time(self, y: float) -> datetime:
        """Convert Y coordinate to datetime."""
        if not self.start_datetime:
            return datetime.now()
        seconds_offset = y / self.pixels_per_second
        return self.start_datetime + timedelta(seconds=seconds_offset)
    
    def telescope_to_x_coordinate(self, telescope_idx: int) -> float:
        """Get left X coordinate for telescope column."""
        column_width = self.get_column_width()

        if telescope_idx == 0:  # TODO FIX THIS
            return (1 - 1) * (column_width + self.COLUMN_SPACING)
        
        return (telescope_idx - 1) * (column_width + self.COLUMN_SPACING)
    
    def update_from_schedule(self, schedule: Schedule):
        """Rebuild all items from schedule data."""
        # Clear existing items
        self.clear_all_items()
        
        # Set time range
        if schedule.dates:
            start_raw = schedule.dates.civil_dark_start - timedelta(hours=1)
            self.start_datetime = start_raw.replace(minute=0, second=0, microsecond=0)
            end_raw = schedule.dates.civil_dark_end + timedelta(hours=1)
            self.end_datetime = end_raw.replace(minute=0, second=0, microsecond=0)
        
        # Calculate scene size
        if self.start_datetime and self.end_datetime:
            total_seconds = (self.end_datetime - self.start_datetime).total_seconds()
            scene_height = total_seconds * self.pixels_per_second
            column_width = self.get_column_width()
            scene_width = self.COLUMN_COUNT * column_width + (self.COLUMN_COUNT - 1) * self.COLUMN_SPACING  # 4 telescopes + sun
            self._scene.setSceneRect(0, 0, scene_width, scene_height)
        
        # Create task rectangles
        for entry in schedule.timeline:
            self._create_task_rect(entry)
    
    def _create_task_rect(self, entry: TimelineEntry) -> TaskRectItem:
        """Create a task rectangle item."""
        column_width = self.get_column_width()

        x = self.telescope_to_x_coordinate(entry.telescope)
        y = self.time_to_y_coordinate(entry.start_time)
        
        duration_seconds = (entry.end_time - entry.start_time).total_seconds()
        height = duration_seconds * self.pixels_per_second
        width = column_width - 2
        
        task_item = TaskRectItem(entry, x, y, width, height)
        
        # Connect click events
        task_item.mousePressEvent = lambda event: self._on_task_clicked(entry.row_index, event)
        
        self._scene.addItem(task_item)
        self.task_items[entry.row_index] = task_item
        
        return task_item
    
    def _on_task_clicked(self, row_index: int, event: Optional[QGraphicsSceneMouseEvent]):
        """Handle task click."""
        if event is not None and event.button() == Qt.MouseButton.RightButton:
            self.task_context_menu.emit(row_index, event.screenPos())
    
    def set_copied_task(self, row_index: Optional[int]):
        """Mark a task as copied."""
        # Clear previous copied highlight
        if self.copied_row_index is not None and self.copied_row_index in self.task_items:
            self.task_items[self.copied_row_index].set_is_copied(False)
        
        # Set new copied highlight
        self.copied_row_index = row_index
        if row_index is not None and row_index in self.task_items:
            self.task_items[row_index].set_is_copied(True)
    
    def update_zoom(self, pixels_per_second: float):
        """Update zoom level and reposition all items."""
        self.pixels_per_second = pixels_per_second
        column_width = self.get_column_width()
        
        # Recalculate scene height
        if self.start_datetime and self.end_datetime:
            total_seconds = (self.end_datetime - self.start_datetime).total_seconds()
            scene_height = total_seconds * self.pixels_per_second
            scene_width = self.COLUMN_COUNT * column_width + (self.COLUMN_COUNT - 1) * self.COLUMN_SPACING
            self._scene.setSceneRect(0, 0, scene_width, scene_height)
        
        # Update all task positions and sizes
        for row_index, task_item in self.task_items.items():
            entry = task_item.timeline_entry
            x = self.telescope_to_x_coordinate(entry.telescope)
            y = self.time_to_y_coordinate(entry.start_time)
            duration_seconds = (entry.end_time - entry.start_time).total_seconds()
            height = max(duration_seconds * self.pixels_per_second, 20)
            width = column_width - 2
            task_item.setRect(x, y, width, height)
            task_item._update_text()
        
    def clear_all_items(self):
        """Remove all items from scene."""
        for item in self.task_items.values():
            self._scene.removeItem(item)
        self.task_items.clear()
    
    def scrollContentsBy(self, dx: int, dy: int):
        """Override to sync with ruler widget."""
        super().scrollContentsBy(dx, dy)

    
    def resizeEvent(self, event):
        """Handle resize to redistribute columns."""
        super().resizeEvent(event)
        schedule = AppContext.getSchedule()
        self.update_from_schedule(schedule)



































class TableViewer(QTableWidget):
    def __init__(self):
        super().__init__()
        self.schedule = AppContext.getSchedule()
        self.schedule.changed.connect(self.refresh_table)

        self.refresh_table()

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        super().selectionChanged(selected, deselected)
        model = self.selectionModel()
        for index in model.selectedIndexes(): # type: ignore
            if index.column() in self.unselectable_columns:
                model.select(index, QItemSelectionModel.SelectionFlag.Deselect) # type: ignore

    def refresh_table(self):
        self.blockSignals(True)
        self.clearContents()
        
        all_columns = set([col for item in self.schedule.get() for col in item.keys()])
        preferred_order = ["type", "telescope", "done"]
        self.columns = [col for col in preferred_order if col in all_columns] + [col for col in all_columns if col not in preferred_order]
        
        headers = ['Nr.'] + self.columns + ['']

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False) # type: ignore
        
        self.setStyleSheet("""
            QHeaderView::section {
                padding-left: 13px;
                padding-right: 13px;
            }
        """)

        self.setRowCount(len(self.schedule.get()))

        for row, item in enumerate(self.schedule.get()):
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(1)

            btn_up = QPushButton("▲")
            btn_down = QPushButton("▼")

            btn_down.setFixedWidth(30)
            btn_up.setFixedWidth(30)

            row_input = QLineEdit(str(row))
            row_input.setFixedWidth(45)
            onlyAvailableRows = QIntValidator()
            row_input.setValidator(onlyAvailableRows)
            row_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_up.clicked.connect(partial(self.move_row_up, row))
            btn_down.clicked.connect(partial(self.move_row_down, row))
            row_input.returnPressed.connect(partial(self.move_row, row, row_input))

            buttons_layout.addWidget(btn_up)
            buttons_layout.addWidget(row_input)
            buttons_layout.addWidget(btn_down)

            self.setCellWidget(row, 0, buttons_widget)
            for col, key in enumerate(self.columns):
                v = str(item.get(key, ""))
                if v in ['None', 'nan']:
                    v = ''
                w = QTableWidgetItem(v)
                if key == 'done':
                    if v == Validator.StatusValue.WAITING:
                        w.setBackground(Qt.GlobalColor.yellow)
                    elif v == Validator.StatusValue.BUSY:
                        w.setBackground(Qt.GlobalColor.blue)
                    elif v == Validator.StatusValue.DONE:
                        w.setBackground(Qt.GlobalColor.green)
                    elif v == Validator.StatusValue.FAILED:
                        w.setBackground(Qt.GlobalColor.red)
                self.setItem(row, col + 1, w)

            # --- Delete button in the last column ---
            delete_icon = qta.icon('fa6.trash-can')
            delete_button = QPushButton()
            delete_button.setIcon(QIcon(delete_icon.pixmap(32, 32)))
            delete_button.setIconSize(QSize(32, 32))
            delete_button.clicked.connect(lambda _, r=row: self.delete_row(r))

            self.setCellWidget(row, len(self.columns) + 1, delete_button)
        
        self.unselectable_columns = [0]
        self.resizeColumnsToContents()
        self.cellChanged.connect(self.on_cell_edited)
        self.blockSignals(False)

    def delete_row(self, row):
        self.schedule.on_row_delete(row)
        self.refresh_table()

    def on_cell_edited(self, row, column):
        if column == 0:
            return  # dont edit nr column

        key = self.columns[column - 1]
        if key == "done":
            return  # dont edit done column
        
        new_value = self.item(row, column).text() # type: ignore

        old_value = self.schedule.getRowValue(row, key)

        row_values = self.schedule.getRow(row)

        ValidatorClass = ACTION_REGISTRY.get(self.schedule.getRowValue(row, 'type'), {}).get('validators', {}).get(key)
        telescope = self.schedule.getRowValue(row, 'telescope')
        if ValidatorClass is None:
            new_value = old_value
        else:
            # TODO: fix this
            # validator_context = Context(dates=self.schedule.dates, telescope=telescope)
            # validator = ValidatorClass(name=key, context=validator_context)
            # if not validator.isValid(new_value):
            #     new_value = old_value
            # else:
            #     new_value = validator.getValue()
            pass

        self.schedule.on_row_value_edit(row, key, new_value)
        self.refresh_table()

    def move_row_up(self, row):
        self.schedule.on_row_move_up(row)
        self.refresh_table()

    def move_row_down(self, row):
        self.schedule.on_row_move_down(row)
        self.refresh_table()

    def move_row(self, old_row, row_input):
        self.schedule.on_row_move(old_row, int(row_input.text()))
        self.refresh_table()

class SegmentedControl(QWidget):
    view_type_changed = pyqtSignal(ViewType)

    def __init__(self, initial_view_type: ViewType):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setSpacing(0)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.buttons = {}

        for i, view_type in enumerate(ViewType):
            btn = QPushButton(view_type.name.title())
            btn.setCheckable(True)
            if view_type == initial_view_type:
                btn.setChecked(True)
            self.group.addButton(btn, i)
            layout.addWidget(btn)
            self.buttons[view_type] = btn

            btn.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid #888;
                    padding: 5px 15px;
                    background-color: #d0d0d0;
                    border-top-left-radius: {5 if i == 0 else 0}px;
                    border-bottom-left-radius: {5 if i == 0 else 0}px;
                    border-top-right-radius: {5 if i == len(ViewType) - 1 else 0}px;
                    border-bottom-right-radius: {5 if i == len(ViewType) - 1 else 0}px;
                }}
                QPushButton:checked {{
                    background-color: #f0f0f0;
                }}
            """)

        self.group.buttonClicked.connect(self.on_button_clicked)

    def on_button_clicked(self, button: QPushButton):
        selected_view = ViewType[button.text().upper()]
        self.view_type_changed.emit(selected_view)

    def set_selected(self, view_type: ViewType):
        if view_type in self.buttons:
            self.buttons[view_type].setChecked(True)
            self.view_type_changed.emit(view_type)

class DateTimeGradient(QWidget):
    def __init__(self):
        super().__init__()
        self.schedule = AppContext.getSchedule()

        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        date_time = EditableLabel(self.schedule.dates._date)
        date_time.edited.connect(self.schedule.dates.new_date)
        date_time.setToolTip("Double click to edit date")
        date_time.setStyleSheet("font-size: 16px;")
        layout.addWidget(date_time)

        bar = GradientBar()
        bar.setMinimumWidth(130)
        layout.addWidget(bar)

        self.setLayout(layout)

class GradientBar(QWidget):
    def __init__(self):
        super().__init__()
        self.dates = AppContext.getSchedule().dates
        self.setMinimumHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        bar_height = 20
        bar_y = rect.center().y() - bar_height // 2
        bar_rect = QRectF(rect.left(), bar_y, rect.width(), bar_height)

        # --- Create horizontal gradient ---
        grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
        grad.setColorAt(0.0, QColor("#FFD580"))   # Sunset
        grad.setColorAt(0.3, QColor("#001030"))   # Night
        grad.setColorAt(0.7, QColor("#001030"))   # Night
        grad.setColorAt(1.0, QColor("#FFD580"))   # Sunrise

        painter.fillRect(bar_rect, grad)

        # --- Optional: border around bar ---
        painter.setPen(QColor("#FFFFFF"))
        painter.drawRect(bar_rect.adjusted(0, 0, -1, -1))

        # --- Text settings ---
        painter.setPen(Qt.GlobalColor.black)
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)

        # --- Draw labels ---
        def draw_label(x_factor: float, time: datetime, y: float):
            x = rect.width() * x_factor
            # Choose alignment based on x position
            if x_factor <= 0.05:
                align = Qt.AlignmentFlag.AlignLeft
                x_offset = 0
            elif x_factor >= 0.95:
                align = Qt.AlignmentFlag.AlignRight
                x_offset = -60
            else:
                align = Qt.AlignmentFlag.AlignCenter
                x_offset = -30
            painter.drawText(QRectF(x + x_offset, int(y) - 10, 60, 20), align, time.strftime('%H:%M'))

        # Positions
        top_y = bar_rect.top() - 10
        bottom_y = bar_rect.bottom() + 12

        # Top labels (sunrise/sunset)
        draw_label(0.0, self.dates.civil_dark_start, top_y)
        draw_label(1.0, self.dates.civil_dark_end, top_y)

        # Bottom labels (night start/end)
        draw_label(0.3, self.dates.astronomical_dark_start, bottom_y)
        draw_label(0.7, self.dates.astronomical_dark_end, bottom_y)

class EditableLabel(QLabel):
    edited = pyqtSignal(date)
    """A QLabel that can be edited on double-click without layout shift."""
    def __init__(self, _date: date, parent=None):
        super().__init__(_date.strftime('%Y-%m-%d'), parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit = None

    def mouseDoubleClickEvent(self, event):
        if self.edit is None:
            # Create QLineEdit at same position and size as QLabel
            self.edit = QLineEdit(self.text(), self.parent())  # type: ignore
            self.edit.setStyleSheet("padding: 0px 1px;")
            self.edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.edit.setGeometry(self.geometry())  # match QLabel size/position
            self.edit.returnPressed.connect(self.finish_edit)
            self.edit.focusOutEvent = self.finish_edit_focus_out # type: ignore
            self.hide()
            self.edit.show()
            self.edit.setFocus()

    def finish_edit(self):
        if self.edit:
            self.setText(self.edit.text())
            self.edit.deleteLater()
            self.edit = None
            self.show()
            try:
                new_date = datetime.strptime(self.text(), '%Y-%m-%d').date()
                self.edited.emit(new_date)
            except ValueError:
                self.setText(datetime.now().strftime('%Y-%m-%d'))
                return

    def finish_edit_focus_out(self, event):
        self.finish_edit()
        super().focusOutEvent(event)

class ActionPicker(QComboBox):
    actionTypeChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.setPlaceholderText("Select Action...")

        model = QStandardItemModel()
        self.setModel(model)
        self.populate(model)

        self.currentIndexChanged.connect(self.emit_action_changed)
        self.showPopup()

    def current_action(self):
        return self.currentData(Qt.ItemDataRole.UserRole)

    def setCurrentAction(self, action_key: Optional[str]) -> None:
        self.blockSignals(True)
        if action_key is None:
            self.setCurrentIndex(0)
        else:
            for i in range(self.count()):
                if self.itemData(i, Qt.ItemDataRole.UserRole) == action_key:
                    self.setCurrentIndex(i)
                    break
        self.blockSignals(False)

    def emit_action_changed(self, _):
        action_key = self.current_action()
        if action_key and action_key in ACTION_REGISTRY:
            self.actionTypeChanged.emit(action_key)

    def populate(self, model:QStandardItemModel):
        # Get unique categories
        categories = set([attr['category'] for attr in ACTION_REGISTRY.values()])

        # This way I dont need to make a tree model (easier)
        for category in sorted(categories):
            # Header item (not selectable)
            header = QStandardItem(category)
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            model.appendRow(header)

            # Get attributes for this category and sort by position
            attrs = [(k,v) for k,v in ACTION_REGISTRY.items() if v['category'] == category]
            sorted_attrs = sorted(attrs, key=lambda attr: attr[1]['position'])

            for key, attr in sorted_attrs:
                child_item = QStandardItem(f"    {attr['display_name']}")
                child_item.setData(key, Qt.ItemDataRole.UserRole)
                model.appendRow(child_item)

    def showPopup(self):
        super().showPopup()
        view = self.view()
        if not view:
            return
        popup = view.window()
        if not popup:
            return
        popup_rect = popup.geometry()
        window = self.window()
        if not window:
            return
        below = self.mapToGlobal(self.rect().bottomLeft())
        window_height = window.height()
        widget_bottom_y = self.mapTo(window, self.rect().bottomLeft()).y()
        space_below = window_height - widget_bottom_y
        popup.resize(popup_rect.width(), space_below - 10) 
        popup.move(below)

def main():
    app = QApplication([])
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
