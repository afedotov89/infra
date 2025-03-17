import * as React from 'react';
import Head from 'next/head';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, useTheme } from '../src/contexts/ThemeContext';
import { createAppTheme } from '../src/theme';
import Header from '../src/components/Header';

// Внутренний компонент для применения темы
function ThemedApp({ Component, pageProps }) {
  const { resolvedTheme } = useTheme();
  const theme = React.useMemo(() => createAppTheme(resolvedTheme), [resolvedTheme]);

  React.useEffect(() => {
    // Remove the server-side injected CSS
    const jssStyles = document.querySelector('#jss-server-side');
    if (jssStyles) {
      jssStyles.parentElement.removeChild(jssStyles);
    }
  }, []);

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      <Header />
      <Component {...pageProps} />
    </MuiThemeProvider>
  );
}

// Основной компонент приложения с провайдером темы
function MyApp(props) {
  return (
    <React.Fragment>
      <Head>
        <title>Next.js Material UI App</title>
        <meta name="viewport" content="minimum-scale=1, initial-scale=1, width=device-width" />
      </Head>
      <ThemeProvider>
        <ThemedApp {...props} />
      </ThemeProvider>
    </React.Fragment>
  );
}

export default MyApp; 