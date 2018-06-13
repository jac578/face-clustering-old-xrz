#! /bin/env python
#---coding=utf-8
import os
import os.path as osp

import numpy as np
import scipy.misc as sc

from sklearn import cluster
from scipy.spatial.distance import cosine as ssd_cosine_dist

import time
import shutil

import urllib2
from parse_json import convert_json_file_to_npy
#from demo_noLFW import rankOrder_cluster_format

from matio import load_feat

import multiprocessing


FEATURE_DIENSION = 512


def read_txtlist(path):
    pathList = []
    with open(path, 'r') as f:
        aPath = f.readline().strip()
        while aPath:
            if aPath.startswith('/'):
                aPath = aPath[1:]
            if aPath.startswith('./'):
                aPath = aPath[2:]
            if aPath.endswith(".npy") or aPath.endswith(".mat") or aPath.endswith(".bin"):
                pathList.append(aPath)
                aPath = f.readline().strip()
        f.close()

    return pathList


def feature_data_reader(dataPath, featureList):
    feature_list = None
    index_list = None
    filePathList = read_txtlist(featureList)
    # Use first one to initialize

    cnt = 0
    feature_list = None

    for filePath in filePathList:
        cnt += 1
        print cnt
        fileFullPath = osp.join(dataPath, filePath)
        # featureVec = np.load(fileFullPath)
        featureVec = load_feat(fileFullPath)
        if featureVec.size() != FEATURE_DIENSION:
            print 'loaded feature size != %d, skip to next' % FEATURE_DIENSION
            continue

        feature_list = np.load(fileFullPath)

        if cnt == 1:
            feature_list = featureVec
        else:
            feature_list = np.vstack((feature_list, featureVec))

    return np.asarray(feature_list), index_list, filePathList


def feature_data_reader_fromList(dataPath, filePathList):
    name = multiprocessing.current_process().name
    # Use first one to initialize
    fileFullPath = osp.join(dataPath, filePathList[0])
    feature_list = np.load(fileFullPath)

    print feature_list.shape
    assert feature_list.shape[0] > 0
    # Concat else
    cnt = 0
    noHeadFilePathList = filePathList[1:]
    while(cnt < len(noHeadFilePathList)):
        filePath = noHeadFilePathList[cnt]
        if cnt % 1000 == 0:
            print "Process", name, "done concating", cnt

        fileFullPath = osp.join(dataPath, filePath)
        featureVec = np.load(fileFullPath)

        if len(featureVec.shape) > 0:  # == 512:
            feature_list = np.vstack((feature_list, featureVec))
        else:
            print 'in', "Process", name
            print feature_list.shape[0], len(noHeadFilePathList), "Process", name
            noHeadFilePathList.pop(cnt)
            print feature_list.shape[0], len(noHeadFilePathList), "Process", name
            cnt -= 1
            print feature_list.shape, featureVec.shape, fileFullPath
        cnt += 1

    print feature_list.shape[0], len(noHeadFilePathList), "Process", name
    newFilePathList = [filePathList[0]] + noHeadFilePathList

    print feature_list.shape[0], len(newFilePathList), "Process", name
    return np.asarray(feature_list), newFilePathList


def multiprocess_feature_data_reader(dataPath, featureList, nProcess=1):
    nProcess = min(nProcess, 64)

    if nProcess == 1:
        return feature_data_reader(dataPath, featureList)
    else:
        feature_list = None
        index_list = None
        filePathList = read_txtlist(featureList)
        total_line = len(filePathList)

        if total_line < nProcess:
            nProcess = 1

        p = multiprocessing.Pool(nProcess)
        pos = 0
        step = total_line / nProcess + 1
        resList = []

        for i in range(nProcess):
            if i == nProcess - 1:
                resList.append(p.apply_async(
                    feature_data_reader_fromList, args=(dataPath, filePathList[pos:],)))
            else:
                resList.append(p.apply_async(
                    feature_data_reader_fromList, args=(dataPath, filePathList[pos:pos + step],)))
                pos += step
        p.close()
        p.join()

        for i in range(nProcess):
            if i == 0:
                feature_list, filePathList = resList[i].get()
            else:
                feature_block, filePathList_part = resList[i].get()
                feature_list = np.vstack((feature_list, feature_block))
                filePathList = filePathList + filePathList_part

        return np.asarray(feature_list), index_list, filePathList


