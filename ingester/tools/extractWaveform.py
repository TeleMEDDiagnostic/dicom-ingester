#! /usr/bin/env python
# -*- coding utf-8 -*-

import sys
import pydicom

"""
    Iterates through a Dataset and writes
    the waveform data on disk if found

    Linux
    Example: python3 writeWaveform.py input.dcm

    Microsoft
    Example: python "writeWaveform.py input.dcm"
"""

if len(sys.argv) < 2:
    sys.exit("Format: python3 input.dcm")
else:
    dataSet = pydicom.dcmread(sys.argv[1])
    numOfItems = 0

    """
    for elm in dataSet.iterall():
        print(elm)
        numOfItems += 1
    """         

    newDS = dataSet.group_dataset(21504)
    for elm in newDS.iterall():
        #print(elm)
        if elm.keyword == "WaveformData":
            print("Waveform found and written")
            waveform = open("waveform", 'wb')
            waveform.write(elm.value)
            waveform.close()

