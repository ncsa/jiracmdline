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
        parser.add_argument( '-P', '--parents', action='store_true',
            help='Specified issues are parents. Find and Operate on their subtasks.' )
        parser.add_argument( 'issues', nargs='+' )
        resources[key] = parser.parse_args()
    return resources[key]


def print_epilogue( jql ):
    safe_jql = urllib.parse.quote( jql )
    server = jl.get_jira().server_url
    full_url = f'{server}/issues/?jql={safe_jql}'
    print( (
        '\n'
        'From the link below, '
        'use the Bulk Change tool to "Move" issues from "Sub-Task" -> "Task"\n'
        f'{full_url}'
        '\n'
        ) )


def run():
    args = get_args()

    # get subtasks from jira
    csv = ",".join( args.issues )
    keyword = 'key'
    if args.parents:
        keyword = 'parent'
    jql = f'{keyword} in ({csv})'
    logr.debug( f"JQL: '{jql}'" )
    issues = jl.get_jira().search_issues( jql, maxResults=9999 )
    for i in issues:
        p = jl.get_parent( i )
        jl.link_to_parent( child=i, parent=p, dryrun=args.dryrun )
    for i in issues:
        jl.print_issue_summary( i )
    print_epilogue( jql )


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
