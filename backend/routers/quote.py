"""
Quote router for the 3D Quotes application.

This module handles STL file uploads, quote calculations, and quote retrieval.
"""
import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from config.settings import settings
from models.quote import MaterialType, Quote
from schemas.quote import (
    PricingBreakdown,
    QuoteResponse,
    QuoteSummary,
)
from services.pricing_calculator import pricing_calculator
from services.stl_processor import stl_processor
from utils.validators import FileValidator, ProcessingError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for quotes (in production, use a database)
quotes_storage: Dict[str, Quote] = {}


def validate_upload_files(files: List[UploadFile]) -> None:
    """
    Validate uploaded files.
    
    Args:
        files: List of uploaded files
        
    Raises:
        HTTPException: If validation fails
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded"
        )

    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed"
        )

    for file in files:
        # Check file extension
        if not FileValidator.validate_filename(file.filename, settings.allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension for {file.filename}. Allowed: {settings.allowed_extensions}"
            )

        # Check file size (if available)
        if hasattr(file, 'size') and file.size:
            if not FileValidator.validate_file_size(file.size, settings.max_file_size):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} too large. Maximum size: {settings.max_file_size} bytes"
                )


async def save_uploaded_file(file: UploadFile, file_path: str) -> int:
    """
    Save uploaded file to temporary storage.
    
    Args:
        file: Uploaded file
        file_path: Path to save the file
        
    Returns:
        int: File size in bytes
    """
    file_size = 0

    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):  # Read in 8KB chunks
            await f.write(chunk)
            file_size += len(chunk)

    return file_size


@router.post("/upload", response_model=QuoteResponse)
async def upload_files_and_create_quote(
    files: List[UploadFile] = File(...),
    materials: List[str] = Form(...),
    quantities: List[int] = Form(...),
    customer_email: str = Form(None)
):
    """
    Upload STL files and create a quote.
    
    Args:
        files: List of STL files to upload
        materials: List of materials for each file
        quantities: List of quantities for each file
        customer_email: Optional customer email
        
    Returns:
        QuoteResponse: Created quote with pricing
    """
    try:
        # Validate inputs
        validate_upload_files(files)

        if len(files) != len(materials) or len(files) != len(quantities):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of files, materials, and quantities must match"
            )

        # Validate materials
        for material in materials:
            try:
                MaterialType(material)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid material type: {material}"
                )

        # Validate quantities
        for quantity in quantities:
            if quantity < 1 or quantity > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity must be between 1 and 1000, got: {quantity}"
                )

        # Process files
        processed_files = []
        file_paths = []

        for i, file in enumerate(files):
            try:
                # Generate unique filename
                file_id = str(uuid.uuid4())
                file_extension = Path(file.filename).suffix
                temp_filename = f"{file_id}{file_extension}"
                file_path = os.path.join(settings.temp_upload_dir, temp_filename)

                # Save file
                file_size = await save_uploaded_file(file, file_path)
                file_paths.append(file_path)

                # Process STL file
                material = MaterialType(materials[i])
                quantity = quantities[i]

                stl_file = await stl_processor.process_stl_file(file_path, material, quantity)

                # Calculate pricing for this file
                stl_file_with_pricing = pricing_calculator.calculate_file_pricing(stl_file)
                processed_files.append(stl_file_with_pricing)

                logger.info(f"Processed file {file.filename}: {quantity} × {material.value}")

            except ValidationError as e:
                # Clean up files on error
                for path in file_paths:
                    await stl_processor.cleanup_file(path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation error for {file.filename}: {e.message}"
                )
            except ProcessingError as e:
                # Clean up files on error
                for path in file_paths:
                    await stl_processor.cleanup_file(path)
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Processing error for {file.filename}: {e.message}"
                )

        # Calculate quote
        try:
            quote = pricing_calculator.calculate_quote_pricing(processed_files)
            quote.customer_email = customer_email

            # Store quote
            quotes_storage[quote.quote_id] = quote

            # Schedule file cleanup
            asyncio.create_task(
                stl_processor.cleanup_files_after_delay(file_paths)
            )

            logger.info(f"Created quote {quote.quote_id} with {len(processed_files)} files, total: ${quote.total}")

            return QuoteResponse.from_orm(quote)

        except ValidationError as e:
            # Clean up files on error
            for path in file_paths:
                await stl_processor.cleanup_file(path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing files"
        )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str):
    """
    Retrieve a quote by ID.
    
    Args:
        quote_id: Quote ID
        
    Returns:
        QuoteResponse: Quote details
    """
    quote = quotes_storage.get(quote_id)

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Check if quote is still valid
    if not quote.is_valid:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Quote has expired"
        )

    return QuoteResponse.from_orm(quote)


@router.get("/{quote_id}/breakdown", response_model=PricingBreakdown)
async def get_quote_breakdown(quote_id: str):
    """
    Get detailed pricing breakdown for a quote.
    
    Args:
        quote_id: Quote ID
        
    Returns:
        PricingBreakdown: Detailed pricing breakdown
    """
    quote = quotes_storage.get(quote_id)

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    breakdown = pricing_calculator.get_pricing_breakdown(quote)
    return PricingBreakdown(**breakdown)


@router.get("/", response_model=List[QuoteSummary])
async def list_quotes(
    customer_email: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List quotes with optional filtering.
    
    Args:
        customer_email: Filter by customer email
        limit: Maximum number of quotes to return
        offset: Number of quotes to skip
        
    Returns:
        List[QuoteSummary]: List of quote summaries
    """
    quotes = list(quotes_storage.values())

    # Filter by customer email if provided
    if customer_email:
        quotes = [q for q in quotes if q.customer_email == customer_email]

    # Sort by creation date (newest first)
    quotes.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    quotes = quotes[offset:offset + limit]

    # Convert to summary format
    summaries = []
    for quote in quotes:
        summary = QuoteSummary(
            quote_id=quote.quote_id,
            file_count=len(quote.files),
            total=quote.total,
            created_at=quote.created_at,
            expires_at=quote.expires_at,
            is_valid=quote.is_valid,
            customer_email=quote.customer_email
        )
        summaries.append(summary)

    return summaries


