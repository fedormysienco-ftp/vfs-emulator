import tkinter as tk
from tkinter import scrolledtext
import shlex
import argparse

class VFSEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VFS Emulator")

        self.vfs_physical_path = None
        self.startup_script_path = None
        self.vfs = {}
        self.current_dir = "/"

        self.create_widgets()
        self.setup_commands()

        # === ДОБАВЛЯЕМ ВЫЗОВ СКРИПТА ПОСЛЕ ИНИЦИАЛИЗАЦИИ ===
        # Запускаем скрипт после небольшой задержки, чтобы GUI успел загрузиться
        self.after(100, self.run_startup_script)

    def create_widgets(self): #кнопки поля
        self.prompt_label = tk.Label(self, text=f"{self.current_dir} $ ", anchor="w")
        self.prompt_label.pack(fill="x", padx=5, pady=(5, 0))

        self.command_entry = tk.Entry(self)
        self.command_entry.pack(fill="x", padx=5, pady=5)
        self.command_entry.bind("<Return>", self.execute_command)

        self.output_area = scrolledtext.ScrolledText(self, state="disabled")
        self.output_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.output_area.configure(font=("Courier New", 10)) #красота

    def setup_commands(self):

        self.commands = {
            "exit": self.cmd_exit,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
        }

    def execute_command(self, event): #обработка команд

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

    def print_output(self, text): #текст в область вывода
        self.output_area.configure(state="normal")
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.configure(state="disabled")
        self.output_area.see(tk.END)

    def print_error(self, text):
        self.print_output(f"vfs: {text}")

    def update_prompt(self): #обновляет приглос командной строки
        self.prompt_label.config(text=f"{self.current_dir} $ ")

    def run_startup_script(self):
        """Выполняет стартовый скрипт если он указан"""
        if not self.startup_script_path:
            return

        try:
            with open(self.startup_script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            self.print_output(f"=== Executing startup script: {self.startup_script_path} ===")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # Пропускаем пустые строки и комментарии
                    continue

                # Имитируем ввод пользователя
                self.print_output(f"{self.prompt_label.cget('text')}{line}")

                try:
                    # Используем существующий парсер команд
                    parts = shlex.split(line)
                    if not parts:
                        continue

                    command = parts[0]
                    args = parts[1:]

                    if command in self.commands:
                        self.commands[command](args)
                    else:
                        self.print_error(f"command not found: {command}")

                except Exception as e:
                    self.print_error(f"Error executing line {line_num}: {e}")
                    continue  # Пропускаем ошибочные строки (требование)

            self.print_output("=== Startup script execution completed ===")

        except FileNotFoundError:
            self.print_error(f"Startup script not found: {self.startup_script_path}")
        except Exception as e:
            self.print_error(f"Error reading script: {e}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='VFS Emulator - Stage 2')
    parser.add_argument('--vfs-path', type=str, help='Path to VFS JSON file')
    parser.add_argument('--script', type=str, help='Path to startup script')
    args = parser.parse_args()

    app = VFSEmulator()
    app.vfs_physical_path = args.vfs_path
    app.startup_script_path = args.script

    # Отладочный вывод
    print("=== VFS Emulator - Debug Info ===")
    print(f"VFS path: {app.vfs_physical_path or 'Not set'}")
    print(f"Startup script: {app.startup_script_path or 'Not set'}")
    print("=================================")

    app.mainloop()