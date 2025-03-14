#!/usr/local/bin/python3

import csv
import io
from project_effort import ProjectEffort
from simple_issue import simple_issue
import argparse
import collections
import datetime
import dateutil
import jira_connection
import libjira
import libweb
import logging
import pandas as pd
import pprint


Week = collections.namedtuple( 'Week', [ 'start', 'end' ] )

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def reset():
    global resources
    resources = {}


def set_current_user( val ):
    key = 'current_user'
    if key not in resources:
        resources[key] = val


def get_current_user():
    key = 'current_user'
    try:
        val = resources[key]
    except KeyError:
        val = None
    return val


def get_holidays():
    # TODO read in text file of holidays
    return []


def get_args( params=None ):
    key = 'args'
    if key not in resources:
        constructor_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Report on all worklogs for the logged in user.',
            'epilog': '''NETRC:
                Jira login credentials should be stored in ~/.netrc.
                Machine name should be hostname only.
                ''',
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        # output format = raw for web use
        parser.add_argument( '-o', '--output_format',
            choices=['text', 'csv', 'raw' ],
            default='text',
        )
        args = parser.parse_args( params )
        resources[key] = args
    return resources[key]


def get_week_bounds( num=4 ):
    ''' Get first and last day of each week, starting with current week
        and then <num>-1 weeks prior to this week.
    '''
    weeks = []
    today = datetime.date.today()
    for i in range(num):
        offset = pd.Timedelta( value=i, unit='W' )
        v = today - offset
        P = pd.Period( value=v, freq='W' )
        # pprint.pprint( P )
        weeks.append( Week( P.start_time.date(), P.end_time.date() ) )
    return weeks


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


def mk_jql( week ):
    current_user = get_current_user() #instance of jira.JIRA
    if not current_user:
        raise UserWarning( 'not logged in' )
    username = current_user.current_user()
    # adjust dates for JQl formatting
    oneday = datetime.timedelta( days=1 )
    startdate = ( week.start - oneday ).strftime( '%Y-%m-%d' )
    enddate = ( week.end + oneday ).strftime( '%Y-%m-%d' )
    # construct JQL
    author = f'worklogauthor in ("{username}")'
    start = f'worklogdate > "{startdate}"'
    end = f'worklogdate < "{enddate}"'
    jql = ' AND '.join( [ author, start, end ] )
    # print( f"JQL: {jql}" )
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


def print_report( weekly_data ):
    # args = get_args()
    # start = args.startdate.strftime( '%Y-%m-%d' )
    # end = args.enddate.strftime( '%Y-%m-%d' )
    for week in weekly_data:
        hdr = f"Week of {week['startdate']} ({week['days']} work days)"
        sep = '=' * len(hdr)
        print( sep )
        print( hdr )
        print( sep )
        print()
        # raise SystemExit()
        for k, p in week['projects'].items():
            sep = "-" * len(p.name)
            print( sep )
            print( f'{p.name}' )
            print( sep )
            print( f'TOTAL: {p.total_hours()}h' )
            print( f'\tTickets' )
            for t, hours in p.ticket_hours().items():
                print( f'\t\t{t}: {hours}h' )
            print( f'\tUsers' )
            for u, effort in p.user_effort( week['days'] ).items():
                print( f'\t\t{u}: {effort} %' )

def print_csv( weekly_data ):
    file = io.StringIO()
    csvdata = csv.writer( file )
    for week in weekly_data:
        for k,p in week['projects'].items():
            # pprint.pprint( p.as_csv_list() )
            for row in p.as_csv_list():
                csvrow = [ week['startdate'] ]
                csvrow.extend( [ str(r) for r in row ] )
                csvdata.writerow( csvrow )
                # print( ','.join( [str(r) for r in row ] ) )
                # rows.append( row )
    file.seek(0)
    print( file.read() )



def run( current_user=None ):
    parts = None
    if not current_user:
        # started from cmdline
        current_user = jira_connection.Jira_Connection( libjira.jira_login() )
    else:
        reset()
        parts = [ '--output_format=raw' ]
    args = get_args( params=parts )
    set_current_user( current_user )
    username = current_user.current_user()

    # get number of workdays covered in the date range
    holidays = get_holidays()

    # get weeks to report on
    weeks = get_week_bounds()

    weekly_data = []
    for week in weeks:
        jql = mk_jql( week )

        # get issues from jira
        issues = current_user.run_jql( jql )

        # process worklogs for each issue
        projects = {}
        for i in issues:
            # pprint.pprint( [ 'ISSUE', i ] )
            try:
                program = issue2program( i )
                # pprint.pprint( [ 'PROGRAM', program ] )
            except UserWarning as e:
                error( e )
                continue
            worklogs = current_user.worklogs( i )
            si = simple_issue.from_src( src=i, jcon=current_user )
            for w in worklogs:
                w_started = dateutil.parser.parse( w.started, ignoretz=True ).date()
                if w_started >= week.start and w_started <= week.end:
                    author = w.author.name
                    secs = w.timeSpentSeconds
                    # only keep worklogs for <username>
                    if author == username:
                        # JQL will return tickets with worklogs in the timerange from
                        # any user, so can't trust those results
                        # Can't set "project" until after doing all our own
                        # checks to validate both author and date
                        project = projects.setdefault( program, ProjectEffort(program) )
                        project.add_worklog( ticket=si, user=author, secs=secs )
                    # else:
                    #     print( f"---SKIPing worklog author {author}" )

        if len( projects ) < 1:
            warn( f'no worklogs found for week {week.start}' )

        weekly_data.append( {
            'projects': projects,
            'startdate': week.start,
            'days': num_workdays( week.start, week.end, holidays ),
            }
        )

    if args.output_format == 'text':
        print_report( weekly_data )
    elif args.output_format == 'csv':
        print_csv( weekly_data )
    else:
        return {
            'weekly_data': weekly_data,
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
