# -*- coding: utf-8 -*-

"""Interactive TUI for Account Pool management."""

import asyncio
from typing import Optional, Dict, List, Any
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    TextArea,
)
from textual.binding import Binding
from textual import events
from .service import AccountService
from .data_manager import CacheManager
from ..common.service_factory import ServiceFactory


# Display constants
DEFAULT_SEPARATOR_WIDTH = 60
MODAL_SEPARATOR_WIDTH = 110
MAX_DISPLAY_TEXT_LENGTH = 40
NOTIFICATION_TIMEOUT = 2
WARNING_TIMEOUT = 3


class BaseScreen(Screen):
    """Base screen with common functionality."""
    
    BINDINGS = [
        Binding("escape", "back", "Back", priority=True),
    ]
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()


class ScrollableTextAreaMixin:
    """Mixin for screens with scrollable TextArea."""
    
    async def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        """Handle scroll with reduced step for better UX."""
        control = event.control
        if isinstance(control, TextArea):
            control.action_scroll_up()
            event.stop()
    
    async def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        """Handle scroll with reduced step for better UX."""
        control = event.control
        if isinstance(control, TextArea):
            control.action_scroll_down()
            event.stop()


class BaseResultScreen(BaseScreen, ScrollableTextAreaMixin):
    """Base screen for displaying results in TextArea."""
    
    def on_mount(self) -> None:
        """Initialize with scroll settings."""
        if hasattr(self, 'query_one'):
            try:
                result_area = self.query_one("#result-area", TextArea)
                result_area.show_line_numbers = False
            except Exception:
                pass
    
    def _format_account_info(self, account: Dict, separator_width: int = DEFAULT_SEPARATOR_WIDTH, use_na_for_missing: bool = False) -> str:
        """
        Format account information for display - unified version.
        
        Args:
            account: Account dictionary
            separator_width: Width of separator line (default: DEFAULT_SEPARATOR_WIDTH)
            use_na_for_missing: If True, use 'N/A' for missing fields; otherwise skip them
        
        Returns:
            Formatted account information string
        """
        lines = []
        separator = "=" * separator_width
        lines.append(separator)
        lines.append("Account Information")
        lines.append(separator)
        
        # Helper function to format field
        def add_field(emoji: str, label: str, value: Any, show_if_none: bool = False):
            if value is not None or show_if_none:
                display_value = value if value is not None else 'N/A'
                lines.append(f"{emoji} {label}: {display_value}")
        
        # Show main fields
        if use_na_for_missing:
            add_field("📱", "Phone", account.get('mainNumber'), show_if_none=True)
            add_field("🆔", "Account ID", account.get('accountId'), show_if_none=True)
            add_field("🏷️ ", "Type", account.get('accountType'), show_if_none=True)
            add_field("🌐", "Environment", account.get('envName'), show_if_none=True)
            add_field("📧", "Email Domain", account.get('companyEmailDomain'), show_if_none=True)
            add_field("📅", "Created", account.get('createdAt'), show_if_none=True)
            add_field("🔗", "MongoDB ID", account.get('_id'), show_if_none=True)
        else:
            if account.get('mainNumber'):
                lines.append(f"📱 Phone: {account['mainNumber']}")
            if account.get('accountId'):
                lines.append(f"🆔 Account ID: {account['accountId']}")
            if account.get('accountType'):
                lines.append(f"🏷️  Type: {account['accountType']}")
            if account.get('envName'):
                lines.append(f"🌐 Environment: {account['envName']}")
            if account.get('companyEmailDomain'):
                lines.append(f"📧 Email Domain: {account['companyEmailDomain']}")
            if account.get('createdAt'):
                lines.append(f"📅 Created: {account['createdAt']}")
            if account.get('loginTimes') is not None:
                lines.append(f"🔢 Login Times: {account['loginTimes']}")
            if account.get('_id'):
                lines.append(f"🔗 MongoDB ID: {account['_id']}")
        
        # Status
        locked = account.get("locked", [])
        status = "🔒 Locked" if locked else "✅ Available"
        lines.append(f"🔐 Status: {status}")
        
        if locked:
            lines.append(f"🛑 Lock Details:")
            for item in locked:
                if isinstance(item, dict):
                    lines.append(f"  • Type: {item.get('accountType', 'N/A')}")
        
        lines.append(separator)
        return "\n".join(lines)


class GetRandomAccountScreen(BaseResultScreen):
    """Screen for getting a random account."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="get-random-container"):
                yield Label("🎲 Get Random Account", id="get-random-title")
                yield Label(
                    "💡 Tip: Use '🏦 List Account Types' in main menu to see all available types",
                    id="get-random-tip"
                )
                yield Input(
                    placeholder="Account Type (e.g., webAqaXmn, webBetaXmn, or index like 1, 2, 3...)",
                    id="account-type-input"
                )
                yield Input(
                    placeholder=f"Environment (default: {AccountService.DEFAULT_ENV_NAME})",
                    id="env-input"
                )
                yield TextArea(id="result-area", read_only=True)
                with Horizontal(id="get-random-buttons"):
                    yield Button("Get Account", id="get-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                    yield Button("Show Types", id="show-types-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the get random account screen."""
        super().on_mount()
        self.query_one("#account-type-input", Input).focus()
        env_input = self.query_one("#env-input", Input)
        env_input.value = AccountService.DEFAULT_ENV_NAME
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "get-btn":
            await self._get_random_account()
        elif event.button.id == "clear-btn":
            self.query_one("#account-type-input", Input).value = ""
            self.query_one("#env-input", Input).value = AccountService.DEFAULT_ENV_NAME
            self.query_one("#result-area", TextArea).text = ""
        elif event.button.id == "show-types-btn":
            self.app.push_screen("list_types")
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "account-type-input":
            self.query_one("#env-input", Input).focus()
        elif event.input.id == "env-input":
            await self._get_random_account()
    
    async def _get_random_account(self) -> None:
        """Get a random account."""
        account_type = self.query_one("#account-type-input", Input).value.strip()
        env_name = self.query_one("#env-input", Input).value.strip() or AccountService.DEFAULT_ENV_NAME
        
        if not account_type:
            self.query_one("#get-random-title", Label).update(
                "⚠️  Please enter Account Type"
            )
            return
        
        result_area = self.query_one("#result-area", TextArea)
        self.query_one("#get-random-title", Label).update("🎲 Loading...")
        result_area.text = ""
        
        try:
            account_service = ServiceFactory.get_account_service()
            
            # Run synchronous method in thread pool
            loop = asyncio.get_event_loop()
            account_result = await loop.run_in_executor(
                None,
                lambda: self._get_random_account_sync(account_service, account_type, env_name)
            )
            
            if account_result is None:
                self.query_one("#get-random-title", Label).update(
                    "❌ Failed to get account"
                )
                result_area.text = "❌ Failed to get account. Please check your inputs and try again."
                return
            
            if isinstance(account_result, tuple) and account_result[0] is None:
                # Error case
                error_msg = account_result[1]
                self.query_one("#get-random-title", Label).update(f"❌ {error_msg}")
                error_detail = (
                    f"Error: {error_msg}\n\n"
                    f"Search Criteria:\n"
                    f"  • Account Type: {account_type}\n"
                    f"  • Environment: {env_name}\n\n"
                    f"💡 Tips:\n"
                    f"  1. Check if the account type exists (click 'Show Types' button)\n"
                    f"  2. Try a different environment (e.g., ci.qa, ci.beta)\n"
                    f"  3. Some account types may not be available in all environments"
                )
                result_area.text = error_detail
                return
            
            account = account_result if not isinstance(account_result, tuple) else account_result[0]
            formatted_output = self._format_account_info(account)
            result_area.text = formatted_output
            self.query_one("#get-random-title", Label).update(
                f"✅ Random account retrieved"
            )
            
        except Exception as e:
            self.query_one("#get-random-title", Label).update(
                f"❌ Error: {str(e)}"
            )
            result_area.text = f"Error: {str(e)}"
    
    def _get_random_account_sync(self, account_service: AccountService, account_type: str, env_name: str) -> Optional[Dict]:
        """Synchronous wrapper for getting random account."""
        try:
            from returns.pipeline import is_successful
            
            final_account_type = account_type
            if account_type.isdigit():
                cached_type = CacheManager.get_account_type_by_index(int(account_type))
                if not cached_type:
                    return (None, "Account type index not found in cache")
                final_account_type = cached_type
            
            result = account_service.data_manager.get_accounts(env_name, final_account_type).bind(
                account_service._select_random_account
            )
            
            if is_successful(result):
                return result.unwrap()
            else:
                error = result.failure()
                return (None, error.message)
        except Exception as e:
            return (None, str(e))


