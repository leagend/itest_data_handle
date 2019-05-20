# -*- coding: utf-8 -*-

from os.path import join, abspath
import re
import yaml
import os
import sys
import numpy as np
import pandas as pd
from ITestClient import ITestClient
import re

COMLUM_TOTAL = 'comlumTotal'
COMLUM = 'comlum'
APP_INFO = 'app_info'
DEVICE_INFO = 'device_info'
TIPS = 'tips'
string_map = {COMLUM_TOTAL: 'sys_property', COMLUM: 'app_property', TIPS: 'tips'}


def read_original_data(columns, csvfile, filterkey):
    df = pd.DataFrame(pd.read_csv(csvfile, header=-1))
    df.columns = columns
    df = df[df[filterkey] >= 0]
    df[columns[1:-1]] = df[columns[1:-1]].apply(pd.to_numeric)
    return df


def get_aggregation_data(df, columns, prefix):
    aggregations = {}
    for i in columns:
        if i == 'time':
            continue
        data_0 = {}
        data_0['count'] = df.count()[i]
        if data_0['count'] == 0:
            data_0['max'] = 0
            data_0['min'] = 0
            data_0['sum'] = 0
            data_0['avg'] = 0
        else:
            data_0['max'] = df.max()[i]
            data_0['min'] = df.min()[i]
            if i.endswith('flow'):
                data_0['sum'] = round(data_0['max'] - data_0['min'], 2)
                data_0['avg'] = round(data_0['sum'] / data_0['count'], 2)
            else:
                data_0['avg'] = round(df.mean()[i], 2)
                data_0['sum'] = round(df.sum()[i], 2)
        aggregations['{0}{1}'.format(prefix, i)] = data_0
    return aggregations


def get_aggregation_data_in_interval(df, columns, prefix, startindex, count):
    if count > 0:
        df2 = df[startindex: startindex + count]
        prefix = '{0}head_{1}_{2}_'.format(prefix, startindex, count)
    else:
        df2 = df[startindex: count]
        prefix = '{0}tail_{1}_{2}_'.format(prefix, startindex, -1)
    return get_aggregation_data(df2, columns, prefix)


