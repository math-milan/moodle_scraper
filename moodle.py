import requests, re, bs4, sys, configparser, helpers.filedownloader as filedownloader, enum, os, json
from helpers.moodle_helper import __get_request__, __post_request__, __bs_find_serach__, __bs_find_all_search__, bcolors, KursNavTypes, ResourceTypes
from typing import List

from helpers.filedownloader import try_download_file, __is_downloadable__, __smaler_then_max_size__, __get_file_name_from_header__, __size_from_header__

path = "config.ini"

CONFIG = configparser.ConfigParser()

class Resources():
    url : str = None
    name : str = None

    size : int = None

    resource_type : ResourceTypes = None

    html : str = None
    html_header : dict = None
    html_status : bool = None

    def __init__(self, name : str, url : str, session : requests.sessions.Session, forcetype : ResourceTypes=None) -> None:
        self.name, self.url, self.session, self.forcetype = name, url, session, forcetype
        
        self.__get_html__()
        if not self.html_status:
            return None
        self.__get_resource_type__()
        if self.forcetype != None and self.forcetype != self.resource_type:
            print(f"{bcolors.FAIL}Resource type missmatch.", self.name, self.url, f"{bcolors.ENDC}"	)
            return None
        self.__get_name__()
        self.__get_external_url__()
        self.__get_resurce__()

    def __get_external_url__(self):
        if self.resource_type != ResourceTypes.URL:
            return None
        self.url = self.response.url

    def __get_html__(self):
        """Get the html of the course page"""
        try:
            r = __get_request__(self.url, self.session, discard=False)
        except requests.exceptions.ConnectionError:
            self.html_status = False
            return None
        if r.ok:
            self.response = r
            self.html = r.text
            self.html_header = r.headers
            self.html_status = True
        else:
            self.html_status = False

    def get_size(self):
        if not self.resource_type == ResourceTypes.FILE:
            return None
        self.size = __size_from_header__(self.html_header)

    def __get_resource_type__(self):
        if __is_downloadable__(self.html_header):
            self.resource_type = ResourceTypes.FILE
        elif "mod/url/" in self.url and "&redirect=1" in self.url:
            self.resource_type = ResourceTypes.URL
        elif "/mod/folder/" in self.url:
            self.resource_type = ResourceTypes.FOLDER
            self.resources : List[Resources] = []
        elif "/mod/assign/" in self.url:
            self.resource_type = ResourceTypes.ASSIGNMENT
        elif "/mod/forum/" in self.url:
            self.resource_type = ResourceTypes.FORUM
        elif "/mod/page/" in self.url:
            self.resource_type = ResourceTypes.PAGE

    def __get_name__(self):
        if self.resource_type == ResourceTypes.FILE:
            self.name = __get_file_name_from_header__(self.html_header)
        
    def __get_resurce__(self):
        if not self.resource_type == ResourceTypes.FOLDER:
            return None
        result = __bs_find_serach__(self.html, CONFIG["MOODLE_FOLDER"]["region_tag"], CONFIG["MOODLE_FOLDER"]["region_type"], CONFIG["MOODLE_FOLDER"]["region_type_value"])
        result = __bs_find_all_search__(str(result), CONFIG["MOODLE_FOLDER"]["content_tag"], CONFIG["MOODLE_FOLDER"]["content_type"], CONFIG["MOODLE_FOLDER"]["content_type_value"])
        for i in result:
            try:
                href = i["href"]
            except KeyError:
                print(self.url, f"{bcolors.FAIL}KeyError{bcolors.ENDC}")
            name = __bs_find_serach__(str(i), CONFIG["MOODLE_FOLDER"]["name_tag"], CONFIG["MOODLE_FOLDER"]["name_type"], CONFIG["MOODLE_FOLDER"]["name_type_value"]).text
            if name != None:
                self.resources.append(Resources(name, href, self.session, ))

    def __str__(self) -> str:
        s = ""
        if self.resource_type == ResourceTypes.FILE:
            s += f"{self.name} {self.resource_type}\n"
        elif self.resource_type == ResourceTypes.URL:
            s += f"{bcolors.UNDERLINE}{self.name} {self.resource_type}{bcolors.ENDC}\n"
        elif self.resource_type == ResourceTypes.FOLDER:
            s += f"{bcolors.OKCYAN}{self.name} {self.resource_type}{bcolors.ENDC}\n"
        elif self.resource_type == ResourceTypes.ASSIGNMENT:
            s += f"{bcolors.WARNING}{self.name} {self.resource_type}{bcolors.ENDC}\n"
        else:
            s += f"{self.name} {self.resource_type}\n"
        return s

