import flask_login
from jira_connection import Jira_Connection


# Custom User class for use with flask_login
class User( flask_login.UserMixin ):
    def __init__( self, user_id=None ):
        self.id = user_id
        self.jira = Jira_Connection.from_user_token( personal_access_token=self.id )
        self.uname = None


    def username( self ):
        if not self.uname:
            self.uname = self.jira.current_user()
        return self.uname


    def __getattr__( self, name ):
        ''' Assume unknown attributes are calls to jira_connection methods
        '''
        return getattr( self.jira, name )