@router.post("/{quote_id}/update", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    file_updates: List[Dict[str, Any]]
):
    """
    Update quantities or materials for files in a quote.
    
    Args:
        quote_id: Quote ID
        file_updates: List of file updates
        
    Returns:
        QuoteResponse: Updated quote
    """
    quote = quotes_storage.get(quote_id)

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    if not quote.is_valid:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Quote has expired"
        )

    try:
        # Update files
        for update in file_updates:
            filename = update.get("filename")
            new_quantity = update.get("quantity")
            new_material = update.get("material")

            # Find file in quote
            file_found = False
            for file in quote.files:
                if file.filename == filename:
                    file_found = True

                    # Update quantity if provided
                    if new_quantity is not None:
                        if new_quantity < 1 or new_quantity > 1000:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Quantity must be between 1 and 1000 for {filename}"
                            )
                        file.quantity = new_quantity

                    # Update material if provided
                    if new_material is not None:
                        try:
                            file.material = MaterialType(new_material)
                        except ValueError:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid material type: {new_material}"
                            )

                    # Recalculate pricing for this file
                    pricing_calculator.calculate_file_pricing(file)
                    break

            if not file_found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File {filename} not found in quote"
                )

        # Recalculate quote totals
        updated_quote = pricing_calculator.calculate_quote_pricing(quote.files)
        updated_quote.quote_id = quote.quote_id
        updated_quote.customer_email = quote.customer_email
        updated_quote.created_at = quote.created_at

        # Update storage
        quotes_storage[quote_id] = updated_quote

        logger.info(f"Updated quote {quote_id}, new total: ${updated_quote.total}")

        return QuoteResponse.from_orm(updated_quote)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating quote {quote_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the quote"
        )


@router.delete("/{quote_id}")
async def delete_quote(quote_id: str):
    """
    Delete a quote.
    
    Args:
        quote_id: Quote ID
        
    Returns:
        dict: Success message
    """
    if quote_id not in quotes_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    del quotes_storage[quote_id]
    logger.info(f"Deleted quote {quote_id}")

    return {"message": "Quote deleted successfully"}


@router.get("/config/materials")
async def get_material_config():
    """
    Get material configuration.
    
    Returns:
        dict: Material rates and types
    """
    return {
        "materials": [
            {
                "type": "PA12_GREY",
                "name": "PA12 Grey",
                "rate_per_cm3": settings.material_rates["PA12_GREY"],
                "description": "Standard PA12 nylon material in grey"
            },
            {
                "type": "PA12_BLACK",
                "name": "PA12 Black",
                "rate_per_cm3": settings.material_rates["PA12_BLACK"],
                "description": "Standard PA12 nylon material in black"
            },
            {
                "type": "PA12_GB",
                "name": "PA12 Glass Bead",
                "rate_per_cm3": settings.material_rates["PA12_GB"],
                "description": "PA12 nylon with glass bead reinforcement"
            }
        ],
        "currency": settings.currency,
        "minimum_order": settings.minimum_order_usd
    }
