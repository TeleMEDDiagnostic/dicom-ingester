#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import pydicom
import numpy
import time
import json
import cv2
import numpngw
import os
import numpy as np
#import skvideo.io
import imageio.v3 as iio
import imageio
import random
import tools.stringUtil as su
import re
from pathlib import Path


# Windows reserved filenames
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10))
}

def sanitize_folder_name(folder_name):
    folder_name = Path(folder_name).name
    folder_name = re.sub(r'[<>:"/\\|?*]', "_", folder_name)
    folder_name = re.sub(r'[\x00-\x1F]', "", folder_name)
    folder_name = folder_name.rstrip(" .")

    if folder_name.upper() in _RESERVED_NAMES:
        folder_name = "_" + folder_name

    return folder_name or "NewFolder"

def regionFlags(element, reference):
  flags = []

  for position in range(len(reference)):
    ''' Create the mask to be used to isolate a specific flag
        Example: 
        numberOfBits = 3
        mask = sum([2 ** i for i in range(numberOfBits)])
        'mask' would hold the value 7, which is 0b111.
    '''
    mask = sum([2 ** i for i in range(reference[position]["numberOfBits"])])

    #  'mask & element' will give as the index of the item that we want from the array of values
    flags.append(reference[position]["flag"][element & mask])
    element = element >> reference[position]["numberOfBits"]

  return flags

def processImageRegion(imageRegion):
  ingesterPath = os.path.dirname(os.path.realpath(__file__))
  referenceTable = {"regions": {}}
  referencePixel = {}
  regionX1 = 0
  regionY1 = 0

  ir = {"boundingBox": {}}
  try:
    with open(os.path.join(ingesterPath, "normalizationTable.json") ,'r') as rf:
        referenceTable = json.load(rf)
        rf.close()
  except FileNotFoundError:
    print("normalizationTable.json is missing")
  
  for element in imageRegion:
    if element.keyword in referenceTable["regions"]:
      key = referenceTable["regions"][element.keyword]["key"]
      if "values" in referenceTable["regions"][element.keyword]:
        if element.keyword is "RegionFlags":
          '''
            NOTE(Josue): When processing flags, for 'priority' (bit 0):
              0 = Region pixels are high priority
              1 = Region pixels are low priority
              https://dicom.innolitics.com/ciods/us-multi-frame-image/us-region-calibration/00186011/00186016
          '''
          flags = regionFlags(element.value, referenceTable["regions"]["RegionFlags"]["values"])
          for position in range(len(referenceTable["regions"]["RegionFlags"]["values"])):
            ir[referenceTable["regions"]["RegionFlags"]["values"][position]["key"]] = flags[position]
        else:
          ir[key] = referenceTable["regions"][element.keyword]["values"][element.value]
      else:
        if element.keyword in ["RegionLocationMinX0", "RegionLocationMinY0", "RegionLocationMaxX1", "RegionLocationMaxY1"]:
          # We store RegionLocationMax{X1, Y1} to calculate width and height later
          if element.keyword is "RegionLocationMaxX1":
            regionX1 = element.value
          elif element.keyword is "RegionLocationMaxY1":
            regionY1 = element.value
          else:
            ir["boundingBox"][key] = element.value
        elif element.keyword in ["ReferencePixelX0", "ReferencePixelY0"]:
          referencePixel[key] = element.value
        else:
          ir[key] = element.value

    else:
      key = element.keyword
      ir[key] = element.value
    
    if bool(referencePixel):
      ir["reference"] = referencePixel

  # Calculate width and height
  ir["boundingBox"]["width"] = regionX1 - ir["boundingBox"]["x"]
  ir["boundingBox"]["height"] = regionY1 - ir["boundingBox"]["y"]

  return ir


