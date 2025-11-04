"""Typer CLI entry point for proplate."""

import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from proplate import __version__
from proplate.clipboard import copy_to_clipboard
from proplate.selector import prompt_for_value, select_template
from proplate.template import fill_placeholders, find_placeholders, get_template_info, parse_template


app = typer.Typer(help="Inject prompt templates with filled placeholders to clipboard")
console = Console()


def version_callback(value: bool) -> None:
    """
    Print version and exit if --version flag is provided.

    :param value: Boolean indicating if version flag was provided
    """
    if value:
        console.print(f"proplate version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
) -> None:
    """
    Global callback to handle --version flag.

    :param version: Flag to show version
    """
    pass


def get_templates_dir() -> Path:
    """
    Get the templates directory path.
    Auto-migrates from old ~/.promptic directory if it exists.

    :return: Path to ~/.proplate/templates/
    """
    old_dir = Path.home() / ".promptic"
    new_dir = Path.home() / ".proplate"
    templates_dir = new_dir / "templates"

    # Auto-migrate from old directory if it exists and new one doesn't
    if old_dir.exists() and not new_dir.exists():
        try:
            old_dir.rename(new_dir)
            console.print(f"✓ Migrated templates directory: {old_dir} → {new_dir}", style="bold green")
        except Exception as e:
            console.print(f"⚠ Could not auto-migrate directory: {e}", style="yellow")
            console.print(f"→ Please manually rename {old_dir} to {new_dir}", style="yellow")

    return templates_dir


def template_name_autocomplete(incomplete: str) -> list[str]:
    """
    Autocomplete function for template names.

    :param incomplete: Partial template name typed by user
    :return: List of matching template names
    """
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        return list()

    template_files = templates_dir.glob("*.md")
    names = [t.stem for t in template_files]
    return [name for name in names if name.startswith(incomplete)]


def process_template(template_path: Path) -> None:
    """
    Process a template: extract placeholders, prompt for values, fill, and copy.

    :param template_path: Path to the template file
    """
    # Read template
    content = template_path.read_text()
    parsed = parse_template(content)

    template_body = parsed["body"]
    metadata = parsed["metadata"]

    # Show template info
    title = metadata.get("title", template_path.stem)
    console.print()
    console.print(Panel(f"[bold]{title}[/bold]", expand=False))
    console.print()

    # Find placeholders
    placeholders = find_placeholders(template_body)

    if not placeholders:
        # No placeholders, just copy as-is
        copy_to_clipboard(template_body)
        return

    # Prompt for each placeholder
    values = dict()
    for placeholder in placeholders:
        value = prompt_for_value(placeholder)
        values[placeholder["name"]] = value

    # Fill placeholders
    filled = fill_placeholders(template_body, values)

    # Copy to clipboard
    console.print()
    copy_to_clipboard(filled)


def run_template(template_name: str | None = None) -> None:
    """
    Run template selection and processing logic.

    :param template_name: Optional template name for direct selection
    """
    templates_dir = get_templates_dir()

    # Auto-create templates directory if it doesn't exist
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    # Check if any templates exist
    template_files = list(templates_dir.glob("*.md"))
    if not template_files:
        console.print("✗ No templates found", style="bold red")
        console.print(f"→ Add .md template files to {templates_dir}", style="yellow")
        console.print("→ Run 'proplate path' to see the templates directory", style="yellow")
        raise typer.Exit(1)

    # Get template path
    if template_name:
        # Direct template selection
        template_path = templates_dir / f"{template_name}.md"
        if not template_path.exists():
            console.print(f"✗ Template '{template_name}' not found", style="bold red")
            console.print("→ Run 'proplate list' to see available templates", style="yellow")
            raise typer.Exit(1)
    else:
        # Interactive selection
        template_path = select_template(templates_dir)
        if template_path is None:
            console.print("✗ No template selected", style="yellow")
            raise typer.Exit(0)

    # Process the template
    process_template(template_path)


@app.command(name="list")
def list_templates() -> None:
    """List all available templates with descriptions."""
    templates_dir = get_templates_dir()

    # Auto-create templates directory if it doesn't exist
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    template_files = sorted(templates_dir.glob("*.md"))

    if not template_files:
        console.print("✗ No templates found", style="bold red")
        console.print(f"→ Add .md template files to {templates_dir}", style="yellow")
        raise typer.Exit(0)

    console.print(f"\n[bold]Available Templates ({len(template_files)}):[/bold]")
    console.print("━" * 60)

    for template_path in template_files:
        info = get_template_info(template_path)
        console.print(f"  [cyan]{template_path.name}[/cyan]")
        if info["description"]:
            console.print(f"    {info['description']}")
        console.print()


