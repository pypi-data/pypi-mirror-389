def text_to_ascii(text):
    return "\n".join([" ".join(list(text.upper())) for _ in range(3)])

def text_shadow(text):
    return f"{text}\n  {text}"

def text_outline(text):
    border = "*" * (len(text) + 4)
    return f"{border}\n* {text} *\n{border}"
