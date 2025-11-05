from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
import json
import re
import os
from pathlib import Path
from PyQt6.QtWidgets import QLineEdit, QCheckBox, QWidget, QRadioButton, QHBoxLayout, QButtonGroup, QComboBox, QPushButton
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QIcon
from PyQt6.QtCore import QTimer, QSize
from typing import Callable, Any, Dict, List, Optional
from configparser import ConfigParser
from .sequencer_common import DateTimes, ValidatorContext
import qtawesome as qta


# Define all unit config files


MCONFIG = Path(os.path.dirname( __file__ )) / "config"

units1 = str(MCONFIG / "marvel/units/unit1.cfg")
units2 = str(MCONFIG / "marvel/units/unit2.cfg")
units3 = str(MCONFIG / "marvel/units/unit3.cfg")
units4 = str(MCONFIG / "marvel/units/unit4.cfg")

UNITCONFIGS = {
    1: units1,
    2: units2,
    3: units3,
    4: units4,
}

class BaseClass:
    dependencies: List[str] = [] # names of context fields this value depends on

    def __init__(
            self,
            *,
            name: str,
            value: Optional[Any] = None,
            context: Optional[ValidatorContext] = None
    ) -> None:
        self.name = name
        self._context = context if context is not None else ValidatorContext(DateTimes(date.today()))
        self._widget: Optional[QWidget] = None
        self._dependencies: List[str] = list(self.dependencies)

        # Register dependencies with context
        for dep in self._dependencies:
            self._context.watch(dep, self._on_dependency_changed)

        self._context.watch(self.name, self._on_own_value_changed)

        # register with context
        full_value = None
        if self.isValid(value):
            full_value = self.to_full(value)
        self._context.set(self.name, value, full_value, notify=False)

    def _on_own_value_changed(self, name: str, value: Any) -> None:
        """
        Called when this fields value changes in context.
        Override in subclasses to update widgets then context value change.
        """
        pass

    @property
    def context(self) -> ValidatorContext:
        """Get the current context."""
        return self._context

    @context.setter
    def context(self, new_context: ValidatorContext) -> None:
        """Set a new context."""
        if hasattr(self, '_context') and self._context is not None:
            # Unregister from old context
            for dep in self._dependencies:
                self._context.unwatch(dep, self._on_dependency_changed)

        self._context = new_context

        # Register with new context
        for dep in self._dependencies:
            self._context.watch(dep, self._on_dependency_changed)

    @property
    def value(self) -> Any:
        return self._context.get(self.name)

    @value.setter
    def value(self, new_value: Any) -> None:
        if self.isValid(new_value):
            full_value = self.to_full(new_value)
        else:
            full_value = self._context.get_full(self.name)
        self._context.set(self.name, new_value, full_value)

    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """Called when a dependency changes. Override in subclasses if needed."""
        ...

    @abstractmethod
    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create and return the input widget for this value."""
        ...

    @abstractmethod
    def isValid(self, value: Any = None) -> bool:
        """Check if the given value is valid."""
        ...

    def to_full(self, value: Any = None) -> Any:
        """
        Return the value formatted for the scheduler.
        Example: meant to save a time as full datetime using the date from context
        """
        return value if value is not None else self.value

    @abstractmethod
    def expected(self) -> str:
        """Return a string describing the expected input format."""
        ...

class BaseCoordinate(BaseClass, ABC):
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    degree_pattern = r'^([+-]?\d{1,3})(?:[:\s]\s*([0-5]?\d)(?:[:\s]\s*([0-5]?\d(?:\.\d+)?))?)?$'

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create input widget for coordinate."""
        widget = QLineEdit()
        widget.setPlaceholderText(self.expected())
        
        if self.value is not None:
            widget.setText(str(self.value))

        def handle_change(text: str):
            self.value = text
            changed()

        widget.textChanged.connect(handle_change)
        self._widget = widget
        return widget
    
    def _on_own_value_changed(self, name: str, value: Any) -> None:
        """Update widget when context value changes."""
        if isinstance(self._widget, QLineEdit) and value is not None:
            self._widget.setText(str(value))

    def isValid(self, value: Any = None) -> bool:
        """Check if the value is a valid coordinate."""
        check_value = value if value is not None else self.value
        try:
            value = str(check_value)
            return self._parse(value) is not None
        except:
            return False
    
    @classmethod
    def _parse(cls, value: Any = None) -> Optional[float]:
        """Attempt both float and string parsing."""
        try:
            value = str(value).strip()
        except:
            return None
        return cls._parse_float(value) if cls._parse_float(value) else None or cls._parse_coord_string(value) if cls._parse_coord_string(value) else None
    
    @classmethod
    def _parse_float(cls, value: str) -> Optional[float]:
        try:
            val_float = float(value)
        except:
            return None
        return val_float if cls.min_max_check(val_float) else None

    @classmethod
    def _parse_coord_string(cls, coord_str: str) -> Optional[float]:
        hours = cls._calculate_hours(coord_str)
        if hours is None:
            return None
        return hours if cls.min_max_check(hours) else None

    @classmethod
    def _calculate_hours(cls, degrees: str) -> Optional[float]:
        match = re.fullmatch(cls.degree_pattern, degrees)
        if match:
            a, b, c = map(float, (match.group(1), match.group(2) or 0, match.group(3) or 0))
            return a + b/60 + c/3600
        return None

    @classmethod
    def min_max_check(cls, value: float) -> bool:
        if cls.min_value is not None and value < cls.min_value:
            return False
        if cls.max_value is not None and value > cls.max_value:
            return False
        return True

    def expected(self) -> str:
        """Return expected input description for coordinate."""
        return "18.072497 | 18:04:20.99"

