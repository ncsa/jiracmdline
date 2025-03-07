#!/usr/local/bin/python3

from calendar import monthrange
from simple_issue import simple_issue
import argparse
from collections import defaultdict
import datetime
import dateutil
import jira.exceptions
import jira_connection
import libjira
import libweb
import logging
import math
import pandas as pd
# import pprint


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


# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def reset():
    global resources
    resources = {}


def get_args( params=None ):
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': (
                'Report on all worklogs '
                'for a given group '
                'in the specified timeframe.'
            ),
            'epilog': 'NETRC:'
                '    Jira login credentials should be stored in ~/.netrc.'
                '    Machine name should be hostname only.'
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        parser.add_argument( 'groups', nargs='*' ) #jira groups to include in jql
        #jira groups to include in jql (from web)
        parser.add_argument( '--group', help=argparse.SUPPRESS )
        date_mutex = parser.add_argument_group( 'Specifying Dates',
            'Defaults to --thismonth' )
        date_group = date_mutex.add_mutually_exclusive_group()
        date_group.add_argument( '--timeframe',
            help=argparse.SUPPRESS )
        date_group.add_argument( '--thismonth',
            dest='timeframe',
            action='store_const',
            const='thismonth',
        )
        date_group.add_argument( '--lastmonth',
            dest='timeframe',
            action='store_const',
            const='lastmonth',
        )
        date_group.add_argument( '--start',
            help='begin date in YYYY-MM-DD format' )
        # end is part of date specs, but don't want it part of the mutex group
        parser.add_argument( '--end',
            help='end date in YYYY-MM-DD format' )
        # startdate and enddate will hold the actual dates, after processing
        parser.add_argument( '--startdate', help=argparse.SUPPRESS )
        parser.add_argument( '--enddate', help=argparse.SUPPRESS )
        # output format = raw for web use
        parser.add_argument( '-o', '--output_format',
            choices=['text', 'csv', 'raw' ],
            default='text',
        )
        args = parser.parse_args( params )
        # process group names from --group (web only)
        if args.group:
            args.groups = args.group.split()
        # Check for group name
        if len( args.groups ) < 1:
            raise UserWarning( "No groups specified. Must have at least one" )
            # error( "No groups specified. Must have at least one" )
        # Process start, end dates
        args.startdate, args.enddate = get_month_bounds(0) # default to thismonth
        if args.timeframe == 'lastmonth':
            args.startdate, args.enddate = get_month_bounds(-1)
        elif args.start:
            args.startdate = dateutil.parser.parse( args.start, ignoretz=True ).date()
            # unused, args.enddate = get_month_bounds(0)
            if args.end:
                args.enddate = dateutil.parser.parse( args.end, ignoretz=True ).date()
        if args.startdate > args.enddate:
            raise UserWarning(
                f"""Startdate '{args.startdate}' cannot be earlier
                than Enddate '{args.enddate}'"""
                )
        resources[key] = args
    return resources[key]


def get_month_bounds( offset=0 ):
    ''' Get first and last day of the month specified by offset,
        where offset is the number of months ahead or behind the current month.
    '''
    today = datetime.date.today()
    yr_offset = int( offset / 12 )
    mo_offset = offset % 12
    if offset < 0:
        #can't get modulo of a negative number, so fix mo_offset
        mo_offset = ( abs( offset ) % 12 ) * -1
    yr = today.year + yr_offset
    mo = today.month + mo_offset
    # pprint.pprint( [ offset, yr_offset, mo_offset, yr, mo ] )
    first_day = datetime.date( yr, mo, 1 )
    last_day = datetime.date( yr, mo, monthrange( yr, mo )[1] )
    # print( f"first_day {first_day} last_day {last_day} " )
    return first_day, last_day


def get_errors():
    key = 'errors'
    if key not in resources:
        resources[key] = []
    return resources[key]


def error( msg ):
    get_errors().append( f'Error: {msg}' )


def get_warnings():
    key = 'warnings'
    if key not in resources:
        resources[key] = []
    return resources[key]


def warn( msg ):
    get_warnings().append( f'Warning: {msg}' )


def mk_jql():
    args = get_args()
    # process groups
    membersof = ','.join( [ f'membersOf("{g}")' for g in args.groups ] )
    # adjust dates for JQl formatting
    oneday = datetime.timedelta( days=1 )
    startdate = ( args.startdate - oneday ).strftime( '%Y-%m-%d' )
    enddate = ( args.enddate + oneday ).strftime( '%Y-%m-%d' )
    # construct JQL
    author = f'worklogauthor in ({membersof})'
    start = f'worklogdate > "{startdate}"'
    end = f'worklogdate < "{enddate}"'
    jql = ' AND '.join( [ author, start, end ] )
    return jql


