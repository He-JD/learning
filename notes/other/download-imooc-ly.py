# coding:utf-8
# !/usr/bin/python3
import time
import urllib
import json
import os
import sys
from urllib import request

'''
python 3.x
雷云-慕课网付费视频下载脚本
注意，水平有限，有些文件不能完全下载，需要手动下载

download-imooc-ly.py为下载脚本
paths.json 为需要下载的文件夹路径配置，具体搜索雷云 https://www.leiyun.org/sf/8a9f0eb75aced5731b91fc109c9aba44.html-》查看网页Element->搜索sfVm.tools获取
down_error.log 下载出错日志
'''

# 文件下载存放的基础目录和项目全局变量
global_list = {
    "baseLocalDirPath": "/Users/caojx/Downloads/test",
    "videoProjectName": ""
}


# 下载进度显示回调函数，count当前块的编号，block_size每次传输的块大小，total_size网页文件总大小
def callBackScheduleInfo(count, block_size, total_size):
    # 进度的百分占比
    prog = float(count * block_size) / float(total_size) * 100.0
    if int(prog) > 100:
        raise RuntimeError("下载进度异常 " + str(prog))
    sys.stdout.write("\r%d%%" % prog + ' complete ')
    sys.stdout.flush()


# 发送Get请求
def doGet(getUrl):
    print("Get请求URL:" + getUrl)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
    }
    req = request.Request(getUrl, None, headers)
    res = request.urlopen(req, timeout=10000000)
    result = res.read()
    res.close()
    print("响应内容" + str(result))
    return json.loads(result)


# 获取文件夹中的文件列表
def folderHandle(path):
    getUrl = "https://www.leiyun.org/share/folderAction.php?list=" + path + "&hash=8a9f0eb75aced5731b91fc109c9aba44&referrer="
    res = doGet(getUrl)
    print(res)
    if res['erron'] != '0':
        print(res['msg'])
    else:
        return res['data']


# 递归文件夹下载文件
def download(path):
    res = folderHandle(path)
    for item in res:
        path = item['path']
        fileName = item['server_filename']
        # 如果是文件夹，递归文件夹
        if item['isdir'] == 1:
            global_list["baseLocalDirPath"] = global_list["baseLocalDirPath"] + "/" + fileName + "/"
            download(path)
            # 上一级别目录下载完成后，获取当前目录的父目录
            absolutePath = os.path.abspath(global_list["baseLocalDirPath"])
            global_list["baseLocalDirPath"] = os.path.dirname(absolutePath)
        else:
            # 下载文件
            downLoadFileURL = "https://www.leiyun.org/share/folderAction.php?down=" + path + "&folderDown=1&hash=8a9f0eb75aced5731b91fc109c9aba44"
            filePath = global_list["baseLocalDirPath"] + "/" + fileName
            try:
                downloadFile(downLoadFileURL, filePath)
            except Exception as e:
                print("开始重试下载 " + filePath)
                count = 0
                while (count < 3):
                    count = count + 1
                    print("开始第" + str(count) + "次重试下载 " + filePath)
                    try:
                        downloadFile(downLoadFileURL, filePath)
                        time.sleep(2)  # 休眠2秒
                        print("重试下载成功 " + filePath)
                        break
                    except Exception as e:
                        time.sleep(2)  # 休眠2秒
                        print("重试下载失败 " + filePath)
                        continue
                if count >= 3:
                    print("重试次数超过" + str(count) + "次，请改用手工下载 " + filePath)


# 下载具体的文件
def downloadFile(url, filePath):
    # 下载出错日志
    downErrorLog = open('down_error_' + global_list["videoProjectName"] + '.log', 'a+')

    isFileExists = os.path.exists(filePath)
    if isFileExists:
        print("文件已存在 " + filePath)
        return

    # 上一级别目录下载完成后，获取当前目录的父目录
    absoluteFilePath = os.path.abspath(filePath)
    parentPath = os.path.dirname(absoluteFilePath)
    isExists = os.path.exists(parentPath)
    if not isExists:  # 文件夹不存在创建文件
        os.makedirs(parentPath)

    # 获取具体的文件下载地址
    res = doGet(url)
    if res['erron'] != "0":
        print(res['msg'])
    elif res['url'] != "":
        print("获取文件下载地址的请求URL：" + url)
        print("下载文件名：" + absoluteFilePath + " 文件下载URL: " + res['url'])
        try:
            # 下载文件
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent',
                                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(res['url'], absoluteFilePath, callBackScheduleInfo)
            time.sleep(2)  # 休眠2秒
        except Exception as e:
            print('str(Exception):\t', str(Exception))
            print('str(e):\t\t', str(e))
            print('repr(e):\t', repr(e))
            print(absoluteFilePath + " 文件下载出错")
            downErrorLog.write('\n下载出错文件: ' + absoluteFilePath + '  下载地址：' + res['url'])
            downErrorLog.flush()
            downErrorLog.close()
            raise RuntimeError("下载文件失败，请重试")
    elif res['msg'] == "该文件不存在":
        print("该文件路径不存在，可能是由于文件名或上级目录名称包含特殊字符导致.请尝试修改后重试！")
    elif res['msg'] == "Illegal File":
        print("该文件已被和谐，无法生成下载!")
    else:
        print(res['msg'])


# 下载入口，paths.json 配置了目录入口json，具体搜索雷云 https://www.leiyun.org/sf/8a9f0eb75aced5731b91fc109c9aba44.html-》查看网页Element->搜索sfVm.tools获取
with open("/Users/caojx/code/learn-python/download-imooc/download-path.json", 'r', encoding='UTF-8') as f:
    print("downloading start")
    data = json.loads(f.read())
    for item in data:
        path = item['path']
        isDir = item['isdir']
        fileName = item['server_filename']
        global_list["videoProjectName"] = fileName
        global_list["baseLocalDirPath"] = "/Users/caojx/Downloads/test"
        if isDir == 1:  # 如果是目录，遍历目录
            global_list["baseLocalDirPath"] = global_list["baseLocalDirPath"] + "/" + fileName + "/"
            download(path)
        else:  # 如果是文件，直接下载
            downLoadFileURL = "https://www.leiyun.org/share/folderAction.php?down=" + path + "&folderDown=1&hash=8a9f0eb75aced5731b91fc109c9aba44"
            filePath = global_list["baseLocalDirPath"] + "/" + fileName
            isFileExists = os.path.exists(filePath)
            if isFileExists:
                print("文件已存在 " + filePath)
                continue
            downloadFile(downLoadFileURL, filePath)
    print("download finish")
