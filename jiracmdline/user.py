import flask_login
import libjira


# Custom User class for use with flask_login
class User( flask_login.UserMixin ):
    def __init__( self, user_id=None ):
        self.id = user_id
        self.uname = None


    def is_authenticated( self ):
        status = False
        if libjira.is_authenticated( self.id ):
            status = True
        return status


    def username( self ):
        if not self.uname:
            self.uname = libjira.get_jira( self.id ).current_user()
        return self.uname


    def logout( self ):
        libjira.jira_logout( self.id )
