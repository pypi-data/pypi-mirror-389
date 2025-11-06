"""
Logging configuration for Zenive with beautiful animations.
"""

import logging
import sys
import time
import threading
import random
from typing import Optional, Any, List, Tuple
from contextlib import contextmanager
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.align import Align
from rich.live import Live
from rich.table import Table
from rich.columns import Columns
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.style import Style

# Import animation configuration
try:
    from .animation_config import get_animation_config
except ImportError:
    # Fallback if animation_config is not available
    def get_animation_config():
        class MockConfig:
            enable_animations = True
            enable_connection_loader = True
            enable_wave_loader = True
            enable_pulse_loader = True
            enable_elegant_borders = True
            enable_rainbow_text = True
            enable_typewriter_effect = True
            connection_speed = 0.15
            wave_speed = 0.125
            pulse_speed = 0.167
            typewriter_speed = 0.05
            connection_width = 30
            wave_width = 20
            primary_color = "cyan"
            success_color = "green"
            default_box_style = "ROUNDED"
        return MockConfig()


class ConnectingLinesAnimation:
    """Elegant interconnecting lines with small diamonds animation."""
    
    def __init__(self, width: int = 30):
        self.width = width
        self.frames = self._generate_connection_frames()
        self.current_frame = 0
    
    def _generate_connection_frames(self) -> List[str]:
        """Generate interconnecting lines animation frames."""
        frames = []
        
        # Connection animation - lines connecting with small diamonds
        for step in range(self.width + 5):
            line = ""
            
            # Build the connection line progressively
            for i in range(min(step, self.width)):
                if i == 0:
                    line += "◆"
                elif i == step - 1 and step < self.width:
                    line += "─◆"
                elif i % 4 == 0:
                    line += "─◇"
                else:
                    line += "──"
            
            # Add completion effect
            if step >= self.width:
                line = "◆" + "─◇" * ((self.width - 1) // 4) + "─" * ((self.width - 1) % 4) + "◆"
            
            frames.append(line)
        
        return frames
    
    def get_next_frame(self) -> str:
        """Get the next animation frame."""
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return frame


class WaveAnimation:
    """Beautiful wave animation for loading."""
    
    def __init__(self, width: int = None):
        config = get_animation_config()
        self.width = width or config.wave_width
        self.frames = self._generate_wave_frames()
        self.current_frame = 0
    
    def _generate_wave_frames(self) -> List[str]:
        """Generate wave animation frames."""
        frames = []
        wave_chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        for offset in range(self.width):
            wave = ""
            for i in range(self.width):
                wave_height = int((len(wave_chars) - 1) * (0.5 + 0.5 * 
                    __import__('math').sin(2 * __import__('math').pi * (i + offset) / 8)))
                wave += wave_chars[wave_height]
            frames.append(wave)
        
        return frames
    
    def get_next_frame(self) -> str:
        """Get the next animation frame."""
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return frame


class PulseAnimation:
    """Pulsing circle animation."""
    
    def __init__(self):
        self.frames = ["◯", "◉", "●", "◉"]
        self.current_frame = 0
    
    def get_next_frame(self) -> str:
        """Get the next animation frame."""
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return frame


class ZeniveLogger:
    """Custom logger for Zenive with rich formatting and beautiful animations."""
    
    def __init__(self, name: str = "zenive", level: int = logging.INFO):
        self.console = Console()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create rich handler
        rich_handler = RichHandler(
            console=self.console,
            show_time=False,
            show_path=False,
            markup=True,
        )
        rich_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter("%(message)s")
        rich_handler.setFormatter(formatter)
        
        self.logger.addHandler(rich_handler)
        self.logger.propagate = False
        
        # Animation instances
        self.connection_anim = ConnectingLinesAnimation()
        self.wave_anim = WaveAnimation()
        self.pulse_anim = PulseAnimation()
        
        # Animation state
        self._current_spinner = None
        self._animation_thread = None
        self._stop_animation = False
    
    def info(self, message: str, **kwargs):
        """Log info message with rich formatting."""
        self.logger.info(f"[blue]ℹ[/blue] {message}", **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message with rich formatting."""
        self.logger.info(f"[green]✓[/green] {message}", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with rich formatting."""
        self.logger.warning(f"[yellow]⚠[/yellow] {message}", **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with rich formatting."""
        self.logger.error(f"[red]✗[/red] {message}", **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with rich formatting."""
        self.logger.debug(f"[dim]🐛[/dim] {message}", **kwargs)
    
    def step(self, message: str, **kwargs):
        """Log step message for processes."""
        self.logger.info(f"[cyan]→[/cyan] {message}", **kwargs)
    
    def progress(self, message: str, **kwargs):
        """Log progress message."""
        self.logger.info(f"[magenta]⟳[/magenta] {message}", **kwargs)
    
    def celebrate(self, message: str, **kwargs):
        """Log celebration message with elegant styling."""
        self.logger.info(f"[bold green]✓[/bold green] {message}", **kwargs)
    
    @contextmanager
    def spinner(self, message: str, spinner_style: str = "dots"):
        """Context manager for showing a spinner during operations."""
        with self.console.status(f"[cyan]{message}[/cyan]", spinner=spinner_style) as status:
            try:
                yield status
            except Exception as e:
                self.error(f"Failed: {e}")
                raise
    
    @contextmanager
    def connection_loader(self, message: str):
        """Context manager for showing elegant connecting lines animation."""
        config = get_animation_config()
        
        if not config.enable_animations or not config.enable_connection_loader:
            # Fallback to simple spinner
            with self.spinner(message):
                yield
            return
        
        self._stop_animation = False
        
        def animate():
            with Live(console=self.console, refresh_per_second=8) as live:
                while not self._stop_animation:
                    connection_frame = self.connection_anim.get_next_frame()
                    content = f"[{config.primary_color}]{message}[/{config.primary_color}]\n\n[bold blue]{connection_frame}[/bold blue]"
                    panel = Panel(
                        Align.center(content),
                        border_style=config.primary_color,
                        box=ROUNDED
                    )
                    live.update(panel)
                    time.sleep(0.15)
        
        self._animation_thread = threading.Thread(target=animate)
        self._animation_thread.daemon = True
        self._animation_thread.start()
        
        try:
            yield
        except Exception as e:
            self.error(f"Failed: {e}")
            raise
        finally:
            self._stop_animation = True
            if self._animation_thread:
                self._animation_thread.join(timeout=1)
    
    @contextmanager
    def wave_loader(self, message: str):
        """Context manager for showing wave animation during operations."""
        config = get_animation_config()
        
        if not config.enable_animations or not config.enable_wave_loader:
            # Fallback to simple spinner
            with self.spinner(message):
                yield
            return
        
        self._stop_animation = False
        
        def animate():
            with Live(console=self.console, refresh_per_second=8) as live:
                while not self._stop_animation:
                    wave_frame = self.wave_anim.get_next_frame()
                    content = f"[{config.primary_color}]{message}[/{config.primary_color}]\n\n[bold {config.success_color}]{wave_frame}[/bold {config.success_color}]"
                    panel = Panel(
                        Align.center(content),
                        border_style=config.success_color,
                        box=ROUNDED
                    )
                    live.update(panel)
                    time.sleep(config.wave_speed)
        
        self._animation_thread = threading.Thread(target=animate)
        self._animation_thread.daemon = True
        self._animation_thread.start()
        
        try:
            yield
        except Exception as e:
            self.error(f"Failed: {e}")
            raise
        finally:
            self._stop_animation = True
            if self._animation_thread:
                self._animation_thread.join(timeout=1)
    
    @contextmanager
    def pulse_loader(self, message: str):
        """Context manager for showing pulse animation during operations."""
        config = get_animation_config()
        
        if not config.enable_animations or not config.enable_pulse_loader:
            # Fallback to simple spinner
            with self.spinner(message):
                yield
            return
        
        self._stop_animation = False
        
        def animate():
            with Live(console=self.console, refresh_per_second=6) as live:
                while not self._stop_animation:
                    pulse_frame = self.pulse_anim.get_next_frame()
                    content = f"[bold {config.warning_color}]{pulse_frame}[/bold {config.warning_color}] [{config.primary_color}]{message}[/{config.primary_color}] [bold {config.warning_color}]{pulse_frame}[/bold {config.warning_color}]"
                    panel = Panel(
                        Align.center(content),
                        border_style=config.warning_color,
                        box=ROUNDED
                    )
                    live.update(panel)
                    time.sleep(config.pulse_speed)
        
        self._animation_thread = threading.Thread(target=animate)
        self._animation_thread.daemon = True
        self._animation_thread.start()
        
        try:
            yield
        except Exception as e:
            self.error(f"Failed: {e}")
            raise
        finally:
            self._stop_animation = True
            if self._animation_thread:
                self._animation_thread.join(timeout=1)
    
    def show_banner(self, title: str, subtitle: str = None):
        """Show a clean, professional banner."""
        content = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"
        
        # Clean line decoration
        decoration = "─" * (len(title) + 4)
        
        panel_content = f"[cyan]{decoration}[/cyan]\n\n{content}\n\n[cyan]{decoration}[/cyan]"
        
        panel = Panel(
            Align.center(panel_content),
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def show_animated_banner(self, title: str, subtitle: str = None):
        """Show an animated banner with typewriter effect."""
        self.console.print()
        
        # Typewriter effect for title
        title_text = Text()
        for char in title:
            title_text.append(char, style="bold cyan")
            self.console.print(Align.center(title_text), end="\r")
            time.sleep(0.05)
        
        self.console.print()
        
        if subtitle:
            time.sleep(0.3)
            subtitle_text = Text()
            for char in subtitle:
                subtitle_text.append(char, style="dim")
                self.console.print(Align.center(subtitle_text), end="\r")
                time.sleep(0.03)
            self.console.print()
        
        self.console.print()
    
    def show_component_info(self, name: str, version: str, description: str, 
                          category: str, dependencies: list, files_count: int):
        """Show component information in a beautiful format with enhanced styling."""
        # Create a beautiful info table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="bold yellow", width=12)
        table.add_column("Value", style="white")
        
        table.add_row("Name", f"[bold green]{name}[/bold green] [dim]v{version}[/dim]")
        table.add_row("Description", f"[dim]{description}[/dim]")
        table.add_row("Category", f"[cyan]{category}[/cyan]")
        table.add_row("Files", f"[blue]{files_count} files[/blue]")
        table.add_row("Dependencies", f"[magenta]{', '.join(dependencies) if dependencies else 'None'}[/magenta]")
        
        # Add some visual flair
        header = "[bold cyan]📦 Component Information[/bold cyan]"
        
        panel = Panel(
            table,
            title=header,
            border_style="green",
            box=ROUNDED,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def show_success_summary(self, component: str, files_installed: int, 
                           dependencies_added: int, install_path: str):
        """Show installation success summary with clean, professional styling."""
        # Create success table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Icon", width=3)
        table.add_column("Info", style="white")
        
        table.add_row("📁", f"[cyan]Files installed:[/cyan] [bold white]{files_installed}[/bold white]")
        table.add_row("📦", f"[cyan]Dependencies added:[/cyan] [bold white]{dependencies_added}[/bold white]")
        table.add_row("📍", f"[cyan]Install path:[/cyan] [dim]{install_path}[/dim]")
        
        # Clean success header
        header = f"[bold green]✓ Successfully installed {component}[/bold green]"
        
        footer = "\n[dim]Component is ready to use[/dim]"
        if dependencies_added > 0:
            footer += "\n[dim]💡 Run 'pip install -r requirements.txt' to install new dependencies[/dim]"
        
        # Combine everything properly
        from rich.console import Group
        content_group = Group(
            f"{header}",
            "",
            table,
            footer
        )
        
        final_panel = Panel(
            content_group,
            border_style="green",
            box=ROUNDED,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(final_panel)
        self.console.print()
    
    def show_progress_bar(self, total: int, description: str = "Processing"):
        """Show a beautiful progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            console=self.console
        )
    
    def show_gradient_text(self, text: str, start_color: str = "cyan", end_color: str = "magenta"):
        """Show text with gradient effect."""
        gradient_text = Text(text)
        gradient_text.stylize(f"bold {start_color}")
        self.console.print(Align.center(gradient_text))
    
    def show_loading_dots(self, message: str, duration: float = 2.0):
        """Show animated loading dots."""
        dots = ""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            for i in range(4):
                dots = "." * i
                self.console.print(f"\r[cyan]{message}{dots}[/cyan]   ", end="")
                time.sleep(0.3)
        
        self.console.print(f"\r[green]{message}... Done![/green]")
    
    def show_matrix_transition(self, message: str, duration: float = 1.5):
        """Show a single line matrix effect that transitions to actual content."""
        chars = "01"
        width = len(message) + 10
        
        with Live(console=self.console, refresh_per_second=15) as live:
            # Matrix phase - single line of random characters
            matrix_duration = duration * 0.6
            start_time = time.time()
            
            while time.time() - start_time < matrix_duration:
                matrix_line = "".join(random.choice(chars) for _ in range(width))
                live.update(f"[green]{matrix_line}[/green]")
                time.sleep(0.067)
            
            # Transition phase - gradually replace with actual message
            transition_duration = duration * 0.4
            start_time = time.time()
            
            while time.time() - start_time < transition_duration:
                progress = (time.time() - start_time) / transition_duration
                reveal_length = int(len(message) * progress)
                
                revealed = message[:reveal_length]
                remaining_matrix = "".join(random.choice(chars) for _ in range(width - len(revealed)))
                
                content = f"[cyan]{revealed}[/cyan][green]{remaining_matrix}[/green]"
                live.update(content)
                time.sleep(0.05)
            
            # Final message
            live.update(f"[cyan]{message}[/cyan]")
            time.sleep(0.3)
    
    def animate_text(self, text: str, delay: float = 0.05):
        """Animate text character by character with typewriter effect."""
        animated_text = Text()
        for char in text:
            animated_text.append(char)
            self.console.print(animated_text, end="\r")
            time.sleep(delay)
        self.console.print()  # New line at the end
    
    def rainbow_text(self, text: str):
        """Display text with rainbow colors."""
        colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]
        rainbow_text = Text()
        
        for i, char in enumerate(text):
            color = colors[i % len(colors)]
            rainbow_text.append(char, style=f"bold {color}")
        
        self.console.print(Align.center(rainbow_text))
    
    def show_ascii_art(self, text: str):
        """Show ASCII art style text."""
        ascii_art = f"""
╔══════════════════════════════════════╗
║              {text.center(20)}              ║
╚══════════════════════════════════════╝
        """
        self.console.print(f"[bold cyan]{ascii_art}[/bold cyan]")
    
    def show_elegant_border(self, content: str, width: int = 50):
        """Show content with clean, elegant border."""
        # Clean line borders
        border_line = "─" * width
        
        bordered_content = f"""
[cyan]{border_line}[/cyan]
{content}
[cyan]{border_line}[/cyan]
        """
        
        panel = Panel(
            Align.center(bordered_content.strip()),
            border_style="cyan",
            box=ROUNDED
        )
        self.console.print(panel)


# Global logger instance
_logger: Optional[ZeniveLogger] = None


def get_logger(name: str = "zenive", level: int = logging.INFO) -> ZeniveLogger:
    """Get or create the global Zenive logger."""
    global _logger
    if _logger is None:
        _logger = ZeniveLogger(name, level)
    return _logger


def set_log_level(level: int):
    """Set the logging level for the global logger."""
    logger = get_logger()
    logger.logger.setLevel(level)
    for handler in logger.logger.handlers:
        handler.setLevel(level)


def enable_debug():
    """Enable debug logging."""
    set_log_level(logging.DEBUG)


def disable_debug():
    """Disable debug logging."""
    set_log_level(logging.INFO)

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    set_log_level(level)
