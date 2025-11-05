"""
Tests for the model module.
"""

import pytest
from flyconf.model import FCBlock, FCConfig


def test_fc_block_creation():
    """Test FCBlock creation."""
    block = FCBlock("test")
    assert block.name == "test"
    assert block.meta == {}
    assert block.data == {}


def test_fc_block_repr():
    """Test FCBlock representation."""
    block = FCBlock("test")
    block.meta = {"version": "1.0"}
    block.data = {"key": "value"}
    
    repr_str = repr(block)
    assert "FCBlock" in repr_str
    assert "test" in repr_str


def test_fc_config_creation():
    """Test FCConfig creation."""
    config = FCConfig()
    assert config.blocks == []
    assert config.variables == {}


def test_fc_config_add_block():
    """Test adding blocks to FCConfig."""
    config = FCConfig()
    block = FCBlock("test")
    
    config.add_block(block)
    assert len(config.blocks) == 1
    assert config.blocks[0] == block


def test_fc_config_get_block():
    """Test getting blocks from FCConfig."""
    config = FCConfig()
    block = FCBlock("test")
    config.add_block(block)
    
    found_block = config.get_block("test")
    assert found_block == block
    
    not_found = config.get_block("nonexistent")
    assert not_found is None


def test_fc_config_to_dict():
    """Test converting FCConfig to dictionary."""
    config = FCConfig()
    config.variables = {"var1": "value1"}
    
    block = FCBlock("test")
    block.meta = {"version": "1.0"}
    block.data = {"key": "value"}
    config.add_block(block)
    
    result = config.to_dict()
    assert "variables" in result
    assert "blocks" in result
    assert result["variables"] == {"var1": "value1"}
    assert "test" in result["blocks"]
    assert result["blocks"]["test"]["meta"] == {"version": "1.0"}
    assert result["blocks"]["test"]["data"] == {"key": "value"}


def test_fc_config_to_json():
    """Test converting FCConfig to JSON."""
    config = FCConfig()
    config.variables = {"var1": "value1"}
    
    block = FCBlock("test")
    block.data = {"key": "value"}
    config.add_block(block)
    
    json_str = config.to_json()
    assert isinstance(json_str, str)
    assert "var1" in json_str
    assert "test" in json_str


def test_fc_config_from_dict():
    """Test creating FCConfig from dictionary."""
    data = {
        "variables": {"var1": "value1"},
        "blocks": {
            "test": {
                "meta": {"version": "1.0"},
                "data": {"key": "value"}
            }
        }
    }
    
    config = FCConfig.from_dict(data)
    assert config.variables == {"var1": "value1"}
    assert len(config.blocks) == 1
    
    block = config.get_block("test")
    assert block is not None
    assert block.meta == {"version": "1.0"}
    assert block.data == {"key": "value"}


def test_fc_config_from_json():
    """Test creating FCConfig from JSON."""
    json_str = '''{
  "variables": {
    "var1": "value1"
  },
  "blocks": {
    "test": {
      "meta": {
        "version": "1.0"
      },
      "data": {
        "key": "value"
      }
    }
  }
}'''
    
    config = FCConfig.from_json(json_str)
    assert config.variables == {"var1": "value1"}
    assert len(config.blocks) == 1
    
    block = config.get_block("test")
    assert block is not None
    assert block.meta == {"version": "1.0"}
    assert block.data == {"key": "value"}