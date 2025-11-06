import json
import logging
from pathlib import Path
from typing import List

import yaml

# MAKE SURE THIS IMPORT IS PRESENT
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import OcrOptions
from docling.datamodel.pipeline_options import PipelineOptions
from docling.document_converter import DocumentConverter, FormatOption
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

_log = logging.getLogger(__name__)


def process_documents(
    input_paths: List[Path], output_dir: Path, ocr_options: OcrOptions
):
    """Processes documents using a custom-configured DocumentConverter."""

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    pipeline_opts_with_ocr = PipelineOptions(ocr_options=ocr_options)

    doc_converter = DocumentConverter(
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.IMAGE,
            InputFormat.DOCX,
            InputFormat.CSV,
            InputFormat.XLSX,
        ],
        format_options={
            InputFormat.PDF: FormatOption(
                pipeline_cls=StandardPdfPipeline,
                backend=PyPdfiumDocumentBackend,
                pipeline_options=pipeline_opts_with_ocr,
            ),
            # --- THIS IS THE CORRECTED SECTION ---
            InputFormat.IMAGE: FormatOption(
                pipeline_cls=SimplePipeline,
                # THIS IS THE LINE THAT MUST BE ADDED
                backend=DoclingParseV4DocumentBackend,
                pipeline_options=pipeline_opts_with_ocr,
            ),
        },
    )

    _log.info(f"Starting conversion for {len(input_paths)} files...")
    conv_results = doc_converter.convert_all(input_paths)

    for res in conv_results:
        if res.errors:
            _log.error(f"Failed to convert {res.input.file.name}: {res.error}")
            continue

        base_name = res.input.file.stem
        print(f"Successfully processed: {res.input.file.name}")

        md_path = output_dir / f"{base_name}.md"
        with md_path.open("w", encoding="utf-8") as fp:
            fp.write(res.document.export_to_markdown())
        print(f"   -> Saved Markdown to: {md_path}")

        json_path = output_dir / f"{base_name}.json"
        with json_path.open("w", encoding="utf-8") as fp:
            fp.write(json.dumps(res.document.export_to_dict(), indent=2))
        print(f"   -> Saved JSON to: {json_path}")

        yaml_path = output_dir / f"{base_name}.yaml"
        with yaml_path.open("w", encoding="utf-8") as fp:
            fp.write(yaml.safe_dump(res.document.export_to_dict(), allow_unicode=True))
        print(f"   -> Saved YAML to: {yaml_path}")