class Ra(BaseCoordinate):
    """Right Ascension coordinate (0-24 hours)."""
    min_value = 0.0
    max_value = 24.0

class Dec(BaseCoordinate):
    """Declination coordinate (-90 to +90 degrees)."""
    min_value = -90.0
    max_value = 90.0

class Azimuth(BaseCoordinate):
    """Azimuth coordinate (0-360 degrees)."""
    min_value = 0.0
    max_value = 360.0

class Altitude(BaseCoordinate):
    """Altitude coordinate (-90 to +90 degrees)."""
    min_value = -90.0
    max_value = 90.0
    dependencies = ['telescope'] # depends on selected telescope

    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """Called when a dependency changes. Update min/max based on telescope."""
        if name == 'telescope':
            self._update_limits(value)

    def _update_limits(self, telescope: Optional[int]) -> None:
        """Update min/max based on selected telescope."""
        if telescope is None or telescope == 0:
            self.min_value = -90.0
            self.max_value = 90.0
        else:
            self.min_value = TELESCOPES[telescope].TELESCOPE.MIN_ALTITUDE
            self.max_value = TELESCOPES[telescope].TELESCOPE.MAX_ALTITUDE

        if isinstance(self._widget, QLineEdit):
            self._widget.setValidator(QDoubleValidator(self.min_value, self.max_value, 10))
            self._widget.setPlaceholderText(self.expected())

    def expected(self) -> str:
        return f"{self.min_value} ≤ altitude ≤ {self.max_value}"

