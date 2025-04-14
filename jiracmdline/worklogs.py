#!/usr/local/bin/python3

from project_effort import ProjectEffort
from simple_issue import simple_issue
import argparse
import collections
import configparser
import csv
import datetime
import dateutil
import io
import jira_connection
from jira.resources import CustomFieldOption
import libjira
import libweb
import logging
import os
import pandas as pd
import pprint
import ldap3


Week = collections.namedtuple( 'Week', [ 'start', 'end' ] )

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
            'description': 'Report all worklogs for the specified user or group.',
            'epilog': '''NETRC:
                Jira login credentials should be stored in ~/.netrc.
                Machine name should be hostname only.
                ''',
            }
        parser = argparse.ArgumentParser( **constructor_args )
        parser.add_argument( '-d', '--debug', action='store_true' )
        parser.add_argument( '-v', '--verbose', action='store_true' )
        # user/group specification
        user_mutex = parser.add_argument_group( 'Users or Groups', 'Specify a user or a group' )
        user_group = user_mutex.add_mutually_exclusive_group()
        user_group.add_argument( '-u', '--user' )
        user_group.add_argument( '-g', '--group' )
        # output format = raw for web use
        parser.add_argument( '-o', '--output_format',
            choices=['text', 'csv', 'raw' ],
            default='text',
        )
        parser.add_argument( '-n', '--num_weeks',
            type=int,
            default=4,
            help='Number of weeks to report (default: %(default)s)')
        args = parser.parse_args( params )
        resources[key] = args
    return resources[key]


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


def get_usernames():
    key = 'query_users'
    users = []
    if key not in resources:
        args = get_args()
        if args.user:
            users = [ args.user ]
        elif args.group:
            users = group2users( args.group )
            # pprint.pprint( users )
            # raise SystemExit()
        else:
            users = [ get_current_user().current_user() ]
        resources[key] = users
    return resources[key]


def group2users( group ):
    ''' Query LDAP for members of the group
    '''
    ldap_server = 'ldaps://ldap3.ncsa.illinois.edu'
    ldap_user = None
    ldap_password = None
    search_base = 'dc=ncsa,dc=illinois,dc=edu'
    search_scope = ldap3.SUBTREE
    # attributes = ldap3.ALL_ATTRIBUTES
    attributes = ["uniqueMember"]
    users = []

    with ldap3.Connection(ldap_server, ldap_user, ldap_password) as conn:
        if not conn.bind():
            msg = "Error: Could not bind to LDAP server"
            error( msg )
            raise UserWarning( msg )
        search_filter = f"(cn={group})"
        result = conn.search(search_base, search_filter, search_scope, attributes=attributes)
        if not result:
            msg = f"Error: Could not find group {group_name}"
            error( msg )
            raise UserWarning( msg )
        entry = conn.entries[0]
        # pprint.pprint( entry )
        members = [ m for m in entry.uniqueMember ]
        uids = [ m.split(',')[0].split('=')[1] for m in entry.uniqueMember ]
        users = uids
        logr.debug(f"uids: {uids}")
        # raise SystemExit()

        # get email for each user
        # for u in uids:
        #     search_filter = f"(uid={u})"
        #     attributes = [ 'mail' ]
        #     result = conn.search(search_base, search_filter, search_scope, attributes=attributes)
        #     if not result:
        #         msg = f"Error: Could not find user {u}"
        #         # msg = f"Error: Could not find user {m}"
        #         error( msg )
        #         raise UserWarning( msg )
        #     entry = conn.entries[0]
        #     # pprint.pprint( entry )
        #     # raise SystemExit()
        #     users.append( entry.mail.value )
    return users


def get_config():
    key = 'cfg'
    if key not in resources:
        envvar = 'JCL_CONFIG'
        default_fn = 'conf/config.ini'
        conf_file = os.getenv( envvar, default_fn )
        cfg = configparser.ConfigParser( allow_no_value=True )
        cfg.optionxform = str
        cfg.read( conf_file )
        resources[key] = cfg
    return resources[key]


def get_config_section( section_name ):
    if section_name not in resources:
        cfg = get_config()
        resources[section_name] = cfg[section_name]
    return resources[section_name]


def get_holidays():
    key = 'holidays'
    section = 'holidays'
    if key not in resources:
        dates = []
        try:
            data = get_config_section(section)
        except KeyError:
            pass
        else:
            dates = [ pd.to_datetime(k) for k in data ]
        resources[key] = dates
    return resources[key]


def get_issue2program_fields():
    key = 'issue2program_fields'
    if key not in resources:
        resources[key] = get_config_section( key )
    return resources[key]


