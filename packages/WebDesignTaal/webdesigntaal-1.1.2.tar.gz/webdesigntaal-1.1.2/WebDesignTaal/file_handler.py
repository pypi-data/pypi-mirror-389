"""file_handler.py

De file handler module werkt samen met de parser om een .wdt bestand om te kunnen zetten in html

"""

# file_handler.py
import os
import sys
from . import wdt_parser  # gebruik relatief importeren als module
from .updater import auto_update, get_local_version

def render_code(code: str) -> str:
    """Render de WDT code naar HTML via de parser module."""
    return wdt_parser.render_code(code)

def file_conversion(wdt_file: str, output_dir: str = None):
    """
    Converteer een .wdt bestand naar een volledige website folder met index.html.
    
    Parameters:
        wdt_file: pad naar het WDT bestand
        output_dir: pad naar de folder waar de site wordt gegenereerd. 
                    Standaard: 'output' in dezelfde folder als wdt_file
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(wdt_file)), "output")

    # 1. lees WDT file
    if not os.path.exists(wdt_file):
        raise FileNotFoundError(f"WDT file '{wdt_file}' bestaat niet.")

    with open(wdt_file, "r", encoding="utf-8") as f:
        code = f.read()

    # 2. render HTML
    try:
        html = render_code(code)
    except ValueError as e:
        print(e)
        sys.exit(1)
 
    # 3. maak output folder als die niet bestaat
    os.makedirs(output_dir, exist_ok=True)

    # 4. schrijf index.html
    output_file = os.path.join(output_dir, "index.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Code gegenereerd in {output_file}. \n\nGebruik je een 'stijl' of 'code' tag?\
 Vergeet dan niet om je .css en/of .js bestanden in dezelfde map te slepen. ({output_dir})")
    return output_file

def main():
    """Entry point voor de command-line tool."""
    auto_update()

    if len(sys.argv) == 2:
        # Check for updates
        if sys.argv[1] == "-u" or sys.argv[1] == "--update":
            auto_update()
            sys.exit(0)

        if sys.argv[1] == "-v" or sys.argv[1] == "--version":
            print(get_local_version())
            print("Gebruik wdt --update om te checken voor nieuwe updates en ze te installeren")
            sys.exit(0)

    if len(sys.argv) < 3 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("Gebruik: wdt <pad_naar_wdt_bestand> <naam_van_output_map>\nUpdate: wdt --update\nCheck versie: wdt --version")
        sys.exit(1)

    wdt_path = sys.argv[1]
    output_map = sys.argv[2]
    file_conversion(wdt_path, output_map)
    sys.exit(0)

# Alleen uitvoeren als standalone script
if __name__ == "__main__":
    main()
