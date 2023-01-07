#!/usr/local/bin/python3

import argparse
import jiralib as jl
import logging
import pprint
import asciitree
import json


# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def get_args():
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Show summary of tasks.',
            'epilog': 'NETRC:'
                '    Jira login credentials should be stored in ~/.netrc.'
                '    Machine name should be hostname only.'
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-r', '--recurse', action='store_true',
            help='Recursively show all children too.' )
        parser.add_argument( '--dump', action='store_true',
            help='Dump raw json returned from Jira API .' )
        parser.add_argument( 'issues', nargs='+' )
        resources[key] = parser.parse_args()
    return resources[key]


def get_jira_server_url():
    key = 'jira_server_url'
    if key not in resources:
        resources[key] = jl.get_jira().server_url
    return resources[key]


def print_issue_dump( issue ):
    print( json.dumps( issue.raw ) )
    # pprint.pprint( issue.raw )


def print_issue_hierarchy( issue ):
    tr = asciitree.LeftAligned()
    # jira_server_url = get_jira_server_url()
    tree = _get_children( issue )
    # pprint.pprint( tree )
    print( tr( tree ) )


def _get_children( issue ):
    ''' Recursively get all "children" of issue.
        Variable "jira_server_url" is defined once in the module
        to avoid making repetitive calls to the function to retrive it.
    '''
    sep = ' '*5
    issue_key = issue.key.ljust(12)
    short_summary = issue.fields.summary[:30].ljust(30)
    url = f'{jira_server_url}/browse/{issue.key}'
    key = f'{issue_key}{sep}{short_summary}{sep}({url})'
    i_type = jl.get_issue_type( issue )
    if i_type == 'Task':
        # response = issue.fields.summary
        response = {}
    elif i_type == 'Story':
        response = {}
        for c in jl.get_linked_children( issue ):
            response.update( _get_children( c ) )
    elif i_type == 'Epic':
        response = {}
        for c in jl.get_stories_in_epic( issue ):
            response.update( _get_children ( c ) )
    else:
        raise UserWarning( f"Unknown issue type '{i_type}' for issue '{issue}'" )
    return { key : response }


def run():
    args = get_args()

    # determine action to take
    action = jl.print_issue_summary
    if args.dump:
        action = print_issue_dump
    elif args.recurse:
        action = print_issue_hierarchy

    # get issues from jira
    issues = jl.get_issues_by_keys( args.issues )
    for i in issues:
        action( i )

    # TODO - recurse for all child tasks (allow both sub-tasks and linked children)


if __name__ == '__main__':
    args = get_args()

    # configure logging
    loglvl = logging.WARNING
    if args.verbose:
        loglvl = logging.INFO
    if args.debug:
        loglvl = logging.DEBUG
    logr.setLevel( loglvl )
    fmtstr = '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s'
    logging.basicConfig( level=loglvl, format=fmtstr )
    ch = logging.StreamHandler()
    logfmt = logging.Formatter( fmtstr )
    ch.setFormatter( logfmt )
    logr.addHandler( ch )

    # Define this at the module level to avoid repetitive calls
    # by _get_chilren() recursive function
    jira_server_url = get_jira_server_url()

    # start processing
    run()