"""
Tests for Cascade Executor

These tests demonstrate the testability of the cascade pattern,
showing how each component can be tested in isolation.
"""

import unittest
from unittest.mock import Mock, MagicMock
from src.cascade import CascadeExecutor, CascadeSelector, SelectorType
from src.detection_result import DetectionResult


class TestCascadeExecutor(unittest.TestCase):
    """Test cases for CascadeExecutor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_driver = Mock()
        self.context = {"driver": self.mock_driver}
    
    def test_cascade_primary_selector_succeeds(self):
        """Test that cascade stops at first successful selector."""
        # Create cascade with multiple selectors
        selectors = [
            CascadeSelector("//div[@id='primary']", SelectorType.XPATH, "Primary"),
            CascadeSelector("//div[@id='fallback']", SelectorType.XPATH, "Fallback"),
        ]
        cascade = CascadeExecutor(selectors)
        
        # Mock driver to return elements for primary selector
        mock_element = Mock()
        self.mock_driver.find_elements_by_xpath.return_value = [mock_element]
        
        # Execute cascade
        result = cascade.execute(self.context)
        
        # Should return elements from primary selector
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        # Should only call primary selector
        self.mock_driver.find_elements_by_xpath.assert_called_once_with("//div[@id='primary']")
    
    def test_cascade_fallback_selector_succeeds(self):
        """Test that cascade falls back when primary fails."""
        selectors = [
            CascadeSelector("//div[@id='primary']", SelectorType.XPATH, "Primary"),
            CascadeSelector("//div[@id='fallback']", SelectorType.XPATH, "Fallback"),
        ]
        cascade = CascadeExecutor(selectors)
        
        # Mock driver: primary fails, fallback succeeds
        self.mock_driver.find_elements_by_xpath.side_effect = [
            [],  # Primary returns empty
            [Mock()],  # Fallback returns element
        ]
        
        result = cascade.execute(self.context)
        
        # Should return elements from fallback
        self.assertIsNotNone(result)
        # Should have tried both selectors
        self.assertEqual(self.mock_driver.find_elements_by_xpath.call_count, 2)
    
    def test_cascade_all_selectors_fail(self):
        """Test that cascade returns None when all selectors fail."""
        selectors = [
            CascadeSelector("//div[@id='primary']", SelectorType.XPATH, "Primary"),
            CascadeSelector("//div[@id='fallback']", SelectorType.XPATH, "Fallback"),
        ]
        cascade = CascadeExecutor(selectors)
        
        # Mock driver: all selectors return empty
        self.mock_driver.find_elements_by_xpath.return_value = []
        
        result = cascade.execute(self.context)
        
        # Should return None
        self.assertIsNone(result)
        # Should have tried all selectors
        self.assertEqual(self.mock_driver.find_elements_by_xpath.call_count, 2)
    
    def test_cascade_text_selector(self):
        """Test that text-based selector works."""
        selectors = [
            CascadeSelector("target text", SelectorType.TEXT, "Text search"),
        ]
        cascade = CascadeExecutor(selectors)
        
        # Mock driver with page source containing target text
        self.mock_driver.page_source = "Some content with target text in it"
        
        result = cascade.execute(self.context)
        
        # Should return True for text match
        self.assertTrue(result)
    
    def test_cascade_no_driver(self):
        """Test that cascade handles missing driver gracefully."""
        selectors = [
            CascadeSelector("//div", SelectorType.XPATH, "Test"),
        ]
        cascade = CascadeExecutor(selectors)
        
        # Context without driver
        context_no_driver = {}
        
        result = cascade.execute(context_no_driver)
        
        # Should return None gracefully
        self.assertIsNone(result)
    
    def test_cascade_selector_exception_handling(self):
        """Test that cascade continues on selector exceptions."""
        selectors = [
            CascadeSelector("//div[@id='primary']", SelectorType.XPATH, "Primary"),
            CascadeSelector("//div[@id='fallback']", SelectorType.XPATH, "Fallback"),
        ]
        cascade = CascadeExecutor(selectors)
        
        # Mock driver: primary raises exception, fallback succeeds
        self.mock_driver.find_elements_by_xpath.side_effect = [
            Exception("Selector failed"),
            [Mock()],
        ]
        
        result = cascade.execute(self.context)
        
        # Should still return result from fallback
        self.assertIsNotNone(result)
        # Should have tried both (exception caught and continued)
        self.assertEqual(self.mock_driver.find_elements_by_xpath.call_count, 2)


if __name__ == "__main__":
    unittest.main()

