# PDFUtil — All-in-One PDF Utility Suite

**PDFUtil** is a lightweight, open-source desktop tool built with **Python + Tkinter**, offering a complete suite of PDF management features — including merge, split, compress, encrypt/decrypt, and conversion to images or Word documents.

No coding needed — just install, run, and manage your PDFs effortlessly.

---

## Key Features

**Merge PDFs** — Combine multiple PDF files into one document.  
**Split PDFs** — Extract specific pages or ranges into a new PDF.  
**Encrypt / Decrypt PDFs** — Add or remove password protection securely.  
**Compress PDFs** — Reduce file size while maintaining readability.  
**Convert PDFs** —

- PDF ➜ JPG or PNG images
- PDF ➜ DOCX (Word file)

**Modern Interface** — Simple and clean Tkinter UI with themed styling.  
**Lightweight** — Runs offline and doesn’t require any paid tools.

---

## Installation

Install directly from **PyPI**:

```bash
pip install pdfutil
```

If you’re installing manually from source:

```bash
git clone https://github.com/yatinannam/pdfutil.git
cd pdfutil
pip install -r requirements.txt
```

---

## Usage

After installation, launch the app using:

```bash
pdfutil
```

This opens the graphical PDF Utility Suite window with all available tools.

---

## Dependencies

All dependencies are automatically installed via `pip`, but if you want to install manually:

```bash
pip install PyPDF2 pdf2image pdf2docx Pillow ttkthemes
```

Additional Requirement (for PDF → Image Conversion)
You’ll need Poppler installed on your system: https://github.com/oschwartz10612/poppler-windows/releases/

---

## Project Structure

```bash
pdfutil/
│
├── __init__.py
├── main.py
│
└── modules/
    ├── __init__.py
    ├── merge_tool.py
    ├── split_tool.py
    ├── compress_tool.py
    ├── encrypt_tool.py
    └── convert_tool.py
```

---

## Development Setup

If you want to contribute or test locally:

```bash
git clone https://github.com/YOUR_USERNAME/pdfutil.git
cd pdfutil
python -m venv venv
venv\Scripts\activate      # On Windows
source venv/bin/activate   # On macOS/Linux
pip install -e .
```

Run the tool:

```bash
pdfutil
```

---
