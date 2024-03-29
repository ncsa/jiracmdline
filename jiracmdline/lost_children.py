#!/usr/local/bin/python3

import argparse
import jira_connection
import libcmdline
import libjira
import liblink
import libweb
import logging
import os
import sys
from simple_issue import simple_issue


# Module level resources
resources = {}


def reset():
    global resources
    resources = {}


def get_args( params=None ):
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Find issues with missing meta-data or conflicting with the Epic-Story-Child model.',
            'epilog': (
                'Environment Variables:\n'
                '    NETRC:\n'
                '        Jira login credentials should be stored in ~/.netrc.\n'
                '        Machine name should be hostname only.\n'
                '    JIRA_PROJECT:\n'
                '        Default jira project (if not specified on cmdline).\n'
            )
        }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-q', '--quiet', action='store_true' )
        parser.add_argument( '-p', '--project',
            help="Jira project from which to search for issues." )
        # raw output requested by web form
        parser.add_argument( '--output_format',
            choices=['text', 'raw' ],
            default='text',
            help=argparse.SUPPRESS )
        resources[key] = parser.parse_args( params )
    return resources[key]


def get_project():
    key = 'project'
    if key not in resources:
        args = get_args()
        if args.project:
            resources[key] = args.project
        else:
            try:
                resources[key] = os.environ['JIRA_PROJECT']
            except KeyError:
                msg = (
                    'No jira project specified.'
                    ' Set JIRA_PROJECT or specify via cmdline option.'
                )
                # logging.exception( msg )
                raise UserWarning( msg )
    return resources[key]


def get_errors():
    key = 'errors'
    if key not in resources:
        resources[key] = []
    return resources[key]


def error( msg ):
    get_errors().append( f'Error: {msg}' )
    set_exit_code(3)


def get_warnings():
    key = 'warnings'
    if key not in resources:
        resources[key] = []
    return resources[key]


def warn( msg ):
    get_warnings().append( f'Warning: {msg}' )
    set_exit_code(2)


def get_exit_code():
    key = 'exit_code'
    try:
        rv = resources[key]
    except KeyError:
        rv = 0
    return rv


def set_exit_code( new_code ):
    key = 'exit_code'
    try:
        resources[key] = max( resources[key], new_code )
    except KeyError:
        resources[key] = new_code


def run( current_user=None, **kwargs ):
    parts = None
    if not current_user:
        # started from cmdline
        current_user = jira_connection.Jira_Connection( libjira.jira_login() )
    else:
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        logging.debug( f"KWARGS: '{parts}'" )
    args = get_args( params=parts )
    logging.debug( f"ARGS: '{args}'" )
    problem_issues = []

    logging.debug( 'Check for resolved stories with unresolved children' )
    jql = f'project = {get_project()} and resolved is not EMPTY and type in (Story)'
    stories = current_user.run_jql( jql )
    for s in stories:
        children = current_user.get_linked_children( s )
        for c in children:
            if not c.fields.resolution:
                si = simple_issue.from_src( src=s, jcon=current_user )
                si.notes = f"Resolved story with unresolved child: '{c.key}'"
                problem_issues.append( si )
                break
        try:
            liblink.check_for_link_problems( s )
        except UserWarning as e:
            si = simple_issue.from_src( src=s, jcon=current_user )
            si.notes = str(e)
            problem_issues.append( si )

    logging.debug( 'Get unresolved issues for link problems' )
    jql = f'project = {get_project()} and resolved is EMPTY and type not in (Epic)'
    jira_issues = current_user.run_jql( jql )
    for i in jira_issues:
        try:
            liblink.check_for_link_problems( i )
        except UserWarning as e:
            si = simple_issue.from_src( src=i, jcon=current_user )
            si.notes = str(e)
            problem_issues.append( si )

    # render output
    if args.output_format == 'text':
        if not args.quiet:
            if len( problem_issues ) > 0:
                set_exit_code(1)
                headers = ( 'key', 'notes' )
                libcmdline.text_table( headers, problem_issues )
            for w in get_warnings():
                print( w )
            for e in get_errors():
                print( e )
        sys.exit( get_exit_code() )
    else:
        headers = ( 'key', 'summary', 'epic', 'links', 'notes' )
        return {
            'headers': headers,
            'issues': problem_issues,
            'errors': get_errors(),
            'messages': get_warnings(),
        }


if __name__ == '__main__':
    args = get_args()

    # Configure logging
    loglvl = logging.WARNING
    if args.verbose:
        loglvl = logging.INFO
    if args.debug:
        loglvl = logging.DEBUG
    fmtstr = '%(levelname)s:%(pathname)s.%(module)s.%(funcName)s[%(lineno)d] %(message)s'
    logging.basicConfig( level=loglvl, format=fmtstr )

    no_debug = [
        'urllib3',
    ]
    for key in no_debug:
        logging.getLogger(key).setLevel(logging.CRITICAL)

    run()
