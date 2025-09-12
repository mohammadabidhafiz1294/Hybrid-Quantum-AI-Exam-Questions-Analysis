"""CLI interface for VQE prediction system."""

import argparse
import json
import sys

from src.services.vqe_predictor import VQEPredictor, PredictionRequest
from src.services.data_loader import DataLoader


def predict_command(args):
    """Handle prediction command."""
    try:
        # Load data
        data_loader = DataLoader()
        if args.data_file.endswith(".csv"):
            raw_data = data_loader.load_csv_data(args.data_file)
        elif args.data_file.endswith(".json"):
            raw_data = data_loader.load_json_data(args.data_file)
        else:
            print("Error: Data file must be .csv or .json")
            return 1

        # Validate data
        errors = data_loader.validate_data(raw_data, args.min_years)
        if errors:
            print("Data validation errors:")
            for error in errors:
                print(f"  - {error}")
            return 1

        # Prepare historical data for prediction
        historical_data = {}
        for topic in args.topics:
            frequencies = data_loader.get_topic_frequencies(raw_data, topic)
            if frequencies:
                historical_data[topic] = frequencies

        if not historical_data:
            print("Error: No valid historical data found for requested topics")
            return 1

        # Create prediction request
        request = PredictionRequest(
            topics=args.topics,
            historical_years=args.historical_years,
            confidence_level=args.confidence,
            force_classical=args.force_classical,
        )

        # Initialize predictor and make predictions
        predictor = VQEPredictor()
        response = predictor.predict_topics(request, historical_data)

        # Display results
        print(f"\nPrediction Results (Execution time: {response.execution_time_ms}ms)")
        print(f"Fallback used: {response.fallback_used}")
        print("-" * 60)

        for prediction in response.predictions:
            print(f"Topic: {prediction.topic}")
            print(".4f")
            print(".4f")
            print(f"Trend: {prediction.trend}")
            print(f"Method: {prediction.method}")
            print("-" * 30)

        # Save results if requested
        if args.output:
            output_data = {
                "predictions": [
                    {
                        "topic": p.topic,
                        "importance": p.importance,
                        "confidence_interval": list(p.confidence_interval),
                        "trend": p.trend,
                        "method": p.method,
                    }
                    for p in response.predictions
                ],
                "execution_time_ms": response.execution_time_ms,
                "fallback_used": response.fallback_used,
            }

            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def list_topics_command(args):
    """Handle list topics command."""
    try:
        # Load data
        data_loader = DataLoader()
        if args.data_file.endswith(".csv"):
            raw_data = data_loader.load_csv_data(args.data_file)
        elif args.data_file.endswith(".json"):
            raw_data = data_loader.load_json_data(args.data_file)
        else:
            print("Error: Data file must be .csv or .json")
            return 1

        # Get available topics
        topics = data_loader.get_available_topics(raw_data, args.min_years)

        print(f"\nAvailable Topics (minimum {args.min_years} years of data):")
        print("-" * 50)

        for topic in topics:
            print(f"ID: {topic['id']}")
            print(f"Name: {topic['name']}")
            print(f"Years available: {topic['years_available']}")
            print(f"Latest year: {topic['latest_year']}")
            print("-" * 30)

        print(f"\nTotal topics: {len(topics)}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="VQE Exam Topic Prediction System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Predict topics using CSV data
  python -m src.cli.main predict quantum-mechanics linear-algebra \\
    --data-file data/exam_data.csv

  # List available topics
  python -m src.cli.main list-topics --data-file data/exam_data.csv

  # Force classical prediction
  python -m src.cli.main predict quantum-mechanics \\
    --data-file data/exam_data.csv --force-classical
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Predict topic importance")
    predict_parser.add_argument("topics", nargs="+", help="Topics to predict")
    predict_parser.add_argument(
        "--data-file",
        required=True,
        help="Path to historical data file (.csv or .json)",
    )
    predict_parser.add_argument(
        "--historical-years",
        type=int,
        default=5,
        help="Number of historical years to use",
    )
    predict_parser.add_argument(
        "--confidence", type=float, default=0.95, help="Confidence level (0-1)"
    )
    predict_parser.add_argument(
        "--force-classical", action="store_true", help="Force classical prediction"
    )
    predict_parser.add_argument(
        "--min-years", type=int, default=3, help="Minimum years of data required"
    )
    predict_parser.add_argument("--output", help="Output file for results (JSON)")

    # List topics command
    list_parser = subparsers.add_parser("list-topics", help="List available topics")
    list_parser.add_argument(
        "--data-file",
        required=True,
        help="Path to historical data file (.csv or .json)",
    )
    list_parser.add_argument(
        "--min-years", type=int, default=3, help="Minimum years of data required"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "predict":
        return predict_command(args)
    elif args.command == "list-topics":
        return list_topics_command(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
