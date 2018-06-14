import json
import os
import os.path as osp
import numpy as np
import urllib2

import base64

from unpack_stream_to_float32 import unpack_feature_from_stream


def convert_json_file_to_npy(jsonFile):
    jsonDict = load_json_file(jsonFile)
    featId = jsonDict['faces'][0]['featId']
    featPath = './' + featId
    try:
        os.makedirs(featPath)
    except:
        pass
    for individualDict in jsonDict['faces']:
        individual_to_npy(individualDict, featPath)
    return featPath


def downloadimg(imgUrl, path):
    response = urllib2.urlopen(imgUrl)
    img = response.read()
    imgName = imgUrl.split('/')[-1]
    with open(path + '/' + imgName, 'wb') as f:
        f.write(img)
        f.close()
    return


def load_json_file(filePath):
    with open(filePath, 'r') as f:
        jsonString = f.read()
        return json.loads(jsonString)


def code_feature_to_npy(jsonString):
    return unpack_feature_from_stream(jsonString)


def individual_to_npy(individualDict, featPath):
    id = individualDict['id']
    individualPath = featPath + '/' + id
    try:
        os.makedirs(individualPath)
    except:
        pass
    for singleimgDict in individualDict['features']:
        downloadimg(singleimgDict['faceUri'], individualPath)
        imgName = singleimgDict['faceUri'].split('/')[-1]

        b64_dat_fn = osp.join(individualPath, imgName + '_b64.dat')
        dat_fn = osp.join(individualPath, imgName + '.dat')

        fp = open(b64_dat_fn, 'w')
        fp.write(singleimgDict['data'])
        fp.close()

        decoded_stream = base64.decodestring(singleimgDict['data'])
        fp = open(dat_fn, 'wb')
        fp.write(decoded_stream)
        fp.close()

        npyFeature = code_feature_to_npy(singleimgDict['data'])
        npyFeature = np.asarray(npyFeature, dtype=np.float32)
        np.save(file=individualPath + '/' + imgName, arr=npyFeature)
    return


if __name__ == "__main__":
    convert_json_file_to_npy('feat1.json')
    convert_json_file_to_npy('feat2.json')
