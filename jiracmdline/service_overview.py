#!/usr/local/bin/python3

import argparse
import jira_connection
import libcmdline
import libjira
import libutil
import libweb
import logging
import os
import urllib.parse
from simple_issue import simple_issue

import pprint

# Module level resources
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
            'description': 'Get all Epics (and all subordinates thereof) associated with a Service.',
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
        parser.add_argument( '-s', '--service_name',
            help="Service Name (epic name with prefix removed)" )
        parser.add_argument( '-p', '--project',
            help="Jira project" )
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
                # logging.exception( msg )
                raise UserWarning( msg )
    return resources[key]


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
        logging.debug( f"KWARGS: '{parts}" )
    args = get_args( params=parts )
    logging.debug( f"ARGS: '{args}" )

    logging.debug( f"get epics for Service: '{args.service_name}'" )
    jql = (
        f'project={get_project()}'
        f' and type=epic and resolved is empty'
        f' and text ~ "{args.service_name}"'
        )
    epic_list = current_user.run_jql( jql )
    epics = {}
    for epic in epic_list:
        epics[ epic.key ] = {
            'epic': simple_issue.from_src( epic, current_user )
            }

        logging.debug( f'get stories for epic {epic.key}' )
        subordinates = []
        for story in current_user.get_stories_in_epic( epic ):
            subordinates.append( simple_issue.from_src( story, current_user ) )

            logging.debug( f'get children of story {story.key}' )
            children_raw = current_user.get_linked_children( story )
            children_simple = [ simple_issue.from_src(c, current_user) for c in children_raw ]
            subordinates.extend( sorted( children_simple ) )
        epics[ epic.key ]['subordinates'] = subordinates

    data = {
        'service_name': args.service_name,
        'epics': epics,
        'headers': ( 'story', 'child', 'summary', 'due', ),
        }

    if args.output_format == 'text':
        pprint.pprint( data )
    else:
        return data


if __name__ == '__main__':
    args = get_args()
    libutil.setup_logging( args )

    no_debug = [
        'urllib3',
    ]
    for key in no_debug:
        logging.getLogger(key).setLevel(logging.CRITICAL)

    run()
