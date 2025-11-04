def create_banner(text, symbol="="):
    line = symbol * (len(text) + 4)
    return f"{line}\n| {text} |\n{line}"

def bordered_text(text):
    border = "+" + "-" * (len(text) + 2) + "+"
    return f"{border}\n| {text} |\n{border}"

def centered_text(text, width=40):
    return text.center(width, " ")
