import requests, re, bs4, sys, enum

# Import the filedownloader module from the helpers package if it exists,
# otherwise import it from the current directory.
try:
    import helpers.filedownloader as filedownloader
except ModuleNotFoundError:
    import filedownloader as filedownloader

def __bs_find_serach__(html_text, tag, type, type_value) -> bs4.element.ResultSet:
    """Find all tags with the given type and type_value"""
    soup = bs4.BeautifulSoup(html_text, "html.parser")
    search = {}
    if type != "":
        search[type] = type_value
    if tag == "":
        # Raise an exception if the tag is empty.
        raise Exception("Tag can't be empty")
    return soup.find(tag, search)

def __bs_find_all_search__(html_text, tag, type, type_value) -> bs4.element.ResultSet:
    """Find all tags with the given type and type_value"""
    soup = bs4.BeautifulSoup(html_text, "html.parser")
    search = {}
    if type != "":
        search[type] = type_value
    if tag == "":
        # Raise an exception if the tag is empty.
        raise Exception("Tag can't be empty")
    return soup.find_all(tag, search)

def __get_request__(url, session, discard = True) -> requests.models.Response:
    """Send a get request to the given url"""
    r = Response()
    try:
        r = session.get(url)
    except requests.exceptions.ConnectionError:
        # Print an error message if the connection fails.
        print(f"Error: Failed to connect to server. Maby the URL is wrong? {url[0:30]}")
        if discard:
            # Exit the script with an error code if discard is True.
            sys.exit(1)
    return r

def __post_request__(url, data, session) -> requests.models.Response:
    """Send a post request to the given url with the given data"""
    r = None
    try:
        r = session.post(url, data=data)
    except requests.exceptions.ConnectionError:
        # Print an error message if the connection fails.
        print("Error: Failed to connect to server. Maby the URL is wrong?")
        # Exit the script with an error code.
        sys.exit(1)
    return r

def __check_if_valid_url__(url) -> bool:
    """Check if the given url is valid"""
    if url == None or url == "":
        return False
    return True

def filepath(s):
    # Replace any non-alphanumeric characters with underscores
    s = re.sub('[^0-9a-zA-Z]+', '_', s)

    # Remove duplicate underscores
    s = re.sub('_+', '_', s)

    # Convert all characters to lowercase
    s = s.lower()

    # Return the resulting string
    return s

# Define a class for colored output in the terminal.
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Define an enumeration for the different types of navigation in a course.
class KursNavTypes(enum.Enum):
    NONE = 0
    NAV_TABS = 1

# Define an enumeration for the different types of
class ResourceTypes(enum.Enum):
    FILE        = 0
    URL         = 1
    ASSIGNMENT  = 2
    FOLDER      = 3
    FORUM       = 4
    PAGE        = 5
    
# Define a class for the response of a request. This is needed because the if the request fails, the response object is not None.
class Response:
    def __init__(self):
        self.status_code = 400
        self.ok = False