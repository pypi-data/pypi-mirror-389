def rainbow_text(text):
    colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
    return "".join(f"[{colors[i % len(colors)]}]{char}" for i, char in enumerate(text))

def mirror_text(text):
    return text + " | " + text[::-1]

def glitch_text(text):
    import random
    glitched = ""
    for char in text:
        if random.random() > 0.8:
            glitched += random.choice("!@#$%^&*()")
        else:
            glitched += char
    return glitched
