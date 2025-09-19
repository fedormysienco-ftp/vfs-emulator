import tkinter as tk
from tkinter import scrolledtext
import shlex

class VFSEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VFS Emulator")

        self.vfs_physical_path = None  # Путь к физическому расположению VFS
        self.startup_script_path = None  # Путь к стартовому скрипту

        self.vfs = {}  # Корень виртуальной файловой системы
        self.current_dir = "/"  # Текущая директория в рамках VFS

        self.create_widgets()
        self.setup_commands()  # Инициализируем словарь команд

    def create_widgets(self):
        self.prompt_label = tk.Label(self, text=f"{self.current_dir} $ ", anchor="w")
        self.prompt_label.pack(fill="x", padx=5, pady=(5, 0))

        self.command_entry = tk.Entry(self)
        self.command_entry.pack(fill="x", padx=5, pady=5)
        self.command_entry.bind("<Return>", self.execute_command)

        self.output_area = scrolledtext.ScrolledText(self, state="disabled")
        self.output_area.pack(fill="both", expand=True, padx=5, pady=5)
        # Устанавливаем моноширинный шрифт для красивого вывода, как в терминале
        self.output_area.configure(font=("Courier New", 10))

    def setup_commands(self):

        self.commands = {
            "exit": self.cmd_exit,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
        }

    def execute_command(self, event):

        command_string = self.command_entry.get()
        self.command_entry.delete(0, tk.END)

        self.print_output(f"{self.prompt_label.cget('text')}{command_string}")

        try:
            parts = shlex.split(command_string)
        except ValueError as e:
            self.print_error(f"Syntax error: {e}")
            return

        if not parts:
            self.update_prompt()
            return

        command = parts[0]
        args = parts[1:]

        if command in self.commands:
            try:
                self.commands[command](args)
            except Exception as e:
                self.print_error(f"{command}: error executing command: {e}")
        else:
            self.print_error(f"vfs: command not found: {command}")

    def cmd_exit(self, args):
        self.quit()

    def cmd_ls(self, args):
        self.print_output(f"ls: listing directory '{self.current_dir}'. Arguments: {args}")

    def cmd_cd(self, args):
        self.print_output(f"cd: changing directory to '{args}'. (Not implemented yet)")
        if args:
            self.current_dir = args[0]
            self.update_prompt()

    def print_output(self, text):
        self.output_area.configure(state="normal")
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.configure(state="disabled")
        self.output_area.see(tk.END)

    def print_error(self, text):
        self.print_output(f"vfs: {text}")

    def update_prompt(self):
        self.prompt_label.config(text=f"{self.current_dir} $ ")

if __name__ == "__main__":
    app = VFSEmulator()
    app.mainloop()