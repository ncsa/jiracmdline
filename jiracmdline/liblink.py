import collections
import logging


# Custom type for Linked_Issue
Linked_Issue = collections.namedtuple(
    'Linked_Issue',
    ['remote_issue','link_type','direction'] )


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


def get_linked_parent( issue ):
    logging.debug( f'{issue}' )
    parents = []
    for link in get_linked_issues( issue ):
        if link.link_type.name == "Ancestor":
            if link.direction == 'inward':
                parents.append( link.remote_issue )
    if len( parents ) < 1:
        raise UserWarning( f'{issue} has no parent' )
    elif len( parents ) > 1:
        raise UserWarning( f'{issue} has multiple parents' )
    return parents[-1]



def check_for_link_problems( issue ):
    logging.debug( f'{issue}' )
    parents = []
    children = []
    for link in get_linked_issues( issue ):
        logging.debug( f"found link '{link.link_type}' with name '{link.link_type.name}'" )
        if link.link_type.name == "Ancestor":
            if link.direction == 'outward':
                children.append( link.remote_issue )
            else:
                parents.append( link.remote_issue )
    issue_type = issue.fields.issuetype.name.lower()
    if issue_type == 'story' and len( parents ) > 0:
        raise UserWarning( 'Story has parent(s)' )
    elif issue_type == 'task':
        if len( children ) > 0:
            raise UserWarning( 'Task has children' )
        elif len( parents ) < 1:
            raise UserWarning( 'Task has no parent' )
        elif len( parents ) > 1:
            raise UserWarning( 'Task has multiple parents' )
    return False


if __name__ == '__main__':
    raise SystemExit( 'not a cmdline module' )