class Int(BaseClass):
    """Integer value with optional min/max bounds."""
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    dependencies = ['telescope'] # some of these depend on selected telescope


    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create input widget for integer."""
        widget = QLineEdit()
        widget.setPlaceholderText(self.expected())

        if self.value is not None:
            widget.setText(str(self.value))

        validator = QIntValidator()
        if self.min_value is not None:
            validator.setBottom(self.min_value)
        if self.max_value is not None:
            validator.setTop(self.max_value)
        widget.setValidator(validator)

        def handle_change(text: str):
            valid = self.isValid(text) if text else False
            self.value = int(text) if valid else text
            changed()

        widget.textChanged.connect(handle_change)
        self._widget = widget
        return widget
    
    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """Called when a dependency changes. Update based on telescope."""
        if name == 'telescope':
            self._update_widget_state(value)

    def _update_widget_state(self, telescope: Optional[int]) -> None:
        """Update widget state based on selected telescope."""
        if telescope is None or telescope == 0:
            return
        config_value = find_config_value(TELESCOPES[telescope], self.name)
        if config_value is None or not self.isValid(config_value):
            return
        # Update value and UI
        self.value = config_value
        if isinstance(self._widget, QLineEdit):
            self._widget.setPlaceholderText(f"{self.expected()} (default: {config_value})")
            self._widget.setText(str(config_value))

    def isValid(self, value: Any = None) -> bool:
        """Check if the value is a valid integer within bounds."""
        check_value = value if value is not None else self.value

        try:
        
            int_value = int(check_value)

            if self.min_value is not None and int_value < self.min_value:
                return False
            
            if self.max_value is not None and int_value > self.max_value:
                return False
            
            return True
        
        except:
            return False

    def expected(self) -> str:
        """Return expected input description with bounds"""
        if self.min_value is not None and self.max_value is not None:
            return f"{self.min_value} <= int <= {self.max_value}"
        
        elif self.min_value is not None:
            return f"int >= {self.min_value}"
        
        elif self.max_value is not None:
            return f"int <= {self.max_value}"
        
        else:
            return "integer"

class TemperatureDefault(Int):
    """Temperature with default value of -20."""

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create input widget with default value of -20."""
        widget = super().input_widget(changed)

        # Set default value to -20 without triggering signals
        widget.blockSignals(True)
        widget.setText(str(-20)) # type: ignore
        self.value = -20
        widget.blockSignals(False)

        return widget

class IntPositive(Int):
    """Positive integer (min 1)"""
    min_value = 1

class FlatMedian(Int):
    """Flat median value between 1 and 90. that updates context on change."""
    min_value = 1
    max_value = 90

class FlatRange(Int):
    min_value = 1
    max_value = 90
    dependencies = ['flat_median'] # depends on flat_median

    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """Called when a dependency changes. Update max based on flat_median."""
        if name == 'flat_median':
            self._update_limits(value)

    def _update_limits(self, flat_median: Optional[int]) -> None:
        """Update max based on flat_median."""
        if flat_median in (None, ''):
            self.max_value = 90 # back to default
            return

        assert self.min_value is not None

        # flat_median - flat_range mag niet onder nul
        # flat median + flat range mag niet boven 100
        self.max_value = min(flat_median, 100 - flat_median)

        if isinstance(self._widget, QLineEdit):
            self._widget.setValidator(QIntValidator(self.min_value, self.max_value))
            self._widget.setPlaceholderText(self.expected())

class Choice(BaseClass, ABC):
    """Abstract class for choices. Do not instantiate directly. You will get a TypeError."""
    _allowed_values: List[Any] = []
    dependencies = ['telescope'] # some of these depend on selected telescope

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if type(self) is Choice:
            raise TypeError("Choice is an abstract class and cannot be instantiated directly.")
        if not self._allowed_values:
            raise ValueError("Subclasses of Choice must define _allowed_values.")
        self._button_group: Optional[QButtonGroup] = None

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create a horizontal group of radio buttons for the allowed choices."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._button_group = QButtonGroup(container)
        self._button_group.setExclusive(True)

        for idx, choice_value in enumerate(self._allowed_values):
            radio_btn = QRadioButton(str(choice_value))
            layout.addWidget(radio_btn)
            self._button_group.addButton(radio_btn, idx)

            # Check if this should be the selected button
            if self.value == choice_value:
                radio_btn.setChecked(True)

        def handle_selection(button_id: int):
            self.value = self._allowed_values[button_id]
            changed()

        self._button_group.idClicked.connect(handle_selection)
        self._widget = container
        return container

    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """Called when a dependency changes. Update based on telescope."""
        if name == 'telescope':
            self._update_widget_state(value)

    def _update_widget_state(self, telescope: Optional[int]) -> None:
        """Update widget state based on selected telescope."""
        if telescope is None or telescope == 0:
            return
        config_value = find_config_value(TELESCOPES[telescope], self.name)
        if config_value is None or not self.isValid(config_value):
            return
        # Update value and UI
        self.value = config_value
        if self._button_group is not None:
            idx = self._allowed_values.index(config_value)
            button = self._button_group.button(idx)
            if button is not None:
                button.setChecked(True)
    
    def isValid(self, value: Any = None) -> bool:
        check_value = value if value is not None else self.value
        return check_value in self._allowed_values
        
    def expected(self) -> str:
        return f"One of: {', '.join(map(str, self._allowed_values))}"

