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


import parsers.xmlTools as EX
import parsers.imageParser as ip
import parsers.waveforParser as wf
import parsers.reportParser as sr


def parser(dataSet, obj, root):
  
    modality = pydicom.tag.Tag(0x0008,0x0060)

    patientID = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)
    studyID = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020, 0x000d)).value)
    seriesID = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020, 0x000e)).value)
    instanceID = EX.toStr(dataSet.get(pydicom.tag.Tag(0x008, 0x0018)).value)
    patientDirectory = os.path.join(obj['folderForPatients'], patientID, studyID, seriesID, instanceID)
    patientDirectoryForSync = os.path.join(obj['folderForFTPSynch'], patientID, studyID, seriesID)
    folderForImporter = os.path.join(obj['folderForImporter'], patientID, studyID)    
    folderForTemplate = os.path.join(obj['folderForTemplate'], "EmptyReport.json")
    if not os.path.exists(patientDirectory):
        os.makedirs(patientDirectory)
    if not os.path.exists(patientDirectoryForSync):   
        os.makedirs(patientDirectoryForSync)
    if not os.path.exists(folderForImporter): 
        os.makedirs(folderForImporter)
        SHT.copy2(folderForTemplate, folderForImporter + "/" + "report.json")

    # ECG
    if EX.toStr(dataSet.get(modality).value) == "ECG":
        waveformSequence = 0
        waveformAnnotationDE = dataSet.get(pydicom.tag.Tag(0x0040, 0xb020))

        for elm in dataSet.iterall():
            # Finding waveformSequencem tag(0x5400, 0x0100)
            if elm.tag.group == pydicom.tag.Tag(0x5400, 0x0100).group and elm.tag.element == pydicom.tag.Tag(0x5400, 0x0100).element:
                waveformSequence = elm.value[0]
                break

        if waveformSequence != 0 and waveformAnnotationDE is not None:
            wf.waveformParser(waveformSequence, waveformAnnotationDE, root)
        else:
            print("The file doesn't have a waveform or a waveform annotation")

    # Ultrasound
    elif EX.toStr(dataSet.get(modality).value) in ["US", "IVUS", ]:
        #TODO(Josue) The way I check if \xff\xc3 is in PixelData should consider \xff\xda. Right now it doesn't (it works though)
        print(dataSet.get(pydicom.tag.Tag(0x0028, 0x0004)).value)
        if ((dataSet.get(pydicom.tag.Tag(0x0028, 0x0004)).value == "RGB" and b'\xff\xc3' in dataSet.PixelData) or dataSet.get(pydicom.tag.Tag(0x0028, 0x0004)).value == "MONOCHROME2" ) and EX.toStr(dataSet.get(modality).value) != "SR":
            oldDcm = "old" + str(time.time()) + ".dcm" 
            ljpeg = "ljpeg" + str(time.time()) + ".dcm"
            pydicom.write_file(oldDcm, dataSet, True)
            subprocess.run(["gdcmconv", "--raw", oldDcm, ljpeg])
            ljpegDataSet = pydicom.dcmread(ljpeg)
            ip.imageToPng(ljpegDataSet, obj)
            # subprocess.run(["rm", oldDcm])
            # subprocess.run(["rm", ljpeg])
            subprocess.run(["del", oldDcm], shell=True)
            subprocess.run(["del", ljpeg], shell=True)

        else:
            ip.imageToPng(dataSet, obj)

    elif EX.toStr(dataSet.get(modality).value) == "SR":
        sr.extractReport(dataSet, obj)

    else:
        print("Modality not implemented")

    """ End of individual sections """

    print("Processed: Patient - " + patientID + ", Test - " + studyID + ", Instance - " + instanceID)


