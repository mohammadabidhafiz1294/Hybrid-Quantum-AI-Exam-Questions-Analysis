"""Data loading service for historical exam data."""

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

from src.config import service_logger


class DataLoader:
    """Service for loading and validating historical exam data."""

    def __init__(self):
        """Initialize data loader."""
        self.data_cache = {}
        service_logger.info("DataLoader initialized")

    def load_csv_data(self, file_path: str) -> Dict[str, List[Tuple[int, int, int]]]:
        """
        Load historical exam data from CSV file.

        Expected CSV format:
        topic,year,frequency,total_questions

        Returns:
            Dict mapping topic names to list of (year, frequency, total_questions)
            tuples
        """
        data = {}
        file_path = Path(file_path)

        service_logger.info("Loading CSV data", file_path=str(file_path))

        if not file_path.exists():
            service_logger.error("Data file not found", file_path=str(file_path))
            raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                topic = row["topic"]
                year = int(row["year"])
                frequency = int(row["frequency"])
                total_questions = int(row["total_questions"])

                if topic not in data:
                    data[topic] = []

                data[topic].append((year, frequency, total_questions))

        # Sort data by year for each topic
        for topic in data:
            data[topic].sort(key=lambda x: x[0])

        self.data_cache = data
        service_logger.info("CSV data loaded successfully", topics_count=len(data))
        return data

    def load_json_data(self, file_path: str) -> Dict[str, List[Tuple[int, int, int]]]:
        """
        Load historical exam data from JSON file.

        Expected JSON format:
        {
            "topics": {
                "topic_name": [
                    {"year": 2020, "frequency": 25, "total_questions": 100},
                    ...
                ]
            }
        }
        """
        data = {}
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, "r") as jsonfile:
            json_data = json.load(jsonfile)

        if "topics" in json_data:
            for topic, records in json_data["topics"].items():
                data[topic] = []
                for record in records:
                    year = record["year"]
                    frequency = record["frequency"]
                    total_questions = record["total_questions"]
                    data[topic].append((year, frequency, total_questions))

                # Sort by year
                data[topic].sort(key=lambda x: x[0])

        self.data_cache = data
        return data

    def get_topic_frequencies(
        self, data: Dict[str, List[Tuple[int, int, int]]], topic: str
    ) -> List[float]:
        """
        Extract frequency percentages for a topic.

        Returns:
            List of frequency percentages over time
        """
        if topic not in data:
            return []

        frequencies = []
        for year, freq, total in data[topic]:
            percentage = (freq / total) * 100 if total > 0 else 0.0
            frequencies.append(percentage)

        return frequencies

    def validate_data(
        self, data: Dict[str, List[Tuple[int, int, int]]], min_years: int = 3
    ) -> List[str]:
        """
        Validate loaded data.

        Returns:
            List of validation error messages
        """
        errors = []

        if not data:
            errors.append("No data loaded")
            return errors

        for topic, records in data.items():
            if len(records) < min_years:
                errors.append(
                    f"Topic '{topic}' has only {len(records)} years of data "
                    f"(minimum {min_years} required)"
                )

            # Check for data consistency
            years = [year for year, _, _ in records]
            if len(set(years)) != len(years):
                errors.append(f"Topic '{topic}' has duplicate years")

            # Check for reasonable frequency values
            for year, freq, total in records:
                if freq < 0:
                    errors.append(f"Topic '{topic}' year {year}: negative frequency")
                if total <= 0:
                    errors.append(
                        f"Topic '{topic}' year {year}: invalid total questions"
                    )
                if freq > total:
                    errors.append(
                        f"Topic '{topic}' year {year}: frequency > total questions"
                    )

        return errors

    def get_available_topics(
        self, data: Dict[str, List[Tuple[int, int, int]]], min_years: int = 3
    ) -> List[Dict]:
        """
        Get list of topics with sufficient historical data.

        Returns:
            List of topic info dictionaries
        """
        topics = []

        for topic_name, records in data.items():
            if len(records) >= min_years:
                years = [year for year, _, _ in records]
                latest_year = max(years)
                topics.append(
                    {
                        "id": topic_name.lower().replace(" ", "-"),
                        "name": topic_name,
                        "years_available": len(records),
                        "latest_year": latest_year,
                    }
                )

        return topics
