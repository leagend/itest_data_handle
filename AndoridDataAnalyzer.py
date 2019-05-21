# -*- coding: utf-8 -*-

import os
import re

import pandas as pd
import yaml
from numpy import long
from pyecharts import configure

from DataAnalyzer import DataAnalyzer, AppPerfDrawer, REPORTS_DIR

DATASETS_YML = 'datasets.yml'
configure(global_theme='roma')


def read_csv(header_text, filename):
    headers = header_text.split(',')
    df = pd.DataFrame(pd.read_csv(filename, header=-1))
    df.columns = headers
    df = df[df['totalcpu'] >= 0]
    df['totalupflow'] = df['totalupflow'] - df['totalupflow'].min()
    df['totaldownflow'] = df['totaldownflow'] - df['totaldownflow'].min()
    # print(filename, df.iloc[:,0].size)
    return df


def read_csv_files(header_text, folders_list):
    dfs_list = []
    for folder in folders_list:
        _df = read_csv(header_text, os.path.join(folder, 'uploadTotalToServer.txt'))
        # print(_df.iloc[:, 0].size)
        dfs_list.append(_df)
    return dfs_list


def read_time_from_logcat(folder, package_name, activity_name):
    time = 0.0
    if os.path.isdir(folder):
        for item in os.listdir(folder):
            if not item.endswith('launch.log'):
                continue
            with open(os.path.join(folder, item)) as file:
                lines = file.readlines()
                _pattern = 'Displayed {0}/{1}:\s+\+(\S+)ms'.format(package_name, activity_name)
                for line in lines:
                    groups = re.search(_pattern, line)
                    if groups:
                        time_str = groups.group(1)
                        print(time_str)
                        group2s = re.search('(\d+)s(\d+)', time_str)
                        if group2s:
                            time = int(group2s.group(1)) + long(group2s.group(2)) / 1000.0
                        else:
                            time = int(time_str)/1000.0
                            # print(time)
                            # break
    return round(time, 2)


class AndroidDataAnalyzer(DataAnalyzer):
    def __init__(self, config_file):
        super(AndroidDataAnalyzer, self).__init__(config_file)
        self.type = 'APK'

    def get_launch_time(self, folders, package_name, activity_name):
        starttimes = []
        for _folder in folders:
            starttimes.append(read_time_from_logcat(_folder, package_name, activity_name))
        # print(starttimes)
        return starttimes
    #
    # def _get_execution_info(self):
    #     return self.datasets_map.get('execution_info')
    #
    # def get_header_text(self):
    #     return self._get_execution_info().get('header_text')
    #
    # def get_package_name(self):
    #     return self._get_execution_info().get('package_name')
    #
    # def get_activity_name(self):
    #     return self._get_execution_info().get('activity_name')
    #
    # def get_app_label(self):
    #     return self._get_execution_info().get('app_label')
    #
    # def get_counters_list(self):
    #     return self.datasets_map[COUNTERS]
    #
    # def get_test_types(self):
    #     return self.datasets_map.get('test_types')
    #
    # def get_test_type(self, index):
    #     return self.get_test_types()[index]
    #
    # def _get_translations(self):
    #     return self.datasets_map.get('translations')
    #
    # def translate(self, item):
    #     return self._get_translations().get(item)
    #
    # def get_models(self):
    #     return self.datasets_map[MODEL_SEQUENCE]
    #
    # def get_summary_values(self):
    #     return self.summary_values
    #
    # def _get_datasets(self):
    #     return self.datasets_map.get('datasets')
    #
    # def get_model_datasets(self, model):
    #     return self._get_datasets()[model]
    #
    # def get_duration(self):
    #     return self.datasets_map.get('duration')
    #
    # def get_scenario_duration(self, scenario):
    #     return self.get_duration().get(scenario)
    #
    # def get_radar_schema(self, counter):
    #     return self.datasets_map.get('radar_schema').get(counter)
    #
    def extract_dataset_from_raw_files(self, original_folders):
        # 获取数据集
        original_datasets = read_csv_files(self.get_header_text(), original_folders)
        return original_datasets
    #
    # def get_data_paths(self, model, scenario, test_type):
    #     scenarioes_map = self.get_model_datasets(model)
    #     # 选择初始数据集序号
    #     original_folders_idx = scenarioes_map[scenario][test_type]
    #     # 获取数据集目录
    #     original_folders = get_folders(original_folders_idx, scenario, test_type, model)
    #     return original_folders
    #
    # def calculate_duration_means(self, duration, model, scenario, test_type, y, counter):
    #     # 获取区间均值
    #     if scenario.startswith(STARTTIME):
    #         collect_duration_mean(self.summary_values, model, scenario, test_type, '1st_min', y, counter, 0, 60)
    #         collect_duration_mean(self.summary_values, model, scenario, test_type, 'rest', y, counter, 60, duration)
    #     else:
    #         collect_duration_mean(self.summary_values, model, scenario, test_type, 'whole', y, counter, 0, -1)
    #     # collect_duration_mean(self.summary_values, model, scenario, test_type, 'whole', y, counter, 0, -1)


