# -*- coding: utf-8 -*-

import pandas as pd
from numpy import *
import numpy as np
from pyecharts import Line, Page, Radar, Bar, configure, Pie
import os
import re
import yaml

STARTTIME = 'starttime'
MODEL_SEQUENCE = 'model_sequence'
COUNTERS = 'counters'
DATASETS_YML = 'datasets.yml'
REPORTS_DIR = 'reports'
configure(global_theme='roma')


def read_csv(header_text, filename):
    headers = header_text.split(',')
    df = pd.DataFrame(pd.read_csv(filename, header=-1))
    df.columns = headers
    df = df[df['totalcpu'] >= 0]
    df['totalupflow'] = df['totalupflow'] - df['totalupflow'].min()
    df['totaldownflow'] = df['totaldownflow'] - df['totaldownflow'].min()
    return df


def read_csv_files(header_text, folders_list):
    dfs_list = []
    for folder in folders_list:
        _df = read_csv(header_text, os.path.join(folder, 'uploadTotalToServer.txt'))
        # print(_df.iloc[:, 0].size)
        dfs_list.append(_df)
    return dfs_list


def get_iterations_mean(counter_name, dfs_list, start=0, end=-1):
    counter_values_list = []
    for df in dfs_list:
        counter_values = df[counter_name].T.values[start:end]
        counter_values_list.append(counter_values)

    y = np.round(np.vstack(counter_values_list).mean(0), decimals=2)
    return y


def get_folders(folder_nums, scenario, test_type, base_path='.'):
    selected_folders = []
    for item in folder_nums:
        item = os.path.join(base_path, test_type, scenario, str(item))
        if os.path.exists(item):
            selected_folders.append(item)
    if len(selected_folders) == 0:
        # print(u'没有找到合适数据集目录')
        # exit(1)
        pass
    return selected_folders


def read_time_from_logcat(folder, package_name, activity_name):
    time = 0.0
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
                    group2s = re.search('(\d+)s(\d+)', time_str)
                    if group2s:
                        time = int(group2s.group(1)) + long(group2s.group(2)) / 1000.0
                        # print(time)
                        # break
    return round(time, 2)


def draw_line_graph(title, x, y0, y1, width=1200, height=600):
    global line
    line = Line(title, title_pos='center', width=width, height=height)
    # line.use_theme('roma')
    line.add(
        u"集成SDK",
        x,
        y1.tolist(),
        is_fill=True,
        line_opacity=0.2,
        area_opacity=0.4,
        is_smooth=True,
        # is_more_utils=True,
        # is_datazoom_show=True,
        legend_top='bottom',
        mark_point=['max'],
        mark_line=['average'],
    )
    # print(y.tolist())
    line.add(
        u"未集成SDK",
        x,
        y0.tolist(),
        is_fill=True,
        area_opacity=0.3,
        legend_top='bottom',
        mark_point=['max'],
        mark_line=['average'],
        is_smooth=True
    )
    return line


def get_launch_time(folders, package_name, activity_name):
    starttimes = []
    for _folder in folders:
        starttimes.append(read_time_from_logcat(_folder, package_name, activity_name))
    return starttimes


def page_render(page, filename):
    page.render(filename)


def collect_duration_mean(collect_values, model, scenario, test_type, duration_txt, df, counter, start=0, end=-1):
    _title = "{0}_{1}_{2}_{3}".format(model, scenario, test_type, duration_txt)
    if _title not in collect_values:
        collect_values[_title] = {}
    collect_values[_title][counter] = np.round(df[start:end].mean(), decimals=2)


