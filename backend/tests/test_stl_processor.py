"""
Tests for STL file processing service.
"""
import os
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pytest

from services.stl_processor import STLProcessor
from models.quote import STLFile, MaterialType, BoundingBox
from utils.validators import ValidationError, ProcessingError


class TestSTLProcessor:
    """Test cases for STL file processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = STLProcessor()

    def test_create_simple_stl_mesh(self):
        """Test creating a simple STL mesh for testing."""
        # Create a simple cube mesh
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # bottom face
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]   # top face
        ])

        # Simple triangular faces (just a few for testing)
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # bottom
            [4, 6, 5], [4, 7, 6],  # top
            [0, 4, 5], [0, 5, 1],  # front
        ])

        return vertices, faces

    @patch('stl.mesh.Mesh.from_file')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @pytest.mark.asyncio
    async def test_process_stl_file_success(self, mock_getsize, mock_exists, mock_from_file):
        """Test successful STL file processing."""
        # Mock file system
        mock_exists.return_value = True
        mock_getsize.return_value = 1000

        # Mock mesh data
        mock_mesh = Mock()
        mock_mesh.vectors = np.array([
            [[0, 0, 0], [1, 0, 0], [0, 1, 0]],  # Triangle 1
            [[1, 0, 0], [1, 1, 0], [0, 1, 0]]   # Triangle 2
        ])
        mock_mesh.points = mock_mesh.vectors.reshape(-1, 3)
        # Mock get_mass_properties method to return (volume, center_of_gravity, inertia)
        mock_mesh.get_mass_properties.return_value = (100.0, np.array([0.5, 0.5, 0.5]), np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
        # Mock min_ and max_ properties for bounding box calculation
        mock_mesh.min_ = np.array([0, 0, 0])
        mock_mesh.max_ = np.array([1, 1, 1])
        mock_from_file.return_value = mock_mesh

        file_path = "test.stl"
        result = await self.processor.process_stl_file(file_path, MaterialType.PA12_GREY, 1)

        assert isinstance(result, STLFile)
        assert result.filename == "test.stl"
        assert result.file_size == 1000
        assert result.volume > 0
        assert result.bounding_box is not None
        assert result.is_watertight is not None
        assert result.material == MaterialType.PA12_GREY
        assert result.quantity == 1

    @pytest.mark.asyncio
    async def test_process_stl_file_not_found(self):
        """Test processing non-existent STL file."""
        with pytest.raises(ValidationError, match="File not found"):
            await self.processor.process_stl_file("nonexistent.stl", MaterialType.PA12_GREY, 1)

    @pytest.mark.asyncio
    async def test_process_stl_file_invalid_format(self):
        """Test processing file with invalid format."""
        with pytest.raises(ValidationError, match="Invalid file format"):
            await self.processor.process_stl_file("test.txt", MaterialType.PA12_GREY, 1)

    def test_calculate_bounding_box(self):
        """Test bounding box calculation."""
        mock_mesh = Mock()
        mock_mesh.points = np.array([
            [0, 0, 0], [1, 0, 0], [0, 1, 0],
            [1, 1, 1], [2, 2, 2]
        ])
        # Mock the min_ and max_ properties that the implementation uses
        mock_mesh.min_ = np.array([0, 0, 0])
        mock_mesh.max_ = np.array([2, 2, 2])

        bbox = self.processor._calculate_bounding_box(mock_mesh)

        assert bbox.min_x == 0.0
        assert bbox.max_x == 2.0
        assert bbox.min_y == 0.0
        assert bbox.max_y == 2.0
        assert bbox.min_z == 0.0
        assert bbox.max_z == 2.0

    def test_check_watertight_basic(self):
        """Test basic watertight check."""
        mock_mesh = Mock()
        mock_mesh.vectors = np.array([
            [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        ])

        is_watertight = self.processor._check_watertight(mock_mesh)
        assert isinstance(is_watertight, bool)

    def test_check_watertight_empty_mesh(self):
        """Test watertight check with empty mesh."""
        mock_mesh = Mock()
        mock_mesh.vectors = np.array([])

        is_watertight = self.processor._check_watertight(mock_mesh)
        assert is_watertight is False

    def test_check_watertight_degenerate_triangle(self):
        """Test watertight check with degenerate triangle."""
        mock_mesh = Mock()
        # Degenerate triangle (all points are the same)
        mock_mesh.vectors = np.array([
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        ])

        is_watertight = self.processor._check_watertight(mock_mesh)
        assert is_watertight is False

    @patch('os.path.exists')
    @patch('os.access')
    @patch('os.path.getsize')
    @patch('stl.mesh.Mesh.from_file')
    @pytest.mark.asyncio
    async def test_validate_file_integrity_success(self, mock_from_file, mock_getsize, mock_access, mock_exists):
        """Test successful file integrity validation."""
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_getsize.return_value = 1000
        
        mock_mesh = Mock()
        mock_mesh.vectors = np.array([
            [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        ])
        mock_from_file.return_value = mock_mesh

        result = await self.processor.validate_file_integrity("test.stl")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_file_integrity_invalid_format(self):
        """Test file integrity validation with invalid format."""
        result = await self.processor.validate_file_integrity("test.txt")
        assert result is False

    @patch('os.path.exists')
    @pytest.mark.asyncio
    async def test_validate_file_integrity_file_not_found(self, mock_exists):
        """Test file integrity validation with non-existent file."""
        mock_exists.return_value = False

        result = await self.processor.validate_file_integrity("nonexistent.stl")
        assert result is False

    def test_get_supported_formats(self):
        """Test getting supported file formats."""
        formats = self.processor.get_supported_formats()
        assert isinstance(formats, list)
        assert '.stl' in formats

    def test_get_printer_constraints(self):
        """Test getting printer constraints."""
        constraints = self.processor.get_printer_constraints()
        assert isinstance(constraints, dict)
        assert 'max_x' in constraints
        assert 'max_y' in constraints
        assert 'max_z' in constraints

    @patch('os.path.exists')
    @patch('os.remove')
    @pytest.mark.asyncio
    async def test_cleanup_file(self, mock_remove, mock_exists):
        """Test file cleanup."""
        mock_exists.return_value = True
        
        await self.processor.cleanup_file("test.stl")
        mock_remove.assert_called_once_with("test.stl")

    @patch('os.path.exists')
    @pytest.mark.asyncio
    async def test_cleanup_file_not_exists(self, mock_exists):
        """Test cleanup of non-existent file."""
        mock_exists.return_value = False
        
        # Should not raise an exception
        await self.processor.cleanup_file("nonexistent.stl")


if __name__ == "__main__":
    pytest.main([__file__])