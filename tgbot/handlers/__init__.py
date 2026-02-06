# Папка handlers является пакетом
# tgbot/handlers/__init__.py

from .menu import router as menu_router
from .triggers import router as triggers_router
from .greetings import router as greetings_router

# Собираем все роутеры в один список
routers = [menu_router, triggers_router, greetings_router]
