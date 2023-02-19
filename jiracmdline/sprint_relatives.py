#!/usr/local/bin/python3

import argparse
import libcmdline
import logging
import os
import libweb
from simple_issue import simple_issue


# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def reset():
    global resources
    resources = {}


def get_args( params=None ):
    global resources
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
        # raw output requested by web form
        parser.add_argument( '-o', '--output_format',
            choices=['text', 'raw' ],
            default='text',
            help=argparse.SUPPRESS )
        # jira session id (from web form)
        parser.add_argument( '--jira_session_id', help=argparse.SUPPRESS )
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
                    ' Set JIRA_PROJECT env var or specify via cmdline option.'
                )
                # logr.exception( msg )
                raise UserWarning( msg )
    return resources[key]


def get_issues_in_sprint( current_user, sprint_name=None ):
    jql = f'sprint in openSprints() and project = {get_project()}'
    if sprint_name:
        raise UserWarning( 'TODO' )
    return current_user.run_jql( jql )



def stories_of_sprint( current_user, issues ):
    stories = []
    for i in issues:
        i_type = i.fields.issuetype.name
        if i_type == "Story":
            stories.append(i)
        elif i_type == "Task":
            parent = current_user.get_linked_parent(i) # returns None if not linked
            if parent:
                stories.append(parent)
        else:
            msg = (
                f"Unsupported issue type '{i_type}' for issue {i}."
                "Expected one of 'Story', 'Task'."
            )
            raise UserWarning( msg )
    return set( stories ) # use a set to remove duplicates


def run( current_user=None, **kwargs ):
    if not current_user:
        raise UserWarning( "needs updates yet for cmdline" )
    else:
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        print( f"KWARGS: '{parts}" )
    args = get_args( params=parts )
    print( f"ARGS: '{args}" )

    logr.debug( 'get sprint issues...' )
    sprint_issues = get_issues_in_sprint( current_user )

    # for any tasks in the sprint, get their parent story
    logr.debug( 'get stories in sprint...' )
    stories = stories_of_sprint( current_user, sprint_issues )

    # get children for each story
    logr.debug( 'get sprint relatives...' )
    sprint_relatives = {}
    for s in stories:
        children = current_user.get_linked_children( s )
        sprint_relatives[ s ] = children

    # post process relatives
    logr.debug( 'post process relatives...' )
    issues = []
    for story, children in sprint_relatives.items():
        issues.append( simple_issue.from_src( src=story, jcon=current_user.jira ) )
        if story in sprint_issues:
            sprint_issues.remove( story )
        for child in children:
            issues.append( simple_issue.from_src( src=child, jcon=current_user.jira ) )
            if child in sprint_issues:
                sprint_issues.remove( child )

    headers = ('story', 'child', 'due', 'in_sprint', 'summary')
    if args.output_format == 'text':
        libcmdline.text_table( headers, issues )
    else:
        return { 'headers': headers, 'issues': issues }


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
