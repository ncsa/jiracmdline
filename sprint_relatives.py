#!/usr/local/bin/python3

import argparse
import dataclasses
import datetime
import jiralib as jl
import logging
import os
import pprint
from tabulate import tabulate, SEPARATING_LINE

# tabulate.PRESERVE_WHITESPACE = True


# Module level resources
logr = logging.getLogger( __name__ )
resources = {}

@dataclasses.dataclass
class issue:
    ''' Basic parts of a jira issue for display purposes '''
    story: str = ''
    task: str = ''
    due: str = None
    in_sprint: str = ''

    def __post_init__(self):
        if self.due is None:
            # self.due = '*no due date*'
            self.due = ' NO DUE '.center(12, '-')


def get_args():
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Get all relatives of issues in the current Sprint.',
            'epilog': (
                'Environment Variables:\n'
                '    NETRC:\n'
                '        Jira login credentials should be stored in ~/.netrc.\n'
                '        Machine name should be hostname only.\n'
                '    JIRA_DEFAULT_PROJECT:\n'
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
        resources[key] = parser.parse_args()
    return resources[key]


def get_project():
    key = 'project'
    if key not in resources:
        args = get_args()
        if args.project:
            resources[key] = args.project
        else:
            try:
                resources[key] = os.environ['JIRA_DEFAULT_PROJECT']
            except KeyError:
                msg = (
                    'No jira project specified.'
                    ' Set JIRA_DEFAULT_PROJECT or specify via cmdline option.'
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


def get_active_sprint_names( issue ):
    sprints = jl.get_sprint_memberships( issue )
    names = []
    for s in sprints:
        if s.is_active():
            names.append( f"{s.name}" )
    return names


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
        in_sprint = None
        if story in sprint_issues:
            in_sprint = pprint.pformat( get_active_sprint_names( story ) )
            sprint_issues.remove( story )
        data.append( issue( story=story.key, due=story.fields.duedate, in_sprint=in_sprint ) )
        for c in children:
            in_sprint = None
            if c in sprint_issues:
                in_sprint = pprint.pformat( get_active_sprint_names( c ) )
                sprint_issues.remove( c )
            data.append( issue( task=c.key, due=c.fields.duedate, in_sprint=in_sprint ) )

    # print data table
    headers= ('Story', 'Task', 'Due', 'Active Sprint')
    print( tabulate( data, headers ) )


if __name__ == '__main__':
    args = get_args()

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
