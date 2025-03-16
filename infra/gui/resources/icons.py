"""
Модуль содержит иконки и ресурсы для GUI приложения Infra.
Иконки представлены в виде байтовых строк, которые можно преобразовать в QPixmap.
"""

import logging
from PyQt6.QtGui import QPixmap, QIcon, QPainter
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QSize, QRectF, Qt, QXmlStreamReader
from PyQt6.QtSvg import QSvgRenderer

# Импортируем запасные SVG иконки
from infra.gui.resources.fallback_icons import get_fallback_icon

# Настройка логгера для отладки
logger = logging.getLogger(__name__)


def get_icon(name):
    """
    Возвращает иконку по имени.
    
    Args:
        name: Имя иконки
        
    Returns:
        QIcon: Объект иконки
    """
    # Сначала пробуем загрузить PNG иконку
    if name in _ICONS:
        try:
            base64_data = _ICONS[name].encode()
            pixmap = QPixmap()
            
            # Очищаем данные от возможных пробелов и переносов строк
            base64_data = b''.join(base64_data.split())
            
            result = pixmap.loadFromData(QByteArray.fromBase64(base64_data))
            if result:
                logger.debug(f"Icon '{name}' loaded successfully, size: {pixmap.width()}x{pixmap.height()}")
                return QIcon(pixmap)
            else:
                logger.warning(f"Failed to load PNG icon data for '{name}', trying SVG fallback")
        except Exception as e:
            logger.warning(f"Error loading PNG icon '{name}': {e}, trying SVG fallback")
    else:
        logger.warning(f"Icon '{name}' not found in icon database, trying SVG fallback")
    
    # Если PNG не удалось загрузить, пробуем SVG
    try:
        svg_data = get_fallback_icon(name)
        if svg_data:
            logger.info(f"Using SVG fallback icon for '{name}'")
            
            # Создаем pixmap из SVG данных
            renderer = QSvgRenderer(bytes(svg_data, 'utf-8'))
            if renderer.isValid():
                pixmap = QPixmap(24, 24)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
            else:
                logger.error(f"Invalid SVG data for '{name}'")
                return QIcon()
        else:
            logger.error(f"No fallback SVG icon found for '{name}'")
            return QIcon()
    except Exception as e:
        logger.error(f"Error loading SVG fallback icon for '{name}': {e}")
        return QIcon()


