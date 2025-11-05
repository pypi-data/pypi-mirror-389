import sys
from pathlib import Path
import pytest
from bs4 import BeautifulSoup

# Ensure we use local fa2svg module
sys.path.insert(0, str(Path(__file__).parent.parent))
from fa2svg.converter import to_inline_png_img, to_inline_svg, revert_to_original_fa


class TestConverter:
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML with Font Awesome icons for testing"""
        return '''
        <div>
            <p><i class="fas fa-envelope"></i> Email</p>
            <p><span class="far fa-star"></span> Star</p>
            <p><i class="fa-solid fa-phone"></i> Phone (new syntax)</p>
            <p><i class="fab fa-github"></i> GitHub</p>
        </div>
        '''
    
    def test_to_inline_png_img_converts_icons(self, sample_html):
        """Test that PNG conversion works and creates img tags"""
        result = to_inline_png_img(sample_html)
        soup = BeautifulSoup(result, 'html.parser')
        
        # Should have 4 img tags (one for each FA icon)
        img_tags = soup.find_all('img')
        assert len(img_tags) == 4
        
        # All img tags should have data URI src
        for img in img_tags:
            assert img.get('src', '').startswith('data:image/png;base64,')
            assert 'height:' in img.get('style', '')
            assert 'vertical-align:-0.125em' in img.get('style', '')
    
    def test_to_inline_png_img_preserves_title(self, sample_html):
        """Test that title attribute contains FA marker"""
        result = to_inline_png_img(sample_html)
        soup = BeautifulSoup(result, 'html.parser')
        
        img_tags = soup.find_all('img')
        for img in img_tags:
            title = img.get('title', '')
            assert title.startswith('__FA__')
    
    def test_to_inline_svg_converts_icons(self, sample_html):
        """Test that SVG conversion works"""
        result = to_inline_svg(sample_html)
        soup = BeautifulSoup(result, 'html.parser')
        
        # Should have 4 svg tags
        svg_tags = soup.find_all('svg')
        assert len(svg_tags) == 4
        
        # All SVG tags should have proper attributes
        for svg in svg_tags:
            assert svg.get('fill') in ['currentColor', '#000']
            assert 'vertical-align:-0.125em' in svg.get('style', '')
    
    def test_revert_to_original_fa(self, sample_html):
        """Test that reversion works correctly"""
        # First convert to PNG
        converted = to_inline_png_img(sample_html)
        
        # Then revert back
        reverted = revert_to_original_fa(converted)
        soup = BeautifulSoup(reverted, 'html.parser')
        
        # Should have original FA elements back
        fa_elements = soup.find_all(['i', 'span'])
        fa_count = sum(1 for el in fa_elements if any(cls.startswith('fa') for cls in el.get('class', [])))
        assert fa_count == 4
    
    def test_empty_html(self):
        """Test with empty HTML"""
        result = to_inline_png_img("")
        # Empty string returns empty string
        assert result == ""
    
    def test_html_without_fa_icons(self):
        """Test with HTML that has no FA icons"""
        html = "<p>Just regular text</p>"
        result = to_inline_png_img(html)
        soup = BeautifulSoup(result, 'html.parser')
        
        # Should have no img tags
        assert len(soup.find_all('img')) == 0
    
    def test_legacy_icon_names(self):
        """Test that legacy icon names are handled"""
        html = '<i class="fas fa-map-marker-alt"></i>'
        result = to_inline_png_img(html)
        soup = BeautifulSoup(result, 'html.parser')
        
        img_tags = soup.find_all('img')
        assert len(img_tags) == 1
        assert img_tags[0].get('src', '').startswith('data:image/png;base64,')


if __name__ == "__main__":
    pytest.main([__file__])