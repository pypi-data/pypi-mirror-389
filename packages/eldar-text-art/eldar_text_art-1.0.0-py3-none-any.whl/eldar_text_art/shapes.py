def text_triangle(text, size=5):
    return "\n".join([text * i for i in range(1, size + 1)])

def text_square(text, size=5):
    return "\n".join([text * size for _ in range(size)])

def text_diamond(text, size=5):
    pattern = []
    for i in range(size):
        spaces = " " * (size - i - 1)
        pattern.append(spaces + text * (2 * i + 1))
    for i in range(size - 2, -1, -1):
        spaces = " " * (size - i - 1)
        pattern.append(spaces + text * (2 * i + 1))
    return "\n".join(pattern)
