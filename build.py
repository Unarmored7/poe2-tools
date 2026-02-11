
import os
import sys
import subprocess
from PIL import Image

def check_dependencies():
    """Check if required packages are installed."""
    required = ['pyinstaller', 'PIL']
    missing = []
    for pkg in required:
        try:
            if pkg == 'PIL':
                import PIL
            else:
                __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Please run: pip install pyinstaller pillow")
        sys.exit(1)

def convert_icon():
    """Convert icon.png to icon.ico if needed."""
    assets_dir = os.path.join("src", "poe2_tools", "assets") # Keep using src assets as source of truth? 
    # Actually user put icon in project root assets
    project_assets = "assets"
    
    icon_png = os.path.join(project_assets, "icon.png")
    icon_ico = os.path.join(project_assets, "icon.ico")
    
    if os.path.exists(icon_png):
        print(f"Converting {icon_png} to {icon_ico}...")
        try:
            img = Image.open(icon_png)
            img.save(icon_ico, format='ICO', sizes=[(256, 256)])
            print("Icon converted successfully.")
            return icon_ico
        except Exception as e:
            print(f"Error converting icon: {e}")
            sys.exit(1)
    elif os.path.exists(icon_ico):
        # Verify it's a real ICO
        try:
            with open(icon_ico, "rb") as f:
                header = f.read(4)
                if header == b'\x00\x00\x01\x00':
                    print("Existing icon.ico is valid.")
                    return icon_ico
                else:
                    print("Existing icon.ico is invalid (likely renamed PNG).")
                    # Try to convert it as PNG
                    img = Image.open(icon_ico)
                    img.save(icon_ico, format='ICO', sizes=[(256, 256)])
                    print("Fixed invalid icon.ico.")
                    return icon_ico
        except Exception as e:
            print(f"Error checking/fixing icon.ico: {e}")
            sys.exit(1)
    else:
        print("No icon found in assets/")
        return None

def build_exe(icon_path):
    """Run PyInstaller."""
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name=POE2-Tools",
        "--clean",
        "--distpath=dist",
        "--workpath=build",
        f"--add-data={os.path.join('assets', '*')}{os.pathsep}{os.path.join('assets')}", # Add root assets to assets/ in exe
        # Note: app.py looks for assets in project_root/assets OR ../../assets relative to file.
        # In onefile mode, sys._MEIPASS is the root.
        # We need to ensure app.py logic handles sys._MEIPASS or we adjust data structure.
        
        # Simpler: just include assets
    ]
    
    # Adjusting add-data for consistency with app.py's expectation?
    # app.py expects: project_root = ../.. from its location.
    # In frozen exe, structure is flattened or extracted to temp.
    
    # Let's adjust app.py later if needed for frozen state, but standard practice is:
    # Check `sys.frozen`.
    
    if icon_path:
        cmd.append(f"--icon={icon_path}")
        
    cmd.append("main.py")
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

if __name__ == "__main__":
    check_dependencies()
    icon_path = convert_icon()
    build_exe(icon_path)
