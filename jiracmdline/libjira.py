import jira
import jira.exceptions
import jira_connection
import logging
import netrc
import os

# Module level resources
logr = logging.getLogger( __name__ )
resources = {}


def jira_login( token=None, jira_server=None, username=None, passwd=None ):
    if not jira_server:
        try:
            jira_server = os.environ[ 'JIRA_SERVER' ]
        except KeyError as e:
            raise UserWarning( 'Jira Server missing. Set JIRA_SERVER environment variable' )
    params = {
        'server': f'https://{jira_server}',
        'validate': True,
    }
    if token:
        logr.info( f'Login using token from params' )
        logr.debug( f"Got token '{token}' from params" )
        params[ 'token_auth' ] = token
    elif username and passwd:
        logr.debug( f'Login using usr/pwd from params' )
        params[ 'basic_auth' ] = ( username, passwd )
    else:
        # attempt to get username & passwd from netrc file
        nrc = netrc.netrc()
        login, account, pwd = nrc.authenticators( jira_server )
        # if "account" is defined, assume it is a Personal Access Token
        # prefer token over username/passwd
        if account:
            logr.info( f"Using token from .netrc" )
            logr.debug( f"Got token '{account}' from .netrc" )
            params[ 'token_auth' ] = account
        else:
            logr.debug( f'Login using usr/pwd from .netrc' )
            params[ 'basic_auth' ] = ( login, pwd )
    raw_connection = None
    try:
        raw_connection = jira.JIRA( **params )
    except jira.exceptions.JIRAError as e:
        logr.debug( f"Caught error:\n{e}" )
        if e.status_code != 401:
            raise e
    return raw_connection


if __name__ == '__main__':
    raise SystemExit( 'not a cmdline module' )
