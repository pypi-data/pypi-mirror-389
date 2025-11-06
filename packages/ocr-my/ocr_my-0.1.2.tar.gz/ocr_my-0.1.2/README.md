# My OCR Tool

A versatile OCR and document processing command-line tool, built with Python and the `docling` library. It uses **RapidOCR** by default and also supports EasyOCR.

## Features

- Process various file types: PDF, PNG, JPG, DOCX, XLSX, CSV.
- Supports `rapidocr` (default) and `easyocr` engines, configurable via YAML files.
- Outputs processed documents into Markdown, JSON, and YAML formats.

## Installation

First, ensure you have Python 3.8+ installed.

You can install the tool from PyPI. The default engine, `rapidocr`, is included automatically.

```bash
pip install myocr-tool
```
### Test the Optional Engine (EasyOCR)
```bash
my-ocr-tool --ocr-engine easyocr "path/to/your/image.png"
```

### Test with a Configuration File
```bash
my-ocr-tool --config rapidocr_config.yaml "path/to/your/image.png"
```
