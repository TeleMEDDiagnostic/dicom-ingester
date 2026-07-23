#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import sys
import pydicom
import json
import os
import copy
import shutil as SHT
import xml.etree.ElementTree as ET


import parsers.xmlTools as EX
import tools.stringUtil as su
import re
from pathlib import Path

# Windows reserved filenames
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10))
}

srData2 = { "name" : "OBGYN Report",
        "report" : {
        "patient" : {},           
        "findingSite" : [],
        "userDefined" : [],
        
        }
    }
srData = { "name" : "Adult Echocardiography Report",
        "report" : {
        "patient" : {}, 
        "findingSite" : [],           
        "userDefined" : [],       
        }
    }
filterByInfo = [{}]

lastUserDefinedKey = ''
lastFound = {}
currentElement=""
currentHead=""

def sanitize_folder_name(folder_name):
    folder_name = Path(folder_name).name
    folder_name = re.sub(r'[<>:"/\\|?*]', "_", folder_name)
    folder_name = re.sub(r'[\x00-\x1F]', "", folder_name)
    folder_name = folder_name.rstrip(" .")

    if folder_name.upper() in _RESERVED_NAMES:
        folder_name = "_" + folder_name

    return folder_name or "NewFolder"

def processChildOBG_SR(dataSet, level, parent, elements, child, anonymizedPatientName):
    counter = 0
    spaces = "     " * level
    anonymizedPatientNameEx = anonymizedPatientName;

    for i in dataSet:
        #print(spaces + "Relationship type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa010)).value))
        #print(spaces + "Value Type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa040)).value))
        #print(i)

        #EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

        value = spaces;
        label = ""
        val = ""
        key= ""
        unit=""
        head=""
       
       

        if i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "CONTAINER":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xA043)).value) > 0:
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xA043)).value[0]
                head = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "TEXT":
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            unit = ""
           # head = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            if(parent == "Label"):
                labelKey = val;


        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "PNAME":
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            #value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val += EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa123)).value)
            #key = EX.toStr(i.get(pydicom.tag.Tag(0x0008, 0x0104)).value)


        # TODO(Josue) this one can have more than one, fix this
        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "NUM":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa300)).value) > 0:
                measuredValueDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa300)).value[0]
                measuredUnitDataSet = measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0x08ea)).value[0]
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]  
                if conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)) is not None:           
                    value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) + " " + EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                    key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                    val = EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) 
                    unit = EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                #head = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "CODE":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa168)).value) > 0:
                conceptCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa168)).value[0]
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
                value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(conceptCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                val = EX.toStr(conceptCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                unit = ""
                #head = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "DATETIME":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa043)).value) > 0:
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
                value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa120)).value)
                key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                val = EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa120)).value)
                #head = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                unit = ""

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "DATE":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa043)).value) > 0:
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
                value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa121)).value)
                key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                val = EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa121)).value)
                #head = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                unit = ""

       
                #measuredValueDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa300)).value[0]
                # measuredUnitDataSet = measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0x08ea)).value[0]
                # conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]            
                # value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) + " " + .toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                # key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                # val = EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) 
                # unit = EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
        
        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "UIDREF":
            value += EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa124)).value)
        

        if head !='':
            global currentHead
            currentHead = head

        #parent = head
        #child = val               
        if val is not None:
            #print(value)
            global currentElement
            if head is not None and level == 0:
                parent = key
                child = val               
                currentElement = val
                srData2["report"]["findingSite"].append(createFindingSite(head))

        if val is not None:
            #print(value)
            if key == "Label"  and level == 2:
                parent = key
                label = val
                

        if key != "" and val != "" :
            fillSRDataOBG(key, val, unit, parent, child, level, label, currentHead, anonymizedPatientNameEx)
        
        
        contentSequence = i.get(pydicom.tag.Tag(0x0040, 0xa730))
       

        currentItem = value
        currentLevel = EX.toStr(level)
        print("parent_level " + parent )
        print("-------title " + head)
        print("-------level " + currentLevel + "; " +  " currentElement: " + currentItem )

        #print("\n" + spaces + "Child " + str(counter) + ", level " + str(level))
        if contentSequence is not None:
            #print(spaces + "Entering level ------------" + str(level + 1))    
            test13 = contentSequence.value        
            processChildOBG_SR(contentSequence.value, level + 1, parent, elements, child, anonymizedPatientNameEx)
        counter += 1
        elements[0] += 1


