#!/usr/local/bin/python3

# import libcmdline
import argparse
import jira_connection
import libjira
import liblink
import libutil
import libweb
import logging
import os
import pprint
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
            'description': 'Find issues having no Epic.',
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
        parser.add_argument( '-a', '--autofix', action='store_true' )
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
        raise UserWarning('not allowed')
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        logging.debug( f"KWARGS: '{parts}'" )
    args = get_args( params=parts )
    logging.debug( f"ARGS: '{args}'" )

    logging.info( 'Get incomplete issues that have no epic link' )
    jql = (
        f'project = {get_project()}'
        ' and resolved is EMPTY'
        ' and type not in (Epic)'
        ' and "Epic Link" is EMPTY'
        )
    logging.debug( f"jql: '{jql}'" )
    # with libutil.timeblock( 'get all issues w/o epic' ):
    issues = current_user.run_jql( jql )

    updates = {}
    for i in issues:
        issue_type = current_user.get_issue_type( i ).lower()
        if issue_type == 'story':
            epic = current_user.get_epic_key( i )
            logging.debug( f"got epic {epic} for story {i}" )
        else:
            p = liblink.get_linked_parent( i )
            p = current_user.reload_issue( p )
            epic = current_user.get_epic_key( p )
            logging.debug( f"got epic {epic} for parent {p} of issue {i}" )
        if epic not in updates:
            updates[epic] = []
        updates[epic].append( i )

    for epic, issue_list in updates.items():
        print( f"Add to epic {epic}:" )
        print( '\n'.join( map( str, issue_list ) ) )
        if args.autofix:
            current_user.add_tasks_to_epic( issue_list, epic )
            print( 'Autofixed' )

    # # render output
    # args = get_args()
    # headers = ( 'key', 'summary', 'epic', 'links', 'notes' )
    # if args.output_format == 'text':
    #     # libcmdline.text_table( headers, issues )
    #     for w in get_warnings():
    #         print( w )
    #     for e in get_errors():
    #         print( e )
    # else:
    #     return {
    #         'headers': headers,
    #         # 'issues': issues,
    #         'errors': get_errors(),
    #         'messages': get_warnings(),
    #     }


if __name__ == '__main__':
    args = get_args()

    # Configure logging
    loglvl = logging.WARNING
    if args.verbose:
        loglvl = logging.INFO
    if args.debug:
        loglvl = logging.DEBUG
    fmtstr = '%(levelname)s:%(pathname)s.%(module)s.%(funcName)s[%(lineno)d] %(message)s'
    logging.basicConfig( force=True, level=loglvl, format=fmtstr )

    no_debug = [
        'urllib3',
    ]
    for key in no_debug:
        logging.getLogger(key).setLevel(logging.CRITICAL)

    run()
