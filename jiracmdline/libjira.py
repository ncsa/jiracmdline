import jira
import jira.exceptions
import jira_connection
import logging
import netrc
import os

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def jira_login( token=None, username=None, passwd=None ):
    try:
        jira_server = os.environ[ 'JIRA_SERVER' ]
    except KeyError as e:
        raise UserWarning( 'Jira Server missing. Set JIRA_SERVER environment variable' )
    params = {
        'server': f'https://{jira_server}',
        'validate': True,
    }
    if token:
        params[ 'token_auth' ] = token
    elif username and passwd:
        params[ 'basic_auth' ] = ( username, passwd )
    else:
        # attempt to get username & passwd from netrc file
        nrc = netrc.netrc()
        login, account, pwd = nrc.authenticators( jira_server )
        # if "account" is defined, assume it is a Personal Access Token
        # prefer token over username/passwd
        if account:
            params[ 'token_auth' ] = account
        else:
            params[ 'basic_auth' ] = ( login, pwd )
    try:
        raw_connection = jira.JIRA( **params )
    except jira.exceptions.JIRAError as e:
        if e.status_code != 401:
            raise e
    # return jira_connection.Jira_Connection( raw_connection )
    return raw_connection


# def get_jira( session_id=None ):
#     print( f"JL.get_jira session_id='{session_id}'" )
#     conn = None
#     if session_id:
#         print( f"JL.get_jira lookup session_id in resources" )
#         conn = resources[ session_id ]
#     else:
#         key = jira_login()
#         if key:
#             conn = resources[ key ]
#     return conn


# def is_authenticated( session_id ):
#     status = False
#     if session_id in resources:
#         status = True
#     return status


if __name__ == '__main__':
    raise SystemExit( 'not a cmdline module' )