def processChild(dataSet, level, parent, elements, child, anonymizedPatientName):
    counter = 0
    spaces = "     " * level
    anonymizedPatientNameEx = anonymizedPatientName;

   

    for i in dataSet:
        #print(spaces + "Relationship type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa010)).value))
        #print(spaces + "Value Type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa040)).value))
        #print(i)

        #EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

        value = spaces;
        label = ""
        val = ""
        key= ""
        unit=""
        head=""
        
        if i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "CONTAINER":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xA043)).value) > 0:
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xA043)).value[0]
                head = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "TEXT":
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            unit = ""
            if(parent == "Label"):
                labelKey = val;


        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "PNAME":
            value += EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa123)).value)

        # TODO(Josue) this one can have more than one, fix this
        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "NUM":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa300)).value) > 0:
                measuredValueDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa300)).value[0]
                measuredUnitDataSet = measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0x08ea)).value[0]
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]    
                if conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)) is not None:       
                    value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) + " " + EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                    key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                    val = EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) 
                    unit = EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "CODE":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa168)).value) > 0:
                conceptCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa168)).value[0]
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
                value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(conceptCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                val = EX.toStr(conceptCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                unit = ""

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "DATETIME":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa043)).value) > 0:
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
                value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa120)).value)
                key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                val = EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa120)).value)
                unit = ""

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "DATE":
            if len(i.get(pydicom.tag.Tag(0x0040, 0xa043)).value) > 0:
                conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
                value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa121)).value)
                key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
                val = EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa121)).value)
                unit = ""
        # elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "CONTAINER":
        #     if len(i.get(pydicom.tag.Tag(0x0040, 0xA730)).value) > 0:
        #         measuredValueDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa300)).value[0]
        #         measuredUnitDataSet = measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0x08ea)).value[0]
        #         conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]            
        #         value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) + " " + EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
        #         key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
        #         val = EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) 
        #         unit = EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            
        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "UIDREF":
            value += EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa124)).value)


        if val is not None:
            #print(value)
            global currentElement
            if key == "Finding Site"  and level != 3:
                parent = key
                child = val               
                currentElement = val
                srData["report"]["findingSite"].append(createFindingSite(child))

           

        if val is not None:
            #print(value)
            if key == "Label"  and level == 2:
                parent = key
                label = val
                #srData["report"]["findingSite"].append(createFindingSite("userDefined"))
                            
            

        if key != "" and val != "" and (key != "Finding Site" or level == 3):
            fillSRData(key, val, unit, parent, child, level, label, anonymizedPatientNameEx)

        # if key != "" and val != "" and key != "Fetal Biometry" :
        #     fillSRData(key, val, unit, parent, child, level, label, anonymizedPatientNameEx)

        # if key != "" and val != "" and key != "Fetus Summary" :
        #     fillSRData(key, val, unit, parent, child, level, label, anonymizedPatientNameEx)


        

        contentSequence = i.get(pydicom.tag.Tag(0x0040, 0xa730))
        # print("parent_level " + " " + parent )
        # print("-------title " + head)
        # print("-------child " + child + " currentElement: " + currentElement + " Unit " + unit)
        #print("\n" + spaces + "Child " + str(counter) + ", level " + str(level))
        currentItem = value
        currentLevel = EX.toStr(level)
        # print("parent_level " + parent )
        # print("-------title " + head)
        # print("-------level " + currentLevel + "; " +  " currentElement: " + currentItem )
        if contentSequence is not None:
            #print(spaces + "Entering level ------------" + str(level + 1))            
            processChild(contentSequence.value, level + 1, parent, elements, child, anonymizedPatientNameEx)
            #print(spaces + "Exiting level ------------" + str(level + 1))            
        counter += 1
        elements[0] += 1

def makefolderForMe(folderName):
    try:
        os.makedirs(folderName)
    except FileExistsError:
        print("folder already created by another thread ..!")

# def makefolderForMe(folder_name):
#     safe_folder = sanitize_folder_name(folder_name)

#     try:
#         os.makedirs(safe_folder)
#     except FileExistsError as ex:
#         print("folder already created by another thread ..!")

    #return safe_folder

