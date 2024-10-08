import csv
import dataclasses
import pprint


# Custom Sprint class
@dataclasses.dataclass
class Sprint:
    ''' Python representation of a Sprint '''
    id: str
    # rapidViewId: int #these might be null, not using it anywhere yet
    state: str
    name: str
    startDate: str
    endDate: str
    completeDate: str
    activatedDate: str
    # sequence: int #might be null, not using it anywhere yet
    goal: str
    autoStartStop: bool

    def is_active( self ):
        return self.state == 'ACTIVE'

# Convenience data structures for creating instances of Sprint
sprint_fields = { f.name:f for f in dataclasses.fields( Sprint ) }
sprint_field_names = sprint_fields.keys()


def get_active_sprint_name( issue ):
    sprints = get_sprint_memberships( issue )
    names = [ '' ]
    for s in sprints:
        if s.is_active():
            names.append( f"{s.name}" )
    return names[-1]


def get_sprint_memberships( issue ):
    ''' In Jira, this customfield is named "Sprint" and is unique per instance
    '''
    # memberships = issue.fields.customfield_10535 #jira-old
    memberships = issue.fields.customfield_10101
    sprints = []
    if memberships:
        for line in memberships:
                sprints.append( _str_to_sprint( line ) )
    return sprints


def _str_to_sprint( line ):
    ''' Parse a line from customfield "Sprint"
        return an instance of a Sprint
    '''
    if not line.startswith( 'com.atlassian.greenhopper.service.sprint.Sprint' ):
        raise UserWarning( f"line doesn't look like a sprint: '{line}'" )
    csv_start = line.index( '[' ) + 1
    raw_csv = line[csv_start:-1]
    # return csv
    reader = csv.reader( [ raw_csv ] )
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
