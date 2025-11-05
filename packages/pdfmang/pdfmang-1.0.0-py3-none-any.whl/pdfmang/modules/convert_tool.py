import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pdf2image import convert_from_path
from pdf2docx import Converter
import os
import traceback


class ConvertTool:
    def __init__(self, parent, status_var):
        self.parent = parent
        self.status_var = status_var
        self.pdf_path = None
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self.parent, text="PDF Conversion Tools", font=("Segoe UI", 14, "bold")).pack(pady=10)

        ttk.Button(self.parent, text="Select PDF", command=self.select_pdf).pack(pady=5)
        self.file_label = ttk.Label(self.parent, text="No file selected", wraplength=700)
        self.file_label.pack(pady=5)

        frame = ttk.Frame(self.parent)
        frame.pack(pady=10)

        ttk.Button(frame, text="Convert to Images (JPG/PNG)", command=self.convert_to_images).grid(row=0, column=0, padx=10)
        ttk.Button(frame, text="Convert to Word (DOCX)", command=self.convert_to_word).grid(row=0, column=1, padx=10)

    def select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            self.pdf_path = path
            self.file_label.config(text=f"Selected: {path}")
            self.status_var.set(f"Loaded PDF: {path}")

    def convert_to_images(self):
        if not self.pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return

        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if not output_dir:
            return

        try:
            self.status_var.set("Converting PDF to images...")
            images = convert_from_path(self.pdf_path)
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]

            for i, img in enumerate(images):
                output_path = os.path.join(output_dir, f"{base_name}_page_{i+1}.jpg")
                img.save(output_path, "JPEG")

            self.status_var.set("PDF successfully converted to images.")
            messagebox.showinfo("Success", "PDF converted to images successfully!")

        except Exception as e:
            error_msg = traceback.format_exc()
            messagebox.showerror("Error", f"Failed to convert:\n{error_msg}")
            self.status_var.set("Conversion failed.")

    def convert_to_word(self):
        if not self.pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Word File As",
            defaultextension=".docx",
            filetypes=[("Word Files", "*.docx")]
        )
        if not output_path:
            return

        try:
            self.status_var.set("Converting PDF to Word...")
            cv = Converter(self.pdf_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()

            self.status_var.set(f"PDF successfully converted to Word: {output_path}")
            messagebox.showinfo("Success", "PDF converted to Word successfully!")

        except Exception as e:
            error_msg = traceback.format_exc()
            messagebox.showerror("Error", f"Failed to convert:\n{error_msg}")
            self.status_var.set("Conversion failed.")