def rmtreeForMe(folderName):
    try:
        SHT.rmtree(folderName)
    except FileExistsError:
        print("folder already remtree by another thread ..!")

def removeForMe(folderName):
    try:
        os.remove(folderName)
    except FileExistsError:
        print("folder already removed by another thread ..!")


def chechIfAlreadyExist(data, key, value, unit):
    for item in data:
       
        if(item["Key"] == key and item["Value"] == value):
            return False
    return True

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def GetValueNumber(value, unit):
    valueNumber = ''
    if(is_number(value)):
        if(unit == 'mm'):
            value = float(value) / 10
            unit = 'cm'
        if(unit == 'mm2'):
            value = float(value) / 100
            unit = 'cm2'
        if(unit == 'mm3'):
            value = float(value) / 1000
            unit = 'cm3'
        if(unit == 'mm/s'):
            value = float(value) / 1000
            unit = 'm/s'
        if(unit != ''):    
            valueNumber = '{:.2f}'.format(float(value))
        else:
            valueNumber = value
    else:
        valueNumber = value    

    return valueNumber


def fillSRData(key, value, unit, parent, currentChild, level, label, anonymizedPatientName):
    obj = {}  

 
    if parent == "Finding Site":
        if level == 2:
            index = len( srData["report"]["findingSite"])

            index2 = len(srData["report"]["findingSite"][index -1]["measurements"])

            srData["report"]["findingSite"][index -1]["measurements"]
            valueNumber = ''
            if(is_number(value)):
                if(unit == 'mm'):
                    value = float(value) / 10
                    unit = 'cm'
                if(unit == 'mm2'):
                    value = float(value) / 100
                    unit = 'cm2'
                if(unit == 'mm3'):
                    value = float(value) / 1000
                    unit = 'cm3'
                if(unit == 'mm/s'):
                    value = float(value) / 1000
                    unit = 'm/s'
                valueNumber = '{:.2f}'.format(float(value))
            else:
                valueNumber = value    
            
            #key data should come from config and check if any matches 
            global lastFound;  
            if(currentElement == "Mitral Valve" and key == "Cardiovascular Orifice Area"):
                             
                lastFound = {"Key": key, "Value": valueNumber, "Unit": unit }
            #key data should come from config and check if any matches 
            if(currentElement == "Aortic Valve" and key == "Cardiovascular Orifice Area"):
                #global lastFound;               
                lastFound = {"Key": key, "Value": valueNumber, "Unit": unit }

            if(currentElement == "Left Ventricle" and key == "Left Ventricular Ejection Fraction"):
                #global lastFound;               
                lastFound = {"Key": key, "Value": valueNumber, "Unit": unit }
            if(currentElement == "Left Atrium" and key == "Left Atrium Systolic Volume Index"):
                #global lastFound;               
                lastFound = {"Key": key, "Value": valueNumber, "Unit": unit }

            # if(currentElement == "Pulmonic Valve" and key == "Peak Gradient"):
            #     #global lastFound;               
            #     lastFound = {"Key": key, "Value": valueNumber, "Unit": unit }

            #Left Atrium Systolic Volume Index
            res = chechIfAlreadyExist(srData["report"]["findingSite"][index -1]["measurements"], key.replace("'", ""), valueNumber, unit)
            if(res):
                if(unit != ""):
                    srData["report"]["findingSite"][index -1]["measurements"].append( {
                        "Key": key.replace("'", ""),
                        "Value": valueNumber,
                        "Unit": unit,
                        "Infos": []
                    })
                #print("-->" +key + ": " + value + " " + unit)
        if level == 3:

            index = len( srData["report"]["findingSite"])
            index2 = len(srData["report"]["findingSite"][index -1]["measurements"])

            #key data should come from config and check if any matches 
            # TDO generlize
            if(currentElement == "Mitral Valve" and key == "Measurement Method"  and value == "Area by Pressure Half-Time" and  lastFound != {}):               
                srData["report"]["userDefined"].append({"Key": "MVA PHT", "Value": lastFound["Value"], "Unit": lastFound["Unit"]})

            if(currentElement == "Aortic Valve" and key == "Measurement Method"  and value == "Continuity Equation by Velocity Time Integral" and  lastFound != {}):               
                srData["report"]["userDefined"].append({"Key": "AVA VTI", "Value": lastFound["Value"], "Unit": lastFound["Unit"]}) 

            if(currentElement == "Left Ventricle" and key == "Measurement Method" and value == "Method of Disks, Biplane" and  lastFound != {}):
                srData["report"]["userDefined"].append({"Key": "EF Biplane", "Value": lastFound["Value"], "Unit": lastFound["Unit"]}) 

            if(currentElement == "Left Atrium" and key == "Measurement Method" and value == "Method of Disks, Biplane" and  lastFound != {}):
                srData["report"]["userDefined"].append({"Key": "LAVI", "Value": lastFound["Value"], "Unit": lastFound["Unit"]}) 

            # if(currentElement == "Pulmonic Valve" and key == "Flow Direction" and value == "Antegrade Flow" and  lastFound != {}):
            #     srData["report"]["userDefined"].append({"Key": "PV maxPG", "Value": lastFound["Value"], "Unit": lastFound["Unit"]}) 

            lastFound  = {}

            if(index > 0 and index2 > 0):
                valueNumber = ''
                if(is_number(value)):
                    valueNumber = '{:.2f}'.format(float(value))
                else:
                    valueNumber = value           
                res = res = chechIfAlreadyExist(srData["report"]["findingSite"][index -1]["measurements"][index2-1]["Infos"], key.replace("'", ""), valueNumber, unit)
                if(res):
                    srData["report"]["findingSite"][index -1]["measurements"][index2-1]["Infos"].append({"Key": key.replace("'", ""), "Value": valueNumber})
                    


    if parent == "patient":
        key1 = key.replace(' ', '_')
        if((anonymizedPatientName == True) and (key1 == "Subject_Name")):
             obj[key1] = su.getMaskedString(value)
        else:
            obj[key1] = value
        srData["report"]["patient"] |= obj

    if parent == "Label":        
        if(key == 'Label'):
            #obj[key + value] = value
            #srData["report"]["userDefined"].append({"Key": key.replace("'", ""), "Value": value})
            global lastUserDefinedKey
            lastUserDefinedKey = value
        if(label == ''):
            #obj[key + value] = value
            if(unit == '' ):
                unit = 'no units'
           
            if(is_number(value) ):
                if(unit == 'mm'):
                    value = float(value) / 10
                    unit = 'cm'
                if(unit == 'mm2'):
                    value = float(value) / 100
                    unit = 'cm2'
                if(unit == 'mm3'):
                    value = float(value) / 1000
                    unit = 'cm3'
                if(unit == 'mm/s'):
                    value = float(value) / 10
                    unit = 'cm/s'
                valueNumber = '{:.2f}'.format(float(value))           
                srData["report"]["userDefined"].append({"Key": lastUserDefinedKey.replace("'", ""), "Value": '{:.2f}'.format(float(valueNumber)), "Unit": unit})
