from moodle import Moodle, MoodleCourse, SubCourse, Resources
from helpers.moodle_helper import __check_if_valid_url__, __bs_find_all_search__, __bs_find_serach__, __get_request__, __post_request__, filepath, bcolors, ResourceTypes, KursNavTypes
from helpers.filedownloader import try_download_file
import os, requests

import pdfkit

class MoodleDownloader():
    download_path = "downloads"

    def __init__(self, moodle : Moodle):
        """Initializes the class with a Moodle instance and sets the download path. Calls the download() method to start downloading the courses."""
        self.moodle : Moodle = moodle
        self.download_path = moodle.download_path
        print(f"{bcolors.OKBLUE}Downloading courses...{bcolors.ENDC}")
        self.download()

    def __download_page_as_pdf__(self, resource : Resources, course_path : str):
        """"method converts a given Moodle page into a PDF file and saves it to a specific course folder."""
        try:
            options = { 'quiet': '' }
            pdfkit.from_string(resource.html, f"{course_path}/{resource.name}.pdf", options=options)
            pass
        except OSError:
            pass
        except Exception as e:
            print(f"{bcolors.FAIL}Error: {e}{bcolors.ENDC}")
    def __download_folder__(self, folder : Resources, course_path : str):
        """downloads all the resources in a given Moodle folder and saves them to a specific course folder."""
        folder_path = f"{course_path}/{filepath(folder.name)}"
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        try:        
            for resource in folder.resources:
                self.__download_resource__(resource, folder_path)
        except AttributeError:
            pass
        self.__download_page_as_pdf__(folder, folder_path)
        pass

    def __download_file__(self, file : Resources, course_path : str):
        """downloads a given Moodle file and saves it to a specific course folder."""
        file_path = f"{course_path}"
        try_download_file(file.url, file_path, self.moodle.session)

    def __download_external_url__(self, resource : Resources, course_path : str):
        """method downloads an external URL and saves it to a specific course folder."""
        resource_path = f"{course_path}/{filepath(resource.name)}.url"
        if not __check_if_valid_url__(resource.url):
            print(f"{bcolors.WARNING}Warning: Resource type {resource.resource_type} is not supported yet.{bcolors.ENDC}")
            return
        preset = "[{000214A0-0000-0000-C000-000000000046}]\nProp3=19,2\n[InternetShortcut]\nIDList=\n\nURL="+resource.url+"\nIconFile=icon.ico\nIconIndex=0\n[{000214A0-0000-0000-C000-000000000046}]"
        try:
            with open(resource_path, "w") as f:
                preset = f.write(preset)
        except PermissionError:
            print(f"{bcolors.FAIL}Error: Permission denied to write to internetshortcut.url{bcolors.ENDC}")
        except FileNotFoundError:
            pass
        
    def __download_assignment__(self, resource : Resources, course_path : str):
        """method downloads all the resources in a given Moodle assignment and saves them to a specific course folder."""
        resource_path = f"{course_path}/{filepath(resource.name)}"
        try:
            print("Downloading assignment...")
            self.__download_folder__(resource, course_path)
        except AttributeError:
            pass
        self.__download_page_as_pdf__(resource, resource_path)

    def __download_resource__(self, resource : Resources, course_path : str):
        """method checks the type of a given Moodle resource and calls the appropriate method to download it."""	
        if resource.resource_type == ResourceTypes.FILE:
            self.__download_file__(resource, course_path)
        elif resource.resource_type == ResourceTypes.FOLDER:
            self.__download_folder__(resource, course_path)
        elif resource.resource_type == ResourceTypes.PAGE:
            self.__download_page_as_pdf__(resource, course_path)
        elif resource.resource_type == ResourceTypes.URL:
            self.__download_external_url__(resource, course_path)
        elif resource.resource_type == ResourceTypes.ASSIGNMENT:
            self.__download_assignment__(resource, course_path)
        elif resource.resource_type == ResourceTypes.FORUM:
            print(f"{bcolors.WARNING}Warning: Resource type {resource.resource_type} is not supported yet.{bcolors.ENDC}")
        else:
            print(f"{bcolors.WARNING}Warning: Resource type {resource.resource_type} is not supported yet. URL: {resource.url}{bcolors.ENDC}")
    
    def __download_sub_course__(self, sub_course : SubCourse, course_path : str):
        """method downloads all the resources in a given Moodle sub-course and saves them to a specific course folder."""
        course_path = f"{course_path}/{filepath(sub_course.name)}"
        if not os.path.exists(course_path):
            os.mkdir(course_path)
        if sub_course.course_nav_tabs == KursNavTypes.NAV_TABS:
            for sub_sub_course in sub_course.sub_courses:
                self.__download_sub_course__(sub_sub_course, course_path)
        elif sub_course.course_nav_tabs == KursNavTypes.NONE:
            for resource in sub_course.resources:
                self.__download_resource__(resource, course_path)
        
        pass

    def __download_course__(self, course : MoodleCourse):
        """method downloads all the resources in a given Moodle course and saves them to a specific course folder."""
        course_path = f"{self.moodle.download_path}/{filepath(course.name)}"
        if not os.path.exists(course_path):
            os.mkdir(course_path)
        if course.course_nav_types == KursNavTypes.NAV_TABS:
            for sub_course in course.sub_courses:
                self.__download_sub_course__(sub_course, course_path)
        elif course.course_nav_types == KursNavTypes.NONE:
            for resource in course.resources:
                self.__download_resource__(resource, course_path)

    def download(self):
        """This method iterates over all the Moodle courses in the Moodle object and calls the appropriate method to download them."""
        if not os.path.exists(self.moodle.download_path):
            os.mkdir(self.moodle.download_path)
        for course in self.moodle.moodel_courses:
            print(f"{bcolors.OKBLUE}Downloading course {course.name}...{bcolors.ENDC}")
            self.__download_course__(course)
        