class SubCourse():
    url : str = None
    name : str = None

    course_nav_tabs : KursNavTypes = None

    resources : List[Resources] = None # contains a list of resources if no sub sub courses are available
    sub_courses = None # contains a list of sub sub courses

    html : str = None
    html_status : bool = None

    def __init__(self, name : str, url : str, session : requests.sessions.Session, deepSearch = True) -> None:
        """Initialize the sub course with the given name and url"""
        self.name, self.url, self.session = name, url, session
        self.resources = []
        self.sub_courses = []

        self.__get_html__()
        if not self.html_status:
            return None
        
        if deepSearch:
            self.__get_nav_tabs__()
        else:
            self.course_nav_tabs = KursNavTypes.NONE
        if self.course_nav_tabs == KursNavTypes.NONE:
            self.__search_for_resources__()

    def __get_html__(self):
        """Get the html of the course page"""
        try:
            r = __get_request__(self.url, self.session)
        except requests.exceptions.ConnectionError:
            self.html_status = False
            return None
        if r.ok:
            self.html = r.text
            self.html_status = True
        else:
            self.html_status = False

    def __get_nav_tabs__(self):
        """Get the nav tabs of the sub course"""
        result = __bs_find_all_search__(self.html, CONFIG["MOODLE_COURSE_NAV"]["region_tag"], CONFIG["MOODLE_COURSE_NAV"]["region_type"], CONFIG["MOODLE_COURSE_NAV"]["region_type_value"])
        if len(result) != 2:
            self.course_nav_tabs = KursNavTypes.NONE
            return None
        tabs = __bs_find_all_search__(str(result[1]), CONFIG["MOODLE_COURSE_NAV"]["course_nav_tag"], CONFIG["MOODLE_COURSE_NAV"]["course_nav_type"], CONFIG["MOODLE_COURSE_NAV"]["course_nav_type_value"])
        if len(tabs) == 0:
            self.course_nav_tabs = KursNavTypes.NONE
        else:
            self.course_nav_tabs = KursNavTypes.NAV_TABS
            for tab in tabs:
                try:
                    link = tab["href"].replace("§", "&sect") # Maby a bug in bs4. The bs4 object returns a false link with § instead of &sect after the course id. Cheap hot fix
                    sub_course = SubCourse(tab["title"], link, self.session, False)
                    self.sub_courses.append(sub_course)
                except KeyError:
                    sub_course = SubCourse(tab["title"], self.url, self.session, False)
                    self.sub_courses.append(sub_course)

    def __search_for_resources__(self):
        result = __bs_find_serach__(self.html, CONFIG["MOODLE_SUB_CONTENT"]["region_tag"], CONFIG["MOODLE_SUB_CONTENT"]["region_type"], CONFIG["MOODLE_SUB_CONTENT"]["region_type_value"])
        result = __bs_find_all_search__(str(result), CONFIG["MOODLE_SUB_CONTENT"]["content_tag"], CONFIG["MOODLE_SUB_CONTENT"]["content_type"], CONFIG["MOODLE_SUB_CONTENT"]["content_type_value"])
        for i in result:
            href = ""
            match = re.search(r"window\.open\('(.+?)'\);", i["onclick"])
            if match:
                href = match.group(1)
            else:
                href = i["href"]
            titel = i.find("span").text
            try:
                self.resources.append(Resources(titel, href, self.session))
            except requests.exceptions.InvalidSchema:
                print(href)
                print(match.group(1))

        
    def __str__(self) -> str:
        s = ""
        if self.course_nav_tabs == KursNavTypes.NONE:
            s += f"\t\t{bcolors.OKGREEN}{self.name}{bcolors.ENDC} Number of Resources: {len(self.resources)} {bcolors.FAIL}{self.url}{bcolors.ENDC}\n"
            for r in self.resources:
                s += f"\t\t\t{r}"
        elif self.course_nav_tabs == KursNavTypes.NAV_TABS:
            s += f"\t\t{bcolors.OKGREEN}{self.name}{bcolors.ENDC} Number of Sub Courses: {len(self.sub_courses)} {bcolors.FAIL}{self.url}{bcolors.ENDC}\n"
            for c in self.sub_courses:
                s += f"{c}"
        return s