def fillHeadItemOBG(key, value, unit, parent,level, label, head): 
    obj = {}  
    if head != "":
        if level == 1 or level == 2:
            index = len( srData2["report"]["findingSite"])
            index2 = len(srData2["report"]["findingSite"][index -1]["measurements"])
            srData2["report"]["findingSite"][index -1]["measurements"]

            valueNumber = GetValueNumber(value, unit)

            res = chechIfAlreadyExist(srData2["report"]["findingSite"][index -1]["measurements"], key.replace("'", ""), valueNumber, unit)
            if(res):
                if(unit != ""):
                    srData2["report"]["findingSite"][index -1]["measurements"].append( {
                        "Key": key.replace("'", ""),
                        "Value": valueNumber,
                        "Unit": unit,
                        "Infos": []
                    })
                else: srData2["report"]["findingSite"][index -1]["measurements"].append( {
                        "Key": key.replace("'", ""),
                        "Value": valueNumber,
                        "Unit": "",
                        "Infos": []
                    })

        if level == 3 or level == 4:
            index = len( srData2["report"]["findingSite"])
            index2 = len(srData2["report"]["findingSite"][index-1]["measurements"])
            if(index > 0 and index2 > 0):
                valueNumber = ''
                if(is_number(value) and unit != ''):
                    valueNumber = '{:.2f}'.format(float(value))
                else:
                    valueNumber = value           
                res = chechIfAlreadyExist(srData2["report"]["findingSite"][index -1]["measurements"][index2-1]["Infos"], key.replace("'", ""), valueNumber, unit)
                if(res):
                    srData2["report"]["findingSite"][index -1]["measurements"][index2-1]["Infos"].append({"Key": key.replace("'", ""), "Value": valueNumber})
     