def cluster_face_features(feature_list, method=None, precomputed=True, eps=0.5):
    if feature_list is not None:
        face_feature_list = feature_list

    if face_feature_list is None:
        return None

    if precomputed:
        metric_type = 'precomputed'
        dist_matrix = __compute_pairwise_distance(face_feature_list)
        dist_matrix = dist_matrix
    else:
        metric_type = 'euclidean'
        dist_matrix = np.vstack(face_feature_list)
        dist_matrix = None

    if method == 'AP':
        cluster_estimator = cluster.AffinityPropagation(
            affinity=metric_type, damping=.55, preference=-1)
        if precomputed:
            dist_matrix = -dist_matrix
    elif method == 'DBSCAN':
        cluster_estimator = cluster.DBSCAN(
            metric=metric_type, eps=eps, min_samples=2)

    t0 = time.time()
    cluster_estimator.fit(dist_matrix)
    t1 = time.time()

    t = t1 - t0
    print 'Clustering takes: %f seconds' % t

    if hasattr(cluster_estimator, 'labels_'):
        y_pred = cluster_estimator.labels_.astype(np.int)
    else:
        y_pred = cluster_estimator.predict(dist_matrix)

    return y_pred


def __compute_pairwise_distance(face_feature_list):
    nsamples = len(face_feature_list)
    assert(nsamples > 0)
    dist_matrix = 1 - np.dot(face_feature_list, face_feature_list.T)
    return dist_matrix


def do_cluster(featDir, featureList, method,
               saveResult=False, saveDir='result',
               imgDir=None, imgList=None,
               eps=0.5,
               nReaderProcess=1, nClusterProcess=1, **kwargs):
    # saveResult = not(not(saveResult))

    # resultDict = {}
    t0 = time.time()

    n_feat = len(featureList)

    if n_feat < nReaderProcess:
        nReaderProcess = 1

    print "Start loading data: ", t0
    #feature_list, index_list, filePathList = feature_data_reader(featDir, featureList)
    feature_list, index_list, filePathList = multiprocess_feature_data_reader(
        featDir, featureList, nReaderProcess)

    t1 = time.time()
    print "Done loading data. Start clustering: ", t1, "Loading data time cost: ", t1 - t0

    do_cluster_after_read(feature_list, filePathList, method,
                          saveResult, saveDir,
                          imgDir, imgList,
                          eps)

    return


