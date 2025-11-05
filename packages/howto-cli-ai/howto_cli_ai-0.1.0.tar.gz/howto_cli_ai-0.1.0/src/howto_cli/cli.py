"""Main CLI entry point using Typer."""

import os
import json
import typer
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from howto_cli.core.config import Config, get_system_info

console = Console()
app = typer.Typer(
    name="how",
    help="AI-powered CLI assistant for shell command generation",
    no_args_is_help=True,
)


@app.command()
def setup() -> None:
    """Configure AI provider settings and API keys."""
    console.print(Panel.fit(
        "🔧 How-to CLI Setup",
        subtitle="Configure AI provider settings"
    ))
    
    console.print("\n[bold]Configure AI Provider Settings[/bold]")
    console.print("Select which AI provider you'd like to use:\n")
    
    providers = [
        ("gemini", "Google Gemini", "GEMINI_API_KEY"),
        ("openai", "OpenAI", "OPENAI_API_KEY"), 
        ("groq", "Groq", "GROQ_API_KEY")
    ]
    
    # Display provider options
    table = Table(title="Available Providers")
    table.add_column("Number", style="cyan", width=8)
    table.add_column("Provider", style="magenta")
    table.add_column("Environment Variable", style="bright_black")
    
    for i, (key, name, env_var) in enumerate(providers, 1):
        table.add_row(str(i), name, env_var)
    
    console.print(table)
    
    # Get provider selection
    choice = Prompt.ask(
        "\nSelect provider by number (1-3)",
        choices=["1", "2", "3"],
        default="1"
    )
    
    provider_key, selected_name, env_var = providers[int(choice) - 1]
    
    # Load current config to check existing API key
    config = Config.load()
    current_key = config.get_stored_api_key(provider_key) or os.getenv(env_var)
    
    console.print(f"\n[bold]Selected:[/bold] {selected_name}")
    console.print(f"[dim]Debug: Checking configuration file and environment variable {env_var}[/dim]")
    console.print(f"[dim]Debug: Current default provider: {config.default_provider or 'None'}[/dim]")
    
    if current_key:
        console.print("[green]✓ API key already configured[/green]")
        console.print(f"[dim]Debug: Found API key of length {len(current_key)}[/dim]")
        if not Confirm.ask("Would you like to update it?"):
            # Even if not updating API key, still update default provider if different
            if config.default_provider != provider_key:
                config_data = config.model_dump()
                config_data["default_provider"] = provider_key
                
                with open(config.get_config_file(), 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                console.print(f"[green]✅ Setup complete! {selected_name} set as default provider[/green]")
                console.print(f"[dim]Default provider updated to: {provider_key}[/dim]")
            else:
                console.print(f"[green]✅ Setup complete! {selected_name} is already the default provider[/green]")
            return
    
    # Get API key
    api_key = Prompt.ask(f"Enter your {selected_name} API key", password=True)
    
    # Save to config file
    try:
        config.set_api_key(provider_key, api_key, set_as_default=True)
        
        # Reload config to get updated default provider
        config = Config.load()
        
        console.print(f"\n[green]✅ Configuration saved to:[/green] {config.get_config_file()}")
        console.print(f"[dim]API key and provider settings stored securely in config file[/dim]")
        console.print(f"[dim]Default provider set to: {config.default_provider}[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to save configuration:[/red] {e}")
        # Fallback to environment variable instructions
        console.print(f"\n[bold]To manually configure, add to your shell profile:[/bold]")
        console.print(f"[cyan]export {env_var}=\"{api_key[:10]}...\"[/cyan]")
        console.print(f"[cyan]export HOW_DEFAULT_PROVIDER=\"{provider_key}\"[/cyan]")
        return
    
    # Test the key
    console.print("\n[yellow]Testing API key...[/yellow]")
    
    try:
        from howto_cli.core.command_generator import CommandGenerator
        generator = CommandGenerator(config)
        generator.generate_command("list files", provider_key)
        console.print(f"[green]✅ Setup complete! {selected_name} is working and set as default provider[/green]")
        console.print(f"[green]✅ Configuration saved to:[/green] {config.get_config_file()}")
        
    except Exception as e:
        console.print(f"[red]❌ API key test failed:[/red] {e}")
        console.print(f"[yellow]Please check your API key and try again[/yellow]")
        
        # Remove the failed configuration
        try:
            config_file = config.get_config_file()
            if config_file.exists():
                config_file.unlink()
        except:
            pass


@app.command(context_settings={"allow_extra_args": True, "allow_interspersed_args": False})
def to(ctx: typer.Context) -> None:
    """Generate shell command from natural language description."""
    
    # Get the task from remaining arguments
    if not ctx.args:
        console.print("[red]Error:[/red] Please provide a task description")
        console.print("Example: how to list all files")
        raise typer.Exit(1)
    
    # Join all remaining arguments as the task description
    task = " ".join(ctx.args)
    
    console.print(f"[bold]🤖 Generating command for:[/bold] {task}")
    
    try:
        from howto_cli.core.command_generator import CommandGenerator
        config = Config.load()
        generator = CommandGenerator(config)
        console.print(f"[dim]Debug: Config default_provider = {config.default_provider}[/dim]")
        
        # Generate command (use mock if no API keys configured)
        provider_override = None
        if not any([
            config.get_provider_config("gemini").api_key,
            config.get_provider_config("openai").api_key,
            config.get_provider_config("groq").api_key
        ]):
            console.print("[yellow]⚡ No API keys configured, using mock provider[/yellow]")
            console.print("[yellow]  Run 'how setup' to configure an AI provider[/yellow]\n")
            provider_override = "mock"
        
        # Generate command
        provider_name = provider_override or config.default_provider
        command_result = generator.generate_command(task, provider_name)
        
        console.print(f"[dim]Using provider: {provider_name}[/dim]")
        console.print(Panel(
            f"[bold]Generated Command:[/bold]\n{command_result.command}",
            title="Shell Command",
            border_style="green"
        ))
        
        console.print(f"[dim]Explanation:[/dim] {command_result.explanation}")
        
        if command_result.safety_flags:
            console.print("[bold red]⚠️  Safety Warnings:[/bold red]")
            for flag in command_result.safety_flags:
                console.print(f"  • {flag}")
        
        # Confirmation prompt
        if Confirm.ask("\nExecute this command?", default=False):
            import subprocess
            try:
                console.print("[green]✓ Executing command...[/green]")
                result = subprocess.run(command_result.command, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    console.print("[bold]Output:[/bold]")
                    console.print(result.stdout)
                
                if result.stderr:
                    console.print("[bold]Errors:[/bold]")
                    console.print(result.stderr, style="red")
                
                console.print(f"[green]✓ Command completed with exit code {result.returncode}[/green]")
                
            except Exception as e:
                console.print(f"[red]Execution failed:[/red] {e}")
        else:
            console.print("[yellow]✗ Command cancelled[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if "not configured" in str(e):
            console.print("[yellow]💡 Try running 'how setup' to configure an AI provider[/yellow]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
