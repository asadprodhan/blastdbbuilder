import os
import shutil
import sys
import subprocess
from pathlib import Path
from importlib.resources import files

APP_ID = "blastdbbuilder-gui"
APP_NAME = "blastdbbuilder GUI"


def install_desktop_shortcut():

    if not sys.platform.startswith("linux"):
        print("Desktop launcher supported only on Linux.")
        return

    home = Path.home()

    applications_dir = home / ".local/share/applications"
    icons_dir = home / ".local/share/icons/hicolor/256x256/apps"
    desktop_dir = home / "Desktop"

    applications_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)

    # copy icon
    icon_src = files("blastdbbuilder_gui").joinpath("icons/blastdbbuilder.png")
    icon_dst = icons_dir / f"{APP_ID}.png"

    try:
        shutil.copy(icon_src, icon_dst)
    except Exception as e:
        print("Icon install warning:", e)

    # create launcher
    desktop_file = applications_dir / f"{APP_ID}.desktop"

    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=GUI for blastdbbuilder
Exec=blastdbbuilder-gui
Icon={APP_ID}
Terminal=false
Categories=Science;Bioinformatics;
"""

    desktop_file.write_text(content)

    # make executable
    os.chmod(desktop_file, 0o755)

    print("Application launcher installed:")
    print(desktop_file)

    # copy to Desktop
    if desktop_dir.exists():

        desktop_shortcut = desktop_dir / f"{APP_ID}.desktop"

        shutil.copy(desktop_file, desktop_shortcut)
        os.chmod(desktop_shortcut, 0o755)

        # mark trusted (fix GNOME "Allow Launching")
        try:
            subprocess.run(
                ["gio", "set", str(desktop_shortcut),
                 "metadata::trusted", "true"],
                check=False
            )
        except Exception:
            pass

        print("Desktop shortcut created:")
        print(desktop_shortcut)

    # refresh desktop database
    os.system("update-desktop-database ~/.local/share/applications >/dev/null 2>&1 || true")

    print("Done. You can now double-click the Desktop icon.")


def main():
    # entry point for: blastdbbuilder-gui-desktop
    return install_desktop_shortcut()

if __name__ == "__main__":
    raise SystemExit(main())

