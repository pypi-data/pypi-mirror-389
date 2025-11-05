"""
Lexer for fc configuration files.
"""

from enum import Enum
from typing import List, Iterator, NamedTuple
import re


class TokenType(Enum):
    """Token types for fc configuration files."""
    AT = "@"  # @
    BLOCK_NAME = "BLOCK_NAME"  # Block name identifier
    LPAREN = "("  # (
    RPAREN = ")"  # )
    LBRACKET = "["  # [
    RBRACKET = "]"  # ]
    GT = ">"  # >
    CARET = "^"  # ^
    DOUBLE_CARET = "^^"  # ^^
    HASH = "#"  # #
    DOLLAR_PAREN = "$("  # $(
    IDENTIFIER = "IDENTIFIER"  # General identifier
    STRING = "STRING"  # String content
    COMMA = ","  # ,
    EQUALS = "="  # =
    NEWLINE = "NEWLINE"  # \n
    WHITESPACE = "WHITESPACE"  # Spaces, tabs
    EOF = "EOF"  # End of file


class Token(NamedTuple):
    """Represents a token with type, value, and position."""
    type: TokenType
    value: str
    line: int
    column: int


class LexerError(Exception):
    """Exception raised for lexer errors."""
    pass


class Lexer:
    """Lexer for fc configuration files."""
    
    def __init__(self, text: str):
        self.text: str = text
        self.pos: int = 0
        self.line: int = 1
        self.column: int = 1
        self.tokens: List[Token] = []
    
    def _current_char(self) -> str:
        """Get the current character."""
        if self.pos >= len(self.text):
            return '\0'
        return self.text[self.pos]
    
    def _peek_char(self, offset: int = 1) -> str:
        """Peek at the next character."""
        if self.pos + offset >= len(self.text):
            return '\0'
        return self.text[self.pos + offset]
    
    def _advance(self) -> None:
        """Advance the position."""
        if self._current_char() == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1
    
    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self._current_char().isspace() and self._current_char() != '\0':
            if self._current_char() == '\n':
                token = Token(TokenType.NEWLINE, '\n', self.line, self.column)
                self.tokens.append(token)
            self._advance()
    
    def _read_identifier(self) -> str:
        """Read an identifier."""
        start = self.pos
        while (self._current_char().isalnum() or 
               self._current_char() in ['_', '-', '.']) and \
              self._current_char() != '\0':
            self._advance()
        return self.text[start:self.pos]
    
    def _read_string(self, delimiter: str) -> str:
        """Read a string until the delimiter."""
        start = self.pos
        while self._current_char() != delimiter and self._current_char() != '\0':
            # Handle escaped characters
            if self._current_char() == '\\' and self._peek_char() != '\0':
                self._advance()
            self._advance()
        
        if self._current_char() == '\0':
            raise LexerError(f"Unterminated string at line {self.line}, column {self.column}")
        
        value = self.text[start:self.pos]
        # Skip the closing delimiter
        self._advance()
        return value
    
    def _read_multiline_string(self, delimiter: str) -> str:
        """Read a multiline string until the delimiter."""
        start = self.pos
        # Look for the closing delimiter (two consecutive ^)
        while not (self._current_char() == delimiter and 
                   self._peek_char() == delimiter) and \
              self._current_char() != '\0':
            # Handle escaped characters
            if self._current_char() == '\\' and self._peek_char() != '\0':
                self._advance()
            self._advance()
        
        if self._current_char() == '\0':
            raise LexerError(f"Unterminated multiline string at line {self.line}, column {self.column}")
        
        value = self.text[start:self.pos]
        # Skip the closing delimiters
        self._advance()  # Skip first ^
        self._advance()  # Skip second ^
        return value
    
    def _read_raw_string(self, delimiter: str) -> str:
        """Read a raw string until the delimiter."""
        start = self.pos
        # Look for the closing delimiter (three consecutive ^)
        while not (self._current_char() == delimiter and 
                   self._peek_char() == delimiter and 
                   self._peek_char(2) == delimiter) and \
              self._current_char() != '\0':
            self._advance()
        
        if self._current_char() == '\0':
            raise LexerError(f"Unterminated raw string at line {self.line}, column {self.column}")
        
        value = self.text[start:self.pos]
        # Skip the closing delimiters
        self._advance()  # Skip first ^
        self._advance()  # Skip second ^
        self._advance()  # Skip third ^
        return value
    
    def _skip_comment(self) -> None:
        """Skip a comment until end of line."""
        while self._current_char() != '\n' and self._current_char() != '\0':
            self._advance()
    
    def tokenize(self) -> List[Token]:
        """Tokenize the input text."""
        while self._current_char() != '\0':
            # Skip whitespace but capture newlines
            self._skip_whitespace()
            
            if self._current_char() == '\0':
                break
            
            # Handle comments
            if self._current_char() == '#':
                self._skip_comment()
                continue
            
            # Handle special tokens
            char = self._current_char()
            next_char = self._peek_char()
            next_next_char = self._peek_char(2)
            
            # Handle triple caret (raw string) (^^^)
            if char == '^' and next_char == '^' and next_next_char == '^':
                self._advance()
                self._advance()
                self._advance()
                # Read raw string
                string_value = self._read_raw_string('^')
                string_token = Token(TokenType.STRING, string_value, self.line, self.column)
                self.tokens.append(string_token)
                continue
            
            # Handle double caret (multiline string) (^^)
            if char == '^' and next_char == '^' and next_next_char != '^':
                self._advance()
                self._advance()
                # Read multiline string
                string_value = self._read_multiline_string('^')
                string_token = Token(TokenType.STRING, string_value, self.line, self.column)
                self.tokens.append(string_token)
                continue
            
            # Handle single caret (^)
            if char == '^':
                self._advance()
                # Read string
                string_value = self._read_string('^')
                string_token = Token(TokenType.STRING, string_value, self.line, self.column)
                self.tokens.append(string_token)
                continue
            
            # Handle other special tokens
            special_tokens = {
                '@': TokenType.AT,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                '>': TokenType.GT,
                ',': TokenType.COMMA,
                '=': TokenType.EQUALS,
                '#': TokenType.HASH,
            }
            
            # Handle $(
            if char == '$' and next_char == '(':
                token = Token(TokenType.DOLLAR_PAREN, '$(', self.line, self.column)
                self.tokens.append(token)
                self._advance()
                self._advance()
                continue
            
            # Handle other special tokens
            if char in special_tokens:
                token = Token(special_tokens[char], char, self.line, self.column)
                self.tokens.append(token)
                self._advance()
                continue
            
            # Handle identifiers
            if char.isalnum() or char == '_':
                value = self._read_identifier()
                token = Token(TokenType.IDENTIFIER, value, self.line, self.column)
                self.tokens.append(token)
                continue
            
            # Skip unknown characters
            self._advance()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens