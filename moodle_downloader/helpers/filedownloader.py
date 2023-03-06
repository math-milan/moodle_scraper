# Import required libraries
import requests, re, os

# Set the maximum file size to be downloaded to 200MB
MAX_SIZE = 2e8

# Define the colors to be used in the terminal
FAIL = '\033[91m'
ENDC = '\033[0m'

# Define a helper function to check if the URL points to a downloadable resource
def __is_downloadable__(header):
    """
    Does the url contain a downloadable resource
    """
    # Get the content type from the HTTP header
    content_type = header.get('content-type')
    # Check if the content type indicates that the resource is a text or HTML document
    if 'html' in content_type.lower():
        return False
    
    # Otherwise, assume the resource is downloadable
    return True


def __size_from_header__(header):
    """
    Get the size of the file from the header
    """
    # Get the content length from the HTTP header
    content_length = header.get('content-length', 0)
    return int(content_length)

# Define a helper function to check if the file size is smaller than the maximum size
def __smaler_then_max_size__(header):
    """
    Is the file smaller than the max size
    """
    # Get the content length from the HTTP header
    content_length = header.get('content-length', 0)
    
    # If the content length is larger than the maximum size, the file is too large
    if int(content_length) > MAX_SIZE:
        return False
    
    # Otherwise, assume the file is small enough to download
    return True

# Define a helper function to extract the file name from the HTTP header
def __get_file_name_from_header__(header):
    """
    Get the file name from the header
    """
    # Get the content disposition from the HTTP header
    cd = header.get('content-disposition')
    
    # If there is no content disposition, there is no file name to extract
    if not cd:
        return None
    
    # Use regular expressions to extract the file name from the content disposition
    fname = re.findall('filename=(.+)', cd)
    
    # If no file name is found, return None
    if len(fname) == 0:
        return None
    
    # Otherwise, return the first file name found
    return fname[0].replace('"', '')

def filepath(s):
    # Replace any non-alphanumeric characters with underscores 
    s = re.sub('[^0-9a-zA-Z]+', '_', s)

    # Remove duplicate underscores
    s = re.sub('_+', '_', s)

    # Convert all characters to lowercase
    s = s.lower()

    # replace the last underscore with a dot
    for i in range(len(s) - 1, 0, -1):
        if s[i] == '_':
            s = s[:i] + '.' + s[i + 1:]
            break

    # Return the resulting string
    return s

# Define the main function to download a file from a URL to a local destination
def try_download_file(url : str, dst : str, s : requests.sessions.Session = None, give_warning = True, timeout = 3):
    """
    Download a file from a url to a destination
    """
    r = None
    # Send an HTTP GET request to the URL and stream the response to avoid downloading the entire file at once
    try:
        if s == None: r = requests.get(url, stream=True, allow_redirects=True)
        else: r = s.get(url, stream=True, allow_redirects=True)
    except requests.exceptions.ConnectionError:
        if give_warning:
            print(f"{FAIL}Wrong URL{ENDC}")
        return False
    except requests.exceptions.SSLError:
        if give_warning:
            print(f"{FAIL}SSL Error, no valid certificate{ENDC}")
        return False
    except requests.exceptions.MissingSchema:
        return False
    except requests.exceptions.ReadTimeout:
        if give_warning:
            print(f"{FAIL}Timeout, discard request. URL: {url}{ENDC}")
        return False

    # Check if the resource is downloadable and small enough to download
    if __is_downloadable__(r.headers) and __smaler_then_max_size__(r.headers):
        # Extract the file name from the HTTP header
        fname = __get_file_name_from_header__(r.headers)
        
        # If a file name is found, append it to the destination path
        if fname:
            dst = dst + "/" + fname
        else:
            return False
        

        if os.path.exists(dst):
            return True
        
        # Open the destination file in binary write mode and write the response in chunks of 1024 bytes
        try:
            with open(dst, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except PermissionError:
            if give_warning:
                print(f"{FAIL}Permission denied{ENDC}")
            return False
        except FileNotFoundError:
            pass
        
        # Return True to indicate that the download was successful
        return True
    
    # Return False to indicate that the download failed
    return False

# Define a conditional block that is executed when the script is run as the main program
if __name__ == "__main__":
    # Prompt the user to enter the URL and destination for the file to download
    url = input("Enter the url of the file to download: ")
    dst = input("Enter the destination of the file: ")
    
    # Call the download_file function with the user-specified URL and destination
    result = try_download_file(url, dst)
    if result:
        print("Download successful")
    else:
        print("Download failed")

