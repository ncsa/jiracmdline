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
            'description': (
                'Display summary of all subordinate issues.'
                'For each issue, find lines in the description that '
            ),
            'epilog': 'NETRC:'
                '    Jira login credentials should be stored in ~/.netrc.'
                '    Machine name should be hostname only.'
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( 'issues', nargs='*' )
        # issues list via web
        parser.add_argument( '--ticket_ids', help=argparse.SUPPRESS )
        # output format = raw for web use
        parser.add_argument( '--output_format',
            choices=['text', 'raw' ],
            default='text',
            help=argparse.SUPPRESS )
        args = parser.parse_args( params )
        if args.ticket_ids:
            args.issues.extend( args.ticket_ids.split() )
        resources[key] = args
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

    # load specified issues from jira
    parents = {}
    simple_parents = []
    for key in args.issues:
        try:
            i = current_user.get_issue_by_key( key )
        except jira.exceptions.JIRAError as e:
            raise UserWarning( e.text )

        i_type = current_user.get_issue_type( i )
        if i_type == 'Epic':
            for p in current_user.get_stories_in_epic( i ):
                parents[ p.key ] = p
                simple_parents.append( simple_issue.from_src( src=p, jcon=current_user.jira ) )
        elif i_type == 'Story':
            parents[ i.key ] = i
            simple_parents.append( simple_issue.from_src( src=i, jcon=current_user.jira ) )
        else:
            raise UserWarning( f'Not a Story or Epic: {key}' )

    simple_parents.sort()
    all_issues = []
    
    for simple_p in simple_parents:
        p = parents[ simple_p.key ]
        logr.debug( f"processing parent '{p}'" )
        try:
            children = current_user.get_linked_children( p )
        except jira.exceptions.JIRAError as e:
            raise UserWarning( e.text )
        simple_children = [ simple_issue.from_src( src=c, jcon=current_user.jira ) for c in children ]
        simple_children.sort()
        all_issues.append( simple_p )
        all_issues.extend( simple_children )

    if args.output_format == 'text':
        # for i in raw_issues:
        #     current_user.print_issue_summary( i )
        raise UserWarning( "needs review ..." )
    else:
        headers = ( 'story', 'child', 'summary', 'due', 'epic', 'links', 'resolution' )
        return {
            'headers': headers,
            'issues': all_issues,
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
