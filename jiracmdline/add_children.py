#!/usr/local/bin/python3

import argparse
import jira.exceptions
import libweb
import logging
from simple_issue import simple_issue

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def reset():
    global resources
    resources = {}


def get_args( params=None ):
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Create child tasks from stdin, split on newline.',
            'epilog': 'NETRC:'
                '    Jira login credentials should be stored in ~/.netrc.'
                '    Machine name should be hostname only.'
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-n', '--dryrun', action='store_true',
            help='Show what would be done but make no changes.' )
        parser.add_argument( '--parent', 
            help='Ticket-id of parent, to which children tasks will be added.' )
        parser.add_argument( 'text', nargs='*',
            help='Text to process for new task summaries, one per line.' )
        # text from the web
        parser.add_argument( '--new_child_text', help=argparse.SUPPRESS )
        # output format = raw for web use
        parser.add_argument( '--output_format',
            choices=['text', 'raw' ],
            default='text',
            help=argparse.SUPPRESS )
        resources[key] = parser.parse_args( params )
    return resources[key]


def get_errors():
    key = 'errors'
    if key not in resources:
        resources[key] = []
    return resources[key]


def error( msg ):
    get_errors().append( f'Error: {msg}' )


def get_warnings():
    key = 'warnings'
    if key not in resources:
        resources[key] = []
    return resources[key]


def warn( msg ):
    get_warnings().append( f'Warning: {msg}' )


def mk_summaries( text ):
    # split lines into array, remove leading list chars, white space
    lines = [ x.strip('*# ').strip() for x in text.splitlines() ]
    # filter out blank lines
    filtered_lines = filter( len, lines )
    return filtered_lines


def run( current_user=None, **kwargs ):
    if not current_user:
        raise UserWarning( "needs updates yet for cmdline" )
    else:
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        print( f"KWARGS: '{parts}'" )
    args = get_args( params=parts )
    print( f"ARGS: '{args}'" )

    # process text into child task summaries
    summaries = mk_summaries( args.new_child_text )
    if not summaries:
        raise UserWarning( 'unable to make summaries from text' )
    
    # get parent from jira
    try:
        parent = current_user.get_issue_by_key( args.parent )
    except jira.exceptions.JIRAError as e:
        raise UserWarning( f"No such ticket '{args.parent}'" )

    # get parent epic
    epic = current_user.get_epic_key( parent )
    if not epic:
        raise UserWarning( f"Parent '{parent.key}' has no Epic" )

    children = current_user.mk_child_tasks( parent=parent, child_summaries=summaries )
    current_user.add_tasks_to_epic( children, epic )
    parent = current_user.reload_issue( parent )

    if args.output_format == 'text':
        current_user.print_issue_summary( parent )
    else:
        headers = ( 'story', 'child', 'summary', 'epic', 'links' )
        raw_issues = [ parent ]
        raw_issues.extend( current_user.reload_issues( children ) )
        issues = [ simple_issue.from_src( src=i, jcon=current_user.jira ) for i in raw_issues ]
        return {
            'headers': headers,
            'issues': issues,
            'errors': get_errors(),
            'messages': get_warnings(),
        }


if __name__ == '__main__':
    args = get_args()

    # configure logging
    loglvl = logging.WARNING
    if args.verbose or args.dryrun:
        loglvl = logging.INFO
    if args.debug:
        loglvl = logging.DEBUG
    logr.setLevel( loglvl )
    logfmt = logging.Formatter( '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s' )
    ch = logging.StreamHandler()
    ch.setFormatter( logfmt )
    logr.addHandler( ch )

    # start processing
    run()
