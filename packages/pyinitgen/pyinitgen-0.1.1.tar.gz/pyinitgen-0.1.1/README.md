---

# pyinitgen

Automated __init__.py generator for Python packages
Ensures every directory in your project is a proper Python package — no more mysterious ModuleNotFoundError surprises.

Perfect for:

Large refactors

Monorepos / multi-package architectures

Auto-generated project structures

Migration from namespace-less directories

CI environments ensuring package integrity



---

🚀 Features

Feature	Description

📂 Recursive scan	Walks directory tree intelligently
🛠️ Auto-creates __init__.py	Only where missing — safe & precise
🧠 Excludes system/runtime dirs	__pycache__, .git, .venv, etc.
👀 Dry-Run Mode	See what will be created first
🎯 Project-safe	Avoids touching non-Python folders
✨ Emoji status (optional)	Fancy terminal UX
🔒 Zero destructive actions	Never overwrites content



---

📦 Installation

pip install pyinitgen


---

🧠 Usage

✅ Default — scan current directory

pyinitgen

📁 Scan a specific project root

pyinitgen --base-dir src/

🔍 Preview changes (no write)

pyinitgen --dry-run

🗣️ Verbose mode

pyinitgen --verbose

🤐 Quiet mode

pyinitgen --quiet

🛑 Disable emojis

pyinitgen --no-emoji


---

📝 Example Output

Scanning: src/utils
Created src/utils/__init__.py
✅ Operation complete. Scanned 43 dirs, created 8 new __init__.py files.


---

🧩 Why this tool?

Problem	Solution

Large Python codebases without -inits	Auto insert all required files
ModuleNotFoundError during import	Ensures folders become packages
Hand-creating 50+ __init__.py files	One command 🤖
Accidental file writes?	Only creates missing files



---

⚙️ CLI Help

pyinitgen --help


---

🛡️ Safe by Design

Never touches existing files

Ignores system & irrelevant dirs by default

Supports dry-run to preview



---

💡 Tip

Use in CI to guarantee package consistency:

pyinitgen --dry-run


---

🤝 Contributing

PRs welcome — improve detection logic, add custom exclusion rules, enhance output UX.

👉 Repo: https://github.com/dhruv13x/pyinitgen


---

📜 License

MIT


---

🧭 Related Tools in the Suite

Tool	Purpose

importdoc	Import issue diagnosis
import-surgeon	Safe import refactoring
pypurge	Clean caches, venv junk
pyinitgen	Generate missing __init__.py ✅ (this project)



---

⭐ Support

If you like this tool:

⭐ Star the GitHub repo

🐍 Use it in CI & projects

📦 Recommend to Python dev friends



---