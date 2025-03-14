#!/usr/local/bin/python3

from collections import defaultdict
import math


class ProjectEffort:
    '''Track effort (hours) on a project per task and per author.
    '''
    user_max_hours_daily = 6.4 #32 focus hours per week / 5 work days per week

    def __init__( self, name: str ):
        self.name = name
        self.tickets = defaultdict( int )
        self.users = defaultdict( int )
        self.total = 0
        self.data = defaultdict(lambda: defaultdict(int)) #2-deep defaultdict

    def add_worklog( self, ticket: str, user: str, secs: int ):
        # print( f'Add: {self.name} {ticket.key}, {user} {secs}' )
        self.data[ticket.key][user] += secs
        # update per-ticket, per-user, per-project totals
        self.tickets[ticket] += secs
        self.users[user] += secs
        self.total += secs

    def ticket_hours( self ):
        return { t: self.s2h(v) for t,v in self.tickets.items() }

    def total_hours( self ):
        return self.s2h( self.total )

    def user_effort( self, num_days ):
        # effort hours = user hours / hours_in_the_specified_range
        # which makes it entirely relevant on the request time range
        range_hours = num_days * self.user_max_hours_daily
        # percent = secs / 3600 / num_days / user_max_hours_daily * 100
        return { u: v/36/range_hours for u,v in self.users.items() }

    def as_csv_list( self ):
        table = []
        for t, u_data in self.data.items():
            for u, secs in u_data.items():
                table.append( [ self.name, t, u, secs ] )
        return table

    def urls_for_all_tickets( self ):
        urls = {}
        servers = defaultdict( list )
        for t in self.tickets:
            sname = t.server_url
            servers[ sname ].append( t )
        for s, tickets in servers.items():
            keys = ','.join( [ t.key for t in tickets ] )
            s_name = s[8:]
            urls[s_name] = f"{s}/issues/?jql=key%20in%20({keys})"
        return urls

    @staticmethod
    def s2h( seconds ):
        """Convert seconds to hours, rounding up to the nearest quarter-hour."""
        quarter_hours = seconds / 900  # Convert seconds to quarter-hour units
        return math.ceil(quarter_hours) * 0.25  # Round up and convert back to hours

    def __str__( self ):
        return f'<ProjectEffort ({self.name}: tickets={len(self.tickets)} time={self.total})>'

    __repr__ = __str__


if __name__ == '__main__':
    raise SystemExit( 'not a cmdline module' )