class Bool(Choice):
    _allowed_values = [True, False]

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create a checkbox for boolean input."""
        widget = QCheckBox()

        if self.value is not None:
            widget.setChecked(bool(self.value))

        def handle_toggle(checked: bool):
            self.value = checked
            changed()

        widget.toggled.connect(handle_toggle)
        self._widget = widget
        return widget
    
    def expected(self) -> str:
        """Return expected input description for boolean."""
        return "True or False"

class Binning(Choice):
    """Binning options for the camera."""
    _allowed_values = [1, 2, 3, 4]

class NasmythPort(Choice):
    """Nasmyth port options."""
    _allowed_values = [1, 2]

class StatusValue(str, Enum):
    """Enumeration for status values."""
    WAITING = "WAITING"
    BUSY = "BUSY"
    DONE = "DONE"
    FAILED = "FAILED"

    def __str__(self):
        return self.value

class Status(Choice):
    """Status options."""
    _allowed_values = [s.value for s in StatusValue]

class Telescope(Choice):
    """Telescope selection."""
    _allowed_values = [1, 2, 3, 4]

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._button_group = QButtonGroup(container)
        self._button_group.setExclusive(True)

        # Create radio buttons for each telescope
        for telescope_id in self._allowed_values:
            radio_btn = QRadioButton(str(telescope_id))
            layout.addWidget(radio_btn)
            self._button_group.addButton(radio_btn, telescope_id)

            # Check if this should be the selected button
            if self.value == telescope_id:
                radio_btn.setChecked(True)
                
        def handle_selection(telescope_id: int):
            self.value = telescope_id
            changed()

        self._button_group.idClicked.connect(handle_selection)
        self._widget = container
        return container

class TelescopeWithNone(Telescope):
    """Telescope selection including 'None' option."""
    _allowed_values = [0, 1, 2, 3, 4]

class Float(BaseClass):
    """Floating-point number with optional min/max bounds."""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    dependencies = ['telescope'] # some of these depend on selected telescope

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        widget = QLineEdit()
        widget.setPlaceholderText(self.expected())

        if self.value is not None:
            widget.setText(str(self.value))
        
        validator = QDoubleValidator()
        if self.min_value is not None:
            validator.setBottom(self.min_value)
        if self.max_value is not None:
            validator.setTop(self.max_value)
        widget.setValidator(validator)

        def handle_change(text: str):
            is_valid = self.isValid(text) if text else False
            self.value = float(text) if is_valid else text
            changed()

        widget.textChanged.connect(handle_change)
        self._widget = widget
        return widget
    
    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """Called when a dependency changes. Update based on telescope."""
        if name == 'telescope':
            self._update_widget_state(value)

    def _update_widget_state(self, telescope: Optional[int]) -> None:
        """Update widget state based on selected telescope."""
        if telescope is None or telescope == 0:
            return
        config_value = find_config_value(TELESCOPES[telescope], self.name)
        if config_value is None or not self.isValid(config_value):
            return
        # Update value and UI
        self.value = config_value
        if isinstance(self._widget, QLineEdit):
            self._widget.setPlaceholderText(f"{self.expected()} (default: {config_value})")
            self._widget.setText(str(config_value))

    def isValid(self, value: Any = None) -> bool:
        """Check if the value is a valid float within bounds."""
        check_value = value if value is not None else self.value

        try:
            float_value = float(check_value)
            if self.min_value is not None and float_value < self.min_value:
                return False
            
            if self.max_value is not None and float_value > self.max_value:
                return False
            
            return True
        except:
            return False

    def expected(self) -> str:
        if self.min_value is not None and self.max_value is not None:
            return f"{self.min_value} <= float <= {self.max_value}"
        elif self.min_value is not None:
            return f"float >= {self.min_value}"
        elif self.max_value is not None:
            return f"float <= {self.max_value}"
        else:
            return "float"

class FocalLength(Float):
    """Focal length"""
    min_value = 0.0
    max_value = 28.0

class String(BaseClass):
    """String value validator."""
       
    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        widget = QLineEdit()
        widget.setPlaceholderText(self.expected())

        if self.value is not None:
            widget.setText(str(self.value))

        def handle_change(text: str):
            self.value = text
            changed()

        widget.textChanged.connect(handle_change)
        self._widget = widget
        return widget

    def isValid(self, value: Any = None) -> bool:
        check_value = value if value is not None else self.value
        try:
            str(check_value)
            return True
        except:
            return False

    def expected(self) -> str:
        """Return expected input description"""
        return "string"

class ObjectName(String):
    """String value with object catalog search functionality."""

    ICON_SIZE = QSize(20, 20)

    
    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create input widget with search button for object lookup."""
        # Create horizontal widget
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Create text input
        text_input = QLineEdit()
        text_input.setPlaceholderText(self.expected())
        
        if self.value is not None:
            text_input.setText(str(self.value))
        
        def handle_text_change(text: str):
            self.value = text
            changed()
            # Enable/disable search button based on text
            search_button.setEnabled(bool(text.strip()))
        
        text_input.textChanged.connect(handle_text_change)
        
        # Create search button magnifying-glass
        search_button = QPushButton()
        search_button.setIcon(qta.icon('fa6s.magnifying-glass'))
        search_button.setIconSize(self.ICON_SIZE)
        search_button.setToolTip("Search object coordinates")
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        search_button.setEnabled(bool(self.value))
        search_button.clicked.connect(lambda: self._search_object(search_button))
        
        layout.addWidget(text_input)
        layout.addWidget(search_button)
        
        self._widget = widget
        return widget
    
    def _search_object(self, button: QPushButton) -> None:
        """Search for object in catalog and update RA/DEC in context."""
        
        # Get and normalize object name
        object_name = self.value.strip()
        
        if not object_name:
            self._show_feedback(button, False)
            return
        
        # Load catalog from JSON file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "object_catalog.json")
        
        catalog = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    catalog = json.load(f)
            except Exception as e:
                return
        else:
            return
        
        # Look up in catalog
        if object_name not in catalog:
            self._show_feedback(button, False)
            return
        
        coords = catalog[object_name]
        ra_value = coords["RA"]
        dec_value = coords["DEC"]
        
        # Check if context has RA and DEC fields
        try:
            # Try to update RA
            if 'RA' not in self.context._values.keys():
                self._show_feedback(button, False)
                return
            
            # Try to update DEC
            if 'DEC' not in self.context._values.keys():
                self._show_feedback(button, False)
                return
            
            # Update both values
            self.context.set('RA', ra_value)
            self.context.set('DEC', dec_value)
            
            # Show success feedback
            self._show_feedback(button, True)

            
        except Exception as e:
            self._show_feedback(button, False)
    
    def _show_feedback(self, button: QPushButton, success: bool) -> None:
        """Show visual feedback on the button."""
        # Store original style
        original_style = button.styleSheet()
        
        # Update button appearance
        if success:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                }
            """)
            icon = qta.icon('fa6s.check')
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                }
            """)
            icon = qta.icon('fa6s.xmark')
        
        button.setIcon(icon)
        button.setIconSize(self.ICON_SIZE)
        
        # Reset after 500 milliseconds
        QTimer.singleShot(500, lambda: self._reset_button(button, original_style))
    
    def _reset_button(self, button: QPushButton, original_style: str) -> None:
        """Reset button to original state."""
        button.setStyleSheet(original_style)
        button.setIcon(qta.icon('fa6s.magnifying-glass'))
        button.setIconSize(self.ICON_SIZE)
        button.setToolTip("Search object coordinates")
    
    def expected(self) -> str:
        """Return expected input description."""
        return "Object name (e.g., M31, NGC 253)"

