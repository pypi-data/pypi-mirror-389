import time
import shutil
from pathlib import Path

def run():
    ascii_path = Path(__file__).parent / "ascii_art.txt"
    if not ascii_path.exists():
        print("❌ ascii_art.txt not found.")
        return

    art = ascii_path.read_text(encoding="utf-8").splitlines()
    term_width = shutil.get_terminal_size().columns
    padded_art = [" " * term_width + line + " " * term_width for line in art]

    banner = "VAN RICKSHAWWWW VAN RICKSHAWWWW"
    banner_pad = " " * term_width + banner + " " * term_width

    try:
        shift = 0
        direction = 1
        while True:
            # Print banner
            print(banner_pad[shift:shift + term_width])

            # Print ASCII art
            for line in padded_art:
                print(line[shift:shift + term_width])

            time.sleep(0.1)
            print("\033[F" * (len(art) + 1), end="")  # move cursor up

            # Bounce logic
            shift += direction
            if shift <= 0 or shift >= len(padded_art[0]) - term_width:
                direction *= -1  # reverse direction
    except KeyboardInterrupt:
        print("\n🛑 Animation stopped.")
