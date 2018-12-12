# -*- coding: utf-8 -*-

from os.path import join, abspath
import re
import yaml
import requests
import zipfile
import tempfile
import os
import sys
from urlparse import urljoin


COMLUM_TOTAL = 'comlumTotal'
COMLUM = 'comlum'
TIPS = 'tips'
string_map = {COMLUM_TOTAL: 'sys_property', COMLUM: 'app_property', TIPS: 'tips'}


class ITestClient(object):
    def __init__(self, path):
        self.base_path = path
        self.json_data = {}
        self.zip_path = ''
        self._read_settings()
        self._compress_path()

    def _read_settings(self):
        file_path = abspath(join(self.base_path, 'uplaodSetting.txt'))
        for line in open(file_path, 'r').readlines():
            line = line.strip()
            m = re.search(r"(\S+?):([\s\S]+)", line)
            key_name = m.group(1)
            if key_name in string_map.keys():
                self.json_data[string_map[key_name]] = m.group(2)
            else:
                self.json_data[key_name] = yaml.load(m.group(2).replace("\/", "/"))
        file2_path = abspath(join(self.base_path, 'uploadTotalToServer.txt'))
        if not os.path.exists(file2_path):
            file2_path = file2_path.replace('.txt', '.csv')
        lines = open(file2_path, 'r').readlines()
        group = lines[0].split(',')
        self.json_data['begin_time'] = group[0].strip('Z')
        group = lines[-1].split(',')
        self.json_data['end_time'] = group[0].strip('Z')

    def _compress_path(self):
        startdir = self.base_path
        tmp_dir = tempfile.mkdtemp()
        file_news = join(tmp_dir, 'result.zip')
        z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
        for dirpath, dirnames, filenames in os.walk(startdir):
            fpath = dirpath.replace(startdir, '')
            fpath = fpath and fpath + os.sep or ''
            for filename in filenames:
                z.write(os.path.join(dirpath, filename), fpath + filename)
                # print (u'压缩成功')
        z.close()
        self.zip_path = file_news

    def get_json_data(self):
        return self.json_data

    def get_zip_file(self):
        # print self.zip_path
        return self.zip_path

    def upload_result(self, base_url):
        files = {'zip': open(self.zip_path, 'rb')}
        resp = requests.post(urljoin(base_url, 'upload'), json=self.json_data)
        if resp.status_code == 200:
            id = resp.json()['record_id']
            resp = requests.post(urljoin(base_url, 'upload1/{0}'.format(id)), files=files)
            if resp.status_code != 200:
                print "Upload Fail!"
            else:
                print(resp.json())
        else:
            print "Add Fail!"




