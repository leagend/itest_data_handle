# -*- coding: utf-8 -*-

import pandas as pd
import os
import yaml
from pyecharts import configure

from DataAnalyzer import DataAnalyzer, AppPerfDrawer

STARTTIME = 'launchtime'
IOS_DATASETS_YML = 'ios_datasets.yml'
REPORTS_DIR = 'ios_reports'
configure(global_theme='roma')


def read_csv(header_text, filename):
    headers = header_text.replace(' ', '').split(',')
    df = pd.DataFrame(pd.read_csv("{0}.csv".format(filename), header=-1))
    df.columns = headers
    df = df[df['memory'] >0]
    df['upflow'] = df['upflow']
    df['downflow'] = df['downflow']
    # print(df)
    # print(filename, df.iloc[:,0].size)
    return df


def read_csv_files(header_text, files_list):
    dfs_list = []
    for _file in files_list:
        _df = read_csv(header_text, _file)
        # print(_df.iloc[:, 0].size)
        dfs_list.append(_df)
    return dfs_list


class IosDataAnalyzer(DataAnalyzer):
    def __init__(self, config_file):
        super(IosDataAnalyzer, self).__init__(config_file)
        self.type = 'IPA'

    def get_launch_time(self, folders, package_name, activity_name):
        with open(os.path.join(os.path.dirname(folders[0]), 'starttime.csv')) as file:
            string_groups = file.readline().replace(' ', '').split(',')
            startimes = []
            for item in string_groups:
                startimes.append(float(item))
        return startimes

    def extract_dataset_from_raw_files(self, original_folders):
        # 获取数据集
        original_datasets = read_csv_files(self.get_header_text(), original_folders)
        return original_datasets


if __name__ == '__main__':
    analyzer = IosDataAnalyzer(IOS_DATASETS_YML)
    # starttimes = ['2048': {}]
    drawer = AppPerfDrawer(analyzer)
    drawer.draw_lines_per_models()
    drawer.draw_summary_bars_per_scenarioes()
    clean_apk = [41.3]
    integrated_apk = [41.4]
    installed_app = [96.0]
    installed_integrated_app = [96.1]
    drawer.draw_occupation_bar(clean_apk, integrated_apk, installed_app, installed_integrated_app)
    print('Done!')

