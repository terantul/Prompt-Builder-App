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
    def __init__(self, master):
        self.api_config = {"api_url": "", "model_name": ""}
        self.interface_lang = "en"
        self.tags_order = []
        self.prompt_groups = {}
        self.lang_data = {}
        self.i18n_widgets = {}
        self.notebook = None
        self.generate_btn = None
        self.improve_btn = None
        self.result_text = None
        self.load_config()
        self.load_language()
        self.load_tags()

        self.root = master
        self.root.title(self.get("ui", "title", "Prompt constructor for image generation"))
        self.root.geometry("800x600")

        self.create_menu()

        self.tag_list_boxes = {}
        self.selected_tags = {group: [] for group in self.prompt_groups}
        self._last_action_group = None

        self.create_ui()

    # =================== MENU ===================
    def create_menu(self):
        if hasattr(self, "menubar"):
            self.root.config(menu=None)
            self.menubar.destroy()

        menubar = tk.Menu(self.root)
        info_menu = tk.Menu(menubar, tearoff=0)
        info_menu.add_command(label=self.get("menu", "settings", "Settings"), command=self.open_settings)
        info_menu.add_command(label=self.get("menu", "about", "About"), command=self.show_about)
        menubar.add_cascade(label=self.get("menu", "info", "Info"), menu=info_menu)
        self.root.config(menu=menubar)

    def show_about(self):
        messagebox.showinfo(
            self.get("menu", "about", "About"),
            self.get("messages", "show_about", "Prompt constructor for image generation\n")
            + self.get("info", "created_by", "Created by DTerantul"),
        )

    # =================== MULTI-LANGUAGE GET ===================
    def get(self, section, key, default=None):
        if not hasattr(self, "lang_data"):
            return default if default is not None else key

        return self.lang_data.get(section, {}).get(key, default if default is not None else key)

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title(self.get("ui", "settings", "Settings"))
        settings_win.geometry("400x250")
        settings_win.grab_set()

        # --- API URL ---
        tk.Label(settings_win, text=self.get("ui", "api_url", "API URL:")).pack(pady=5)
        api_entry = tk.Entry(settings_win, width=50)
        api_entry.pack(pady=5)
        api_entry.insert(0, self.api_config.get("api_url", ""))

        # --- Model Name ---
        tk.Label(settings_win, text=self.get("ui", "model_name", "Model Name:")).pack(pady=5)
        model_entry = tk.Entry(settings_win, width=50)
        model_entry.pack(pady=5)
        model_entry.insert(0, self.api_config.get("model_name", ""))

        # --- Interface Language ---
        tk.Label(settings_win, text=self.get("ui", "interface_language", "Interface Language:")).pack(pady=5)

        # --- Read the list of languages from the lang directory ---
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
            with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
                json.dump(self.api_config, config_file, indent=4)

            # Reload the interface language
            self.interface_lang = interface_lang_var.get()
            self.load_language()
            self.apply_language()
            self.create_menu()

            messagebox.showinfo(
                self.get("messages", "settings_saved", "Settings saved!"),
                self.get("messages", "settings_saved_msg", "Settings have been saved successfully."),
            )
            settings_win.destroy()

        save_btn = ttk.Button(settings_win, text=self.get("ui", "save", "Save"), command=save_settings)
        save_btn.pack(pady=10)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.api_config = {
                        "api_url": cfg.get("api_url", ""),
                        "model_name": cfg.get("model_name", ""),
                    }
                    self.interface_lang = cfg.get("interface_lang", "en")
            except Exception as e:
                load_error = self.get("messages", "load_error", "load error")
                messagebox.showwarning("Warning", f"{load_error} config.json:\n{e}")
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
                load_error_lang_file = self.get("messages", "load_error_lang_file", "load error lang file")
                messagebox.showwarning("Warning", f"{load_error_lang_file} {lang_file}:\n{e}")
                self.lang_data = {}
        else:
            lang_file_missing = self.get("messages", "lang_file_missing", "Language file {file} missing")
            messagebox.showwarning("Warning", f"{lang_file_missing}")
            self.lang_data = {}

    def load_tags(self):
        if os.path.exists(ORDER_TAGS_FILE):
            try:
                with open(ORDER_TAGS_FILE, "r", encoding="utf-8") as f:
                    self.tags_order = json.load(f)
            except Exception as e:
                load_error = self.get("messages", "load_error", "load error")
                messagebox.showinfo("Warning", f"{load_error} '{ORDER_TAGS_FILE}':\n{e}")

        if not os.path.exists(TAGS_DIR) or not os.path.isdir(TAGS_DIR):
            messagebox.showinfo(
                "Warning",
                self.get("messages", "dir", "directory")
                + TAGS_DIR
                + self.get("messages", "not_found", " not found"),
            )
            self.prompt_groups = {}
            return

        for group_name in self.tags_order:
            file_path = os.path.join(TAGS_DIR, f"{group_name}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tags = json.load(f)
                        if isinstance(tags, list):
                            self.prompt_groups[group_name] = tags
                        else:
                            messagebox.showinfo(
                                self.get("messages", "warning", "Warning"),
                                self.get("messages", "tags_file_invalid",
                                         "File has invalid format. Expected a list of tags.")
                                .replace("{file}", f"{group_name}.json"),
                            )
                except Exception as e:
                    messagebox.showinfo(
                        self.get("messages", "warning", "Warning"),
                        self.get("messages", "tags_file_load_error", "Failed to load file {file}: {error}")
                        .replace("{file}", f"{group_name}.json")
                        .replace("{error}", str(e)),
                    )
            else:
                messagebox.showinfo(
                    self.get("messages", "warning", "Warning"),
                    self.get("messages", "tags_file_missing", "Tags file missing for group {group}")
                    .replace("{group}", group_name),
                )

        if not self.prompt_groups:
            messagebox.showinfo(
                self.get("messages", "warning", "Warning"),
                self.get("messages", "tags_dir_empty", "Tags directory is empty!"),
            )

    # =================== PROMPT BUILDER UI ===================
    def create_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        label_title = self.get("ui", "choose_tags", f"Choose tags for ")
        for group, tags in self.prompt_groups.items():
            frame = ttk.Frame(self.notebook)

            self.notebook.add(frame, text=self.get("groups", group, group))

            label_group = self.get("groups", group, group)
            label = ttk.Label(frame, text=label_title + label_group)

            label.pack(pady=5)
            self.i18n_widgets[f"{group}_label"] = label

            if "Subject" in group:
                selectmode = tk.SINGLE
            else:
                selectmode = tk.MULTIPLE

            listbox = tk.Listbox(frame, selectmode=selectmode, height=12, width=50)
            for tag in tags:
                listbox.insert(tk.END, tag)
            listbox.pack(pady=5)

            listbox.bind("<<ListboxSelect>>", lambda e, g=group: self.update_selection(g))

            self.tag_list_boxes[group] = listbox

        self.generate_btn = ttk.Button(
            self.root, text=self.get("ui", "generate_btn", "Generate prompt"), command=self.generate_prompt
        )
        self.generate_btn.pack(pady=5)
        self.i18n_widgets["generate_btn"] = self.generate_btn

        self.improve_btn = ttk.Button(
            self.root, text=self.get("ui", "improve_btn", "Improve prompt"), command=self.improve_prompt_thread
        )
        self.improve_btn.pack(pady=5)
        self.i18n_widgets["improve_btn"] = self.improve_btn

        self.result_text = tk.Text(self.root, height=8, wrap="word")
        self.result_text.pack(fill="x", padx=10, pady=5)

    def apply_language(self):
        self.root.title(self.get("ui", "title", "Prompt constructor for image generation"))

        for key, widget in self.i18n_widgets.items():
            widget.config(text=self.get("ui", key, widget.cget("text")))

        for idx, (group, _) in enumerate(self.prompt_groups.items()):
            self.notebook.tab(idx, text=self.get("groups", group, group))

    def update_selection(self, group):
        listbox = self.tag_list_boxes[group]
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

    # =================== GENERATE PROMPT ===================
    def generate_prompt(self):
        parts = []
        for group, tags in self.selected_tags.items():
            if tags:
                parts.append(", ".join(tags))

        if not parts:
            messagebox.showinfo(
                self.get("messages", "warning", "Warning"),
                self.get("messages", "select_tag", "Please select at least one tag!"),
            )
            return

        prompt = ", ".join(parts)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, prompt)

    def improve_prompt_thread(self):
        prompt = self.result_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showinfo(
                self.get("messages", "warning", "Warning"),
                self.get("messages", "generate_first", "Please generate a prompt first!"),
            )
            return

        api_url = self.api_config.get("api_url")
        model_name = self.api_config.get("model_name")
        if not api_url or not model_name:
            messagebox.showinfo(
                self.get("messages", "warning", "Warning"),
                self.get("messages", "set_api", "Please configure API and model in Settings!"),
            )
            return

        self.improve_btn.config(state=tk.DISABLED)
        self.result_text.insert(tk.END, "\n\n[" + self.get("messages", "improving_prompt", "Improving prompt...") + "]")

        self.call_local_llm(api_url, model_name, prompt, self.on_llm_done)

    def on_llm_done(self, enhanced_prompt):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, enhanced_prompt)
        self.improve_btn.config(state=tk.NORMAL)

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
                        ),
                    },
                    {"role": "user", "content": f"Enhance this prompt: {prompt}"},
                ],
                "temperature": 0.7,
                "max_tokens": 512,
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
                enhanced_prompt = "[" + self.get("messages", "timeout_error",
                                                 "Error: LLM response timeout exceeded.") + "]"
                print("[LLM Error]", self.get("messages", "llm_timeout_console", "Model needs more time to generate."))
            except Exception as e:
                enhanced_prompt = "[" + self.get("messages", "llm_error", "Error while calling LLM") + f": {e}]"
                print("[LLM Error]", str(e))

            self.root.after(0, lambda: callback(enhanced_prompt))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = PromptBuilderApp(root)
    root.mainloop()