class GetAccountByIdScreen(BaseResultScreen):
    """Screen for getting account by ID."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="get-by-id-container"):
                yield Label("🆔 Get Account by ID", id="get-by-id-title")
                yield Input(placeholder="Account ID", id="account-id-input")
                yield Input(
                    placeholder=f"Environment (default: {AccountService.DEFAULT_ENV_NAME})",
                    id="env-input"
                )
                yield TextArea(id="result-area", read_only=True)
                with Horizontal(id="get-by-id-buttons"):
                    yield Button("Get Account", id="get-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the get by ID screen."""
        super().on_mount()
        self.query_one("#account-id-input", Input).focus()
        env_input = self.query_one("#env-input", Input)
        env_input.value = AccountService.DEFAULT_ENV_NAME
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "get-btn":
            await self._get_account_by_id()
        elif event.button.id == "clear-btn":
            self.query_one("#account-id-input", Input).value = ""
            self.query_one("#env-input", Input).value = AccountService.DEFAULT_ENV_NAME
            self.query_one("#result-area", TextArea).text = ""
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "account-id-input":
            self.query_one("#env-input", Input).focus()
        elif event.input.id == "env-input":
            await self._get_account_by_id()
    
    async def _get_account_by_id(self) -> None:
        """Get account by ID."""
        account_id = self.query_one("#account-id-input", Input).value.strip()
        env_name = self.query_one("#env-input", Input).value.strip() or AccountService.DEFAULT_ENV_NAME
        
        if not account_id:
            self.query_one("#get-by-id-title", Label).update(
                "⚠️  Please enter Account ID"
            )
            return
        
        result_area = self.query_one("#result-area", TextArea)
        self.query_one("#get-by-id-title", Label).update("🆔 Loading...")
        result_area.text = ""
        
        try:
            account_service = ServiceFactory.get_account_service()
            
            loop = asyncio.get_event_loop()
            account_result = await loop.run_in_executor(
                None,
                lambda: self._get_account_by_id_sync(account_service, account_id, env_name)
            )
            
            if account_result is None:
                self.query_one("#get-by-id-title", Label).update(
                    "❌ Failed to get account"
                )
                result_area.text = "❌ Failed to get account. Please check your inputs and try again."
                return
            
            if isinstance(account_result, tuple) and account_result[0] is None:
                error_msg = account_result[1]
                self.query_one("#get-by-id-title", Label).update(f"❌ {error_msg}")
                result_area.text = f"Error: {error_msg}"
                return
            
            account = account_result if not isinstance(account_result, tuple) else account_result[0]
            formatted_output = self._format_account_info(account)
            result_area.text = formatted_output
            self.query_one("#get-by-id-title", Label).update(
                f"✅ Account retrieved"
            )
            
        except Exception as e:
            self.query_one("#get-by-id-title", Label).update(
                f"❌ Error: {str(e)}"
            )
            result_area.text = f"Error: {str(e)}"
    
    def _get_account_by_id_sync(self, account_service: AccountService, account_id: str, env_name: str) -> Optional[Dict]:
        """Synchronous wrapper for getting account by ID."""
        try:
            from returns.pipeline import is_successful
            
            result = account_service.data_manager.get_account_by_id(account_id, env_name)
            
            if is_successful(result):
                return result.unwrap()
            else:
                error = result.failure()
                return (None, error.message)
        except Exception as e:
            return (None, str(e))