def createTiledImage(arrayOfFrames, resolution, numberOfTiles):
    tiledImage = []
    dimensions = []
    extraTiles = 0

    oneSideLength = 1
    while numberOfTiles > (oneSideLength * oneSideLength):
        oneSideLength += 1


    # Check what dimensions are optimal for a good looking square shaped image
    if oneSideLength * (oneSideLength - 2) > numberOfTiles and oneSideLength * (oneSideLength - 2) - numberOfTiles < oneSideLength * (oneSideLength - 1) - numberOfTiles:
        dimensions, extraTiles = [oneSideLength, oneSideLength - 2], oneSideLength * (oneSideLength - 2) - numberOfTiles

    elif oneSideLength * (oneSideLength - 1) > numberOfTiles and oneSideLength * (oneSideLength - 1) - numberOfTiles < oneSideLength * oneSideLength - numberOfTiles:
        dimensions, extraTiles = [oneSideLength, oneSideLength - 1], oneSideLength * (oneSideLength - 1) - numberOfTiles

    else:
        dimensions, extraTiles = [oneSideLength, oneSideLength], oneSideLength * oneSideLength - numberOfTiles
    

    # Filling up the last row with empty thumbnails if needed
    for i in range(extraTiles):
        arrayOfFrames.append(numpy.zeros((resolution[0], resolution[1], 3), dtype=int))

    for y in range(dimensions[1]):
        for k in range(resolution[0]):
            row = numpy.array(arrayOfFrames[y * dimensions[0]][k])
            for x in range(1, dimensions[0]):
                row = numpy.concatenate((row, arrayOfFrames[y * dimensions[0] + x][k]), axis=0)

            tiledImage.append(row)

    return numpy.array(tiledImage, dtype = numpy.uint8)



def generateInfoFile(dicomInfo, folder, anonymizedPatientName, scaleFactor = 0):
    obj = {}
    print("Generating info file")
    for baseKey, baseValue in dicomInfo.items():
        obj[baseKey] = {}
        for key, val in baseValue.items():
            if val is not None:
              if isinstance(val, list):
                obj[baseKey][key] = val
              else:
                if isinstance(val, int) | isinstance(val, str):
                    obj[baseKey][key] = val
                else:
                    if(anonymizedPatientName == True):
                      if(key == "PatientName"):
                        obj[baseKey][key] = su.getMaskedString(EX.toStr(val.value))
                      else:
                        obj[baseKey][key] = EX.toStr(val.value)
                    else:
                      obj[baseKey][key] = EX.toStr(val.value)


    if scaleFactor != 0:
        obj["Image"]["scaledRows"] =  str(int(dicomInfo["Image"]["rows"].value * scaleFactor))
        obj["Image"]["scaledColumns"] =  str(int(dicomInfo["Image"]["columns"].value * scaleFactor))
    
    if dicomInfo["Image"]["numberOfFrames"] is not None and dicomInfo["Image"]["recommendedDisplayFrameRate"] is None:
        # default value arbitrarily set to 29
        obj["Image"]["recommendedDisplayFrameRate"] = "29"
    
    if dicomInfo["Image"]["samplesPerPixel"].value == 3:
      obj["Image"]["isColor"] = True
    else:
      obj["Image"]["isColor"] = False

    with open(folder + "/info.json", 'w') as fp:
        json.dump(obj, fp)
        fp.close()

def scaleImage(image, ratio):
    return cv2.resize(image, dsize=(int(ratio * len(image[0])), int(ratio * len(image))), interpolation = cv2.INTER_LINEAR)

def getIndex(comment):
  xy = 0
  if comment is not None:
      splited = EX.toStr(comment.value).split(':')
      for item in splited:
        print(item)
        if 'RowNumber' in item:
          rowSplited = item.split('=')
          xy +=  int(rowSplited[1])
        if 'ColNumber' in item:
          colSplited = item.split('=')
          xy += 10 * int(colSplited[1])
      return xy
  else:
      return random.randint(800, 999)

