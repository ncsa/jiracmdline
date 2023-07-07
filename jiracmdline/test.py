import collections
import libjira
import json
import logging
import pprint

logfmt = '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s'
loglvl = logging.INFO
loglvl = logging.DEBUG
logging.basicConfig( level=loglvl, format=logfmt )
logging.getLogger( 'libjira' ).setLevel( loglvl )

Linked_Issue = collections.namedtuple(
    'Linked_Issue',
    ['remote_issue','link_type','direction'] )

resources = {} #module level resources

def get_jira():
    JIRA_SERVER = 'jira.ncsa.illinois.edu'
    key = 'jira_connection'
    try:
        j = resources[key]
    except KeyError:
        j = libjira.jira_login()
    return j


def get_all_projects():
    j = get_jira()
    key = 'all_projects'
    if key not in resources:
        resources[key] = { x.key:x for x in j.projects() }
    return resources[key]


def print_all_projects():
    by_name = get_all_projects()
    for key in sorted(by_name.keys()):
        name = by_name[key].name
        id = by_name[key].id
        print( f'{key} : {name} ({id})' )


def get_all_fields():
    j = get_jira()
    key = 'all_fields'
    if key not in resources:
        resources[key] = { x['id']:x for x in j.fields() }
    return resources[key]


def print_all_fields():
    by_name = { v['name']:k for k,v in get_all_fields().items() }
    for name in sorted(by_name.keys()):
        id = by_name[name]
        print( f'{name} : {id}' )


def get_issue_link_types():
    j = get_jira()
    key = 'issue_link_types'
    if key not in resources:
        resources[key] = { x.id:x for x in j.issue_link_types() }
    return resources[key]


def print_issue_link_types():
    r = get_issue_link_types()
    by_name = { v.name:k for k,v in get_issue_link_types().items() }
    for name in sorted(by_name.keys()):
        id = by_name[name]
        print( f'{name} : {id}' )


def get_labels( issue ):
    # return get_jira().issue( id ).fields.labels
    return issue.fields.labels


def dump_issue( issue ):
    pprint.pprint( issue.raw )


def get_linked_issues( issue ):
    linked_issues = []
    for link in issue.fields.issuelinks:
        # l_type = link['type']
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


def get_parent( issue ):
    #issue = get_jira().issue( id )
    try:
        parent = issue.fields.parent
    except AttributeError:
        parent = None
    return parent


def get_all_subtasks():
    jql = 'project = "Service Planning" and issuetype = Sub-task and resolution is EMPTY'
    return get_jira().search_issues( jql, maxResults=9999 )


def add_label( issue, new_label ):
    issue.fields.labels.append( new_label )
    issue.update( fields={"labels":issue.fields.labels}, notify=False )


def add_childof_label( issue ):
    p = get_parent( issue )
    parent_label = f'childof{p}'
    add_label( issue, parent_label )


def link_to_parent( issue, parent=None ):
    if parent is None:
        parent = get_parent( issue )
    if parent is None:
        logging.warn( f"No parent for issue '{issue.key}'" )
    logging.info( f'Parent={parent} Child={issue}' )
    j = get_jira()
    j.create_issue_link(
        type='Ancestor',
        inwardIssue=parent.key,
        outwardIssue=issue.key
        )


def print_issue_summary( issue ):
    print( f"{issue}" )
    parent = get_parent( issue )
    print( f"\tParent {parent}" )
    labels = get_labels( issue )
    print( f"\tLabels {labels}" )
    links = get_linked_issues( issue )
    for link in links:
        if link.direction == 'inward':
            link_text = link.link_type.inward
        else:
            link_text = link.link_type.outward
        print( f"\t{link_text} {link.remote_issue.key}" )


if __name__ == '__main__':

    # print( ">>>FIELDS" )
    # print_all_fields()
    # print( ">>>ISSUE LINK TYPES" )
    # print_issue_link_types()
    # print( ">>>PROJECTS" )
    # print_all_projects()

    print( json.dumps( get_jira().issue('SVCPLAN-398').raw ) )

    # # elems = [ f'SVCPLAN-{x}' for x in range( 289, 295 ) ]
    # elems = [ f'SVCPLAN-{x}' for x in range( 289, 292 ) ]
    # jql = f'id in ({",".join(elems)})'
    # issues = get_jira().search_issues( jql, maxResults=9999 )

    # # issues = get_all_subtasks()

    # for i in issues:
    # #     add_childof_label( i )
    #     # link_to_parent( i )
    #     print_issue_summary( i )
