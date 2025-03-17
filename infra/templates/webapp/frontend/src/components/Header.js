import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import SettingsIcon from '@mui/icons-material/Settings';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import SettingsBrightnessIcon from '@mui/icons-material/SettingsBrightness';
import Link from 'next/link';
import { Box, Tooltip, Container } from '@mui/material';
import { useTheme, THEME_MODES } from '../contexts/ThemeContext';

// Header component for LangTask AI subscription service
const Header = () => {
  // Using useTheme hook with error handling
  let themeMode = THEME_MODES.SYSTEM;
  
  try {
    const themeContext = useTheme();
    themeMode = themeContext?.themeMode || THEME_MODES.SYSTEM;
  } catch (error) {
    console.error('Error using theme context:', error);
    // Fallback to system theme in case of error
  }

  // Defining theme icon based on current theme
  const getThemeIcon = () => {
    switch (themeMode) {
      case THEME_MODES.LIGHT:
        return <LightModeIcon fontSize="small" />;
      case THEME_MODES.DARK:
        return <DarkModeIcon fontSize="small" />;
      default:
        return <SettingsBrightnessIcon fontSize="small" />;
    }
  };

  // Tooltip text for current theme
  const getThemeText = () => {
    switch (themeMode) {
      case THEME_MODES.LIGHT:
        return 'Light Theme';
      case THEME_MODES.DARK:
        return 'Dark Theme';
      default:
        return 'System Theme';
    }
  };

  return (
    <AppBar position="static" color="transparent" elevation={0}>
      <Container maxWidth={false}>
        <Toolbar disableGutters sx={{ px: 2, py: 1 }}>
          <Link href="/" passHref style={{ textDecoration: 'none', color: 'inherit', flexGrow: 1 }}>
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                fontWeight: 500,
                letterSpacing: 0.5
              }}
            >
              LangTask AI
            </Typography>
          </Link>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title={getThemeText()}>
              <Box sx={{ mx: 1, display: 'flex', alignItems: 'center', opacity: 0.7 }}>
                {getThemeIcon()}
              </Box>
            </Tooltip>
            
            <Link href="/settings" passHref>
              <Tooltip title="Settings">
                <IconButton 
                  color="inherit"
                  sx={{ 
                    opacity: 0.7,
                    '&:hover': {
                      opacity: 1
                    }
                  }}
                >
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
            </Link>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header; 