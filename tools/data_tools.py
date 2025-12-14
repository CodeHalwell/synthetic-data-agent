import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from io import StringIO

sys.path.append(str(Path(__file__).parent.parent))

from google.adk.tools import Tool

class DataAnalysisTools(Tool):
    """
    Tools for analyzing and summarizing synthetic data.
    
    Provides methods for statistical analysis, quality assessment,
    and data profiling of synthetic datasets.
    """
    
    def __init__(self):
        super().__init__(
            name="data_analysis_tools",
            description="Tools for analyzing and summarizing synthetic data, including statistical summaries, quality metrics, and data profiling",
        )

    def analyze_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the data and return a comprehensive summary.
        
        Args:
            data: The DataFrame to analyze
            
        Returns:
            Dictionary containing summary statistics, data info, missing values, and data types
        """
        # Capture info() output as string
        buffer = StringIO()
        data.info(buf=buffer)
        info_str = buffer.getvalue()
        
        return {
            "row_count": len(data),
            "column_count": len(data.columns),
            "summary": data.describe().to_dict() if len(data.select_dtypes(include=[np.number]).columns) > 0 else {},
            "head": data.head().to_dict('records'),
            "info": info_str,
            "missing_values": data.isnull().sum().to_dict(),
            "missing_percentage": (data.isnull().sum() / len(data) * 100).to_dict(),
            "data_types": {col: str(dtype) for col, dtype in data.dtypes.items()},
            "columns": list(data.columns),
        }
    
    def analyze_synthetic_data_quality(
        self, 
        data: pd.DataFrame, 
        topic_column: Optional[str] = "topic",
        sub_topic_column: Optional[str] = "sub_topic"
    ) -> Dict[str, Any]:
        """
        Analyze quality metrics specific to synthetic data generation.
        
        Args:
            data: The DataFrame containing synthetic data
            topic_column: Name of the topic column (default: "topic")
            sub_topic_column: Name of the sub_topic column (default: "sub_topic")
            
        Returns:
            Dictionary with quality metrics including diversity, coverage, and distribution
        """
        quality_metrics = {
            "total_records": len(data),
        }
        
        # Topic and sub-topic distribution
        if topic_column and topic_column in data.columns:
            topic_counts = data[topic_column].value_counts().to_dict()
            quality_metrics["topic_distribution"] = topic_counts
            quality_metrics["unique_topics"] = data[topic_column].nunique()
        
        if sub_topic_column and sub_topic_column in data.columns:
            sub_topic_counts = data[sub_topic_column].value_counts().to_dict()
            quality_metrics["sub_topic_distribution"] = sub_topic_counts
            quality_metrics["unique_sub_topics"] = data[sub_topic_column].nunique()
        
        # Difficulty distribution (if present)
        if "difficulty" in data.columns:
            difficulty_counts = data["difficulty"].value_counts().to_dict()
            quality_metrics["difficulty_distribution"] = difficulty_counts
        
        # Quality score analysis (if present)
        if "quality_score" in data.columns:
            quality_metrics["quality_score_stats"] = {
                "mean": float(data["quality_score"].mean()) if not data["quality_score"].isna().all() else None,
                "median": float(data["quality_score"].median()) if not data["quality_score"].isna().all() else None,
                "min": float(data["quality_score"].min()) if not data["quality_score"].isna().all() else None,
                "max": float(data["quality_score"].max()) if not data["quality_score"].isna().all() else None,
                "std": float(data["quality_score"].std()) if not data["quality_score"].isna().all() else None,
            }
        
        # Review status (if present)
        if "review_status" in data.columns:
            review_counts = data["review_status"].value_counts().to_dict()
            quality_metrics["review_status_distribution"] = review_counts
        
        return quality_metrics
    
    def get_text_statistics(
        self, 
        data: pd.DataFrame, 
        text_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze text statistics for text columns in the dataset.
        
        Useful for analyzing instruction, response, prompt, and other text fields.
        
        Args:
            data: The DataFrame to analyze
            text_columns: List of column names to analyze. If None, auto-detects text columns.
            
        Returns:
            Dictionary with text statistics (length, word count, etc.)
        """
        if text_columns is None:
            # Auto-detect text columns (object/string type columns)
            text_columns = [col for col in data.columns if data[col].dtype == 'object']
        
        text_stats = {}
        
        for col in text_columns:
            if col not in data.columns:
                continue
                
            # Convert to string and remove NaN
            text_series = data[col].astype(str).replace('nan', np.nan).dropna()
            
            if len(text_series) == 0:
                text_stats[col] = {"error": "No valid text data"}
                continue
            
            # Calculate statistics
            char_lengths = text_series.str.len()
            word_counts = text_series.str.split().str.len()
            
            text_stats[col] = {
                "mean_char_length": float(char_lengths.mean()),
                "median_char_length": float(char_lengths.median()),
                "min_char_length": int(char_lengths.min()),
                "max_char_length": int(char_lengths.max()),
                "mean_word_count": float(word_counts.mean()),
                "median_word_count": float(word_counts.median()),
                "min_word_count": int(word_counts.min()),
                "max_word_count": int(word_counts.max()),
                "non_empty_count": int((text_series != '').sum()),
                "empty_count": int((text_series == '').sum()),
            }
        
        return text_stats
    
    def compare_datasets(
        self, 
        dataset1: pd.DataFrame, 
        dataset2: pd.DataFrame,
        key_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare two datasets to identify differences and similarities.
        
        Useful for comparing synthetic data against reference data or
        comparing different versions of synthetic data.
        
        Args:
            dataset1: First DataFrame to compare
            dataset2: Second DataFrame to compare
            key_columns: Optional list of columns to use for comparison
            
        Returns:
            Dictionary with comparison metrics
        """
        comparison = {
            "dataset1_size": len(dataset1),
            "dataset2_size": len(dataset2),
            "size_difference": len(dataset1) - len(dataset2),
            "common_columns": list(set(dataset1.columns) & set(dataset2.columns)),
            "unique_to_dataset1": list(set(dataset1.columns) - set(dataset2.columns)),
            "unique_to_dataset2": list(set(dataset2.columns) - set(dataset1.columns)),
        }
        
        # Compare column statistics if columns match
        common_cols = comparison["common_columns"]
        if common_cols:
            comparison["column_statistics"] = {}
            for col in common_cols:
                if dataset1[col].dtype == dataset2[col].dtype:
                    if pd.api.types.is_numeric_dtype(dataset1[col]):
                        comparison["column_statistics"][col] = {
                            "dataset1_mean": float(dataset1[col].mean()) if not dataset1[col].isna().all() else None,
                            "dataset2_mean": float(dataset2[col].mean()) if not dataset2[col].isna().all() else None,
                        }
        
        return comparison
