import csv
import libjira
import liblink
import logging
import pprint

logr = logging.getLogger( __name__ )

class Jira_Connection( object ):
    def __init__( self, conn ):
        self.jira = conn


    @classmethod
    def from_session_id( cls, session_id ):
        conn = libjira.get_jira( session_id )
        return cls( conn )


    @classmethod
    def from_user_token( cls, personal_access_token ):
        conn = libjira.jira_login( token=personal_access_token )
        return cls( conn )


    def __getattr__( self, name ):
        ''' Allow access to jira.JIRA attributes as a last resort.
        '''
        return getattr( self.jira, name )


    def run_jql( self, jql ):
        return self.jira.search_issues( jql, maxResults=9999 )


    def get_issue_by_key( self, key ):
        ''' key: String
        '''
        return self.jira.issue( key )


    def get_issues_by_keys( self, keys ):
        ''' keys: List of Strings
        '''
        csv = ",".join( keys )
        return self.run_jql( f'key in ({csv})' )


    def reload_issue( self, issue ):
        return self.get_issue_by_key( issue.key )


    def reload_issues( self, issues ):
        return [ self.reload_issue(i) for i in issues ]


    @staticmethod
    def get_issue_type( issue ):
        return issue.fields.issuetype.name


    @staticmethod
    def get_labels( issue ):
        return issue.fields.labels


    @staticmethod
    def get_epic_name( issue ) :
        try:
            epic = issue.fields.customfield_10536
        except AttributeError:
            epic = None
        return epic


    def get_parent( self, issue ):
        try:
            parent_key = issue.fields.parent
        except AttributeError:
            parent = None
        else:
            parent = self.get_issue_by_key( parent_key )
        return parent


    def get_linked_parent( self, issue ):
        jql = f'issue in linkedIssues( {issue.key}, "is a child of" )'
        issues = self.run_jql( jql )
        qty = len( issues )
        if qty > 1:
            raise UserWarning( f"Found more than one parent for '{issue.key}'" )
        elif qty < 1:
            parent = None
        else:
            parent = issues[0]
        return parent


    def get_linked_children( self, parent ):
        jql = f'issue in linkedIssues( {parent.key}, "is the parent of" )'
        return self.run_jql( jql )


    def get_project_key( self, issue ):
        return issue.key.split('-')[0]


    def get_issues_in_epic( self, issue_key, stories_only=False, exclude_completed_issues=True ):
        jql = f'"Epic Link" = {issue_key}'
        if stories_only:
            jql = f'{jql} and type = Story'
        if exclude_completed_issues:
            jql = f'{jql} and resolved is empty'
        return self.run_jql( jql )


    def get_stories_in_epic( self, issue_key ):
        return self.get_issues_in_epic( issue_key, stories_only=True )


    def print_issue_summary( self, issue, parts=None ):
        # force reload of issue
        i = self.reload_issue( issue )
        print( f"{i}" )
        print( f"\tSummary: {i.fields.summary}" )
        print( f"\tEpic: {get_epic_name( i )}" )
        # print( f"\tDescription: {i.fields.description}" )
        links = liblink.get_linked_issues( i )
        for link in links:
            if link.direction == 'inward':
                link_text = link.link_type.inward
            else:
                link_text = link.link_type.outward
            print( f"\tLink: {link_text} {link.remote_issue.key}" )


    def link_to_parent( self, child, parent, dryrun=False ):
        logr.info( f'Create link: Parent={parent} -> Child={child}' )
        if dryrun:
            return #stop here on dryrun
        self.jira.create_issue_link(
            type='Ancestor',
            inwardIssue=parent.key,
            outwardIssue=child.key
        )


    def add_tasks_to_epic( self, issue_list, epic_key ):
        params = {
            'epic_id': epic_key,
            'issue_keys': [ i.key for i in issue_list ],
            }
        result = self.jira.add_issues_to_epic( **params )
        logr.debug( f"Add to epic results: '{pprint.pformat( result ) }'" )
        result.raise_for_status() # https://requests.readthedocs.io/en/latest/api/#requests.Response


    def mk_child_tasks( self, parent, child_summaries, dryrun=False ):
        ''' parent: parent Story ticket
            child_summaries: list of strings, each is the summary for a new ticket
        '''
        defaults = {
            'project': { 'key': self.get_project_key( parent ) },
            'issuetype': { 'name': 'Task' },
        }
        issue_list = []
        for summary in child_summaries:
            custom_parts = { 'summary': summary[0:254] }
            issue_list.append( defaults | custom_parts )
        logr.debug( f'About to create {pprint.pformat( issue_list )}' )
        child_issues = []
        if not dryrun and issue_list:
            new_tasks = self.jira.create_issues( field_list=issue_list )
            for result in new_tasks:
                if result['status'] == 'Success':
                    child = result['issue']
                    logr.info( f"Created issue: {child}" )
                    self.link_to_parent( child=child, parent=parent )
                    child_issues.append( child )
                else:
                    logr.warn( f"Error creating child ticket: '{pprint.pformat( result )}'" )
        return child_issues


if __name__ == '__main__':
    raise SystemExit( 'not a cmdline module' )
