#!/bin/bash
# Script to build the macOS application bundle

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Infra.app for macOS...${NC}"

# Create resources directory if it doesn't exist
if [ ! -d "infra/gui/resources" ]; then
    echo -e "${YELLOW}Creating resources directory...${NC}"
    mkdir -p infra/gui/resources
fi

# Check if icon.icns exists, if not, create a placeholder message
if [ ! -f "infra/gui/resources/icon.icns" ]; then
    echo -e "${YELLOW}Warning: icon.icns not found. A default icon will be used.${NC}"
    echo -e "${YELLOW}To use a custom icon, create infra/gui/resources/icon.icns file.${NC}"
fi

# Activate Poetry environment if running from outside it
if [ -z "$POETRY_ACTIVE" ]; then
    echo -e "${YELLOW}Activating Poetry environment...${NC}"
    eval "$(poetry env info --path)/bin/activate" || { 
        echo "Failed to activate Poetry environment. Make sure Poetry is installed and configured."; 
        exit 1; 
    }
fi

# Install development dependencies
echo -e "${GREEN}Installing py2app...${NC}"
pip install py2app

# Clean previous builds
echo -e "${GREEN}Cleaning previous builds...${NC}"
rm -rf build dist

# Build the application bundle
echo -e "${GREEN}Building application bundle...${NC}"
python setup.py py2app

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo -e "${GREEN}The application is located at:${NC} $(pwd)/dist/Infra.app"
    echo -e "${GREEN}To run it, use:${NC} open dist/Infra.app"
    echo ""
    echo -e "${YELLOW}Note: This is a development build. For a production build, use:${NC}"
    echo -e "${YELLOW}python setup.py py2app -A${NC}"
else
    echo -e "${YELLOW}Build failed. Check the error messages above.${NC}"
fi 