@app.command()
def new(template_name: str = typer.Argument(...,
                                            help="Name for the new template (without .md extension)")) -> None:
    """Create a new template file and open it in $EDITOR."""
    templates_dir = get_templates_dir()

    # Auto-create templates directory if it doesn't exist
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    # Add .md extension if not provided
    if not template_name.endswith(".md"):
        template_path = templates_dir / f"{template_name}.md"
    else:
        template_path = templates_dir / template_name

    # Check if template already exists
    if template_path.exists():
        console.print(f"✗ Template '{template_name}' already exists", style="bold red")
        console.print(f"→ Use 'proplate edit {template_name}' to modify it", style="yellow")
        raise typer.Exit(1)

    # Create template with starter content
    starter_content = """---
title: {title}
description: Add a description here
---

# {{{{placeholder}}}}

Your template content goes here.
Use {{{{placeholder}}}} syntax for variables.
""".format(title=template_name.replace("-", " ").replace("_", " ").title().replace(".md", ""))

    template_path.write_text(starter_content)
    console.print(f"✓ Created template: {template_path.name}", style="bold green")

    # Open in editor
    editor = os.environ.get("EDITOR", "vim")

    try:
        subprocess.run([editor, str(template_path)], check=True)
        console.print(f"\n✓ Template '{template_path.name}' is ready to use!", style="bold green")
    except Exception as e:
        console.print(f"✗ Failed to open editor: {e}", style="bold red")
        console.print(f"→ You can manually edit: {template_path}", style="yellow")
        raise typer.Exit(1)


@app.command()
def edit(template_name: str = typer.Argument(...,
                                             autocompletion=template_name_autocomplete,
                                             help="Template name to edit")) -> None:
    """Open a template in $EDITOR."""
    templates_dir = get_templates_dir()

    # Auto-create templates directory if it doesn't exist
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    template_path = templates_dir / f"{template_name}.md"

    if not template_path.exists():
        console.print(f"✗ Template '{template_name}' not found", style="bold red")
        console.print(f"→ Use 'proplate new {template_name}' to create it", style="yellow")
        raise typer.Exit(1)

    editor = os.environ.get("EDITOR", "vim")

    try:
        subprocess.run([editor, str(template_path)], check=True)
    except Exception as e:
        console.print(f"✗ Failed to open editor: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def delete(
    template_name: str = typer.Argument(...,
                                        autocompletion=template_name_autocomplete,
                                        help="Template name to delete"),
    force: bool = typer.Option(False, "--force", "-f",
                               help="Skip confirmation prompt")
) -> None:
    """Delete a template file."""
    templates_dir = get_templates_dir()

    # Auto-create templates directory if it doesn't exist
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    template_path = templates_dir / f"{template_name}.md"

    if not template_path.exists():
        console.print(f"✗ Template '{template_name}' not found", style="bold red")
        console.print("→ Use 'proplate list' to see available templates", style="yellow")
        raise typer.Exit(1)

    # Show confirmation unless --force is used
    if not force:
        # Check for interactive terminal before importing questionary
        # (questionary/prompt_toolkit fails in non-TTY environments)
        if not sys.stdin.isatty():
            console.print("✗ Confirmation requires a terminal. Use --force to skip confirmation.", style="bold red")
            raise typer.Exit(1)

        import questionary

        confirm = questionary.confirm(f"Delete template '{template_name}'?", default=False).ask()

        if not confirm:
            console.print("✗ Deletion cancelled", style="yellow")
            raise typer.Exit(0)

    # Delete the template
    try:
        template_path.unlink()
        console.print(f"✓ Deleted template: {template_name}", style="bold green")
    except Exception as e:
        console.print(f"✗ Failed to delete template: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def init() -> None:
    """
    Initialize templates directory (optional - auto-created on first use).
    Useful for seeing the templates location before adding files.
    """
    templates_dir = get_templates_dir()

    if templates_dir.exists():
        console.print(f"✓ Templates directory already exists: {templates_dir}", style="green")
    else:
        templates_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"✓ Created templates directory: {templates_dir}", style="bold green")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Add your .md template files to this directory")
    console.print("2. Run 'proplate list' to see your templates")
    console.print("3. Run 'proplate' to use them interactively")


@app.command()
def path() -> None:
    """Print the templates directory path."""
    templates_dir = get_templates_dir()
    console.print(str(templates_dir))


