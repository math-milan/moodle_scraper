from moodle import Moodle, MoodleCourse, SubCourse, Resources
from helpers.moodle_helper import *
from helpers.filedownloader import try_download_file
import os, requests



class MoodleDownloader():
    def __init__(self, moodle : Moodle):
        self.moodle : Moodle = moodle
        print(f"{bcolors.OKBLUE}Downloading courses...{bcolors.ENDC}")
        self.download()


    def __download_page_as_pdf__(self, resource : Resources, course_path : str):
        pass

    def __download_folder__(self, folder : Resources, course_path : str):
        folder_path = f"{course_path}/{filepath(folder.name)}"
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        for resource in folder.resources:
            self.__download_resource__(resource, folder_path)

    def __download_file__(self, file : Resources, course_path : str):
        file_path = f"{course_path}/"
        try_download_file(file.url, file_path, self.moodle.session)

    def __download_external_url__(self, resource : Resources, course_path : str):
        resource_path = f"{course_path}/{filepath(resource.name)}.url"
        if not True:# __check_if_valid_url__(resource.url):
            print(f"{bcolors.WARNING}Warning: Resource type {resource.resource_type} is not supported yet.{bcolors.ENDC}")
            return
        preset = "[{{000214A0-0000-0000-C000-000000000046}]\nProp3=19,2\n[InternetShortcut]\nIDList=\n\nURL="+resource.url+"\nIconFile=icon.ico\nIconIndex=0\n[{000214A0-0000-0000-C000-000000000046}]"
        try:
            with open(resource_path, "w") as f:
                preset = f.write(preset)
        except PermissionError:
            print(f"{bcolors.FAIL}Error: Permission denied to write to internetshortcut.url{bcolors.ENDC}")
        except FileNotFoundError:
            pass
        
    def __download_assignment__(self, resource : Resources, course_path : str):
        resource_path = f"{course_path}/{filepath(resource.name)}"
        try:
            for file in resource.resources:
                self.__download_file__(file, resource_path)
        except AttributeError:
            pass
        self.__download_page_as_pdf__(resource, resource_path)

    def __download_resource__(self, resource : Resources, course_path : str):
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
            print(f"{bcolors.WARNING}Warning: Resource type {resource.resource_type} is not supported yet.{bcolors.ENDC}")
    
    def __download_sub_course__(self, sub_course : SubCourse, course_path : str):
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
        if not os.path.exists(self.moodle.download_path):
            os.mkdir(self.moodle.download_path)
        for course in self.moodle.moodel_courses:
            print(f"{bcolors.OKBLUE}Downloading course {course.name}...{bcolors.ENDC}")
            self.__download_course__(course)
        