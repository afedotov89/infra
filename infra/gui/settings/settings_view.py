"""
Settings view for the Infra GUI application.
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings

from infra.config import Config


class SettingsView(QWidget):
    """
    Settings view for configuring the application.
    
    Allows users to configure:
    - The theme (light, dark, system)
    - The path to the .env file
    - Other global settings
    """
    
    def __init__(self, config: Config, settings: QSettings, parent=None):
        """Initialize the settings view."""
        super().__init__(parent)
        self.config = config
        self.settings = settings
        
        # Create the UI
        self._create_ui()
        
        # Load settings
        self._load_settings()
    
    def _create_ui(self):
        """Create the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Title
        title_label = QLabel("Настройки")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Add some spacing
        main_layout.addSpacing(10)
        
        # Appearance group
        appearance_group = QGroupBox("Внешний вид")
        appearance_layout = QFormLayout(appearance_group)
        
        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Темная", "Системная"])
        appearance_layout.addRow("Тема:", self.theme_combo)
        
        main_layout.addWidget(appearance_group)
        
        # Configuration group
        config_group = QGroupBox("Конфигурация")
        config_layout = QFormLayout(config_group)
        
        # .env file selector
        env_layout = QHBoxLayout()
        self.env_path_edit = QLineEdit()
        self.env_path_edit.setReadOnly(True)
        env_layout.addWidget(self.env_path_edit)
        
        self.browse_button = QPushButton("Обзор...")
        self.browse_button.clicked.connect(self._browse_env_file)
        env_layout.addWidget(self.browse_button)
        
        config_layout.addRow("Файл .env:", env_layout)
        
        # Default configuration
        self.create_default_button = QPushButton("Создать пример .env файла")
        self.create_default_button.clicked.connect(self._create_default_env)
        config_layout.addRow("", self.create_default_button)
        
        main_layout.addWidget(config_group)
        
        # Add some spacing
        main_layout.addSpacing(20)
        
        # Save and cancel buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self._save_settings)
        buttons_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.clicked.connect(self._load_settings)
        buttons_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Add a stretcher to push everything to the top
        main_layout.addStretch()
    
    def _load_settings(self):
        """Load settings from the settings object."""
        # Theme
        theme = self.settings.value("theme", "system")
        theme_map = {"light": "Светлая", "dark": "Темная", "system": "Системная"}
        self.theme_combo.setCurrentText(theme_map.get(theme, "Системная"))
        
        # .env path
        env_path = self.settings.value("env_path", "")
        self.env_path_edit.setText(env_path)
    
    def _save_settings(self):
        """Save settings to the settings object."""
        # Theme
        theme_map = {"Светлая": "light", "Темная": "dark", "Системная": "system"}
        theme = theme_map.get(self.theme_combo.currentText(), "system")
        self.settings.setValue("theme", theme)
        
        # .env path
        env_path = self.env_path_edit.text()
        self.settings.setValue("env_path", env_path)
        
        # Update label in status bar (parent's parent is the main window)
        main_window = self.parent().parent()
        if hasattr(main_window, "theme_label"):
            main_window.theme_label.setText(f"Theme: {theme.title()}")
        if hasattr(main_window, "env_path_label"):
            main_window.env_path_label.setText(f".env: {env_path}")
        
        # Show success message
        QMessageBox.information(
            self, 
            "Настройки сохранены", 
            "Настройки успешно сохранены.",
            QMessageBox.StandardButton.Ok
        )
        
        # Apply theme change immediately
        # This would typically require restarting the app
        # In a production app, we would have a theme manager that could switch on the fly
    
    def _browse_env_file(self):
        """Open a file dialog to browse for the .env file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл .env",
            str(Path.home()),
            "Env Files (*.env);;All Files (*)"
        )
        
        if file_path:
            self.env_path_edit.setText(file_path)
    
    def _create_default_env(self):
        """Create a default .env file in the user's home directory."""
        # Check if ~/.infra directory exists, create if not
        infra_dir = Path.home() / ".infra"
        if not infra_dir.exists():
            infra_dir.mkdir(parents=True)
        
        # Default .env file path
        default_env_path = infra_dir / ".env"
        
        # Check if file already exists
        if default_env_path.exists():
            # Ask for confirmation to overwrite
            reply = QMessageBox.question(
                self,
                "Файл уже существует",
                f"Файл {default_env_path} уже существует. Перезаписать?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Read example .env file from the project
        example_path = Path(__file__).parent.parent.parent.parent / ".env.example"
        
        if example_path.exists():
            with open(example_path, "r") as example_file:
                example_content = example_file.read()
            
            # Write content to the default file
            with open(default_env_path, "w") as default_file:
                default_file.write(example_content)
            
            # Update the env path edit
            self.env_path_edit.setText(str(default_env_path))
            
            # Show success message
            QMessageBox.information(
                self,
                "Файл создан",
                f"Пример файла .env создан по пути:\n{default_env_path}",
                QMessageBox.StandardButton.Ok
            )
        else:
            # Show error message
            QMessageBox.warning(
                self,
                "Ошибка",
                "Не удалось найти файл .env.example в проекте.",
                QMessageBox.StandardButton.Ok
            ) 