#!/usr/local/bin/python3

import argparse
import jiralib as jl
import logging
import pprint


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
        parser.add_argument( '--dump', action='store_true',
            help='Dump raw json returned from Jira API .' )
        parser.add_argument( 'issues', nargs='+' )
        resources[key] = parser.parse_args()
    return resources[key]


def print_issue_dump( issue ):
    pprint.pprint( issue.raw )


def run():
    args = get_args()

    # determine action to take
    action = jl.print_issue_summary
    if args.dump:
        action = print_issue_dump

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
    logfmt = logging.Formatter( '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s' )
    ch = logging.StreamHandler()
    ch.setFormatter( logfmt )
    logr.addHandler( ch )

    # start processing
    run()