class GetAccountByPhoneScreen(BaseResultScreen):
    """Screen for getting account by phone number."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="get-by-phone-container"):
                yield Label("📱 Get Account by Phone", id="get-by-phone-title")
                yield Input(placeholder="Phone Number", id="phone-input")
                yield Input(
                    placeholder=f"Environment (default: {AccountService.DEFAULT_ENV_NAME})",
                    id="env-input"
                )
                yield TextArea(id="result-area", read_only=True)
                with Horizontal(id="get-by-phone-buttons"):
                    yield Button("Get Account", id="get-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the get by phone screen."""
        super().on_mount()
        self.query_one("#phone-input", Input).focus()
        env_input = self.query_one("#env-input", Input)
        env_input.value = AccountService.DEFAULT_ENV_NAME
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "get-btn":
            await self._get_account_by_phone()
        elif event.button.id == "clear-btn":
            self.query_one("#phone-input", Input).value = ""
            self.query_one("#env-input", Input).value = AccountService.DEFAULT_ENV_NAME
            self.query_one("#result-area", TextArea).text = ""
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "phone-input":
            self.query_one("#env-input", Input).focus()
        elif event.input.id == "env-input":
            await self._get_account_by_phone()
    
    async def _get_account_by_phone(self) -> None:
        """Get account by phone number."""
        phone = self.query_one("#phone-input", Input).value.strip()
        env_name = self.query_one("#env-input", Input).value.strip() or AccountService.DEFAULT_ENV_NAME
        
        if not phone:
            self.query_one("#get-by-phone-title", Label).update(
                "⚠️  Please enter Phone Number"
            )
            return
        
        result_area = self.query_one("#result-area", TextArea)
        self.query_one("#get-by-phone-title", Label).update("📱 Loading...")
        result_area.text = ""
        
        try:
            account_service = ServiceFactory.get_account_service()
            
            loop = asyncio.get_event_loop()
            account_result = await loop.run_in_executor(
                None,
                lambda: self._get_account_by_phone_sync(account_service, phone, env_name)
            )
            
            if account_result is None:
                self.query_one("#get-by-phone-title", Label).update(
                    "❌ Failed to get account"
                )
                result_area.text = "❌ Failed to get account. Please check your inputs and try again."
                return
            
            if isinstance(account_result, tuple) and account_result[0] is None:
                error_msg = account_result[1]
                self.query_one("#get-by-phone-title", Label).update(f"❌ {error_msg}")
                result_area.text = f"Error: {error_msg}"
                return
            
            account = account_result if not isinstance(account_result, tuple) else account_result[0]
            formatted_output = self._format_account_info(account)
            result_area.text = formatted_output
            self.query_one("#get-by-phone-title", Label).update(
                f"✅ Account retrieved"
            )
            
        except Exception as e:
            self.query_one("#get-by-phone-title", Label).update(
                f"❌ Error: {str(e)}"
            )
            result_area.text = f"Error: {str(e)}"
    
    def _get_account_by_phone_sync(self, account_service: AccountService, phone: str, env_name: str) -> Optional[Dict]:
        """Synchronous wrapper for getting account by phone."""
        try:
            from returns.pipeline import is_successful
            from my_cli_utilities_common.config import ValidationUtils
            
            main_number_str = ValidationUtils.normalize_phone_number(phone)
            if not main_number_str:
                return (None, "Invalid phone number format")
            
            result = account_service.data_manager.get_all_accounts_for_env(env_name).bind(
                lambda accounts: account_service._find_account_by_phone_in_list(accounts, main_number_str)
            )
            
            if is_successful(result):
                return result.unwrap()
            else:
                error = result.failure()
                return (None, error.message)
        except Exception as e:
            return (None, str(e))
    
    def _format_account_info(self, account: Dict) -> str:
        """Format account information for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("Account Information")
        lines.append("=" * 60)
        lines.append(f"📱 Phone: {account.get('mainNumber', 'N/A')}")
        lines.append(f"🆔 Account ID: {account.get('accountId', 'N/A')}")
        lines.append(f"🏷️  Type: {account.get('accountType', 'N/A')}")
        lines.append(f"🌐 Environment: {account.get('envName', 'N/A')}")
        lines.append(f"📧 Email Domain: {account.get('companyEmailDomain', 'N/A')}")
        lines.append(f"📅 Created: {account.get('createdAt', 'N/A')}")
        lines.append(f"🔗 MongoDB ID: {account.get('_id', 'N/A')}")
        
        locked = account.get("locked", [])
        status = "🔒 Locked" if locked else "✅ Available"
        lines.append(f"🔐 Status: {status}")
        
        if locked:
            lines.append(f"🛑 Lock Details:")
            for item in locked:
                if isinstance(item, dict):
                    lines.append(f"  • Type: {item.get('accountType', 'N/A')}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class ListAccountTypesScreen(BaseScreen):
    """Screen for listing account types."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="list-types-container"):
                yield Label("🏦 List Account Types", id="list-types-title")
                yield Input(
                    placeholder=f"Brand (default: {AccountService.DEFAULT_BRAND})",
                    id="brand-input"
                )
                yield Input(
                    placeholder="Filter keyword (optional)",
                    id="filter-input"
                )
                yield DataTable(id="types-table")
                with Horizontal(id="list-types-buttons"):
                    yield Button("List Types", id="list-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the list types screen."""
        table = self.query_one("#types-table", DataTable)
        table.add_columns("#", "Account Type")
        self.query_one("#brand-input", Input).focus()
        brand_input = self.query_one("#brand-input", Input)
        brand_input.value = AccountService.DEFAULT_BRAND
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "list-btn":
            await self._load_account_types()
        elif event.button.id == "clear-btn":
            self.query_one("#brand-input", Input).value = AccountService.DEFAULT_BRAND
            self.query_one("#filter-input", Input).value = ""
            table = self.query_one("#types-table", DataTable)
            table.clear()
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "brand-input":
            self.query_one("#filter-input", Input).focus()
        elif event.input.id == "filter-input":
            await self._load_account_types()
    
    async def _load_account_types(self) -> None:
        """Load account types."""
        brand = self.query_one("#brand-input", Input).value.strip() or AccountService.DEFAULT_BRAND
        filter_keyword = self.query_one("#filter-input", Input).value.strip() or None
        
        table = self.query_one("#types-table", DataTable)
        table.clear()
        
        self.query_one("#list-types-title", Label).update("🏦 Loading...")
        
        try:
            account_service = ServiceFactory.get_account_service()
            
            loop = asyncio.get_event_loop()
            types = await loop.run_in_executor(
                None,
                lambda: self._load_account_types_sync(account_service, brand, filter_keyword)
            )
            
            if types is None:
                self.query_one("#list-types-title", Label).update(
                    "❌ Failed to load account types. Please check brand and try again."
                )
                return
            
            # Add results to table
            for i, account_type_setting in enumerate(types, 1):
                account_type = account_type_setting.get("accountType", "N/A")
                table.add_row(str(i), account_type, key=str(i))
            
            title_text = f"🏦 {len(types)} Account Types"
            if filter_keyword:
                title_text += f" (filtered by '{filter_keyword}')"
            self.query_one("#list-types-title", Label).update(title_text)
            
        except Exception as e:
            self.query_one("#list-types-title", Label).update(
                f"❌ Error: {str(e)}"
            )
    
    def _load_account_types_sync(self, account_service: AccountService, brand: str, filter_keyword: Optional[str]) -> Optional[List[Dict]]:
        """Synchronous wrapper for loading account types."""
        try:
            from returns.pipeline import is_successful
            
            result = account_service.data_manager.get_account_settings(brand).map(
                lambda settings: account_service._filter_settings(settings, filter_keyword)
            )
            
            if is_successful(result):
                types = result.unwrap()
                # Cache the results
                CacheManager.save_cache(
                    [t.get("accountType") for t in types],
                    filter_keyword,
                    brand
                )
                return types
            else:
                error = result.failure()
                return None
        except Exception as e:
            return None


class CacheManagementScreen(BaseScreen, ScrollableTextAreaMixin):
    """Screen for cache management."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="cache-container"):
                yield Label("💾 Cache Management", id="cache-title")
                yield TextArea(id="cache-info-area", read_only=True)
                with Horizontal(id="cache-buttons"):
                    yield Button("Refresh", id="refresh-btn", variant="primary")
                    yield Button("Clear Cache", id="clear-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the cache management screen."""
        try:
            text_area = self.query_one("#cache-info-area", TextArea)
            text_area.show_line_numbers = False
        except Exception:
            pass
        self.app.call_later(self._load_cache_info)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "refresh-btn":
            await self._load_cache_info()
        elif event.button.id == "clear-btn":
            await self._clear_cache()
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def _load_cache_info(self) -> None:
        """Load cache information."""
        try:
            loop = asyncio.get_event_loop()
            cache_info = await loop.run_in_executor(
                None,
                lambda: CacheManager.load_cache()
            )
            
            info_area = self.query_one("#cache-info-area", TextArea)
            
            if not cache_info:
                info_area.text = "ℹ️  Cache is empty."
                self.query_one("#cache-title", Label).update("💾 Cache Status: Empty")
                return
            
            lines = []
            lines.append("=" * 60)
            lines.append("Cache Status")
            lines.append("=" * 60)
            
            for key, value in cache_info.items():
                display_key = key.replace('_', ' ').title()
                display_value = value
                if isinstance(value, list) and len(value) > 10:
                    display_value = f"[{len(value)} items] {value[:5]}..."
                lines.append(f"{display_key}: {display_value}")
            
            lines.append("=" * 60)
            info_area.text = "\n".join(lines)
            self.query_one("#cache-title", Label).update("💾 Cache Status: Loaded")
            
        except Exception as e:
            self.query_one("#cache-title", Label).update(
                f"❌ Error: {str(e)}"
            )
    
    async def _clear_cache(self) -> None:
        """Clear cache."""
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                lambda: CacheManager.clear_cache()
            )
            
            if success:
                self.query_one("#cache-info-area", TextArea).text = "✅ Cache cleared successfully"
                self.query_one("#cache-title", Label).update("💾 Cache Status: Cleared")
            else:
                self.query_one("#cache-info-area", TextArea).text = "ℹ️  No cache file to clear."
                self.query_one("#cache-title", Label).update("💾 Cache Status: Already Empty")
                
        except Exception as e:
            self.query_one("#cache-title", Label).update(
                f"❌ Error: {str(e)}"
            )


