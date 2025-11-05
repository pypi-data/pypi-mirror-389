import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter

class SplitTool:
    def __init__(self, parent, status_var):
        self.parent = parent
        self.status_var = status_var
        self.pdf_path = None
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self.parent, text="Split PDF File", font=("Segoe UI", 14, "bold")).pack(pady=10)

        ttk.Button(self.parent, text="Select PDF", command=self.select_pdf).pack(pady=5)

        # Label to show selected file
        self.file_label = ttk.Label(self.parent, text="No file selected", wraplength=700)
        self.file_label.pack(pady=5)

        # Entry for page ranges
        range_frame = ttk.Frame(self.parent)
        range_frame.pack(pady=10)

        ttk.Label(range_frame, text="Enter page ranges (e.g., 1-3,5,7-9):").pack()
        self.range_entry = ttk.Entry(range_frame, width=50)
        self.range_entry.pack(pady=5)

        ttk.Button(self.parent, text="Split PDF", command=self.split_pdf).pack(pady=10)

    def select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            self.pdf_path = path
            self.file_label.config(text=f"Selected: {path}")
            self.status_var.set(f"Loaded PDF: {path}")

    def parse_ranges(self, text, total_pages):
        """Convert '1-3,5,8-10' into [1,2,3,5,8,9,10] (1-based indexing)"""
        pages = set()
        parts = text.split(',')
        for part in parts:
            if '-' in part:
                start, end = part.split('-')
                pages.update(range(int(start), int(end)+1))
            else:
                pages.add(int(part))
        # Clip invalid pages
        return [p for p in sorted(pages) if 1 <= p <= total_pages]

    def split_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return

        page_text = self.range_entry.get().strip()
        if not page_text:
            messagebox.showwarning("No Range", "Please enter page ranges to extract.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Split PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not output_path:
            return

        try:
            reader = PdfReader(self.pdf_path)
            total_pages = len(reader.pages)
            pages_to_extract = self.parse_ranges(page_text, total_pages)

            if not pages_to_extract:
                messagebox.showerror("Invalid Range", "No valid pages found in the given range.")
                return

            writer = PdfWriter()
            for p in pages_to_extract:
                writer.add_page(reader.pages[p-1])

            with open(output_path, "wb") as f:
                writer.write(f)

            self.status_var.set(f"Split PDF saved to {output_path}")
            messagebox.showinfo("Success", f"Extracted {len(pages_to_extract)} page(s).")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_var.set("Split failed.")
