# -*- coding: utf-8 -*-

"""Screen for getting SP value."""

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, TextArea
from ...tui_common import BaseResultScreen
from ..service import sp_service
from ..display_manager import SPDisplayManager


class SPGetValueScreen(BaseResultScreen):
    """Screen for getting SP value."""
    
    def compose(self):
        yield Header()
        with Vertical():
            with Container(id="get-container"):
                yield Label("📊 Get Service Parameter Value", id="get-title")
                yield Input(placeholder="SP ID (e.g., SP-123)", id="sp-id-input")
                yield Input(placeholder="Account ID (e.g., 8023391076)", id="account-id-input")
                yield TextArea(id="result-area", read_only=True)
                with Horizontal(id="get-buttons"):
                    yield Button("Get Value", id="get-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                    yield Button("Back", id="back-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the get value screen."""
        super().on_mount()
        self.query_one("#sp-id-input", Input).focus()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "get-btn":
            await self._get_sp_value()
        elif event.button.id == "clear-btn":
            self.query_one("#sp-id-input", Input).value = ""
            self.query_one("#account-id-input", Input).value = ""
            self.query_one("#result-area", TextArea).text = ""
        elif event.button.id == "back-btn":
            self.action_back()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "account-id-input":
            await self._get_sp_value()
        elif event.input.id == "sp-id-input":
            self.query_one("#account-id-input", Input).focus()
    
    async def _get_sp_value(self) -> None:
        """Get SP value for account."""
        sp_id = self.query_one("#sp-id-input", Input).value.strip()
        account_id = self.query_one("#account-id-input", Input).value.strip()
        
        if not sp_id or not account_id:
            self.query_one("#get-title", Label).update(
                "⚠️  Please enter both SP ID and Account ID"
            )
            return
        
        result_area = self.query_one("#result-area", TextArea)
        self.query_one("#get-title", Label).update("📊 Loading...")
        result_area.text = ""
        
        try:
            result = await sp_service.get_service_parameter_value(sp_id, account_id)
            
            if not result.success:
                self.query_one("#get-title", Label).update(
                    f"❌ Error: {result.error_message}"
                )
                result_area.text = f"Error: {result.error_message}"
                return
            
            sp_data = result.data
            formatted_output = SPDisplayManager.format_sp_value(sp_data)
            
            result_area.text = formatted_output
            self.query_one("#get-title", Label).update(
                f"✅ SP {sp_id} value retrieved"
            )
            
        except Exception as e:
            self.query_one("#get-title", Label).update(
                f"❌ Error: {str(e)}"
            )
            result_area.text = f"Error: {str(e)}"

