import flask_login
import libjira


# Custom User class for use with flask_login
class User( flask_login.UserMixin ):
    def __init__( self, user_id=None ):
        self.id = user_id

    def is_authenticated( self ):
        status = False
        if libjira.is_authenticated( self.id ):
            status = True
        return status