class Timestamp(String):
    """Timestamp validator supporting HH:MM, HH:MM:SS, and full YYYY-MM-DD HH:MM:SS formats."""

    # Time format patterns
    _TIME_FORMAT = r"^\d{2}:\d{2}$"
    _TIME_WITH_SECONDS_FORMAT = r"^\d{2}:\d{2}:\d{2}$"
    _FULL_DATETIME_FORMAT = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    
    # Noon threshold for day rollover
    _NOON_TIME = datetime.strptime("12:00", "%H:%M").time()
    _NOON_TIME_WITH_SECONDS = datetime.strptime("12:00:00", "%H:%M:%S").time()

    def isValid(self, value: Any = None) -> bool:
        check_value = value if value is not None else self.value

        if check_value is None:
            return False

        try:
            check_value = str(check_value)
            
            # Check HH:MM format
            if re.match(self._TIME_FORMAT, check_value):
                datetime.strptime(check_value, "%H:%M")
                return True
            
            # Check HH:MM:SS format
            if re.match(self._TIME_WITH_SECONDS_FORMAT, check_value):
                datetime.strptime(check_value, "%H:%M:%S")
                return True
            
            # Check full YYYY-MM-DD HH:MM:SS format
            datetime.strptime(check_value, "%Y-%m-%d %H:%M:%S")
            return True

        except:
            return False

    def to_full(self, value: Any = None) -> str:
        """
        Format the timestamp to full 'YYYY-MM-DD HH:MM:SS' using context date for partial times.
        Raises ValueError if the timestamp is invalid or if context date is not set.
        Which should never happen as isValid is called first.        
        """

        value = value if value is not None else self.value

        base_date = self.context.dates._date
        if base_date is None:
            raise ValueError("Cannot convert to full timestamp without a base date.")
        
        if not self.isValid(value):
            raise ValueError("Invalid timestamp format.")

        value_str = str(value)

        # Handle HH:MM format
        if re.match(self._TIME_FORMAT, value_str):
            time_object = datetime.strptime(value_str, "%H:%M").time()
            dt = datetime.combine(base_date, time_object)

            # Add a day if time is before noon
            if time_object < self._NOON_TIME:
                dt += timedelta(days=1)

            return dt.strftime("%Y-%m-%d %H:%M:%S")

        # Handle HH:MM:SS format
        if re.match(self._TIME_WITH_SECONDS_FORMAT, value_str):
            time_object = datetime.strptime(value_str, "%H:%M:%S").time()
            dt = datetime.combine(base_date, time_object)

            # Add a day if time is before noon
            if time_object < self._NOON_TIME_WITH_SECONDS:
                dt += timedelta(days=1)

            return dt.strftime("%Y-%m-%d %H:%M:%S")

        # Already in full datetime format
        return value_str

    def expected(self) -> str:
        """Return expected input description"""
        return "HH:MM | HH:MM:SS"

