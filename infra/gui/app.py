#!/usr/bin/env python3
"""
Main GUI application entry point.
"""

import sys
import platform
import ctypes
import logging
from functools import partial

from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtCore import Qt, QSettings, QEvent, QSize, QObject
from PyQt6.QtGui import QIcon, QPalette, QColor, QFontDatabase

from infra.config import Config
from infra.gui.main_window import MainWindow
from infra.gui.resources.styles import get_style

# Настройка логгера для диагностики проблем
logger = logging.getLogger(__name__)


def set_macos_appearance(app):
    """Set up macOS specific appearance settings."""
    if platform.system() == "Darwin":
        logger.info("Configuring macOS appearance")
        
        # Включение поддержки high DPI (Retina)
        # В новых версиях PyQt6 некоторые атрибуты были переименованы/перемещены
        try:
            # Пробуем использовать атрибуты из новых версий
            app.setAttribute(getattr(Qt.ApplicationAttribute, "HighDpiScaleFactorRoundingPolicy", None))
            logger.info("Set HighDpiScaleFactorRoundingPolicy")
        except (AttributeError, TypeError):
            # Пробуем использовать атрибуты из старых версий
            try:
                app.setAttribute(getattr(Qt, "AA_UseHighDpiPixmaps", None))
                logger.info("Set AA_UseHighDpiPixmaps")
            except (AttributeError, TypeError):
                logger.warning("Could not set HiDPI attributes, they may be unavailable")
        
        # Настройка нативных меню macOS
        try:
            # Сначала проверяем современное имя атрибута
            if hasattr(Qt.ApplicationAttribute, "DontUseNativeMenuBar"):
                app.setAttribute(Qt.ApplicationAttribute.DontUseNativeMenuBar, False)
                logger.info("Set DontUseNativeMenuBar (new style)")
            elif hasattr(Qt.ApplicationAttribute, "AA_DontUseNativeMenuBar"):
                app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)
                logger.info("Set AA_DontUseNativeMenuBar (old style)")
            else:
                logger.warning("Native menu bar attributes not found")
        except Exception as e:
            logger.warning(f"Error setting native menu: {e}")
        
        # Set fusion style for modern look
        app.setStyle("Fusion")
        
        # Use the system accent color for highlights
        try:
            # Import PyObjC modules for macOS integration
            # This won't work without PyObjC installed
            from AppKit import NSApp, NSAppearance, NSApplication
            from AppKit import NSColor, NSControlTintDefaultValue
            
            # Use native macOS appearance mode
            NSApp.setAppearance_(NSAppearance.appearanceNamed_(
                "NSAppearanceNameAqua" 
                if is_dark_mode() else 
                "NSAppearanceNameVibrantLight"
            ))
            
            # Use system accent color
            tint_color = NSColor.controlAccentColor()
            r, g, b, _ = tint_color.getRed_green_blue_alpha_(None, None, None, None)
            accent_color = QColor(int(r * 255), int(g * 255), int(b * 255))
            
            # Apply to palette
            palette = app.palette()
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Highlight, accent_color)
            app.setPalette(palette)
            logger.info("Applied system accent color")
        except ImportError:
            logger.info("PyObjC not available, using default accent color")
        except Exception as e:
            logger.warning(f"Error setting accent color: {e}")


def is_dark_mode():
    """Detect if the system is in dark mode."""
    if platform.system() == "Darwin":
        try:
            # Try to determine if macOS is in dark mode
            # This requires the Objective-C bridge
            from AppKit import NSAppearance
            appearance = NSAppearance.currentAppearance().name() or ""
            return "Dark" in str(appearance)
        except (ImportError, AttributeError):
            # Fallback: use a simpler method without PyObjC
            # This might not be as accurate
            try:
                import subprocess
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True, text=True
                )
                return result.stdout.strip() == "Dark"
            except (subprocess.SubprocessError, FileNotFoundError):
                return False
    elif platform.system() == "Windows":
        try:
            # Windows 10 1903+ dark mode detection
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except (ImportError, FileNotFoundError, OSError):
            return False
    else:
        # Linux/Unix dark mode detection is more complex and varies by DE
        # This is a very basic implementation
        try:
            import subprocess
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True, text=True
            )
            theme = result.stdout.strip().lower().replace("'", "")
            return "dark" in theme
        except (subprocess.SubprocessError, FileNotFoundError):
            return False


def add_animation_effects(app):
    """Add platform-appropriate animation effects."""
    if platform.system() == "Darwin":
        # Smooth animations are built into macOS
        try:
            # Проверяем доступность API анимаций
            if hasattr(Qt, "UIEffect"):
                app.setEffectEnabled(Qt.UIEffect.AnimateCombo, True)
                app.setEffectEnabled(Qt.UIEffect.AnimateMenu, True)
                app.setEffectEnabled(Qt.UIEffect.AnimateTooltip, True)
                logger.info("Enabled animation effects")
            else:
                logger.info("UIEffect not found in Qt")
        except Exception as e:
            logger.warning(f"Could not enable animations: {e}")
    
    # Use animated tooltips on all platforms
    try:
        app.installEventFilter(_TooltipFilter())
        logger.info("Installed tooltip filter")
    except Exception as e:
        logger.warning(f"Could not install tooltip filter: {e}")


class _TooltipFilter(QObject):
    """Event filter for custom tooltip behavior."""
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ToolTip:
            # Custom tooltip behavior - could be expanded with styling
            return False  # Let default handler process
        return False  # Don't filter other events


def load_system_fonts():
    """Load additional system fonts for better rendering."""
    if platform.system() == "Darwin":
        # macOS system fonts are already available
        pass
    elif platform.system() == "Windows":
        # Add some Windows fonts if we need them
        pass
    else:
        # Linux fonts
        pass
    
    # Ensure Qt knows about the fonts
    # We could add custom fonts here if needed
    # QFontDatabase.addApplicationFont(":/fonts/Roboto-Regular.ttf")
    pass


def main():
    """Launch the GUI application."""
    # Настройка логгирования для отладки
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Логирование начала запуска приложения
    logger.info("Starting Infra GUI Application")
    logger.info(f"Running on {platform.system()} {platform.release()}")
    logger.info(f"Python {platform.python_version()}")
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Infra")
    app.setOrganizationName("InfraTech")
    app.setOrganizationDomain("example.com")
    
    # Configure for platform
    set_macos_appearance(app)
    
    # Add animation effects
    add_animation_effects(app)
    
    # Load system fonts
    load_system_fonts()
    
    # Load config
    config = Config()
    
    try:
        config.load()
        logger.info("Config loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        config = Config()  # Use default config
    
    # Detect current system theme
    theme = "dark" if is_dark_mode() else "light"
    logger.info(f"Detected system theme: {theme}")
    
    # Load application settings
    settings = QSettings()
    
    # Override system theme if set in settings
    if settings.contains("gui/theme"):
        theme = settings.value("gui/theme")
        logger.info(f"Override theme from settings: {theme}")
    
    # Apply the style from our custom module
    app.setStyleSheet(get_style(theme))
    
    # Create and show the main window
    main_window = MainWindow(config, settings, theme)
    main_window.show()
    logger.info("Main window displayed")
    
    # Run the application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 