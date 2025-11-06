# src/cli/completion.py - Tab completion support for DFIT

import os
import click
from pathlib import Path


class PathCompleter:
    """Provides path completion for Click commands."""
    
    @staticmethod
    def complete_path(ctx, param, incomplete):
        """Complete file paths with tab."""
        # Get the directory and prefix
        if incomplete.startswith('/'):
            # Absolute path
            directory = os.path.dirname(incomplete) or '/'
            prefix = os.path.basename(incomplete)
        else:
            # Relative path
            directory = os.path.dirname(incomplete) or '.'
            prefix = os.path.basename(incomplete)
        
        # Expand user home directory
        directory = os.path.expanduser(directory)
        
        try:
            # List files in directory
            if os.path.isdir(directory):
                items = os.listdir(directory)
                # Filter by prefix
                matches = [item for item in items if item.startswith(prefix)]
                
                # Return full paths
                completions = []
                for match in matches:
                    full_path = os.path.join(directory, match)
                    if os.path.isdir(full_path):
                        completions.append(full_path + '/')
                    else:
                        completions.append(full_path)
                
                return sorted(completions)
        except (OSError, PermissionError):
            pass
        
        return []
    
    @staticmethod
    def complete_image_files(ctx, param, incomplete):
        """Complete image file paths with tab."""
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        
        # Get the directory and prefix
        if incomplete.startswith('/'):
            directory = os.path.dirname(incomplete) or '/'
            prefix = os.path.basename(incomplete)
        else:
            directory = os.path.dirname(incomplete) or '.'
            prefix = os.path.basename(incomplete)
        
        # Expand user home directory
        directory = os.path.expanduser(directory)
        
        try:
            if os.path.isdir(directory):
                items = os.listdir(directory)
                matches = [item for item in items if item.startswith(prefix)]
                
                completions = []
                for match in matches:
                    full_path = os.path.join(directory, match)
                    if os.path.isdir(full_path):
                        completions.append(full_path + '/')
                    elif os.path.isfile(full_path):
                        # Check if it's an image file
                        ext = os.path.splitext(full_path)[1].lower()
                        if ext in supported_extensions:
                            completions.append(full_path)
                
                return sorted(completions)
        except (OSError, PermissionError):
            pass
        
        return []


def setup_completion():
    """Setup shell completion for DFIT CLI."""
    # This function can be called to enable completion in different shells
    # For bash: eval "$(_DFIT_COMPLETE=bash_source dfit)"
    # For zsh: eval "$(_DFIT_COMPLETE=zsh_source dfit)"
    pass
