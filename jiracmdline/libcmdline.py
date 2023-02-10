from tabulate import tabulate


def text_table( headers, issues ):
    # make a list of lists of only the requested cols in headers
    data = []
    for i in issues:
        data.append( [ getattr(i, h) for h in headers ] )
    print( tabulate( data, headers ) )


if __name__ == '__main__':
    raise UserWarning( 'Invocation error; not a standalone script.' )
