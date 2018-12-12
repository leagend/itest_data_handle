import commands
import os
import time


class PerfTest(object):
    def __init__(self, SN=None, package="", activity=""):
        if not SN:
            self.SN = SN
        else:
            self.SN = os.getenv("SN")
        self.TEST_TOOL = "iflytek.testTech.propertytool"
        if package == "":
            self.package = os.getenv("PACKAGE")
        else:
            self.package = package
        if activity == "":
            self.activity = os.getenv("ACTIVITY")
        else:
            self.activity = activity

    def pull_logcat(self, data_dir):
        ls_str = "adb -s {0} shell ls /sdcard/AndroidPropertyTool4/logcatTool/|grep -v logcat|tail -n 1".format(self.SN)
        status, output = commands.getstatusoutput(ls_str)
        output = output.strip()
        lines = None
        if status:
            print("Can not get logcatTool folder")
            exit(1)
        elif not output.endswith("No such file or directory"):
            lines = output.split("\n")
        pull_str = "adb -s {0} pull /sdcard/AndroidPropertyTool4/logcatTool/{1} {2}/logcat"
        for line in lines:
            line = line.strip()
            status, output = commands.getstatusoutput(pull_str.format(self.SN, line, data_dir))
            print(output)

    def start_external_logcat(self):
        status, output = commands.getstatusoutput("adb -s {0} logcat -c".format(self.SN))
        print(output)
        commands.getstatusoutput("adb -s {0} logcat -v time > launch.log &".format(self.SN))
        print(output)

    def clear_app_cache(self):
        commands.getstatusoutput("adb -s {0} shell pm clear {1}".format(self.SN, self.package))

    def launch_itest(self):
        commands.getstatusoutput(
            "adb -s {0} shell am start -W {1}/{1}.activity.BootActivity".format(self.SN, self.TEST_TOOL))

    def start_itest(self, tag, interval=1):
        commands.getstatusoutput(
            "adb -s {0} shell am broadcast -a SceneMarker --es markerValue {1}".format(self.SN, tag))
        commands.getstatusoutput("adb -s {0} shell am broadcast -a LogcatTool --es open true".format(self.SN))
        commands.getstatusoutput(
            "adb -s {0} shell am broadcast -a monitorStart --es monitor cpu,pss,upflow,downflow,battery,cputemp,fps "
            "--es pkg {1} --es interval {2}".format(self.SN, self.package, interval))
        commands.getstatusoutput("adb -s {0} shell am broadcast -a disableFloatWindow".format(self.SN))

    def stop_itest(self):
        commands.getstatusoutput("adb -s {0} shell am broadcast -a monitorFinish".format(self.SN))
        commands.getstatusoutput("adb -s {0} shell am broadcast -a LogcatTool --es open false".format(self.SN))
        commands.getstatusoutput("ps e|grep 'adb -s %s logcat'|grep -v grep|awk '{print $1}'|xargs kill -9" % self.SN)

    def pull_itest_data(self, data_dir):
        commands.getstatusoutput("adb -s {0} pull /sdcard/AndroidPropertyTool4/handTest {1}".format(self.SN, data_dir))
        commands.getstatusoutput("mv launch.log {0}/".format(data_dir))

    def launch_app(self):
        commands.getstatusoutput(
            "adb -s {0} shell am start -W {1}/{2}.activity.BootActivity".format(self.SN, self.package, self.activity))

    def stop_app(self):
        commands.getstatusoutput("adb -s {0} shell am force-stop ${1}".format(self.SN, self.package))

    def click_power_btn(self):
        commands.getstatusoutput("adb -s {0} shell input keyevent 26".format(self.SN))

    def test_launch(self, relaunch=False, wait_time=180, count=5):
        number = 1
        while number < count:
            result_dir = 'tmp_results/{0}'.format(number)
            self.start_external_logcat()
            if relaunch:
                self.clear_app_cache()
                time.sleep(5)
                tag = 'initial_{0}'.format(number)
            else:
                tag = 'secondary_{0}'.format(number)
            self.launch_itest()
            self.start_itest(tag)
            self.launch_app()
            time.sleep(wait_time)
            self.stop_itest()
            self.pull_itest_data(result_dir)
            self.pull_logcat(result_dir)
            self.stop_app()
            number += 1

    def test_polling(self, screen_on=True, wait_time=600, count=5):
        number = 1
        while number < count:
            result_dir = 'tmp_results/{0}'.format(number)
            self.start_external_logcat()
            self.launch_app()
            time.sleep(10)
            if not screen_on:
                tag = 'screen_off_{0}'.format(number)
            else:
                tag = 'screen_on_{0}'.format(number)
            self.launch_itest()
            self.start_itest(tag)
            self.launch_app()
            if not screen_on:
                self.click_power_btn()
            time.sleep(wait_time)
            self.stop_itest()
            self.pull_itest_data(result_dir)
            self.pull_logcat(result_dir)
            if not screen_on:
                self.click_power_btn()
            self.stop_app()
            number += 1
