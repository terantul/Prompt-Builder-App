# Prompt Builder App

**Prompt Builder App** is a graphical prompt constructor for image generation using a Local Large Language Model (LLM) and tag-based input. The project is implemented in Python with Tkinter.

## Features
- Select tags for prompt generation.
- Generate and enhance prompts via a local LLM API (using a local model).
- Multi-language interface support (language JSON files, e.g., `ua.json`), with English as the default language.
- Save API and model settings in `config.json`.
- Support for single or multiple tag selection depending on the group.

## Project Structure
<pre>.
├── main.py # Main application code
├── config.json # API and model settings
├── tags/ # JSON files containing tag groups
│ ├── Subject.json
│ ├── Style.json
│ └── ...
├── tags_order.json # Order for loading tag groups
├── lang/ # Language JSON files for UI
│ └── ua.json
└── requirements.txt # Python dependencies
</pre>

## Installation

1. Clone the repository:
<pre>
git clone <URL>
cd <repo>
Create a virtual environment (recommended):

python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
Install dependencies:

pip install -r requirements.txt

Usage
Run the application:

python main.py
</pre>

Configure your API and model via the Settings menu.

Select tags for prompt generation.

Click Generate prompt to create a prompt.

Click Improve prompt to enhance the prompt via LLM.

Configuration Files
config.json — stores API and model settings.

tags_order.json — defines the order of loading tag groups.

tags/ — JSON files containing tags for each group.

lang/ — language files for the interface (e.g., ua.json for Ukrainian).