class GetAccountByAliasScreen(BaseResultScreen):
    """Screen for getting account by alias."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="get-by-alias-container"):
                yield Label("🏷️  Get Account by Alias", id="get-by-alias-title")
                yield Input(placeholder="Alias (e.g., webAqaXmn)", id="alias-input")
                yield Input(
                    placeholder=f"Environment (default: {AccountService.DEFAULT_ENV_NAME})",
                    id="env-input"
                )
                yield Input(placeholder="Account Type (optional)", id="type-input")
                yield TextArea(id="result-area", read_only=True)
                with Horizontal(id="get-by-alias-buttons"):
                    yield Button("Get Account", id="get-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the get by alias screen."""
        super().on_mount()
        self.query_one("#alias-input", Input).focus()
        env_input = self.query_one("#env-input", Input)
        env_input.value = AccountService.DEFAULT_ENV_NAME
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "get-btn":
            await self._get_account_by_alias()
        elif event.button.id == "clear-btn":
            self.query_one("#alias-input", Input).value = ""
            self.query_one("#env-input", Input).value = AccountService.DEFAULT_ENV_NAME
            self.query_one("#type-input", Input).value = ""
            self.query_one("#result-area", TextArea).text = ""
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "alias-input":
            self.query_one("#env-input", Input).focus()
        elif event.input.id == "env-input":
            self.query_one("#type-input", Input).focus()
        elif event.input.id == "type-input":
            await self._get_account_by_alias()
    
    async def _get_account_by_alias(self) -> None:
        """Get account by alias."""
        alias = self.query_one("#alias-input", Input).value.strip()
        env_name = self.query_one("#env-input", Input).value.strip() or AccountService.DEFAULT_ENV_NAME
        account_type = self.query_one("#type-input", Input).value.strip() or None
        
        if not alias:
            self.query_one("#get-by-alias-title", Label).update(
                "⚠️  Please enter Alias"
            )
            return
        
        result_area = self.query_one("#result-area", TextArea)
        self.query_one("#get-by-alias-title", Label).update("🏷️  Loading...")
        result_area.text = ""
        
        try:
            account_service = ServiceFactory.get_account_service()
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._get_account_by_alias_sync(account_service, alias, env_name, account_type)
            )
            
            if result is None or (isinstance(result, tuple) and result[0] is None):
                error_msg = result[1] if isinstance(result, tuple) else "Failed to get account"
                self.query_one("#get-by-alias-title", Label).update(f"❌ {error_msg}")
                result_area.text = f"Error: {error_msg}"
                return
            
            account = result if not isinstance(result, tuple) else result[0]
            formatted_output = self._format_account_info(account)
            result_area.text = formatted_output
            self.query_one("#get-by-alias-title", Label).update("✅ Account retrieved")
            
        except Exception as e:
            self.query_one("#get-by-alias-title", Label).update(f"❌ Error: {str(e)}")
            result_area.text = f"Error: {str(e)}"
    
    def _get_account_by_alias_sync(
        self,
        account_service: AccountService,
        alias: str,
        env_name: str,
        account_type: Optional[str]
    ) -> Optional[Dict]:
        """Synchronous wrapper for getting account by alias."""
        try:
            from returns.pipeline import is_successful
            
            # Get kaminoKey from alias
            mapping = account_service.alias_service.get_mapping_by_alias(alias)
            
            if not mapping:
                return (None, f"Alias '{alias}' not found in GitLab configuration")
            
            kamino_key = mapping.kamino_key
            result = account_service.data_manager.get_account_by_kamino_key(
                kamino_key,
                env_name,
                account_type
            )
            
            if is_successful(result):
                return result.unwrap()
            else:
                error = result.failure()
                return (None, error.message)
        except ValueError as e:
            return (None, str(e))
        except Exception as e:
            return (None, str(e))


