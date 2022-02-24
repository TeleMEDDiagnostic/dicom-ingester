#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import urllib3
import json
import io
import os
import threading
import numpy
import pydicom
import xml.etree.ElementTree as ET
import uuid
import time
import stat
import subprocess
import shutil as SHT
import glob

def restoreDicomFile(obj, filePath, folderToCheck, dcmFile):
    print(filePath)
    try:
        result = glob.glob(folderToCheck + "/" + "*." + dcmFile)
        if os.path.isfile(result[0]):
            head, tail = os.path.split(result[0])
            SHT.move(result[0], obj["incomingFolder"] + "/" + tail)
        if not os.path.isfile(result[0]):
            os.remove(filePath)
    except FileNotFoundError:
        print("Restore file failed : " + dcmFile)
   

def checkProcessedFolder(obj, file):

    try:
        path = obj['folderForFolderToCheck'] + "/" + file
        if os.path.isfile(path):
            file1 = open(path, 'r')
            line = file1.readline()
            file1.close()
            print(line)
            head_tail = os.path.split(line)
            imageFile = head_tail[1]
            head_tail_01 = os.path.split(head_tail[0])
            session = head_tail_01[1]
            head_tail_02 = os.path.split(head_tail_01[0])
            testid = head_tail_02[1]
            head_tail_03 = os.path.split(head_tail_02[0])
            pid = head_tail_03[1]
            print(head_tail)
            processEcho = obj['processedEchoFolder'] + "/" + pid + "/" + testid
            restoreDicomFile(obj, path, processEcho, imageFile)
    except FileNotFoundError:
        print("Parsing file content failed,  it may not match folder structure : " + path)


def getEmptyFolderList(obj):
    print("")
    emptyFolderlist = obj['folderForFolderToCheck']
    arr = os.listdir(emptyFolderlist)
    for file in arr:
        checkProcessedFolder(obj, file)

def init():
    obj = {}
    ingesterPath = os.path.dirname(os.path.realpath(__file__))
    currentPath = os.getcwd()
    try:
        with open(os.path.join(ingesterPath, "config.json"), "r") as cfg:
            obj = json.load(cfg)
            cfg.close()
        getEmptyFolderList(obj)
            


    except FileNotFoundError:
        print("File config.json not found, creating one with default output path: " + currentPath )
       
if __name__ == "__main__":
    import sys
    init()
        