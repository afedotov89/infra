# Infra GUI Module

Graphical User Interface for the Infra infrastructure automation toolkit. This module provides a native macOS application for managing infrastructure components and project setup.

## Architecture

The GUI is built with PyQt6 (Qt6 for Python) and follows a modular architecture that mirrors the functionality provided by the CLI tool. The application features:

- Native macOS UI with theme detection
- Settings management with dark/light/system themes
- Form-based interfaces for project and resource setup
- Comprehensive logging system with color-coded output
- Direct integration with the CLI functionality

## Module Structure

```
gui/
├── README.md               # This file
├── __init__.py             # Module initialization
├── app.py                  # Main application entry point
├── main_window.py          # Main window implementation
├── resources/              # Application resources (icons, etc.)
├── logging/                # Logging components
│   ├── __init__.py
│   └── log_widget.py       # UI component for displaying logs
├── settings/               # Settings-related components
│   ├── __init__.py
│   └── settings_view.py    # Settings UI view
├── project/                # Project setup components
│   ├── __init__.py
│   └── project_setup_view.py  # Project setup UI view
├── create/                 # Resource creation components
│   ├── __init__.py
│   ├── repo_view.py        # Repository creation view
│   ├── db_view.py          # Database creation view
│   ├── container_view.py   # Container creation view
│   └── bucket_view.py      # Storage bucket creation view
├── templates/              # Template management components
│   ├── __init__.py
│   └── templates_view.py   # Templates UI view
└── operations/             # Operation execution components
    ├── __init__.py
    ├── operation_dialog.py # Operation execution dialog
    └── executor.py         # Command execution system
```

## Key Components

### MainWindow

The main application window serves as the container for all other UI components. It implements:

- Navigation sidebar with tree-based menu
- Content area with stackable pages
- Status bar displaying application state
- Menu bar with application actions

### LogWidget

Custom widget for displaying log messages with:

- Color-coded output based on log level
- Filtering by log level
- Auto-scrolling capability
- Log saving and clearing functionality

### SettingsView

Provides UI for configuring application settings including:

- Theme selection (Light, Dark, System)
- Configuration file (.env) selection and creation
- Settings persistence

### ProjectSetupView

Comprehensive form for setting up new projects with options for:

- Project basic information (name, visibility)
- Technology stack selection (Django, React, or both)
- Infrastructure configuration (database, CI/CD, containers, storage)
- Logging of setup process

## UI Style Guidelines

The application follows modern macOS-inspired design patterns with careful attention to visual details. This section outlines the key UI principles and style guidelines for maintaining a consistent user experience.

### Theme System

The application supports light and dark themes with a unified style approach:

- **Central Style Repository**: All styles are managed in `resources/styles.py`
- **Three-Part Structure**:
  - `BASE_STYLE` contains shared styles applied to all themes
  - `LIGHT_STYLE` contains light theme-specific styles
  - `DARK_STYLE` contains dark theme-specific styles
- **Dynamic Application**: Styles are applied at runtime based on user settings or system theme

### Component Guidelines

#### Cards and Containers

Card components (like `ActionCard`) follow these guidelines:

- Always use dark backgrounds (#2d2d2d) for better visibility and contrast
- All text elements within cards must have `background-color: transparent`
- Text should be white with appropriate opacity (titles at 100%, descriptions at 80%)
- Proper padding (15px) should be maintained around content
- Corner radius of 8px should be applied consistently
- Hover effects should be subtle and consistent

Example styling for card components:
```css
#actionCard {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
}

#actionCard QLabel {
    background-color: transparent;
}

#cardTitle {
    font-weight: bold;
    font-size: 15px;
    color: white;
}

#cardDescription {
    color: rgba(255, 255, 255, 0.8);
}
```

#### Typography

Text elements follow these guidelines:

- Use the system font stack across the application
- Font sizes:
  - Regular text: 13px
  - Card titles: 15px
  - Section headers: 20px
- Maintain readable contrast (WCAG AA minimum)
- Set appropriate line height for comfortable reading

#### Icons

Icons in the application support two formats:

- **PNG Icons**: Defined in `resources/icons.py` as Base64 strings
- **SVG Fallbacks**: Defined in `resources/fallback_icons.py` as SVG XML strings

When creating new icons:
- Include both PNG (24x24) and SVG fallback versions
- Keep SVG icons simple with minimal path complexity
- Use the application's color scheme (primarily #007AFF for light, #0A84FF for dark)
- Provide proper icon names that match their function

#### Layout Principles

- Use appropriate margins and padding (typically 15px for content areas)
- Apply consistent spacing between elements
- Use stretchers and spacers for flexible layouts
- Organize related controls with proper alignment
- Follow the visual hierarchy from macOS guidelines

### Adding New UI Components

When adding new UI components:

1. **Naming Convention**: Use descriptive, CamelCase names
2. **ObjectName**: Set proper objectName for CSS targeting
3. **Transparency**: Ensure all labels have transparent backgrounds
4. **Theme Support**: Set styles that work with both themes
5. **CSS Properties**: Use `setProperty()` rather than inline styles when possible

Example for creating a new component:
```python
# In widget code
new_widget = QWidget()
new_widget.setObjectName("customComponent")
new_widget.setProperty("customProperty", True)

# In CSS
#customComponent {
    background-color: #333333;
}

[customProperty="true"] {
    border: 1px solid #555555;
}
```

### Performance Considerations

To maintain smooth performance:

- Avoid setting styles individually when global CSS can be used
- Use style sheets for repeated styles rather than inline styling
- Cache complex widgets rather than recreating them
- Load icons and resources once, then reuse them
- Minimize layout recalculations with proper layouts

## Building and Running

### Running from CLI

```bash
# Install GUI dependencies
poetry install --with gui

# Run through CLI command
poetry run infra gui

# Or run directly
poetry run python -m infra.gui.app
```

### Building macOS Application

A build script is provided to create a standalone macOS application:

```bash
# Make build script executable
chmod +x build_macos_app.sh

# Run build script
./build_macos_app.sh

# Launch the application
open dist/Infra.app
```

The build script:
1. Creates necessary directories
2. Checks for icon files
3. Sets up the build environment
4. Runs py2app to create the application bundle
5. Outputs the path to the built application

## Creating Icons

For a proper macOS application, you should create an icon file:

1. Create a set of PNG images at different sizes (16x16, 32x32, 64x64, 128x128, 256x256, 512x512, 1024x1024)
2. Use `iconutil` to convert to .icns format:
   ```
   iconutil -c icns icon.iconset -o infra/gui/resources/icon.icns
   ```

## Theme Support

The application supports three theme modes:

- **Light**: Forces light appearance
- **Dark**: Forces dark appearance 
- **System**: Follows macOS system settings

Theme settings are stored using Qt's QSettings and persist between application launches.

## Working with .env Configuration

The application can create, locate, and use .env configuration files:

1. Default location is `~/.infra/.env`
2. User can browse and select any .env file
3. Option to create a default .env from the provided template

## Integration with CLI

The GUI leverages the same underlying functionality as the CLI, ensuring consistency between both interfaces. Commands triggered through the GUI:

1. Execute the same code paths as CLI commands
2. Provide real-time feedback through the logging system
3. Display detailed progress information

## Future Improvements

- Full theme system that can change dynamically without restart
- Implementation of remaining resource creation views
- Advanced operation dialog with cancelation support
- Templates browser with preview functionality
- Integration with AI assistant capabilities 