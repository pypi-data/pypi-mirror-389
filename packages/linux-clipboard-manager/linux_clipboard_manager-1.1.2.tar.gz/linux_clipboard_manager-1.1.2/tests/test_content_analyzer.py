"""
Tests for ContentAnalyzer
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.content_analyzer import ContentAnalyzer


def test_url_detection():
    """Test URL detection"""
    analyzer = ContentAnalyzer()
    
    result = analyzer.analyze("https://www.example.com")
    assert result['content_type'] == 'url'
    assert 'domain' in result['metadata']
    assert result['metadata']['domain'] == 'www.example.com'


def test_email_detection():
    """Test email detection"""
    analyzer = ContentAnalyzer()
    
    result = analyzer.analyze("contact@example.com")
    assert result['content_type'] == 'email'
    assert 'email' in result['metadata']


def test_code_detection():
    """Test code detection"""
    analyzer = ContentAnalyzer()
    
    code = """
def hello_world():
    print("Hello, World!")
    return True
"""
    
    result = analyzer.analyze(code)
    assert result['content_type'] == 'code'
    assert result['metadata']['language'] == 'python'


def test_sensitive_content():
    """Test sensitive content detection"""
    analyzer = ContentAnalyzer()
    
    # Test password detection
    result = analyzer.analyze("password: MyP@ssw0rd123")
    assert result['is_sensitive'] == True
    
    # Test credit card detection
    result = analyzer.analyze("4532 1234 5678 9010")
    assert result['is_sensitive'] == True


def test_preview():
    """Test content preview"""
    analyzer = ContentAnalyzer()
    
    long_text = "A" * 200
    preview = analyzer.get_preview(long_text, max_length=50)
    
    assert len(preview) <= 53  # 50 + "..."
    assert preview.endswith("...")


def test_json_detection():
    """Test JSON detection"""
    analyzer = ContentAnalyzer()
    
    json_text = '{"name": "John", "age": 30}'
    result = analyzer.analyze(json_text)
    assert result['content_type'] == 'json'


def test_markdown_detection():
    """Test Markdown detection"""
    analyzer = ContentAnalyzer()
    
    markdown = """
# Header
This is **bold** text
- List item 1
- List item 2
"""
    
    result = analyzer.analyze(markdown)
    assert result['content_type'] == 'markdown'


if __name__ == "__main__":
    # Run tests
    test_url_detection()
    test_email_detection()
    test_code_detection()
    test_sensitive_content()
    test_preview()
    test_json_detection()
    test_markdown_detection()
    
    print("All tests passed! ✅")

