import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

CONFIG_FILE = "config.json"

class PromptBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Конструктор промтів (для людей)")
        self.root.geometry("800x600")

        # Створимо меню
        self.create_menu()

        # Дані конфігурації для API
        self.api_config = {"api_url": "", "model_name": ""}

        # Завантажуємо конфіг, якщо є
        self.load_config()

        # Групи з тегами
        self.prompt_groups = {
            "Subject (Об'єкт)": [
                "young woman", "old man", "teenager", "child", "muscular man",
                "elegant lady", "cyborg human", "fantasy elf", "samurai warrior"
            ],
            "Style (Стиль)": [
                "digital painting", "realistic photo", "oil on canvas",
                "anime style", "pixar style", "concept art", "cyberpunk art"
            ],
            "Details (Деталі)": [
                "red braided hair", "freckles", "blue eyes", "tattoos",
                "armored suit", "casual clothes", "glowing sword",
                "intricate jewelry", "symmetrical face"
            ],
            "Composition (Композиція)": [
                "portrait shot", "full body", "close-up", "low angle",
                "high angle", "rule of thirds", "dynamic pose"
            ],
            "Quality (Якість)": [
                "masterpiece", "best quality", "highly detailed",
                "8k resolution", "sharp focus", "ultra detailed"
            ],
            "Color/Lighting (Світло/Кольори)": [
                "cinematic lighting", "golden hour", "dramatic shadows",
                "soft light", "neon lights", "monochrome", "vibrant colors"
            ],
            "Context (Контекст)": [
                "in a futuristic city", "on a snowy mountain",
                "inside a cozy tavern", "in a dark forest",
                "on a beach", "in outer space", "in a battlefield"
            ]
        }

        self.listboxes = {}
        self.selected_tags = {group: [] for group in self.prompt_groups}  # тимчасове сховище вибраного
        self._last_action_group = None

        self.create_ui()

    # =================== MENU ===================
    def create_menu(self):
        menubar = tk.Menu(self.root)
        info_menu = tk.Menu(menubar, tearoff=0)
        info_menu.add_command(label="Settings", command=self.open_settings)
        info_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Info", menu=info_menu)
        self.root.config(menu=menubar)

    def show_about(self):
        messagebox.showinfo(
            "About",
            "Конструктор промтів для генерації зображень людей\n"
            "Created by DTerantul & ChatGPT"
        )

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("400x200")
        settings_win.grab_set()  # робимо модальним

        tk.Label(settings_win, text="API URL:").pack(pady=5)
        api_entry = tk.Entry(settings_win, width=50)
        api_entry.pack(pady=5)
        api_entry.insert(0, self.api_config.get("api_url", ""))

        tk.Label(settings_win, text="Model Name:").pack(pady=5)
        model_entry = tk.Entry(settings_win, width=50)
        model_entry.pack(pady=5)
        model_entry.insert(0, self.api_config.get("model_name", ""))

        def save_settings():
            self.api_config["api_url"] = api_entry.get()
            self.api_config["model_name"] = model_entry.get()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.api_config, f, indent=4)
            messagebox.showinfo("Settings", "Налаштування збережено!")
            settings_win.destroy()

        save_btn = ttk.Button(settings_win, text="Save", command=save_settings)
        save_btn.pack(pady=10)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.api_config = json.load(f)
            except Exception as e:
                messagebox.showwarning("Warning", f"Не вдалося завантажити config.json:\n{e}")

    # =================== PROMPT BUILDER UI ===================
    def create_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        for group, tags in self.prompt_groups.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=group)

            label = ttk.Label(frame, text=f"Оберіть теги для {group}:")
            label.pack(pady=5)

            selectmode = tk.SINGLE if "Subject" in group else tk.MULTIPLE

            listbox = tk.Listbox(frame, selectmode=selectmode, height=12, width=50, exportselection=False)
            for tag in tags:
                listbox.insert(tk.END, tag)
            listbox.pack(pady=5)

            listbox.bind("<Button-1>", lambda e, g=group: self.on_listbox_click(e, g))
            listbox.bind("<<ListboxSelect>>", lambda e, g=group: self.update_selection(g))

            self.listboxes[group] = listbox

        generate_btn = ttk.Button(self.root, text="Згенерувати промт", command=self.generate_prompt)
        generate_btn.pack(pady=10)

        self.result_text = tk.Text(self.root, height=8, wrap="word")
        self.result_text.pack(fill="x", padx=10, pady=5)

    def on_listbox_click(self, event, group):
        self._last_action_group = group

    def update_selection(self, group):
        listbox = self.listboxes[group]
        cur_selection = [listbox.get(i) for i in listbox.curselection()]

        if not cur_selection and self._last_action_group != group:
            return

        if "Subject" in group:
            if cur_selection:
                self.selected_tags[group] = [cur_selection[-1]]
                listbox.selection_clear(0, tk.END)
                try:
                    last_index = listbox.get(0, tk.END).index(cur_selection[-1])
                    listbox.selection_set(last_index)
                except ValueError:
                    pass
            else:
                self.selected_tags[group] = []
        else:
            self.selected_tags[group] = cur_selection

        self._last_action_group = None
        print(self.selected_tags)

    def generate_prompt(self):
        parts = []
        for group, tags in self.selected_tags.items():
            if tags:
                parts.append(", ".join(tags))

        if not parts:
            messagebox.showwarning("Увага", "Виберіть хоча б один тег!")
            return

        prompt = ", ".join(parts)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, prompt)


if __name__ == "__main__":
    root = tk.Tk()
    app = PromptBuilderApp(root)
    root.mainloop()
