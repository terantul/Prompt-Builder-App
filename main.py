import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
import threading

CONFIG_FILE = "config.json"

class PromptBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Конструктор промтів (для людей)")
        self.root.geometry("800x600")

        # Меню
        self.create_menu()

        # Дані конфігурації для API
        self.api_config = {"api_url": "", "model_name": ""}

        # Завантажуємо конфіг, якщо є
        self.load_config()

        # Групи з тегами
        self.prompt_groups = {
            "Subject (Об'єкт)": [
                "young woman", "young man", "old man", "teenager", "child", "muscular man",
                "elegant lady", "cyborg human", "fantasy elf", "samurai warrior"
            ],
            "Style (Стиль)": [
                "digital painting", "photorealistic", "realistic photo", "oil on canvas",
                "anime style", "pixar style", "concept art", "cyberpunk art"
            ],
            "Details (Деталі)": [
                "freckles", "blue eyes", "green eyes", "tattoos",
                "armored suit", "casual clothes", "glowing sword",
                "intricate jewelry", "symmetrical face", "detailed face",
                "hand 5 fingers", "detailed hands", "blonde hair", "brunette hair", "red hair",
                "short hair", "long hair", "curly hair", "straight hair", "bald head"
            ],
            "Anatomy (Анатомія)": [
                "well-proportioned body", "muscular build", "slim figure",
                "athletic physique", "broad shoulders", "narrow waist",
                "curvy", "voluptuous", "hourglass figure", "petite", "slender"
            ],
            "Actions (Дії)": [
                "standing", "running", "walking ", "jumping", "sitting", "lies",
                "lies on his back", "lies on her side", "lies on his stomach", "crouching",
                "flying", "dancing",
                "holding a sword", "casting a spell", "looking at the horizon"
            ],
            "NSFW (18+)": [
                "erotic", "porno", "half-dressed", "half-undressed", "nude", "naked", "bare-chested", "lingerie",
                "underwear", "bikini", "sexy pose", "sensual", "provocative",
                "breast", "boobs", "ass", "pussy", "vagina", "nipples"

            ],
            "Composition (Композиція)": [
                "portrait shot", "full body shot", "from head to toe", "feet visible", "close-up", "low angle",
                "high angle", "rule of thirds", "dynamic pose", "wide shot", "rear view", "side view",
                "over-the-shoulder"
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
        self.selected_tags = {group: [] for group in self.prompt_groups}
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
        settings_win.grab_set()  # модальне

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