class MechanicalAngle(BaseClass):
    """Mechanical angle validator with telescope-dependent bounds."""
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    dependencies = ['telescope'] # depends on selected telescope

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        """Create input widget for mechanical angle."""
        widget = QLineEdit()
        widget.setPlaceholderText(self.expected())
        widget.setValidator(QIntValidator())

        # Set default value if none provided
        if self.value is None:
            self.value = 180
            widget.setText("180")
        else:
            widget.setText(str(self.value))

        def handle_change(text: str):
            is_valid = self.isValid(text) if text else False
            self.value = int(text) if is_valid else text
            changed()

        widget.textChanged.connect(handle_change)
        self._widget = widget
        return widget
    
    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """Called when dependency changes. Updates when telescope changes."""
        if name == 'telescope':
            self.update_limits(value)
            self.update_widget_state(value)

    def update_widget_state(self, telescope: Optional[int]) -> None:
        """Enable/disable widget and update placeholder based on telescope."""
        if isinstance(self._widget, QLineEdit):
            self._widget.setPlaceholderText(self.expected())
            if telescope is None:
                self._widget.setEnabled(False)
            else:
                self._widget.setEnabled(True)

    def update_limits(self, telescope: Optional[int]) -> None:
        """Update limits based on selected telescope."""
        if telescope is None or telescope == 0:
            self.min_value = 0
            self.max_value = 360
        else:
            self.min_value = TELESCOPES[telescope].ROTATOR.LIMIT_LOW
            self.max_value = TELESCOPES[telescope].ROTATOR.LIMIT_HIGH

    def isValid(self, value: Any = None) -> bool:
        check_value = value if value is not None else self.value

        try:
            int_value = int(check_value)

            if self.min_value is None or self.max_value is None:
                return False
            
            return self.min_value <= int_value <= self.max_value

        except:
            return False

    def expected(self) -> str:
        """Return expected min max."""

        if self.min_value is None or self.max_value is None:
            return "Select a telescope first"

        return f"{self.min_value} <= int <= {self.max_value}"