def getIndex(dataSet):
  xy = 0
  stage = 0
  tag = dataSet.get(pydicom.tag.Tag(0x0008,0x2120))
  if tag is not None:
    #numberOfStages =  dataSet.get(pydicom.tag.Tag(0x0008,0x2124)).value
    stageNumber =  returnElementNotNullReturnNum(dataSet.get(pydicom.tag.Tag(0x0008,0x2122)))
    viewNumber = returnElementNotNullReturnNum(dataSet.get(pydicom.tag.Tag(0x0008,0x2128)))
    acquisitionDateTime =  returnElementNotNullReturnNum(dataSet.get(pydicom.tag.Tag(0x0008,0x002A)))
    stageName =  returnElementNotNullReturnStr(dataSet.get(pydicom.tag.Tag(0x0008,0x2120))).upper()
     
    if stageName == "REST":
      stage = 1
    if stageName == "POST" or stageName == "PEAK":
      stage = 2
    if stageName == "RECOVERY":
      stage = 3 

    #xy = (numberOfStages * 1000) + (stageNumber * 100) + (viewNumber * 10) + stage

    if stageName == '-':
     return acquisitionDateTime

    xy = (viewNumber * 100) + (stageNumber * 10) + stage
    return xy
     
  else:
      return int(returnElementNotNullReturnNum(dataSet.get(pydicom.tag.Tag(0x0008,0x0033))))

def returnElementNotNull(elem):
  if elem is not None:
    return elem
  return EX.toStr('-')

def returnElementNotNullReturnNum(elem):
  if elem is not None:
    return elem.value
  return 0
def returnElementNotNullReturnNumInt(elem):
  if elem is not None:
    return int(elem.value)
  return 0
def returnElementNotNullReturnStr(elem):
  if elem is not None:
    return elem.value
  return EX.toStr('-')

COLOR_MAP = {
    "GRAY2RGB": cv2.COLOR_GRAY2RGB,
    "BGR2RGB": cv2.COLOR_BGR2RGB,
    "BGRA2RGB": cv2.COLOR_BGRA2RGB,
}

def safe_cvt(frame, colorPlate=None):
    if frame is None:
        return None
    

    frame = np.asarray(frame)

    # AUTO mode (recommended)
    if colorPlate is None or colorPlate == "AUTO":
        if frame.ndim == 2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

        if frame.ndim == 3:
            if frame.shape[2] == 1:
                return cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            if frame.shape[2] == 3:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if frame.shape[2] == 4:
                return cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

        raise ValueError(f"AUTO conversion failed for shape {frame.shape}")

    # Explicit mode
    if isinstance(colorPlate, str):
        if colorPlate not in COLOR_MAP:
            raise ValueError(f"Unsupported colorPlate '{colorPlate}'")

        required_channels = {
            "GRAY2RGB": 1,
            "BGR2RGB": 3,
            "BGRA2RGB": 4,
        }[colorPlate]

        if frame.ndim == 3 and frame.shape[2] != required_channels:
            raise ValueError(
                f"{colorPlate} requires {required_channels} channels, "
                f"got {frame.shape}"
            )

        if frame.ndim == 2 and required_channels != 1:
            raise ValueError(f"{colorPlate} requires multi-channel input")

        return cv2.cvtColor(frame, COLOR_MAP[colorPlate])

    raise TypeError("colorPlate must be a string or None")




