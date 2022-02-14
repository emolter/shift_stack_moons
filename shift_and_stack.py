#!/usr/bin/env python

'''


example call:
python shift_and_stack.py images_list.txt "Despina" "568" "2021-10-07 00:00" "2021-10-07 23:59" 0.009942

make filename list with, e.g., ls frame*.fits > images_list.txt

filestem = '/Users/emolter/research/keck/observations/nirc2/reduced/2021oct07/'
filenames = [filestem + 'frame%i_nophot_h.fits'%i for i in range(30)]
outfile = '/Users/emolter/research/keck/analysis/shift_and_stack/data/shifted_stacked_%s.fits'%moon.lower()

'''

import numpy as np
from image_registration.chi2_shifts import chi2_shift
from image_registration.fft_tools.shift import shift2d
from image import Image
from astroquery.jplhorizons import Horizons
from scipy import ndimage
import sys
from datetime import datetime
import argparse
import pandas as pd
import warnings


def parse_arguments(args):

    parser = argparse.ArgumentParser(
        description="Shift and stack observation frames according to a moon ephemeris"
    )
    parser.add_argument(
        "fname_list",
        type=argparse.FileType('r'),
        help='text file with one input fits filename per line. requires full path to each file',
    )
    parser.add_argument(
        "code", nargs="?", help='JPL Horizons target name or NAIF ID, e.g. "Despina"'
    )
    parser.add_argument(
        "obscode",
        nargs="?",
        help='JPL Horizons observatory code, e.g. "568" for Maunakea',
    )
    parser.add_argument(
        "tstart", nargs="?", help='Observation start time in format "YYYY-MM-DD HH:MM"". Needs not be exact as long as it is before first image was taken'
    )
    parser.add_argument(
        "tend",
        nargs="?",
        default=None,
        const=None,
        help='Observation end time in format "YYYY-MM-DD HH:MM"". Needs not be exact as long as it is after last image was taken',
    )
    parser.add_argument(
        "pixscale",
        nargs="?",
        default=0.009942,
        const=None,
        help='Pixel scale of the images in arcseconds. Default is 0.009942 for NIRC2 narrow camera',
    )
    parser.add_argument("--version", action="version", version="0.0.1")

    args = parser.parse_args(args)
    args.fname_list = list(args.fname_list.readlines())
    args.fname_list = [s.strip(', \n') for s in args.fname_list]
    
    args.pixscale = float(args.pixscale)

    return args


def chisq_stack(frames):
    '''Cross-correlate the images applying sub-pixel shift.
    Shift found using DFT upsampling method as written by image_registration package
    Stack them on top of each other to increase SNR.'''
    shifted_data = [frames[0]]
    for frame in frames[1:]:
        [dx,dy,dxerr,dyerr] = chi2_shift(frames[0],frame)
        #error is nonzero only if you include per-pixel error of each image as an input. Should eventually do that, but no need for now.
        shifted = shift2d(frame,-1*dx,-1*dy)
        shifted_data.append(shifted)
        
    return shifted_data
    
def shift_and_stack(fname_list, ephem, pixscale = 0.009942):
    '''
    ephem should be an ephemeris pandas data table from get_ephem
    
    will likely only work on Keck NIRC2 images
    otherwise must read different header keywords
    '''
    
    frames = [Image(fname).data for fname in fname_list]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        frames_centered = chisq_stack(frames)
    
    #plt.plot(x_shifts, y_shifts, linestyle = '', marker = '.')
    #plt.show()
    
    # loop through all the input images and perform shift and stack
    shifted_images = []
    shifted_x = []
    shifted_y = []
    total_itime_seconds = 0
    for i in range(len(frames_centered)):
        
        print('Processing file %i out of %i'%(i+1, len(frames_centered)))
        filename = fname_list[i]
        frame = frames_centered[i]
        hdr = Image(filename).header
        
        # rotate frame to posang 0, in case was rotated before
        angle_needed = -float(Image(filename).header['ROTPOSN'])
        if np.abs(angle_needed) > 0.0:
            frame = ndimage.rotate(frame, angle_needed)
        
        # match ephemeris time with time in fits header
        obsdate = hdr['DATE-OBS'].strip(', \n')
        obsdate = datetime.strftime(datetime.strptime(obsdate, '%Y-%m-%d'), '%Y-%b-%d')
        start_time = obsdate + ' ' + hdr['EXPSTART'][:5]
        ephem_line = ephem.loc[start_time]
        x_shift = float(ephem_line['sat_X'])
        y_shift = float(ephem_line['sat_Y'])
        
        # translate from arcsec to number of pixels
        dx = x_shift / pixscale
        dy = y_shift / pixscale
        shifted_x.append(dx)
        shifted_y.append(dy)
        
        # do the shift
        shifted = shift2d(frame,dx,-dy)
        shifted_images.append(shifted)
        
        # add to total exposure time
        itime = hdr['ITIME'] * hdr['COADDS']
        total_itime_seconds += itime
        
        
    shifted_images = np.asarray(shifted_images)
    stacked_image = np.sum(shifted_images, axis = 0)
    
    # save the stacked image as .fits
    fits_out = Image(fname_list[0]) # steal most of the header info from an input image
    fits_out.data = stacked_image
    fits_out.header['NAXIS1'] = stacked_image.shape[0]
    fits_out.header['NAXIS2'] = stacked_image.shape[1]
    fits_out.header['ITIME'] = total_itime_seconds
    fits_out.header['COADDS'] = 1
    
    return fits_out
    

if __name__ == "__main__":

    args = parse_arguments(sys.argv[1:])
    
    ## get ephemeris from Horizons. quantity 6 is the satellite relative position to parent in arcsec
    horizons_obj = Horizons(id=args.code, location=args.obscode, epochs = {'start':args.tstart, 'stop': args.tend, 'step':'1m'})
    ephem = horizons_obj.ephemerides(quantities=6).to_pandas()
    ephem = ephem.set_index(pd.DatetimeIndex(ephem['datetime_str']))
    
    # do shift-and-stack and write
    fits_out = shift_and_stack(args.fname_list, ephem, pixscale = args.pixscale)
    outfname = 'shifted_stacked_%s.fits'%(args.code)
    fits_out.write(outfname)


