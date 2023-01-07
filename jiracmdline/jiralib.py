import csv
import os
import collections
import jira
import logging
import pprint
import netrc
import dataclasses

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}

# Create a new type for Linked_Issue
Linked_Issue = collections.namedtuple(
    'Linked_Issue',
    ['remote_issue','link_type','direction'] )


# Custom Sprint class
@dataclasses.dataclass
class Sprint:
    ''' Python representation of a Sprint '''
    id: str
    rapidViewId: int
    state: str
    name: str
    startDate: str
    endDate: str
    completeDate: str
    activatedDate: str
    sequence: int
    goal: str
    autoStartStop: bool

    def is_active( self ):
        return self.state == 'ACTIVE'

# Convenience data structures for creating instances of Sprint
sprint_fields = { f.name:f for f in dataclasses.fields( Sprint ) }
sprint_field_names = sprint_fields.keys()


def get_jira():
    key = 'jira_connection'
    if key not in resources:
        jira_server = os.getenv( 'JIRA_SERVER' )
        # attempt to get user,pass from netrc file
        nrc = netrc.netrc()
        login, account, pwd = nrc.authenticators( jira_server )
        # logr.debug( f'USR:{login} PWD:{pwd}' )
        params = {
            'server': f'https://{jira_server}',
            'basic_auth': ( login, pwd ),
        }
        # logr.debug( pprint.pformat( [ 'LOGIN', params ] ) )
        resources[key] = jira.JIRA( **params )
    return resources[key]


def get_issue_by_key( key ):
    ''' key: String
    '''
    return get_jira().issue( key )


def get_issues_by_keys( keys ):
    ''' keys: List of Strings
    '''
    csv = ",".join( keys )
    return get_jira().search_issues( f'key in ({csv})', maxResults=9999 )


def reload_issue( issue ):
    return get_issue_by_key( issue.key )


def get_issue_type( issue ):
    return issue.fields.issuetype.name


def get_labels( issue ):
    return issue.fields.labels


def get_epic_name( issue ) :
    try:
        epic = issue.fields.customfield_10536
    except AttributeError:
        epic = None
    return epic


def get_parent( issue ):
    try:
        parent_key = issue.fields.parent
    except AttributeError:
        parent = None
    else:
        parent = get_issue_by_key( parent_key )
    return parent


def get_linked_parent( issue ):
    jql = f'issue in linkedIssues( {issue.key}, "is a child of" )'
    issues = get_jira().search_issues( jql, maxResults=9999 )
    qty = len( issues )
    if qty > 1:
        raise UserWarning( f"Found more than one parent for '{issue.key}'" )
    elif qty < 1:
        parent = None
    else:
        parent = issues[0]
    return parent


def get_linked_children( parent ):
    jql = f'issue in linkedIssues( {parent.key}, "is the parent of" )'
    return get_jira().search_issues( jql, maxResults=9999 )


def get_project_key( issue ):
    return issue.key.split('-')[0]


def get_issues_in_epic( issue, include_completed_issues=False ):
    jql = f'"Epic Link" = {issue.key}'
    if include_completed_issues:
        jql = f'{jql} and resolved is empty'
    return get_jira().search_issues( jql, maxResults=9999 )


def get_stories_in_epic( issue ):
    children = get_issues_in_epic( issue )
    return [ i for i in children if i.fields.issuetype.name == 'Story' ]


def get_linked_issues( issue ):
    linked_issues = []
    for link in issue.fields.issuelinks:
        try:
            remote_issue = link.inwardIssue
            direction = 'inward'
        except AttributeError:
            remote_issue = link.outwardIssue
            direction = 'outward'
        linked_issues.append(
            Linked_Issue(
                remote_issue=remote_issue,
                link_type=link.type,
                direction=direction
                )
            )
    return linked_issues


def print_issue_summary( issue, parts=None ):
    # force reload of issue
    i = get_jira().issue( issue.key )
    print( f"{i}" )
    print( f"\tSummary: {i.fields.summary}" )
    print( f"\tEpic: {get_epic_name( i )}" )
    # print( f"\tDescription: {i.fields.description}" )
    links = get_linked_issues( i )
    for link in links:
        if link.direction == 'inward':
            link_text = link.link_type.inward
        else:
            link_text = link.link_type.outward
        print( f"\tLink: {link_text} {link.remote_issue.key}" )


def link_to_parent( child, parent, dryrun=False ):
    logr.info( f'Create link: Parent={parent} -> Child={child}' )
    if dryrun:
        return #stop here on dryrun
    j = get_jira()
    j.create_issue_link(
        type='Ancestor',
        inwardIssue=parent.key,
        outwardIssue=child.key
        )


def add_tasks_to_epic( issue_list, epic_key ):
    params = {
        'epic_id': epic_key,
        'issue_keys': [ i.key for i in issue_list ],
        }
    result = get_jira().add_issues_to_epic( **params )
    logr.debug( f"Add to epic results: '{pprint.pformat( result ) }'" )
    result.raise_for_status() # https://requests.readthedocs.io/en/latest/api/#requests.Response


def mk_child_tasks( parent, child_summaries, dryrun=False ):
    ''' parent: parent Story ticket
        child_summaries: list of strings, each is the summary for a new ticket
    '''
    defaults = {
        'project': { 'key': get_project_key( parent ) },
        'issuetype': { 'name': 'Task' },
    }
    issue_list = []
    for summary in child_summaries:
        custom_parts = { 'summary': summary[0:254] }
        issue_list.append( defaults | custom_parts )
    logr.debug( f'About to create {pprint.pformat( issue_list )}' )
    child_issues = []
    if not dryrun:
        new_tasks = get_jira().create_issues( field_list=issue_list )
        for result in new_tasks:
            if result['status'] == 'Success':
                child = result['issue']
                logr.info( f"Created issue: {child}" )
                link_to_parent( child=child, parent=parent )
                child_issues.append( child )
            else:
                logr.warn( f"Error creating child ticket: '{pprint.pformat( result )}'" )
    return child_issues


def get_sprint_memberships( issue ):
    pprint.pprint( issue )
    memberships = issue.fields.customfield_10535
    pprint.pprint( memberships )
    # try:
    #     memberships = issue.fields.customfield_10535
    # except AttributeError:
    #     i = reload_issue( issue )
    #     memberships = i.fields.customfield_10535
    sprints = []
    if memberships:
        for line in memberships:
                sprints.append( _str_to_sprint( line ) )
    return sprints


def _str_to_sprint( line ):
    ''' Parse a line from customfield_10535
        return an instance of a Sprint
    '''
    if not line.startswith( 'com.atlassian.greenhopper.service.sprint.Sprint' ):
        raise UserWarning( f"line doesn't look like a sprint: '{line}'" )
    csv_start = line.index( '[' ) + 1
    raw_csv = line[csv_start:-1]
    # return csv
    reader = csv.reader( [raw_csv] )
    # for row in reader:
    row = next(reader)
    sprint_data = {}
    for elem in row:
        (k,v) = elem.split( '=', maxsplit=1 )
        if k in sprint_field_names:
            sprint_data[k] = sprint_fields[k].type( v )
    return Sprint( **sprint_data )


if __name__ == '__main__':
    raise SystemExit( 'not a cmdline module' )
