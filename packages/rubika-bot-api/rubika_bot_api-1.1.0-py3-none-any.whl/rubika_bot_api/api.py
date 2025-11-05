import aiohttp
import asyncio
import inspect
import time
from typing import List, Optional, Dict, Any, Literal, Callable, Awaitable, Union
import aiofiles

from .exceptions import APIRequestError
from .logger import logger
from .update import Message, InlineMessage  # Import from update.py instead
from collections import deque
from pathlib import Path

API_URL = "https://botapi.rubika.ir/v3"

class InvalidTokenError(Exception):
    """Raised when the provided bot token is invalid or expired."""
    pass

class Robot:
    def __init__(self, token: str):
        """
        Initialize the bot with a token.

        Parameters
        ----------
        token : str
            The bot token obtained from Rubika Bot Developer panel.

        Attributes
        ----------
        token : str
            The bot token.
        session : Optional[aiohttp.ClientSession]
            The aiohttp session used for making requests to the API.
        _offset_id : Optional[int]
            The last offset ID received from the API.
        _message_handler : Optional[Dict[str, Any]]
            The message handler function. See `on_message` decorator.
        _edited_message_handler : Optional[Dict[str, Any]]
            The edited message handler function. See `on_edited_message` decorator.
        _inline_query_handler : Optional[Callable[[Any, InlineMessage], Awaitable[None]]]
            The inline query handler function. See `on_inline_query` decorator.
        _started_bot_handler : Optional[Callable[[Any, Any], Awaitable[None]]]
            The started bot handler function. See `on_started_bot` decorator.
        _stopped_bot_handler : Optional[Callable[[Any, Any], Awaitable[None]]]
            The stopped bot handler function. See `on_stopped_bot` decorator.
        _on_callback_handler : Dict[str, Callable]
            The on_callback handlers by button_id. See `on_callback` decorator.
        offset_file : str
            The file name to store the last offset ID.

        Notes
        -----
        The bot will start at the last offset ID stored in the offset file.
        If the offset file does not exist, the bot will start from the beginning.
        """
        self.token = token
        self._offset_id = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._message_handler: Optional[Dict[str, Any]] = None 
        self._edited_message_handler: Optional[Dict[str, Any]] = None
        self._inline_query_handler: Optional[Callable[[Any, InlineMessage], Awaitable[None]]] = None 
        self._started_bot_handler: Optional[Callable[[Any, Any], Awaitable[None]]] = None 
        self._stopped_bot_handler: Optional[Callable[[Any, Any], Awaitable[None]]] = None 
        self._on_callback_handler: Dict[str, Callable] = {} 
        self.offset_file = f"offset_{self.token[:10]}.txt"
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Performance optimizations
        self.rate_limit = 0.05  # 50ms between requests for high performance
        self.last_request_time = 0
        self.processed_messages = deque(maxlen=10000)  # Cache processed messages
        self.running = False
        self.first_get_updates = True
        self._token_validated = False
        
        # Middleware support (for high performance processing)
        self.middlewares: List[Callable] = []
        
        # Start handlers
        self.start_handlers: List[Callable] = []
        self.shutdown_handlers: List[Callable] = []

        logger.info(
            f"Starting ON offset: {self._read_offset()}"
        )
    
    async def _validate_token(self):
        """Validate the bot token by calling getMe (async)."""
        if self._token_validated:
            return
        try:
            if not self.session:
                # Create temporary session for validation
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as temp_session:
                    url = f"{API_URL}/{self.token}/getMe"
                    async with temp_session.post(url, json={}) as response:
                        response.raise_for_status()
                        result = await response.json()
                        if result.get('status') != "OK":
                            raise InvalidTokenError("The provided bot token is invalid or expired.")
            else:
                result = await self._post("getMe", {})
                if result.get('status') != "OK":
                    raise InvalidTokenError("The provided bot token is invalid or expired.")
            self._token_validated = True
        except Exception as e:
            if isinstance(e, InvalidTokenError):
                raise
            logger.warning(f"Could not validate token: {e}")

    def _read_offset(self) -> Optional[str]:
        try:
            with open(self.offset_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError: return None

    def _save_offset(self, offset_id: str):
        with open(self.offset_file, "w") as f:
            f.write(str(offset_id))

    async def _rate_limit_delay(self):
        """Rate limiting for high performance - prevents API throttling"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    async def _post(self, method: str, data: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError("The bot session is not running. Please use 'await bot.run()'.")
        
        # Rate limiting for performance
        await self._rate_limit_delay()
        
        url = f"{API_URL}/{self.token}/{method}"
        try:
            async with self.session.post(url, json=data, timeout=timeout) as response:
                response.raise_for_status()
                try:
                    json_resp = await response.json()
                except aiohttp.ContentTypeError:
                    response_text = await response.text()
                    logger.error(f"Invalid JSON response from {method}: {response_text}")
                    raise APIRequestError(f"Invalid JSON response: {response_text}")

                if method != "getUpdates":
                    logger.debug(f"API Response from {method}: {json_resp}")
                
                # Check for API errors
                if json_resp.get("status") != "OK":
                    raise APIRequestError(f"API error: {json_resp.get('status_det', 'Unknown error')}")
                
                return json_resp

        except asyncio.TimeoutError:
            logger.error(f"Request to {method} timed out after {timeout} seconds.")
            raise APIRequestError(f"Request timed out: {method}")
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            raise APIRequestError(f"API request failed: {e}") from e

    def on_message(self, filters: Optional[Callable[[Message], bool]] = None, commands: Optional[List[str]] = None):
        def decorator(func: Callable[[Any, Message], Awaitable[None]]):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("The message handler function must be a coroutine (using async def).")
            self._message_handler = {
                "func": func,
                "filters": filters,
                "commands": commands
            }
            return func
        return decorator

    def on_edited_message(self, filters: Optional[Callable[[Message], bool]] = None):
        def decorator(func: Callable[[Any, Message], Awaitable[None]]):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("The edited message handler function must be a coroutine (using async def).")
            self._edited_message_handler = {
                "func": func,
                "filters": filters
            }
            return func
        return decorator

    def on_inline_query(self): 
        def decorator(func: Callable[[Any, InlineMessage], Awaitable[None]]):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("The inline query handler function must be a coroutine (using async def).")
            self._inline_query_handler = func
            return func
        return decorator

    def on_started_bot(self): 
        def decorator(func: Callable[[Any, Any], Awaitable[None]]):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("The bot started handler function must be a coroutine (using async def).")
            self._started_bot_handler = func
            return func
        return decorator

    def on_stopped_bot(self):
        """
        Decorator to register a function that will be called when the bot is stopped.
    
        The decorated function must be an asynchronous function (defined using `async def`).
        It should accept two positional arguments, which will be provided by the event
        that triggers the stop handler.
    
        Raises:
            TypeError: If the decorated function is not a coroutine.
        """
    
        def decorator(func: Callable[[Any, Any], Awaitable[None]]):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("The bot stopped handler function must be a coroutine (using async def).")
            self._stopped_bot_handler = func
            return func
        return decorator

    def on_start(self):
        """Decorator to register startup handlers."""
        def decorator(func: Callable):
            self.start_handlers.append(func)
            return func
        return decorator

    def on_shutdown(self):
        """Decorator to register shutdown handlers."""
        def decorator(func: Callable):
            self.shutdown_handlers.append(func)
            return func
        return decorator

    def middleware(self):
        """
        Decorator to register a middleware function.
        
        Middleware receives (bot, update, next_middleware).
        It must call `await next_middleware()` to continue chain.
        """
        def decorator(func: Callable):
            self.middlewares.append(func)
            logger.info(f"Middleware {func.__name__} registered")
            return func
        return decorator

    # New: Decorator for on_callback (similar to rubka)
    def on_callback(self, button_id: str) -> Callable:
        """Decorator to register a function that will be called when a button with the specified ID is clicked.

        The decorated function must be an asynchronous function (defined using `async def`).
        It should accept one positional argument, a `Message` object, which will be the message context of the button click event.

        Args:
            button_id: The unique ID of the button to be handled. This ID should match the value passed to `button_id` when creating the button.

        Raises:
            TypeError: If the decorated function is not a coroutine.
        """

        def decorator(func: Callable[[Any, Message], Awaitable[None]]): # Changed to Message context for uniformity
            if not inspect.iscoroutinefunction(func):
                raise TypeError("Callback handler must be a coroutine (using async def).")
            self._on_callback_handler[button_id] = func
            return func
        return decorator

    def _is_duplicate(self, message_id: str, max_age_sec: int = 300) -> bool:
        """Check if message was already processed (for performance)"""
        if message_id in self.processed_messages:
            return True
        self.processed_messages.append(message_id)
        return False

    def _has_time_passed(self, last_time: Optional[str], seconds: int = 5) -> bool:
        """Check if message is too old (skip old messages for performance)"""
        if not last_time:
            return False
        try:
            timestamp = int(float(last_time))
            now = time.time()
            return (now - timestamp) > seconds
        except (TypeError, ValueError):
            return False

    async def _run_middlewares(self, update: Dict[str, Any], index: int = 0):
        """Run middleware chain for high performance processing."""
        if index < len(self.middlewares):
            mw = self.middlewares[index]
            async def next_middleware():
                await self._run_middlewares(update, index + 1)
            
            if inspect.iscoroutinefunction(mw):
                await mw(self, update, next_middleware)
            else:
                mw(self, update, next_middleware)
        else:
            await self._process_update(update)

    async def _process_update(self, update: Dict[str, Any]):
        event_type = update.get('type')
        
        if event_type == 'NewMessage':
            # Check for specific button callbacks first (on_callback decorator)
            msg = update.get("new_message", {})
            message_id = str(msg.get('message_id', ''))
            
            # Skip duplicates for performance
            if self._is_duplicate(message_id):
                return
            
            # Skip old messages (performance optimization)
            if self._has_time_passed(msg.get('time'), seconds=5):
                return
            
            if msg.get('aux_data') and msg['aux_data'].get('button_id'):
                button_id = msg['aux_data']['button_id']
                if button_id in self._on_callback_handler:
                    context = Message(bot=self, chat_id=update.get('object_guid') or update.get('chat_id'),
                                      message_id=message_id, sender_id=msg.get('sender_id'),
                                      text=msg.get('text'), raw_data=msg)
                    asyncio.create_task(self._on_callback_handler[button_id](self, context))
                    return # Handle callback, don't pass to general message handler

            # If not a callback, proceed to general message handler
            if self._message_handler:
                chat_id = update.get('object_guid') or update.get('chat_id')
                if not chat_id: return
                context = Message(bot=self, chat_id=chat_id, message_id=message_id, 
                                  sender_id=msg.get('sender_id'), text=msg.get('text'), raw_data=msg)
                
                handler_info = self._message_handler
                # Check filters (async-aware)
                if handler_info.get("filters"):
                    filter_result = handler_info["filters"]
                    if inspect.iscoroutinefunction(filter_result):
                        if not await filter_result(context):
                            return
                    elif not filter_result(context):
                        return
                
                if handler_info.get("commands"):
                    if not context.text or not context.text.startswith("/"): return
                    parts = context.text.split()
                    cmd = parts[0][1:]
                    if cmd not in handler_info["commands"]: return
                    context.args = parts[1:] if len(parts) > 1 else []
                
                # Process asynchronously for high performance
                asyncio.create_task(handler_info["func"](self, context))
        
        elif event_type == 'UpdatedMessage':
            if self._edited_message_handler:
                msg = update.get("updated_message", {})
                chat_id = update.get('object_guid') or update.get('chat_id')
                if not chat_id: return

                context = Message(
                    bot=self,
                    chat_id=chat_id,
                    message_id=msg.get('message_id'),
                    sender_id=msg.get('sender_id'),
                    text=msg.get('text'),
                    raw_data=msg
                )
                await self._edited_message_handler["func"](self, context)
        elif event_type == 'ReceiveQuery': 
             if self._inline_query_handler:
                msg = update.get("inline_message", {})
                context = InlineMessage(bot=self, raw_data=msg)
                await self._inline_query_handler(self, context)
                return
        elif event_type == 'StartedBot' and self._started_bot_handler:
            chat_id = update.get('chat_id') 
            await self._started_bot_handler(self, chat_id)
        elif event_type == 'StoppedBot' and self._stopped_bot_handler:
            chat_id = update.get('chat_id')
            await self._stopped_bot_handler(self, chat_id)
        elif event_type == 'RemovedMessage':
            removed_id = update.get('removed_message_id')
            logger.info(f"Message {removed_id} was removed in a chat.")
        else:
            logger.debug(f"Received an unhandled event type: {event_type}")

    async def run(self):
        """
        Continuously fetch and process updates for the bot.

        This asynchronous method starts the bot's main loop, which continuously
        polls for new updates (messages, events, etc.) from the server. It manages
        the session life cycle with `aiohttp.ClientSession` and processes each update
        using the `_process_update` method. The method handles exceptions gracefully
        by logging errors and retrying after a short delay.

        Attributes
        ----------
        _offset_id : int
            The current offset ID to keep track of processed updates.
        session : aiohttp.ClientSession
            The HTTP session used for making requests to the API.

        Notes
        -----
        The loop polls the server every 0.5 seconds for updates and adjusts the
        offset ID based on the responses to ensure continuity in message processing.
        Errors in the update loop are logged, and the loop pauses for 5 seconds
        before retrying in case of an error.
        """

        print("🟢 BOT IS WAKING UP ✅")
        self._offset_id = self._read_offset()
        self.running = True
        
        # Run start handlers
        for handler in self.start_handlers:
            if inspect.iscoroutinefunction(handler):
                await handler(self)
            else:
                handler(self)
        
        # Validate token before starting
        await self._validate_token()
        
        # Create session with optimized settings for high performance
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=50)  # High concurrency
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            self.session = session
            print("OFSET UPDATED . LISENNING FOR NEW MESSAGES ♻")

            # Skip first get_updates to avoid old messages
            if self.first_get_updates:
                await self.get_updates(offset_id=self._offset_id, limit=100)
                self.first_get_updates = False

            try:
                while self.running:
                    try:
                        updates_response = await self.get_updates(offset_id=self._offset_id, limit=100)
                        if updates_response and updates_response.get('data'):
                            update_list = updates_response['data'].get('updates', [])
                            
                            # Process all updates in parallel with middleware support for maximum performance
                            tasks = [self._run_middlewares(update) for update in update_list]
                            if tasks:
                                await asyncio.gather(*tasks, return_exceptions=True)

                            next_offset = updates_response['data'].get('next_offset_id')
                            if next_offset:
                                self._offset_id = next_offset
                                self._save_offset(next_offset)
                        
                        # Minimal sleep for high performance (0.1s = 10 requests/second)
                        await asyncio.sleep(0.1)

                    except Exception as e:
                        logger.error(f"An unexpected error occurred in run loop: {e}")
                        await asyncio.sleep(1)  # Shorter retry delay
            finally:
                # Run shutdown handlers
                for handler in self.shutdown_handlers:
                    if inspect.iscoroutinefunction(handler):
                        await handler(self)
                    else:
                        handler(self)

    async def send_message(
        self,
        chat_id: str,
        text: str,
        chat_keypad: Optional[Dict[str, Any]] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        chat_keypad_type: Optional[Any] = None, 
        auto_delete: Optional[float] = None
    ) -> Dict[str, Any]:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification
        }
        if chat_keypad: payload["chat_keypad"] = chat_keypad
        if inline_keypad: payload["inline_keypad"] = inline_keypad
        if reply_to_message_id: payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad_type: payload["chat_keypad_type"] = chat_keypad_type.value if hasattr(chat_keypad_type, 'value') else chat_keypad_type

        result = await self._post("sendMessage", payload)
        
        if auto_delete and result and result.get('data', {}).get('message_update', {}).get('message_id'):
            sent_message_id = result['data']['message_update']['message_id']
            asyncio.create_task(
                self.auto_delete_message(
                    chat_id=chat_id,
                    message_id=sent_message_id,
                    delay=auto_delete
                )
            )
        return result

    async def auto_delete_message(self, chat_id: str, message_id: str, delay: float):
        await asyncio.sleep(delay)
        try:
            await self.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.warning(f"Could not auto-delete message {message_id}: {e}")

    async def send_poll(
        self,
        chat_id: str,
        question: str,
        options: List[str],
        type: Literal["Regular", "Quiz"] = "Regular",
        allows_multiple_answers: bool = False,
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        explanation: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
        chat_keypad: Optional[Dict[str, Any]] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad_type: Optional[Literal["New", "Removed"]] = None
    ) -> Dict[str, Any]:
        """Send a poll with advanced options."""
        payload = {
            "chat_id": chat_id,
            "question": question,
            "options": options,
            "type": type,
            "allows_multiple_answers": allows_multiple_answers,
            "is_anonymous": is_anonymous,
            "disable_notification": disable_notification,
        }
        if correct_option_index is not None:
            payload["correct_option_index"] = correct_option_index
        if explanation:
            payload["explanation"] = explanation
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad:
            payload["chat_keypad"] = chat_keypad
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
        if chat_keypad_type:
            payload["chat_keypad_type"] = chat_keypad_type
        
        return await self._post("sendPoll", payload)

    async def send_location(self, chat_id: str, latitude: str, longitude: str, disable_notification: bool = False, inline_keypad: Optional[Dict[str, Any]] = None, reply_to_message_id: Optional[str] = None, chat_keypad_type: Optional[Literal["New", "Removed"]] = None) -> Dict[str, Any]:
        payload = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude, "disable_notification": disable_notification, "inline_keypad": inline_keypad, "reply_to_message_id": reply_to_message_id, "chat_keypad_type": chat_keypad_type}
        payload = {k: v for k, v in payload.items() if v is not None}
        return await self._post("sendLocation", payload)

    async def send_contact(self, chat_id: str, first_name: str, last_name: str, phone_number: str, chat_keypad: Optional[Dict[str, Any]] = None, inline_keypad: Optional[Dict[str, Any]] = None, disable_notification: bool = False, reply_to_message_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {"chat_id": chat_id, "first_name": first_name, "last_name": last_name, "phone_number": phone_number, "disable_notification": disable_notification}
        if chat_keypad: payload["chat_keypad"] = chat_keypad
        if inline_keypad: payload["inline_keypad"] = inline_keypad
        if reply_to_message_id: payload["reply_to_message_id"] = reply_to_message_id
        return await self._post("sendContact", payload)

    async def get_chat(self, chat_id: str) -> Dict[str, Any]:
        return await self._post("getChat", {"chat_id": chat_id})

    # New method: get_me (from rubpy)
    async def get_me(self) -> Dict[str, Any]:
        """Get bot information."""
        result = await self._post("getMe", {})
        return result.get("data", {})

    # New method: get_name (based on rubka)
    async def get_name(self, user_id: str) -> Optional[str]:
        """Gets the first name of a user from their user_id."""
        try:
            chat_info_response = await self.get_chat(user_id)
            chat_data = chat_info_response.get("data", {}).get("chat", {})
            first_name = chat_data.get("first_name", "")
            last_name = chat_data.get("last_name", "")
            if first_name and last_name:
                return f"{first_name} {last_name}"
            return first_name or last_name or "Unknown"
        except Exception:
            return "Unknown"

    # New method: get_username (based on rubka)
    async def get_username(self, user_id: str) -> Optional[str]:
        """Gets the username of a user from their user_id."""
        try:
            chat_info_response = await self.get_chat(user_id)
            return chat_info_response.get("data", {}).get("chat", {}).get("username", "None")
        except Exception:
            return "None"

    # New method: check_join (placeholder for rubka)
    async def check_join(self, chat_id: str, user_id: str) -> bool:
        """Try to check if `user_id` is member of `chat_id` using an adaptor client when available.

        Falls back to simple False when not available.
        """
        # Try using BotClient Client if present for more advanced member queries
        try:
            from .client_bot import Client as Bot_Client
        except Exception:
            Bot_Client = None

        if Bot_Client:
            try:
                client = Bot_Client(self.token[:6]) if hasattr(Bot_Client, '__call__') else Bot_Client()
                # prefer username lookup when possible
                chat_info = await self.get_chat(user_id)
                username = chat_info.get('data', {}).get('chat', {}).get('username')
                if username:
                    members = client.get_all_members(chat_id, search_text=username)
                    return any(m.get('username') == username for m in members)
                user_guid = chat_info.get('data', {}).get('chat', {}).get('user_id')
                if user_guid:
                    guids = client.get_all_members(chat_id, just_get_guids=True)
                    return user_guid in guids
            except Exception:
                return False

        # fallback
        logger.warning(f"check_join called for chat_id: {chat_id}, user_id: {user_id}. BotClient not available, returning False.")
        return False

    # New method: get_all_member (placeholder for rubka)
    async def get_all_member(self, chat_id: str) -> List[Dict[str, Any]]:
        """Attempt to return members using BotClient Client if available.

        Returns empty list when not available.
        """
        try:
            from .client_bot import Client as Bot_Client
        except Exception:
            Bot_Client = None

        if Bot_Client:
            try:
                client = Bot_Client(self.token[:6]) if hasattr(Bot_Client, '__call__') else Bot_Client()
                return client.get_all_members(chat_id)
            except Exception:
                return []

        logger.warning(f"get_all_member called for chat_id: {chat_id}. BotClient not available, returning empty list.")
        return []

    async def get_updates(self, offset_id: Optional[str] = None, limit: Optional[int] = None, timeout: int = 20) -> Dict[str, Any]:
        data = {}
        if offset_id: data["offset_id"] = offset_id
        if limit: data["limit"] = limit
        return await self._post("getUpdates", data, timeout=timeout)

    async def forward_message(self, from_chat_id: str, message_id: str, to_chat_id: str, disable_notification: bool = False) -> Dict[str, Any]:
        return await self._post("forwardMessage", {"from_chat_id": from_chat_id, "message_id": message_id, "to_chat_id": to_chat_id, "disable_notification": disable_notification})

    async def edit_message_text(self, chat_id: str, message_id: str, text: str) -> Dict[str, Any]:
        return await self._post("editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text})

    async def edit_inline_keypad(self,chat_id: str,message_id: str,inline_keypad: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("editMessageKeypad", {"chat_id": chat_id,"message_id": message_id, "inline_keypad": inline_keypad})

    async def delete_message(self, chat_id: str, message_id: str) -> Dict[str, Any]:
        return await self._post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    async def set_commands(self, bot_commands: List[Dict[str, str]]) -> Dict[str, Any]:
        return await self._post("setCommands", {"bot_commands": bot_commands})

    async def update_bot_endpoint(self, url: str, type: str) -> Dict[str, Any]:
        return await self._post("updateBotEndpoints", {"url": url, "type": type})

    async def remove_keypad(self, chat_id: str) -> Dict[str, Any]:
        return await self._post("editChatKeypad", {"chat_id": chat_id, "chat_keypad_type": "Removed"})

    async def edit_chat_keypad(self, chat_id: str, chat_keypad: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("editChatKeypad", {"chat_id": chat_id, "chat_keypad_type": "New", "chat_keypad": chat_keypad})

    # Additional API methods from rubpy for enhanced functionality
    async def get_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Get information about a member of a chat."""
        return await self._post("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def pin_chat_message(self, chat_id: str, message_id: str, disable_notification: bool = False) -> Dict[str, Any]:
        """Pin a message in a chat."""
        return await self._post("pinChatMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification
        })

    async def unpin_chat_message(self, chat_id: str, message_id: str) -> Dict[str, Any]:
        """Unpin a message in a chat."""
        return await self._post("unpinChatMessage", {
            "chat_id": chat_id,
            "message_id": message_id
        })

    async def unpin_all_chat_messages(self, chat_id: str) -> Dict[str, Any]:
        """Unpin all messages in a chat."""
        return await self._post("unpinAllChatMessages", {"chat_id": chat_id})

    async def get_chat_administrators(self, chat_id: str) -> Dict[str, Any]:
        """Get a list of administrators in a chat."""
        return await self._post("getChatAdministrators", {"chat_id": chat_id})

    async def get_chat_member_count(self, chat_id: str) -> Dict[str, Any]:
        """Get the number of members in a chat."""
        return await self._post("getChatMemberCount", {"chat_id": chat_id})

    async def ban_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Ban a member from a chat."""
        return await self._post("banChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def unban_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Unban a member from a chat."""
        return await self._post("unbanChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def send_photo(
        self,
        chat_id: str,
        photo: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send photo (supports file path or file_id/photo string)."""
        # If photo is a path, upload it first
        if photo and isinstance(photo, (str, Path)) and Path(photo).exists():
            file_name = Path(photo).name
            upload_url = await self.get_upload_url("Image")
            file_id = await self.upload_file(upload_url, file_name, photo)
            photo = file_id
        
        # If photo is still a string (file_id from API), use it directly
        if not photo and not file_id:
            raise ValueError("Either photo (path/file_id) or file_id must be provided.")
        
        photo_id = photo or file_id
        payload = {"chat_id": chat_id, "photo": photo_id, "disable_notification": disable_notification}
        if caption: payload["caption"] = caption
        if reply_to_message_id: payload["reply_to_message_id"] = reply_to_message_id
        if inline_keypad: payload["inline_keypad"] = inline_keypad
        if chat_keypad: payload["chat_keypad"] = chat_keypad
        return await self._post("sendPhoto", payload)

    async def send_video(
        self,
        chat_id: str,
        video: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send video (supports file path or file_id/video string)."""
        # If video is a path, upload it first
        if video and isinstance(video, (str, Path)) and Path(video).exists():
            file_name = Path(video).name
            upload_url = await self.get_upload_url("Video")
            file_id = await self.upload_file(upload_url, file_name, video)
            video = file_id
        
        # If video is still a string (file_id from API), use it directly
        if not video and not file_id:
            raise ValueError("Either video (path/file_id) or file_id must be provided.")
        
        video_id = video or file_id
        payload = {"chat_id": chat_id, "video": video_id, "disable_notification": disable_notification}
        if caption: payload["caption"] = caption
        if reply_to_message_id: payload["reply_to_message_id"] = reply_to_message_id
        if inline_keypad: payload["inline_keypad"] = inline_keypad
        if chat_keypad: payload["chat_keypad"] = chat_keypad
        return await self._post("sendVideo", payload)

    async def send_document(
        self,
        chat_id: str,
        path: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        document: Optional[str] = None,  # Legacy support
        text: Optional[str] = None,
        caption: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
        chat_keypad_type: Optional[Literal["New", "Removed"]] = None
    ) -> Dict[str, Any]:
        """Send document (supports file path or file_id/document string)."""
        # Legacy support: if document is provided, use it as file_id
        if document and not file_id and not path:
            file_id = document
        
        # If path is provided, upload it first
        if path:
            file_name = Path(path).name
            upload_url = await self.get_upload_url("File")
            file_id = await self.upload_file(upload_url, file_name, path)
        
        if not file_id:
            raise ValueError("Either path, file_id, or document must be provided.")
        
        payload = {
            "chat_id": chat_id,
            "file_id": file_id,
            "text": text or caption,
            "disable_notification": disable_notification,
        }
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
        if chat_keypad:
            payload["chat_keypad"] = chat_keypad
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad_type:
            payload["chat_keypad_type"] = chat_keypad_type
        
        return await self._post("sendFile", payload)

    async def send_sticker(self, chat_id: str, sticker_id: str, disable_notification: bool = False, reply_to_message_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {"chat_id": chat_id, "sticker_id": sticker_id, "disable_notification": disable_notification}
        if reply_to_message_id: payload["reply_to_message_id"] = reply_to_message_id
        return await self._post("sendSticker", payload)

    async def send_file(self, chat_id: str, file_id: str, **kwargs) -> Dict[str, Any]:
        payload = {"chat_id": chat_id, "file_id": file_id, **kwargs}
        return await self._post("sendFile", payload)

    # File upload/download methods (from rubpy and rubka)
    async def get_upload_url(self, media_type: Literal['File', 'Image', 'Voice', 'Music', 'Gif', 'Video']) -> str:
        """Get upload URL for file type."""
        allowed = ['File', 'Image', 'Voice', 'Music', 'Gif', 'Video']
        if media_type not in allowed:
            raise ValueError(f"Invalid media type. Must be one of {allowed}")
        result = await self._post("requestSendFile", {"type": media_type})
        return result.get("data", {}).get("upload_url")

    async def upload_file(self, upload_url: str, file_name: str, file_path: Union[str, Path]) -> str:
        """Upload file to server and return file_id."""
        import mimetypes
        import os
        
        if isinstance(file_path, str) and file_path.startswith("http"):
            import requests
            response = requests.get(file_path)
            if response.status_code != 200:
                raise APIRequestError(f"Failed to download file from URL ({response.status_code})")
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(response.content)
            temp_file.close()
            file_path = temp_file.name
            is_temp = True
        else:
            is_temp = False
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        content_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        
        async with aiofiles.open(str(file_path), 'rb') as f:
            file_data = await f.read()
        
        form_data = aiohttp.FormData()
        form_data.add_field('file', file_data, filename=file_name, content_type=content_type)
        
        async with aiohttp.ClientSession() as upload_session:
            async with upload_session.post(upload_url, data=form_data) as response:
                if response.status != 200:
                    text = await response.text()
                    raise APIRequestError(f"Upload failed ({response.status}): {text}")
                data = await response.json()
                file_id = data.get('data', {}).get('file_id')
                if not file_id:
                    raise APIRequestError("No file_id in upload response")
                
                if is_temp:
                    os.remove(file_path)
                
                return file_id

    async def get_file_url(self, file_id: str) -> str:
        """Get download URL for file_id."""
        result = await self._post("getFile", {'file_id': file_id})
        return result.get("data", {}).get("download_url")

    async def download_file(
        self,
        file_id: str,
        save_as: Optional[str] = None,
        chunk_size: int = 65536,
        as_bytes: bool = False,
        timeout: Optional[Union[int, float]] = 60.0
    ) -> Union[str, bytes]:
        """Download file by file_id."""
        import mimetypes
        
        download_url = await self.get_file_url(file_id)
        if not download_url:
            raise ValueError(f"Invalid file_id: {file_id}")

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(download_url) as response:
                if response.status != 200:
                    raise APIRequestError(f"Failed to download file: {response.status}")

                content_type = response.headers.get("Content-Type", "")
                ext = mimetypes.guess_extension(content_type) or ""
                total_size = int(response.headers.get("Content-Length", 0))

                if as_bytes:
                    content = bytearray()
                    async for chunk in response.content.iter_chunked(chunk_size):
                        content.extend(chunk)
                    return bytes(content)
                else:
                    if save_as is None:
                        save_as = f"{file_id}{ext}"

                    async with aiofiles.open(save_as, "wb") as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await f.write(chunk)

                    return save_as

    # New send methods with file upload support (from rubka)
    async def send_image(
        self,
        chat_id: str,
        path: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        text: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
        chat_keypad_type: Optional[Literal["New", "Removed"]] = None
    ) -> Dict[str, Any]:
        """Send image (supports file path or file_id)."""
        if path:
            file_name = Path(path).name
            upload_url = await self.get_upload_url("Image")
            file_id = await self.upload_file(upload_url, file_name, path)
        if not file_id:
            raise ValueError("Either path or file_id must be provided.")
        
        payload = {
            "chat_id": chat_id,
            "file_id": file_id,
            "text": text,
            "disable_notification": disable_notification,
        }
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
        if chat_keypad:
            payload["chat_keypad"] = chat_keypad
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad_type:
            payload["chat_keypad_type"] = chat_keypad_type
        
        return await self._post("sendFile", payload)

    async def send_music(
        self,
        chat_id: str,
        path: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        text: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
        chat_keypad_type: Optional[Literal["New", "Removed"]] = None
    ) -> Dict[str, Any]:
        """Send music file."""
        if path:
            file_name = Path(path).name
            upload_url = await self.get_upload_url("Music")
            file_id = await self.upload_file(upload_url, file_name, path)
        if not file_id:
            raise ValueError("Either path or file_id must be provided.")
        
        payload = {
            "chat_id": chat_id,
            "file_id": file_id,
            "text": text,
            "disable_notification": disable_notification,
        }
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
        if chat_keypad:
            payload["chat_keypad"] = chat_keypad
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad_type:
            payload["chat_keypad_type"] = chat_keypad_type
        
        return await self._post("sendFile", payload)

    async def send_voice(
        self,
        chat_id: str,
        path: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        text: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
        chat_keypad_type: Optional[Literal["New", "Removed"]] = None
    ) -> Dict[str, Any]:
        """Send voice message."""
        if path:
            file_name = Path(path).name
            upload_url = await self.get_upload_url("Voice")
            file_id = await self.upload_file(upload_url, file_name, path)
        if not file_id:
            raise ValueError("Either path or file_id must be provided.")
        
        payload = {
            "chat_id": chat_id,
            "file_id": file_id,
            "text": text,
            "disable_notification": disable_notification,
        }
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
        if chat_keypad:
            payload["chat_keypad"] = chat_keypad
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad_type:
            payload["chat_keypad_type"] = chat_keypad_type
        
        return await self._post("sendFile", payload)

    async def send_gif(
        self,
        chat_id: str,
        path: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        text: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
        chat_keypad_type: Optional[Literal["New", "Removed"]] = None
    ) -> Dict[str, Any]:
        """Send GIF."""
        if path:
            file_name = Path(path).name
            upload_url = await self.get_upload_url("Gif")
            file_id = await self.upload_file(upload_url, file_name, path)
        if not file_id:
            raise ValueError("Either path or file_id must be provided.")
        
        payload = {
            "chat_id": chat_id,
            "file_id": file_id,
            "text": text,
            "disable_notification": disable_notification,
        }
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
        if chat_keypad:
            payload["chat_keypad"] = chat_keypad
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad_type:
            payload["chat_keypad_type"] = chat_keypad_type
        
        return await self._post("sendFile", payload)

    async def send_document(
        self,
        chat_id: str,
        path: Optional[Union[str, Path]] = None,
        file_id: Optional[str] = None,
        text: Optional[str] = None,
        inline_keypad: Optional[Dict[str, Any]] = None,
        chat_keypad: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: bool = False,
        chat_keypad_type: Optional[Literal["New", "Removed"]] = None
    ) -> Dict[str, Any]:
        """Send document (supports file path or file_id)."""
        if path:
            file_name = Path(path).name
            upload_url = await self.get_upload_url("File")
            file_id = await self.upload_file(upload_url, file_name, path)
        if not file_id:
            raise ValueError("Either path or file_id must be provided.")
        
        payload = {
            "chat_id": chat_id,
            "file_id": file_id,
            "text": text,
            "disable_notification": disable_notification,
        }
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
        if chat_keypad:
            payload["chat_keypad"] = chat_keypad
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if chat_keypad_type:
            payload["chat_keypad_type"] = chat_keypad_type
        
        return await self._post("sendFile", payload)

    # Context managers for better resource management
    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def stop(self):
        """Stop the bot gracefully."""
        self.running = False
        # Run shutdown handlers
        for handler in self.shutdown_handlers:
            if inspect.iscoroutinefunction(handler):
                await handler(self)
            else:
                handler(self)
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("Bot stopped")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    def __enter__(self):
        """Sync context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        self.running = False