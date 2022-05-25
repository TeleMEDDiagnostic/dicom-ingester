from math import ceil

def mask_string(s, perc=0.6):
    mask_chars = ceil(len(s) * perc)
    return f'{"*" * mask_chars}{s[mask_chars:]}'

def getMaskedString(name):
  nameSplited = name.split('^')
  maskedName = ''
  for item in nameSplited:
    maskedName += mask_string(item) + '^'
  return maskedName