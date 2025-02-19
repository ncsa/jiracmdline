import dataclasses
import liblink
import libsprint
import logging
import packaging


@dataclasses.dataclass
class simple_issue:
    ''' Basic parts of a jira issue for display purposes '''
    key: str = ''
    issue_type: str = ''
    summary: str = ''
    story: str = dataclasses.field(repr=False, default='')
    child: str = dataclasses.field(repr=False, default='')
    due: str = dataclasses.field(repr=False, default='')
    in_sprint: str = dataclasses.field(repr=False, default='')
    url: str = dataclasses.field(repr=False, default=None)
    links: list[str] = dataclasses.field( repr=False, default_factory=list )
    epic: str = dataclasses.field(repr=False, default=None)
    epic_name: str = dataclasses.field(repr=False, default=None)
    notes: str = dataclasses.field(repr=False, default='')
    resolution: str = dataclasses.field(repr=False, default='')
    resolved: str = dataclasses.field(repr=False, default='')


    def __post_init__( self ):
        if not self.due:
            self.due = '-'
        if not self.epic:
            self.epic = '-'
        if self.resolution:
            self.resolved = 'resolved'


    # def __repr__( self ):
    #     return f'<simple_issue [{self.key} ({self.summary})>'
    # __repr__ = __str__


    @classmethod
    def from_src( cls, src, jcon ):
        ''' Create from an existing issue
            jcon is an instance of a jira_connection
        '''
        logging.debug(f'got src:{src}')
        params = {}
        # if type is not 'story', then assume it's a 'child'
        # use-case: SECURITY-1553 "is a child of" SVCPLAN-1911, even though type=security-vetting
        issue_type = jcon.get_issue_type(src).lower()
        if issue_type not in ('story', 'epic') :
            issue_type = 'child'
        params['issue_type'] = issue_type
        params[issue_type] = src.key
        params['due'] = src.fields.duedate
        params['in_sprint'] = libsprint.get_active_sprint_name( src )
        params['summary'] = src.fields.summary[0:50]
        params['url'] = f'{jcon.server_url}/browse/{src.key}'
        params['key'] = src.key
        # can an epic belong to itself?
        params['epic'] = jcon.get_epic_key( src )
        params['epic_name'] = jcon.get_epic_name( src )
        if src.fields.resolution:
            params['resolution'] = src.fields.resolution.name
        params['links'] = []
        for link in liblink.get_linked_issues( src ):
            if link.direction == 'inward':
                link_text = link.link_type.inward
            else:
                link_text = link.link_type.outward
            params['links'].append( f'{link_text} {link.remote_issue.key}' )
        return cls( **params )

    def key_parts( self ):
        '''Split the key into string and numeric parts to enable better sorting
        '''
        x, y = self.key.split( sep='-', maxsplit=1 )
        return (x, int(y) )


    def __hash__( self ):
        return hash( (self.due, self.key_parts()) )


    def __eq__( self, other ):
        if isinstance( other, simple_issue ):
            return (self.due, self.key_parts()) == (other.due, other.key_parts())
        return NotImplemented


    def __lt__( self, other ):
        if isinstance( other, simple_issue ):
            return (self.due, self.key_parts()) < (other.due, other.key_parts())
        return NotImplemented


    def __le__( self, other ):
        if isinstance( other, simple_issue ):
            return (self.due, self.key_parts()) <= (other.due, other.key_parts())
        return NotImplemented


    def __gt__( self, other ):
        if isinstance( other, simple_issue ):
            return (self.due, self.key_parts()) > (other.due, other.key_parts())
        return NotImplemented


    def __ge__( self, other ):
        if isinstance( other, simple_issue ):
            return (self.due, self.key_parts()) >= (other.due, other.key_parts())
        return NotImplemented


if __name__ == '__main__':
    raise UserWarning( 'Invocation error; not a standalone script.' )
