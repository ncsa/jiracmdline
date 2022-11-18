#!/usr/local/bin/python3

import argparse
import logging
import pprint
import urllib
import jiralib as jl

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def get_args():
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Create "child of" link from sub-tasks of parent',
            'epilog': '''
NETRC:
    Jira login credentials should be stored in ~/.netrc.
    Machine name should be hostname only.
            '''
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-n', '--dryrun', action='store_true',
            help='Show what would be done but make no changes.' )
        parser.add_argument( '-P', '--parent', required=True,
            help='The ticket to link as "Parent".' )
        parser.add_argument( 'issues', nargs='+' )
        args = parser.parse_args()
        resources[key] = args
    return resources[key]


def run():
    args = get_args()

    # link tasks to parent
    parent = jl.get_issue_by_key( args.parent )
    issues = jl.get_issues_by_keys( args.issues )
    for i in issues:
        jl.link_to_parent( i, parent, args.dryrun )

    # add tasks to parent's epic
    epic = jl.get_epic_name( parent )
    if epic:
        jl.add_tasks_to_epic( issues, epic )

    # new summary of parent
    jl.print_issue_summary( parent )


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
