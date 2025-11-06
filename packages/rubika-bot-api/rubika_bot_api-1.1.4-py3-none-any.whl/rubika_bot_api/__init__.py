
"""
Rubika Bot API - A high-performance asynchronous Python library for Rubika Bot API
"""

__version__ = "1.2.0"

# Core components
from .api import Robot, InvalidTokenError
from .update import Message, InlineMessage
from .exceptions import APIRequestError

# UI Components
from .keyboards import (
    InlineKeyboardBuilder,
    ChatKeyboardBuilder,
    create_simple_keyboard,
)

# Decorators and Filters
from .decorators import (
    on_message,
    on_callback,
    on_edited_message,
    on_inline_query,
    on_started_bot,
    on_stopped_bot,
    middleware
)
from . import filters

# Enums and Types
from .enums import (
    ChatTypeEnum,
    ChatKeypadTypeEnum,
    UpdateTypeEnum,
    MediaTypeEnum,
)

# Utilities and Helpers
from .helpers import (
    StateManager,
    RateLimiter,
    Scheduler,
    FileUploader,
    AsyncCache,
    MessageQueue
)

# Socket and Network
from .socket_manager import AsyncSocketManager
from .client_bot.network.socket import Socket
from .client_bot.network.network import Network

__all__ = [
    # Core
    "Robot",
    "Message",
    "InlineMessage",
    "InvalidTokenError",
    "APIRequestError",
    
    # UI
    "InlineKeyboardBuilder",
    "ChatKeyboardBuilder",
    "create_simple_keyboard",
    
    # Decorators & Filters
    "on_message",
    "on_callback",
    "on_edited_message",
    "on_inline_query",
    "middleware",
    "filters",
    
    # Enums
    "ChatTypeEnum",
    "ChatKeypadTypeEnum",
    "UpdateTypeEnum",
    "MediaTypeEnum",
    
    # Utilities
    "StateManager",
    "RateLimiter",
    "Scheduler",
    "FileUploader",
    "AsyncCache",
    "MessageQueue",
    
    # Network
    "AsyncSocketManager",
    "Socket",
    "Network",
]
