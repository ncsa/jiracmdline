import dataclasses
import liblink
import libsprint


@dataclasses.dataclass
class simple_issue:
    ''' Basic parts of a jira issue for display purposes '''
    key: str = ''
    story: str = ''
    child: str = ''
    due: str = None
    in_sprint: str = ''
    summary: str = ''
    issue_type: str = ''
    url: str = None
    links: list[str] = dataclasses.field( default_factory=list )
    epic: str = None
    notes: str = ''


    def __post_init__( self ):
        if not self.due:
            self.due = '-'
        if not self.epic:
            self.epic = '-'


    @classmethod
    def from_src( cls, src, jcon ):
        ''' Create from an existing issue
            jcon is an instance of a jira_connection
        '''
        print(f'got src:{src}')
        params = {}
        # if type is not 'story', then assume it's a 'child'
        # use-case: SECURITY-1553 "is a child of" SVCPLAN-1911, even though type=security-vetting
        issue_type = jcon.get_issue_type(src).lower()
        if issue_type != 'story':
            issue_type = 'child'
        params['issue_type'] = issue_type
        params[issue_type] = src.key
        params['due'] = src.fields.duedate
        params['in_sprint'] = libsprint.get_active_sprint_name( src )
        params['summary'] = src.fields.summary[0:50]
        params['url'] = f'{jcon.server_url}/browse/{src.key}'
        params['key'] = src.key
        params['epic'] = jcon.get_epic_name( src )
        params['links'] = []
        for link in liblink.get_linked_issues( src ):
            if link.direction == 'inward':
                link_text = link.link_type.inward
            else:
                link_text = link.link_type.outward
            params['links'].append( f'{link_text} {link.remote_issue.key}' )
        return cls( **params )


if __name__ == '__main__':
    raise UserWarning( 'Invocation error; not a standalone script.' )
