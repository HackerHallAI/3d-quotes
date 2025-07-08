"""
STL file processing service for the 3D Quotes application.

This module handles STL file validation, volume calculation, bounding box 
calculation, and HP MJF printer constraint validation.
"""
import asyncio
import logging
import os
from pathlib import Path

import numpy as np

try:
    from stl import mesh
except ImportError:
    raise ImportError("numpy-stl is required. Install with: pip install numpy-stl")

from config.settings import settings
from models.quote import BoundingBox, MaterialType, STLFile
from utils.validators import ProcessingError, ValidationError

logger = logging.getLogger(__name__)


class STLProcessor:
    """
    Service for processing STL files and calculating properties.
    """

    def __init__(self):
        self.printer_constraints = settings.printer_constraints
        self.temp_dir = Path(settings.temp_upload_dir)
        self.max_file_size = settings.max_file_size

    async def process_stl_file(
        self,
        file_path: str,
        material: MaterialType,
        quantity: int
    ) -> STLFile:
        """
        Process an STL file and return complete STL file data.
        
        Args:
            file_path: Path to the STL file
            material: Material type for the part
            quantity: Number of parts to print
            
        Returns:
            STLFile: Complete STL file data with calculated properties
            
        Raises:
            ValidationError: If file format is invalid or constraints are violated
            ProcessingError: If STL processing fails
        """
        # PATTERN: Always validate file format first
        if not file_path.lower().endswith('.stl'):
            raise ValidationError("Invalid file format - must be .stl")

        # Check if file exists
        if not os.path.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise ValidationError(f"File too large: {file_size} bytes (max: {self.max_file_size})")

        # CRITICAL: numpy-stl requires proper mesh loading
        try:
            mesh_data = mesh.Mesh.from_file(file_path)
            volume, center_of_gravity, inertia = mesh_data.get_mass_properties()
        except Exception as e:
            logger.error(f"STL processing failed for {file_path}: {e}")
            raise ProcessingError(f"STL processing failed: {e}")

        # GOTCHA: Volume calculation can be negative for inverted meshes
        volume = abs(volume)

        # PATTERN: Calculate bounding box from mesh vectors
        bounding_box = self._calculate_bounding_box(mesh_data)

        # CRITICAL: Validate HP MJF printer constraints
        self._validate_printer_constraints(bounding_box)

        # Check if mesh is watertight
        is_watertight = self._check_watertight(mesh_data)

        # Get filename from path
        filename = os.path.basename(file_path)

        # Create STL file data (unit_price and total_price will be calculated by pricing service)
        stl_file_data = STLFile(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            volume=volume,
            bounding_box=bounding_box,
            is_watertight=is_watertight,
            material=material,
            quantity=quantity,
            unit_price=0.0,  # Will be calculated by pricing service
            total_price=0.0   # Will be calculated by pricing service
        )

        logger.info(f"Successfully processed STL file: {filename}")
        return stl_file_data

    def _calculate_bounding_box(self, mesh_data: mesh.Mesh) -> BoundingBox:
        """
        Calculate bounding box from mesh vectors.
        
        Args:
            mesh_data: Loaded mesh data
            
        Returns:
            BoundingBox: Calculated bounding box
        """
        min_coords = mesh_data.min_
        max_coords = mesh_data.max_

        return BoundingBox(
            min_x=float(min_coords[0]),
            min_y=float(min_coords[1]),
            min_z=float(min_coords[2]),
            max_x=float(max_coords[0]),
            max_y=float(max_coords[1]),
            max_z=float(max_coords[2])
        )

    def _validate_printer_constraints(self, bounding_box: BoundingBox) -> None:
        """
        Validate that the part fits within HP MJF printer constraints.
        
        Args:
            bounding_box: Calculated bounding box
            
        Raises:
            ValidationError: If part exceeds printer build volume
        """
        dimensions = bounding_box.dimensions

        if dimensions[0] > self.printer_constraints["max_x"]:
            raise ValidationError(f"Part width ({dimensions[0]:.2f}mm) exceeds printer max X ({self.printer_constraints['max_x']}mm)")

        if dimensions[1] > self.printer_constraints["max_y"]:
            raise ValidationError(f"Part depth ({dimensions[1]:.2f}mm) exceeds printer max Y ({self.printer_constraints['max_y']}mm)")

        if dimensions[2] > self.printer_constraints["max_z"]:
            raise ValidationError(f"Part height ({dimensions[2]:.2f}mm) exceeds printer max Z ({self.printer_constraints['max_z']}mm)")

    def _check_watertight(self, mesh_data: mesh.Mesh) -> bool:
        """
        Check if the mesh is watertight (closed manifold).
        
        Args:
            mesh_data: Loaded mesh data
            
        Returns:
            bool: True if mesh appears to be watertight
        """
        # Basic check: ensure we have triangles
        if len(mesh_data.vectors) == 0:
            return False

        # More sophisticated watertight checking could be implemented here
        # For now, we'll do a basic check for degenerate triangles
        try:
            # Check for degenerate triangles (zero area)
            for triangle in mesh_data.vectors:
                # Calculate triangle area using cross product
                v1 = triangle[1] - triangle[0]
                v2 = triangle[2] - triangle[0]
                area = 0.5 * np.linalg.norm(np.cross(v1, v2))
                if area < 1e-10:  # Very small area indicates degenerate triangle
                    return False
            return True
        except Exception:
            return False

    async def validate_file_integrity(self, file_path: str) -> bool:
        """
        Validate STL file integrity without full processing.
        
        Args:
            file_path: Path to the STL file
            
        Returns:
            bool: True if file appears to be valid
        """
        try:
            # Check file format
            if not file_path.lower().endswith('.stl'):
                return False

            # Check file exists and is readable
            if not os.path.exists(file_path) or not os.access(file_path, os.R_OK):
                return False

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0 or file_size > self.max_file_size:
                return False

            # Try to load the mesh (quick check)
            mesh_data = mesh.Mesh.from_file(file_path)

            # Check if we have triangles
            if len(mesh_data.vectors) == 0:
                return False

            return True

        except Exception as e:
            logger.error(f"File integrity check failed for {file_path}: {e}")
            return False

    async def cleanup_file(self, file_path: str) -> None:
        """
        Clean up processed STL file.
        
        Args:
            file_path: Path to the file to clean up
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {e}")

    async def cleanup_files_after_delay(self, file_paths: list, delay_seconds: int = None) -> None:
        """
        Clean up multiple files after a delay.
        
        Args:
            file_paths: List of file paths to clean up
            delay_seconds: Delay before cleanup (default from settings)
        """
        if delay_seconds is None:
            delay_seconds = settings.file_cleanup_timeout

        await asyncio.sleep(delay_seconds)

        for file_path in file_paths:
            await self.cleanup_file(file_path)

    def get_supported_formats(self) -> list:
        """
        Get list of supported file formats.
        
        Returns:
            list: List of supported file extensions
        """
        return ['.stl']

    def get_printer_constraints(self) -> dict:
        """
        Get printer constraint information.
        
        Returns:
            dict: Printer constraints
        """
        return self.printer_constraints.copy()


# Global processor instance
stl_processor = STLProcessor()
