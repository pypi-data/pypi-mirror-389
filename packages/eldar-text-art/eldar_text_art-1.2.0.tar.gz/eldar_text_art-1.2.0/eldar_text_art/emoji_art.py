def safe_emoji(char, fallback='*'):
    try:
        return char.encode('utf-8').decode('utf-8')
    except Exception:
        return fallback

def emoji_banner(text, emoji='??'):
    e = safe_emoji(emoji)
    line = e * (len(text) + 4)
    return f"{line}\n{e} {text} {e}\n{line}"

def emoji_box(text, emoji='?'):
    e = safe_emoji(emoji)
    border = e * (len(text) + 4)
    return f"{border}\n{e} {text} {e}\n{border}"

def emoji_shape(emoji='??', size=5):
    e = safe_emoji(emoji)
    pattern = []
    for i in range(size):
        pattern.append(e * (i + 1))
    for i in range(size - 2, -1, -1):
        pattern.append(e * (i + 1))
    return "\n".join(pattern)
