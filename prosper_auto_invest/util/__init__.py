import black


def ppprint(o):
    return black.format_str(repr(o), mode=black.Mode())
