#!/usr/local/bin/python3

import jiralib as jl
import argparse
import collections
import jira
import logging
import pprint
import time

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}

# Create a new type for Linked_Issue
Linked_Issue = collections.namedtuple(
    'Linked_Issue',
    ['remote_issue','link_type','direction'] )

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
        parser.add_argument( '--dump', action='store_true',
            help='Dump raw json returned from Jira API .' )
        parser.add_argument( 'issues', nargs='+' )
        resources[key] = parser.parse_args()
    return resources[key]


def get_epic_name( issue ) :
    return issue.fields.customfield_10536


def print_issue_summary( issue ):
    # TODO - allow showing only specific fields
    print( f"{issue}" )
    print( f"\tSummary: {issue.fields.summary}" )
    # TODO - Add Epic if it exists
    links = jl.get_linked_issues( issue )
    for link in links:
        if link.direction == 'inward':
            link_text = link.link_type.inward
        else:
            link_text = link.link_type.outward
        print( f"\tLink: {link_text} {link.remote_issue.key}" )


def print_issue_dump( issue ):
    pprint.pprint( issue.raw )


def run():
    args = get_args()

    # determine action to take
    action = print_issue_summary
    if args.dump:
        action = print_issue_dump

    # get issues from jira
    csv = ",".join( args.issues )
    jql = f'key in ({csv})'
    issues = jl.get_jira().search_issues( jql, maxResults=9999 )
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
    logfmt = logging.Formatter( '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s' )
    ch = logging.StreamHandler()
    ch.setFormatter( logfmt )
    logr.addHandler( ch )

    # start processing
    run()