# Данные иконок в формате Base64
_ICONS = {
    # Примерная иконка для проекта (упрощенный куб)
    "project": """
    iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAC
    SklEQVR4nO2ZTUhUURTHf45OhYtadBCLCKIgouim2ogi2lhBULiLNtGmRdAmCqJViyKoRQvbSUKL
    NkFQiyJaRLYIwcUgiRQ1RVHTwtGZOHAeXB7zed+9z5n3B4fx3XfP+f/n3Hveua8gxphGoA04DTwD
    psNrBhgFbgLHgKTvDa8GjgKTbM0y8AS4ACz5MqCd77Sx82+Bu8AXl0a04w8Aa/wXngFJV0ZS6hM3
    4W/WYoK+2gj8ArLABedG/lELTMscpx3MG5O5n7kyIGRl8hfAflemRIkPgQu5NieSPJP5Lrk2JpIc
    kTnfuDAlkgzLnBdcmBJJ+mTOrS5MiSSXZc4hF6ZEkh6Z87ALUyJJh8w56cKUSNIrc054HSGipCJP
    f8g7+ysBr8RnVA2InP3lQED8RtWAyFXlQED8R9WAyFXlQED8R9WAyFXlQED8R9WAXuTycgDXO9BD
    K4pJrE0KciI3bHuATgKNwLzl3CSwA7gfZlGkZoCQkvN/CRguc9530h7YQHwMvJfnF91WRNI2MXuv
    jAEBtMu9wbzMke95vTDqBkT+uDzXXSkGBFAmz1dlLP+Z15sBMTEmc/Racb1FcSAEzsh9MU6kHZyA
    BnmeFhNRNQDQJfdvpU2cDQgdMocawJ56n2NiYEza7LKYl5jWHj8DfdLmifQ1EWcDQuC53FeAQ9Qj
    USsB3dLnMdAmfZ2BhDgbqJF7zbWYt1Sh7yJ6WNGN25dK3RnlNUGt/H9QDAxKn5dSH1J5TZCY1/8F
    vwEX1D4L7YbUPwAAAABJRU5ErkJggg==
    """,
    
    # Иконка для настроек (шестеренка)
    "settings": """
    iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAC
    P0lEQVR4nO2YTUhUURTHfzPqTH6AU5sgaBG0iaJoYaCUZbQIwpU0URsX0aaINrUyxFpVtCmI2kRL
    F1GLoE1RtIiiQimUIrNCiCxHU8bJOXAHHo/33rz7Zu4M+sPhwn3nnv8599z3ce8DQ0NDQ8N/QRuw
    G/gEzACzwB/gATAA7HTdbRHcAlLABvAZ+ArcB74B68Br4JyzDgvkOPDDTHAC6AfaTewyYO+zwJSJ
    3wC+AA+Bw85nkYc+YNE0chem+5/ANyA2AwwCF4B2oBE4BFwB7pmYP6bGmJN5ZdEIfDITmAd2lfC7
    ClwFNs3GbwK7ncy0gIj1fQPoKeP3ODAF/AZOWfEhJw3n4ZoFT6I8ZoFnQBTztDqABvN5GVi24ued
    dF+AW1Z8X0i/CeA1cMVKBjiGeuNUDu9PwPkQvfZbvd4J0U8oTlrLZjREjpztW6g7PQPcsOK9wBqQ
    ROlUCR1OW70+DtFPKI5Y8Uk0pUrFa+AUcBR1qDTwC3UWz2Mp8G5L6XA5pI9QRK14Kt8XBFnvNLPU
    C31p1PlIWZ8T+X7oyNNwuZRKPZlSGrksG1PHZKzP0Xx5pXS4alW64KDBmHkvsq2dDtHEk3LuVNsS
    Xk6tGXjmYAn9L0jWU6Oay+c4esxSrKJuDd4a/zC1UmMrqIfOsYoiRqxKp6tdxBHiaPtHKVwHjqO+
    JzXjRnepNfI9NGK19uYq4ZFNFJ5oVq0lNKaGx85qTCKKBfSGPVLJIl7VTwrtJsJFvDLkfaahUW/8
    BVJ8WiV16N7JAAAAAElFTkSuQmCC
    """,
    
    # Иконка для репозитория (ветка)
    "repo": """
    iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAD
    K0lEQVR4nO2Yz0sVURTHP25lpKWVFUVJJAUtXLQLF7kozYUQLVr0ByS0KINahOAmF/0BQQsjimgR
    RJughdGiRdFCqIWQQtGmRdSYiKLpx5k4cB5cHvPeu/Peu/PmBX3hsMx9c875njn3zLlnHgQEBAQE
    BFQ7aoAWYAF4BUx5vN4D8/Id+cZ6T7b3AVeBLv62/n0DHgIXgdqkxDcA08CsBwtpvAbaXYtfCrzP
    YnQBmJD3uLRBoBN4msH3FbDXlej9JnEMtb+9wCygK8hW50h8X2TGazJTn4AGYCziFwKp74AdpYpv
    F4eRCGO1kjD+5HEctxK3p0rGT/M/1oEJ4JZkjFYXBTzDFN8P7E747KtSIqVJ0qVWziaBeuCOzOy1
    lMIvSJ/zXJgSSTolXepljNMOtIvIRqA3YpY18CxDydMGXEvYgbYxZwdaYuzMaAfWaAe60ggfljNa
    GZuXbGBDnQ2dNtqB6SQd0HS5KIdCn5WedYnYoXWA5P05dGQ10CIdaLIdUI7tkgCukYJdEmCVwvCN
    2Aq9Rx5+2/LJhJxbE6NvjdgrlLZyOtArF69L9lsvzs+LXmvE3nMX4nvEcVL0S0nnLtkw2iX6ncD6
    GPsN6JLruqTfFdFHgFqi8SDiZNt/L6nmL9Ev1LCCeJfhGovkOnO7uik69Qb9kOj7i3Tgs+g35bBd
    J/rpolUCm0Q/W6QDc6JvzWG7WfTjRasEWkT/s0gHJkW/M4dtk+h/FOpAK7AKWAFsLRD4vwpw3CyO
    2lYXSI9XCxzq5exd8LEz/QakH/A34JeYFLO7AKeeXsN52SHo2JFkm+RaUKwD94FewCnmwFxM4Kjx
    0+C61CFpN2ZZKWpxJMscMwTcldcy96yPn0NbD6HRwFbaDRmznPsZWjSVdFjP5ckrcpM+a9F26qlz
    GStDo95VzzdZuSx+CmyTe6eeQjcD2SoZRXH6vGR1nHYQFgKzrqap1Yuvt2v1YueVKueW0H4iPEHR
    FcRb+muZE6VEa0Pbz4C7hO+KNYnT59qrZOIeGf3XRkROR4R/BrC9l0qnDQ0NDcv4C/if5bzOurwG
    AAAAAElFTkSuQmCC
    """,
    
    # Иконка для базы данных
    "database": """
    iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAC
    b0lEQVR4nO2Y30tTYRzGP5ualNXFiGpIF0HUomvDCxXqwgsX9QfUzUQQuhRddVlddBNBgkiQQVde
    RZcVeKEJXUhSF9KFLUIMocRmWZM+8M3vwplnr3POmds58A0e2M73fZ7n+ezH8+PsgLGxsbGxScA+
    4AwwBbwE3gLvgC/AMvAQGAL2ZqiZF4PADPAdqMX8VoHHwOms5hPHlJXM3wXuAyX9u6oDv2uCAiBr
    2gngk/JfB+4Be4B2oADsAo4B14BlZfsBOJhl8gNKrArcjrF/CYwYtpeBKhF/INPU9TY1MBNR+AXQ
    E+MzYM1gAZhPMWZiKSjBAVGcUvpVJU5CRYl7UoxJ2bAKC6IoKvdfYiY/jq+i0JViTKI7KIGaEpWS
    JD+OWVFoTzEm0RmUQF0JDqeY/Aaww0oydCQck7I7KIGKEpxKMfkLSaKEYwW9TdeU4EZCv7zwuwoc
    Tjgm5ZJRAuX2FuO3QzmqA0GcitGUleZmgnglq3YrhhOaZ412bRtwiYi7UBbM6efSRrE/xOGsngSO
    7+ixijmsKQG/Ukw8Av4Av4AHwDHxfUr5vgV2bzdxH9PK+RXQ1aBpBZ4pmxUga7wVLgLzSrCktxtj
    FDzGXeCH8r+W5+S1+JIS/QTOhezvVKsyD9QbcBlYUP6XdIf+F9qIt+JGf1HkbXxFCWvA+ZbjJ2DY
    mo2b+rfjnPDOCbtDOLQCL5TP1TwlH8RFPblFVeEIsLhp/6kel7lzXIl/RwzWV/XrwFmzlfQTtwEv
    VILTpskc9hBNnZ+G3ebAU+JJbvnI1MYMzOi9f8IUn8pq0sbGxsbGZgP+AfFcVom8rBXvAAAAAElF
    TkSuQmCC
    """,
    
    # Иконка для контейнера (Docker-как)
    "container": """
    iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAA
    Bd0lEQVR4nO2YTU7DMBBGXxoqWLABUbYVEi07VuQQpYgdXKTswQ3aMCrqhp+zZsGebyPFjvNmns
    eO7UyoVCqVvbMHHoB34Bcwgx2Ax/WesUxjYD8DO/rXmNs5e5kL4KMnkLFMkXydK73R46cA56OSr
    6NbwzkgeYNKvnLtQjMGJj8HTgNrvMf2/+b19CbVeE/y1oF9UuJmnfz+GUkCpyLJPwOnAuS7ECPP
    aWfylXrg5Csu6ckC23qR6kq+AsQmYK5lCJzT0HT8X54a4yAPsQnY6XUPZJKvc5BHgwLdpCfdoNT
    qNEb+0lkWaXReuhKIwVb+eJ+f1zLcRjhwCdj9/pijvHGRP5uayhp5tSvRgbz+j4xzO+AqP3VSGHm
    4yhv3XchMfpnUARf5pQDQyC8FgEZ+SQAM9xqZ+yBv5JcEQCO/JAAa+SUBaOWXBsBcfg4Iy0vAN4T
    lJeATggNjhOUlYF3lXyEszoFvCItzoFKpVCrvPAHFhP6X/ZS1FAAAAABJRU5ErkJggg==
    """,
    
    # Иконка для хранилища (бакета)
    "storage": """
    iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAB
    sElEQVR4nO2YMUvDQBTHfzaKIg46VHBQcOrWxa2LTl0c7ZcQ0cn6IRxU6CS4dHTyCzj5ASouFqdC
    BwebRbDQJuSgKSS5u8S0uZL2Dwde7v7v/X+Xd7k7qBQkdOv3LrAGdIAWYP16BLwBLWAG2APKOSYX
    KR3gw/J2MaHkl4BzD/EQdxIXvBwT+SmgD1wkIL+EqhgTeRu4SUC+CuwDpcBXEZg71i8nsCR/onKr
    RbJ3Bc0WoMs61Q04A+6BPjCbpYCA/A/ALrABrAArwCawC/RiBKwHPAInQLnEqICQfA9oAgOaPX6/
    Bgx+v2sCMuDvnV8BIXkzxtxQhDQCQvJmgvInYJr42cDTF5IQkCT5RfDxNQEpnAWE5GdNBETl+T+A
    kHwQkDcRkI7nA1LykwjoJFkBP/mw7AcW0GXf10D3qYDu56/H2U9awE9+y9DvQLqyj4CvvJWAwDrg
    Ky8toCXvIiAu/whcGfgXpQIkPuQH5AUE5CUEyF9eQKAoewEVn+QlBYqyFzCZvLSAmbyEQGz5Q6AZ
    YV4eArHl561TCHt37BdTpyDAfqzvwIcQdgr+Kc8yfiLmGf39ASGEPWesOLLIAAAAAElFTkSuQmCC
    """,
    
    # Иконка для шаблонов
    "templates": """
    iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAC
    U0lEQVR4nO2YS0hUURjHf3NzrLFJK4hsUSBRUbSKMFy0CLFVq9q0CjFatCsKchNF9FgVBC0qDFpJ
    q6hFRdFTKIpoEfUiCKpNEdHDmTLnwBl+V+/lztwZ7Z77h8Plnu98j+/xnfMdmDFjxoz5r1kKnAa+
    A78qr1/AZWCxTeOpOCSO+OEn0GDTeBoMDjeA/Skc8hmwOPQ4klLPgCXARaAIfAXOAu3ATNXdCOyo
    ZOAfQbeYMJuZXUBRg1wFtpLkiLJC4CngPxKLXUq2qe6nGjNX9Kfj9JZnAM3/rjEa5ZgbA+dY4hVV
    R4Rr1B0GBDmtyj5LKVoCTKOGWCO1bQvw2VLvGXCHMFmzQZwA7hcq2JDSnlnAw5T29pGgW0j/TnP+
    s5TSl4GrwEcNcgs4pu9OBMcQdctqmwkjQJPW2TdFXVXklG1xJAEzpG9zAl1XJLzNkeELwIiRMZrx
    j27JtqUU7pFwj0XZ71V/i6NMRD3ZGpKGJlXZk1JY4Lky9MaQ2StZERhxaOun2i6Jm9XpsjguyjlL
    yd3ApyQBmtLo61HdVwL73gEDDl3viGmn2WwQ5VNLyU1SeodF9ldPuvoURykxGaVBXvstnZ1Sxa2W
    ZR6Svl6HOk6Kwh6L8ntEX3Jo61UcRYu2LoljSG95C2Y/0FWRtqvuLeD7X/SdEOOo5XfQGnHa7jg3
    f1aKwT4LP3vFORfHYIcK+tWoLFuqdqvEvpk88F4cJGt0S3l71TqT0y+UJuBGxfm7wFWgyaahhlih
    jF0AOoF5Ns2YMWPGjP8CP7QWnZaE8zQhAAAAAElFTkSuQmCC
    """,
} 