class FilterWheel(BaseClass):
    """Filter wheel selection based on selected telescope."""
    dependencies = ['telescope'] # depends on selected telescope

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.options = {}

    def input_widget(self, changed: Callable[[], None]) -> QWidget:
        widget = QComboBox()
        widget.setStyleSheet("QComboBox { combobox-popup: 0; }")
        
        self._populate_widget()

        def handle_change(index):
            # Filter positions are 1-based
            self.value = index + 1
            changed()

        # Set initial selection if value is set
        if self.value is not None and 1 <= self.value <= len(self.options):
            widget.setCurrentIndex(self.value - 1)

        widget.currentIndexChanged.connect(handle_change)
        self._widget = widget
        return widget
    
    def _on_dependency_changed(self, name: str, value: Any) -> None:
        """React to telescoep changes."""
        if name == 'telescope':
            self._set_default_value(value)
            self._populate_widget()

    def _set_default_value(self, telescope: Optional[int]) -> None:
        """Set default filter value based on selected telescope."""
        has_filterwheel = TELESCOPES[telescope].CAMERA.HAS_FILTERWHEEL if telescope and telescope != 0 else False
        
        # Set default value
        if self.options and has_filterwheel:
            self.value = 1
        else:
            self.value = None

    def _populate_widget(self) -> None:
        """Populate the combo box with filter options based on the selected telescope."""

        if not isinstance(self._widget, QComboBox):
            return

        self._widget.blockSignals(True)
        self._widget.clear()
        telescope = self.context.telescope
        
        if telescope is None or telescope == 0:
            self._widget.addItems(["Select telescope first"])
            self._widget.setEnabled(False)
            self.options = {}
            self._widget.blockSignals(False)
            return
        
        has_filterwheel = TELESCOPES[telescope].CAMERA.HAS_FILTERWHEEL
        self.options = TELESCOPES[telescope].FILTERWHEEL.FILTERS
        
        if has_filterwheel and self.options:
            self._widget.addItems(self.options.values())
            self._widget.setEnabled(True)
        else:
            self._widget.addItems(["N/A"])
            self._widget.setEnabled(False)
        
        self._widget.blockSignals(False)

    def format(self) -> Any:
        """
        Return the selected filter key
        If not filterwheel available, return 0
        """
        telescope = self.context.telescope
        
        if telescope is None or telescope == 0:
            return 0
        
        has_filterwheel = TELESCOPES[telescope].CAMERA.HAS_FILTERWHEEL
        
        if not has_filterwheel:
            return 0
        
        if self.value is None:
            return 0

        return self.value


    def isValid(self, value: Any = None) -> bool:
        check_value = value if value is not None else self.value

        try:

            telescope = self.context.telescope
            
            if telescope is None or telescope == 0:
                return False
            
            has_filterwheel = TELESCOPES[telescope].CAMERA.HAS_FILTERWHEEL
            
            if not has_filterwheel:
                return True
            
            return 1 <= int(check_value) <= len(TELESCOPES[telescope].FILTERWHEEL.FILTERS)
        except:
            return False

    def expected(self) -> str:
        """Return expected input description based on selected telescope."""
        telescope = self.context.telescope

        if telescope is None or telescope == 0:
            return "Select telescope first"
        
        has_filterwheel = TELESCOPES[telescope].CAMERA.HAS_FILTERWHEEL
        
        if not has_filterwheel:
            return "No filter wheel available"
        
        return "Select filter"

@dataclass
class CameraConfig:
    GAIN: int
    OFFSET: int
    BINNING: int
    HAS_FILTERWHEEL: bool

@dataclass
class FilterWheelConfig:
    FILTERS: Dict[str, str]

@dataclass
class AutoFocuserConfig:
    FOCUS_START: float
    FOCUS_STEPS: int
    FOCUS_STEP_SIZE: float
    EXPOSURE_TIME: int
    DARKMASTER: str
    INNER: bool
    QUANTILE: float

