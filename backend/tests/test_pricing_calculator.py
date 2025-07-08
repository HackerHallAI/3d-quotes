"""
Tests for pricing calculator service.
"""
from unittest.mock import Mock

import pytest

from services.pricing_calculator import PricingCalculator
from models.quote import BoundingBox, STLFile, MaterialType, ShippingSize


class TestPricingCalculator:
    """Test cases for pricing calculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = PricingCalculator()

    def test_calculate_material_cost_pa12_grey(self):
        """Test material cost calculation for PA12 Grey."""
        volume_mm3 = 10000.0  # mm³ (10 cm³)
        cost = self.calculator.calculate_material_cost(volume_mm3, MaterialType.PA12_GREY)

        expected = 10.0 * self.calculator.material_rates["PA12_GREY"]  # 10 cm³
        assert cost == expected
        assert cost > 0

    def test_calculate_material_cost_pa12_gb(self):
        """Test material cost calculation for PA12 Glass Filled."""
        volume_mm3 = 15000.0  # mm³ (15 cm³)
        cost = self.calculator.calculate_material_cost(volume_mm3, MaterialType.PA12_GB)

        expected = 15.0 * self.calculator.material_rates["PA12_GB"]  # 15 cm³
        assert cost == expected
        assert cost > 0

    def test_calculate_material_cost_unknown_material(self):
        """Test material cost calculation with unknown material type."""
        volume_mm3 = 10000.0
        # Create a mock material type that doesn't exist in rates
        class UnknownMaterial:
            value = "UNKNOWN_MATERIAL"
        
        cost = self.calculator.calculate_material_cost(volume_mm3, UnknownMaterial())
        assert cost == 0.0  # Should return 0 for unknown materials

    def test_calculate_material_cost_zero_volume(self):
        """Test material cost calculation with zero volume."""
        cost = self.calculator.calculate_material_cost(0.0, MaterialType.PA12_GREY)
        assert cost == 0.0

    def test_calculate_material_cost_negative_volume(self):
        """Test material cost calculation with negative volume."""
        # The current implementation doesn't validate negative volumes, it just calculates
        cost = self.calculator.calculate_material_cost(-1000.0, MaterialType.PA12_GREY)
        assert cost < 0  # Will be negative

    def test_calculate_quantity_pricing(self):
        """Test quantity-based pricing calculation."""
        unit_cost = 10.0
        quantity = 5
        
        unit_price, total_cost = self.calculator.calculate_quantity_pricing(unit_cost, quantity)
        
        # Currently no quantity discounts implemented
        assert unit_price == unit_cost
        assert total_cost == unit_cost * quantity

    def test_calculate_markup(self):
        """Test markup calculation."""
        base_cost = 100.0
        markup = self.calculator.calculate_markup(base_cost)
        
        expected_markup = base_cost * (self.calculator.markup_percentage / 100.0)
        assert markup == expected_markup
        assert markup > 0

    def test_calculate_shipping_cost(self):
        """Test shipping cost calculation."""
        # Create bounding boxes
        bbox = BoundingBox(
            min_x=0, max_x=100,  # 10cm
            min_y=0, max_y=100,  # 10cm  
            min_z=0, max_z=100   # 10cm
        )
        
        total_volume_cm3 = 50.0  # Small volume
        shipping_cost, shipping_size = self.calculator.calculate_shipping_cost(total_volume_cm3, [bbox])
        
        assert shipping_cost > 0
        assert shipping_size in [ShippingSize.SMALL, ShippingSize.MEDIUM, ShippingSize.LARGE]

    def test_get_material_rates(self):
        """Test getting material rates."""
        rates = self.calculator.get_material_rates()
        
        assert isinstance(rates, dict)
        assert "PA12_GREY" in rates
        assert "PA12_BLACK" in rates
        assert "PA12_GB" in rates
        assert all(rate > 0 for rate in rates.values())

    def test_get_shipping_info(self):
        """Test getting shipping information."""
        info = self.calculator.get_shipping_info()
        
        assert "costs" in info
        assert "thresholds" in info
        assert "currency" in info
        assert info["currency"] == self.calculator.currency


class TestPricingCalculatorIntegration:
    """Integration tests for pricing calculator with STL files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = PricingCalculator()

    def create_mock_stl_file(self, volume=50000.0, material=MaterialType.PA12_GREY, quantity=1):
        """Create a mock STL file for testing."""
        bbox = BoundingBox(
            min_x=0, max_x=100,
            min_y=0, max_y=100,
            min_z=0, max_z=100
        )
        
        return STLFile(
            filename="test.stl",
            file_size=1000,
            volume=volume,
            bounding_box=bbox,
            is_watertight=True,
            material=material,
            quantity=quantity,
            unit_price=0.0,  # Will be calculated
            total_price=0.0  # Will be calculated
        )

    def test_calculate_file_pricing(self):
        """Test calculating pricing for a single STL file."""
        stl_file = self.create_mock_stl_file()
        
        result = self.calculator.calculate_file_pricing(stl_file)
        
        assert result.unit_price > 0
        assert result.total_price > 0
        assert result.total_price == result.unit_price * result.quantity

    def test_calculate_quote_pricing_single_file(self):
        """Test calculating quote pricing for single file."""
        stl_file = self.create_mock_stl_file()
        stl_file = self.calculator.calculate_file_pricing(stl_file)
        
        quote = self.calculator.calculate_quote_pricing([stl_file])
        
        assert quote.subtotal == stl_file.total_price
        assert quote.shipping_cost > 0
        assert quote.total == quote.subtotal + quote.shipping_cost
        assert quote.shipping_size in [ShippingSize.SMALL, ShippingSize.MEDIUM, ShippingSize.LARGE]

    def test_calculate_quote_pricing_multiple_files(self):
        """Test calculating quote pricing for multiple files."""
        stl_file1 = self.create_mock_stl_file(volume=25000.0)
        stl_file2 = self.create_mock_stl_file(volume=30000.0, material=MaterialType.PA12_BLACK)
        
        # Calculate individual pricing
        stl_file1 = self.calculator.calculate_file_pricing(stl_file1)
        stl_file2 = self.calculator.calculate_file_pricing(stl_file2)
        
        quote = self.calculator.calculate_quote_pricing([stl_file1, stl_file2])
        
        expected_subtotal = stl_file1.total_price + stl_file2.total_price
        assert quote.subtotal == expected_subtotal
        assert quote.total > quote.subtotal  # Should include shipping

    def test_get_pricing_breakdown(self):
        """Test getting detailed pricing breakdown."""
        stl_file = self.create_mock_stl_file()
        stl_file = self.calculator.calculate_file_pricing(stl_file)
        quote = self.calculator.calculate_quote_pricing([stl_file])
        
        breakdown = self.calculator.get_pricing_breakdown(quote)
        
        assert "currency" in breakdown
        assert "files" in breakdown
        assert "subtotal_breakdown" in breakdown
        assert "shipping" in breakdown
        assert "total" in breakdown
        assert len(breakdown["files"]) == 1


if __name__ == "__main__":
    pytest.main([__file__])
