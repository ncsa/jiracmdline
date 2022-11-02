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
        g1 = parser.add_mutually_exclusive_group()
        g1.add_argument( '-P', '--parents', action='store_true',
            help='Specified issues are parents. Find and Operate on their subtasks.' )
        g1.add_argument( '-p', '--project', 
            help="Find all matching issues in PROJECT. Add to their parent's epic." )
        parser.add_argument( 'issues', nargs='*' )
        args = parser.parse_args()
        resources[key] = args
        # Check for sane input
        # pprint.pprint( args )
        # print( f'ISSUES: {args.issues}' )
        # print( f'project: {args.project}' )
        if args.issues and args.project:
            raise SystemExit( f"Cannot specify both PROJECT and issue list" )
    return resources[key]


def run():
    args = get_args()

    # get task list from jira
    if args.issues:
        # logr.debug( f'args.Issues: {args.issues}' )
        issues = jl.get_issues_by_keys( args.issues )
        # logr.debug( f'Issues: {issues}' )
        if args.parents:
            children = []
            for i in issues:
                children.extend( jl.get_linked_children( i ) )
            issues = children
    elif args.project:
        jql = f'project={args.project} AND issueLinkType in ("is a child of") AND "Epic Link" is EMPTY'
        logr.debug( f"JQL: '{jql}'" )
        issues = jl.get_jira().search_issues( jql, maxResults=9999 )
    else:
        raise SystemExit( "Missing one of --project, --parents, issues list." )
    epics = {}
    for i in issues:
        p = jl.get_linked_parent( i )
        if not p:
            logr.warning( f"Issue '{i}' has no linked parent ... skipping." )
            continue
        parent = jl.reload_issue( p )
        epic_name = jl.get_epic_name( parent )
        if not epic_name:
            logr.warning( f"Parent issue '{parent}' has no epic ... skipping child issue '{i}'." )
            continue
        if epic_name not in epics:
            epics[ epic_name ] = []
        epics[ epic_name ].append( i )
    for e_name, i_list in epics.items():
        logr.info( f"Add to epic {e_name} <-- '{i_list}'")
        if not args.dryrun:
            jl.add_tasks_to_epic( i_list, e_name )
    for i in issues:
        jl.print_issue_summary( i )


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
