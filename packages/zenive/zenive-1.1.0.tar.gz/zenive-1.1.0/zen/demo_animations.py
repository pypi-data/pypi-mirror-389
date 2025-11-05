#!/usr/bin/env python3
"""
Demo script to showcase all the beautiful animations in Zenive CLI.
"""

import time
import sys
from pathlib import Path

# Add the zen module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zen.core.logger import get_logger

def main():
    """Demonstrate all the beautiful animations."""
    logger = get_logger()
    
    # Welcome message
    logger.show_ascii_art("ZENIVE ANIMATIONS")
    time.sleep(1)
    
    # Rainbow text demo
    logger.info("🌈 Rainbow Text Demo:")
    logger.rainbow_text("Welcome to Zenive's Beautiful UI!")
    time.sleep(2)
    

    
    # Connecting lines animation demo
    logger.info("🔗 Connecting Lines Animation Demo:")
    with logger.connection_loader("Processing your request"):
        time.sleep(3)
    logger.success("Connection animation completed!")
    time.sleep(1)
    
    # Wave animation demo
    logger.info("🌊 Wave Loading Animation Demo:")
    with logger.wave_loader("Downloading components"):
        time.sleep(3)
    logger.success("Wave animation completed!")
    time.sleep(1)
    
    # Pulse animation demo
    logger.info("💓 Pulse Loading Animation Demo:")
    with logger.pulse_loader("Connecting to server"):
        time.sleep(3)
    logger.success("Pulse animation completed!")
    time.sleep(1)
    
    # Elegant border demo
    logger.info("📐 Elegant Border Demo:")
    logger.show_elegant_border("Professional Content with Clean Lines", 60)
    time.sleep(2)
    
    # Component info demo
    logger.info("📦 Enhanced Component Info Demo:")
    logger.show_component_info(
        name="email-validator",
        version="1.2.0",
        description="A beautiful email validation component with regex patterns",
        category="validation",
        dependencies=["re", "typing"],
        files_count=5
    )
    time.sleep(2)
    
    # Success summary demo
    logger.info("🎉 Success Summary Demo:")
    logger.show_success_summary(
        component="awesome-component",
        files_installed=8,
        dependencies_added=3,
        install_path="src/components/awesome-component"
    )
    time.sleep(2)
    
    # Celebration demo
    logger.info("🎊 Celebration Messages Demo:")
    logger.celebrate("Installation completed successfully!")
    logger.celebrate("All tests passed!")
    logger.celebrate("Project created with style!")
    time.sleep(2)
    
    # Loading dots demo
    logger.info("⏳ Loading Dots Demo:")
    logger.show_loading_dots("Initializing project", 2.0)
    time.sleep(1)
    
    # Matrix transition demo
    logger.info("🔢 Matrix Transition Demo:")
    logger.show_matrix_transition("Loading complete - Welcome to Zenive!", 2.5)
    time.sleep(1)
    
    # Typewriter effect demo
    logger.info("⌨️  Typewriter Effect Demo:")
    logger.animate_text("This text appears character by character like a typewriter!", 0.08)
    time.sleep(2)
    
    # Gradient text demo
    logger.info("🎨 Gradient Text Demo:")
    logger.show_gradient_text("Beautiful Gradient Text Effect", "cyan", "magenta")
    time.sleep(2)
    
    # Final celebration
    logger.show_elegant_border("✓ Animation Demo Complete", 50)
    logger.rainbow_text("Thank you for using Zenive!")
    
    # Show all message types
    logger.info("📝 All message types:")
    logger.info("This is an info message")
    logger.success("This is a success message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.debug("This is a debug message")
    logger.step("This is a step message")
    logger.progress("This is a progress message")
    
    print("\n" + "="*60)
    print("🎨 All animations demonstrated successfully!")
    print("These beautiful animations will enhance your CLI experience.")
    print("="*60)

if __name__ == "__main__":
    main()