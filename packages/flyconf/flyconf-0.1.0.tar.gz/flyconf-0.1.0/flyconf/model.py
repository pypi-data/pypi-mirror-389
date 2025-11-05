"""
Data models for fc configuration files.
"""

from typing import List, Dict, Any, Optional


class FCBlock:
    """
    Represents a block in fc configuration file.
    
    A block consists of:
    - name: Block identifier
    - meta: Metadata dictionary
    - data: Data dictionary containing key-value pairs
    """
    
    def __init__(self, name: str):
        self.name: str = name
        self.meta: Dict[str, Any] = {}
        self.data: Dict[str, Any] = {}
    
    def __repr__(self) -> str:
        return f"FCBlock(name='{self.name}', meta={self.meta}, data={self.data})"


class FCConfig:
    """
    Represents a complete fc configuration.
    
    Contains:
    - blocks: List of FCBlock objects
    - variables: Global variables dictionary
    """
    
    def __init__(self):
        self.blocks: List[FCBlock] = []
        self.variables: Dict[str, Any] = {}
    
    def get_block(self, name: str) -> Optional[FCBlock]:
        """Get a block by name."""
        for block in self.blocks:
            if block.name == name:
                return block
        return None
    
    def add_block(self, block: FCBlock) -> None:
        """Add a block to the configuration."""
        self.blocks.append(block)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        result = {
            "variables": self.variables,
            "blocks": {}
        }
        
        for block in self.blocks:
            result["blocks"][block.name] = {
                "meta": block.meta,
                "data": block.data
            }
        
        return result
    
    def to_json(self) -> str:
        """Convert the configuration to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FCConfig":
        """Create a configuration from a dictionary."""
        config = cls()
        config.variables = data.get("variables", {})
        
        for block_name, block_data in data.get("blocks", {}).items():
            block = FCBlock(block_name)
            block.meta = block_data.get("meta", {})
            block.data = block_data.get("data", {})
            config.add_block(block)
        
        return config
    
    @classmethod
    def from_json(cls, json_str: str) -> "FCConfig":
        """Create a configuration from a JSON string."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __repr__(self) -> str:
        return f"FCConfig(blocks={len(self.blocks)}, variables={len(self.variables)})"