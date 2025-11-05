import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from pdfmang.modules.merge_tool import MergeTool
from pdfmang.modules.split_tool import SplitTool
from pdfmang.modules.compress_tool import CompressTool
from pdfmang.modules.encrypt_tool import EncryptTool
from pdfmang.modules.convert_tool import ConvertTool

# Main Application Window
def main():
    root = ThemedTk(theme="breeze")
    root.title("PDF Utility Suite")
    root.geometry("800x600")

    # Create status bar variable first
    status_var = tk.StringVar()
    status_var.set("Ready")

    # Notebook for multiple tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    tabs = {
        "Merge": ttk.Frame(notebook),
        "Split": ttk.Frame(notebook),
        "Compress": ttk.Frame(notebook),
        "Encrypt": ttk.Frame(notebook),
        "Convert": ttk.Frame(notebook),
    }

    for name, frame in tabs.items():
        notebook.add(frame, text=name)

    # Initialize tools (pass the status_var here)
    merge_tool = MergeTool(tabs["Merge"], status_var)
    split_tool = SplitTool(tabs["Split"], status_var)
    compress_tool = CompressTool(tabs["Compress"], status_var)
    encrypt_tool = EncryptTool(tabs["Encrypt"], status_var)
    convert_tool = ConvertTool(tabs["Convert"], status_var)

    # Status bar at the bottom
    status_bar = ttk.Label(root, textvariable=status_var, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")

    root.mainloop()



if __name__ == "__main__":
    main()