def addPatientAndTestToXML(dataSet):
    root = ET.Element("Main")

    """
        Patient information section
    """
    #print("\n*** Patient Info Section ***")
    patientFieldTuple = ('PatientID',       # PatientID
                        'PatientName',      # PatientName
                        'PatientDOB',       # PatientBirthDate
                        'PatientGender',    # PatientSex
                        'PatientEthnic',    # EthnicGroup
                        'PatientWeight',    # PatientWeight
                        'PatientHeight')    # PatientSize

    patientTagTuple = (pydicom.tag.Tag(0x0010,0x0020),    # PatientID
                        pydicom.tag.Tag(0x0010,0x0010),   # PatientName
                        pydicom.tag.Tag(0x0010,0x0030),   # PatientBirthDate
                        pydicom.tag.Tag(0x0010,0x0040),   # PatientSex
                        pydicom.tag.Tag(0x0010,0x2160),   # EthnicGroup
                        pydicom.tag.Tag(0x0010,0x1030),   # PatientWeight
                        pydicom.tag.Tag(0x0010,0x1020))   # PatientSize
    # PaceMaker is missing!
    pt = ET.SubElement(root, "Patient")

    EX.insertTupleInXML(patientFieldTuple, patientTagTuple, dataSet, pt)

    """
        Device information section
    """
    #print("\n*** Device Information Section ***")
    deviceFieldTuple = ('DeviceName',           # ManufacturerModelName
                        'DeviceModel',          # SoftwareVersion
                        'DeviceSerialNumber',   # DeviceSerialNumber
                        'VendorName',           # Manufacturer
                        'OperatorName',
                        'Accession')         # Operator Name           
    
    deviceTagTuple = (pydicom.tag.Tag(0x0008,0x1090),   # ManufacturerModelName
                        pydicom.tag.Tag(0x0018,0x1020), # SoftwareVersion
                        pydicom.tag.Tag(0x0018,0x1000), # DeviceSerialNumber
                        pydicom.tag.Tag(0x0008,0x0070), # Manufacturer
                        pydicom.tag.Tag(0x0008,0x1070),
                        pydicom.tag.Tag(0x0008,0x0050)) 

    ts = ET.SubElement(root, "Test")
    EX.insertTupleInXML(deviceFieldTuple, deviceTagTuple, dataSet, ts)

    """
        Test information section
    """
    #print("\n*** Test Information Section ***")
    testFieldTuple = ('TestType',      # Modality
                    'TestDescription', # StudyDescription
                    'TestDate',        # StudyDate
                    'TestTime',        # StudyTime
                    'TestUID')         # Study Instance UID        

    testTagTuple = (pydicom.tag.Tag(0x0008,0x0060),     # Modality
                    pydicom.tag.Tag(0x0008,0x1030),     # StudyDescription
                    pydicom.tag.Tag(0x0008,0x0020),     # StudyDate
                    pydicom.tag.Tag(0x0008,0x0030),     # StudyTime
                    pydicom.tag.Tag(0x0020,0x000D))     # Study Instance UID    

    EX.insertTupleInXML(testFieldTuple, testTagTuple, dataSet, ts)

    return root


def isValidDICOMfile(dicomPath):
    try:
        dataSet = pydicom.dcmread(dicomPath)

    except pydicom.errors.InvalidDicomError:
        print("Dicom file '" + dicomPath + "' is missing metadata information")

    except FileNotFoundError:
        print("File '" + dicomPath + "' not found")

    else:
        return dataSet

def getTestsFromPACS(patientID, obj):
    http = urllib3.PoolManager()

    param = {"PatientID": patientID}
    headerForQuery = urllib3.make_headers(
        {"Accept": "application/json"}, basic_auth="ostep:OSTEP"
    )
    headerForRetrieve = urllib3.make_headers(
        {
            "Accept": "multipart/related",
            "type": "application/dicom",
            "transfer-syntax": "1.2.840.10008.1.2.4.51",
        },
        basic_auth="ostep:OSTEP",
    )

    serverURL = (
        obj["server"]["url"]
        + ":"
        + obj["server"]["port"]
        + obj["server"]["serviceEndpoint"]
    )
    print("Connecting to " + serverURL)

    historicalData = []
    try:
        query = http.request(
            "GET", serverURL + "instances", headers=headerForQuery, fields=param
        )
    except urllib3.exceptions.MaxRetryError:
        print("Connection rejected or timed out trying to connect")
    else:

        if query.status == 200:
            files = json.loads(query.data)

            for instance in files:
                request = http.request(
                    "GET",
                    serverURL
                    + "studies/"
                    + str(instance["0020000D"]["Value"][0])
                    + "/series/"
                    + str(instance["0020000E"]["Value"][0])
                    + "/instances/"
                    + str(instance["00080018"]["Value"][0]),
                    headers=headerForRetrieve,
                    decode_content=True,
                )

                # This is a wonky way of parsin DICOM files, it works but it should be revised
                dicomFile = request.data.split(b"\r\n\r\n")
                historicalData.append(pydicom.dcmread(io.BytesIO(dicomFile[1])))

        else:
            print("Error: " + str(query.status))

    return historicalData

def file_age_in_seconds(pathname):
    ttime = time.time() - os.stat(pathname)[stat.ST_MTIME]
    return ttime

