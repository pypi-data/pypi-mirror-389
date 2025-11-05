"""Ultra-simplified OAuth2 flow."""

import asyncio
import webbrowser
from typing import Optional
from urllib.parse import urlparse

from aiohttp import web
from rich.console import Console

from simulator.auth.oauth2_client import OAuth2Client


class OAuthFlow:
    """Ultra-simple OAuth2 flow - just browser + callback."""

    def __init__(self, oauth_client: OAuth2Client, console: Console):
        self.oauth_client = oauth_client
        self.console = console
        self._code: Optional[str] = None
        self._runner: Optional[web.AppRunner] = None

    async def authenticate(self) -> bool:
        """Authenticate user via OAuth2."""
        self.console.print("\n[bold blue]🔐 Authentication[/bold blue]")

        # Try existing tokens
        if self.oauth_client.ensure_valid_access_token():
            self.console.print("[green]✅ Already authenticated[/green]")
            return True

        # New authentication
        self.console.print("[yellow]⏳ Opening browser...[/yellow]")

        try:
            # Start server & open browser
            await self._start_server()
            auth_url = self.oauth_client.get_authorization_url()
            webbrowser.open(auth_url)

            # Wait for callback
            if await self._wait_for_code():
                if self._code is not None:
                    self.oauth_client.exchange_code_for_tokens(self._code)
                    self.console.print("[green]✅ Authentication successful![/green]")
                    return True
                else:
                    self.console.print(
                        "[red]❌ Authentication failed: No code received[/red]"
                    )
                    return False
            else:
                self.console.print("[red]❌ Authentication timed out[/red]")
                return False

        except Exception as e:
            self.console.print(f"[red]❌ Error: {e}[/red]")
            return False
        finally:
            await self._stop_server()

    async def _start_server(self) -> None:
        """Start callback server."""
        port = urlparse(self.oauth_client.redirect_uri).port or 3000
        app = web.Application()
        app.router.add_get("/callback", self._callback)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        await web.TCPSite(self._runner, "localhost", port).start()

    async def _callback(self, request: web.Request) -> web.Response:
        """Handle OAuth callback."""
        self._code = request.query.get("code")
        return web.Response(
            text='<h2 class="success">✅ Authentication Successful!</h2> <div class="info">You can close this window and return to the simulator.</div>',
            content_type="text/html",
        )

    async def _wait_for_code(self, timeout: int = 300) -> bool:
        """Wait for auth code."""
        for _ in range(timeout):
            if self._code:
                return True
            await asyncio.sleep(1)
        return False

    async def _stop_server(self) -> None:
        """Stop server."""
        if self._runner:
            await self._runner.cleanup()
