#!/usr/local/bin/python3

import argparse
import jira_connection
import libcmdline
import libjira
import libweb
import logging
import os
import urllib.parse
from simple_issue import simple_issue

import pprint

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def reset():
    global resources
    resources = {}


def get_args( params=None ):
    global resources
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'List services (Epics) in a Jira project.',
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
            help="Jira project from which to get current Sprint" )
        # raw output requested by web form
        parser.add_argument( '-o', '--output_format',
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
                    ' Set JIRA_PROJECT env var or specify via cmdline option.'
                )
                # logr.exception( msg )
                raise UserWarning( msg )
    return resources[key]


def mk_link( service_name ):
    query = urllib.parse.urlencode( {
        'service_name': service_name,
        'project': get_project(),
        } )
    return f'/service_overview?{query}'


def run( current_user=None, **kwargs ):
    parts = None
    if not current_user:
        # started from cmdline
        current_user = jira_connection.Jira_Connection( libjira.jira_login() )
    else:
        # running from web
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        print( f"KWARGS: '{parts}" )
    args = get_args( params=parts )
    print( f"ARGS: '{args}" )

    logr.debug( 'get epics...' )
    # Strip prefix from epic name to create a list of unique service names
    raw_names = []
    jql = f'project={get_project()} and type=epic and resolved is empty'
    epics = current_user.run_jql( jql )
    for epic in epics:
        e_name = current_user.get_epic_name( epic )
        parts = e_name.split( '-', maxsplit=1 )
        raw_names.append( parts[-1].strip() )
    service_names = sorted( set( raw_names ) )

    # Create HTML anchor targets for each service
    service_links = { s: mk_link( s ) for s in service_names }

    if args.output_format == 'text':
        print( '\n'.join( [ f"'{k}' {v}" for k,v in service_links.items() ] ) )
    else:
        return {
            'service_links': service_links,
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