def issue2program( issue ):
    ''' Determine what (funding) program an issue belongs to.
        IF jira project = SVCPLAN or SUP, then try (in order):
            customfield_10406 = "Programs and Services" in NCSA Jira
            customfield_10409 = "Research System"
        Otherwise, use map of jira project -> program
    '''
	# map jira project -> program
    jira_projects = {
        'CIL':   'CILogon',
        'DELTA': 'Delta',
        'HYDRO': 'Hydro',
        'IRC':   'Illinois Computes',
        'ISL':   'Innovative Systems Lab',
        'MNIP':  'mForge',
        'NUS':   'Nightingale',
    }
    # map research system -> program
    research_systems = {
		# 'Archie': '',
		'Boneyard': 'Innovative Systems Lab',
		# 'Delta': 'Delta',
		# 'DeltaAI': 'DeltaAI',
		# 'DES': '',
		# 'Granite': '',
		'HAL': 'HAL',
		'HAL-DGX': 'HAL',
		'HTC': 'Illinois Computes',
		# 'Hydro': '',
		'ICRN': 'Illinois Computes',
		'Illinois Campus Cluster': 'Illinois Campus Cluster Program (ICCP)',
		'Illinois Campus Cluster - MWT2': 'Illinois Campus Cluster Program (ICCP)',
		'isl-cluster': 'Innovative Systems Lab',
		# 'Jade': '',
		# 'Magnus': '',
		# 'mForge': '',
		'Overdrive': 'Innovative Systems Lab',
		# 'Nightingale': '',
		# 'Radiant': '',
		# 'Taiga': '',
		# 'TGIRails': '',
		'vForge': 'Industry Program',
		'Vlad': 'Innovative Systems Lab',
    }
    prj = issue.fields.project.key
    prog_serv = issue.fields.customfield_10406
    research_system = issue.fields.customfield_10409
    if prj in jira_projects:
        program = jira_projects[ prj ]
    elif prog_serv:
        program = prog_serv[0].value
    elif research_system:
        # if mapping exists, use it, otherwise, use raw value
        program = research_system[0].value
        if program in research_systems:
            program = research_systems[program]
    else:
        raise UserWarning( f'No program for issue {issue}' )
    # pprint.pprint( f"Found program: {program}" )
    return program


def num_workdays(start_date, end_date, holidays=[]):
    """Return the number of workdays between two dates, excluding given holidays."""
    # # to make this inclusive, have to modify end_date by 1
    # end = end_date + datetime.timedelta( days=1 )
    workdays = pd.bdate_range(start=start_date, end=end_date, freq='B')
    # pprint.pprint( workdays )
    return len([day for day in workdays if day not in holidays])


def print_report( projects, days ):
    args = get_args()
    start = args.startdate.strftime( '%Y-%m-%d' )
    end = args.enddate.strftime( '%Y-%m-%d' )
    hdr = f'Report for {start} - {end} ({days} work days)'
    sep = '=' * len(hdr)
    print( sep )
    print( hdr )
    print( sep )
    print()
    # raise SystemExit()
    for k, p in projects.items():
        sep = "-" * len(p.name)
        print( sep )
        print( f'{p.name}' )
        print( sep )
        print( f'TOTAL: {p.total_hours()}h' )
        print( f'\tTickets' )
        for t, hours in p.ticket_hours().items():
            print( f'\t\t{t}: {hours}h' )
        print( f'\tUsers' )
        for u, effort in p.user_effort( days ).items():
            print( f'\t\t{u}: {effort} %' )

def print_csv( projects, days ):
    # rows = []
    for k,p in projects.items():
        # pprint.pprint( p.as_csv_list() )
        for row in p.as_csv_list():
            print( ','.join( [str(r) for r in row ] ) )
            # rows.append( row )



def run( current_user=None, **kwargs ):
    parts = None
    if not current_user:
        # started from cmdline
        # raise UserWarning( "needs updates yet for cmdline" )
        current_user = jira_connection.Jira_Connection( libjira.jira_login() )
    else:
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
        # print( f"KWARGS: '{parts}'" )
    args = get_args( params=parts )

    # errs = get_errors()
    # if errs:
    #     all_errs = "\n".join( errs )
    #     raise UserWarning( all_errs )
    # print( f"ARGS: '{args}'" )
    # raise SystemExit()

    # get number of workdays covered in the date range
    holidays = [] #TODO read these in from some other source
    days = num_workdays( args.startdate, args.enddate, holidays )
    # print( f'Workdays: {days}\n' )
    # raise SystemExit()

    # make jql
    jql = mk_jql()
    # print( f"JQL: '{jql}'" )
    # raise SystemExit()

    # get issues from jira
    issues = current_user.run_jql( jql )
    # pprint.pprint(issues[0].raw)
    # pprint.pprint( issues )
    # raise SystemExit()

    # process worklogs for each issue
    projects = {}
    for i in issues:
        # pprint.pprint( [ 'ISSUE', i ] )
        try:
            program = issue2program( i )
        except UserWarning as e:
            error( e )
            continue
        project = projects.setdefault( program, ProjectEffort(program) )
        worklogs = current_user.worklogs( i )
        si = simple_issue.from_src( src=i, jcon=current_user )
        for w in worklogs:
            # pprint.pprint( w.raw )
            w_started = dateutil.parser.parse( w.started, ignoretz=True ).date()
            # print( f'{args.startdate} < {w_started} < {args.enddate} ??' )
            if w_started >= args.startdate and w_started <= args.enddate:
                # print( '---YES---' )
                author = w.author.name
                secs = w.timeSpentSeconds
                project.add_worklog( ticket=si, user=author, secs=secs )
        # raise UserWarning( 'Debug worklog' )

    if len( projects ) < 1:
        warn( f'no worklogs found' )

    if args.output_format == 'text':
        print_report( projects, days )
    elif args.output_format == 'csv':
        print_csv( projects, days )
    else:
        return {
            'projects': projects,
            'days': days,
            'group': args.group,
            'timeframe': args.timeframe,
            'startdate': args.startdate,
            'enddate': args.enddate,
            'errors': get_errors(),
            'messages': get_warnings(),
        }


if __name__ == '__main__':
    args = get_args()

    # configure logging
    loglvl = logging.WARNING
    if args.verbose:
        loglvl = logging.INFO
    if args.debug:
        loglvl = logging.DEBUG
    logr.setLevel( loglvl )
    logfmt = logging.Formatter( '%(levelname)s:%(funcName)s[%(lineno)d] %(message)s' )
    ch = logging.StreamHandler()
    ch.setFormatter( logfmt )
    logr.addHandler( ch )

    # start processing
    run()