def fillSRDataOBG(key, value, unit, parent, currentChild, level, label, head, anonymizedPatientName):
    obj = {}  

    if head == "Observer Type":
       fillHeadItemOBG(key, value, unit, parent,level, label, head)
                    
    if head == "Summary":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Fetus Summary":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Fetus Biometry Ratios":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Fetal Biometry":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Biometry Group":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Fetal Cranium":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    
    if head == "Fetal Anatomy":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Fetal Doppler":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Doppler Group":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "Maternal Doppler":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)

    if head == "MVP":
        fillHeadItemOBG(key, value, unit, parent,level, label, head)
     
     
    if parent == "patient":
        key1 = key.replace(' ', '_')
        if((anonymizedPatientName == True) and (key1 == "Subject_Name")):
                obj[key1] = su.getMaskedString(value)
        else:
            obj[key1] = value
        srData2["report"]["patient"] |= obj
    
    if parent == "Label":        
        if(key == 'Label'):
            #obj[key + value] = value
            #srData["report"]["userDefined"].append({"Key": key.replace("'", ""), "Value": value})
            global lastUserDefinedKey
            lastUserDefinedKey = value
        if(label == ''):
            #obj[key + value] = value
            if(unit == '' ):
                unit = 'no units'
           
           
                valueNumber = GetValueNumber(value, unit)         
                srData2["report"]["userDefined"].append({"Key": lastUserDefinedKey.replace("'", ""), "Value": '{:.2f}'.format(float(valueNumber)), "Unit": unit})

def createFindingSite(Name):
    return { "Name": Name,
    "measurements": []
    }

def generateMeasurmentAvg(data):
    avgs = copy.deepcopy(data)
    index = 0;
    for item in data["report"]["findingSite"]:
        msAvgs = {
            "Name": item["Name"],
            "Avgs": []
        }

        print(item["Name"])
        prevKey = ""
        prevUnit = ""

        avgValue = 0
        keyCount = 0
        for ms in item["measurements"]:
            if(prevKey != ms["Key"]):
                if(keyCount > 0):
                    avgs["report"]["findingSite"][index]["measurements"].append( {
                        "Key": prevKey + " Avg",
                        "Value": avgValue/keyCount,
                        "Unit": prevUnit,
                        "Infos": [{"Key": "Calculated", "Value": "Average"}]
                    })
                    keyCount = 0
                    avgValue = 0
                prevKey = ms["Key"]
                prevUnit =  ms["Unit"]
                
            if(prevKey == ms["Key"]):
                keyCount += 1;
                avgValue += float(ms["Value"])

           
            
            print("       " + ms["Key"])
        #this should cover last index
        if(keyCount > 0):
                    avgs["report"]["findingSite"][index]["measurements"].append( {
                        "Key": prevKey + " Avg",
                        "Value": avgValue/keyCount,
                        "Unit": prevUnit,
                        "Infos": [{"Key": "Calculated", "Value": "Average"}]
                    })
        index += 1;

    return avgs;