class DataAnalyzer(object):
    def __init__(self, config_file=DATASETS_YML):
        self.datasets_map = yaml.load(open(config_file))
        self.summary_values = {}
        if not os.path.isdir(REPORTS_DIR):
            os.mkdir(REPORTS_DIR)

    def _get_execution_info(self):
        return self.datasets_map.get('execution_info')

    def get_header_text(self):
        return self._get_execution_info().get('header_text')

    def get_package_name(self):
        return self._get_execution_info().get('package_name')

    def get_activity_name(self):
        return self._get_execution_info().get('activity_name')

    def get_app_label(self):
        return self._get_execution_info().get('app_label')

    def get_counters_list(self):
        return self.datasets_map[COUNTERS]

    def get_test_types(self):
        return self.datasets_map.get('test_types')

    def get_test_type(self, index):
        return self.get_test_types()[index]

    def _get_translations(self):
        return self.datasets_map.get('translations')

    def translate(self, item):
        return self._get_translations().get(item)

    def get_models(self):
        return self.datasets_map[MODEL_SEQUENCE]

    def get_summary_values(self):
        return self.summary_values

    def _get_datasets(self):
        return self.datasets_map.get('datasets')

    def get_model_datasets(self, model):
        return self._get_datasets()[model]

    def get_duration(self):
        return self.datasets_map.get('duration')

    def get_scenario_duration(self, scenario):
        return self.get_duration().get(scenario)

    def get_radar_schema(self, counter):
        return self.datasets_map.get('radar_schema').get(counter)

    def extract_dataset_from_raw_files(self, original_folders):
        # 获取数据集
        original_datasets = read_csv_files(self.get_header_text(), original_folders)
        return original_datasets

    def get_data_paths(self, model, scenario, test_type):
        scenarioes_map = self.get_model_datasets(model)
        # 选择初始数据集序号
        original_folders_idx = scenarioes_map[scenario][test_type]
        # 获取数据集目录
        original_folders = get_folders(original_folders_idx, scenario, test_type, model)
        return original_folders

    def calculate_duration_means(self, duration, model, scenario, test_type, y, counter):
        # 获取区间均值
        if scenario.startswith(STARTTIME):
            collect_duration_mean(self.summary_values, model, scenario, test_type, '1st_min', y, counter, 0, 60)
            collect_duration_mean(self.summary_values, model, scenario, test_type, 'rest', y, counter, 60, duration)
        else:
            collect_duration_mean(self.summary_values, model, scenario, test_type, 'whole', y, counter, 0, -1)


