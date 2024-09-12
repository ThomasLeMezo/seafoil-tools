import os

def create_linux_shortcut(directory_path, script_path, shortcut_name):
    """Create a .desktop shortcut on the Linux desktop."""
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    shortcut_path = os.path.join(desktop, f"{shortcut_name}.desktop")

    # Create the .desktop file with the appropriate content
    shortcut_content = f"""[Desktop Entry]
Type=Application
Name={shortcut_name}
# source .zshrc and execute the script
Exec=zsh -c 'cd {directory_path} && source ~/.zshrc && python3 {script_path}'
Icon=preferences-system
Terminal=true
"""

    # Write to the .desktop file
    with open(shortcut_path, 'w') as file:
        file.write(shortcut_content)

    # Make the .desktop file executable
    os.chmod(shortcut_path, 0o755)
    print(f"Shortcut created on the desktop: {shortcut_path}")

def main():
    # The path to the Python script you want to create a shortcut for
    python_script_path = os.path.abspath('seafoil.py')

    # Get the directory path of the Python script
    directory_path = os.path.dirname(python_script_path)

    # Create a shortcut named "MyPythonProgram" on the desktop
    create_linux_shortcut(directory_path=directory_path, script_path=python_script_path, shortcut_name="Seafoil")

    # Set the file permissions of the script to be executable
    os.chmod(python_script_path, 0o755)

if __name__ == "__main__":
    main()