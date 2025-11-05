import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter


class EncryptTool:
    def __init__(self, parent, status_var):
        self.parent = parent
        self.status_var = status_var
        self.pdf_path = None
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self.parent, text="Encrypt / Decrypt PDF", font=("Segoe UI", 14, "bold")).pack(pady=10)

        ttk.Button(self.parent, text="Select PDF", command=self.select_pdf).pack(pady=5)
        self.file_label = ttk.Label(self.parent, text="No file selected", wraplength=700)
        self.file_label.pack(pady=5)

        # Password Entry
        ttk.Label(self.parent, text="Enter Password:").pack(pady=5)
        self.password_entry = ttk.Entry(self.parent, show="*", width=40)
        self.password_entry.pack(pady=5)

        # Action Buttons
        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Encrypt PDF", command=self.encrypt_pdf).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Decrypt PDF", command=self.decrypt_pdf).grid(row=0, column=1, padx=5)

    def select_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            self.pdf_path = path
            self.file_label.config(text=f"Selected: {path}")
            self.status_var.set(f"Loaded PDF: {path}")

    def encrypt_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return

        password = self.password_entry.get().strip()
        if not password:
            messagebox.showwarning("No Password", "Please enter a password to encrypt the PDF.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Encrypted PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not output_path:
            return

        try:
            reader = PdfReader(self.pdf_path)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            writer.encrypt(password)

            with open(output_path, "wb") as f:
                writer.write(f)

            # clear password entry after success
            self.password_entry.delete(0, tk.END)

            self.status_var.set(f"PDF encrypted successfully: {output_path}")
            messagebox.showinfo("Success", "PDF encrypted successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_var.set("Encryption failed.")

    def decrypt_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return

        password = self.password_entry.get().strip()
        if not password:
            messagebox.showwarning("No Password", "Please enter the password to decrypt the PDF.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Decrypted PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not output_path:
            return

        try:
            reader = PdfReader(self.pdf_path)
            if reader.is_encrypted:
                if not reader.decrypt(password):
                    messagebox.showerror("Error", "Incorrect password! Decryption failed.")
                    self.status_var.set("Decryption failed — wrong password.")
                    return

            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            with open(output_path, "wb") as f:
                writer.write(f)

            # clear password entry after success
            self.password_entry.delete(0, tk.END)

            self.status_var.set(f"PDF decrypted successfully: {output_path}")
            messagebox.showinfo("Success", "PDF decrypted successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_var.set("Decryption failed.")
