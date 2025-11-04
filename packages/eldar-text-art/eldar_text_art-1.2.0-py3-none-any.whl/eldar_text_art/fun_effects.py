import time
import sys
import math

def wave_text(text, amplitude=2, frequency=0.3):
    result = []
    for i, char in enumerate(text):
        spaces = int(amplitude * (1 + math.sin(frequency * i)))
        result.append(' ' * spaces + char)
    return '\n'.join(result)

def typing_effect(text, delay=0.05):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def heart_border(text):
    heart = '?'
    line = heart * (len(text) + 4)
    return f"{line}\n{heart} {text} {heart}\n{line}"

def neon_text(text):
    return f"\033[95m{text}\033[0m"

def rainbow_wave(text):
    colors = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += f"{color}{char}\033[0m"
    return result
