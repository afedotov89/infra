"""
Main window implementation for the Infra GUI application.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTreeWidget, QTreeWidgetItem, QStackedWidget,
    QLabel, QStatusBar, QSplitter, QToolBar, QToolTip, QFrame
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap

from infra.config import Config
from infra.gui.settings.settings_view import SettingsView
from infra.gui.project.project_setup_view import ProjectSetupView
from infra.gui.logging.log_widget import LogWidget
from infra.gui.resources.icons import get_icon
from infra.gui.resources.styles import get_style


class MainWindow(QMainWindow):
    """
    Main window for the Infra GUI application.
    
    Provides the primary user interface with a sidebar navigation tree
    and a content area that changes based on the selected action.
    """
    
    def __init__(self, config: Config, settings: QSettings, theme="light", parent=None):
        """Initialize the main window."""
        super().__init__(parent)
        self.config = config
        self.settings = settings
        self.theme = theme
        
        # Устанавливаем атрибут для стилей в зависимости от темы
        self.setProperty("darkMode", self.theme == "dark")
        
        # Window setup
        self.setWindowTitle("Infra - Infrastructure Automation Toolkit")
        self.resize(1200, 800)
        
        # Применяем стили из модуля стилей
        self.setStyleSheet(get_style(self.theme))
        
        # Load window state if it exists
        self._load_window_state()
        
        # Create UI components
        self._create_actions()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Initialize the UI state
        self._show_section(0)  # Start with Project Setup
    
    def _load_window_state(self):
        """Load saved window state from settings."""
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))
    
    def _create_actions(self):
        """Create application actions."""
        # File menu actions
        self.exit_action = QAction("Выход", self)
        self.exit_action.triggered.connect(self.close)
        self.exit_action.setStatusTip("Выйти из приложения")
        
        # Help menu actions
        self.about_action = QAction("О программе", self)
        self.about_action.setStatusTip("Показать информацию о программе")
        # self.about_action.triggered.connect(self._show_about_dialog)
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction(self.exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Справка")
        help_menu.addAction(self.about_action)
    
    def _create_toolbar(self):
        """Создает панель инструментов"""
        toolbar = QToolBar("Основная панель", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        # Кнопка создания проекта
        create_project_action = QAction(get_icon("project"), "Создать проект", self)
        create_project_action.setStatusTip("Создать новый проект")
        create_project_action.triggered.connect(lambda: self._show_section(0))
        toolbar.addAction(create_project_action)
        
        # Кнопка создания репозитория
        create_repo_action = QAction(get_icon("repo"), "Создать репозиторий", self)
        create_repo_action.setStatusTip("Создать Git репозиторий")
        create_repo_action.triggered.connect(lambda: self._show_section(1))
        toolbar.addAction(create_repo_action)
        
        # Кнопка создания базы данных
        create_db_action = QAction(get_icon("database"), "Создать базу данных", self)
        create_db_action.setStatusTip("Создать базу данных")
        create_db_action.triggered.connect(lambda: self._show_section(2))
        toolbar.addAction(create_db_action)
        
        # Кнопка создания контейнера
        create_container_action = QAction(get_icon("container"), "Создать контейнер", self)
        create_container_action.setStatusTip("Создать контейнер")
        create_container_action.triggered.connect(lambda: self._show_section(3))
        toolbar.addAction(create_container_action)
        
        # Кнопка создания хранилища
        create_storage_action = QAction(get_icon("storage"), "Создать хранилище", self)
        create_storage_action.setStatusTip("Создать хранилище объектов")
        create_storage_action.triggered.connect(lambda: self._show_section(4))
        toolbar.addAction(create_storage_action)
        
        # Разделитель
        toolbar.addSeparator()
        
        # Кнопка шаблонов
        templates_action = QAction(get_icon("templates"), "Шаблоны", self)
        templates_action.setStatusTip("Просмотр шаблонов проектов")
        templates_action.triggered.connect(lambda: self._show_section(5))
        toolbar.addAction(templates_action)
        
        # Разделитель
        toolbar.addSeparator()
        
        # Кнопка настроек
        settings_action = QAction(get_icon("settings"), "Настройки", self)
        settings_action.setStatusTip("Открыть настройки приложения")
        settings_action.triggered.connect(lambda: self._show_section(6))
        toolbar.addAction(settings_action)
        
        # Добавляем тулбар к окну
        self.addToolBar(toolbar)
    
    def _create_central_widget(self):
        """Create the main window's central widget."""
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a horizontal splitter for sidebar and content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create sidebar with frame for better visual separation
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar_frame")  # Для CSS селектора
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create sidebar (navigation tree)
        self.navigation_tree = self._create_navigation_tree()
        sidebar_layout.addWidget(self.navigation_tree)
        
        # Add the sidebar frame to the splitter
        splitter.addWidget(sidebar_frame)
        
        # Create content area with better padding and margins
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Stacked widget to manage different pages
        self.stacked_widget = QStackedWidget()
        
        # Add pages to stacked widget
        self.project_setup_view = ProjectSetupView(self.config)
        self.stacked_widget.addWidget(self.project_setup_view)
        
        # Placeholder for other views
        # These will be replaced with actual implementations later
        repo_placeholder = QLabel("Create Repository View")
        repo_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        repo_placeholder.setStyleSheet("font-size: 16px;")
        self.stacked_widget.addWidget(repo_placeholder)
        
        db_placeholder = QLabel("Create Database View")
        db_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        db_placeholder.setStyleSheet("font-size: 16px;")
        self.stacked_widget.addWidget(db_placeholder)
        
        container_placeholder = QLabel("Create Container View")
        container_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_placeholder.setStyleSheet("font-size: 16px;")
        self.stacked_widget.addWidget(container_placeholder)
        
        bucket_placeholder = QLabel("Create Storage Bucket View")
        bucket_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bucket_placeholder.setStyleSheet("font-size: 16px;")
        self.stacked_widget.addWidget(bucket_placeholder)
        
        templates_placeholder = QLabel("Templates View")
        templates_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        templates_placeholder.setStyleSheet("font-size: 16px;")
        self.stacked_widget.addWidget(templates_placeholder)
        
        # Settings view
        self.settings_view = SettingsView(self.config, self.settings)
        self.stacked_widget.addWidget(self.settings_view)
        
        content_layout.addWidget(self.stacked_widget)
        
        # Create log widget
        self.log_widget = LogWidget()
        content_layout.addWidget(self.log_widget)
        
        # Hide log widget initially (will show when operations are running)
        self.log_widget.setVisible(False)
        
        # Add content container to splitter
        splitter.addWidget(content_container)
        
        # Set split ratio (30% sidebar, 70% content)
        splitter.setSizes([300, 900])
        
        # Set the central widget
        self.setCentralWidget(main_widget)
    
    def _create_navigation_tree(self):
        """Create the navigation tree widget."""
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setAnimated(True)
        tree.setIndentation(20)
        tree.setMinimumWidth(250)
        tree.setIconSize(QSize(24, 24))  # Увеличиваем размер иконок
        
        # Улучшаем визуализацию дерева
        tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: transparent;
            }
            QTreeWidget::branch:has-siblings:!adjoins-item {
                border-image: none;
                image: none;
            }
            QTreeWidget::branch:has-siblings:adjoins-item {
                border-image: none;
                image: none;
            }
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                border-image: none;
                image: none;
            }
        """)
        
        # Create top-level items with icons and tooltips
        project_setup_item = QTreeWidgetItem(tree, ["Настройка проекта"])
        project_setup_item.setIcon(0, get_icon("project"))
        project_setup_item.setToolTip(0, "Создание и настройка нового проекта")
        project_setup_item.setData(0, Qt.ItemDataRole.UserRole, 0)  # Индекс для stacked widget
        
        # Create Resources group
        create_resources_item = QTreeWidgetItem(tree, ["Создание ресурсов"])
        create_resources_item.setIcon(0, QIcon())  # Пустая иконка для группы
        create_resources_item.setToolTip(0, "Создание отдельных инфраструктурных ресурсов")
        create_resources_item.setExpanded(True)
        create_resources_item.setFlags(create_resources_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # Не выбираем группу
        
        # Add children to Create Resources
        repo_item = QTreeWidgetItem(create_resources_item, ["Репозиторий"])
        repo_item.setIcon(0, get_icon("repo"))
        repo_item.setToolTip(0, "Создать Git репозиторий")
        repo_item.setData(0, Qt.ItemDataRole.UserRole, 1)  # Индекс для stacked widget
        
        db_item = QTreeWidgetItem(create_resources_item, ["База данных"])
        db_item.setIcon(0, get_icon("database"))
        db_item.setToolTip(0, "Создать базу данных в облаке")
        db_item.setData(0, Qt.ItemDataRole.UserRole, 2)  # Индекс для stacked widget
        
        container_item = QTreeWidgetItem(create_resources_item, ["Контейнер"])
        container_item.setIcon(0, get_icon("container"))
        container_item.setToolTip(0, "Создать Docker контейнер")
        container_item.setData(0, Qt.ItemDataRole.UserRole, 3)  # Индекс для stacked widget
        
        bucket_item = QTreeWidgetItem(create_resources_item, ["Хранилище"])
        bucket_item.setIcon(0, get_icon("storage"))
        bucket_item.setToolTip(0, "Создать облачное хранилище объектов")
        bucket_item.setData(0, Qt.ItemDataRole.UserRole, 4)  # Индекс для stacked widget
        
        # Add Templates item
        templates_item = QTreeWidgetItem(tree, ["Шаблоны"])
        templates_item.setIcon(0, get_icon("templates"))
        templates_item.setToolTip(0, "Просмотр и управление шаблонами проектов")
        templates_item.setData(0, Qt.ItemDataRole.UserRole, 5)  # Индекс для stacked widget
        
        # Add Settings item
        settings_item = QTreeWidgetItem(tree, ["Настройки"])
        settings_item.setIcon(0, get_icon("settings"))
        settings_item.setToolTip(0, "Настройки приложения и окружения")
        settings_item.setData(0, Qt.ItemDataRole.UserRole, 6)  # Индекс для stacked widget
        
        # Connect selection signal
        tree.itemClicked.connect(self._on_navigation_item_clicked)
        
        return tree
    
    def _create_status_bar(self):
        """Create the status bar."""
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        
        # Status label
        self.status_label = QLabel("Готов к работе")
        status_bar.addWidget(self.status_label, 1)
        
        # User info (will be populated when user is authenticated)
        self.user_label = QLabel("Пользователь: Не авторизован")
        status_bar.addPermanentWidget(self.user_label)
        
        # Theme indicator
        theme_display = self.theme.title() if self.theme != "system" else "Системная"
        self.theme_label = QLabel(f"Тема: {theme_display}")
        status_bar.addPermanentWidget(self.theme_label)
        
        # Env file path
        env_path = self.settings.value("env_path", "Не настроен")
        self.env_path_label = QLabel(f".env: {env_path}")
        status_bar.addPermanentWidget(self.env_path_label)
    
    def _on_navigation_item_clicked(self, item, column):
        """Handle navigation tree item click."""
        # Check if item has UserRole data (section index)
        section_index = item.data(0, Qt.ItemDataRole.UserRole)
        if section_index is not None:
            self._show_section(section_index)
    
    def _show_section(self, index):
        """Show the specified section in the stacked widget."""
        if index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            
            # Обновляем статусную строку с контекстной информацией
            section_names = [
                "Настройка нового проекта",
                "Создание Git репозитория",
                "Создание базы данных",
                "Создание контейнера",
                "Создание хранилища объектов",
                "Просмотр шаблонов проектов",
                "Настройки приложения"
            ]
            
            if index < len(section_names):
                self.status_label.setText(f"Раздел: {section_names[index]}")
    
    def closeEvent(self, event):
        """Handle window close event to save state."""
        # Save window geometry and state
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event) 