"""
Ingestion & Validation Pipeline for DeLTa
"""
from backend.ingestion.validator import ObservationValidator
from backend.ingestion.pipeline import IngestionPipeline

__all__ = ["ObservationValidator", "IngestionPipeline"]
