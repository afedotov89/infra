"""
Запасные иконки в формате SVG для GUI приложения Infra.
Используются, если есть проблемы с загрузкой основных иконок в формате PNG.
"""

# Запасные SVG-иконки в простом формате
FALLBACK_ICONS = {
    # Простая иконка для проекта
    "project": """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <rect x="4" y="4" width="16" height="16" fill="none" stroke="#007AFF" stroke-width="2" />
      <path d="M4 8 L20 8" stroke="#007AFF" stroke-width="2" />
      <circle cx="12" cy="16" r="3" fill="none" stroke="#007AFF" stroke-width="2" />
    </svg>
    """,
    
    # Иконка для настроек
    "settings": """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <circle cx="12" cy="12" r="7" fill="none" stroke="#007AFF" stroke-width="2" />
      <path d="M12 5 L12 2" stroke="#007AFF" stroke-width="2" />
      <path d="M12 22 L12 19" stroke="#007AFF" stroke-width="2" />
      <path d="M5 12 L2 12" stroke="#007AFF" stroke-width="2" />
      <path d="M22 12 L19 12" stroke="#007AFF" stroke-width="2" />
    </svg>
    """,
    
    # Иконка для репозитория
    "repo": """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <circle cx="12" cy="6" r="3" fill="none" stroke="#007AFF" stroke-width="2" />
      <circle cx="12" cy="18" r="3" fill="none" stroke="#007AFF" stroke-width="2" />
      <path d="M12 9 L12 15" stroke="#007AFF" stroke-width="2" />
    </svg>
    """,
    
    # Иконка для базы данных
    "database": """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <ellipse cx="12" cy="6" rx="8" ry="3" fill="none" stroke="#007AFF" stroke-width="2" />
      <path d="M4 6 L4 18" stroke="#007AFF" stroke-width="2" />
      <path d="M20 6 L20 18" stroke="#007AFF" stroke-width="2" />
      <ellipse cx="12" cy="18" rx="8" ry="3" fill="none" stroke="#007AFF" stroke-width="2" />
    </svg>
    """,
    
    # Иконка для контейнера
    "container": """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <rect x="3" y="8" width="18" height="12" fill="none" stroke="#007AFF" stroke-width="2" />
      <rect x="6" y="11" width="4" height="4" fill="none" stroke="#007AFF" stroke-width="1" />
      <rect x="14" y="11" width="4" height="4" fill="none" stroke="#007AFF" stroke-width="1" />
      <path d="M7 8 L7 4 L17 4 L17 8" stroke="#007AFF" stroke-width="2" />
    </svg>
    """,
    
    # Иконка для хранилища
    "storage": """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <path d="M4 8 L12 4 L20 8 L12 12 Z" fill="none" stroke="#007AFF" stroke-width="2" />
      <path d="M4 8 L4 16 L12 20 L20 16 L20 8" fill="none" stroke="#007AFF" stroke-width="2" />
      <path d="M12 12 L12 20" stroke="#007AFF" stroke-width="2" />
    </svg>
    """,
    
    # Иконка для шаблонов
    "templates": """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
      <rect x="5" y="3" width="14" height="18" fill="none" stroke="#007AFF" stroke-width="2" />
      <path d="M8 8 L16 8" stroke="#007AFF" stroke-width="2" />
      <path d="M8 12 L16 12" stroke="#007AFF" stroke-width="2" />
      <path d="M8 16 L13 16" stroke="#007AFF" stroke-width="2" />
    </svg>
    """,
}

def get_fallback_icon(name):
    """
    Возвращает запасную SVG иконку по имени.
    
    Args:
        name: Имя иконки
        
    Returns:
        str: XML строка с SVG-данными иконки или пустая строка
    """
    return FALLBACK_ICONS.get(name, "") 