#!/usr/local/bin/python3

import argparse
import dataclasses
import datetime
import jiralib as jl
import logging
import os
import pprint
from tabulate import tabulate, SEPARATING_LINE


# Module level resources
logr = logging.getLogger( __name__ )
resources = {}

@dataclasses.dataclass
class issue:
    ''' Basic parts of a jira issue for display purposes '''
    story: str = ''
    child: str = ''
    due: str = None
    in_sprint: str = ''
    summary: str = ''
    issue_type: str = ''
    url: str = None

    def __post_init__( self ):
        if not self.due:
            self.due = ' NO DUE '.center(12, '-')

    @classmethod
    def from_src( cls, src ):
        print(f'got src:{src}')
        params = {}
        # if type is not 'story', then assume it's a 'child'
        # use-case: SECURITY-1553 "is a child of" SVCPLAN-1911, even though type=security-vetting
        issue_type = jl.get_issue_type(src).lower()
        if issue_type != 'story':
            issue_type = 'child'
        params['issue_type'] = issue_type
        params[issue_type] = src.key
        params['due'] = src.fields.duedate
        params['in_sprint'] = get_active_sprint_name( src )
        params['summary'] = src.fields.summary[0:50]
        params['url'] = f'{jl.get_jira().server_url}/browse/{src.key}'
        return cls( **params )


def get_args( is_cmdline=False ):
    key = 'args'
    if key not in resources:
        params = ['--output_format=raw'] # not a cmdline invocation
        if is_cmdline:
            params = None # parse_args() will process sys.stdin
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Get all relatives of issues in the current Sprint.',
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
        parser.add_argument( '-s', '--sprint',
            help="Sprint name to use (instead of looking for current sprint)" )
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
                    ' Set JIRA_PROJECT or specify via cmdline option.'
                )
                logr.exception( msg )
    return resources[key]


def get_issues_in_sprint( sprint_name=None ):
    jql = f'sprint in openSprints() and project = {get_project()}'
    if sprint_name:
        raise UserWarning( 'TODO' )
    j = jl.get_jira()
    return j.search_issues( jql, maxResults=9999 )


def stories_of_sprint( issues ):
    stories = []
    for i in issues:
        i_type = i.fields.issuetype.name
        if i_type == "Story":
            stories.append(i)
        elif i_type == "Task":
            parent = jl.get_linked_parent(i) # returns None if not linked
            if parent:
                stories.append(parent)
        else:
            msg = (
                f"Unsupported issue type '{i_type}' for issue {i}."
                "Expected one of 'Story', 'Task'."
            )
            raise UserWarning( msg )
    return set( stories ) # use a set to remove duplicates


def get_active_sprint_name( issue ):
    sprints = jl.get_sprint_memberships( issue )
    names = [ None ]
    for s in sprints:
        if s.is_active():
            names.append( f"{s.name}" )
    return names[-1]


def run():
    logr.debug( 'get sprint issues...' )
    sprint_issues = get_issues_in_sprint()

    # for any tasks in the sprint, get their parent story
    logr.debug( 'get stories in sprint...' )
    stories = stories_of_sprint( sprint_issues )

    # get children for each story
    logr.debug( 'get sprint relatives...' )
    sprint_relatives = {}
    for s in stories:
        children = jl.get_linked_children( s )
        sprint_relatives[ s ] = children

    # post process relatives
    logr.debug( 'post process relatives...' )
    data = []
    for story, children in sprint_relatives.items():
        data.append( issue.from_src( src=story ) )
        if story in sprint_issues:
            sprint_issues.remove( story )
        for child in children:
            data.append( issue.from_src( src=child ) )
            if child in sprint_issues:
                sprint_issues.remove( child )

    headers = ('story', 'child', 'due', 'in_sprint', 'summary')
    args = get_args()
    if args.output_format == 'text':
        print( tabulate( data, headers ) )
    else:
        info = {
            'jira_server': jl.get_jira().server_url,
        }
        return { 'info': info, 'headers': headers, 'data': data }


if __name__ == '__main__':
    args = get_args( is_cmdline=True )

    # Configure logging
    loglvl = logging.WARNING
    if args.verbose:
        loglvl = logging.INFO
    if args.debug:
        loglvl = logging.DEBUG
    fmtstr = '%(levelname)s:%(pathname)s.%(module)s.%(funcName)s[%(lineno)d] %(message)s'
    logging.basicConfig( level=loglvl, format=fmtstr )
    # logfmt = logging.Formatter( fmtstr )
    # ch = logging.StreamHandler()
    # ch.setFormatter( logfmt )
    # logr.addHandler( ch )

    # # Configure root logger
    # root = logging.getLogger()
    # root.setLevel( loglvl )
    # rh = logging.StreamHandler()
    # rh.setFormatter( logging.Formatter( fmtstr ) )
    # root.addHandler( rh )

    no_debug = [
        'urllib3',
    ]
    for key in no_debug:
        logging.getLogger(key).setLevel(logging.CRITICAL)

    run()
