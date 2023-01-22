#!/usr/local/bin/python3

import argparse
import jiralib as jl
import logging
import pprint
import re
import urllib

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def get_args( is_cmdline=False, custom_params=[] ):
    key = 'args'
    if key not in resources:
        if is_cmdline:
            params = None # parse_args() will process sys.stdin
        else:
            # not a cmdline invocation
            params = [ '--output_format=raw' ]
            params.extend( custom_params )
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Create "child of" link from sub-tasks of parent',
            'epilog': (
                'Environment Variables:\n'
                'NETRC:\n'
                '   Jira login credentials should be stored in ~/.netrc.\n'
                '   Machine name should be hostname only.\n'
            )
        }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( '-n', '--dryrun', action='store_true',
            help='Show what would be done but make no changes.' )
        # convenience for cmdline
        parser.add_argument( '-P', '--parents', dest='ticket_type',
            action='store_const', const='parent',
            help='Specified issues are parents. Find and Operate on their subtasks.' )
        parser.add_argument( 'issues', nargs='*' )
        # allowance for issues list via web
        parser.add_argument( '--ticket_ids', help=argparse.SUPPRESS )
        # allowance for ticket_type via web
        parser.add_argument( '-t', '--ticket_type',
            choices=['subtask','parent'],
            help=argparse.SUPPRESS )
        # allowance for output type via web
        parser.add_argument( '-o', '--output_format',
            choices=['text', 'raw' ],
            help=argparse.SUPPRESS )
        parser.set_defaults(
            output_format='text',
            ticket_type='subtask',
        )
        args = parser.parse_args( params )
        if args.ticket_ids:
            args.issues.extend( args.ticket_ids.split() )
        resources[key] = args
    return resources[key]


def jql2url( jql ):
    # safe_jql = urllib.parse.quote( jql )
    server = jl.get_jira().server_url
    # return f'{server}/issues/?jql={safe_jql}'
    return f'{server}/issues/?jql={jql}'


def mk_instructions():
    args = get_args()
    header = 'Step 2 - convert Sub-tasks to Tasks in your browser'
    if args.output_format == 'text':
        step1 = 'Copy the URL below into a browser, then'
        step2 = 'use the Bulk Change tool to "Move" issues from "Sub-Task" -> "Task"'
    else:
        step1 = 'Follow the link below, then'
        step2 = 'use the Bulk Change tool to "Move" issues from "Sub-Task" &rarr; "Task"'
    instructions = [
        header,
        step1,
        step2,
    ]
    return instructions


def sanitize_key( key ):
    return re.sub( '[^a-zA-Z0-9_-]', '', key )


def sanitize_val( val ):
    temp = re.sub( ',', ' ', val )
    return re.sub( '[^ a-zA-Z0-9_-]', '', temp )


def run( **kwargs ):
    parts = []
    for k,v in kwargs.items():
        key = sanitize_key( k )
        val = sanitize_val( v )
        parts.extend( [ f'--{key}', val ] )
    args = get_args( custom_params=parts )
    logr.debug( f"ARGS: '{args}" )
    print( f"ARGS: '{args}" )

    # get subtasks from jira
    csv = ",".join( args.issues )
    keyword = 'key'
    if args.ticket_type == 'parent':
        keyword = 'parent'
    jql = f'{keyword} in ({csv})'
    logr.debug( f"JQL: '{jql}'" )
    issues = jl.get_jira().search_issues( jql, maxResults=9999 )
    logr.debug( f"ISSUES: '{issues}'" )
    for i in issues:
        p = jl.get_parent( i )
        jl.link_to_parent( child=i, parent=p, dryrun=args.dryrun )

    # show results and instructions
    jql_url = jql2url( jql )
    logr.debug( f"JQL: '{jql_url}'" )
    instructions = mk_instructions()
    logr.debug( f"INSTRUCTIONS: '{instructions}'" )
    if args.output_format == 'text':
        for i in issues:
            jl.print_issue_summary( i )
        print( '\n' )
        print( '\n'.join( instructions ) )
        print( '\n' )
        print( jql_url )
        print( '\n' )
    else:
        reloaded_issues = jl.reload_issues( issues )
        links = {}
        epics = {}
        for i in reloaded_issues:
            links[ i.key ] = []
            for link in jl.get_linked_issues( i ):
                if link.direction == 'inward':
                    link_text = link.link_type.inward
                else:
                    link_text = link.link_type.outward
                links[ i.key ].append( f'{link_text} {link.remote_issue.key}' )
            epics[ i.key ] = jl.get_epic_name( i )
        data = {
            'url': jql_url,
            'instructions': instructions,
            'issues': reloaded_issues,
            'links': links,
            'epics': epics,
        }
        logr.debug( f"DATA: {data}" )
        pprint.pprint( data )
        return data


if __name__ == '__main__':
    args = get_args( is_cmdline=True )

    # configure logging
    loglvl = logging.WARNING
    if args.verbose or args.dryrun:
        loglvl = logging.INFO
    if args.debug:
        loglvl = logging.DEBUG
    fmtstr = '%(levelname)s:%(pathname)s.%(module)s.%(funcName)s[%(lineno)d] %(message)s'
    logging.basicConfig( level=loglvl, format=fmtstr )
    # logr.setLevel( loglvl )
    # logfmt = logging.Formatter( '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s' )
    # ch = logging.StreamHandler()
    # ch.setFormatter( logfmt )
    # logr.addHandler( ch )

    # start processing
    run()
