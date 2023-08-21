##!/bin/bash/python
# -*-coding:utf-8-*-
import os

import subprocess
import re
from collections import defaultdict
from xml.etree import ElementTree as ET
import getpass
import configparser
from datetime import datetime

def svnStat(svn_repo_path,start_date,end_date):


    # 获取提交列表
    svn_log_command = f'svn log -r {{{start_date}}}:{{{end_date}}} --xml {svn_repo_path}'
    svn_log_output = subprocess.check_output(svn_log_command, shell=True).decode()

    # 解析提交历史，统计每个人的代码行数
    author_lines = defaultdict(int)

    # 解析XML输出，获取每次提交的信息
    xml_root = ET.fromstring(svn_log_output)

    # 由于svn log -r {开始时间}:{结束时间}的原因，每次统计时会多一个在开始时间之前的最近提交的一次版本记录，所以在解析时需要根据date进行过滤
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    for logentry in xml_root.findall('.//logentry'):

        date_str = logentry.find("date").text
        # print(date_str)
        entry_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        if start_date_obj <= entry_date <= end_date_obj:
            # 修改作者
            author = logentry.find('author').text.strip()
            # 版本
            revision = logentry.get('revision')
            print("涉及版本：",revision)
            # 这里定义两个数组，一个统计+号为开头的内容行，一个统计-号为开头的内容行，因为由于svn diff的原因，有时候会出现+号和-号后面的内容一致，但是代码本质其实是没有修改的
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
                    line_content = line[1:].strip()  # 去掉开头的+
                    if not line_content or line_content.startswith("#"):
                        continue  # 过滤空行和注释行
                    if line_content not in delete_content_list:
                        add_content_list.append(line_content)
                        lines_added += 1
                    else:
                        delete_content_list.remove(line_content)
                elif line.startswith("-") and not line.startswith("---"):
                    line_content = line[1:].strip()  # 去掉开头的-
                    if not line_content or line_content.startswith("#"):
                        continue  # 过滤空行和注释行
                    if line_content not in add_content_list:
                        delete_content_list.append(line_content)
                    else:
                        lines_added -= 1

            author_lines[author] += max(lines_added, 0)

            # 输出统计结果
    print("代码工作量统计结果:")
    for author, lines in author_lines.items():
        print(f"{author}: {lines} 行")
    return author_lines
# 远程连接svn
def svnConnect(username,password,svn_url):
    try:
        cmd = f'svn log --username "{username}" --password "{password}" {svn_url} -r 1:HEAD --xml'
        svn_log_output = subprocess.check_output(cmd, shell=True,stderr=subprocess.PIPE, encoding="utf-8")
        print("连接成功！")
        return svn_log_output

    except subprocess.CalledProcessError as e:
        cmd_safe = re.sub(r'--password ".*"', '--password "******"', cmd)
        print(f"ErrorCommand: {cmd_safe}")
        return None

# 把获取到的日志文件以xml格式写入log
def write_log_tofile(svn_log_output,start_date, end_date):
    if not svn_log_output:
        return
    log_filename = f"{start_date}~{end_date}.log"
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log_file.write(svn_log_output)

    print("写入",log_filename,"成功")
    return log_file

# 读取配置文件config.ini
def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

# 把统计结果写入txt文件里
def write_svn_stat(author_lines,start_date,end_date):
    output_folder = f"svn代码统计_{start_date}_{end_date}"
    os.makedirs(output_folder,exist_ok = True)
    output_filename = os.path.join(output_folder,"代码量统计.txt")

    with open(output_filename,"w",encoding='utf-8') as output_file:
        output_file.write("代码工作量统计结果：\n")
        for author, lines in author_lines.items():
            output_file.write(f"{author}: {lines} 行\n")
    print("统计结果已保存！")

# def filter_zsandkb():



if __name__ == '__main__':
    # svn_repo_path = 'svn://svn.svnbucket.com/lpcccc10086/project1/trunk'
    config = get_config()
    start_date = config.get("svn","start_date")#开始时间
    end_date = config.get("svn","end_date")#结束时间
    admin_username = config.get("svn","username")#svn管理员账户
    admin_password = config.get("svn","password")#svn管理员密码

    while True:
        svn_username = input("请输入svn账号：")
        svn_password = getpass.getpass("请输入svn密码：")
        if svn_username != admin_username or svn_password != admin_password:
            print("账户或密码错误，请重新输入！")
            continue
        print("登录成功!")
        break

    while True:
        svn_repo_path = input("请输入仓库路径：")
        # 这里加入一个检索url就更好了,
        log_output = svnConnect(svn_username, svn_password, svn_repo_path)
        # print(log_output)
        if not log_output:
            print("url错误")
            continue
        print("仓库路径为：", svn_repo_path)
        # 写日志文件
        #write_log_tofile(log_output,start_date,end_date)
        # 获取每人代码工作量
        author_lines = svnStat(svn_repo_path, start_date, end_date)
        # 写入txt文件
        write_svn_stat(author_lines,start_date,end_date)

        break





















