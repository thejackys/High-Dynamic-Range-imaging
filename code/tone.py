#!/usr/bin/python
import cv2 as cv
import numpy as np
from utils import parse_args, ToneMapping
from pathlib import Path

def main(args):
    
    name = args.name;key = args.key
    white = args.white;phi = args.phi;threshold = args.threshold
    path = args.save
    ##get hdr img
    #hdr, RC= HDR_image(img, B, srow = srow, scol = scol)
    #cv.imwrite(name+'pic.hdr', hdr)
    hdr = np.load("./code/"+name+'.npy')
    type = '_clip'
    for b in [1, 0.5, 0]:
        hdr_img = ToneMapping(hdr, blend = b, key = key, white = white, threshold=0.05, phi = phi)*255
        tone = np.clip(hdr_img, 0, 255)
        file = args.save + 'tone'+name+'_blend_'+str(b)+type+'.png'
        print(max(hdr_img.flatten()))
        cv.imwrite(file, np.round(tone).astype('uint8'))
        print(file)

    type = '_norm'
    for b in [1, 0.5, 0]:
        hdr_img = ToneMapping(hdr, blend = b, key = key, white = white, threshold=0.05, phi = 8)*255
        tone = np.zeros(hdr_img.shape)
        tone = cv.normalize(np.log(hdr_img), tone, alpha = 0, beta = 255, norm_type=cv.NORM_MINMAX)
        print(max(hdr_img.flatten()))
        file = args.save + 'tone'+name+'_blend_'+str(b)+type+'.png'
        cv.imwrite(file, np.round(tone).astype('uint8'))
        print(file)


if __name__ == "__main__":
    args = parse_args()
    main(args)
