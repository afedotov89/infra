"""
Custom widgets for the Infra GUI application.

These widgets provide enhanced UI components with better styling
and macOS integration.
"""

from PyQt6.QtWidgets import (
    QPushButton, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint, QRect, QRectF
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QPainterPath, QPaintEvent


class CardButton(QPushButton):
    """
    A card-styled button that appears as a square card with an icon and text.
    Perfect for dashboards and landing pages.
    """
    
    def __init__(self, icon: QIcon, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setIcon(icon)
        self.setIconSize(QSize(32, 32))
        self.title = title
        self.description = description
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumSize(QSize(180, 120))
        self.setMaximumSize(QSize(180, 120))
        self.setProperty("class", "card-button")


class ActionCard(QFrame):
    """
    A card widget that displays an action with an icon, title and description.
    Has a hover effect and can be clicked to trigger an action.
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, icon: QIcon, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.description = description
        self.hovered = False
        
        self.setObjectName("actionCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(QSize(200, 120))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Icon and title in horizontal layout
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(32, 32))
        # Устанавливаем прозрачный фон для иконки
        icon_label.setStyleSheet("background-color: transparent;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setStyleSheet("font-weight: bold; font-size: 15px; color: white; background-color: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("cardDescription")
            desc_label.setWordWrap(True)
            
            # Светлый текст с прозрачным фоном
            desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: transparent;")
                
            layout.addWidget(desc_label)
        
        layout.addStretch()
    
    def enterEvent(self, event):
        self.hovered = True
        self.update()
    
    def leaveEvent(self, event):
        self.hovered = False
        self.update()
    
    def mousePressEvent(self, event):
        self.clicked.emit()
    
    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        
        # Определяем цвет подсветки в зависимости от темы
        highlight_color = QColor(0, 122, 255, 40)  # По умолчанию синий (светлая тема)
        
        # Проверяем, находимся ли мы в темном режиме
        parent_widget = self.parent()
        while parent_widget:
            if parent_widget.property("darkMode") is not None:
                dark_mode = parent_widget.property("darkMode")
                if dark_mode:
                    highlight_color = QColor(10, 132, 255, 60)  # Более яркий синий для темной темы
                break
            parent_widget = parent_widget.parent()
        
        if self.hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(highlight_color, 2))
            path = QPainterPath()
            # Преобразуем QRect в QRectF для совместимости с PyQt6
            rectf = QRectF(1.0, 1.0, float(self.width() - 2), float(self.height() - 2))
            path.addRoundedRect(rectf, 8.0, 8.0)
            painter.drawPath(path)


class TitleLabel(QLabel):
    """
    A styled label for section titles with proper typography and spacing.
    """
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 10px;
            padding-bottom: 5px;
            background-color: transparent;
        """)


class SectionHeader(QWidget):
    """
    A complete section header with title and optional action buttons.
    """
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 5)
        
        # Title
        self.title_label = TitleLabel(title)
        layout.addWidget(self.title_label)
        
        # Action buttons container
        self.actions_layout = QHBoxLayout()
        layout.addLayout(self.actions_layout)
        layout.addStretch()
    
    def add_action(self, icon: QIcon, tooltip: str, callback):
        """Add an action button to the header."""
        button = QPushButton()
        button.setIcon(icon)
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tooltip)
        button.setFixedSize(QSize(32, 32))
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        self.actions_layout.addWidget(button)
        return button 