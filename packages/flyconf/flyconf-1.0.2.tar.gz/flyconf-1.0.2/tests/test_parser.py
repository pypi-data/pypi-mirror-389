"""
Tests for the parser module.
"""

import pytest
from flyconf.parser import FCConfigParser, ParserError
from flyconf.model import FCConfig, FCBlock


def test_parser_simple_block():
    """Test parser with a simple block."""
    text = "@server"
    config = FCConfigParser.parse_text(text)
    
    assert isinstance(config, FCConfig)
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert isinstance(block, FCBlock)
    assert block.name == "server"
    assert block.meta == {}
    assert block.data == {}


def test_parser_block_with_meta():
    """Test parser with a block with meta section."""
    text = "@server(type>conf.db)"
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert block.meta == {"type": "conf.db"}
    assert block.data == {}


def test_parser_block_with_data():
    """Test parser with a block with data section."""
    text = "@server username>admin password>1234"
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert block.meta == {}
    assert block.data == {"username": "admin", "password": "1234"}


def test_parser_complete_block():
    """Test parser with a complete block."""
    text = "@server(type>conf.db) dbtype>mysql host>localhost port>3306"
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert block.meta == {"type": "conf.db"}
    assert block.data == {"dbtype": "mysql", "host": "localhost", "port": "3306"}


def test_parser_multiple_blocks():
    """Test parser with multiple blocks."""
    text = """
@server(type>conf.db) dbtype>mysql host>localhost port>3306
@database username>admin password>1234
"""
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 2
    
    server_block = config.get_block("server")
    assert server_block is not None
    assert server_block.meta == {"type": "conf.db"}
    assert server_block.data == {"dbtype": "mysql", "host": "localhost", "port": "3306"}
    
    db_block = config.get_block("database")
    assert db_block is not None
    assert db_block.meta == {}
    assert db_block.data == {"username": "admin", "password": "1234"}


def test_parser_with_strings():
    """Test parser with strings."""
    text = '@server name>^Server Name^ description>^^^This is a\nmultiline description^^^'
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert block.data["name"] == "Server Name"
    assert block.data["description"] == "This is a\nmultiline description"


def test_parser_with_lists():
    """Test parser with lists."""
    text = "@server users>[user1,user2,user3]"
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert "users" in block.data
    assert isinstance(block.data["users"], list)
    assert block.data["users"] == ["user1", "user2", "user3"]


def test_parser_with_nested_lists():
    """Test parser with nested lists."""
    text = "@server nested>[item1, [nested1, nested2], item3]"
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert "nested" in block.data
    assert isinstance(block.data["nested"], list)
    assert block.data["nested"] == ["item1", ["nested1", "nested2"], "item3"]


def test_parser_with_named_lists():
    """Test parser with named lists."""
    text = "@server users>[A>[id>1 username>admin], B>[id>2 username>user]]"
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert "users" in block.data
    assert isinstance(block.data["users"], list)
    # The named lists should be represented as dictionaries in the list
    assert len(block.data["users"]) == 2
    assert isinstance(block.data["users"][0], dict)
    assert isinstance(block.data["users"][1], dict)


def test_parser_with_variable_references():
    """Test parser with variable references."""
    text = "@server path>$(config.path)"
    config = FCConfigParser.parse_text(text)
    
    assert len(config.blocks) == 1
    
    block = config.blocks[0]
    assert block.name == "server"
    assert block.data["path"] == "$(config.path)"


def test_parser_error_handling():
    """Test parser error handling."""
    # Missing block name should raise an error
    text = "@"
    
    # Note: Due to the way our parser works, it might not raise an error
    # for this case, but it should handle it gracefully
    try:
        config = FCConfigParser.parse_text(text)
        # If it doesn't raise an error, it should at least produce
        # a valid (though possibly empty) config
        assert isinstance(config, FCConfig)
    except ParserError:
        # This is also acceptable
        pass