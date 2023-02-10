#!/usr/local/bin/python3

import argparse
import libjira
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
        # jira session id (from web form)
        parser.add_argument( '--jira_session_id', help=argparse.SUPPRESS )
        resources[key] = parser.parse_args( params )
    return resources[key]


def get_jira():
    return libjira.get_jira( get_args().jira_session_id )


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


# def mk_children_from_description( issue ):
#     args = get_args()
#     j = libjira.get_jira()
#     summaries = split_issue_description( issue )
#     children = libjira.mk_child_tasks( parent=issue, child_summaries=summaries )
#     return children


def run( **kwargs ):
    parts = libweb.process_kwargs( kwargs )
    if parts:
        reset()
    print( f"KWARGS: '{parts}'" )
    args = get_args( params=parts )
    print( f"ARGS: '{args}'" )

    jc = get_jira() #jira_connection

    # process text into child task summaries
    summaries = mk_summaries( args.new_child_text )
    if not summaries:
        raise UserWarning( 'unable to make summaries from text' )
    
    # get parent from jira
    parent = jc.get_issue_by_key( args.parent )
    if not parent:
        raise UserWarning( f"No such ticket '{args.parent}'" )

    # get parent epic
    epic = jc.get_epic_name( parent )
    if not epic:
        raise UserWarning( f"Parent '{parent.key}' has no Epic" )

    children = jc.mk_child_tasks( parent=parent, child_summaries=summaries )
    jc.add_tasks_to_epic( children, epic )
    parent = jc.reload_issue( parent )

    if args.output_format == 'text':
        jc.print_issue_summary( parent )
    else:
        headers = ( 'story', 'child', 'summary', 'epic', 'links' )
        raw_issues = [ parent ]
        raw_issues.extend( jc.reload_issues( children ) )
        issues = [ simple_issue.from_src( src=i, jcon=jc ) for i in raw_issues ]
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