class MoodleCourse():
    course_nav_types : KursNavTypes = None
    sub_courses = None
    resources = None

    url : str = None
    name : str = None

    html : str = None
    html_status : bool = None

    download_path : str = None

    def __init__(self, name : str, url : str, session : requests.sessions.Session) -> None:
        """Initialize the moodle course with the given name and url"""
        self.name, self.url, self.session = name, url, session

        self.sub_courses = []
        self.resources = []

        self.__get_html__()
        if not self.html_status:
            return None
        
        self.__get_nav_type__()
        if self.course_nav_types == KursNavTypes.NONE:
            self.__search_for_resources__()
        elif self.course_nav_types == KursNavTypes.NAV_TABS:
            pass
        
    
    def __get_html__(self) -> None:
        """Get the html of the course page"""
        try:
            r = __get_request__(self.url, self.session)
        except requests.exceptions.ConnectionError:
            self.html_status = False
            return None
        if r.ok:
            self.html = r.text
            self.html_status = True
        else:
            self.html_status = False

    def __get_nav_type__(self):
        """Get the course nav tabs"""
        result = __bs_find_serach__(self.html, CONFIG["MOODLE_COURSE_NAV"]["region_tag"], CONFIG["MOODLE_COURSE_NAV"]["region_type"], CONFIG["MOODLE_COURSE_NAV"]["region_type_value"])
        tabs = __bs_find_all_search__(str(result), CONFIG["MOODLE_COURSE_NAV"]["course_nav_tag"], CONFIG["MOODLE_COURSE_NAV"]["course_nav_type"], CONFIG["MOODLE_COURSE_NAV"]["course_nav_type_value"])
        if len(tabs) == 0:
            self.course_nav_types = KursNavTypes.NONE
            return None
        else:
            self.course_nav_types = KursNavTypes.NAV_TABS
            for tab in tabs:
                try:
                    link = tab["href"].replace("§", "&sect") # Maby a bug in bs4. The bs4 object returns a false link with § instead of &sect after the course id. Cheap hot fix
                    sub_course = SubCourse(tab["title"], link, self.session)
                    self.sub_courses.append(sub_course)
                except KeyError:
                    sub_course = SubCourse(tab["title"], self.url, self.session)
                    self.sub_courses.append(sub_course)

    def __search_for_resources__(self):
        result = __bs_find_serach__(self.html, CONFIG["MOODLE_MAIN_COUNTENT"]["region_tag"], CONFIG["MOODLE_MAIN_COUNTENT"]["region_type"], CONFIG["MOODLE_MAIN_COUNTENT"]["region_type_value"])
        result = __bs_find_all_search__(str(result), CONFIG["MOODLE_MAIN_COUNTENT"]["content_tag"], CONFIG["MOODLE_MAIN_COUNTENT"]["content_type"], CONFIG["MOODLE_MAIN_COUNTENT"]["content_type_value"])
        for i in result:
            href = ""
            match = re.search(r"window\.open\('(.+?)'\);", i["onclick"])
            if match:
                href = match.group(1)
            else:
                href = i["href"]
            titel = i.find("span").text

            self.resources.append(Resources(titel, href, self.session))

    def __str__(self) -> str:
        s = ""
        s += f"\t{bcolors.OKBLUE}{self.name}{bcolors.ENDC} Number of Resources: {bcolors.OKCYAN}{len(self.resources)}{bcolors.ENDC}\n"
        if self.course_nav_types == KursNavTypes.NAV_TABS:
            for sub_course in self.sub_courses:
                s += f"{sub_course}"
        else:
            for r in self.resources:
                s += f"\t\t{r}"
        return s

