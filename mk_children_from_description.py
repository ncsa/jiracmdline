#!/usr/local/bin/python3

import argparse
import collections
import logging
import pprint
import jiralib as jl

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def get_args():
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Create child tasks from the description, one per line',
            'epilog': 'NETRC:'
                '    Jira login credentials should be stored in ~/.netrc.'
                '    Machine name should be hostname only.'
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-n', '--dryrun', action='store_true',
            help='Show what would be done but make no changes.' )
        parser.add_argument( 'issues', nargs='+' )
        resources[key] = parser.parse_args()
    return resources[key]


def split_issue_description( issue ):
    # split lines into array, remove leading list chars, white space
    lines = [ x.strip('*# ').strip() for x in issue.fields.description.splitlines() ]
    # filter out blank lines
    filtered_lines = filter( len, lines )
    return filtered_lines


def mk_children_from_description( issue ):
    args = get_args()
    j = jl.get_jira()
    summaries = split_issue_description( issue )
    defaults = {
        'project': { 'key': jl.get_project_key( issue ) },
        'issuetype': { 'name': 'Task' },
        }
    issue_list = []
    for summary in summaries:
        # max summary size is 254
        custom_parts = { 'summary': summary[0:254] }
        issue_list.append( defaults | custom_parts )
    #DEBUGGING --- DO ONLY ONE TASK --- REMOVE FOR PRODUCTION
    # issue_list = issue_list[0:1]
    logr.debug( f'About to create {pprint.pformat( issue_list )}' )
    child_issues = []
    if not args.dryrun:
        new_tasks = j.create_issues( field_list=issue_list )

        # logr.debug( f'New tasks: {pprint.pformat( new_tasks )}' )
        # check success
        for result in new_tasks:
            # Result: {
            #     'error': None,
            #     'input_fields': {'issuetype': {'name': 'Task'},
            #                      'project': {'key': 'SVCPLAN'},
            #                      'summary': 'One Use cases and documentation of such'},
            #     'issue': <JIRA Issue: key='SVCPLAN-2498', id='294950'>,
            #     'status': 'Success' }
            if result['status'] == 'Success':
                child = result['issue']
                logr.info( f"Created issue: {child}" )
                jl.link_to_parent( child=child, parent=issue )
                child_issues.append( child )
            else:
                logr.warn( f"Error creating child ticket: '{pprint.pformat( result )}'" )
    return child_issues


def run():
    args = get_args()

    # get issues from jira
    csv = ",".join( args.issues )
    jql = f'key in ({csv})'
    issues = jl.get_jira().search_issues( jql, maxResults=9999 )
    for i in issues:
        logr.debug( f'got issue {i}' )
        child_issues = mk_children_from_description( i )
        epic_key = jl.get_epic_name( i )
        if not args.dryrun:
            jl.add_tasks_to_epic( child_issues, epic_key )
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