class AppPerfDrawer(object):
    def __init__(self, analyzer):
        self.analyzer = analyzer
        pass

    def draw_lines_per_models(self):
        for model in self.analyzer.get_models():
            self.draw_lines_per_scenarioes(model)

    def draw_lines_per_scenarioes(self, model):
        scenarioes_map = self.analyzer.get_model_datasets(model)
        for scenario in scenarioes_map:
            page = Page()

            # 读取原始数据
            original_folders = self.analyzer.get_data_paths(model, scenario, self.analyzer.get_test_type(0))
            integrated_folders = self.analyzer.get_data_paths(model, scenario, self.analyzer.get_test_type(1))
            original_datasets = self.analyzer.extract_dataset_from_raw_files(original_folders)
            integrated_datasets = self.analyzer.extract_dataset_from_raw_files(integrated_folders)

            if len(original_datasets) == 0 or len(integrated_datasets) == 0:
                continue

            # 初始化性能均值表
            original_means = []
            integrated_means = []

            # 对选定的性能参数逐一绘制总体情况对比折线图
            for counter in self.analyzer.get_counters_list():
                # 读多轮测试数据并计算平均值
                duration = self.analyzer.get_scenario_duration(scenario)
                y = get_iterations_mean(counter, original_datasets, 0, duration)
                yy = get_iterations_mean(counter, integrated_datasets, 0, duration)
                x = range(0, len(y))

                # 绘制指定设备，指定场景，指定性能指标的折线图
                line = draw_line_graph(u"APP运行时-%s" % self.analyzer.translate(counter), x, y, yy)
                page.add_chart(line)

                # 将性能指标均值汇总
                integrated_means.append(np.round(yy.mean(), decimals=2))
                original_means.append(np.round(y.mean(), decimals=2))

                # 计算区间性能指标均值
                self.analyzer.calculate_duration_means(duration, model, scenario, self.analyzer.get_test_type(0), y,
                                                       counter)
                self.analyzer.calculate_duration_means(duration, model, scenario, self.analyzer.get_test_type(1), yy,
                                                       counter)

            # 绘制指定设备，指定场景下各性能指标汇总图
            radar = self.draw_radar_per_scenario(model, integrated_folders, integrated_means, original_folders,
                                                 original_means, scenario)
            page.add_chart(radar)

            # 生成指定设备，指定场景的性能页面
            page_render(page, os.path.join(REPORTS_DIR, "{0}_{1}.html".format(model, scenario)))

    def draw_radar_per_scenario(self, model, integrated_folders, integrated_means, original_folders, original_means,
                                scenario):
        # 绘制汇总体雷达图
        title = u'性能指标对比汇总'
        schema = []
        for counter in self.analyzer.get_counters_list():
            counter_txt = self.analyzer.translate(counter)
            schema.append((counter_txt, self.analyzer.get_radar_schema(counter)))
        if scenario.startswith(STARTTIME):
            counter_txt = self.analyzer.translate(STARTTIME)
            schema.append((counter_txt, self.analyzer.get_radar_schema(STARTTIME)))
            # 获取启动时间时间
            original_launch = np.array(get_launch_time(original_folders, self.analyzer.get_package_name(),
                                                       self.analyzer.get_activity_name()))
            integrated_launch = np.array(get_launch_time(integrated_folders, self.analyzer.get_package_name(),
                                                         self.analyzer.get_activity_name()))
            # 计算启动均值并汇总
            original_means.append(original_launch.mean())
            integrated_means.append(integrated_launch.mean())
            collect_duration_mean(self.analyzer.summary_values, model, scenario, self.analyzer.get_test_type(0),
                                  'launch',
                                  np.array(original_launch), STARTTIME)
            collect_duration_mean(self.analyzer.summary_values, model, scenario, self.analyzer.get_test_type(1),
                                  'launch',
                                  np.array(integrated_launch), STARTTIME)
        v0 = [np.round(np.array(original_means), decimals=2).tolist()]
        v1 = [np.round(np.array(integrated_means), decimals=2).tolist()]
        radar = Radar(title, title_pos='center')
        # radar.use_theme('roma')
        radar.config(schema)
        radar.add(self.analyzer.translate(self.analyzer.get_test_type(1)), v1, legend_top='bottom',
                  is_area_show=False)
        radar.add(self.analyzer.translate(self.analyzer.get_test_type(0)), v0, legend_top='bottom',
                  item_color="#4e79a7", is_splitline=True, is_axisline_show=True, is_more_utils=False)
        return radar

    def draw_summary_bars_per_scenarioes(self):
        counters_list = self.analyzer.get_counters_list()
        counters_list.append(STARTTIME)
        for scenario in self.analyzer.get_duration():
            page = Page()
            self.draw_summary_bars_per_scenario(page, scenario, counters_list)

    def draw_summary_bars_per_scenario(self, page, scenario, counters_list):
        for counter in counters_list:
            if counter == STARTTIME:
                ratio = 0.5
            else:
                ratio = 1
            bar = Bar(u'%s-%s' % (self.analyzer.translate(scenario), self.analyzer.translate(counter)),
                      title_pos='center', width=1200 * ratio, height=600 * ratio)
            _summary_map = {}
            for model in self.analyzer.get_models():
                for test_type in self.analyzer.get_test_types():
                    if test_type not in _summary_map:
                        _summary_map[test_type] = []
                        attr = []
                    if scenario.startswith(STARTTIME):
                        subfixes = ['1st_min', 'rest', 'launch']
                    else:
                        subfixes = ['whole']
                    for subfix in subfixes:
                        summary_title = "{0}_{1}_{2}_{3}".format(model, scenario, test_type, subfix)
                        if summary_title in self.analyzer.summary_values and counter in self.analyzer.summary_values[
                            summary_title]:
                            if test_type not in _summary_map:
                                _summary_map[test_type] = []
                            _summary_map[test_type].append(self.analyzer.summary_values[summary_title][counter])
                            y_axis = u"%s-%s" % (model, self.analyzer.translate(subfix))
                            if y_axis not in attr:
                                attr.append(y_axis)
            for test_type in _summary_map:
                bar.add(self.analyzer.translate(test_type), attr, _summary_map[test_type], legend_top='bottom',
                        is_label_show=True)
            page.add_chart(bar)
        page_render(page, os.path.join(REPORTS_DIR, "summary_{0}.html".format(scenario)))

    def draw_silent_power_usage_bar(self, v1, v2, v3):
        bar = Bar(u"各静态场景下手机功耗(J)", title_pos='center', width=1200, height=600)
        bar.add(u"未安装", self.analyzer.get_models(), v1, legend_top='bottom', is_label_show=True)
        bar.add(u"安装未集成SDK包", self.analyzer.get_models(), v2, legend_top='bottom', is_label_show=True)
        bar.add(u"安装集成SDK包", self.analyzer.get_models(), v3, legend_top='bottom', is_label_show=True)
        bar.render(os.path.join(REPORTS_DIR, 'silent_power_usage.html'))

    def draw_active_power_usage_bar(self, v1, v2, v3, v4):
        bar = Bar(u"运行App时的手机功耗(J)", title_pos='center', width=800, height=450)
        bar.add(u"未集成SDK时总功耗", self.analyzer.get_models(), v1, legend_top='bottom', is_label_show=True)
        bar.add(u"集成SDK时总功耗", self.analyzer.get_models(), v2, legend_top='bottom', is_label_show=True)
        bar.add(u"未集成SDK的APP功耗", self.analyzer.get_models(), v3, legend_top='bottom', is_label_show=True)
        bar.add(u"集成SDK的APP功耗", self.analyzer.get_models(), v4, legend_top='bottom', is_label_show=True)
        bar.render(os.path.join(REPORTS_DIR, 'active_power_usage.html'))

    def create_pie(self, vs, index, model, test_type):
        attr = [self.analyzer.get_app_label(), u'其它']
        v1 = []
        for _v in vs:
            v1.append(_v[index])
        pie = Pie(u'%s-%s-%s功耗占比' % (model, self.analyzer.get_app_label(), self.analyzer.translate(test_type)),
                  title_pos='center', width=600, height=400)
        pie.add(str(index), attr, v1, is_label_show=True, legend_top='bottom')
        return pie

    def draw_power_usage_percent_pie(self, flag, vs):
        test_type = self.analyzer.get_test_type(flag)
        page = Page(u'App运行时功耗占比饼图')
        models = self.analyzer.get_models()
        pie0 = self.create_pie(vs, 0, models[0], test_type)
        page.add_chart(pie0)
        pie1 = self.create_pie(vs, 1, models[1], test_type)
        page.add_chart(pie1)
        pie2 = self.create_pie(vs, 2, models[2], test_type)
        page.add_chart(pie2)
        if len(models) > 3:
            pie3 = self.create_pie(vs, 3, models[3], test_type)
            page.add_chart(pie3)
        page.render(os.path.join(REPORTS_DIR, 'power_usage_percent_{0}.html').format(test_type))


