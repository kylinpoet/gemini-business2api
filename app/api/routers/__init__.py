from .accounts import AccountRouteDeps, register_account_routes
from .settings import SettingsRouteDeps, register_settings_routes
from .system import SystemRouteDeps, register_system_routes

__all__ = [
    "AccountRouteDeps",
    "SettingsRouteDeps",
    "SystemRouteDeps",
    "register_account_routes",
    "register_settings_routes",
    "register_system_routes",
]
