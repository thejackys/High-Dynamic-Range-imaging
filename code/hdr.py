#!/usr/bin/python
import cv2 as cv
import numpy as np
import argparse
from pathlib import Path
from utils import loadExposureSeq, HDR_image, parse_args


def main(args):
    
    name = args.name
    path = args.path;name = args.name
    srow = args.srow;scol = args.scol

    img, time = loadExposureSeq(path)
    n_imgs,xsize,ysize,_ = img.shape
    n = 256
    print(n_imgs)
    # Zij pixel valus of pixedl location number i in image j [256,5]
    #Bj log delta t, log shutter speed for img j
    #l constant amount of smoothness
    #w(z) weighting function for pixel value z

    B = np.log(time)
    #隨機取樣

    ##get hdr img
    hdr, RC= HDR_image(img, B, srow = srow, scol = scol)
    np.save('./code/'+name, hdr)
    cv.imwrite('./data/hdrimg/'+name+'.hdr', hdr)

if __name__ == "__main__":
    args = parse_args()
    main(args)
