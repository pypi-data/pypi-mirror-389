"""Main CLI interface for Laurelin."""
import click
import sys
import json
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
@click.version_option(version='1.1.0', prog_name='laurelin')
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


# =============================================================================
# NIMROD SIMULATION COMMANDS
# =============================================================================

@cli.group()
def nimrod():
    """
    NIMROD magnetohydrodynamics simulation management.

    Manage NIMROD simulations, run analysis, and visualize results.
    """
    pass


@nimrod.command(name='create')
@click.option('--type', 'sim_type',
              type=click.Choice(['tokamak_disruption', 'tearing_mode', 'elm_stability', 'rwm_stability', 'resistive_mhd']),
              help='Simulation type')
@click.option('--nstep', type=int, help='Number of timesteps')
@click.option('--nr', type=int, help='Radial grid points')
@click.option('--nz', type=int, help='Vertical grid points')
@click.option('--nphi', type=int, help='Toroidal grid points')
@click.option('--beta', type=float, help='Plasma beta')
@click.option('--resistivity', type=float, help='Plasma resistivity')
def nimrod_create(sim_type, nstep, nr, nz, nphi, beta, resistivity):
    """Create a new NIMROD simulation."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    click.echo(f"\n{Colors.BOLD}Create NIMROD Simulation{Colors.RESET}")
    click.echo("=" * 70)

    # Interactive prompts if options not provided
    if not sim_type:
        click.echo("\nSimulation Types:")
        click.echo("  1. tokamak_disruption - Tokamak disruption analysis")
        click.echo("  2. tearing_mode - Tearing mode instability")
        click.echo("  3. elm_stability - Edge Localized Mode stability")
        click.echo("  4. rwm_stability - Resistive Wall Mode stability")
        click.echo("  5. resistive_mhd - General resistive MHD")

        choice = click.prompt("\nSelect simulation type", type=click.IntRange(1, 5), default=5)
        types = ['tokamak_disruption', 'tearing_mode', 'elm_stability', 'rwm_stability', 'resistive_mhd']
        sim_type = types[choice - 1]

    if not nstep:
        nstep = click.prompt("Number of timesteps", type=int, default=1000)

    if not nr or not nz or not nphi:
        click.echo("\nGrid Configuration:")
        if not nr:
            nr = click.prompt("  Radial points (nr)", type=int, default=64)
        if not nz:
            nz = click.prompt("  Vertical points (nz)", type=int, default=128)
        if not nphi:
            nphi = click.prompt("  Toroidal points (nphi)", type=int, default=16)

    if beta is None:
        beta = click.prompt("Plasma beta", type=float, default=0.01)

    if resistivity is None:
        resistivity = click.prompt("Plasma resistivity", type=float, default=1e-7)

    # Build parameters
    params = {
        'simulation_type': sim_type,
        'nstep': nstep,
        'grid_size': {'nr': nr, 'nz': nz, 'nphi': nphi},
        'beta': beta,
        'resistivity': resistivity
    }

    click.echo(f"\n{Colors.YELLOW}Creating simulation...{Colors.RESET}")

    try:
        result = api_client.create_nimrod_simulation(params)

        if result.get('success'):
            sim = result.get('data', {})
            success("Simulation created successfully!")
            click.echo(f"\n{Colors.BOLD}Simulation Details:{Colors.RESET}")
            click.echo(f"  ID: {Colors.CYAN}{sim.get('id')}{Colors.RESET}")
            click.echo(f"  Type: {sim.get('params', {}).get('simulation_type')}")
            click.echo(f"  Status: {sim.get('status')}")
            click.echo(f"\nUse '{Colors.CYAN}laurelin nimrod status {sim.get('id')}{Colors.RESET}' to check progress")
        else:
            error(f"Failed to create simulation: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='list')
@click.option('--limit', type=int, help='Maximum number of simulations to show')
@click.option('--status', type=click.Choice(['pending', 'running', 'completed', 'failed', 'cancelled']),
              help='Filter by status')
def nimrod_list(limit, status):
    """List your NIMROD simulations."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    try:
        simulations = api_client.list_nimrod_simulations(limit=limit, status=status)

        if not simulations:
            info("No NIMROD simulations found")
            return

        click.echo(f"\n{Colors.BOLD}Your NIMROD Simulations{Colors.RESET}")
        click.echo("=" * 90)

        for sim in simulations:
            sim_id = sim.get('id', '')[-12:]
            sim_type = sim.get('params', {}).get('simulation_type', 'unknown')
            sim_status = sim.get('status', 'unknown')
            created = sim.get('created_at', '')[:19]

            # Color code status
            if sim_status == 'completed':
                status_display = f"{Colors.GREEN}✓ {sim_status}{Colors.RESET}"
            elif sim_status == 'running':
                status_display = f"{Colors.CYAN}⟳ {sim_status}{Colors.RESET}"
            elif sim_status == 'failed':
                status_display = f"{Colors.RED}✗ {sim_status}{Colors.RESET}"
            else:
                status_display = f"{Colors.YELLOW}◦ {sim_status}{Colors.RESET}"

            click.echo(f"\n{Colors.CYAN}[...{sim_id}]{Colors.RESET} {sim_type}")
            click.echo(f"  Status: {status_display}")
            click.echo(f"  Created: {created}")

        click.echo()

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='status')
@click.argument('simulation_id')
@click.option('--watch', is_flag=True, help='Watch status updates in real-time')
def nimrod_status(simulation_id, watch):
    """Get detailed status of a NIMROD simulation."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    if watch:
        import time
        click.echo(f"{Colors.YELLOW}Watching simulation status (Ctrl+C to stop)...{Colors.RESET}\n")

        try:
            while True:
                result = api_client.get_nimrod_status(simulation_id)

                if result.get('success'):
                    sim = result.get('data', {})

                    # Clear screen
                    click.clear()

                    click.echo(f"{Colors.BOLD}NIMROD Simulation Status{Colors.RESET}")
                    click.echo("=" * 70)
                    click.echo(f"ID: {sim.get('id')}")
                    click.echo(f"Status: {sim.get('status')}")
                    click.echo(f"Type: {sim.get('params', {}).get('simulation_type')}")
                    click.echo(f"Created: {sim.get('created_at', '')[:19]}")

                    if sim.get('status') in ['completed', 'failed', 'cancelled']:
                        break

                time.sleep(5)

        except KeyboardInterrupt:
            info("\nStopped watching")
            return

    else:
        try:
            result = api_client.get_nimrod_status(simulation_id)

            if result.get('success'):
                sim = result.get('data', {})

                click.echo(f"\n{Colors.BOLD}NIMROD Simulation Status{Colors.RESET}")
                click.echo("=" * 70)
                click.echo(f"ID: {Colors.CYAN}{sim.get('id')}{Colors.RESET}")
                click.echo(f"Status: {sim.get('status')}")
                click.echo(f"Type: {sim.get('params', {}).get('simulation_type')}")
                click.echo(f"Created: {sim.get('created_at', '')[:19]}")

                params = sim.get('params', {})
                click.echo(f"\n{Colors.BOLD}Parameters:{Colors.RESET}")
                click.echo(f"  Timesteps: {params.get('nstep')}")
                grid = params.get('grid_size', {})
                click.echo(f"  Grid: {grid.get('nr')}×{grid.get('nz')}×{grid.get('nphi')}")
                click.echo(f"  Beta: {params.get('beta')}")
                click.echo(f"  Resistivity: {params.get('resistivity')}")

                click.echo()
            else:
                error(f"Failed to get status: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            error(f"Error: {str(e)}")
            sys.exit(1)


@nimrod.command(name='cancel')
@click.argument('simulation_id')
@click.option('--force', is_flag=True, help='Skip confirmation')
def nimrod_cancel(simulation_id, force):
    """Cancel a running NIMROD simulation."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    if not force:
        if not click.confirm(f"Are you sure you want to cancel simulation {simulation_id}?"):
            info("Cancelled")
            return

    api_client = APIClient(auth_manager)

    try:
        result = api_client.cancel_nimrod_simulation(simulation_id)

        if result.get('success'):
            success("Simulation cancelled successfully")
        else:
            error(f"Failed to cancel: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='results')
@click.argument('simulation_id')
@click.option('--download', is_flag=True, help='Download all result files')
@click.option('--output', '-o', help='Output directory for downloads')
def nimrod_results(simulation_id, download, output):
    """Get results from a completed NIMROD simulation."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    try:
        result = api_client.get_nimrod_results(simulation_id)

        if result.get('success'):
            data = result.get('data', {})
            files = data.get('files', [])

            if not files:
                info("No result files available yet")
                return

            click.echo(f"\n{Colors.BOLD}NIMROD Simulation Results{Colors.RESET}")
            click.echo("=" * 70)
            click.echo(f"Simulation: {simulation_id}")
            click.echo(f"Files: {len(files)}\n")

            for file_info in files:
                file_path = file_info.get('path', '')
                file_size = file_info.get('size', 0)
                size_mb = file_size / (1024 * 1024)

                click.echo(f"{Colors.CYAN}▸{Colors.RESET} {file_path} ({size_mb:.2f} MB)")

            if download:
                warning("Download functionality not yet implemented")
                info("Use the web interface to download files for now")

            click.echo()
        else:
            error(f"Failed to get results: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='analyze')
@click.argument('simulation_id')
def nimrod_analyze(simulation_id):
    """Interactive analysis menu for NIMROD simulation (requires nimpy)."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    try:
        # Get available analyses
        result = api_client.list_nimrod_analyses(simulation_id)

        if not result.get('success'):
            error(f"Failed to get analysis info: {result.get('error', 'Unknown error')}")
            sys.exit(1)

        data = result.get('data', {})
        nimpy_status = data.get('nimpy_status', {})

        if not nimpy_status.get('available'):
            error("nimpy is not available on the backend")
            info("Contact support to enable nimpy analysis features")
            sys.exit(1)

        analyses = data.get('available_analyses', [])

        if not analyses:
            warning("No analyses available for this simulation yet")
            info("Make sure the simulation has completed and produced output files")
            return

        click.echo(f"\n{Colors.BOLD}NIMROD Analysis Menu{Colors.RESET}")
        click.echo("=" * 70)
        click.echo(f"Simulation: {simulation_id}")
        click.echo(f"Files available: {data.get('file_count', 0)}")
        click.echo(f"Has dump files: {'Yes' if data.get('has_dump_files') else 'No'}\n")

        click.echo("Available Analyses:")
        for i, analysis in enumerate(analyses, 1):
            status_icon = "✓" if analysis.get('status') == 'ready' else "⚠"
            click.echo(f"  {i}. {status_icon} {analysis.get('type')} - {analysis.get('description')}")

        choice = click.prompt("\nSelect analysis", type=click.IntRange(1, len(analyses)))
        selected = analyses[choice - 1]

        analysis_type = selected.get('type')

        # Route to specific analysis
        if analysis_type == 'field_analysis':
            field_name = click.prompt("Field name", type=click.Choice(['temperature', 'density', 'velocity', 'pressure', 'magnetic_field']))
            time_step = click.prompt("Time step (leave empty for last)", default='', show_default=False)

            result = api_client.analyze_nimrod_field(simulation_id, field_name, int(time_step) if time_step else None)

        elif analysis_type == 'equilibrium':
            result = api_client.analyze_nimrod_equilibrium(simulation_id)

        elif analysis_type == 'growth_rate':
            result = api_client.compute_nimrod_growth_rate(simulation_id)

        elif analysis_type == 'flux_surface_average':
            field_name = click.prompt("Field name", type=click.Choice(['temperature', 'density', 'pressure']))
            result = api_client.compute_nimrod_fsa(simulation_id, field_name)

        elif analysis_type == 'visualization':
            field_name = click.prompt("Field name")
            plot_type = click.prompt("Plot type", type=click.Choice(['contour', 'surface', 'vector']), default='contour')
            time_step = click.prompt("Time step (leave empty for last)", default='', show_default=False)

            result = api_client.generate_nimrod_visualization(
                simulation_id, field_name, plot_type, int(time_step) if time_step else None
            )

        # Display results
        if result.get('success'):
            success("Analysis completed!")
            data = result.get('data', {})
            click.echo(f"\n{Colors.BOLD}Results:{Colors.RESET}")
            click.echo(json.dumps(data, indent=2))
        else:
            error(f"Analysis failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='analyze-field')
@click.argument('simulation_id')
@click.option('--field', required=True, type=click.Choice(['temperature', 'density', 'velocity', 'pressure', 'magnetic_field']),
              help='Field to analyze')
@click.option('--timestep', type=int, help='Time step to analyze (defaults to last)')
def nimrod_analyze_field(simulation_id, field, timestep):
    """Analyze a specific field from simulation results (direct command)."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    click.echo(f"\n{Colors.YELLOW}Analyzing {field}...{Colors.RESET}")

    try:
        result = api_client.analyze_nimrod_field(simulation_id, field, timestep)

        if result.get('success'):
            success("Field analysis completed!")
            data = result.get('data', {})
            click.echo(f"\n{Colors.BOLD}Analysis Results:{Colors.RESET}")
            click.echo(f"  Field: {data.get('field_name')}")
            click.echo(f"  Time step: {data.get('time_step', 'last')}")
            click.echo(f"  Status: {data.get('status')}")
            click.echo(f"  Message: {data.get('message')}")
            click.echo()
        else:
            error(f"Analysis failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='analyze-equilibrium')
@click.argument('simulation_id')
def nimrod_analyze_equilibrium(simulation_id):
    """Compute equilibrium quantities (direct command)."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    click.echo(f"\n{Colors.YELLOW}Computing equilibrium...{Colors.RESET}")

    try:
        result = api_client.analyze_nimrod_equilibrium(simulation_id)

        if result.get('success'):
            success("Equilibrium computation completed!")
            data = result.get('data', {})
            quantities = data.get('quantities', {})

            click.echo(f"\n{Colors.BOLD}Equilibrium Quantities:{Colors.RESET}")
            click.echo(f"  Plasma beta: {quantities.get('plasma_beta')}")
            click.echo(f"  Resistivity: {quantities.get('resistivity')}")
            grid = quantities.get('grid_size', {})
            click.echo(f"  Grid: {grid.get('nr')}×{grid.get('nz')}×{grid.get('nphi')}")
            click.echo()
        else:
            error(f"Analysis failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='visualize')
@click.argument('simulation_id')
@click.option('--field', required=True, help='Field to visualize')
@click.option('--type', 'plot_type', type=click.Choice(['contour', 'surface', 'vector']),
              default='contour', help='Plot type')
@click.option('--timestep', type=int, help='Time step to visualize (defaults to last)')
def nimrod_visualize(simulation_id, field, plot_type, timestep):
    """Generate visualization of simulation data (direct command)."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    click.echo(f"\n{Colors.YELLOW}Generating {plot_type} plot of {field}...{Colors.RESET}")

    try:
        result = api_client.generate_nimrod_visualization(simulation_id, field, plot_type, timestep)

        if result.get('success'):
            success("Visualization generated!")
            data = result.get('data', {})
            click.echo(f"\n{Colors.BOLD}Visualization Details:{Colors.RESET}")
            click.echo(f"  Field: {data.get('field_name')}")
            click.echo(f"  Plot type: {data.get('plot_type')}")
            click.echo(f"  Time step: {data.get('time_step', 'last')}")

            plot_url = data.get('plot_url')
            if plot_url:
                click.echo(f"  URL: {Colors.CYAN}{plot_url}{Colors.RESET}")
            else:
                info("Plot will be generated when simulation output is available")

            click.echo()
        else:
            error(f"Visualization failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@nimrod.command(name='cost')
@click.option('--type', 'sim_type',
              type=click.Choice(['tokamak_disruption', 'tearing_mode', 'elm_stability', 'rwm_stability', 'resistive_mhd']),
              help='Simulation type')
@click.option('--nstep', type=int, help='Number of timesteps')
@click.option('--nr', type=int, help='Radial grid points')
@click.option('--nz', type=int, help='Vertical grid points')
@click.option('--nphi', type=int, help='Toroidal grid points')
def nimrod_cost(sim_type, nstep, nr, nz, nphi):
    """Estimate cost for a NIMROD simulation."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    # Interactive prompts if not provided
    if not sim_type:
        sim_type = 'resistive_mhd'

    if not nstep:
        nstep = click.prompt("Number of timesteps", type=int, default=1000)

    if not nr:
        nr = click.prompt("Radial points", type=int, default=64)

    if not nz:
        nz = click.prompt("Vertical points", type=int, default=128)

    if not nphi:
        nphi = click.prompt("Toroidal points", type=int, default=16)

    params = {
        'simulation_type': sim_type,
        'nstep': nstep,
        'grid_size': {'nr': nr, 'nz': nz, 'nphi': nphi}
    }

    try:
        result = api_client.estimate_nimrod_cost(params)

        if result.get('success'):
            data = result.get('data', {})
            estimates = data.get('estimates', {})

            click.echo(f"\n{Colors.BOLD}Cost Estimates{Colors.RESET}")
            click.echo("=" * 70)

            for gpu_type, est in estimates.items():
                runtime = est.get('runtime_hours')
                cost = est.get('total_cost')
                hourly = est.get('hourly_rate')

                click.echo(f"\n{Colors.CYAN}{gpu_type.upper()}{Colors.RESET}")
                click.echo(f"  Runtime: {runtime:.1f} hours")
                click.echo(f"  Hourly rate: ${hourly:.2f}")
                click.echo(f"  Total cost: ${cost:.2f}")

            recommended = data.get('recommended', '')
            click.echo(f"\n{Colors.GREEN}Recommended: {recommended}{Colors.RESET}")
            click.echo()

        else:
            error(f"Failed to estimate cost: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


# =============================================================================
# STORAGE COMMANDS
# =============================================================================

@cli.group()
def storage():
    """
    Manage simulation output storage.

    View quota usage, list simulations, download files, and manage storage.
    """
    pass


@storage.command(name='quota')
def storage_quota():
    """Show storage quota and current usage."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    try:
        result = api_client.get(f"/api/storage/quota")

        if result.get('success'):
            data = result.get('data', {})

            click.echo(f"\n{Colors.BOLD}Storage Quota{Colors.RESET}")
            click.echo("=" * 70)

            used_gb = data.get('used_gb', 0)
            quota_gb = data.get('quota_gb', 0)
            percentage = data.get('percentage_used', 0)
            sim_count = data.get('simulation_count', 0)
            sub_type = data.get('subscription_type', 'free').capitalize()

            # Color code based on usage percentage
            if percentage < 60:
                usage_color = Colors.GREEN
            elif percentage < 80:
                usage_color = Colors.YELLOW
            else:
                usage_color = Colors.RED

            click.echo(f"\n{Colors.CYAN}Subscription:{Colors.RESET} {sub_type}")
            click.echo(f"{Colors.CYAN}Simulations:{Colors.RESET} {sim_count}")
            click.echo(f"\n{Colors.CYAN}Usage:{Colors.RESET} {usage_color}{used_gb:.2f} GB{Colors.RESET} / {quota_gb:.2f} GB ({percentage:.1f}%)")

            # Progress bar
            bar_width = 50
            filled = int(bar_width * percentage / 100)
            bar = '█' * filled + '░' * (bar_width - filled)
            click.echo(f"[{usage_color}{bar}{Colors.RESET}]")

            remaining_gb = quota_gb - used_gb
            if remaining_gb > 0:
                click.echo(f"\n{Colors.GREEN}Available:{Colors.RESET} {remaining_gb:.2f} GB")
            else:
                warning("Storage quota exceeded!")

            click.echo()

        else:
            error(f"Failed to get quota: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@storage.command(name='list')
@click.option('--simulation-id', '-s', help='Show files for a specific simulation')
def storage_list(simulation_id):
    """List all simulations or files in a simulation."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    try:
        if simulation_id:
            # List files in a simulation
            result = api_client.get(f"/api/storage/simulations/{simulation_id}/files")

            if result.get('success'):
                files = result.get('data', [])

                if not files:
                    info(f"No files found in simulation {simulation_id}")
                    return

                click.echo(f"\n{Colors.BOLD}Files in {simulation_id}{Colors.RESET}")
                click.echo("=" * 70)

                total_size = 0
                for file_info in files:
                    name = file_info.get('name', '')
                    size_mb = file_info.get('size_mb', 0)
                    total_size += size_mb

                    click.echo(f"\n{Colors.GREEN}●{Colors.RESET} {name}")
                    click.echo(f"  Size: {size_mb:.2f} MB")

                click.echo(f"\n{Colors.CYAN}Total:{Colors.RESET} {len(files)} files, {total_size:.2f} MB")
                click.echo()
            else:
                error(f"Failed to list files: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        else:
            # List all simulations
            result = api_client.get(f"/api/storage/simulations")

            if result.get('success'):
                simulations = result.get('data', [])

                if not simulations:
                    info("No simulations found in storage")
                    return

                click.echo(f"\n{Colors.BOLD}Your Simulations{Colors.RESET}")
                click.echo("=" * 70)

                for sim in simulations:
                    sim_id = sim.get('simulation_id', sim.get('id', ''))
                    created = sim.get('created_at', '')[:10]
                    expires = sim.get('expires_at', '')[:10]
                    size_bytes = sim.get('total_size_bytes', 0)
                    size_mb = size_bytes / (1024**2)
                    file_count = sim.get('file_count', 0)

                    click.echo(f"\n{Colors.GREEN}●{Colors.RESET} {sim_id}")
                    click.echo(f"  Created: {created}")
                    click.echo(f"  Expires: {expires}")
                    click.echo(f"  Size: {size_mb:.2f} MB ({file_count} files)")

                click.echo(f"\n{Colors.CYAN}Total:{Colors.RESET} {len(simulations)} simulations")
                click.echo()
            else:
                error(f"Failed to list simulations: {result.get('error', 'Unknown error')}")
                sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@storage.command(name='download')
@click.argument('simulation_id')
@click.argument('filename')
@click.option('--output', '-o', help='Output file path (default: current directory)')
def storage_download(simulation_id, filename, output):
    """Download a file from a simulation."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    try:
        # Get download URL
        result = api_client.get(f"/api/storage/simulations/{simulation_id}/files/{filename}/download")

        if not result.get('success'):
            error(f"Failed to get download URL: {result.get('error', 'Unknown error')}")
            sys.exit(1)

        data = result.get('data', {})
        download_url = data.get('url')
        size_mb = data.get('size_mb', 0)

        if not download_url:
            error("No download URL received")
            sys.exit(1)

        # Determine output path
        import os
        if output:
            output_path = output
        else:
            output_path = os.path.join(os.getcwd(), filename)

        click.echo(f"\n{Colors.BOLD}Downloading {filename}{Colors.RESET}")
        click.echo(f"Size: {size_mb:.2f} MB")
        click.echo(f"To: {output_path}")
        click.echo()

        # Download the file with progress bar
        success_download = api_client.download_file(download_url, output_path)

        if success_download:
            success(f"Downloaded {filename} successfully!")
            info(f"Saved to: {output_path}")
        else:
            error("Download failed")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


@storage.command(name='delete')
@click.argument('simulation_id')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
def storage_delete(simulation_id, yes):
    """Delete a simulation and all its files."""
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        error("Not authenticated. Please run 'laurelin login' first.")
        sys.exit(1)

    api_client = APIClient(auth_manager)

    try:
        # Get simulation details first
        result = api_client.get(f"/api/storage/simulations/{simulation_id}")

        if not result.get('success'):
            error(f"Simulation not found: {simulation_id}")
            sys.exit(1)

        sim_data = result.get('data', {})
        size_bytes = sim_data.get('total_size_bytes', 0)
        size_mb = size_bytes / (1024**2)
        file_count = sim_data.get('file_count', 0)

        click.echo(f"\n{Colors.BOLD}Delete Simulation{Colors.RESET}")
        click.echo("=" * 70)
        click.echo(f"Simulation ID: {simulation_id}")
        click.echo(f"Size: {size_mb:.2f} MB ({file_count} files)")
        click.echo()

        # Confirm deletion
        if not yes:
            if not click.confirm(f"{Colors.RED}Are you sure you want to delete this simulation?{Colors.RESET}"):
                info("Deletion cancelled")
                return

        # Delete simulation
        result = api_client.delete(f"/api/storage/simulations/{simulation_id}")

        if result.get('success'):
            data = result.get('data', {})
            files_deleted = data.get('files_deleted', 0)
            gb_freed = data.get('gb_freed', 0)

            success(f"Deleted simulation {simulation_id}")
            info(f"Freed {gb_freed:.2f} GB ({files_deleted} files)")
        else:
            error(f"Failed to delete simulation: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
