"""
Content analyzer for categorizing clipboard content
"""
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class ContentAnalyzer:
    """Analyzes and categorizes clipboard content"""
    
    # Regex patterns for content detection
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Common code patterns
    CODE_PATTERNS = [
        re.compile(r'(def|class|function|var|let|const|import|from)\s+\w+'),
        re.compile(r'[{}\[\]();].*[{}\[\]();]'),  # Multiple brackets/braces
        re.compile(r'(if|for|while|switch|try|catch)\s*\('),
        re.compile(r'=>|->|\|\||&&'),  # Arrow functions, logical operators
    ]
    
    # File path patterns
    FILE_PATH_PATTERN = re.compile(
        r'(?:[a-zA-Z]:\\|/)?(?:[\w\-]+[/\\])+[\w\-\.]+\.\w+'
    )
    
    # Credit card pattern (basic)
    CREDIT_CARD_PATTERN = re.compile(
        r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
    )
    
    # Password-like patterns
    PASSWORD_PATTERN = re.compile(
        r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}'
    )
    
    def __init__(self):
        """Initialize content analyzer"""
        pass
    
    def analyze(self, content: str) -> Dict[str, Any]:
        """Analyze content and return categorization
        
        Args:
            content: Content to analyze
            
        Returns:
            Dict with content_type, is_sensitive, and metadata
        """
        if not content or len(content.strip()) == 0:
            return {
                'content_type': 'empty',
                'is_sensitive': False,
                'metadata': {}
            }
        
        # Check for sensitive content first
        is_sensitive = self._is_sensitive(content)
        
        # Determine content type
        content_type = self._determine_type(content)
        
        # Extract metadata
        metadata = self._extract_metadata(content, content_type)
        
        return {
            'content_type': content_type,
            'is_sensitive': is_sensitive,
            'metadata': metadata
        }
    
    def _determine_type(self, content: str) -> str:
        """Determine the type of content
        
        Args:
            content: Content to analyze
            
        Returns:
            Content type string
        """
        content_lower = content.lower()
        
        # Check for URLs
        if self.URL_PATTERN.search(content):
            return 'url'
        
        # Check for emails
        if self.EMAIL_PATTERN.search(content):
            return 'email'
        
        # Check for code
        if self._is_code(content):
            return 'code'
        
        # Check for file paths
        if self.FILE_PATH_PATTERN.search(content):
            return 'file_path'
        
        # Check for numbers (could be phone, ID, etc.)
        if content.strip().replace('-', '').replace(' ', '').isdigit():
            return 'number'
        
        # Check for JSON
        if self._is_json_like(content):
            return 'json'
        
        # Check for markdown/formatted text
        if self._is_markdown(content):
            return 'markdown'
        
        # Default to plain text
        return 'text'
    
    def _is_code(self, content: str) -> bool:
        """Check if content looks like code
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be code
        """
        # Count how many code patterns match
        matches = sum(1 for pattern in self.CODE_PATTERNS if pattern.search(content))
        
        # If multiple patterns match, likely code
        if matches >= 2:
            return True
        
        # Check for high density of special characters
        special_chars = sum(1 for c in content if c in '{}[]();=<>+-*/%&|')
        if len(content) > 0 and special_chars / len(content) > 0.1:
            return True
        
        return False
    
    def _is_json_like(self, content: str) -> bool:
        """Check if content looks like JSON
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be JSON
        """
        content = content.strip()
        return (
            (content.startswith('{') and content.endswith('}')) or
            (content.startswith('[') and content.endswith(']'))
        ) and '"' in content
    
    def _is_markdown(self, content: str) -> bool:
        """Check if content looks like Markdown
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be Markdown
        """
        markdown_indicators = [
            r'^#{1,6}\s',  # Headers
            r'\*\*.*\*\*',  # Bold
            r'\*.*\*',  # Italic
            r'^\s*[-*+]\s',  # Lists
            r'^\s*\d+\.\s',  # Numbered lists
            r'\[.*\]\(.*\)',  # Links
        ]
        
        return any(re.search(pattern, content, re.MULTILINE) 
                  for pattern in markdown_indicators)
    
    def _is_sensitive(self, content: str) -> bool:
        """Check if content might be sensitive
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears sensitive
        """
        # Check for credit card numbers
        if self.CREDIT_CARD_PATTERN.search(content):
            return True
        
        # Check for password-like strings
        if self.PASSWORD_PATTERN.search(content):
            return True
        
        # Check for common sensitive keywords
        sensitive_keywords = [
            'password', 'passwd', 'pwd', 'secret', 'token', 'api_key',
            'apikey', 'private_key', 'privatekey', 'ssn', 'social security'
        ]
        
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in sensitive_keywords):
            return True
        
        return False
    
    def _extract_metadata(self, content: str, content_type: str) -> Dict[str, Any]:
        """Extract metadata based on content type
        
        Args:
            content: Content to analyze
            content_type: Type of content
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'length': len(content),
            'lines': content.count('\n') + 1,
            'words': len(content.split())
        }
        
        if content_type == 'url':
            urls = self.URL_PATTERN.findall(content)
            if urls:
                parsed = urlparse(urls[0])
                metadata['domain'] = parsed.netloc
                metadata['scheme'] = parsed.scheme
        
        elif content_type == 'email':
            emails = self.EMAIL_PATTERN.findall(content)
            if emails:
                metadata['email'] = emails[0]
                metadata['domain'] = emails[0].split('@')[1]
        
        elif content_type == 'code':
            # Try to detect programming language
            metadata['language'] = self._detect_language(content)
        
        return metadata
    
    def _detect_language(self, content: str) -> Optional[str]:
        """Detect programming language from code
        
        Args:
            content: Code content
            
        Returns:
            Language name or None
        """
        language_patterns = {
            'python': [r'\bdef\s+\w+\s*\(', r'\bimport\s+\w+', r'\bclass\s+\w+:'],
            'javascript': [r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=', r'=>'],
            'java': [r'\bpublic\s+class\s+\w+', r'\bprivate\s+\w+\s+\w+'],
            'cpp': [r'#include\s*<', r'\bstd::', r'\bnamespace\s+\w+'],
            'go': [r'\bfunc\s+\w+\s*\(', r'\bpackage\s+\w+'],
            'rust': [r'\bfn\s+\w+\s*\(', r'\blet\s+mut\s+\w+'],
            'ruby': [r'\bdef\s+\w+', r'\bend\b', r'@\w+'],
            'php': [r'<\?php', r'\$\w+\s*='],
        }
        
        for language, patterns in language_patterns.items():
            if any(re.search(pattern, content) for pattern in patterns):
                return language
        
        return None
    
    def get_preview(self, content: str, max_length: int = 100) -> str:
        """Get a preview of content
        
        Args:
            content: Content to preview
            max_length: Maximum preview length
            
        Returns:
            Preview string
        """
        if len(content) <= max_length:
            return content
        
        # Try to break at word boundary
        preview = content[:max_length]
        last_space = preview.rfind(' ')
        
        if last_space > max_length * 0.8:  # If space is reasonably close to end
            preview = preview[:last_space]
        
        return preview + '...'

