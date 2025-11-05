import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfMerger

class MergeTool:
    def __init__(self, parent, status_var):
        self.parent = parent
        self.status_var = status_var
        self.pdf_files = []

        self.setup_ui()

    def setup_ui(self):
        # Title
        ttk.Label(self.parent, text="Merge PDF Files", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # Frame for listbox
        list_frame = ttk.Frame(self.parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Listbox to show selected PDFs
        self.listbox = tk.Listbox(list_frame, height=10, selectmode=tk.SINGLE)
        self.listbox.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Buttons
        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Add PDFs", command=self.add_pdfs).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Merge PDFs", command=self.merge_pdfs).grid(row=0, column=2, padx=5)

    def add_pdfs(self):
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if files:
            for f in files:
                if f not in self.pdf_files:
                    self.pdf_files.append(f)
                    self.listbox.insert("end", f)
            self.status_var.set(f"Added {len(files)} file(s).")

    def remove_selected(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            removed_file = self.pdf_files.pop(index)
            self.listbox.delete(index)
            self.status_var.set(f"Removed: {removed_file}")
        else:
            messagebox.showwarning("No Selection", "Please select a file to remove.")

    def merge_pdfs(self):
        if len(self.pdf_files) < 2:
            messagebox.showwarning("Not Enough Files", "Please select at least two PDF files to merge.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if output_path:
            try:
                merger = PdfMerger()
                for pdf in self.pdf_files:
                    merger.append(pdf)
                merger.write(output_path)
                merger.close()
                self.status_var.set(f"Successfully merged into {output_path}")
                messagebox.showinfo("Success", "PDFs merged successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                self.status_var.set("Merge failed.")