def imageToPng(dataSet, obj):
    print("Processing Ultrasound Image")   
    dicomData = { "Patient" :
                        {"PatientName" : dataSet.get(pydicom.tag.Tag(0x0010, 0x0010)),                 
                        "PatientID" : dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)), 
                        "PatientDOB" : dataSet.get(pydicom.tag.Tag(0x0010, 0x0030)),
                        "PatientGender" : dataSet.get(pydicom.tag.Tag(0x0010, 0x0040)),
                        "PatientEthnic" : dataSet.get(pydicom.tag.Tag(0x0010, 0x2160)),
                        "PatientWeight" : dataSet.get(pydicom.tag.Tag(0x0010, 0x1030)),
                        "PatientHeight" : dataSet.get(pydicom.tag.Tag(0x0010, 0x1020))
                        },
                    "Device" :
                        {"DeviceName" : dataSet.get(pydicom.tag.Tag(0x0008, 0x1090)),
                        "DeviceModel" : dataSet.get(pydicom.tag.Tag(0x0018, 0x1020)),
                        "DeviceSerialNumber" : dataSet.get(pydicom.tag.Tag(0x0018, 0x1000)),
                        "VendorName" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0070))
                        },
                    "Test" :
                        {"TestModality" : dataSet.get(pydicom.tag.Tag(0x0008,0x0060)),
                        "TestDescription" : dataSet.get(pydicom.tag.Tag(0x0008,0x1030)),
                        "TestDate" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0020)),
                        "TestTime" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0030)),
                        "TimezoneOffset" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0201)),
                        "referringPhysician" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0090)),
                        "StudyInstanceUID" : dataSet.get(pydicom.tag.Tag(0x0020, 0x000d)),
                        "SeriesInstanceUID" : dataSet.get(pydicom.tag.Tag(0x0020, 0x000e)),
                        "SOPInstanceUID" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0018))
                        },
                    "Image" :
                        {"samplesPerPixel" : dataSet.get(pydicom.tag.Tag(0x0028, 0x0002)),
                        "rows" : dataSet.get(pydicom.tag.Tag(0x0028, 0x0010)),
                        "columns" : dataSet.get(pydicom.tag.Tag(0x0028, 0x0011)),
                        "bitsAllocated" : dataSet.get(pydicom.tag.Tag(0x0028, 0x0100)),
                        "compressionMethod" : dataSet.get(pydicom.tag.Tag(0x0028, 0x2114)),
                        "numberOfFrames" : dataSet.get(pydicom.tag.Tag(0x0028, 0x0008)),
                        "imageType" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0008)),
                        "recommendedDisplayFrameRate" : dataSet.get(pydicom.tag.Tag(0x0008, 0x2144)),    
                        "photometricInterpretation" : dataSet.get(pydicom.tag.Tag(0x0028, 0x0004)),
                        "pixelRepresentation" : dataSet.get(pydicom.tag.Tag(0x0028, 0x0103)),
                        "stageName" : returnElementNotNull(dataSet.get(pydicom.tag.Tag(0x0008, 0x2120))),
                        "viewName" : returnElementNotNull(dataSet.get(pydicom.tag.Tag(0x0008, 0x2127))),
                        "index" : getIndex(dataSet),
                        "comment" : returnElementNotNull(dataSet.get(pydicom.tag.Tag(0x0020, 0x4000))),
                        "Date" : dataSet.get(pydicom.tag.Tag(0x0008, 0x0023)),
                        "Time" : dataSet.get(pydicom.tag.Tag(0x0008,0x0033)),
                        "ElapsedTime" : returnElementNotNullReturnNumInt(dataSet.get(pydicom.tag.Tag(0x0008, 0x2130))),
                        "HeartRate" : returnElementNotNullReturnNumInt(dataSet.get(pydicom.tag.Tag(0x0018, 0x1088)))
                        }
                }

    imageRegionData = dataSet.get(pydicom.tag.Tag(0x0018,0x6011))
    regions = []
    if imageRegionData is not None:
      for imageRegion in imageRegionData.value:
        regions.append(processImageRegion(imageRegion))

    dicomData["Image"]["regions"] = regions
    patientDir = obj['folderForPatients'] + "/" + sanitize_folder_name( EX.toStr(dicomData["Patient"]["PatientID"].value)) + "/" + EX.toStr(dicomData["Test"]["StudyInstanceUID"].value) + "/" + EX.toStr(dicomData["Test"]["SeriesInstanceUID"].value) + "/" + EX.toStr(dicomData["Test"]["SOPInstanceUID"].value)
    if not os.path.exists(patientDir):
        os.makedirs(patientDir)

    #print(dataSet.get(pydicom.tag.Tag(0x0028, 0x0004)).value)
    colorPlate = 0;
   
    colorPlate = obj["singleFrame_colorPlate"];


    #print(colorPlate);


    # Single-frame
    if dicomData["Image"]["numberOfFrames"] is None:
        print("Single-frame")
        start = time.time()
        frame = dataSet.pixel_array

        if frame.ndim == 2 or frame.shape[-1] == 1:
          output = frame
        elif colorPlate != 0:
          output = safe_cvt(frame, colorPlate); #cv2.cvtColor(frame, colorPlate)
        else:
          output = frame

        cv2.imwrite(
          patientDir + "/image.png",
          output,
          [cv2.IMWRITE_PNG_COMPRESSION, 5]
        )


        print(time.time() - start)

        print("Done processing image")
        generateInfoFile(dicomData, patientDir, obj["anonymizedPatientName"])

    # Multi-frame
    else:
        
                 
        print("Multi-frame")
        print(len(dataSet.PixelData))
        newArray = []
        for i in range(dicomData["Image"]["numberOfFrames"].value):
            newArray.append(scaleImage(dataSet.pixel_array[i], obj['scaleFactor']))

        numpyFrames = numpy.array(newArray, dtype = numpy.uint8)
        
        if dicomData["Image"]["recommendedDisplayFrameRate"] is not None:
            delayInMl = 1000 / dicomData["Image"]["recommendedDisplayFrameRate"].value
        else:
            delayInMl = 50

        # generate preview     
  
        

        pixel_array = dataSet.pixel_array

        print("Complete DICOM pixel array shape:", pixel_array.shape)

        # Select one image from the DICOM pixel array.
        if pixel_array.ndim == 4:
            # Multi-frame RGB/RGBA.
            frame = pixel_array[0]

        elif pixel_array.ndim == 3:
            if pixel_array.shape[-1] in (3, 4):
                # Single-frame RGB/RGBA.
                frame = pixel_array
            else:
                # Multi-frame grayscale.
                frame = pixel_array[0]

        elif pixel_array.ndim == 2:
            # Single-frame grayscale.
            frame = pixel_array

        else:
            raise ValueError(
                "Unsupported DICOM pixel array shape: "
                + str(pixel_array.shape)
            )

        print("Thumbnail source frame shape:", frame.shape)

        if frame.ndim == 2:
            output = frame

        elif frame.ndim == 3 and frame.shape[-1] == 1:
            output = frame[:, :, 0]

        elif colorPlate != 0:
            output = safe_cvt(frame, colorPlate)

        else:
            output = frame

        print("Thumbnail output shape:", output.shape)

        thumbnail_path = patientDir + "/image.png"

        success = cv2.imwrite(
            thumbnail_path,
            output,
            [cv2.IMWRITE_PNG_COMPRESSION, 5]
        )

        if not success:
            raise RuntimeError(
                "OpenCV failed to create thumbnail: " + thumbnail_path
            )

        # Generate MP4.
        print("The delay is " + str(delayInMl))
        start = time.time()

       

        writer = imageio.get_writer(
          patientDir + "/image.mp4",
          fps=25,
          codec="libx264",
          pixelformat="yuv420p",
          macro_block_size=1,
          ffmpeg_params=[
              "-crf", "15",
              "-preset", "veryslow"
          ])

        colorPlate = obj["multiFrame_colorPlate"]

        
        for frame in dataSet.pixel_array:
          if frame.ndim == 2 or frame.shape[-1] == 1:
              writer.append_data(frame)
          elif colorPlate != 0:
              writer.append_data(safe_cvt(frame, colorPlate))
          else:
              writer.append_data(frame)


        writer.close()

        print("Generated MP4 in " + str(time.time() - start))

      


        generateInfoFile(dicomData, patientDir, obj["anonymizedPatientName"], obj["scaleFactor"])


if __name__ == '__main__':

    import sys, os
    import xmlTools as EX

    if len(sys.argv) < 2:
        sys.exit("Format: python3 inputParser.py input.dcm")
    else:
        try:
            dataSet = pydicom.dcmread(sys.argv[1])

        except pydicom.errors.InvalidDicomError:
            print("Dicom file '" + sys.argv[1] + "' is missing metadata information")

        except FileNotFoundError:
            print("File '" + sys.argv[1] + "' not found")

        else:
            imageToPng(dataSet)

else:
    import parsers.xmlTools as EX
