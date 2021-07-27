#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import sys
import os
import struct


def parseWaveform(waveform, size, numberOfChannels, interpretation):
    if interpretation == "SB":
        # signed 8 bit linear
        result = struct.unpack('b' * int(size), waveform)

    elif interpretation == "UB":
        # unsigned 8 bit linear
        result = struct.unpack('B' * int(size), waveform)

    elif interpretation == "MB":
        # 8 bit mu-law (in accordance with ITU-T Recommendation G.711)
        print("Not implemented yet")

    elif interpretation == "AB":
        # 8 bit A-law (in accordance with ITU-T Recommendation G.711)
        print("Not implemented yet")

    elif interpretation == "SS":
        # signed 16 bit linear
        sizeForReading = size / 2
        result = struct.unpack('h' * int(sizeForReading), waveform)

    elif interpretation == "US":
        # unsigned 16 bit linear
        sizeForReading = size / 2
        result = struct.unpack('H' * int(sizeForReading), waveform)

    elif interpretation == "SL":
        # signed 32 bit linear
        sizeForReading = size / 2
        result = struct.unpack('l' * int(sizeForReading), waveform)

    elif interpretation == "UL":
        # unsigned 32 bit linear
        sizeForReading = size / 2
        result = struct.unpack('L' * int(sizeForReading), waveform)

    elif interpretation == "SV":
        # signed 64 bit linear
        sizeForReading = size / 2
        result = struct.unpack('q' * int(sizeForReading), waveform)

    elif interpretation == "UV":
        # unsigned 64 bit linear
        sizeForReading = size / 2
        result = struct.unpack('Q' * int(sizeForReading), waveform)

    return result


"""
For testing purposes, this module works with a waveform read from disk,
passing "12" as a number of channels and "SS" as interpretation
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Format: python3 input.dcm")
    else:
        with open(sys.argv[1], "rb") as file:
            print("this is the size of the file :" + str(os.path.getsize(sys.argv[1])))
            sizeForReading = os.path.getsize(sys.argv[1]) / 2

            """
            For this specific case, we're reading the file as in it's a stream of
            shorts, since that's what the dicom file says it is
            """
            val = parseWaveform(file.read(os.path.getsize(sys.argv[1])), os.path.getsize(sys.argv[1]), "12", "SS")

            # val = struct.unpack('h' * int(sizeForReading), file.read(os.path.getsize(sys.argv[1])))
            
            indexForFirstChannel = sizeForReading / 12
            channel1 = val[:int(sizeForReading/12)]

            numberOfValues = 0
            for x in channel1:
                print("Value " + str(x))
                numberOfValues += 1
            
            print(type(val))
            print(len(val))
            print("Number of samples read for 12 channels: " + str(numberOfValues))
