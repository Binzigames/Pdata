import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import PdataMain


class PDataGUI:
    def __init__(self, root, db_filename="storage.db.json"):
        self.root = root
        self.root.title("PData Visual GUI Editor")
        self.root.geometry("750x550")
        self.root.minsize(600, 420)

        self.db_filename = db_filename
        self.db = PdataMain.connect(self.db_filename)

        self.columns = self.db.select("__schema_columns__")
        if not self.columns or not isinstance(self.columns, list):
            self.columns = ["Key", "Value"]
            self.db.upsert("__schema_columns__", self.columns)


        self.entries = {}

        self._init_ui()
        self.refresh_table()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _init_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(
            top_frame,
            text=f"Database: {self.db_filename}",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT)

        btn_save = ttk.Button(top_frame, text=" Save Changes (Commit)", command=self.save_changes)
        btn_save.pack(side=tk.RIGHT)

        self.table_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(self.table_frame, show="headings", selectmode="browse")
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.setup_tree_columns()

        self.editor_frame = ttk.LabelFrame(self.root, text=" Record Editor ", padding=10)
        self.editor_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.inputs_container = ttk.Frame(self.editor_frame)
        self.inputs_container.pack(fill=tk.X, expand=True, pady=5)

        self.build_editor_inputs()

        btn_frame = ttk.Frame(self.editor_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text=" Add Column", command=self.add_column).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text=" Remove Column", command=self.remove_column).pack(side=tk.LEFT, padx=3)

        ttk.Button(btn_frame, text=" Clear Fields", command=self.clear_entries).pack(side=tk.RIGHT, padx=3)
        ttk.Button(btn_frame, text=" Delete Record", command=self.delete_record).pack(side=tk.RIGHT, padx=3)
        ttk.Button(btn_frame, text=" Add / Update", command=self.add_or_update).pack(side=tk.RIGHT, padx=3)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=3)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def setup_tree_columns(self):
        self.tree["columns"] = tuple(self.columns)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor=tk.W)

    def build_editor_inputs(self):
        for widget in self.inputs_container.winfo_children():
            widget.destroy()

        self.entries.clear()

        for i, col in enumerate(self.columns):
            row = i // 2
            col_pos = (i % 2) * 2

            lbl = ttk.Label(self.inputs_container, text=f"{col}:")
            lbl.grid(row=row, column=col_pos, sticky=tk.W, padx=5, pady=3)

            entry = ttk.Entry(self.inputs_container)
            entry.grid(row=row, column=col_pos + 1, sticky=tk.EW, padx=5, pady=3)

            self.inputs_container.columnconfigure(col_pos + 1, weight=1)
            self.entries[col] = entry

    def add_column(self):
        col_name = simpledialog.askstring("Add Column", "Enter new column name:", parent=self.root)
        if not col_name:
            return

        col_name = col_name.strip()
        if not col_name:
            return

        if col_name in self.columns:
            messagebox.showwarning("Warning", f"Column '{col_name}' already exists!")
            return

        self.columns.append(col_name)
        self.db.upsert("__schema_columns__", self.columns)

        self.setup_tree_columns()
        self.build_editor_inputs()
        self.refresh_table()
        self.status_var.set(f"Column '{col_name}' added.")

    def remove_column(self):
        if len(self.columns) <= 1:
            messagebox.showwarning("Warning", "At least one column is required!")
            return

        col_name = simpledialog.askstring(
            "Remove Column",
            f"Enter column name to remove ({', '.join(self.columns)}):",
            parent=self.root
        )
        if not col_name:
            return

        col_name = col_name.strip()
        if col_name not in self.columns:
            messagebox.showerror("Error", f"Column '{col_name}' not found!")
            return

        if messagebox.askyesno("Confirm", f"Remove column '{col_name}'?"):
            self.columns.remove(col_name)
            self.db.upsert("__schema_columns__", self.columns)

            self.setup_tree_columns()
            self.build_editor_inputs()
            self.refresh_table()
            self.status_var.set(f"Column '{col_name}' removed.")

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        records = self.db.select_all()
        count = 0

        for key, value in records.items():
            if key == "__schema_columns__":
                continue

            row_values = []
            if isinstance(value, dict):
                for col in self.columns:
                    row_values.append(value.get(col, ""))
            else:
                row_values.append(key)
                if len(self.columns) > 1:
                    row_values.append(value)
                row_values.extend([""] * (len(self.columns) - len(row_values)))

            self.tree.insert("", tk.END, values=row_values)
            count += 1

        self.status_var.set(f"Loaded {count} record(s).")

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            values = item["values"]

            self.clear_entries()
            for col, val in zip(self.columns, values):
                if col in self.entries:
                    self.entries[col].insert(0, str(val))

    def add_or_update(self):
        if not self.columns:
            return

        primary_col = self.columns[0]
        primary_val = self.entries[primary_col].get().strip()

        if not primary_val:
            messagebox.showwarning(
                "Warning",
                f"First column ({primary_col}) cannot be empty! It acts as the Record Key."
            )
            return


        record_data = {col: self.entries[col].get().strip() for col in self.columns}

        self.db.upsert(primary_val, record_data)
        self.refresh_table()
        self.status_var.set(f"Record '{primary_val}' saved.")

    def delete_record(self):
        if not self.columns:
            return

        primary_col = self.columns[0]
        primary_val = self.entries[primary_col].get().strip()

        if not primary_val:
            messagebox.showwarning("Warning", f"Select or enter '{primary_col}' to delete!")
            return

        if self.db.delete(primary_val):
            self.refresh_table()
            self.clear_entries()
            self.status_var.set(f"Record '{primary_val}' deleted.")
        else:
            messagebox.showerror("Error", f"Record '{primary_val}' not found.")

    def save_changes(self):
        self.db.commit()
        messagebox.showinfo("Success", f"Changes successfully saved to '{self.db_filename}'!")
        self.status_var.set("Changes committed to file.")

    def clear_entries(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def on_close(self):
        self.db.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PDataGUI(root)
    root.mainloop()