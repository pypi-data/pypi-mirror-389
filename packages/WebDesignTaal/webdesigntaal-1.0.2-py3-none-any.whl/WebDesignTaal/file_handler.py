"""file_handler.py

De file handler module werkt samen met de parser om een .wdt bestand om te kunnen zetten in html

"""

# file_handler.py
import os
from . import wdt_parser  # gebruik relatief importeren als module

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
    html = render_code(code)

    # 3. maak output folder als die niet bestaat
    os.makedirs(output_dir, exist_ok=True)

    # 4. schrijf index.html
    output_file = os.path.join(output_dir, "index.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Code gegenereerd in {output_file}. Gebruik je een style of code tag? \
Vergeet dan niet om je .css en/of .js bestanden in dezelfde map te slepen.")
    return output_file

def main():
    """Entry point voor de command-line tool."""
    import sys
    if len(sys.argv) < 3:
        print("Gebruik: wdt <pad_naar_wdt_bestand> <naam_van_output_map>")
        sys.exit(1)

    wdt_path = sys.argv[1]
    output_map = sys.argv[2]
    file_conversion(wdt_path, output_map)

# Alleen uitvoeren als standalone script
if __name__ == "__main__":
    main()
