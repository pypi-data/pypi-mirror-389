"""
Animation configuration for Zenive CLI.
Allows users to customize animation preferences.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AnimationConfig:
    """Configuration for CLI animations."""
    
    # Enable/disable animations
    enable_animations: bool = True
    enable_connection_loader: bool = True
    enable_wave_loader: bool = True
    enable_pulse_loader: bool = True
    enable_elegant_borders: bool = True
    enable_rainbow_text: bool = True
    enable_typewriter_effect: bool = True
    enable_matrix_transitions: bool = True
    
    # Animation speeds (lower = faster)
    connection_speed: float = 0.15
    wave_speed: float = 0.125
    pulse_speed: float = 0.167
    typewriter_speed: float = 0.05
    
    # Animation sizes
    connection_width: int = 30
    wave_width: int = 20
    matrix_transition_duration: float = 1.5
    
    # Color preferences
    primary_color: str = "cyan"
    success_color: str = "green"
    warning_color: str = "yellow"
    error_color: str = "red"
    accent_color: str = "magenta"
    
    # Border styles
    default_box_style: str = "ROUNDED"  # ROUNDED, DOUBLE, HEAVY, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def save_to_file(self, file_path: Path):
        """Save configuration to file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'AnimationConfig':
        """Load configuration from file."""
        if not file_path.exists():
            return cls()  # Return default config
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return cls()  # Return default config on error


class AnimationManager:
    """Manages animation configuration and preferences."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".zen"
        self.config_file = self.config_dir / "animation_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> AnimationConfig:
        """Load animation configuration."""
        return AnimationConfig.load_from_file(self.config_file)
    
    def save_config(self):
        """Save current configuration."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config.save_to_file(self.config_file)
    
    def update_config(self, **kwargs):
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = AnimationConfig()
        self.save_config()
    
    def disable_all_animations(self):
        """Disable all animations for performance."""
        self.update_config(
            enable_animations=False,
            enable_connection_loader=False,
            enable_wave_loader=False,
            enable_pulse_loader=False,
            enable_elegant_borders=False,
            enable_rainbow_text=False,
            enable_typewriter_effect=False,
            enable_matrix_transitions=False
        )
    
    def enable_minimal_animations(self):
        """Enable only minimal animations."""
        self.update_config(
            enable_animations=True,
            enable_connection_loader=False,
            enable_wave_loader=True,
            enable_pulse_loader=False,
            enable_elegant_borders=False,
            enable_rainbow_text=False,
            enable_typewriter_effect=False,
            enable_matrix_transitions=False
        )
    
    def enable_full_animations(self):
        """Enable all animations."""
        self.update_config(
            enable_animations=True,
            enable_connection_loader=True,
            enable_wave_loader=True,
            enable_pulse_loader=True,
            enable_elegant_borders=True,
            enable_rainbow_text=True,
            enable_typewriter_effect=True,
            enable_matrix_transitions=True
        )


# Global animation manager instance
_animation_manager: Optional[AnimationManager] = None


def get_animation_manager() -> AnimationManager:
    """Get or create the global animation manager."""
    global _animation_manager
    if _animation_manager is None:
        _animation_manager = AnimationManager()
    return _animation_manager


def get_animation_config() -> AnimationConfig:
    """Get the current animation configuration."""
    return get_animation_manager().config