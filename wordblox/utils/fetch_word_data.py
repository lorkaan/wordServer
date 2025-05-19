import requests

class ExternalServerFetchException(Exception):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.status_code = code

class FetchController:
    """
        This is a controller for fetching data from an external server.
        Specifically, this class is specifically for the fetching from SpellinBlox server
        that hosts the SpellinBlox word game.

        The goal is get the domain specific words, which requires authentication.

        Using this class, this server can essentially act as a login proxy.

    """

    # Hard code for now. Limit only to domains that I have permission to do this to.
    LOGIN_URL = "https://spellinblox.com/accounts/login/"

    # The static URL that the data exists at 
    # (Parameters are used by server to dynamically serve appropiate data)
    DATA_URL = "https://spellinblox.com/api/load/"
    

    @classmethod
    def isUsernameValid(cls, username: str):
        """
            Validation of the Username. Seperated so that it can be updated independently for more control.
        """
        return type(username) == str and len(username) > 0
    
    @classmethod
    def isPasswordValid(cls, password: str):
        """
            Validation of the Password. Seperated so that it can be updated independently for more control.
        """
        return type(password) == str and len(password) > 0
    
    @classmethod 
    def isDomainValid(cls, domain: str):
        """
            Validation of the Domain. Seperated so that it can be updated independently for more control.
        """
        return type(domain) == str and len(domain) > 0

    def __init__(self):
        """
            Constructor for the Fetch Controller. Creates a session to hold cookies and other session data for this connection.
        """
        self.session = requests.Session()

    def auth(self, username: str, password: str):
        """
            Provide a method for authenticating with the external server.

            Note: No support has been added to the external server specifically for automated logins, 
                    but I have permission from the server's admin to do this.

            @param  {str}   username    The username to authenticate with.
            @param  {str}   password    The password to authenticate with.
        """
        if not self.__class__.isUsernameValid(username):
            raise TypeError("Username is not valid")
        if not self.__class__.isPasswordValid(password):
            raise TypeError("Password is not valid")
        login_payload = {
            'username': username,
            "password": password
        }
        _ = self.session.get(self.__class__.LOGIN_URL) # result not need, but the information in the Session object is
        csrftoken = self.session.cookies.get('csrftoken') # token used when performing login

        headers = {}

        if csrftoken:
            login_payload['csrfmiddlewaretoken'] = csrftoken
            headers['Referer'] = LOGIN_URL

        login_response = self.session.post(self.__class__.LOGIN_URL, data=login_payload, headers=headers)

        if login_response.status_code not in [200, 302]:
            raise ExternalServerFetchException("ERROR: Login Failed", login_response.status_code)
        
    def getData(self, domain:str):
        """
            Fetches tag/word/detail tuple data from the external server, given a specific domain. 
            Domains are used as a control mechanism to provide independent data for multiple games on
            a single database

            @param  {str}   domain  The domain to which get tag/word/detail tuples.
        """
        if not self.__class__.isDomainValid(domain):
            raise TypeError("Domain is not valid")
        csrftoken2 = self.session.cookies.get('csrftoken')
        data_payload = {
            "domain": domain
        }
        data_headers = {
            'Content-Type': "application/json",
            "X-CSRFToken": csrftoken2
        }
        data_response = self.session.post(self.__class__.DATA_URL, headers=data_headers, json=data_payload)
        if not data_response.status_code == 200:
            raise ExternalServerFetchException("ERROR: Data could not be fetched", data_response.status_code)
        return data_response.json()

"""
    ----- Every thing under this is depreciated -----

    This is still here as a way to record and to remember as the code below was tested but the 
    translated code above has yet to be tested, even though it should be functionally equivalent

    --------------------------------------------------
"""

# Hard code for now. Limit only to domains that I have permission to do this to.
LOGIN_URL = "https://spellinblox.com/accounts/login/"

# The static URL that the data exists at 
# (Parameters are used by server to dynamically serve appropiate data)
DATA_URL = "https://spellinblox.com/api/load/"

# Depreciated
def fetch_data_with_auth(username: str, password: str, domain: str):
    """
        This is the helper function that authenticates a user and fetches the appropiate
        Word/Tag data for the game linked to their domain.

        username    {str} The username used to authenticate with the external server
        password    {str} The password used to authenticate with the external server
        domain      {str} An additional parameter required by the external server to determine
                            which data rows are relevant or appropiate.

        {Dictionary}    A dictionary returning all the tag/word/details for the given domain,
                        if the authentication was succuessfull

        {ExternalServerFetchException}  Raised if there is an issue with server communication.
    """
    login_payload = {
        'username': username,
        "password": password
    }

    session = requests.Session()

    # This block gets the csrftoken that is used when loging in automatically
    _ = session.get(LOGIN_URL) # result not need, but the information in the Session object is
    csrftoken = session.cookies.get('csrftoken') # token used when performing login

    headers = {}

    if csrftoken:
        login_payload['csrfmiddlewaretoken'] = csrftoken
        headers['Referer'] = LOGIN_URL

    login_response = session.post(LOGIN_URL, data=login_payload, headers=headers)

    if login_response.status_code not in [200, 302]:
        raise ExternalServerFetchException("ERROR: Login Failed", login_response.status_code)

    csrftoken2 = session.cookies.get('csrftoken')

    data_payload = {
        "domain": domain
    }

    data_headers = {
        'Content-Type': "application/json",
        "X-CSRFToken": csrftoken2
    }

    data_response = session.post(DATA_URL, headers=data_headers, json=data_payload)
    if not data_response.status_code == 200:
        raise ExternalServerFetchException("ERROR: Data could not be fetched", data_response.status_code)
    return data_response.json()