def extractReportOBGYN(dataSet, obj):
    print("I'm extracting the OBGYN report")
    test = dataSet.get(pydicom.tag.Tag(0x0040, 0xa730))
    print(dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)))
    print(type(test))

    print(dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)))
        
    print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa040)))
    print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa043)).value)
    print(dataSet.get(pydicom.tag.Tag(0x0020, 0x0013)))
    print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa491)))
    print(dataSet.get(pydicom.tag.Tag(0x0020, 0x0011)))
    print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa010)))
    print(dataSet.get(pydicom.tag.Tag(0x0400, 0x0510)))
    print(dataSet.get(pydicom.tag.Tag(0x0042, 0x0011)))
    print(dataSet.get(pydicom.tag.Tag(0x0040, 0xDB73)))
    print(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)))
    temp = dataSet.get(pydicom.tag.Tag(0x0008, 0x1030));

    conceptNameCodeDataSet = dataSet.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]

    if((dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)) is not None) and (dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value != '')):
        print(EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value))
        srData2["name"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value)
    else:
        srData2["name"] = "Growth"

    #adding more items to patient section
    #device name
    obj2 = {}    

   
    #Operator's name
    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0008,0x1070)) is not None:
        obj2["Operator"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008,0x1070)).value)
        srData2["report"]["patient"] |= obj2

    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0008,0x0050)) is not None:
        obj2["Accession"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008,0x0050)).value)
        srData2["report"]["patient"] |= obj2
    
    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0010,0x0010)) is not None:
        obj2["Patient Name"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010,0x0010)).value)
        srData2["report"]["patient"] |= obj2

    
    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0010,0x0040)) is not None:
        obj2["Patient Sex"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010,0x0040)).value)
        srData2["report"]["patient"] |= obj2

    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0010,0x0030)) is not None:
        obj2["Patient DOB"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010,0x0030)).value)
        srData2["report"]["patient"] |= obj2

    if dataSet.get(pydicom.tag.Tag(0x0008,0x1090)) is not None:
        obj2["Device"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008,0x1090)).value)
        srData2["report"]["patient"] |= obj2


    if dataSet.get(pydicom.tag.Tag(0x0018,0x1000)) is not None:
        obj2["Device SN"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0018,0x1000)).value)
        srData2["report"]["patient"] |= obj2

    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0018,0x0020)) is not None:
        obj2["Sofware Version"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0018,0x0020)).value)
        srData2["report"]["patient"] |= obj2

    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0020,0x000D)) is not None:
        obj2["Study Instance UID"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020,0x000D)).value)
        srData2["report"]["patient"] |= obj2
    
    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0020,0x000E)) is not None:
        obj2["Study Instance UID"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020,0x000E)).value)
        srData2["report"]["patient"] |= obj2

    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0020,0x0010)) is not None:
        obj2["Study ID"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020,0x0010)).value)
        srData2["report"]["patient"] |= obj2

    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0020,0x0011)) is not None:
        obj2["Series Number"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020,0x0011)).value)
        srData2["report"]["patient"] |= obj2

    obj2 = {}
    if dataSet.get(pydicom.tag.Tag(0x0020,0x0013)) is not None:
        obj2["Instance Number"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020,0x0013)).value)
        srData2["report"]["patient"] |= obj2


    if dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)) is not None:
        print("Length of content sequence " + str(len(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value)))
        print("Type of content sequence " + str(type(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value[0])))
    counter = 0
    numberOfElements = []
    numberOfElements.append(0)

    if dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)) is not None:
        test01 = dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value
        processChildOBG_SR(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value, 0, "patient", numberOfElements, "", obj["anonymizedPatientName"])
    
    print("Number of elements " + str(numberOfElements[0]))

    patientDir = obj["folderForPatients"] + "/" + EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

    iuid = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020, 0x000d)).value)

    testFolder =  patientDir + "/" + iuid

    if not os.path.exists(testFolder):
        makefolderForMe(testFolder)

    with open(testFolder + "/report.json", 'w') as fp:
        json.dump(srData2, fp)
        fp.close()

    reportFolder = obj["folderForImporter"] + "/" + EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value) + "/" + iuid
    reportPatientFolder = obj["folderForImporter"] + "/" + EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

    if os.path.isfile(reportFolder + "/report.json"):
        removeForMe(reportFolder + "/report.json")

    if os.path.exists(reportPatientFolder):
        rmtreeForMe(reportPatientFolder)

    if not os.path.exists(reportFolder):
        makefolderForMe(reportFolder)

    with open(reportFolder + "/report.json", 'w') as fp:
        json.dump(srData2, fp)
        fp.close()  

    destReport = obj['folderForFTPSynch'] + "/" + EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value) + "/" + iuid + "/report.json"
    srceReport = testFolder + "/report.json"

    SHT.move(srceReport, destReport)  

    #clearing data after one file is saved
    srData2["report"]["patient"] = {}
    srData2["report"]["findingSite"] = []
    srData2["report"]["userDefined"] = []
    srData2["report"]["fetalBiometry"] = []
    srData2["report"]["fetusSummary"] = [] 

