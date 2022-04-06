#!/usr/bin/python
import cv2 as cv
import numpy as np
import argparse
import os
from pathlib import Path

def loadExposureSeq(path):
    ##ref: https://docs.opencv.org/3.4/d3/db7/tutorial_hdr_imaging.html
    ##load eposure pic with list txt
    images = []
    times = []
    with open(path/'list.txt') as f:
        content = f.readlines()
    for line in content:
        tokens = line.split()
        images.append(cv.imread(os.path.join(path, tokens[0])))
        times.append(1 / float(tokens[1]))
    return np.asarray(images), np.asarray(times, dtype=np.float32)

def get_img_sample(img, row, col):
    n_imgs = img.shape[0]
    simg = np.zeros((n_imgs, row, col, 3))
    for i in range(n_imgs):
        #col first
        simg[i] = cv.resize(img[i], (col, row), interpolation=cv.INTER_LINEAR)
    simg = np.transpose(simg, (1, 2, 0, 3))
    simg = np.reshape(simg, (row*col, n_imgs, 3)).astype("uint8") #return
    return simg
    
def weight(v):
    min = 0.0; max = 255.0
    if v <= (min+max)/2:
        return v-min
    else:
        return max-v

def response_curve(Z, B, l, weight_function):
    print('computing responce curve')
    n_samples = Z.shape[0]; n_imgs = Z.shape[1]

    A = np.zeros((n_samples * n_imgs + 255, n_samples + 256))
    b = np.zeros((A.shape[0], 1))
    #data fitting constraints
    k = 0
    for i in range(n_samples):
        for j in range(n_imgs):
            #print(Z[i,j].astype(np.int8))
            wij = weight_function(Z[i,j])
            A[k, Z[i,j]] = wij
            A[k, (256) + i] = -wij
            b[k, 0] = wij*B[j]
            k += 1
    

    #smoothness constraint
    for i in range(1, 255):
        w = weight_function(i)
        A[k, i-1] = w * l
        A[k, i] = -2 * w * l
        A[k, i+1] = w * l
        k += 1
    
    A[k, 127] = 1
    k = k+1

    inv = np.linalg.pinv(A)
    x = inv @ b
    
    g = x[0:256]
    le = x[256:x.shape[0]]

    return g, le


def radienceMap(img, l_exptime, response_curve, weight_function):
    '''
    img shape: n_img X weight X height

    return Eradiance with weight X height
    '''
    xsize, ysize = img.shape[1], img.shape[2]
    rad_map = np.zeros((img.shape[1],img.shape[2]))
    n_imgs = len(img)
    print('computing rad Map')

    def lum(pixel):
        return response_curve[pixel]
    
    radweight_v = np.vectorize(weight_function)
    lum_v = np.vectorize(lum)

    w = np.array([radweight_v(img[i, ...]) for i in np.arange(n_imgs)])
    e = np.array([lum_v(img[i, ...])-l_exptime[i] for i in np.arange(n_imgs)])
    print('rad Map done')
    rad_map = np.exp(np.sum(w*e, axis=0)/np.sum(w, axis = 0))
    print(np.min(rad_map.flatten()), np.max(rad_map.flatten()))

    return rad_map
    
def ToneMapping(hdrimg, key = 0.18, white = 1.0, blend = 0, phi = 2, threshold= 0.05 ):
    ##follow from photographic tonereproduction 2002
    ##Lm be normalized img
    ##Ld in [0,1]    
    #blend = 1 if no local operator
    
    toneimg = np.zeros(hdrimg.shape)
    #computer 3 times in RGB channel
    delta = 0.0001 # for nonzero purpose
    Lw = 0.06*hdrimg[:, :, 0] + 0.67*hdrimg[:, :, 1] + 0.27*hdrimg[:, :, 2] + delta #BGR coef follow from the paper
    Lwhite = max(Lw.flatten())*white
    Lmean = np.exp(np.mean(np.log(delta + Lw)))
    Lm = (key/Lmean)*Lw

    #compute gaussian filter first
    '''
    gmap: blurred img in num_map differet scale
    vmap: Vsij for each scale
    '''
    num_map = 9; coef = 1.6

    gmap = np.zeros((Lm.shape[0], Lm.shape[1], num_map)) 
    vmap = np.zeros((Lm.shape[0], Lm.shape[1], num_map-1)) 
    for i in range(num_map):
        size = int(coef**i//2*2 + 1) #odd size for kernel
        #print(size)
        gmap[:, :, i] = cv.GaussianBlur(Lm, (size, size), cv.BORDER_DEFAULT)
    
    for i in range(num_map-1):
        ##compute vmap first
        s = coef**i
        div = (2**phi)*key/(s*s) + gmap[:, :, i] 
        vmap[:, :, i] = (gmap[:, :, i] - gmap[:, :, i+1])/div
    
    #get index of least elements larger than threshold
    over_threshold = np.abs(vmap) > threshold  #dim = w * h * num_map
    print(np.sum(over_threshold))
    #adjustment for ij no larger than threshold to index -1 then change to max index
    adj = np.sum(over_threshold, axis=2) == 0 
    blur_index = np.argmax(over_threshold, axis=2) - adj
    blur_index[blur_index < 0] = num_map-1
    
    #here we found smallest ij larger than threshold
    #hence -1 to get smax and adjust oob index to 0
    blur_index = blur_index-1
    blur_index[blur_index < 0] = 0
    Lblur = np.take_along_axis(gmap, blur_index[..., np.newaxis], axis = 2)
    Lblur = np.squeeze(Lblur, axis=2)
    
    Ldl = Lm / (1+Lblur) #local operator
    Ldg = Lm*(1+Lm/(Lwhite**2)) / (1+Lm) #global operator
    
    Ld = Ldg*blend+Ldl*(1-blend)
    
    for c in range(3):
        toneimg[:, :, c] = hdrimg[:, :, c] / Lw * Ld
        

    return toneimg
    


def HDR_image(img, l_exptime, l = 100, srow = 10, scol = 5):
    n_imgs, xsize, ysize, _ = img.shape 
    hdr_img = np.zeros((xsize, ysize, 3))
    RC = []
    sample = get_img_sample(img, row=srow, col=scol) #Z[i,j, channel]
    print(sample.shape)
    for c in range(3):
        rc,_ = response_curve(sample[:,:,c], l_exptime,  l, weight)
        RC.append(rc)
        ERmap = radienceMap(img[:, :, :, c], l_exptime, rc, weight)
        
        hdr_img[:, :, c] = ERmap

    return hdr_img, RC
    #tommapping
    

def parse_args() -> argparse.Namespace:
    #get imgs
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=Path,  help='pic path')
    parser.add_argument('--name', type=str,  help='pic name')
    parser.add_argument('--key', type=float,  help='key value', default = 0.38)
    parser.add_argument('--white', type=float,  help='white value', default= 1.0)
    parser.add_argument('--phi', type=float,  help='phi value', default = 8)
    parser.add_argument('--threshold', type=float,  help='episilon value', default = 0.05)
    parser.add_argument('--srow', type=int,  help='sample row', default = 15)
    parser.add_argument('--scol', type=int,  help='sample col', default = 15)
    parser.add_argument('--blend', type=float,  help='loc glob blend', default = 1)
    parser.add_argument('--save', type=str,  help='save path', default = './')
    args = parser.parse_args()
    return args
