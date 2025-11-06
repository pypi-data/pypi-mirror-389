import argparse
import logging
from pathlib import Path

import yaml

# Import the options classes directly from the docling library
from docling.datamodel.pipeline_options import EasyOcrOptions, RapidOcrOptions

from .processor import process_documents

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
_log = logging.getLogger(__name__)

def main():
    # ... (The rest of this file remains exactly the same as before) ...
    parser = argparse.ArgumentParser(
        description="A versatile OCR and document processing tool."
    )
    parser.add_argument(
        "input_files",
        metavar="FILE",
        type=str,
        nargs="+",
        help="Path to one or more input files.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output",
        help="The directory to save output files.",
    )
    parser.add_argument(
        "--config", type=str, help="Path to a YAML configuration file for OCR options."
    )
    parser.add_argument(
        "--ocr-engine",
        type=str,
        default="rapidocr",
        choices=["rapidocr", "easyocr"],
        help="Simple OCR engine selector (used if --config is not provided).",
    )

    args = parser.parse_args()

    ocr_options = None
    if args.config:
        _log.info(f"Loading OCR configuration from: {args.config}")
        config_path = Path(args.config)
        if not config_path.is_file():
            _log.error(f"Configuration file not found: {config_path}")
            return

        with config_path.open("r") as f:
            config_data = yaml.safe_load(f)

        kind = config_data.get("kind")
        if kind == "easyocr":
            ocr_options = EasyOcrOptions(**config_data)
        elif kind == "rapidocr":
            ocr_options = RapidOcrOptions(**config_data)
        else:
            _log.error(f"Unknown OCR 'kind' in config file: {kind}. Must be 'rapidocr' or 'easyocr'.")
            return
    else:
        _log.info(f"Using default settings for --ocr-engine: {args.ocr_engine}")
        if args.ocr_engine == "easyocr":
            ocr_options = EasyOcrOptions()
        else:  # Default
            ocr_options = RapidOcrOptions()

    input_paths = [Path(f) for f in args.input_files]
    output_path = Path(args.output_dir)
    valid_paths = [path for path in input_paths if path.exists()]

    if not valid_paths:
        logging.error("No valid input files found. Exiting.")
        return

    process_documents(valid_paths, output_path, ocr_options=ocr_options)
    logging.info("All files processed.")


if __name__ == "__main__":
    main()