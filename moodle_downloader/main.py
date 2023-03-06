from moodle import Moodle
from moodle_downloader import MoodleDownloader

def run():
    moodle = Moodle()
    print(moodle)
    MoodleDownloader(moodle)

    return MoodleDownloader.download_path

if __name__ == '__main__':
    remote_path = "/moodle"
    path = run()