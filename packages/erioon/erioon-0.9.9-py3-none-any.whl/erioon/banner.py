from rich.console import Console
from rich.text import Text


def print_banner():
    console = Console()

    letters = {
        "E": [
            "████████████▒▒",
            "████████████▒▒",
            "████▒▒        ",
            "████▒▒        ",
            "██████████▒▒  ",
            "████▒▒        ",
            "████▒▒        ",
            "████████████▒▒",
            "████████████▒▒",
        ],
        "R": [
            "███████████▒▒",
            "███████████▒▒",
            "████▒▒   ███▒▒",
            "████▒▒   ███▒▒",
            "██████████▒▒ ",
            "█████████▒▒  ",
            "████▒▒  ███▒▒",
            "████▒▒   ███▒▒",
            "████▒▒    ███▒▒",
        ],
        "I": [
            " ███████████▒▒",
            " ███████████▒▒",
            "    ███▒▒",
            "    ███▒▒",
            "     ███▒▒",
            "     ███▒▒",
            "     ███▒▒",
            " ██████████▒▒",
            "██████████▒▒",
        ],
        "O": [
            " ████████▒▒  ",
            "██████████▒▒ ",
            "    ████▒▒  ███▒▒ ",
            "    ████▒▒  ███▒▒ ",
            "    ████▒▒  ███▒▒ ",
            "    ████▒▒  ███▒▒ ",
            "    ████▒▒  ███▒▒ ",
            "██████████▒▒ ",
            " ████████▒▒  ",
        ],
        "0": [
            "  ████████▒▒  ",
            " ██████████▒▒ ",
            "████▒▒  ███▒▒ ",
            "████▒▒  ███▒▒ ",
            "████▒▒  ███▒▒ ",
            "████▒▒  ███▒▒ ",
            "████▒▒  ███▒▒ ",
            " ██████████▒▒ ",
            "  ████████▒▒  ",
        ],
        "N": [
            " ████▒▒    ████▒▒",
            " █████▒▒   ████▒▒",
            "██████▒▒  ████▒▒",
            "████▒██▒▒ ████▒▒",
            "████▒▒████████▒▒",
            "████▒▒   █████▒▒",
            "████▒▒    ████▒▒",
            " ████▒▒     ███▒▒",
            " ████▒▒      ██▒▒",
        ],
    }

    banner_lines = [""] * 9
    for char in "ERIO0N":
        char_pattern = letters[char]
        for i in range(9):
            banner_lines[i] += char_pattern[i] + "  "

    def get_gradient(start_hex, end_hex, steps):
        start_hex = start_hex.lstrip("#")
        end_hex = end_hex.lstrip("#")
        sr, sg, sb = (
            int(start_hex[0:2], 16),
            int(start_hex[2:4], 16),
            int(start_hex[4:6], 16),
        )
        er, eg, eb = int(end_hex[0:2], 16), int(end_hex[2:4], 16), int(end_hex[4:6], 16)
        gradient = []
        for i in range(steps):
            r = int(sr + (er - sr) * i / (steps - 1))
            g = int(sg + (eg - sg) * i / (steps - 1))
            b = int(sb + (eb - sb) * i / (steps - 1))
            gradient.append(f"#{r:02x}{g:02x}{b:02x}")
        return gradient

    total_chars = max(len(line) for line in banner_lines)
    colors = get_gradient("#3A3A3A", "#ffffff", total_chars)

    # Render banner with gradient
    gradient_text = Text()
    for line in banner_lines:
        for i, char in enumerate(line):
            gradient_text.append(char, style=f"bold {colors[i]}")
        gradient_text.append("\n")

    console.print(gradient_text)
    console.print("Build anything with Erioon - www.erioon.com", style="bold white", justify="start")
    console.print("\n")