if __name__ == '__main__':
    analyzer = DataAnalyzer()
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
    clean_power_usage = [1102.3, 1823.1, 1384.5]
    installation_power_usage_0 = [1115.3, 1968.1, 1385.0]
    installation_power_usage_1 = [1118.2, 1973.0, 1388.5]
    runtime_power_usage_0 = [1135.4, 2142.2, 1423.9]
    runtime_power_usage_1 = [1174.0, 2390.9, 1452.5]
    app_power_usage_0 = [0.50, 6.20, 2.50]
    app_power_usage_1 = [10.70, 384.30, 47.20]
    drawer.draw_silent_power_usage_bar(clean_power_usage, installation_power_usage_0, installation_power_usage_1)
    drawer.draw_active_power_usage_bar(runtime_power_usage_0, runtime_power_usage_1, app_power_usage_0,
                                       app_power_usage_1)
    drawer.draw_power_usage_percent_pie(0, (
        app_power_usage_0,
        np.round(np.array(runtime_power_usage_0) - np.array(app_power_usage_0), decimals=2).tolist()))
    drawer.draw_power_usage_percent_pie(1, (
        app_power_usage_1,
        np.round(np.array(runtime_power_usage_1) - np.array(app_power_usage_1), decimals=2).tolist()))
    print('Done!')
