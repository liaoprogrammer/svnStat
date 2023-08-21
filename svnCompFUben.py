#!/bin/bash/python
# -*-coding:utf-8-*-
from datetime import datetime

import os

import subprocess
import re
from collections import defaultdict
from xml.etree import ElementTree as ET

svn_repo_path = 'svn://svn.svnbucket.com/lpcccc10086/project1/trunk'
start_date = '2023-08-18'
end_date = '2023-08-19'


# 获取提交列表
svn_log_command = f'svn log -r {{{start_date}}}:{{{end_date}}} --xml {svn_repo_path}'
svn_log_output = subprocess.check_output(svn_log_command, shell=True).decode()
print(svn_log_output)
# 解析提交历史，统计每个人的代码行数
author_lines = defaultdict(int)

# 解析XML输出，获取每次提交的信息
xml_root = ET.fromstring(svn_log_output)
# 由于svn log -r {开始时间}:{结束时间}的原因，每次统计时会多一个在开始时间之前的最近提交的一次版本记录，所以在解析时需要根据date进行过滤
start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

for logentry in xml_root.findall('.//logentry'):
    #过滤不在时间段内的date
    date_str = logentry.find("date").text
    print(date_str)
    entry_date = datetime.strptime(date_str,'%Y-%m-%dT%H:%M:%S.%fZ')
    if start_date_obj <= entry_date <= end_date_obj:
        author = logentry.find('author').text.strip()
        revision = logentry.get('revision')
        # +号为开头的代码行
        add_content_list = []
        delete_content_list = []
        # 获取每次提交的代码修改
        svn_diff_command = f'svn diff -c {revision} {svn_repo_path}'
        svn_diff_output = subprocess.check_output(svn_diff_command, shell=True).decode()

        # 解析svn diff输出，记录每次修改的内容
        diff_lines = svn_diff_output.strip().split('\n')

        lines_added = 0  # 每版修改的代码行计数

        for line in diff_lines:

            if line.startswith('+') and not line.startswith('+++'):
                line_content = line[1:]  # 去掉开头的+
                if len(line_content) == 0 or line_content.startswith("#"):
                    continue
                if line_content not in delete_content_list:
                    add_content_list.append(line_content)
                    lines_added += 1
                else:
                    delete_content_list.remove(line_content)
            elif line.startswith("-") and not line.startswith("---"):
                line_content = line[1:]
                if len(line_content) == 0 or line_content.startswith("#"):
                    continue
                if line_content not in add_content_list:
                    delete_content_list.append(line_content)
                else:
                    lines_added -= 1

        print("计数：", lines_added)
        author_lines[author] += max(lines_added, 0)



def filter(line):

    return


# 输出统计结果
print("代码工作量统计结果:")
for author, lines in author_lines.items():
    print(f"{author}: {lines} 行")






