if __name__ == '__main__':
    analyzer = AndroidDataAnalyzer(DATASETS_YML)
    drawer = AppPerfDrawer(analyzer)
    drawer.draw_lines_per_models()
    drawer.draw_summary_bars_per_scenarioes()
    # 顺序按照self.analyzer.get_models()
    # print(self.analyzer.get_models())
    '''1102.3, 1823.1, 1384.5 
1115.3, 1968.1, 1385.0 
1118.2, 1973.0, 1388.5 
1135.4, 2142.2, 1423.9 
1174.0, 2390.9, 1452.5 
0.50, 6.20, 2.50 
10.70, 384.30, 47.20 '''
    # clean_power_usage = [1102.3, 1823.1, 1384.5]
    clean_power_usage = [2362.04, 1426.48, 1844.44, 560.76, 1153.33, 1685.16]
    # installation_power_usage_0 = [1115.3, 1968.1, 1385.0]
    installation_power_usage_0 = [2380.79, 1465.16, 1879.45, 568.43, 1171.49, 1883.70]
    # installation_power_usage_1 = [1118.2, 1973.0, 1388.5]
    installation_power_usage_1 = [2464.19, 1480.8, 1900.88, 561.47, 1146.67, 1843.42]
    # runtime_power_usage_0 = [1135.4, 2142.2, 1423.9]
    runtime_power_usage_0 = [4345.58, 2625, 1535.17, 608.08, 1242.11, 2150.46]
    # runtime_power_usage_1 = [1174.0, 2390.9, 1452.5]
    runtime_power_usage_1 = [5196.51, 2608.86, 1550.23, 604.80, 1219.00, 2010.12]
    # app_power_usage_0 = [0.50, 6.20, 2.50]
    app_power_usage_0 = [329.65, 357, 38.8, 37, 34.9, 122.6]
    # app_power_usage_1 = [10.70, 384.30, 47.20]
    app_power_usage_1 = [375.55, 357.6, 39.7, 41.96, 23, 118.63]
    drawer.draw_silent_power_usage_bar(clean_power_usage, installation_power_usage_0, installation_power_usage_1)
    drawer.draw_active_power_usage_bar(runtime_power_usage_0, runtime_power_usage_1, app_power_usage_0,
                                       app_power_usage_1)

    clean_apk = [2.75, 2.75, 2.75, 2.75, 2.75, 2.75]
    integrated_apk = [5.30, 5.30, 5.30, 5.30, 5.30, 5.30]
    installed_app = [11.2, 11.87, 12.79, 7.22, 6.52, 11.87]
    installed_integrated_app = [14.4, 15.12, 16.2, 10.39, 9.52, 15.12]
    drawer.draw_occupation_bar(clean_apk, integrated_apk, installed_app, installed_integrated_app)

    clean_first_launch = [570.4, 784.2, 919.8, 629.8, 817.4, 720.6]
    clean_secondary_launch = [481.4, 603.6, 875.6, 400, 750.2, 571.8]
    integrated_first_launch = [768.4, 1126.8, 1151.2, 756.6, 1360.8, 1196.8]
    integrated_secondary_launch = [623.6, 935.5, 1125.8, 435.6, 1078.4, 615.7]
    drawer.draw_launchtime_first_bar2(clean_first_launch, integrated_first_launch)
    drawer.draw_launchtime_secondary_bar2(clean_secondary_launch, integrated_secondary_launch)
    # drawer.draw_power_usage_percent_pie(0, (
    #     app_power_usage_0,
    #     np.round(np.array(runtime_power_usage_0) - np.array(app_power_usage_0), decimals=2).tolist()))
    #    drawer.1
    # (1, (
    #        app_power_usage_1,
    #        np.round(np.array(runtime_power_usage_1) - np.array(app_power_usage_1), decimals=2).tolist()))
    print('Done!')