import collections


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


if __name__ == '__main__':
    raise SystemExit( 'not a cmdline module' )
