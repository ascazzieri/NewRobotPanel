from re import match as re_match

def is_number_regex(s):
    """ Returns True if string is a number. """
    if re_match("^\d+?\.\d+?$", s) is None:
        return s.isdigit()

    return True