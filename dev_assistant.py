from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).parent

REQUIRED_DIRS = [
    "agents",
    "skills",
    "tools",
    "data",
]

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    ".env",
    ".gitignore",
    "tools/openai_client.py",
    "tools/file_loader.py",
    "tools/book_metadata_tool.py",
    "skills/literacy_skills.py",
]

REQUIRED_PACKAGES = [
    "streamlit",
    "openai",
    "python-dotenv",
    "pandas",
    "pillow",
    "requests",
]


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def check_project_structure():
    print_header("PAAI Project Structure Check")

    print(f"Project root: {PROJECT_ROOT}")

    print("\nFolders:")
    for folder in REQUIRED_DIRS:
        path = PROJECT_ROOT / folder
        status = "OK" if path.exists() else "MISSING"
        print(f"  {status}: {folder}")

    print("\nFiles:")
    for file_name in REQUIRED_FILES:
        path = PROJECT_ROOT / file_name
        status = "OK" if path.exists() else "MISSING"
        print(f"  {status}: {file_name}")


def create_missing_structure():
    print_header("Creating Missing Folders and Package Files")

    for folder in REQUIRED_DIRS:
        path = PROJECT_ROOT / folder
        path.mkdir(exist_ok=True)
        print(f"OK: ensured folder exists: {folder}")

    for package_folder in ["agents", "skills", "tools"]:
        init_file = PROJECT_ROOT / package_folder / "__init__.py"
        init_file.touch(exist_ok=True)
        print(f"OK: ensured package file exists: {package_folder}/__init__.py")


def check_env_file():
    print_header(".env Check")

    env_path = PROJECT_ROOT / ".env"

    if not env_path.exists():
        print("MISSING: .env file does not exist.")
        print("Create it with this line:")
        print("OPENAI_API_KEY=your_actual_api_key_here")
        return

    content = env_path.read_text(encoding="utf-8")

    if "OPENAI_API_KEY=" not in content:
        print("WARNING: .env exists, but OPENAI_API_KEY was not found.")
        print("Expected format:")
        print("OPENAI_API_KEY=your_actual_api_key_here")
        return

    key_line = [
        line for line in content.splitlines()
        if line.strip().startswith("OPENAI_API_KEY=")
    ]

    if not key_line:
        print("WARNING: OPENAI_API_KEY line was not found.")
        return

    value = key_line[0].split("=", 1)[1].strip()

    if not value or value == "your_actual_api_key_here":
        print("WARNING: OPENAI_API_KEY exists but does not look filled in.")
    else:
        print("OK: OPENAI_API_KEY appears to be set.")
        print("Safety: key value is hidden and was not printed.")


def check_requirements():
    print_header("requirements.txt Check")

    req_path = PROJECT_ROOT / "requirements.txt"

    if not req_path.exists():
        print("MISSING: requirements.txt")
        return

    content = req_path.read_text(encoding="utf-8")

    for package in REQUIRED_PACKAGES:
        if package in content:
            print(f"OK: {package}")
        else:
            print(f"MISSING: {package}")


def write_safe_gitignore():
    print_header("Writing Safe .gitignore")

    gitignore_path = PROJECT_ROOT / ".gitignore"

    safe_content = """.env
.venv/
__pycache__/
.DS_Store
*.pyc
"""

    gitignore_path.write_text(safe_content, encoding="utf-8")
    print("OK: .gitignore updated with safe defaults.")


def list_project_files():
    print_header("PAAI Files")

    for folder in ["agents", "skills", "tools", "data"]:
        folder_path = PROJECT_ROOT / folder

        print(f"\n{folder}/")
        if not folder_path.exists():
            print("  MISSING")
            continue

        for path in sorted(folder_path.iterdir()):
            if path.is_file():
                print(f"  {path.name}")


def run_streamlit():
    print_header("Starting Streamlit")

    app_path = PROJECT_ROOT / "app.py"

    if not app_path.exists():
        print("ERROR: app.py not found.")
        return

    print("Running: streamlit run app.py")
    print("Press Control + C in Terminal to stop the app.")

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            cwd=PROJECT_ROOT,
            check=False,
        )
    except KeyboardInterrupt:
        print("\nStreamlit stopped.")


def show_menu():
    print_header("PAAI Developer Assistant")

    print("""
Choose an option:

1. Check project structure
2. Create missing folders/package files
3. Check .env API key setup
4. Check requirements.txt
5. Write safe .gitignore
6. List agents/skills/tools/data files
7. Run Streamlit app
8. Run all safe checks
0. Exit
""")


def run_all_safe_checks():
    check_project_structure()
    create_missing_structure()
    check_env_file()
    check_requirements()
    list_project_files()


def main():
    while True:
        show_menu()
        choice = input("Enter choice: ").strip()

        if choice == "1":
            check_project_structure()
        elif choice == "2":
            create_missing_structure()
        elif choice == "3":
            check_env_file()
        elif choice == "4":
            check_requirements()
        elif choice == "5":
            write_safe_gitignore()
        elif choice == "6":
            list_project_files()
        elif choice == "7":
            run_streamlit()
        elif choice == "8":
            run_all_safe_checks()
        elif choice == "0":
            print("Exiting PAAI Developer Assistant.")
            break
        else:
            print("Invalid choice. Please enter a number from 0 to 8.")


if __name__ == "__main__":
    main()
