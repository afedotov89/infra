import React, { createContext, useState, useContext, useEffect } from 'react';

// Типы тем
export const THEME_MODES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
};

// Проверка окружения браузера
const isBrowser = typeof window !== 'undefined';

// Значение по умолчанию
const defaultThemeContextValue = {
  themeMode: THEME_MODES.SYSTEM,
  setThemeMode: () => {},
  resolvedTheme: 'light', // Фактическая тема после разрешения системной
};

// Создаем контекст
export const ThemeContext = createContext(defaultThemeContextValue);

// Провайдер контекста
export const ThemeProvider = ({ children }) => {
  // Получаем сохраненную тему из localStorage
  const [themeMode, setThemeMode] = useState(THEME_MODES.SYSTEM);
  // Фактическая тема после разрешения системной
  const [resolvedTheme, setResolvedTheme] = useState(THEME_MODES.LIGHT);

  // При инициализации проверяем сохраненную тему
  useEffect(() => {
    if (isBrowser) {
      const savedTheme = localStorage.getItem('themeMode');
      if (savedTheme && Object.values(THEME_MODES).includes(savedTheme)) {
        setThemeMode(savedTheme);
      }
    }
  }, []);

  // Сохраняем выбранную тему
  useEffect(() => {
    if (isBrowser) {
      localStorage.setItem('themeMode', themeMode);
    }
  }, [themeMode]);

  // Определяем системную тему и разрешаем фактическую тему
  useEffect(() => {
    if (!isBrowser) return;
    
    const updateResolvedTheme = () => {
      if (themeMode === THEME_MODES.SYSTEM) {
        // Проверяем системные настройки
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setResolvedTheme(systemPrefersDark ? THEME_MODES.DARK : THEME_MODES.LIGHT);
      } else {
        setResolvedTheme(themeMode);
      }
    };

    updateResolvedTheme();

    // Слушаем изменения системной темы
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (themeMode === THEME_MODES.SYSTEM) {
        updateResolvedTheme();
      }
    };

    // Добавляем и удаляем слушатель
    mediaQuery.addEventListener('change', handleChange);
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [themeMode]);

  // Значение контекста
  const contextValue = {
    themeMode,
    setThemeMode,
    resolvedTheme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Хук для использования темы
export const useTheme = () => useContext(ThemeContext); 