class DataParser(object):
    def __init__(self):
        self.app_property = ''
        self.sys_property = ''
        self.json_data = {'code': 0, 'reason': '', 'status': 'ok', 'data': []}
        self.base_path = ''

    def _read_total_data(self, record_id):
        total_file = join(self.base_path, 'uploadTotalToServer.txt')
        if not os.path.exists(total_file):
            total_file = total_file.replace('.txt', '.csv')
        filter_key = 'totalcpu'
        prefix = 'avg_'
        id_prefix = 'test_record_id'
        return self._get_records_data(self.sys_property, filter_key, id_prefix, prefix, record_id, total_file)

    def _read_app_data(self, package_name):
        app_file = join(self.base_path, 'uploadToServer_{0}.txt'.format(package_name.replace('.', '_')))
        if not os.path.exists(app_file):
            app_file = app_file.replace('.txt', '.csv')
        filter_key = 'cpu'
        prefix = 'avg_'
        id_prefix = 'test_record_app_id'
        return self._get_records_data(self.app_property, filter_key, id_prefix, prefix, package_name, app_file)

    def _get_records_data(self, columns, filter_key, id_prefix, prefix, record_id, record_file):
        df = read_original_data(columns, record_file, filter_key)
        for i in ['upflow', 'downflow', 'totalupflow', 'totaldownflow']:
            if i in columns:
                df[i] = (df[i] - df.min()[i]).round(2)
        aggregations = get_aggregation_data(df, columns, prefix)
        aggregations2 = get_aggregation_data_in_interval(df, columns, prefix, 0, 60)
        aggregations.update(aggregations2)
        aggregations3 = get_aggregation_data_in_interval(df, columns, prefix, 60, -1)
        aggregations.update(aggregations3)
        # print aggregations
        return aggregations

    def _read_settings(self):
        file_path = abspath(join(self.base_path, 'uplaodSetting.txt'))
        json_data = {}
        for line in open(file_path, 'r').readlines():
            line = line.strip()
            m = re.search(r"(\S+?):([\s\S]+)", line)
            key_name = m.group(1)
            if key_name in string_map.keys():
                json_data[string_map[key_name]] = m.group(2)
            else:
                json_data[key_name] = yaml.load(m.group(2).replace("\/", "/"))
        self.sys_property = json_data['sys_property'].split(',')
        self.app_property = json_data['app_property'].split(',')

    def read_data(self, target_dir, app_id):
        self.base_path = os.path.abspath(target_dir)
        self._read_settings()
        aggregations1 = self._read_total_data(target_dir)
        # app_id = 'com.chinamworld.main'
        aggregations2 = self._read_app_data(app_id)

        return {'sys': aggregations1, 'app': aggregations2}

    def analysis_data(self, result_data, name, start=0, end=-1):
        data = {'fps': None}
        for i in self.app_property:
            if i == 'time':
                continue
            if start == 0 and end == -1:
                _title = 'avg_{0}'.format(i)
            elif start == 0:
                _title = 'avg_head_{0}_{1}_{2}'.format(start, end, i)
            else:
                _title = 'avg_tail_{0}_{1}_{2}'.format(start, end, i)
            if _title not in result_data.keys():
                print("not find _title {0} in result_data".format(_title))
            if _title.endswith('flow'):
                data[i] = result_data[_title]['sum']
            elif _title in result_data:
                data[i] = result_data[_title][name]
        # print("{target}: 1st minute,{cpu},{mem},{upflow},{downflow},{fps}".format(target=name.capitalize(), **data))
        return data

    def read_time_from_logcat(self, folder, activity_name):
        time = 0.0
        for item in os.listdir(folder):
            if not item.endswith('launch.log'):
                continue
            with open(join(folder, item)) as file:
                lines = file.readlines()
                _pattern = 'Displayed {0}/{1}:\s+\+(\S+)ms'.format(package_name, activity_name)
                for line in lines:
                    # if 'Displayed' in line:
                        # print(line)
                    groups = re.search(_pattern, line)
                    if groups:
                        time_str = groups.group(1)
                        group2s = re.search('(\d+)s(\d+)', time_str)
                        if group2s:
                            time = int(group2s.group(1)) + long(group2s.group(2))/1000.0
                            # print(time)
                            break
        return round(time, 3)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        folder_name = sys.argv[1]
    else:
        folder_name = r'D:\PycharmProjects\app-perf-scripts\btest\handTest'
    if not os.path.isdir(folder_name):
        print("Can not find the folder: {0}.".format(folder_name))
        exit(1)

    if 'PACKAGE' in os.environ:
        package_name = os.getenv('PACKAGE')
    else:
        package_name = 'com.sgcc.evs.echarge'
    if 'ACTIVITY' in os.environ:
        activity_name = os.getenv('ACTIVITY')
    else:
        activity_name = 'com.bitrice.evclub.ui.activity.WelcomeActivity'
    # print folder_name, app_id
    # irecord = DataParser()
    # results = irecord.read_data(folder_name, package_name)
    # result = results['app']
    interval_num = 60

    results = {}
    folder_name = os.path.abspath(folder_name)

    model_list = os.listdir(folder_name)

    for model in model_list:
        if os.path.isdir(os.path.join(folder_name, model)):
            modes = os.listdir(os.path.join(folder_name, model))
            for mode in modes:
                if mode not in ['integrated', 'original']:
                    continue
                results['{0}_{1}'.format(model, mode)] = {}
                scenarioes = os.listdir(os.path.join(folder_name, model, mode))
                for scenario in scenarioes:
                    if not os.path.isdir(os.path.join(folder_name, model, mode, scenario)):
                        continue
                    if scenario.startswith("starttime") or scenario.startswith("polling") or scenario.startswith(
                            "threats"):
                        executions = os.listdir(os.path.join(folder_name, model, mode, scenario))
                        exec_results = {}
                        for execution in executions:
                            if not os.path.isdir(os.path.join(folder_name, model, mode, scenario, execution)):
                                continue
                            try:
                                if int(execution) in range(1, 10, 1):
                                    _execution = os.path.join(folder_name, model, mode, scenario, execution)

                                    base_url = 'http://172.16.31.98:8090'
                                    creator = ITestClient(_execution)
                                    json_data = creator.get_json_data()
                                    json_data.update({'username': 'leagend', 'password': '123456'})
                                    zipped_file = creator.get_zip_file()
                                    uploaded = join(_execution, 'uploaded')
                                    if not os.path.isfile(uploaded) and creator.upload_result(base_url, zipped_file, json_data):
                                        with open(uploaded, 'a') as file:
                                            file.write('1')
                                    exec_result = {}
                                    _parser = DataParser()
                                    data_dict = _parser.read_data(_execution, package_name)['app']
                                    exec_result['0-59'] = _parser.analysis_data(data_dict, 'avg', 0, interval_num)
                                    exec_result['60+'] = _parser.analysis_data(data_dict, 'avg', interval_num, -1)
                                    exec_result['all'] = _parser.analysis_data(data_dict, 'avg')
                                    try:
                                        exec_result[activity_name] = _parser.read_time_from_logcat(_execution, activity_name)
                                    except:
                                        pass
                                    exec_results[execution] = exec_result
                            except:
                                pass
                        results['{0}_{1}'.format(model, mode)][scenario] = exec_results

                        for item in ['0-59', '60+', 'all']:
                            print('{0}_{1}_{2}: {3}'.format(model, mode, scenario, item))
                            _data0 = {}
                            _sum_value = {}
                            count = 0
                            columns = []
                            for _value in exec_results.values():
                                count += 1
                                if item not in _value:
                                    continue
                                try:
                                    for column in _value[item].keys():
                                        _tmp_value = _value[item][column]
                                        if column not in _data0:
                                            _data0[column] = []
                                            _sum_value[column] =0.0
                                        _data0[column].append(_tmp_value)
                                        if _tmp_value:
                                            _sum_value[column] += _tmp_value
                                except:
                                    print("error on item: {0}".format(item))
                                    pass
                            launch_str = 'startup_time'
                            for _value in exec_results.values():
                                _launch_time = _value[activity_name]
                                if launch_str not in _data0:
                                    _data0[launch_str] = []
                                    _sum_value[launch_str] =0.0
                                _data0[launch_str].append(_launch_time)
                                _sum_value[launch_str] += _launch_time

                            for column in _data0:
                                _data0[column].append(round(_sum_value[column]/count, 3))
                                output = '{0}, {1}'.format(column, _data0[column])

                                print(output.replace('[','').replace(']', ''))
                            print("\n")
