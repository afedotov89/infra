"""
Log widget for displaying colored log messages.
"""

import logging
from PyQt6.QtWidgets import (
    QTextEdit, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QComboBox, QLabel, QToolBar,
    QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor

# Define a custom log level for success messages
SUCCESS_LEVEL = 25  # Between INFO and WARNING
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


class LogWidget(QWidget):
    """
    A widget that displays colored log messages.
    
    This widget can be used to show log messages from various operations,
    with different colors for different log levels.
    """
    
    def __init__(self, parent=None):
        """Initialize the log widget."""
        super().__init__(parent)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar for log controls
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Create text edit for log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_text)
        
        # Initialize colors for different log levels
        self.level_colors = {
            logging.DEBUG: QColor(100, 100, 255),    # синий
            logging.INFO: QColor(0, 0, 0),           # черный (будет адаптироваться к теме)
            logging.WARNING: QColor(255, 170, 0),    # оранжевый
            logging.ERROR: QColor(255, 0, 0),        # красный
            logging.CRITICAL: QColor(200, 0, 0),     # темно-красный
            SUCCESS_LEVEL: QColor(0, 170, 0)         # зеленый
        }
        
        # Set minimum size
        self.setMinimumHeight(150)
    
    def _create_toolbar(self):
        """Create the toolbar with log control buttons."""
        toolbar = QToolBar()
        
        # Log level filter
        level_label = QLabel("Уровень:")
        toolbar.addWidget(level_label)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setCurrentText("INFO")
        toolbar.addWidget(self.level_combo)
        
        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        toolbar.addWidget(spacer)
        
        # Add auto-scroll checkbox
        self.auto_scroll = QCheckBox("Авто-прокрутка")
        self.auto_scroll.setChecked(True)
        toolbar.addWidget(self.auto_scroll)
        
        # Add clear button
        clear_button = QPushButton("Очистить")
        clear_button.clicked.connect(self.clear_log)
        toolbar.addWidget(clear_button)
        
        # Add save button
        save_button = QPushButton("Сохранить...")
        save_button.clicked.connect(self._save_log)
        toolbar.addWidget(save_button)
        
        return toolbar
    
    def clear_log(self):
        """Clear the log display."""
        self.log_text.clear()
    
    def _save_log(self):
        """Save the log contents to a file."""
        # This will be implemented later
        pass
    
    @pyqtSlot(str, int)
    def append_log_message(self, message, level=logging.INFO):
        """
        Append a message to the log with the specified level.
        
        Args:
            message: The message to append
            level: The log level (affects the color)
        """
        # Skip messages below the selected level
        selected_level = getattr(logging, self.level_combo.currentText())
        if level < selected_level:
            return
        
        # Get color for the level
        color = self.level_colors.get(level, QColor(0, 0, 0))
        
        # Set up text format
        format = QTextCharFormat()
        format.setForeground(color)
        
        # Append the message
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(message + "\n", format)
        
        # Auto-scroll if enabled
        if self.auto_scroll.isChecked():
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()
    
    def set_visible_with_message(self, visible, message=None, level=logging.INFO):
        """
        Show or hide the log widget with an optional initial message.
        
        Args:
            visible: Whether to show the widget
            message: Optional message to append when showing
            level: Log level for the message
        """
        if visible and message:
            self.append_log_message(message, level)
        
        self.setVisible(visible)


class LogHandler(logging.Handler):
    """
    A log handler that sends log messages to a LogWidget.
    
    This handler intercepts Python logging messages and sends them
    to a LogWidget for display.
    """
    
    def __init__(self, log_widget):
        """Initialize the handler with a log widget."""
        super().__init__()
        self.log_widget = log_widget
    
    def emit(self, record):
        """Process a log record by sending it to the log widget."""
        try:
            # Format the message
            msg = self.format(record)
            
            # Send to the log widget
            # Use invokeMethod to ensure thread safety
            self.log_widget.append_log_message(msg, record.levelno)
        except Exception:
            self.handleError(record) 