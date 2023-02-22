#!/usr/local/bin/python3

import argparse
import jira.exceptions
import libweb
import logging
import re
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
                'Create child tasks from (^TASK) lines in the description.\n\n'
                'For each issue, find lines in the description that '
                'begin with the string "TASK " and create a new '
                'task with the matching line as the summary '
                'and link as "a child of" the parent.'
            ),
            'epilog': 'NETRC:'
                '    Jira login credentials should be stored in ~/.netrc.'
                '    Machine name should be hostname only.'
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-n', '--dryrun', action='store_true',
            help='Show what would be done but make no changes.' )
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


def get_child_summaries( issue ):
    # grab text from all lines starting with TASK
    logr.debug( f'got issue {issue}' )
    summaries = []
    pattern = r'^\s*TASK (.*)$'
    if issue.fields.description:
        for m in re.finditer( pattern, issue.fields.description, re.MULTILINE ):
            logr.debug( f'match {m}' )
            summaries.append( m.group(1).strip() )
    else:
        raise UserWarning( f"Issue '{issue.key}' has an empty description." )
    return summaries


def mk_children_from_description( current_user, issue ):
    children = []
    args = get_args()
    summaries = get_child_summaries( issue )
    if summaries:
        children = current_user.mk_child_tasks(
            parent=issue,
            child_summaries=summaries,
            dryrun=args.dryrun
        )
    else:
        raise UserWarning( f"No TASK lines found in '{issue}'s description." )
    return children


def run( current_user=None, **kwargs ):
    if not current_user:
        # need to make an instance of user.User (a logged in user)
        raise UserWarning( "needs updates yet for cmdline" )
    else:
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        print( f"KWARGS: '{parts}'" )
    args = get_args( params=parts )
    print( f"ARGS: '{args}'" )

    # load specified issues from jira
    parents = []
    children = []
    try:
        parents = current_user.get_issues_by_keys( args.issues )
    except jira.exceptions.JIRAError as e:
        error( e.text )
    raw_issues = []
    for p in parents:
        logr.debug( f'got issue {p}' )
        try:
            children = mk_children_from_description( current_user, p )
        except UserWarning as e:
            warn( str( e ) )
            continue
        if children:
            raw_issues.append( p )
            # assign parent's epic to each child
            # TODO - catch jira error
            epic_key = current_user.get_epic_name( p )
            if not args.dryrun:
                current_user.add_tasks_to_epic( children, epic_key )
            raw_issues.extend( current_user.reload_issues( children ) )
    if args.output_format == 'text':
        for i in raw_issues:
            current_user.print_issue_summary( i )
    else:
        headers = ( 'story', 'child', 'summary', 'epic', 'links' )
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
