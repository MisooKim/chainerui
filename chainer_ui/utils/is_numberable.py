''' is_numberable.py '''


def is_numberable(number_str):
    ''' is_numberable '''
    try:
        int(number_str)
    except:
        return False
    return True