class Moodle():    
    session : requests.sessions.Session = requests.session()

    moodel_courses : List[MoodleCourse] = []

    def __init__(self, config_path : str = "config.ini") -> None:
        """Initialize the moodel class with the given config file"""
        path = config_path
        CONFIG.read(path)

        self.download_path = CONFIG["LOGIN"]["download_path"]

        self.base_url = CONFIG['MOODLE_URLS']['base_url']
        
        self.__get_login_token__()
        if not self.login():
            print(f"{bcolors.FAIL}Error: Failed to login. Maby the username or password is wrong?{bcolors.ENDC}")
            sys.exit(1)
        else:
            print(f"{bcolors.OKGREEN}Login successful!{bcolors.ENDC}")
        
        self.__get_courses__()

    def __get_login_token__(self):
        """Get the login token from the login page"""
        login_url = self.base_url + CONFIG["MOODLE_URLS"]["login_url"]
        r = __get_request__(login_url, self.session)
        if r.ok:
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            token = soup.find(id='login').find('input', {'name': 'logintoken'})['value']
        self.token = token
    
    def login(self):
        """Login to moodle and return True if login was successful"""
        login_url = self.base_url + CONFIG["MOODLE_URLS"]["login_url"]
        login_data = {
            "username": CONFIG["LOGIN"]["user"],
            "password": CONFIG["LOGIN"]["pwd"],
            "logintoken": self.token
        }
        r = __post_request__(login_url, login_data, self.session)
        if r.ok:
            return True
        else:
            return False
        
    def __get_courses__(self):
        """Get a list of all courses urls"""
        courses_urls = []

        courses_url = self.base_url + CONFIG["MOODLE_URLS"]["courses_url"]

        r = __get_request__(courses_url, self.session)

        if r.ok:
            result = __bs_find_serach__(r.text, CONFIG["MOODLE_COURSES"]["region_tag"], CONFIG["MOODLE_COURSES"]["region_type"], CONFIG["MOODLE_COURSES"]["region_type_value"])
            result = __bs_find_all_search__(str(result), CONFIG["MOODLE_COURSES"]["course_tag"], CONFIG["MOODLE_COURSES"]["course_type"], CONFIG["MOODLE_COURSES"]["course_type_value"])
            for course in result:
                courses_urls.append({"name": course.text, "links": [course['href']]})
        else:
            print("Error: Failed to get courses")
            sys.exit(1)
        
        # course = courses_urls[1]
        # moodle_course = MoodleCourse(course["name"], course["links"][0], self.session)
        # self.moodel_courses.append(moodle_course)
        for course in courses_urls:
            print(f"{bcolors.FAIL}Start downloading course: " + course["name"] + f"{bcolors.ENDC}")
            moodle_course = MoodleCourse(course["name"], course["links"][0], self.session)
            
            self.moodel_courses.append(moodle_course)
    
    def __str__(self) -> str:
        s = ""
        for course in self.moodel_courses:
            s += f"{course}"
        return s

if __name__ == "__main__":
    m = Moodle()
    print(m)
