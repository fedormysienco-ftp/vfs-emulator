import tkinter as tk
from tkinter import scrolledtext
import shlex
import argparse
import json
import os


class VFSEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VFS Emulator")

        self.vfs_physical_path = None
        self.startup_script_path = None
        self.vfs = {}  # Корень VFS
        self.current_dir = "/"  # Текущая директория
        self.current_path = []  # Текущий путь в VFS

        self.create_widgets()
        self.setup_commands()

        # Загружаем VFS если указан путь
        if self.vfs_physical_path:
            self.load_vfs()

        # Запускаем скрипт после задержки
        self.after(100, self.run_startup_script)

    def load_vfs(self):
        """Загружает VFS из JSON-файла"""
        try:
            self.print_output(f"DEBUG: Trying to load VFS from: {self.vfs_physical_path}")

            if not os.path.exists(self.vfs_physical_path):
                self.print_error(f"VFS file not found: {self.vfs_physical_path}")
                return False

            self.print_output(f"DEBUG: VFS file exists, reading...")

            with open(self.vfs_physical_path, 'r', encoding='utf-8') as f:
                vfs_data = json.load(f)

            self.print_output(f"DEBUG: JSON loaded successfully, type: {type(vfs_data)}")

            # Проверяем структуру VFS
            if not isinstance(vfs_data, dict):
                raise ValueError("Invalid VFS structure: root must be a dictionary")

            # Проверяем обязательные поля для корневой директории
            if vfs_data.get('type') != 'directory':
                raise ValueError("Root VFS node must be a directory")

            if 'contents' not in vfs_data:
                raise ValueError("Root VFS node must have 'contents' field")

            self.vfs = vfs_data
            self.current_path = [self.vfs]
            self.current_dir = "/"

            self.print_output(f"=== VFS loaded successfully from: {self.vfs_physical_path} ===")
            self.print_output(f"VFS structure: {self.get_vfs_stats()}")
            return True

        except json.JSONDecodeError as e:
            self.print_error(f"Invalid JSON format in VFS file: {e}")
            return False
        except Exception as e:
            self.print_error(f"Error loading VFS: {e}")
            return False

    def is_vfs_loaded(self):
        """Проверяет, загружена ли VFS"""
        return bool(self.vfs and 'type' in self.vfs and self.vfs['type'] == 'directory')

    def get_current_node(self):
        """Возвращает текущий узел VFS"""
        if not self.is_vfs_loaded():
            return None
        return self.current_path[-1] if self.current_path else self.vfs

    def resolve_path(self, path):
        """Разрешает путь в VFS и возвращает узел"""
        if not self.is_vfs_loaded():
            return None

        if not path or path == ".":
            return self.get_current_node()

        if path == "..":
            # Переход на уровень выше (если не корень)
            if len(self.current_path) > 1:
                self.current_path.pop()
                # Обновляем current_dir на основе пути
                if len(self.current_path) == 1:
                    self.current_dir = "/"
                else:
                    # Собираем путь из имен узлов
                    path_parts = []
                    for node in self.current_path[1:]:
                        # Ищем имя узла в его родителе
                        parent = self.current_path[self.current_path.index(node) - 1]
                        for name, child in parent.get('contents', {}).items():
                            if child is node:
                                path_parts.append(name)
                                break
                    self.current_dir = "/" + "/".join(path_parts)
                self.update_prompt()
            return self.get_current_node()

        # Обработка абсолютных и относительных путей
        if path.startswith('/'):
            # Абсолютный путь - начинаем с корня
            path_parts = [p for p in path.split('/') if p]
            current = self.vfs
            new_path = [self.vfs]
        else:
            # Относительный путь - начинаем с текущей директории
            path_parts = [p for p in path.split('/') if p]
            current = self.get_current_node()
            new_path = self.current_path.copy()

        # Навигация по пути
        for part in path_parts:
            if part == '..':
                # Обработка .. в пути
                if len(new_path) > 1:
                    new_path.pop()
                    current = new_path[-1]
                continue
            elif part == '.':
                # Текущая директория - пропускаем
                continue

            if 'contents' in current and part in current['contents']:
                child = current['contents'][part]
                if child.get('type') == 'directory':
                    current = child
                    new_path.append(current)
                else:
                    return None  # Не можем перейти в файл
            else:
                return None  # Путь не найден

        # Обновляем текущий путь если навигация успешна
        self.current_path = new_path

        # Обновляем current_dir
        if len(new_path) == 1:
            self.current_dir = "/"
        else:
            # Собираем путь из имен узлов
            path_parts = []
            for i, node in enumerate(new_path[1:], 1):
                parent = new_path[i - 1]
                for name, child in parent.get('contents', {}).items():
                    if child is node:
                        path_parts.append(name)
                        break
            self.current_dir = "/" + "/".join(path_parts)

        self.update_prompt()
        return current

    def get_vfs_stats(self):
        """Возвращает статистику по VFS"""
        if not self.is_vfs_loaded():
            return "No VFS loaded"

        def count_nodes(node):
            files = 0
            dirs = 0

            if node.get('type') == 'directory' and 'contents' in node:
                for child in node['contents'].values():
                    if child.get('type') == 'directory':
                        sub_dirs, sub_files = count_nodes(child)
                        dirs += 1 + sub_dirs
                        files += sub_files
                    else:
                        files += 1
            return dirs, files

        dirs, files = count_nodes(self.vfs)
        return f"{dirs} directories, {files} files"

    def create_widgets(self):
        self.prompt_label = tk.Label(self, text=f"{self.current_dir} $ ", anchor="w")
        self.prompt_label.pack(fill="x", padx=5, pady=(5, 0))

        self.command_entry = tk.Entry(self)
        self.command_entry.pack(fill="x", padx=5, pady=5)
        self.command_entry.bind("<Return>", self.execute_command)

        self.output_area = scrolledtext.ScrolledText(self, state="disabled")
        self.output_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.output_area.configure(font=("Courier New", 10))

    def setup_commands(self):
        self.commands = {
            "exit": self.cmd_exit,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "mount": self.cmd_mount,
            "pwd": self.cmd_pwd,
            "cat": self.cmd_cat,
            "uname": self.cmd_uname,
            "clear": self.cmd_clear,
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

    def cmd_cat(self, args):
        """Показывает содержимое файла"""
        if not self.is_vfs_loaded():
            self.print_error("No VFS loaded")
            return

        if not args:
            self.print_error("Usage: cat <filename>")
            return

        filename = args[0]
        current_node = self.get_current_node()

        if current_node and 'contents' in current_node and filename in current_node['contents']:
            file_node = current_node['contents'][filename]
            if file_node.get('type') == 'file':
                content = file_node.get('content', '')
                self.print_output(content)
            else:
                self.print_error(f"cat: {filename}: Is a directory")
        else:
            self.print_error(f"cat: {filename}: No such file")

    def cmd_clear(self, args):
        """Очищает экран"""
        self.output_area.configure(state="normal")
        self.output_area.delete(1.0, tk.END)
        self.output_area.configure(state="disabled")

    def cmd_uname(self, args):
        """Показывает информацию о системе"""
        if args and args[0] == '-a':
            self.print_output("VFS-Emulator 1.0 (Stage 4) - Virtual File System Emulator")
        else:
            self.print_output("VFS-Emulator")

    def cmd_mount(self, args):
        """Команда mount для загрузки VFS"""
        if not args:
            if self.vfs_physical_path:
                self.print_output(f"Currently mounted: {self.vfs_physical_path}")
                self.print_output(f"VFS loaded: {self.is_vfs_loaded()}")
            else:
                self.print_output("No VFS mounted")
            return

        vfs_path = args[0]
        if not os.path.exists(vfs_path):
            self.print_error(f"VFS file not found: {vfs_path}")
            return

        self.vfs_physical_path = vfs_path
        if self.load_vfs():
            self.print_output(f"VFS mounted successfully from: {vfs_path}")
        else:
            self.print_error(f"Failed to mount VFS from: {vfs_path}")

    def cmd_pwd(self, args):
        """Показывает текущую директорию"""
        self.print_output(self.current_dir)

    def cmd_ls(self, args):
        self.print_output(f"DEBUG: vfs_path={self.vfs_physical_path}, vfs_loaded={self.is_vfs_loaded()}")

        if self.is_vfs_loaded():
            # Режим VFS - показываем содержимое текущей директории
            current_node = self.get_current_node()
            if current_node and current_node.get('type') == 'directory' and 'contents' in current_node:
                items = []
                for name, child in current_node['contents'].items():
                    item_type = 'd' if child.get('type') == 'directory' else '-'
                    items.append(f"{name}/" if item_type == 'd' else name)

                if items:
                    self.print_output("  ".join(sorted(items)))
                else:
                    self.print_output("Directory is empty")
            else:
                self.print_output("Directory is empty")
        else:
            # Режим заглушки (как раньше)
            self.print_output(f"ls: listing directory '{self.current_dir}'. Arguments: {args}")

    def cmd_cd(self, args):
        self.print_output(f"DEBUG: vfs_path={self.vfs_physical_path}, vfs_loaded={self.is_vfs_loaded()}")

        if not args:
            # cd без аргументов - переход в корень
            if self.is_vfs_loaded():
                self.current_dir = "/"
                self.current_path = [self.vfs]
                self.update_prompt()
            else:
                self.current_dir = "/"
                self.update_prompt()
            return

        target_dir = args[0]

        if self.is_vfs_loaded():
            # Режим VFS - проверяем существование пути
            if target_dir == "/":
                # Переход в корень
                self.current_dir = "/"
                self.current_path = [self.vfs]
                self.update_prompt()
                return

            new_node = self.resolve_path(target_dir)

            if new_node and new_node.get('type') == 'directory':
                self.print_output(f"Changed directory to {self.current_dir}")
            else:
                self.print_error(f"cd: {target_dir}: No such directory")
        else:
            # Режим заглушки
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

    def run_startup_script(self):
        if not self.startup_script_path:
            return

        try:
            with open(self.startup_script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            self.print_output(f"=== Executing startup script: {self.startup_script_path} ===")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                self.print_output(f"{self.prompt_label.cget('text')}{line}")

                try:
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
                    continue

            self.print_output("=== Startup script execution completed ===")

        except FileNotFoundError:
            self.print_error(f"Startup script not found: {self.startup_script_path}")
        except Exception as e:
            self.print_error(f"Error reading script: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='VFS Emulator - Stage 3')
    parser.add_argument('--vfs-path', type=str, help='Path to VFS JSON file')
    parser.add_argument('--script', type=str, help='Path to startup script')
    args = parser.parse_args()

    app = VFSEmulator()
    app.vfs_physical_path = args.vfs_path
    app.startup_script_path = args.script

    print("=== VFS Emulator - Debug Info ===")
    print(f"VFS path: {app.vfs_physical_path or 'Not set'}")
    print(f"Startup script: {app.startup_script_path or 'Not set'}")
    print("=================================")

    app.mainloop()