class AccountQueryResultScreen(Screen):
    """Modal screen to display account query results with copy support."""
    
    BINDINGS = [
        Binding("escape", "back", "Back", priority=True),
        Binding("c", "copy_selected", "Copy Selected", show=True),
        Binding("a", "copy_all", "Copy All", show=True),
    ]
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def __init__(self, account: Dict, query_info: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = account
        self.query_info = query_info
    
    def _format_account_info(self, account: Dict) -> str:
        """Format account information for display with modal width."""
        # Use modal separator width and don't show N/A for missing fields
        return BaseResultScreen._format_account_info(self, account, separator_width=MODAL_SEPARATOR_WIDTH, use_na_for_missing=False)
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="account-result-modal-container"):
                yield Label(f"✅ Account Found: {self.query_info}", id="modal-title")
                yield TextArea(
                    "",
                    read_only=True,
                    show_line_numbers=False,
                    id="modal-result-area"
                )
            with Horizontal(id="modal-buttons"):
                yield Button("Copy Selected", id="copy-selected-btn", variant="success")
                yield Button("Copy All", id="copy-all-btn")
                yield Button("Back", id="back-btn", variant="primary")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen with account data."""
        result_area = self.query_one("#modal-result-area", TextArea)
        formatted_output = self._format_account_info(self.account)
        result_area.text = formatted_output
        result_area.show_line_numbers = False
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "copy-selected-btn":
            self.action_copy_selected()
        elif event.button.id == "copy-all-btn":
            self.action_copy_all()
        elif event.button.id == "back-btn":
            self.app.pop_screen()
    
    def _extract_field_value(self, field_name: str) -> str:
        """Extract a specific field value from account dict."""
        field_mapping = {
            'phone': ('mainNumber', 'phone'),
            'account_id': ('accountId', '_id'),
            'type': ('accountType',),
            'env': ('envName',),
            'email': ('companyEmailDomain',),
            'created': ('createdAt',),
            'login_times': ('loginTimes',),
        }
        
        field_name_lower = field_name.lower().replace(' ', '_')
        keys = field_mapping.get(field_name_lower, [])
        
        for key in keys:
            value = self.account.get(key)
            if value is not None:
                result = str(value)
                # Remove leading + for phone numbers
                if field_name_lower == 'phone' and result.startswith('+'):
                    result = result[1:]
                return result
        
        return ""
    
    def action_copy_selected(self) -> None:
        """Copy selected text or smart field extraction from TextArea to clipboard."""
        try:
            import pyperclip
            
            result_area = self.query_one("#modal-result-area", TextArea)
            text = result_area.text
            lines = text.split('\n') if text else []  # Initialize lines early for reuse
            
            # Try to get selected text using different methods
            selected_text = None
            
            # Method 1: Try selection.selected_text if available
            try:
                selection = result_area.selection
                if selection:
                    if hasattr(selection, 'selected_text') and selection.selected_text:
                        selected_text = selection.selected_text
                    elif hasattr(selection, 'start') and hasattr(selection, 'end'):
                        start, end = selection.start, selection.end
                        if start < end and text:
                            selected_text = text[start:end]
            except Exception:
                pass
            
            # Method 2: If no selection, try to extract value from line at cursor position
            if not selected_text or not selected_text.strip():
                # Try to get cursor position from selection start
                cursor_pos = None
                try:
                    selection = result_area.selection
                    if selection and hasattr(selection, 'start'):
                        start = selection.start
                        # Handle both int and tuple (line, column) formats
                        if isinstance(start, tuple) and len(start) >= 1:
                            # If it's a tuple, use the line number directly
                            cursor_line = start[0]
                            if 0 <= cursor_line < len(lines):
                                line = lines[cursor_line].strip()
                                # Try to extract just the value (after colon or emoji)
                                if ':' in line:
                                    parts = line.split(':')
                                    if len(parts) > 1:
                                        value = ':'.join(parts[1:]).strip()
                                        if value:
                                            selected_text = value
                                        else:
                                            selected_text = line
                                    else:
                                        selected_text = line
                                else:
                                    selected_text = line
                        elif isinstance(start, int):
                            cursor_pos = start
                except Exception:
                    pass
                
                # If we have a cursor position (int), calculate which line it's on
                if cursor_pos is not None and isinstance(cursor_pos, int) and cursor_pos >= 0:
                    # Count characters up to cursor position to find the line
                    char_count = 0
                    cursor_line = 0
                    for i, line in enumerate(lines):
                        line_len = len(line) + 1  # +1 for newline
                        if char_count + line_len > cursor_pos:
                            cursor_line = i
                            break
                        char_count += line_len
                    
                    if 0 <= cursor_line < len(lines):
                        line = lines[cursor_line].strip()
                        
                        # Try to extract just the value (after colon or emoji)
                        # Example: "📱 Phone: +13476901535" -> "+13476901535"
                        if ':' in line:
                            # Extract value after the last colon
                            parts = line.split(':')
                            if len(parts) > 1:
                                value = ':'.join(parts[1:]).strip()
                                if value:
                                    selected_text = value
                                else:
                                    selected_text = line
                            else:
                                selected_text = line
                        else:
                            selected_text = line
                
                # Method 3: If still no text, try smart field extraction based on line content
                if not selected_text or not selected_text.strip():
                    # Parse the displayed text to extract field values
                    for line in lines:
                        line_lower = line.lower()
                        if 'phone' in line_lower and ':' in line:
                            selected_text = self._extract_field_value('phone')
                            break
                        elif 'account id' in line_lower and ':' in line:
                            selected_text = self._extract_field_value('account_id')
                            break
                        elif 'type' in line_lower and ':' in line and 'account' not in line_lower:
                            selected_text = self._extract_field_value('type')
                            break
                
                # If still no text, ask user to select text manually
                if not selected_text or not selected_text.strip():
                    self.app.notify("⚠️  Please select text or use 'Copy All' (a)", severity="warning", timeout=WARNING_TIMEOUT)
                    return
            
            if not selected_text or not selected_text.strip():
                self.app.notify("⚠️  No text to copy. Select text or use 'Copy All' (a)", severity="warning", timeout=WARNING_TIMEOUT)
                return
            
            # Copy to clipboard
            text_to_copy = selected_text.strip()
            # Remove leading + for phone numbers
            if text_to_copy.startswith('+'):
                # Check if the copied text is from a Phone line
                # Reuse the lines variable that was already retrieved earlier
                for line in lines:
                    if ('phone' in line.lower() or '📱' in line) and text_to_copy in line:
                        text_to_copy = text_to_copy.lstrip('+')
                        break
            
            pyperclip.copy(text_to_copy)
            
            # Show notification with truncated value
            display_text = text_to_copy[:MAX_DISPLAY_TEXT_LENGTH] + "..." if len(text_to_copy) > MAX_DISPLAY_TEXT_LENGTH else text_to_copy
            self.app.notify(f"✅ Copied: {display_text}", timeout=NOTIFICATION_TIMEOUT)
                
        except ImportError:
            self.app.notify("❌ pyperclip not installed. Please install it: pip install pyperclip", severity="error", timeout=5)
        except Exception as e:
            import traceback
            error_msg = f"❌ Failed to copy: {str(e)}"
            self.app.notify(error_msg, severity="error", timeout=5)
            print(f"Copy error details: {traceback.format_exc()}")
    
    def action_copy_all(self) -> None:
        """Copy all account information to clipboard."""
        try:
            import pyperclip
            
            # Get the text from the TextArea
            result_area = self.query_one("#modal-result-area", TextArea)
            text_to_copy = result_area.text
            
            if not text_to_copy:
                # Fallback: format the account info again
                text_to_copy = self._format_account_info(self.account)
            
            # Remove + from phone numbers in the text
            lines = text_to_copy.split('\n')
            processed_lines = []
            for line in lines:
                if ('phone' in line.lower() or '📱' in line) and ':' in line:
                    # Extract and process phone number
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        label = parts[0]
                        value = parts[1].strip()
                        if value.startswith('+'):
                            value = value[1:]
                        processed_lines.append(f"{label}: {value}")
                    else:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
            text_to_copy = '\n'.join(processed_lines)
            
            # Copy to clipboard
            pyperclip.copy(text_to_copy)
            
            # Verify it was copied (optional check)
            copied_text = pyperclip.paste()
            if copied_text == text_to_copy:
                self.app.notify("✅ Account info copied to clipboard!", timeout=2)
            else:
                self.app.notify("⚠️  Copy may have failed - please try again", severity="warning", timeout=3)
                
        except ImportError:
            self.app.notify("❌ pyperclip not installed. Please install it: pip install pyperclip", severity="error", timeout=5)
        except Exception as e:
            import traceback
            error_msg = f"❌ Failed to copy: {str(e)}"
            self.app.notify(error_msg, severity="error", timeout=5)
            print(f"Copy error details: {traceback.format_exc()}")


class ListAliasesScreen(BaseScreen):
    """Screen for listing aliases."""
    
    BINDINGS = [
        Binding("escape", "back", "Back", priority=True),
        Binding("c", "copy_selected", "Copy", show=True),
        Binding("/", "focus_search", "Search", show=True),
        Binding("enter", "query_account", "Query", show=True),
        Binding("r", "query_account", "Query", show=True),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._all_mappings = []  # Store all mappings for filtering
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="list-aliases-container"):
                yield Label("🏷️  List Aliases", id="list-aliases-title")
                yield Input(placeholder="🔍 Search aliases (fuzzy match)...", id="search-input")
                yield DataTable(id="aliases-table", cursor_type="cell")
                with Horizontal(id="list-aliases-buttons"):
                    yield Button("Load Aliases", id="load-btn", variant="primary")
                    yield Button("Refresh", id="refresh-btn")
                    yield Button("Copy Cell", id="copy-btn")
                    yield Button("Query Account", id="query-account-btn", variant="success")
                    yield Button("Clear Search", id="clear-search-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the list aliases screen."""
        table = self.query_one("#aliases-table", DataTable)
        table.add_column("#", width=5)
        table.add_column("Alias", width=32)
        table.add_column("Brand", width=10)
        table.add_column("Kamino Key")  # No width specified - takes remaining space
        self.app.call_later(self._load_aliases, False)
    
    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "load-btn":
            await self._load_aliases(False)
        elif event.button.id == "refresh-btn":
            await self._load_aliases(True)
        elif event.button.id == "copy-btn":
            self.action_copy_selected()
        elif event.button.id == "query-account-btn":
            await self.action_query_account()
        elif event.button.id == "clear-search-btn":
            search_input = self.query_one("#search-input", Input)
            search_input.value = ""
            self._filter_aliases("")
        elif event.button.id == "back-btn":
            self.action_back()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self._filter_aliases(event.value)
    
    def action_copy_selected(self) -> None:
        """Copy selected cell to clipboard."""
        table = self.query_one("#aliases-table", DataTable)
        
        if table.row_count == 0:
            self.app.notify("No data to copy", severity="warning", timeout=2)
            return
        
        try:
            # Get cursor position (row, column)
            cursor_row = table.cursor_row
            cursor_col = table.cursor_column
            
            if cursor_row is None or cursor_col is None:
                self.app.notify("No cell selected", severity="warning", timeout=2)
                return
            
            # Get cell value
            cell_value = table.get_cell_at((cursor_row, cursor_col))
            copy_text = str(cell_value)
            
            # Copy to clipboard
            import pyperclip
            pyperclip.copy(copy_text)
            
            # Get column name for better notification
            columns = ["#", "Alias", "Brand", "Kamino Key"]
            col_name = columns[cursor_col] if cursor_col < len(columns) else "Cell"
            
            # Show notification with truncated preview
            preview = copy_text[:40] + "..." if len(copy_text) > 40 else copy_text
            self.app.notify(f"✅ Copied {col_name}: {preview}", timeout=2)
            
        except ImportError:
            self.app.notify("⚠️  pyperclip not installed. Install with: pip install pyperclip", 
                          severity="error", timeout=5)
        except Exception as e:
            self.app.notify(f"❌ Copy failed: {str(e)}", severity="error", timeout=3)
    
    async def action_query_account(self) -> None:
        """Query account using the selected row's alias or kamino key."""
        table = self.query_one("#aliases-table", DataTable)
        
        if table.row_count == 0:
            self.app.notify("No data available", severity="warning", timeout=2)
            return
        
        try:
            # Get cursor position
            cursor_row = table.cursor_row
            cursor_col = table.cursor_column
            
            if cursor_row is None or cursor_row < 0:
                self.app.notify("Please select a row first", severity="warning", timeout=2)
                return
            
            # Get the row data (columns: #, Alias, Brand, Kamino Key)
            alias = str(table.get_cell_at((cursor_row, 1)))
            kamino_key = str(table.get_cell_at((cursor_row, 3)))
            
            # Determine query method based on selected column
            # Column 1 = Alias, Column 3 = Kamino Key
            use_alias = (cursor_col == 1)
            
            if use_alias and alias:
                # Query by alias
                self.app.notify(f"🔍 Querying account by Alias: {alias}", timeout=2)
                query_param = ('alias', alias)
            elif kamino_key:
                # Query by kamino key (default)
                self.app.notify(f"🔍 Querying account by Kamino Key from: {alias}", timeout=2)
                query_param = ('kamino_key', kamino_key)
            else:
                self.app.notify("No valid query parameter found", severity="warning", timeout=2)
                return
            
            # Query account
            account_service = ServiceFactory.get_account_service()
            loop = asyncio.get_event_loop()
            
            result = await loop.run_in_executor(
                None,
                lambda: self._query_account_sync(account_service, query_param, alias)
            )
            
            if result is None or (isinstance(result, tuple) and result[0] is None):
                error_msg = result[1] if isinstance(result, tuple) else "Failed to query account"
                self.app.notify(f"❌ {error_msg}", severity="error", timeout=5)
                return
            
            # Create a result screen to display the account info
            account = result if not isinstance(result, tuple) else result[0]
            self._show_account_result_popup(account, alias, query_param[1])
            
        except Exception as e:
            self.app.notify(f"❌ Query failed: {str(e)}", severity="error", timeout=3)
    
    def _query_account_sync(self, account_service: AccountService, query_param: tuple, display_name: str):
        """Synchronous wrapper for querying account by alias or kamino key.
        
        Args:
            account_service: Service instance
            query_param: Tuple of (query_type, query_value) where query_type is 'alias' or 'kamino_key'
            display_name: Name to display in messages
        """
        try:
            from returns.pipeline import is_successful
            
            query_type, query_value = query_param
            
            if query_type == 'alias':
                # Query by alias - use the alias service to get kamino key first
                mapping = account_service.alias_service.get_mapping_by_alias(query_value)
                if not mapping:
                    return (None, f"Alias '{query_value}' not found")
                
                # Use the kamino key from the mapping
                result = account_service.data_manager.get_account_by_kamino_key(
                    kamino_key=mapping.kamino_key,
                    env_name=AccountService.DEFAULT_ENV_NAME
                )
            else:
                # Query by kamino key directly
                result = account_service.data_manager.get_account_by_kamino_key(
                    kamino_key=query_value,
                    env_name=AccountService.DEFAULT_ENV_NAME
                )
            
            # Don't use handler in TUI - it calls typer.Exit() which crashes the TUI!
            # Instead, manually unwrap the Result
            if is_successful(result):
                account = result.unwrap()
                return account
            else:
                # Get error from Failure
                error = result.failure()
                return (None, str(error))
            
        except Exception as e:
            return (None, str(e))
    
    def _show_account_result_popup(self, account: Dict, alias: str, kamino_key: str) -> None:
        """Show account result in a modal screen."""
        if not account:
            self.app.notify("❌ No account found", severity="warning", timeout=3)
            return
        
        try:
            # Create the result screen
            result_screen = AccountQueryResultScreen(account, alias)
            
            # Push the screen - AccountPoolTUIApp.push_screen now supports Screen instances
            self.app.push_screen(result_screen)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.app.notify(f"❌ Failed to show result: {str(e)}", severity="error", timeout=5)
            print(f"Error details: {error_details}")
    
    async def _load_aliases(self, force_refresh: bool = False) -> None:
        """Load aliases from GitLab."""
        table = self.query_one("#aliases-table", DataTable)
        table.clear()
        
        title = "🏷️  Refreshing..." if force_refresh else "🏷️  Loading..."
        self.query_one("#list-aliases-title", Label).update(title)
        
        try:
            account_service = ServiceFactory.get_account_service()
            
            loop = asyncio.get_event_loop()
            mappings = await loop.run_in_executor(
                None,
                lambda: self._load_aliases_sync(account_service, force_refresh)
            )
            
            if mappings is None or (isinstance(mappings, tuple) and mappings[0] is None):
                error_msg = mappings[1] if isinstance(mappings, tuple) else "Failed to load aliases"
                self.query_one("#list-aliases-title", Label).update(f"❌ {error_msg}")
                return
            
            # Store all mappings for filtering
            self._all_mappings = mappings
            
            # Add results to table
            for i, mapping in enumerate(mappings, 1):
                table.add_row(
                    str(i),
                    mapping.alias,
                    mapping.brand,
                    mapping.kamino_key,
                    key=str(i)
                )
            
            title_text = f"🏷️  {len(mappings)} Alias(es) Found"
            if force_refresh:
                title_text += " (Refreshed)"
            self.query_one("#list-aliases-title", Label).update(title_text)
            
        except Exception as e:
            self.query_one("#list-aliases-title", Label).update(f"❌ Error: {str(e)}")
    
    def _filter_aliases(self, search_term: str) -> None:
        """Filter aliases based on search term (fuzzy match)."""
        table = self.query_one("#aliases-table", DataTable)
        table.clear()
        
        if not self._all_mappings:
            return
        
        search_term = search_term.lower().strip()
        
        # If no search term, show all
        if not search_term:
            filtered = self._all_mappings
        else:
            # Fuzzy match: search in alias, brand, and kamino_key
            filtered = []
            for mapping in self._all_mappings:
                # Check if search term appears in any field (case-insensitive)
                if (search_term in mapping.alias.lower() or
                    search_term in mapping.brand.lower() or
                    search_term in mapping.kamino_key.lower()):
                    filtered.append(mapping)
        
        # Add filtered results to table
        for i, mapping in enumerate(filtered, 1):
            table.add_row(
                str(i),
                mapping.alias,
                mapping.brand,
                mapping.kamino_key,
                key=str(i)
            )
        
        # Update title
        if search_term:
            title_text = f"🔍 {len(filtered)} / {len(self._all_mappings)} Alias(es) (filtered)"
        else:
            title_text = f"🏷️  {len(filtered)} Alias(es) Found"
        self.query_one("#list-aliases-title", Label).update(title_text)
    
    def _load_aliases_sync(self, account_service: AccountService, force_refresh: bool) -> Optional[List]:
        """Synchronous wrapper for loading aliases."""
        try:
            mappings = account_service.alias_service.get_mappings(force_refresh)
            return list(mappings.values())
        except ValueError as e:
            return (None, str(e))
        except Exception as e:
            return (None, str(e))


