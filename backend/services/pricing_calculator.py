"""
Pricing calculator service for the 3D Quotes application.

This module handles material rate calculations, quantity-based pricing,
shipping cost calculations, and markup calculations.
"""
import logging
from typing import Any, Dict, List, Tuple

from config.settings import settings
from models.quote import BoundingBox, MaterialType, Quote, ShippingSize, STLFile
from utils.validators import PricingValidator, ValidationError

logger = logging.getLogger(__name__)


class PricingCalculator:
    """
    Service for calculating pricing for STL files and quotes.
    """

    def __init__(self):
        self.material_rates = settings.material_rates
        self.shipping_costs = settings.shipping_costs
        self.shipping_thresholds = settings.shipping_thresholds
        self.minimum_order = settings.minimum_order_usd
        self.markup_percentage = settings.markup_percentage
        self.currency = settings.currency

    def calculate_material_cost(self, volume_mm3: float, material: MaterialType) -> float:
        """
        Calculate material cost based on volume and material type.
        
        Args:
            volume_mm3: Volume in cubic millimeters
            material: Material type
            
        Returns:
            float: Material cost in USD
        """
        # Convert volume from mm³ to cm³ (divide by 1000)
        volume_cm3 = volume_mm3 / 1000.0

        # Get material rate per cm³
        material_rate = self.material_rates.get(material.value, 0.0)

        # Calculate base material cost
        material_cost = volume_cm3 * material_rate

        logger.debug(f"Material cost calculation: {volume_cm3:.2f} cm³ × ${material_rate:.2f} = ${material_cost:.2f}")
        return material_cost

    def calculate_quantity_pricing(self, unit_cost: float, quantity: int) -> Tuple[float, float]:
        """
        Calculate quantity-based pricing with potential discounts.
        
        Args:
            unit_cost: Cost per unit
            quantity: Number of units
            
        Returns:
            tuple: (unit_price_with_discount, total_cost)
        """
        # For now, no quantity discounts - could be added later
        quantity_discount = 0.0

        # Future quantity discount logic could be:
        # if quantity >= 10:
        #     quantity_discount = 0.05  # 5% discount for 10+ units
        # elif quantity >= 5:
        #     quantity_discount = 0.025  # 2.5% discount for 5+ units

        discounted_unit_cost = unit_cost * (1 - quantity_discount)
        total_cost = discounted_unit_cost * quantity

        logger.debug(f"Quantity pricing: {quantity} × ${discounted_unit_cost:.2f} = ${total_cost:.2f}")
        return discounted_unit_cost, total_cost

    def calculate_markup(self, base_cost: float) -> float:
        """
        Calculate markup on base cost.
        
        Args:
            base_cost: Base cost before markup
            
        Returns:
            float: Markup amount
        """
        markup = base_cost * (self.markup_percentage / 100.0)
        logger.debug(f"Markup calculation: ${base_cost:.2f} × {self.markup_percentage}% = ${markup:.2f}")
        return markup

    def calculate_shipping_cost(self, total_volume_cm3: float, bounding_boxes: List[BoundingBox]) -> Tuple[float, ShippingSize]:
        """
        Calculate shipping cost based on volume and dimensions.
        
        Args:
            total_volume_cm3: Total volume in cubic centimeters
            bounding_boxes: List of bounding boxes for all parts
            
        Returns:
            tuple: (shipping_cost, shipping_size)
        """
        # Calculate maximum dimensions across all parts
        max_dimensions = self._calculate_max_dimensions(bounding_boxes)

        # Determine shipping size based on volume and dimensions
        shipping_size = self._determine_shipping_size(total_volume_cm3, max_dimensions)

        # Get shipping cost for the determined size
        shipping_cost = self.shipping_costs[shipping_size.value]

        logger.debug(f"Shipping calculation: {shipping_size.value} = ${shipping_cost:.2f}")
        return shipping_cost, shipping_size

    def _calculate_max_dimensions(self, bounding_boxes: List[BoundingBox]) -> Tuple[float, float, float]:
        """
        Calculate maximum dimensions across all bounding boxes.
        
        Args:
            bounding_boxes: List of bounding boxes
            
        Returns:
            tuple: (max_width, max_height, max_depth) in mm
        """
        if not bounding_boxes:
            return (0.0, 0.0, 0.0)

        max_width = max(bbox.dimensions[0] for bbox in bounding_boxes)
        max_height = max(bbox.dimensions[1] for bbox in bounding_boxes)
        max_depth = max(bbox.dimensions[2] for bbox in bounding_boxes)

        return (max_width, max_height, max_depth)

    def _determine_shipping_size(self, total_volume_cm3: float, max_dimensions: Tuple[float, float, float]) -> ShippingSize:
        """
        Determine shipping size based on volume and dimensions.
        
        Args:
            total_volume_cm3: Total volume in cubic centimeters
            max_dimensions: Maximum dimensions (width, height, depth) in mm
            
        Returns:
            ShippingSize: Determined shipping size
        """
        # Convert max dimension from mm to cm for comparison
        max_dimension_cm = max(max_dimensions) / 10.0

        # Determine size based on volume and maximum dimension
        if total_volume_cm3 <= self.shipping_thresholds["SMALL"] and max_dimension_cm <= 20:
            return ShippingSize.SMALL
        elif total_volume_cm3 <= self.shipping_thresholds["MEDIUM"] and max_dimension_cm <= 40:
            return ShippingSize.MEDIUM
        else:
            return ShippingSize.LARGE

    def calculate_file_pricing(self, stl_file: STLFile) -> STLFile:
        """
        Calculate pricing for a single STL file.
        
        Args:
            stl_file: STL file data without pricing
            
        Returns:
            STLFile: STL file data with calculated pricing
        """
        # Calculate material cost
        material_cost = self.calculate_material_cost(stl_file.volume, stl_file.material)

        # Apply markup to get unit price
        markup = self.calculate_markup(material_cost)
        unit_price_with_markup = material_cost + markup

        # Calculate quantity pricing
        unit_price, total_price = self.calculate_quantity_pricing(unit_price_with_markup, stl_file.quantity)

        # Round to 2 decimal places
        unit_price = round(unit_price, 2)
        total_price = round(total_price, 2)

        # Update the STL file with pricing
        stl_file.unit_price = unit_price
        stl_file.total_price = total_price

        logger.info(f"Calculated pricing for {stl_file.filename}: ${unit_price:.2f} × {stl_file.quantity} = ${total_price:.2f}")
        return stl_file

    def calculate_quote_pricing(self, files: List[STLFile]) -> Quote:
        """
        Calculate complete quote pricing for multiple files.
        
        Args:
            files: List of STL files with calculated individual pricing
            
        Returns:
            Quote: Complete quote with pricing breakdown
        """
        if not files:
            raise ValidationError("Cannot calculate pricing for empty file list")

        # Calculate subtotal from all files
        subtotal = sum(file.total_price for file in files)

        # Calculate shipping cost
        total_volume_cm3 = sum(file.volume / 1000.0 for file in files)  # Convert mm³ to cm³
        bounding_boxes = [file.bounding_box for file in files]
        shipping_cost, shipping_size = self.calculate_shipping_cost(total_volume_cm3, bounding_boxes)

        # Calculate total
        total = subtotal + shipping_cost

        # Round to 2 decimal places
        subtotal = round(subtotal, 2)
        shipping_cost = round(shipping_cost, 2)
        total = round(total, 2)

        # Validate minimum order
        if not PricingValidator.validate_minimum_order(total, self.minimum_order):
            raise ValidationError(f"Order total ${total:.2f} is below minimum order value ${self.minimum_order:.2f}")

        # Create quote
        quote = Quote(
            files=files,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            shipping_size=shipping_size,
            estimated_shipping_days=5  # Default shipping time
        )

        logger.info(f"Calculated quote: Subtotal ${subtotal:.2f} + Shipping ${shipping_cost:.2f} = Total ${total:.2f}")
        return quote

    def get_pricing_breakdown(self, quote: Quote) -> Dict[str, Any]:
        """
        Get detailed pricing breakdown for a quote.
        
        Args:
            quote: Quote to analyze
            
        Returns:
            dict: Detailed pricing breakdown
        """
        breakdown = {
            "currency": self.currency,
            "files": [],
            "subtotal_breakdown": {
                "material_cost": 0.0,
                "markup": 0.0,
                "subtotal": quote.subtotal
            },
            "shipping": {
                "size": quote.shipping_size.value,
                "cost": quote.shipping_cost,
                "estimated_days": quote.estimated_shipping_days
            },
            "total": quote.total,
            "meets_minimum": quote.total >= self.minimum_order
        }

        # Calculate material cost and markup for each file
        total_material_cost = 0.0
        total_markup = 0.0

        for file in quote.files:
            material_cost = self.calculate_material_cost(file.volume, file.material)
            markup = self.calculate_markup(material_cost)
            total_material_cost += material_cost * file.quantity
            total_markup += markup * file.quantity

            file_breakdown = {
                "filename": file.filename,
                "material": file.material.value,
                "quantity": file.quantity,
                "volume_cm3": round(file.volume / 1000.0, 2),
                "material_cost_per_unit": round(material_cost, 2),
                "markup_per_unit": round(markup, 2),
                "unit_price": file.unit_price,
                "total_price": file.total_price
            }
            breakdown["files"].append(file_breakdown)

        breakdown["subtotal_breakdown"]["material_cost"] = round(total_material_cost, 2)
        breakdown["subtotal_breakdown"]["markup"] = round(total_markup, 2)

        return breakdown

    def get_material_rates(self) -> Dict[str, float]:
        """
        Get current material rates.
        
        Returns:
            dict: Material rates per cm³
        """
        return self.material_rates.copy()

    def get_shipping_info(self) -> Dict[str, Any]:
        """
        Get shipping information.
        
        Returns:
            dict: Shipping costs and thresholds
        """
        return {
            "costs": self.shipping_costs.copy(),
            "thresholds": self.shipping_thresholds.copy(),
            "currency": self.currency
        }


# Global calculator instance
pricing_calculator = PricingCalculator()
