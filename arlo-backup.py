from arlo import Arlo

from datetime import timedelta, date
import datetime
import os
import time
import requests
import re
import functools


USERNAME = os.getenv('AB_USERNAME')
PASSWORD = os.getenv('AB_PASSWORD')

BPATH = os.getenv('AB_BASEPATH')


def GetCvrPlaylist(self, camera, fromDate, toDate):
    """ This function downloads a Cvr Playlist file for the period fromDate to toDate. """
    return self.request.get(f'https://{self.BASE_URL}/hmsweb/users/devices/'+camera.get('uniqueId')+'/playlist?fromDate='+fromDate+'&toDate='+toDate)


Arlo.GetCvrPlaylist = GetCvrPlaylist


def backup():
    arlo = Arlo(USERNAME, PASSWORD, "./gmail.credentials")
    cameras = arlo.GetDevices('camera')
    camera_names = {camera['deviceId']: camera['deviceName']
                    for camera in cameras}

    def get_camera_name(camera_id):
        try:
            return camera_names[camera_id].replace(' ', '_')
        except:
            return camera_id

    date_to = (date.today() + timedelta(days=1)).strftime("%Y%m%d")
    date_from = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

    library = arlo.GetLibrary(date_from, date_to)

    for recording in library:
        stream = arlo.StreamRecording(recording['presignedContentUrl'])
        camera_name = get_camera_name(recording['deviceId'])
        fpath = BPATH + '/events/' + datetime.datetime.fromtimestamp(
            int(recording['name']) // 1000).strftime(
                '%Y/%m/%d/%Y-%m-%d__%H-%M-%S') + '__' + camera_name + '__ev.mpeg'

        if os.path.isfile(fpath):
            print('Skipping video:   ' + fpath)
            continue

        fdir = os.path.dirname(fpath)
        if not os.path.exists(fdir):
            os.makedirs(fdir)

        with open(fpath, 'wb') as f:
            for chunk in stream:
                f.write(chunk)
            f.close()

        print('Downloaded video: ' + fpath)

    for camera in cameras:
        if camera['cvrEnabled'] != True:
            continue

        print(camera['deviceName'])

        playlist = arlo.GetCvrPlaylist(camera, date_from, date_to)
        print(playlist)

        for playlistPerDay in playlist['playlist']:
            # Iterate through each m3u8 (playlist) file
            for recordings in playlist['playlist'][playlistPerDay]:
                m3u8 = requests.get(recordings['url']).text.split("\n")
                # Iterate the m3u8 file and get all the streams
                for m3u8Line in m3u8:
                    # debug to show the m3u8 file
                    # print m3u8Line

                    # Split the url into parts used for filename (camera id and timestamp)
                    m = re.match(
                        "^http.+([A-Z0-9]{13})_[0-9]{13}_([0-9]{13})", m3u8Line)
                    if m:
                        cameraId = m.group(1)
                        videoTime = datetime.datetime.fromtimestamp(
                            int(m.group(2)) // 1000)

                        stream = arlo.StreamRecording(m3u8Line)

                        camera_name = get_camera_name(cameraId)
                        fpath = BPATH + '/timeline/' + videoTime.strftime('%Y/%m/%d/') \
                            + camera_name + '/' \
                            + videoTime.strftime('%Y-%m-%d__%H-%M-%S') \
                            + '__' + camera_name + '__tl.mpeg'

                        if os.path.isfile(fpath):
                            print('Skipping video:   ' + fpath)
                            continue

                        fdir = os.path.dirname(fpath)
                        if not os.path.exists(fdir):
                            os.makedirs(fdir)

                        with open(fpath, 'wb') as f:
                            for chunk in stream:
                                f.write(chunk)
                            f.close()

                        print('Downloaded video: ' + fpath)

    arlo.Logout()
    print('Logged out')


def main():
    while True:
        backup()
        time.sleep(600)


if __name__ == "__main__":
    main()