def get_issue2program_field_order():
    key = 'issue2program_field_order'
    if key not in resources:
        data = get_issue2program_fields()
        fields = [ k for k in data.keys() ]
        resources[key] = fields
    return resources[key]


def get_customfield_human_name( customfield_name ):
    key = f'{customfield_name}_human_name'
    if key not in resources:
        resources[key] = get_issue2program_fields()[customfield_name]
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
    # author = get_current_user().current_user()
    # args = get_args()
    # if args.user:
    #     author = args.user
    # elif args.group:
    #     author = f'membersOf("{args.group}")'
    usernames = [ f'"{u}"' for u in get_usernames() ]
    users = ','.join( usernames )
    # adjust dates for JQl formatting
    oneday = datetime.timedelta( days=1 )
    startdate = ( week.start - oneday ).strftime( '%Y-%m-%d' )
    enddate = ( week.end + oneday ).strftime( '%Y-%m-%d' )
    # construct JQL
    worklogauthor = f'worklogauthor in ({users})'
    start = f'worklogdate > "{startdate}"'
    end = f'worklogdate < "{enddate}"'
    jql = ' AND '.join( [ worklogauthor, start, end ] )
    return jql


def issue2program( issue ):
    ''' Determine what (funding) program an issue belongs to.
        Get customfield order from config.
        For each customfield, if a matching key is found, use that value.
        Once a value is found, stop looking.
        If no value found, throw an error.
        If the issue has multiple values in the customfield, throw an error.
    '''

    program = None
    # get order of customfields
    customfields = get_issue2program_field_order()
    # pprint.pprint( customfields )
    # raise SystemExit( 'DEBUG' )

    for fieldname in customfields:
        # split on parts to allow nested attributes, like issue.fields.project.key
        parts = fieldname.split('.')
        tgt = issue.fields
        try:
            for p in parts:
                tgt = getattr( tgt, p )
        except AttributeError:
            # if the Jira issue doesn't have this field,
            # skip it and move on to the checking the next field
            continue
        if isinstance( tgt, str ):
            lookup_key = tgt
        elif isinstance( tgt, CustomFieldOption ):
            lookup_key = tgt.value
        elif isinstance( tgt, list ):
            if len(tgt) > 1:
                fname = get_customfield_human_name( fieldname )
                raise UserWarning( f'Multiple values for field "{fname}" in issue {issue}' )
            lookup_key = tgt[0].value
        elif tgt is None:
            continue
        else:
            pprint.pprint( tgt )
            fname = get_customfield_human_name( fieldname )
            raise UserWarning( f'Unknown value type for field "{fname}" in issue {issue}' )
        # get lookup table for this fieldname
        lookup_table = get_config_section( fieldname )
        if lookup_key in lookup_table:
            program = lookup_table[ lookup_key ]
            break
    if not program:
        raise UserWarning( f'No program for issue {issue}' )
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


def run( current_user=None, **kwargs ):
    parts = None
    if not current_user:
        # started from cmdline
        current_user = jira_connection.Jira_Connection( libjira.jira_login() )
    else:
        reset()
        parts = libweb.process_kwargs( kwargs )
        parts.append( '--output_format=raw' )
    args = get_args( params=parts )
    set_current_user( current_user )
    query_users = get_usernames()
    logr.debug( f'Query Users: {query_users}' )
    # raise SystemExit()

    # get number of workdays covered in the date range
    holidays = get_holidays()

    # get weeks to report on
    weeks = get_week_bounds( args.num_weeks )

    weekly_data = []
    for week in weeks:
        jql = mk_jql( week )
        logr.debug( f'JQL: {jql}' )
        # raise SystemExit()

        # get issues from jira
        issues = current_user.run_jql( jql )
        # pprint.pprint( issues )
        # raise SystemExit()

        # process worklogs for each issue
        projects = {}
        for i in issues:
            logr.debug( [ 'ISSUE', i ] )
            # pprint.pprint( i.raw )
            # raise SystemExit()
            try:
                program = issue2program( i )
                logr.debug( [ 'PROGRAM', program ] )
            except UserWarning as e:
                error( e )
                continue
            worklogs = current_user.worklogs( i )
            si = simple_issue.from_src( src=i, jcon=current_user )
            for w in worklogs:
                w_started = dateutil.parser.parse( w.started, ignoretz=True ).date()
                if w_started >= week.start and w_started <= week.end:
                    # author = w.author.emailAddress
                    author = w.author.name
                    secs = w.timeSpentSeconds
                    # only add worklog entries from users in query_users
                    if author in query_users:
                        project = projects.setdefault( program, ProjectEffort(program) )
                        project.add_worklog( ticket=si, user=author, secs=secs )
                    else:
                        logr.debug( f"---SKIPing worklog author {author}" )

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
