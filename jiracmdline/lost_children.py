#!/usr/local/bin/python3

import argparse
import libcmdline
import libweb
import logging
import os
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
        # jira session id (from web form)
        parser.add_argument( '--jira_session_id', help=argparse.SUPPRESS )
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
                # logr.exception( msg )
                raise UserWarning( msg )
    return resources[key]


def run( current_user=None, **kwargs ):
    if not current_user:
        # need to create current_user (a logged in user)
        raise UserWarning( "needs updates yet for cmdline" )
    else:
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        print( f"KWARGS: '{parts}'" )
    args = get_args( params=parts )
    print( f"ARGS: '{args}'" )

    logr.debug( "Get all the tasks that don't have an epic link" )
    jql = f'project = {get_project()} and type = Task and "Epic Link" is EMPTY'
    tasks = current_user.run_jql( jql )

    logr.debug( "filter out tasks that don't have a \"linked parent\"" )
    issues = []
    for task in tasks:
        p = current_user.get_linked_parent( task )
        if p:
            # attempt to find parent's Epic
            epic = current_user.get_epic_name( task )
            if epic:
                reason = f'Parent Epic: {epic}'
            else:
                reason = f'Parent has no epic'
            si = simple_issue.from_src( src=task, jcon=current_user.jira )
            si.notes = reason
            issues.append( si )

    # render output
    args = get_args()
    headers = ( 'key', 'summary', 'epic', 'links', 'notes' )
    if args.output_format == 'text':
        libcmdline.text_table( headers, issues )
    else:
        return { 'headers': headers, 'issues': issues }


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
    # logfmt = logging.Formatter( fmtstr )
    # ch = logging.StreamHandler()
    # ch.setFormatter( logfmt )
    # logr.addHandler( ch )

    # # Configure root logger
    # root = logging.getLogger()
    # root.setLevel( loglvl )
    # rh = logging.StreamHandler()
    # rh.setFormatter( logging.Formatter( fmtstr ) )
    # root.addHandler( rh )

    no_debug = [
        'urllib3',
    ]
    for key in no_debug:
        logging.getLogger(key).setLevel(logging.CRITICAL)

    run()
