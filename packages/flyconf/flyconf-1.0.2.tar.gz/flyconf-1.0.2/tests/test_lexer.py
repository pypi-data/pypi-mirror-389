"""
Tests for the lexer module.
"""

import pytest
from flyconf.lexer import Lexer, TokenType


def test_lexer_simple_tokens():
    """Test lexer with simple tokens."""
    text = "@block_name"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    assert len(tokens) == 3  # @, block_name, EOF
    assert tokens[0].type == TokenType.AT
    assert tokens[0].value == "@"
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "block_name"
    assert tokens[2].type == TokenType.EOF


def test_lexer_with_meta():
    """Test lexer with meta section."""
    text = "@block_name(version>1.0)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    assert len(tokens) == 8  # @, block_name, (, version, >, 1.0, ), EOF
    assert tokens[0].type == TokenType.AT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "block_name"
    assert tokens[2].type == TokenType.LPAREN
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[3].value == "version"
    assert tokens[4].type == TokenType.GT
    assert tokens[5].type == TokenType.IDENTIFIER
    assert tokens[5].value == "1.0"
    assert tokens[6].type == TokenType.RPAREN
    assert tokens[7].type == TokenType.EOF


def test_lexer_with_strings():
    """Test lexer with strings."""
    text = '@block_name(key>^value^)'
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    assert len(tokens) == 8  # @, block_name, (, key, >, value, ), EOF
    assert tokens[0].type == TokenType.AT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "block_name"
    assert tokens[2].type == TokenType.LPAREN
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[3].value == "key"
    assert tokens[4].type == TokenType.GT
    assert tokens[5].type == TokenType.STRING
    assert tokens[5].value == "value"
    assert tokens[6].type == TokenType.RPAREN
    assert tokens[7].type == TokenType.EOF


def test_lexer_with_multiline_strings():
    """Test lexer with multiline strings."""
    text = '@block_name(key>^^^multiline\nstring^^^)'
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.AT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "block_name"
    assert tokens[2].type == TokenType.LPAREN
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[3].value == "key"
    assert tokens[4].type == TokenType.GT
    assert tokens[5].type == TokenType.STRING
    assert tokens[5].value == "multiline\nstring"
    assert tokens[6].type == TokenType.RPAREN
    assert tokens[7].type == TokenType.EOF


def test_lexer_with_comments():
    """Test lexer with comments."""
    text = '''@block_name
# This is a comment
(key>value)'''
    
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    # Comment should be skipped, so we should have:
    # @, block_name, NEWLINE, NEWLINE, (, key, >, value, ), EOF
    assert len(tokens) == 10
    assert tokens[0].type == TokenType.AT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "block_name"
    assert tokens[2].type == TokenType.NEWLINE
    assert tokens[3].type == TokenType.NEWLINE  # Empty line where comment was
    assert tokens[4].type == TokenType.LPAREN
    assert tokens[5].type == TokenType.IDENTIFIER
    assert tokens[5].value == "key"
    assert tokens[6].type == TokenType.GT
    assert tokens[7].type == TokenType.IDENTIFIER
    assert tokens[7].value == "value"
    assert tokens[8].type == TokenType.RPAREN


def test_lexer_with_lists():
    """Test lexer with lists."""
    text = '@block_name(list>type>item1,item2)'
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.AT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "block_name"
    assert tokens[2].type == TokenType.LPAREN
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[3].value == "list"
    assert tokens[4].type == TokenType.GT
    assert tokens[5].type == TokenType.IDENTIFIER
    assert tokens[5].value == "type"
    assert tokens[6].type == TokenType.GT
    assert tokens[7].type == TokenType.IDENTIFIER
    assert tokens[7].value == "item1"
    assert tokens[8].type == TokenType.COMMA
    assert tokens[9].type == TokenType.IDENTIFIER
    assert tokens[9].value == "item2"
    assert tokens[10].type == TokenType.RPAREN
    assert tokens[11].type == TokenType.EOF


def test_lexer_with_variable_references():
    """Test lexer with variable references."""
    text = '@block_name(key>$(variable))'
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.AT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].value == "block_name"
    assert tokens[2].type == TokenType.LPAREN
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[3].value == "key"
    assert tokens[4].type == TokenType.GT
    assert tokens[5].type == TokenType.DOLLAR_PAREN
    assert tokens[5].value == "$("
    assert tokens[6].type == TokenType.IDENTIFIER
    assert tokens[6].value == "variable"
    assert tokens[7].type == TokenType.RPAREN
    assert tokens[8].type == TokenType.RPAREN
    assert tokens[9].type == TokenType.EOF