def extractReport(dataSet, obj):
    print("I'm extracting the report")

    # Remove this when integrated with main since the checking will happen somewhere else
    test = dataSet.get(pydicom.tag.Tag(0x0040, 0xa730))
    print(dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)))
    print(type(test))
    if dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)).value == "SR":
        print(dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)))
        
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa040)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa043)).value)
        print(dataSet.get(pydicom.tag.Tag(0x0020, 0x0013)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa491)))
        print(dataSet.get(pydicom.tag.Tag(0x0020, 0x0011)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa010)))
        print(dataSet.get(pydicom.tag.Tag(0x0400, 0x0510)))
        print(dataSet.get(pydicom.tag.Tag(0x0042, 0x0011)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xDB73)))
        print(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)))


       

        conceptNameCodeDataSet = dataSet.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]

        #srData["name"] = EX.toStr(EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value))
       
        temp = dataSet.get(pydicom.tag.Tag(0x0008, 0x1030));

        if((dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)) is not None) and (dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value != '')):
            print(EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value))
            srData["name"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value)
        else:
            srData["name"] = "Adult Echo"
        
        #adding more items to patient section
        #device name
        obj2 = {}
        
        if dataSet.get(pydicom.tag.Tag(0x0008,0x1090)) is not None:
            obj2["Device"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008,0x1090)).value)
            srData["report"]["patient"] |= obj2
        #Operator's name
        obj2 = {}
        if dataSet.get(pydicom.tag.Tag(0x0008,0x1070)) is not None:
            obj2["Operator"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008,0x1070)).value)
            srData["report"]["patient"] |= obj2

        obj2 = {}
        if dataSet.get(pydicom.tag.Tag(0x0008,0x0050)) is not None:
            obj2["Accession"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008,0x0050)).value)
            srData["report"]["patient"] |= obj2



        if dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)) is not None:
            print("Length of content sequence " + str(len(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value)))
            print("Type of content sequence " + str(type(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value[0])))
        counter = 0
        numberOfElements = []
        numberOfElements.append(0)
        if dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)) is not None:
            processChild(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value, 0, "patient", numberOfElements, "", obj["anonymizedPatientName"])

        print("Number of elements " + str(numberOfElements[0]))
        
        patientDir = obj["folderForPatients"] + "/" +  sanitize_folder_name(EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value))

        # for item  in srData["report"]["findingSite"]:
        #     mes = list(dict.fromkeys(item["measurements"]))

        iuid = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020, 0x000d)).value)

        testFolder =  patientDir + "/" + iuid

        if not os.path.exists(testFolder):
            makefolderForMe(testFolder)
            #os.makedirs(testFolder)

        # srDataAvgs = generateMeasurmentAvg(srData);
        with open(testFolder + "/report.json", 'w') as fp:
            json.dump(srData, fp)
            fp.close()
        
        reportFolder = obj["folderForImporter"] + "/" + sanitize_folder_name(EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)) + "/" + iuid

        reportPatientFolder = obj["folderForImporter"] + "/" +  sanitize_folder_name(EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)) 
        if os.path.isfile(reportFolder + "/report.json"):
            removeForMe(reportFolder + "/report.json")
            #os.remove(reportFolder + "/report.json")
            
        if os.path.exists(reportPatientFolder):
            rmtreeForMe(reportPatientFolder)
            #SHT.rmtree(reportPatientFolder)


        if not os.path.exists(reportFolder):
            makefolderForMe(reportFolder)
            #os.makedirs(reportFolder)
        
        # create the report file to trigger importer action to import a new test


        with open(reportFolder + "/report.json", 'w') as fp:
            json.dump(srData, fp)
            fp.close()


        destReport = obj['folderForFTPSynch'] + "/" +  sanitize_folder_name(EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)) + "/" + iuid + "/report.json"
        srceReport = testFolder + "/report.json"
        # if os.path.isfile(reportFolder + "/report.json"):
        #      os.remove(destReport)
        SHT.move(srceReport, destReport)
        
        #clearing data after one file is saved
        srData["report"]["patient"] = {}
        srData["report"]["findingSite"] = []
        srData["report"]["userDefined"] = []  
        

        
        
        #print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa504)).value)
    else:
        print("This is not an SR dicom file")

if __name__ == '__main__':

    import sys

    if len(sys.argv) < 2:
        sys.exit("Format: python3 input.dcm")
    else:
        try:
            dataSet = pydicom.dcmread(sys.argv[1])

        except pydicom.errors.InvalidDicomError:
            print("Dicom file '" + sys.argv[1] + "' is missing metadata information")

        except FileNotFoundError:
            print("File '" + sys.argv[1] + "' not found")

        else:
            extractReport(dataSet)
