#!/usr/local/bin/python3

import argparse
import jira_connection
import libcmdline
import libjira
import liblink
import libutil
import libweb
import logging
import os
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
            'description': 'Find child issues having no Epic.',
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


def get_warnings():
    key = 'warnings'
    if key not in resources:
        resources[key] = []
    return resources[key]


def warn( msg ):
    get_warnings().append( f'Warning: {msg}' )


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

    logging.debug( 'Get incomplete tasks' )
    jql = f'project = {get_project()} and resolved is EMPTY and type not in (Epic)'
    tasks = current_user.run_jql( jql )

    logging.debug( "Check tasks for link problems" )
    issues = []
    for task in tasks:
        try:
            liblink.check_for_link_problems( task )
        except UserWarning as e:
            si = simple_issue.from_src( src=task, jcon=current_user )
            si.notes = str(e)
            issues.append( si )

    # render output
    args = get_args()
    headers = ( 'key', 'summary', 'epic', 'links', 'notes' )
    if args.output_format == 'text':
        libcmdline.text_table( headers, issues )
        for w in get_warnings():
            print( w )
        for e in get_errors():
            print( e )
    else:
        return {
            'headers': headers,
            'issues': issues,
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
