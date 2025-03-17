import { createTheme } from '@mui/material/styles';

// Function for creating a theme based on mode (light, dark or system)
export const createAppTheme = (mode) => {
  const isDark = mode === 'dark';
  
  // Neutral colors for light and dark themes
  const neutral = {
    main: isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
    light: isDark ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)',
    dark: isDark ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.9)',
    contrastText: isDark ? '#121212' : '#ffffff',
  };

  return createTheme({
    palette: {
      mode,
      primary: neutral,
      secondary: {
        main: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
      },
      background: {
        default: isDark ? '#121212' : '#f5f5f5',
        paper: isDark ? '#1e1e1e' : '#ffffff',
      },
      text: {
        primary: isDark ? 'rgba(255, 255, 255, 0.87)' : 'rgba(0, 0, 0, 0.87)',
        secondary: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
      },
      action: {
        active: isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
        hover: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
      },
    },
    typography: {
      fontFamily: [
        '-apple-system',
        'BlinkMacSystemFont',
        '"Segoe UI"',
        'Roboto',
        '"Helvetica Neue"',
        'Arial',
        'sans-serif',
      ].join(','),
    },
    shape: {
      borderRadius: 6,
    },
    components: {
      MuiButton: {
        defaultProps: {
          disableElevation: true, // Disable button shadows
        },
        styleOverrides: {
          root: {
            textTransform: 'none', // Remove capitalization on buttons
            fontWeight: 500,
          },
          // Settings for outlined button variant
          outlined: ({ theme }) => ({
            borderColor: theme.palette.mode === 'dark' 
              ? 'rgba(255, 255, 255, 0.23)' 
              : 'rgba(0, 0, 0, 0.23)',
            '&:hover': {
              backgroundColor: theme.palette.mode === 'dark'
                ? 'rgba(255, 255, 255, 0.05)'
                : 'rgba(0, 0, 0, 0.05)',
              borderColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.4)' 
                : 'rgba(0, 0, 0, 0.4)',
            }
          }),
          // Settings for contained button variant
          contained: ({ theme }) => ({
            backgroundColor: theme.palette.mode === 'dark' 
              ? 'rgba(255, 255, 255, 0.1)' 
              : 'rgba(0, 0, 0, 0.08)',
            color: theme.palette.text.primary,
            '&:hover': {
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.2)' 
                : 'rgba(0, 0, 0, 0.15)',
            }
          }),
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: ({ theme }) => ({
            color: theme.palette.text.primary,
          }),
        },
      },
      MuiAppBar: {
        styleOverrides: {
          colorTransparent: {
            // Subtle bottom line for header
            borderBottom: '1px solid',
            borderColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
        },
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
        },
      },
      MuiSvgIcon: {
        styleOverrides: {
          root: ({ theme }) => ({
            color: 'inherit',
          }),
        },
      },
    },
  });
};

// Export light theme as default
const theme = createAppTheme('light');

export default theme; 