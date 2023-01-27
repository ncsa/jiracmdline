import re


def sanitize_key( key ):
    return re.sub( '[^a-zA-Z0-9_-]', '', key )


def sanitize_val( val ):
    temp = re.sub( ',', ' ', val )
    return re.sub( '[^ a-zA-Z0-9_-]', '', temp )


def process_kwargs( kwargs ):
    parts = []
    for k,v in kwargs.items():
        key = sanitize_key( k )
        val = sanitize_val( v )
        parts.extend( [ f'--{key}', val ] )
    if not parts: # if list is empty
        parts = None
    return parts


if __name__ == '__main__':
    raise UserWarning( 'Invocation error; not a standalone script.' )