def getPaths(path):
    paths = []

    if os.path.isfile(os.path.join(path, "DICOMDIR")):
      dicomdirFile = isValidDICOMfile(os.path.join(path, "DICOMDIR"))
      # change this to consider more than one study and more than one series
      instances = dicomdirFile.patient_records[0].children[0].children[0].children
      paths = [os.path.join(path, *instance.ReferencedFileID) for instance in instances]

    else:
        for root, dirs, files in os.walk(path):            
            ds = pydicom.dcmread(os.path.join(root, files[0]))
            patientID01 = EX.toStr(ds.get(pydicom.tag.Tag(0x0010, 0x0020)).value)
            for file in files:
                ds2 = pydicom.dcmread(os.path.join(root, file))
                patientIDCurrent = EX.toStr(ds2.get(pydicom.tag.Tag(0x0010, 0x0020)).value)
                if(patientID01 == patientIDCurrent):
                    if file_age_in_seconds(os.path.join(root, file)) > 30:
                        paths.append(os.path.join(root, file))
                   

    return paths

def getListOfFiles(path):
    paths = []
    
    for root, dirs, files in os.walk(path):            
        for file in files:
            fileName = os.path.join(root, file)
            if file_age_in_seconds(fileName) > 30:
                paths.append(os.path.join(root, file))
                    

    return paths


def processDataSets(chunk, obj, xml):
    threadList = []
    for dicomFile in chunk:
        dataSet = isValidDICOMfile(dicomFile)
        if dataSet is not None:
            t = threading.Thread(target=parser, args=(dataSet, obj, xml))
            t.start()
            threadList.append(t)

    for t in threadList:
        t.join()

def moveTestToFTPFolder(pFolder, tFolder, obj):
    try:
        dest = obj['folderForFTPSynch'] + "/" + pFolder + "/" + tFolder
        scre = obj['folderForPatients'] + "/" + pFolder + "/" + tFolder 

        directory_contents = os.listdir(scre)
        for item in directory_contents:
            sub_items = os.listdir(obj['folderForPatients'] + "/" + pFolder + "/" + tFolder + "/" + item)
            if(len(sub_items) > 0):
                for file in sub_items:
                    SHT.move(scre + "/" + item + "/"+file, dest + "/" + item)
                break


        #subprocess.run([scre + " " + dest], shell=True)
        
    except ValueError:
        print("move to FTP fialed ... !")




