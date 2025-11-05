"""Main CLI interface for Laurelin."""
import click
import sys
from typing import Optional
from .auth import AuthManager
from .api_client import APIClient


# Color scheme for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def success(message: str) -> None:
    """Print success message."""
    click.echo(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def error(message: str) -> None:
    """Print error message."""
    click.echo(f"{Colors.RED}❌ {message}{Colors.RESET}", err=True)


def warning(message: str) -> None:
    """Print warning message."""
    click.echo(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def info(message: str) -> None:
    """Print info message."""
    click.echo(f"{Colors.CYAN}{message}{Colors.RESET}")


@click.group()
@click.version_option(version='1.0.0', prog_name='laurelin')
def cli():
    """
    Laurelin CLI - Terminal interface for Laurelin nuclear fusion chat platform.

    Get started with: laurelin login
    """
    pass


@cli.command()
@click.option('--production', is_flag=True, help='Use production API endpoint')
@click.option('--dev', is_flag=True, help='Use development API endpoint (localhost:8080)')
def login(production: bool, dev: bool):
    """
    Authenticate with your CLI tokens.

    Get your tokens from: https://chat.laurelin-inc.com/api-access
    """
    auth_manager = AuthManager()

    # Set API mode
    if production:
        auth_manager.set_production_mode(True)
        info("Using production API endpoint")
    elif dev:
        auth_manager.set_production_mode(False)
        info("Using development API endpoint (localhost:8080)")

    click.echo(f"\n{Colors.BOLD}Laurelin CLI Login{Colors.RESET}")
    click.echo("=" * 50)

    # Check if already logged in
    if auth_manager.is_authenticated():
        if not click.confirm("\nYou are already logged in. Do you want to log in again?"):
            return

    click.echo("\n📍 Get your CLI tokens from:")
    click.echo(f"   {Colors.CYAN}https://chat.laurelin-inc.com/api-access{Colors.RESET}\n")

    # Prompt for tokens
    access_token = click.prompt("Access Token", hide_input=True)
    refresh_token = click.prompt("Refresh Token", hide_input=True)

    if not access_token or not refresh_token:
        error("Both access token and refresh token are required")
        sys.exit(1)

    # Save tokens
    try:
        auth_manager.save_tokens(access_token, refresh_token)

        # Test the connection
        api_client = APIClient(auth_manager)
        if api_client.test_connection():
            success("Authentication successful!")
            info(f"Tokens saved to: {auth_manager.credentials_file}")
        else:
            warning("Tokens saved, but could not verify connection to API")
            info("This might be expected if using development mode without backend running")
    except Exception as e:
        error(f"Login failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('message', required=False)
@click.option('--session', '-s', help='Session ID to continue conversation')
@click.option('--interactive', '-i', is_flag=True, help='Start interactive chat mode')
def chat(message: Optional[str], session: Optional[str], interactive: bool):
    """
    Send a message to Laurelin AI.

    Examples:
      laurelin chat "What is the plasma density?"
      laurelin chat --interactive
      laurelin chat -s abc123 "Follow-up question"
    """
    auth_manager = AuthManager()

    # Check authentication
    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    # Interactive mode
    if interactive:
        click.echo(f"\n{Colors.BOLD}Laurelin Interactive Chat{Colors.RESET}")
        click.echo("=" * 50)
        click.echo("Type 'exit' or 'quit' to end the session\n")

        current_session_id = session

        while True:
            try:
                user_message = click.prompt(f"{Colors.GREEN}You{Colors.RESET}", prompt_suffix="> ")

                if user_message.lower() in ['exit', 'quit', 'q']:
                    info("Goodbye!")
                    break

                if not user_message.strip():
                    continue

                # Send message
                try:
                    with click.progressbar(length=100, label='Thinking...',
                                          fill_char='█', empty_char='░') as bar:
                        response = api_client.send_message(user_message, current_session_id)
                        bar.update(100)

                    if response.get('success'):
                        ai_response = response.get('response', '')
                        model_used = response.get('model_used', 'unknown')

                        click.echo(f"\n{Colors.CYAN}Laurelin ({model_used}){Colors.RESET}: {ai_response}\n")

                        # Update session ID for continuation
                        if not current_session_id:
                            current_session_id = response.get('session', {}).get('session_id')
                    else:
                        error(f"Failed to get response: {response.get('message', 'Unknown error')}")

                except Exception as e:
                    error(f"Error: {str(e)}")

            except (KeyboardInterrupt, EOFError):
                info("\nGoodbye!")
                break

        return

    # Single message mode
    if not message:
        error("Please provide a message or use --interactive mode")
        click.echo("Example: laurelin chat \"What is the plasma density?\"")
        sys.exit(1)

    try:
        click.echo(f"\n{Colors.GREEN}You{Colors.RESET}: {message}\n")

        with click.progressbar(length=100, label='Thinking...',
                              fill_char='█', empty_char='░') as bar:
            response = api_client.send_message(message, session)
            bar.update(100)

        if response.get('success'):
            ai_response = response.get('response', '')
            model_used = response.get('model_used', 'unknown')

            click.echo(f"\n{Colors.CYAN}Laurelin ({model_used}){Colors.RESET}: {ai_response}\n")
        else:
            error(f"Failed to get response: {response.get('message', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
def logout():
    """Clear authentication tokens and log out."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        warning("You are not logged in")
        return

    if click.confirm("Are you sure you want to log out?"):
        auth_manager.clear_tokens()
        success("Logged out successfully")


@cli.command()
def status():
    """Show authentication and configuration status."""
    auth_manager = AuthManager()

    click.echo(f"\n{Colors.BOLD}Laurelin CLI Status{Colors.RESET}")
    click.echo("=" * 50)

    # Authentication status
    if auth_manager.is_authenticated():
        click.echo(f"Authentication: {Colors.GREEN}✅ Logged in{Colors.RESET}")
        click.echo(f"Credentials: {auth_manager.credentials_file}")
    else:
        click.echo(f"Authentication: {Colors.RED}❌ Not logged in{Colors.RESET}")
        click.echo(f"\nRun '{Colors.CYAN}laurelin login{Colors.RESET}' to get started")

    # Configuration
    config = auth_manager.load_config()
    api_url = auth_manager.get_api_url()

    click.echo(f"\nAPI Endpoint: {Colors.CYAN}{api_url}{Colors.RESET}")
    click.echo(f"Production Mode: {config.get('use_production', False)}")

    # Test connection
    if auth_manager.is_authenticated():
        api_client = APIClient(auth_manager)
        click.echo(f"\nConnection Test: ", nl=False)
        if api_client.test_connection():
            click.echo(f"{Colors.GREEN}✅ Connected{Colors.RESET}")
        else:
            click.echo(f"{Colors.YELLOW}⚠️  Cannot connect to API{Colors.RESET}")

    click.echo()


@cli.command()
def sessions():
    """List your recent chat sessions."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    try:
        api_client = APIClient(auth_manager)
        session_list = api_client.list_sessions()

        if not session_list:
            info("No chat sessions found")
            return

        click.echo(f"\n{Colors.BOLD}Your Chat Sessions{Colors.RESET}")
        click.echo("=" * 70)

        for sess in session_list[:10]:  # Show last 10
            session_id = sess.get('session_id', '')[:8]
            title = sess.get('title', 'Untitled')
            created = sess.get('created_at', '')[:10]

            click.echo(f"\n{Colors.CYAN}[{session_id}]{Colors.RESET} {title}")
            click.echo(f"  Created: {created}")

        click.echo()

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
def tokens():
    """List your active CLI tokens."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    try:
        api_client = APIClient(auth_manager)
        token_list = api_client.list_cli_tokens()

        if not token_list:
            info("No active CLI tokens found")
            return

        click.echo(f"\n{Colors.BOLD}Active CLI Tokens{Colors.RESET}")
        click.echo("=" * 70)

        for token in token_list:
            token_id = token.get('token_id', '')[:12]
            name = token.get('token_name', 'Unnamed')
            created = token.get('created_at', '')[:10]
            last_used = token.get('last_used_at', 'Never')
            if last_used != 'Never':
                last_used = last_used[:10]

            click.echo(f"\n{Colors.GREEN}●{Colors.RESET} {name}")
            click.echo(f"  ID: {token_id}...")
            click.echo(f"  Created: {created}")
            click.echo(f"  Last used: {last_used}")

        click.echo()

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