@dataclass
class PlateSolverConfig:
    EXPOSURE_TIME_US: int
    MAX_ITERATIONS: int

@dataclass
class TelescopeDetailsConfig:
    MAX_ALTITUDE: int
    MIN_ALTITUDE: int
    PARK_ALTITUDE: int
    PARK_AZIMUTH: int
    NASMYTH_PORT: int

@dataclass
class RotatorConfig:
    LIMIT_LOW: int
    LIMIT_HIGH: int

@dataclass
class DefaultsConfig:
    PM_RA: float
    PM_DEC: float
    REF_EPOCH: float

@dataclass
class TelescopeConfig:
    ROTATOR: RotatorConfig
    TELESCOPE: TelescopeDetailsConfig
    CAMERA: CameraConfig
    FILTERWHEEL: FilterWheelConfig
    AUTOFOCUSER: AutoFocuserConfig
    PLATESOLVER: PlateSolverConfig
    DEFAULTS: DefaultsConfig

def getConstants(configfile):
    """Load ROTATOR constants from a config file."""
    config = ConfigParser()
    config.read(configfile)

    rotator = RotatorConfig(
        LIMIT_LOW=int(config.get("ROTATOR", "limit_low")),
        LIMIT_HIGH=int(config.get("ROTATOR", "limit_high"))
    )
    telescope = TelescopeDetailsConfig(
        MAX_ALTITUDE=int(config.get("TELESCOPE", "max_altitude")),
        MIN_ALTITUDE=int(config.get("TELESCOPE", "min_altitude")),
        PARK_ALTITUDE=int(config.get("TELESCOPE", "park_altitude")),
        PARK_AZIMUTH=int(config.get("TELESCOPE", "park_azimuth")),
        NASMYTH_PORT=int(config.get("TELESCOPE", "nasmyth_port"))
    )
    camera = CameraConfig(
        GAIN=int(config.get("CAMERA", "gain")),
        OFFSET=int(config.get("CAMERA", "offset")),
        BINNING=int(config.get("CAMERA", "binning")),
        HAS_FILTERWHEEL=config.getboolean("CAMERA", "has_filterwheel")
    )
    filterwheel = FilterWheelConfig(
        FILTERS={k: v for k, v in config.items("FILTERWHEEL")}
    )
    autofocuser = AutoFocuserConfig(
        FOCUS_START=float(config.get("AUTOFOCUSER", "focus_start")),
        FOCUS_STEPS=int(config.get("AUTOFOCUSER", "focus_steps")),
        FOCUS_STEP_SIZE=float(config.get("AUTOFOCUSER", "focus_step_size")),
        EXPOSURE_TIME=int(config.get("AUTOFOCUSER", "exposure_time")),
        DARKMASTER=config.get("AUTOFOCUSER", "darkmaster"),
        INNER=config.getboolean("AUTOFOCUSER", "inner"),
        QUANTILE=float(config.get("AUTOFOCUSER", "quantile"))
    )
    platesolver = PlateSolverConfig(
        EXPOSURE_TIME_US=int(config.get("PLATESOLVER", "exposure_time_us")),
        MAX_ITERATIONS=int(config.get("PLATESOLVER", "max_iterations"))
    )
    defaults = DefaultsConfig(
        PM_RA=float(config.get("DEFAULTS", "pm_RA")),
        PM_DEC=float(config.get("DEFAULTS", "pm_DEC")),
        REF_EPOCH=float(config.get("DEFAULTS", "ref_epoch"))
    )

    return TelescopeConfig(
        ROTATOR=rotator,
        TELESCOPE=telescope,
        CAMERA=camera,
        FILTERWHEEL=filterwheel,
        AUTOFOCUSER=autofocuser,
        PLATESOLVER=platesolver,
        DEFAULTS=defaults
    )

# Load all telescope configs
TELESCOPES: dict[int, TelescopeConfig] = {t : getConstants(cfg) for t,cfg in UNITCONFIGS.items()}

def find_config_value(config, key):
    for _, section_obj in vars(config).items():
        if hasattr(section_obj, key.upper()):
            return getattr(section_obj, key.upper())
    return None