class GetAliasInfoScreen(BaseResultScreen):
    """Screen for getting alias information."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="get-alias-info-container"):
                yield Label("🏷️  Get Alias Info", id="get-alias-info-title")
                yield Input(placeholder="Alias name", id="alias-input")
                yield TextArea(id="result-area", read_only=True)
                with Horizontal(id="get-alias-info-buttons"):
                    yield Button("Get Info", id="get-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the get alias info screen."""
        super().on_mount()
        self.query_one("#alias-input", Input).focus()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "get-btn":
            await self._get_alias_info()
        elif event.button.id == "clear-btn":
            self.query_one("#alias-input", Input).value = ""
            self.query_one("#result-area", TextArea).text = ""
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "alias-input":
            await self._get_alias_info()
    
    async def _get_alias_info(self) -> None:
        """Get alias information."""
        alias = self.query_one("#alias-input", Input).value.strip()
        
        if not alias:
            self.query_one("#get-alias-info-title", Label).update(
                "⚠️  Please enter Alias name"
            )
            return
        
        result_area = self.query_one("#result-area", TextArea)
        self.query_one("#get-alias-info-title", Label).update("🏷️  Loading...")
        result_area.text = ""
        
        try:
            account_service = ServiceFactory.get_account_service()
            
            loop = asyncio.get_event_loop()
            mapping = await loop.run_in_executor(
                None,
                lambda: self._get_alias_info_sync(account_service, alias)
            )
            
            if mapping is None or (isinstance(mapping, tuple) and mapping[0] is None):
                error_msg = mapping[1] if isinstance(mapping, tuple) else "Alias not found"
                self.query_one("#get-alias-info-title", Label).update(f"❌ {error_msg}")
                result_area.text = f"Error: {error_msg}"
                return
            
            formatted_output = self._format_alias_info(mapping)
            result_area.text = formatted_output
            self.query_one("#get-alias-info-title", Label).update("✅ Alias information retrieved")
            
        except Exception as e:
            self.query_one("#get-alias-info-title", Label).update(f"❌ Error: {str(e)}")
            result_area.text = f"Error: {str(e)}"
    
    def _get_alias_info_sync(self, account_service: AccountService, alias: str):
        """Synchronous wrapper for getting alias info."""
        try:
            mapping = account_service.alias_service.get_mapping_by_alias(alias)
            if not mapping:
                return (None, f"Alias '{alias}' not found")
            return mapping
        except Exception as e:
            return (None, str(e))
    
    def _format_alias_info(self, mapping) -> str:
        """Format alias information for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("Alias Information")
        lines.append("=" * 60)
        lines.append(f"🏷️  Alias: {mapping.alias}")
        lines.append(f"🏢 Brand: {mapping.brand}")
        lines.append(f"🔑 Kamino Key: {mapping.kamino_key}")
        lines.append("=" * 60)
        lines.append("")
        lines.append("💡 Use 'Get Account by Alias' to query account information")
        lines.append("=" * 60)
        return "\n".join(lines)


class MainMenuScreen(BaseScreen):
    """Main menu screen."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("escape", "quit", "Quit", priority=True),
        Binding("up", "move_up", "Move Up", priority=True),
        Binding("down", "move_down", "Move Down", priority=True),
        Binding("enter", "select", "Select", priority=True),
    ]
    
    button_ids = [
        "get-random-btn",
        "get-by-id-btn",
        "get-by-phone-btn",
        "get-by-alias-btn",
        "list-aliases-btn",
        "alias-info-btn",
        "list-types-btn",
        "cache-btn",
        "exit-btn",
    ]
    selected_index = 0
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Container(id="menu-container"):
                yield Label("🏦 Account Pool Management", id="menu-title")
                with Vertical(id="menu-buttons"):
                    yield Button("🎲 Get Random Account", id="get-random-btn", variant="primary")
                    yield Button("🆔 Get Account by ID", id="get-by-id-btn")
                    yield Button("📱 Get Account by Phone", id="get-by-phone-btn")
                    yield Button("🏷️  Get Account by Alias", id="get-by-alias-btn")
                    yield Button("📋 List Aliases", id="list-aliases-btn")
                    yield Button("ℹ️  Alias Info", id="alias-info-btn")
                    yield Button("🏦 List Account Types", id="list-types-btn")
                    yield Button("💾 Cache Management", id="cache-btn")
                    yield Button("❌ Exit", id="exit-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize menu with first button focused."""
        self._update_selection()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def on_key(self, event: events.Key) -> None:
        """Handle key events explicitly."""
        if event.key == "escape":
            self.app.exit()
            event.prevent_default()
        # Let other keys be handled by default processing
    
    def action_move_up(self) -> None:
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._update_selection()
    
    def action_move_down(self) -> None:
        """Move selection down."""
        if self.selected_index < len(self.button_ids) - 1:
            self.selected_index += 1
            self._update_selection()
    
    def action_select(self) -> None:
        """Select the current menu item."""
        button_id = self.button_ids[self.selected_index]
        button = self.query_one(f"#{button_id}", Button)
        button.press()
    
    def _update_selection(self) -> None:
        """Update button selection state."""
        for i, button_id in enumerate(self.button_ids):
            button = self.query_one(f"#{button_id}", Button)
            if i == self.selected_index:
                button.variant = "primary"
                button.focus()
            else:
                button.variant = "default"
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "get-random-btn":
            self.app.push_screen("get_random")
        elif event.button.id == "get-by-id-btn":
            self.app.push_screen("get_by_id")
        elif event.button.id == "get-by-phone-btn":
            self.app.push_screen("get_by_phone")
        elif event.button.id == "get-by-alias-btn":
            self.app.push_screen("get_by_alias")
        elif event.button.id == "list-aliases-btn":
            self.app.push_screen("list_aliases")
        elif event.button.id == "alias-info-btn":
            self.app.push_screen("alias_info")
        elif event.button.id == "list-types-btn":
            self.app.push_screen("list_types")
        elif event.button.id == "cache-btn":
            self.app.push_screen("cache")
        elif event.button.id == "exit-btn":
            self.app.exit()


class AccountPoolTUIApp(App):
    """Main TUI application for Account Pool management."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #menu-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    #menu-title {
        text-align: center;
        width: 100%;
        margin: 1;
    }
    
    #menu-buttons {
        width: 100%;
        height: auto;
    }
    
    #menu-buttons > Button {
        width: 100%;
        margin: 1;
    }
    
    #get-random-container, #get-by-id-container, #get-by-phone-container,
    #get-by-alias-container, #list-aliases-container, #get-alias-info-container,
    #list-types-container, #cache-container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    #account-result-modal-container {
        width: 120;
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    #get-random-title, #get-by-id-title, #get-by-phone-title,
    #get-by-alias-title, #list-aliases-title, #get-alias-info-title,
    #list-types-title, #cache-title, #modal-title {
        text-align: center;
        width: 100%;
        margin: 1;
    }
    
    #get-random-tip {
        text-align: center;
        width: 100%;
        color: $text-muted;
        text-style: italic;
    }
    
    #types-table, #aliases-table {
        height: 20;
        width: 100%;
    }
    
    #result-area, #cache-info-area {
        height: 10;
        width: 100%;
    }
    
    #modal-result-area {
        height: 25;
        width: 100%;
    }
    
    #account-type-input, #account-id-input, #phone-input, #alias-input,
    #env-input, #brand-input, #filter-input, #type-input {
        width: 100%;
        margin: 1;
    }
    
    #get-random-buttons, #get-by-id-buttons, #get-by-phone-buttons,
    #get-by-alias-buttons, #list-aliases-buttons, #get-alias-info-buttons,
    #list-types-buttons, #cache-buttons, #modal-buttons {
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    
    #get-random-buttons > Button, #get-by-id-buttons > Button,
    #get-by-phone-buttons > Button, #get-by-alias-buttons > Button,
    #list-aliases-buttons > Button, #get-alias-info-buttons > Button,
    #list-types-buttons > Button, #cache-buttons > Button, #modal-buttons > Button {
        margin: 1;
    }
    """
    
    TITLE = "Account Pool Management TUI"
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]
    
    def on_mount(self) -> None:
        """Set up the initial screen."""
        self.push_screen("main")
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
    
    def push_screen(self, screen_name_or_instance) -> None:
        """Push a screen by name or Screen instance."""
        # If it's already a Screen instance, push it directly
        from textual.screen import Screen as TextualScreen
        if isinstance(screen_name_or_instance, TextualScreen):
            super().push_screen(screen_name_or_instance)
            return
        
        # Otherwise, treat it as a string name and look it up
        screens = {
            "main": MainMenuScreen(),
            "get_random": GetRandomAccountScreen(),
            "get_by_id": GetAccountByIdScreen(),
            "get_by_phone": GetAccountByPhoneScreen(),
            "get_by_alias": GetAccountByAliasScreen(),
            "list_aliases": ListAliasesScreen(),
            "alias_info": GetAliasInfoScreen(),
            "list_types": ListAccountTypesScreen(),
            "cache": CacheManagementScreen(),
        }
        
        if screen_name_or_instance in screens:
            super().push_screen(screens[screen_name_or_instance])


def run_tui():
    """Run the TUI application."""
    try:
        app = AccountPoolTUIApp()
        app.run()
    except Exception as e:
        import sys
        print(f"Error running TUI: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    run_tui()

