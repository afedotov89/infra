"""
CSS styles for the Infra GUI application.
"""

# Base styles for all themes
BASE_STYLE = """
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

QTreeWidget {
    background-color: transparent;
    border: none;
}

QTreeWidget::item {
    height: 36px;
    border-radius: 4px;
    margin: 2px 4px;
    padding-left: 4px;
}

QGroupBox {
    margin-top: 15px;
    font-weight: bold;
    border: 1px solid;
    border-radius: 4px;
    padding: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    padding: 8px 16px;
    border-radius: 4px;
    border: none;
    font-weight: 500;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    padding: 8px;
    border-radius: 4px;
    border: 1px solid;
}

QProgressBar {
    border-radius: 4px;
    text-align: center;
    min-height: 10px;
}

QTabWidget::pane {
    border: 1px solid;
    border-radius: 4px;
    top: -1px;
}

QTabBar::tab {
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QHeaderView::section {
    padding: 8px;
    border: none;
    border-right: 1px solid;
    border-bottom: 1px solid;
}

QSplitter::handle {
    width: 1px;
    height: 1px;
}

QStatusBar {
    min-height: 22px;
}

/* Стили для карточек, которые всегда имеют темный фон */
#actionCard {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
}

#actionCard:hover {
    background-color: #353535;
    border: 1px solid #4d4d4d;
}

/* Все метки внутри карточек должны иметь прозрачный фон */
#actionCard QLabel {
    background-color: transparent;
}

/* Стили для заголовка и описания в карточках */
#cardTitle {
    font-weight: bold;
    font-size: 15px;
    color: white;
}

#cardDescription {
    color: rgba(255, 255, 255, 0.8);
}
"""

# Light theme styles
LIGHT_STYLE = """
QWidget {
    color: #333333;
    background-color: #ffffff;
}

QTreeWidget::item:selected {
    background-color: rgba(60, 60, 60, 0.1);
    color: #007aff;
}

QTreeWidget::item:hover:!selected {
    background-color: rgba(60, 60, 60, 0.05);
}

QFrame#sidebar_frame {
    background-color: #f5f5f7;
    border-right: 1px solid #e0e0e0;
}

QPushButton {
    background-color: #007aff;
    color: white;
}

QPushButton:hover {
    background-color: #3396ff;
}

QPushButton:pressed {
    background-color: #0062cc;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #888888;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    border-color: #dddddd;
    background-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #007aff;
}

QGroupBox {
    border-color: #dddddd;
}

QProgressBar {
    background-color: #f0f0f0;
    border: 1px solid #dddddd;
}

QProgressBar::chunk {
    background-color: #007aff;
    border-radius: 4px;
}

QTabWidget::pane {
    border-color: #dddddd;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #eeeeee;
    border: 1px solid #dddddd;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #ffffff;
}

QHeaderView::section {
    background-color: #f5f5f5;
    border-right-color: #dddddd;
    border-bottom-color: #dddddd;
}

QToolTip {
    border: 1px solid #cccccc;
    background-color: #ffffff;
    color: #000000;
    padding: 5px;
    border-radius: 3px;
    opacity: 200;
}

QToolBar {
    background-color: #f5f5f7;
    border-bottom: 1px solid #e0e0e0;
}

QSplitter::handle {
    background-color: #e0e0e0;
}
"""

# Dark theme styles
DARK_STYLE = """
QWidget {
    color: #ffffff;
    background-color: #222222;
}

QTreeWidget::item:selected {
    background-color: rgba(255, 255, 255, 0.15);
    color: #0a84ff;
}

QTreeWidget::item:hover:!selected {
    background-color: rgba(255, 255, 255, 0.07);
}

QFrame#sidebar_frame {
    background-color: #2d2d2d;
    border-right: 1px solid #3d3d3d;
}

QPushButton {
    background-color: #0a84ff;
    color: white;
}

QPushButton:hover {
    background-color: #409cff;
}

QPushButton:pressed {
    background-color: #0060b9;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    border-color: #555555;
    background-color: #333333;
    color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #0a84ff;
}

QGroupBox {
    border-color: #555555;
}

QProgressBar {
    background-color: #333333;
    border: 1px solid #555555;
}

QProgressBar::chunk {
    background-color: #0a84ff;
    border-radius: 4px;
}

QTabWidget::pane {
    border-color: #555555;
    background-color: #222222;
}

QTabBar::tab {
    background-color: #333333;
    border: 1px solid #555555;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #222222;
}

QHeaderView::section {
    background-color: #333333;
    border-right-color: #555555;
    border-bottom-color: #555555;
}

QToolTip {
    border: 1px solid #555555;
    background-color: #333333;
    color: #ffffff;
    padding: 5px;
    border-radius: 3px;
    opacity: 200;
}

QStatusBar {
    background-color: #333333;
    color: #dddddd;
}

QToolBar {
    background-color: #333333;
    border-bottom: 1px solid #444444;
}

QSplitter::handle {
    background-color: #444444;
}
"""

def get_style(theme="light"):
    """Return the combined CSS style for the requested theme."""
    if theme == "dark":
        return BASE_STYLE + DARK_STYLE
    else:
        return BASE_STYLE + LIGHT_STYLE