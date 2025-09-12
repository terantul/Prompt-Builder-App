import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
import threading

CONFIG_FILE = "config.json"
ORDER_TAGS_FILE = "tags_order.json"
TAGS_DIR = "tags"

class PromptBuilderApp:
    def __init__(self, root):
        # Дані конфігурації для API
        self.api_config = {"api_url": "", "model_name": ""}

        # Завантажуємо конфіг, якщо є
        self.load_config()

        self.load_language()
        # Завантажуємо теги
        self.load_tags()

        self.root = root
        self.root.title(self.get("ui", "title", "Constructor of promts for image generation"))
        self.root.geometry("800x600")

        # Меню
        self.create_menu()

        self.listboxes = {}
        self.selected_tags = {group: [] for group in self.prompt_groups}
        self._last_action_group = None

        self.create_ui()

    # =================== MENU ===================
    def create_menu(self):
        menubar = tk.Menu(self.root)
        info_menu = tk.Menu(menubar, tearoff=0)
        info_menu.add_command(label=self.get("menu", "settings", "Settings"), command=self.open_settings)
        info_menu.add_command(label=self.get("menu", "about", "About"), command=self.show_about)
        menubar.add_cascade(label=self.get("menu", "info", "Info"), menu=info_menu)
        self.root.config(menu=menubar)

    def show_about(self):
        messagebox.showinfo(
            self.get("menu", "about", "About"),
            self.get("messages", "show_about", "Prompt constructor for image generation\n") +
            self.get("info", "created_by", "Created by DTerantul & ChatGPT")
        )

    # =================== MULTI-LANGUAGE GET ===================
    def get(self, section, key, default=None):
        print(section, key, default)
        """
        Повертає перекладений рядок з lang_data.
        Якщо ключ не знайдено — повертає default або key.
        """
        if not hasattr(self, "lang_data"):
            return default if default is not None else key

        return self.lang_data.get(section, {}).get(key, default if default is not None else key)

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title(self.get("ui", "settings", "Settings"))
        settings_win.geometry("400x250")
        settings_win.grab_set()  # модальне

        # --- API URL ---
        tk.Label(settings_win, text=self.get("api_url", "API URL:")).pack(pady=5)
        api_entry = tk.Entry(settings_win, width=50)
        api_entry.pack(pady=5)
        api_entry.insert(0, self.api_config.get("api_url", ""))

        # --- Model Name ---
        tk.Label(settings_win, text=self.get("model_name", "Model Name:")).pack(pady=5)
        model_entry = tk.Entry(settings_win, width=50)
        model_entry.pack(pady=5)
        model_entry.insert(0, self.api_config.get("model_name", ""))

        # --- Interface Language ---
        tk.Label(settings_win, text=self.get("interface_language", "Interface Language:")).pack(pady=5)

        # Зчитуємо список мов з директорії lang
        available_langs = ["en"]
        if os.path.exists("lang") and os.path.isdir("lang"):
            for f in os.listdir("lang"):
                if f.endswith(".json"):
                    lang_code = os.path.splitext(f)[0]
                    if lang_code not in available_langs:
                        available_langs.append(lang_code)

        interface_lang_var = tk.StringVar()
        interface_lang_var.set(getattr(self, "interface_lang", "en"))

        lang_menu = ttk.OptionMenu(settings_win, interface_lang_var, interface_lang_var.get(), *available_langs)
        lang_menu.pack(pady=5)

        def save_settings():
            self.api_config["api_url"] = api_entry.get()
            self.api_config["model_name"] = model_entry.get()
            self.api_config["interface_lang"] = interface_lang_var.get()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.api_config, f, indent=4)

            # Перезавантажуємо мову інтерфейсу
            self.interface_lang = interface_lang_var.get()
            self.load_language()

            messagebox.showinfo(self.get("settings_saved", "Settings saved!"),
                                self.get("settings_saved_msg", "Settings have been saved successfully."))
            settings_win.destroy()

        save_btn = ttk.Button(settings_win, text=self.get("save", "Save"), command=save_settings)
        save_btn.pack(pady=10)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.api_config = {
                        "api_url": cfg.get("api_url", ""),
                        "model_name": cfg.get("model_name", "")
                    }
                    self.interface_lang = cfg.get("interface_lang", "en")
            except Exception as e:
                messagebox.showwarning("Warning", f"Не вдалося завантажити config.json:\n{e}")
                self.api_config = {"api_url": "", "model_name": ""}
                self.interface_lang = "en"
        else:
            self.api_config = {"api_url": "", "model_name": ""}
            self.interface_lang = "en"

    def load_language(self):
        if self.interface_lang == "en":
            self.lang_data = {}
            return

        lang_file = os.path.join("lang", f"{self.interface_lang}.json")
        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self.lang_data = json.load(f)
            except Exception as e:
                messagebox.showwarning("Warning", f"Не вдалося завантажити файл мови {lang_file}:\n{e}")
                self.lang_data = {}
        else:
            messagebox.showwarning("Warning", f"Файл мови {lang_file} не знайдено!")
            self.lang_data = {}


    def load_tags(self):
        # 1. Завантажуємо порядок груп
        self.tags_order = []
        if os.path.exists(ORDER_TAGS_FILE):
            try:
                with open(ORDER_TAGS_FILE, "r", encoding="utf-8") as f:
                    self.tags_order = json.load(f)
            except Exception as e:
                messagebox.showwarning("Warning", f"Не вдалося завантажити '{ORDER_TAGS_FILE}':\n{e}")

        # 2. Перевірка директорії тегів
        if not os.path.exists(TAGS_DIR) or not os.path.isdir(TAGS_DIR):
            messagebox.showwarning("Warning", f"Директорія '{TAGS_DIR}' не знайдена!")
            self.prompt_groups = {}
            return

        # 3. Формуємо словник груп тегів згідно tags_order
        self.prompt_groups = {}
        for group_name in self.tags_order:
            file_path = os.path.join(TAGS_DIR, f"{group_name}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tags = json.load(f)
                        if isinstance(tags, list):
                            self.prompt_groups[group_name] = tags
                        else:
                            messagebox.showwarning(
                                "Warning",
                                f"Файл '{group_name}.json' має неправильний формат. Очікується список тегів."
                            )
                except Exception as e:
                    messagebox.showwarning("Warning", f"Не вдалося завантажити файл '{group_name}.json':\n{e}")
            else:
                messagebox.showwarning("Warning", f"Файл тегів для групи '{group_name}' не знайдено в '{TAGS_DIR}'!")

        # 4. Якщо не завантажено жодної групи
        if not self.prompt_groups:
            messagebox.showwarning("Warning", "Не вдалося завантажити жодну групу тегів.")


    # =================== PROMPT BUILDER UI ===================
    def create_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        for group, tags in self.prompt_groups.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=group)

            label = ttk.Label(frame, text=f"Оберіть теги для {group}:")
            label.pack(pady=5)

            # Для Subject дозволяємо тільки один вибір
            if "Subject" in group:
                selectmode = tk.SINGLE
            else:
                selectmode = tk.MULTIPLE

            listbox = tk.Listbox(frame, selectmode=selectmode, height=12, width=50)
            for tag in tags:
                listbox.insert(tk.END, tag)
            listbox.pack(pady=5)

            # Прив'язуємо подію вибору
            listbox.bind("<<ListboxSelect>>", lambda e, g=group: self.update_selection(g))

            self.listboxes[group] = listbox

        # Кнопка генерації промту
        generate_btn = ttk.Button(self.root, text="Згенерувати промт", command=self.generate_prompt)
        generate_btn.pack(pady=5)

        # Кнопка покращення промту через LLM
        self.improve_btn = ttk.Button(self.root, text="Покращити промт", command=self.improve_prompt_thread)
        self.improve_btn.pack(pady=5)

        # Поле результату
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

    # =================== GENERATE PROMPT ===================
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

    # =================== ENHANCE PROMPT ===================
    def enhance_prompt(self):
        prompt = self.result_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Увага", "Спочатку згенеруйте промт!")
            return
        api_url = self.api_config.get("api_url")
        model_name = self.api_config.get("model_name")
        if not api_url or not model_name:
            messagebox.showwarning("Увага", "Налаштуйте API та модель у Settings!")
            return

        enhanced = self.call_local_llm(api_url, model_name, prompt)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, enhanced)

    def improve_prompt_thread(self):
        prompt = self.result_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Увага", "Спочатку згенеруйте промт!")
            return

        api_url = self.api_config.get("api_url")
        model_name = self.api_config.get("model_name")
        if not api_url or not model_name:
            messagebox.showwarning("Увага", "Налаштуйте API та модель у Settings!")
            return

        # Блокуємо кнопку під час генерації
        self.improve_btn.config(state=tk.DISABLED)
        self.result_text.insert(tk.END, "\n\n[Покращення промту...]")

        # Виклик LLM у окремому потоці з callback
        self.call_local_llm(api_url, model_name, prompt, self.on_llm_done)

    # Функція для оновлення GUI після отримання відповіді LLM
    def on_llm_done(self, enhanced_prompt):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, enhanced_prompt)
        self.improve_btn.config(state=tk.NORMAL)

    # Функція call_local_llm з підтримкою потоків і callback
    def call_local_llm(self, api_url, model_name, prompt, callback):
        def worker():
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an AI prompt enhancer for image generation. "
                            "Your task is to improve and enrich prompts for high-quality image generation "
                            "without making them excessively long. "
                            "Keep the enhanced prompt under 150 words (or ~1000 characters). "
                            "Focus on clarity, vivid details, and key visual elements. "
                            "Do not repeat descriptions or add unnecessary filler. "
                            "Use concise but descriptive language suitable for generating 8K-resolution images."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Enhance this prompt: {prompt}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 512
            }

            print("=== LLM Request ===")
            print(f"API URL: {api_url}")
            print(f"Model: {model_name}")
            print(f"Prompt:\n{prompt}")
            print("===================")

            try:
                response = requests.post(f"{api_url}/v1/chat/completions", json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                enhanced_prompt = data["choices"][0]["message"]["content"].strip()
                print("=== LLM Response ===")
                print(enhanced_prompt)
                print("===================")
            except requests.exceptions.ReadTimeout:
                enhanced_prompt = "[Помилка: час очікування відповіді LLM перевищено.]"
                print("[LLM Error] Read timeout. Модель потребує більше часу для генерації.")
            except Exception as e:
                enhanced_prompt = f"[Помилка при зверненні до LLM: {e}]"
                print(f"[LLM Error] {e}")

            # Оновлюємо GUI у головному потоці
            self.root.after(0, lambda: callback(enhanced_prompt))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = PromptBuilderApp(root)
    root.mainloop()
