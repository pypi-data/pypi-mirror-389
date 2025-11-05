import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
import os

class CompressTool:
    def __init__(self, parent, status_var):
        self.parent = parent
        self.status_var = status_var
        self.pdf_path = None
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self.parent, text="Compress PDF File", font=("Segoe UI", 14, "bold")).pack(pady=10)

        ttk.Button(self.parent, text="Select PDF", command=self.select_pdf).pack(pady=5)
        self.file_label = ttk.Label(self.parent, text="No file selected", wraplength=700)
        self.file_label.pack(pady=5)

        # Compression Quality Options
        ttk.Label(self.parent, text="Select Compression Quality:").pack(pady=5)
        self.quality = tk.StringVar(value="medium")

        options = [("Low (max compression)", "low"),
                   ("Medium (balanced)", "medium"),
                   ("High (better quality)", "high")]

        for text, value in options:
            ttk.Radiobutton(self.parent, text=text, value=value, variable=self.quality).pack(anchor="w", padx=50)

        ttk.Button(self.parent, text="Compress PDF", command=self.compress_pdf).pack(pady=10)

    def select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            self.pdf_path = path
            self.file_label.config(text=f"Selected: {path}")
            self.status_var.set(f"Loaded PDF: {os.path.basename(path)}")

    def compress_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Compressed PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not output_path:
            return

        try:
            quality = self.quality.get()
            zoom = {"low": 0.5, "medium": 0.7, "high": 0.9}[quality]

            doc = fitz.open(self.pdf_path)
            new_pdf = fitz.open()

            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                img_page = new_pdf.new_page(width=pix.width, height=pix.height)
                img_page.insert_image(img_page.rect, pixmap=pix)

            new_pdf.save(output_path, deflate=True)
            new_pdf.close()
            doc.close()

            original_size = os.path.getsize(self.pdf_path) / 1024
            compressed_size = os.path.getsize(output_path) / 1024
            reduction = ((original_size - compressed_size) / original_size) * 100

            self.status_var.set(f"Compressed by {reduction:.1f}%")
            messagebox.showinfo("Success", f"PDF compressed successfully!\nReduced by {reduction:.1f}%")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_var.set("Compression failed.")