def do_cluster_after_read(feature_list, filePathList, method,
                          saveResult=False, saveDir='result',
                          imgDir=None, imgList=None,
                          eps=0.5):
    # saveResult = not(not(saveResult))

    # print 'saveResult: ', saveResult

    t1 = time.time()
    print feature_list.shape, len(filePathList)
    assert feature_list.shape[0] == len(filePathList)
    # filePathList = filePathList[0:2]
    y_pred = cluster_face_features(
        feature_list=feature_list, method=method, eps=eps)
    assert len(y_pred) == len(filePathList)
    t2 = time.time()

    print "Done clustering. Start copying result: ", t2, "Clustering time cost", t2 - t1

    # if saveResult:
    #     #saveDirPrefix = 'result_' + method + featDir.replace('./', '')
    #     saveDirPrefix = saveDir
    #     for i in range(len(y_pred)):
    #         classDir = saveDirPrefix+'/'+str(y_pred[i])+'/'
    #         try:
    #             os.makedirs(classDir)
    #         except:
    #             pass
    #         imgName = filePathList[i].replace('.npy', '.jpg').split('/')[-1]
    #         if imgName.startswith('/'):
    #             imgName = imgName[1:]
    #         imgPath = osp.join(imgDir, imgName)
    #         try:
    #             shutil.copy2(imgPath, classDir+imgName)
    #         except IOError, e:
    #             pass
    if saveResult:
        #saveDirPrefix = 'result_' + method + featDir.replace('./', '')
        saveDirPrefix = saveDir

        if isinstance(imgList, str) and osp.exists(imgList):
            imgList2 = []
            with open(imgList, 'r') as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    imgList2.append(line)
                imgList = imgList2
                fp.close()

        ###################################
        # fix imgList according to your need
        if not imgList:
            imgList = []
            for i in range(len(y_pred)):
                imgList.append(filePathList[i].replace('.npy', '.jpg'))
        ###################################

        print '===> imgList: ', imgList
        for i in range(len(y_pred)):
            classDir = osp.join(saveDirPrefix, str(y_pred[i]))

            print '===> classDir: ' + classDir
            if not osp.exists(classDir):
                os.makedirs(classDir)

            # imgPath = filePathList[i].replace('/workspace/data/blued_code/face-feature-api/ava-version-python-little-endian/feature_face/facex_api_response_blue_list_',
            #                                   '/workspace/data/blued_data/image_cropping_extend/image_face_cropping_ext_').replace('.npy', '.jpg')
            # imgName = filePathList[i].replace('.npy', '.jpg').split('/')[-1]
            # imgName = filePathList[i].replace('.npy', '.jpg')
            imgName = imgList[i]

            if imgName.startswith('/'):
                imgName = imgName[1:]

            imgPath = osp.join(imgDir, imgName)

            print '===> imgPath: ' + imgPath
            print '===> imgName: ' + imgName

            save_path = osp.join(classDir, osp.basename(imgName))
            print '===> save_path: ' + save_path

            sub_dir = osp.dirname(save_path)
            if not osp.exists(sub_dir):
                os.makedirs(sub_dir)

            shutil.copy2(imgPath, save_path)

    t3 = time.time()
    print "Done copying: ", t3, "Copying time cost", t3 - t2
    # print "Exiting..."
    # exit(0)

    return


def cluster_from_feat_dir(featDir, featureList,
                          methodList=['DBSCAN'],
                          saveResult=False, saveDir='result',
                          imgDir=None, imgList=None,
                          eps=0.5, nProcess=1):
    methodResultDict = {}
    # saveResult = not(not(saveResult))

    for method in methodList:
        t0 = time.time()
        print "method: ", method
        print "start time: ", t0

        # methodResultDict[method] = do_cluster(featDir, featureList, imgDir, method, saveResult, saveDir, eps, nProcess)
        do_cluster(featDir, featureList,  method,
                   saveResult, saveDir,
                   imgDir, imgList,
                   eps, nProcess)

        t1 = time.time()

        print "end time: ", t1
        print "time cost: ", t1 - t0
    return methodResultDict


def download_json(httpLink):
    strHtml = urllib2.urlopen(httpLink).read()
    with open('extraSample1.json', 'w') as f:
        f.write(strHtml)
    return 'extraSample1.json'


def cluster_from_httpLink(httpLink):
    jsonFile = download_json(httpLink)
    featDir = convert_json_file_to_npy(jsonFile)
    # cluster_from_feat_dir(featDir=featDir)


def cluster_from_httpLinkList(httpLinkList):
    for httpLink in httpLinkList:
        cluster_from_httpLink(httpLink)


if __name__ == "__main__":
    httpLinkList = ['http://100.100.62.235:8000/v1/feats/5aba6d7a4d7eac0007611734/faces',
                    #'http://100.100.62.235:8000/v1/feats/5aba6d7a4d7eac0007611736/faces',
                    #'http://100.100.62.235:8000/v1/feats/5aba6da14d7eac0007611738/faces',
                    #'http://100.100.62.235:8000/v1/feats/5aba6da94d7eac000761173a/faces',
                    ]
    # cluster_from_httpLinkList(httpLinkList)
    #cluster_from_feat_dir(featDir='5ab52c0e28734100076d67b9', methodList=['DBSCAN'])