@app.command()
def show(template_name: str = typer.Argument(...,
                                             autocompletion=template_name_autocomplete,
                                             help="Template name to display")) -> None:
    """Display template contents with beautiful formatting."""
    templates_dir = get_templates_dir()

    # Auto-create templates directory if it doesn't exist
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    template_path = templates_dir / f"{template_name}.md"

    if not template_path.exists():
        console.print(f"✗ Template '{template_name}' not found", style="bold red")
        console.print("→ Use 'proplate list' to see available templates", style="yellow")
        raise typer.Exit(1)

    # Read and parse template
    content = template_path.read_text()
    parsed = parse_template(content)
    metadata = parsed["metadata"]
    body = parsed["body"]

    # Display header
    console.print()
    title = metadata.get("title", template_name)
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))

    # Display metadata if present
    if metadata:
        console.print()
        console.print("[bold]Metadata:[/bold]")
        metadata_table = Table(show_header=False, box=None, padding=(0, 2))
        metadata_table.add_column("Key", style="cyan")
        metadata_table.add_column("Value", style="white")

        for key, value in metadata.items():
            metadata_table.add_row(key, str(value))

        console.print(metadata_table)

    # Find and display placeholders
    placeholders = find_placeholders(body)
    if placeholders:
        console.print()
        console.print("[bold]Placeholders:[/bold]")
        placeholder_table = Table(show_header=True, box=None, padding=(0, 2))
        placeholder_table.add_column("Name", style="yellow")
        placeholder_table.add_column("Default Value", style="dim")

        for placeholder in placeholders:
            name = placeholder["name"]
            default = placeholder.get("default")
            default_display = default if default else "[dim]none[/dim]"
            placeholder_table.add_row(name, default_display)

        console.print(placeholder_table)

    # Display template body
    console.print()
    console.print("[bold]Template Content:[/bold]")
    console.print()

    # Render as markdown for beautiful display
    md = Markdown(body)
    console.print(Panel(md, expand=False, border_style="dim"))

    # Display raw template path
    console.print()
    console.print(f"[dim]Template path: {template_path}[/dim]")
    console.print()


def cli_wrapper() -> None:
    """
    Custom CLI wrapper to handle default command behavior.
    If no recognized command is provided, treat first arg as template name.
    """
    # Check if we're in shell completion mode
    # Typer uses environment variables like _PROPLATE_COMPLETE=complete_zsh
    completion_env_vars = [
        "_PROPLATE_COMPLETE",
        "_PROPLATE_COMPLETE_ZSH",
        "_PROPLATE_COMPLETE_BASH",
        "_PROPLATE_COMPLETE_FISH"
    ]
    if any(os.environ.get(var) for var in completion_env_vars):
        # In completion mode - need to provide completions
        # Parse the completion args to figure out what to complete
        complete_args = os.environ.get("_TYPER_COMPLETE_ARGS", "").split()

        # Check if we're completing the first argument (after 'proplate ')
        # complete_args will be like: ['proplate'] or ['proplate', 'l'] or ['proplate', 'list']
        if len(complete_args) >= 1:
            # Get the incomplete word being typed (last arg if exists, else empty)
            incomplete = complete_args[-1] if len(complete_args) > 1 else ""

            # If we only have 'proplate' or 'proplate <incomplete>', we're at the first arg
            # Check if we're not in a subcommand (like 'proplate edit <something>')
            if len(complete_args) <= 2 and not incomplete.startswith("-"):
                # Dynamically extract command names from registered commands
                commands = [
                    cmd.name if cmd.name else cmd.callback.__name__
                    for cmd in app.registered_commands
                    if cmd.callback
                ]

                # Provide both command and template completions
                all_completions = commands + template_name_autocomplete(incomplete)

                # Filter to only matches that start with the incomplete string
                matches = [c for c in all_completions if c.startswith(incomplete)]

                # Output in zsh completion format that can be eval'd
                # The completion script uses: eval $(proplate ...)
                # So we need to output a zsh completion command, not just plain text
                if matches:
                    # Format as: _arguments '*: :((value1 value2 value3))'
                    # Escape any special characters for zsh
                    escaped_matches = [m.replace("'", "'\\''").replace('"', '\\"') for m in matches]
                    completion_items = " ".join(f'"{m}"' for m in escaped_matches)
                    print(f"_arguments '*: :(({completion_items}))'")
                return

        # Fall back to normal Typer completion for other cases (subcommands, options, etc.)
        app()
        return

    # Build set of recognized commands and options dynamically
    # Extract command names from registered commands
    command_names = {
        cmd.name if cmd.name else cmd.callback.__name__
        for cmd in app.registered_commands
        if cmd.callback
    }
    # Add global options/flags
    commands = command_names | {
        "--help", "-h",
        "--version", "-v",
        "--install-completion",
        "--show-completion"
    }

    try:
        # Check if we have args and if first arg is not a command
        if len(sys.argv) > 1 and sys.argv[1] not in commands and not sys.argv[1].startswith("-"):
            # First arg is a template name, run template selection
            template_name = sys.argv[1] if len(sys.argv) > 1 else None
            run_template(template_name)
        elif len(sys.argv) == 1:
            # No args, run interactive mode
            run_template()
        else:
            # Run Typer app normally for commands
            app()
    except typer.Exit as e:
        # Gracefully handle typer exits
        sys.exit(e.exit_code)


if __name__ == "__main__":
    cli_wrapper()