def initiateIngestion(dicomPath):

    # Validate 'config,json'
    obj = {}
    ingesterPath = os.path.dirname(os.path.realpath(__file__))
    currentPath = os.getcwd()
    try:
        with open(os.path.join(ingesterPath, "config.json"), "r") as cfg:
            obj = json.load(cfg)
            cfg.close()

            if not os.path.exists(obj["folderForXML"]):
                print("Path " + obj["folderForXML"] + " doesn't exist or is not accesible")
                obj["folderForXML"] = currentPath + "/DataIngestor"
                print("Using default path: " + obj["folderForXML"] + " for XML files")

            if not os.path.exists(obj["folderForPatients"]):
                print("Path " + obj["folderForPatients"] + " doesn't exist or is not accesible")
                obj["folderForPatients"] = currentPath + "/DataIngestor"
                print("Using default path: " + obj["folderForPatients"] + " for images and reports")
            if not os.path.exists(obj["folderForProcessed"]):
                print("Path " + obj["folderForProcessed"] + " doesn't exist or is not accesible")
                obj["folderForProcessed"] = currentPath + "/Processed"
                print("Using default path: " + obj["folderForProcessed"] + " for proccessed DICOM files")

            if not os.path.exists(obj["folderForImporter"]):
                print("Path " + obj["folderForImporter"] + " doesn't exist or is not accesible")
                obj["folderForImporter"] = currentPath + "/Processed"
                print("Using default path: " + obj["folderForImporter"] + " for report files to be use by the Importer")

          
                

            if not (0 < obj["scaleFactor"] < 1):
                print("The scale factor " + str(obj["scaleFactor"]) + " must be a value between 0 and 1. Resetting it to default: 0.5")
                obj["scaleFactor"] = 0.5


    except FileNotFoundError:
        print("File config.json not found, creating one with default output path: " + currentPath + "/DataIngestor")
        obj = {
            "folderForXML": currentPath + "/DataIngestor",
            "folderForPatients": currentPath + "/DataIngestor",
            "folderForProcessed": currentPath + "/Processed",
             "folderForImporter": currentPath + "/Importer",
             "folderForFTPSynch" : currentPath + "/EchoFTP",
             "folderForTemplate" : currentPath + "/Template",
            "server": {
                "url": "http://localhost",
                "port": "8042",
                "serviceEndpoint": "/dicom-web/",
            },
            "scaleFactor": 0.5,
        }
        with open(
            os.path.join(ingesterPath, "config.json"), "w"
        ) as fp:
            json.dump(obj, fp)
            fp.close()

    # Process dicomPath passed from CL
    xmlFile = 0
    patientID = 0
    historicalDataSets = []
    iuid = ""


    if os.path.isfile(dicomPath):
        dataSet = isValidDICOMfile(dicomPath)

        if dataSet is not None:
            xmlFile = addPatientAndTestToXML(dataSet)
            iuid = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020, 0x000d)).value)
            parser(dataSet, obj, xmlFile)
            patientID = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

    elif os.path.isdir(dicomPath) and len(os.listdir(dicomPath)) != 0:
        listOfPaths = getPaths(dicomPath)

        ds = pydicom.dcmread(listOfPaths[0])
        xmlFile = addPatientAndTestToXML(ds)
        iuid = EX.toStr(ds.get(pydicom.tag.Tag(0x0020, 0x000d)).value)
        patientID = EX.toStr(ds.get(pydicom.tag.Tag(0x0010, 0x0020)).value)
        studyID = EX.toStr(ds.get(pydicom.tag.Tag(0x0020, 0x000d)).value)
        seriesID = EX.toStr(ds.get(pydicom.tag.Tag(0x0020, 0x000e)).value)

        FILES_PER_CHUNK = 5

        #move folder
        if not os.path.exists(obj['folderForProcessed'] + "/" + patientID + "/" + iuid ):
          os.makedirs(obj['folderForProcessed'] + "/" + patientID + "/" + iuid )


        if FILES_PER_CHUNK > len(listOfPaths):
            for f in listOfPaths:
                parser(isValidDICOMfile(f), obj, xmlFile)
                head, tail = os.path.split(f)
                if(os.path.isfile(obj['folderForProcessed'] + "/" + patientID + "/" + iuid + "/" + tail)):
                    os.remove(obj['folderForProcessed'] + "/" + patientID + "/" + iuid + "/" + tail)
                    SHT.move(f, obj['folderForProcessed'] + "/" + patientID + "/" + iuid )
                    
                else:
                    SHT.move(f, obj['folderForProcessed'] + "/" + patientID + "/" + iuid )
           
                moveTestToFTPFolder(patientID, studyID,obj)

        else:
            chunks = numpy.array_split(listOfPaths, len(listOfPaths) / FILES_PER_CHUNK)

            for chunk in chunks:
                processDataSets(chunk, obj, xmlFile)
                for f in chunk:
                    head, tail = os.path.split(f)
                    if(os.path.isfile(obj['folderForProcessed'] + "/" + patientID + "/" + iuid + "/" + tail)):
                        os.remove(obj['folderForProcessed'] + "/" + patientID + "/" + iuid + "/" + tail)
                        SHT.move(f, obj['folderForProcessed'] + "/" + patientID + "/" + iuid )
                        
                    else:
                        SHT.move(f, obj['folderForProcessed'] + "/" + patientID + "/" + iuid )
                        
                moveTestToFTPFolder(patientID, studyID,obj)

    else:
      print("There was an error processing the provided folder\n")
      print("Folder provided may be empty")
      exit(1)
    
    if patientID != 0:
      processDataSets(historicalDataSets, obj, xmlFile)        
            
      tree = ET.ElementTree(xmlFile)
      if not os.path.exists(obj['folderForXML']):
          os.makedirs(obj['folderForXML'])

     

      testFolder = obj['folderForXML'] + "/" + patientID + "/" + iuid 

      if not os.path.exists(testFolder):
        os.makedirs(testFolder)

      uuidForPatient = str(uuid.uuid4())

      uuidForPatient = iuid.replace('.','_');
      tree.write(testFolder + "/" + uuidForPatient + ".xml", xml_declaration = True, encoding = 'utf-8')
      dest = obj['folderForFTPSynch'] + "/" + patientID + "/" + iuid  + "/" + uuidForPatient + ".xml"
      scre = obj['folderForPatients'] + "/" + patientID + "/" + iuid + "/" + uuidForPatient + ".xml"
      SHT.move(scre, dest)

    listOfPaths = getListOfFiles(dicomPath)

    if(len(listOfPaths) > 0):
        initiateIngestion(dicomPath)
    


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sys.exit("Format: python3 input.dcm")
    else:
        if(len(getListOfFiles(sys.argv[1])) > 0):
            initiateIngestion(sys.argv[1])
