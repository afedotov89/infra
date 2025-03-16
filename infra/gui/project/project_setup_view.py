"""
Project setup view for the Infra GUI application.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QGridLayout, QScrollArea,
    QGroupBox, QFormLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon

from infra.config import Config
from infra.gui.resources.icons import get_icon
from infra.gui.widgets.custom_widgets import ActionCard, SectionHeader, TitleLabel


class ProjectSetupView(QWidget):
    """
    Project setup view for creating and configuring new projects.
    
    This view provides an interface for creating new infrastructure projects,
    with options for project name, location, and template selection.
    """
    
    def __init__(self, config: Config, parent=None):
        """Initialize the project setup view."""
        super().__init__(parent)
        self.config = config
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = SectionHeader("Создание проекта")
        main_layout.addWidget(header)
        
        # Description
        description = QLabel(
            "Создайте новый проект инфраструктуры или выберите существующий проект для работы."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        main_layout.addWidget(description)
        
        # Scroll area for main content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Container widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(30)
        
        # -- Quick Actions Section --
        quick_actions_header = QLabel("Быстрые действия")
        quick_actions_header.setStyleSheet("font-size: 18px; font-weight: 500;")
        scroll_layout.addWidget(quick_actions_header)
        
        # Grid layout for quick action cards
        quick_actions_grid = QGridLayout()
        quick_actions_grid.setSpacing(15)
        
        # Add action cards
        create_project_card = ActionCard(
            get_icon("project"),
            "Новый проект",
            "Создать новый проект инфраструктуры с нуля"
        )
        create_project_card.clicked.connect(self._on_create_project)
        quick_actions_grid.addWidget(create_project_card, 0, 0)
        
        open_project_card = ActionCard(
            get_icon("project"),
            "Открыть проект",
            "Открыть существующий проект инфраструктуры"
        )
        open_project_card.clicked.connect(self._on_open_project)
        quick_actions_grid.addWidget(open_project_card, 0, 1)
        
        import_project_card = ActionCard(
            get_icon("repo"),
            "Импорт из Git",
            "Импортировать проект из Git репозитория"
        )
        import_project_card.clicked.connect(self._on_import_project)
        quick_actions_grid.addWidget(import_project_card, 0, 2)
        
        # Add templates section
        templates_card = ActionCard(
            get_icon("templates"),
            "Шаблоны проектов",
            "Создать проект на основе готового шаблона"
        )
        templates_card.clicked.connect(self._on_templates)
        quick_actions_grid.addWidget(templates_card, 1, 0)
        
        # Add the grid to the main layout
        scroll_layout.addLayout(quick_actions_grid)
        
        # -- New Project Form Section --
        new_project_group = QGroupBox("Создание нового проекта")
        new_project_layout = QFormLayout(new_project_group)
        new_project_layout.setContentsMargins(15, 25, 15, 15)
        new_project_layout.setSpacing(12)
        
        # Project form fields
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Введите название проекта")
        new_project_layout.addRow("Название проекта:", self.project_name)
        
        # Project path selection with browse button
        path_layout = QHBoxLayout()
        self.project_path = QLineEdit()
        self.project_path.setPlaceholderText("Выберите директорию для проекта")
        path_layout.addWidget(self.project_path)
        
        browse_button = QPushButton("Обзор...")
        browse_button.clicked.connect(self._on_browse_path)
        path_layout.addWidget(browse_button)
        
        new_project_layout.addRow("Расположение:", path_layout)
        
        # Create project button
        create_button = QPushButton("Создать проект")
        create_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-weight: 500;
            }
        """)
        create_button.clicked.connect(self._on_create_project_action)
        
        # Add button to form layout
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(create_button)
        
        new_project_layout.addRow("", button_container)
        
        # Add new project form to main layout
        scroll_layout.addWidget(new_project_group)
        
        # Add a spacer at the bottom
        scroll_layout.addStretch()
        
        # Set the scroll content
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def _on_create_project(self):
        """Handle create project card click."""
        # Scroll to the project form
        pass
    
    def _on_open_project(self):
        """Handle open project card click."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        file_dialog.setWindowTitle("Открыть проект")
        if file_dialog.exec():
            selected_dir = file_dialog.selectedFiles()[0]
            self._open_project(selected_dir)
    
    def _on_import_project(self):
        """Handle import project card click."""
        # Show Git repository import dialog
        pass
    
    def _on_templates(self):
        """Handle templates card click."""
        # Navigate to templates view
        pass
    
    def _on_browse_path(self):
        """Handle browse button click to select project directory."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        file_dialog.setWindowTitle("Выберите директорию для проекта")
        if file_dialog.exec():
            selected_dir = file_dialog.selectedFiles()[0]
            self.project_path.setText(selected_dir)
    
    def _on_create_project_action(self):
        """Handle create project button click."""
        project_name = self.project_name.text().strip()
        project_path = self.project_path.text().strip()
        
        # Validate inputs
        if not project_name:
            # Show error
            return
        
        if not project_path:
            # Show error
            return
        
        # Create the project
        # This would call into the Infra API to create the project
        # Then navigate to the project dashboard
        pass
    
    def _open_project(self, project_path):
        """Open an existing project."""
        # Load the project configuration
        # This would call into the Infra API to load the project
        # Then navigate to the project dashboard
        pass 