from typing import List, Dict, Any, Optional
from .lexer import Lexer, Token, TokenType
from .model import FCConfig, FCBlock


class ParserError(Exception):
    """Exception raised for parser errors."""
    pass


class FCConfigParser:
    """Parser for fc configuration files."""
    
    def __init__(self, text: str):
        self.lexer = Lexer(text)
        self.tokens: List[Token] = []
        self.pos: int = 0
        self.config: FCConfig = FCConfig()
    
    def _current_token(self) -> Token:
        """Get the current token."""
        if self.pos >= len(self.tokens):
            return Token(TokenType.EOF, '', 0, 0)
        return self.tokens[self.pos]
    
    def _peek_token(self, offset: int = 1) -> Token:
        """Peek at the next token."""
        if self.pos + offset >= len(self.tokens):
            return Token(TokenType.EOF, '', 0, 0)
        return self.tokens[self.pos + offset]
    
    def _consume_token(self) -> Token:
        """Consume the current token and advance."""
        token = self._current_token()
        self.pos += 1
        return token
    
    def _match_token(self, token_type: TokenType) -> bool:
        """Check if the current token matches the expected type."""
        if self._current_token().type == token_type:
            self._consume_token()
            return True
        return False
    
    def _expect_token(self, token_type: TokenType) -> Token:
        """Expect a specific token type or raise an error."""
        if self._current_token().type == token_type:
            return self._consume_token()
        raise ParserError(
            f"Expected token {token_type}, got {self._current_token().type} "
            f"at line {self._current_token().line}, column {self._current_token().column}"
        )
    
    def _parse_block_name(self) -> str:
        """Parse a block name."""
        token = self._expect_token(TokenType.IDENTIFIER)
        return token.value
    
    def _parse_key_value_list(self) -> Dict[str, Any]:
        """Parse a key-value list."""
        result = {}
        
        while self._current_token().type not in [TokenType.RPAREN, TokenType.RBRACKET, TokenType.EOF]:
            # Skip newlines
            if self._current_token().type == TokenType.NEWLINE:
                self._consume_token()
                continue
                
            # Check if we've reached the start of a new block
            if self._current_token().type == TokenType.AT:
                break
            
            # Check if the first token is a list (special case for lists without keys)
            if self._current_token().type == TokenType.LBRACKET:
                # This is a list without a key, which is not valid in our format
                raise ParserError(
                    f"Unexpected list at line {self._current_token().line}, column {self._current_token().column}. "
                    f"Lists must be associated with a key."
                )
                
            # Parse key
            key_token = self._expect_token(TokenType.IDENTIFIER)
            key = key_token.value
            
            # Check if there's a value (indicated by > or directly a list)
            if self._current_token().type == TokenType.GT:
                self._consume_token()  # Consume >
                # Parse value
                value = self._parse_value()
                result[key] = value
            elif self._current_token().type == TokenType.LBRACKET:
                # Direct list value without >
                value = self._parse_value()
                result[key] = value
            else:
                # No value, treat as a flag
                result[key] = True
            
            # Optional comma
            if self._current_token().type == TokenType.COMMA:
                self._consume_token()
                # Handle trailing comma
                if self._current_token().type in [TokenType.RPAREN, TokenType.RBRACKET, TokenType.EOF]:
                    break
        
        return result
    
    def _parse_value(self) -> Any:
        """Parse a value."""
        token = self._current_token()
        
        # Handle string
        if token.type == TokenType.STRING:
            return self._consume_token().value
        
        # Handle list
        if token.type == TokenType.LBRACKET:
            return self._parse_list()
        
        # Handle variable reference
        if token.type == TokenType.DOLLAR_PAREN:
            return self._parse_variable_reference()
        
        # Handle identifier (can be a simple value or part of a list)
        if token.type == TokenType.IDENTIFIER:
            return self._consume_token().value
        
        # Default - consume and return as string
        return self._consume_token().value
    
    def _parse_list_item(self) -> Dict[str, Any]:
        """Parse a single list item (object with key-value pairs)."""
        result = {}
        
        # Parse key-value pairs until we hit a comma, bracket, or EOF
        while self._current_token().type not in [TokenType.COMMA, TokenType.RBRACKET, TokenType.EOF]:
            # Skip newlines
            if self._current_token().type == TokenType.NEWLINE:
                self._consume_token()
                continue
            
            # Check if we've reached the start of a new block
            if self._current_token().type == TokenType.AT:
                break
                
            # Parse key
            key_token = self._expect_token(TokenType.IDENTIFIER)
            key = key_token.value
            
            # Check if there's a value (indicated by >)
            if self._current_token().type == TokenType.GT:
                self._consume_token()  # Consume >
                # Parse value
                value = self._parse_value()
                result[key] = value
            else:
                # No value, treat as a flag
                result[key] = True
        
        return result
    
    def _parse_list(self) -> List[Any]:
        """Parse a list."""
        # Expect [
        self._expect_token(TokenType.LBRACKET)
        
        items = []
        while self._current_token().type != TokenType.RBRACKET and \
              self._current_token().type != TokenType.EOF:
            
            # Skip newlines
            if self._current_token().type == TokenType.NEWLINE:
                self._consume_token()
                continue
            
            # Check if we've reached the start of a new block
            if self._current_token().type == TokenType.AT:
                break
            
            # Handle comma separator between list items
            if self._current_token().type == TokenType.COMMA:
                self._consume_token()
                continue
            
            # Check if this is the start of a list item (key-value pairs)
            if self._current_token().type == TokenType.IDENTIFIER:
                # Parse list item as an object
                item = self._parse_list_item()
                items.append(item)
            elif self._current_token().type == TokenType.RBRACKET:
                # End of list
                break
            else:
                # Unexpected token in list
                raise ParserError(
                    f"Unexpected token {self._current_token().type} in list "
                    f"at line {self._current_token().line}, column {self._current_token().column}"
                )
        
        # Expect ]
        self._expect_token(TokenType.RBRACKET)
        return items
    
    def _parse_variable_reference(self) -> str:
        """Parse a variable reference."""
        # Expect $(
        self._expect_token(TokenType.DOLLAR_PAREN)
        
        # Parse variable name
        var_name = ""
        while self._current_token().type != TokenType.EOF and \
              self._current_token().type != TokenType.RPAREN:
            var_name += self._consume_token().value
        
        # Expect )
        self._expect_token(TokenType.RPAREN)
        
        return f"$({var_name})"
    
    def _parse_meta_part(self) -> Dict[str, Any]:
        """Parse the meta part of a block."""
        # Expect (
        self._expect_token(TokenType.LPAREN)
        
        # Parse key-value list
        meta = self._parse_key_value_list()
        
        # Expect )
        self._expect_token(TokenType.RPAREN)
        
        return meta
    
    def _parse_data_part(self) -> Dict[str, Any]:
        """Parse the data part of a block."""
        # Parse key-value list directly (no braces)
        return self._parse_key_value_list()
    
    def _parse_block(self) -> FCBlock:
        """Parse a block."""
        # Expect @
        self._expect_token(TokenType.AT)
        
        # Parse block name
        block_name = self._parse_block_name()
        block = FCBlock(block_name)
        
        # Optional meta part
        if self._current_token().type == TokenType.LPAREN:
            block.meta = self._parse_meta_part()
        
        # Skip newlines before data part
        while self._current_token().type == TokenType.NEWLINE:
            self._consume_token()
        
        # Optional data part - check if the next token is an identifier (start of key-value pair)
        # Lists are not allowed directly in the data part without a key
        if self._current_token().type == TokenType.IDENTIFIER:
            block.data = self._parse_data_part()
        
        return block
    
    def parse(self) -> FCConfig:
        """Parse the entire configuration."""
        # Tokenize the input
        self.tokens = self.lexer.tokenize()
        
        # Parse blocks
        while self._current_token().type != TokenType.EOF:
            # Skip newlines
            if self._current_token().type == TokenType.NEWLINE:
                self._consume_token()
                continue
            
            # Parse block
            if self._current_token().type == TokenType.AT:
                block = self._parse_block()
                self.config.add_block(block)
            else:
                # Skip unknown tokens
                self._consume_token()
        
        return self.config
    
    @classmethod
    def parse_text(cls, text: str) -> FCConfig:
        """Parse configuration from text."""
        parser = cls(text)
        return parser.parse()
    
    @classmethod
    def parse_file(cls, file_path: str) -> FCConfig:
        """Parse configuration from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return cls.parse_text(text)