"""
Transformer for fc configuration files.
Handles variable resolution and advanced transformations.
"""

import os
from typing import Any, Dict
from .model import FCConfig, FCBlock


class VariableResolver:
    """Resolves variable references in the configuration."""
    
    def __init__(self, config: FCConfig):
        self.config = config
    
    def resolve_variable(self, var_ref: str) -> str:
        """Resolve a variable reference."""
        # Remove the $() wrapper
        if var_ref.startswith("$(") and var_ref.endswith(")"):
            var_name = var_ref[2:-1]
        else:
            var_name = var_ref
        
        # Handle environment variables
        if var_name.startswith("ENV:"):
            env_var_name = var_name[4:]  # Remove "ENV:" prefix
            return os.getenv(env_var_name, "")
        
        # Handle internal references (this.block_name.key)
        if var_name.startswith("this."):
            parts = var_name[5:].split(".")  # Remove "this." prefix
            if len(parts) >= 2:
                block_name = parts[0]
                key = ".".join(parts[1:])  # Join remaining parts with dots
                
                block = self.config.get_block(block_name)
                if block:
                    # Navigate through nested dictionaries if needed
                    value = block.data
                    key_parts = key.split(".")
                    try:
                        for part in key_parts:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                return var_ref  # Return original if not found
                        return str(value)
                    except (KeyError, TypeError):
                        return var_ref  # Return original if error occurs
        
        # Handle global variables
        if var_name in self.config.variables:
            return str(self.config.variables[var_name])
        
        # Variable not found
        return var_ref
    
    def resolve_value(self, value: Any) -> Any:
        """Recursively resolve variables in a value."""
        if isinstance(value, str):
            if value.startswith("$(") and value.endswith(")"):
                return self.resolve_variable(value)
            return value
        elif isinstance(value, dict):
            resolved = {}
            for k, v in value.items():
                resolved[k] = self.resolve_value(v)
            return resolved
        elif isinstance(value, list):
            return [self.resolve_value(item) for item in value]
        else:
            return value
    
    def resolve_config(self) -> FCConfig:
        """Resolve all variables in the configuration."""
        resolved_config = FCConfig()
        resolved_config.variables = self.config.variables.copy()
        
        # Copy and resolve each block
        for block in self.config.blocks:
            resolved_block = FCBlock(block.name)
            resolved_block.meta = block.meta.copy()
            
            # Resolve data values
            for key, value in block.data.items():
                resolved_block.data[key] = self.resolve_value(value)
            
            resolved_config.add_block(resolved_block)
        
        return resolved_config


class ConfigTransformer:
    """Transforms and processes FCConfig objects."""
    
    @staticmethod
    def resolve_variables(config: FCConfig) -> FCConfig:
        """Resolve all variable references in the configuration."""
        resolver = VariableResolver(config)
        return resolver.resolve_config()
    
    @staticmethod
    def apply_environment(config: FCConfig, env_name: str = None) -> FCConfig:
        """Apply environment-specific configurations."""
        # For now, we'll just return the config as-is
        # In a full implementation, this would merge environment-specific blocks
        return config
    
    @staticmethod
    def merge_configs(base_config: FCConfig, override_config: FCConfig) -> FCConfig:
        """Merge two configurations, with override_config taking precedence."""
        merged_config = FCConfig()
        
        # Copy base variables and update with override variables
        merged_config.variables = base_config.variables.copy()
        merged_config.variables.update(override_config.variables)
        
        # Create a dict of base blocks for easy lookup
        base_blocks = {block.name: block for block in base_config.blocks}
        
        # Add all base blocks
        for block in base_config.blocks:
            merged_config.add_block(block)
        
        # Add or replace with override blocks
        for override_block in override_config.blocks:
            existing_block = merged_config.get_block(override_block.name)
            if existing_block:
                # Replace existing block
                existing_block.meta.update(override_block.meta)
                existing_block.data.update(override_block.data)
            else:
                # Add new block
                merged_config.add_block(override_block)
        
        return merged_config