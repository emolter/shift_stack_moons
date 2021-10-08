#!/usr/bin/env python

import numpy as np
from image_registration.chi2_shifts import chi2_shift
from image_registration.fft_tools.shift import shift2d
from image import Image
import get_ephem
import matplotlib.pyplot as plt
from scipy import ndimage
import sys
from datetime import datetime

'''
shift and stack according to a moon ephemeris
'''

def chisq_stack(frames):
    '''Cross-correlate the images applying sub-pixel shift.
    Shift found using DFT upsampling method as written by 
    Stack them on top of each other to increase SNR.'''
    shifted_data = [frames[0]]
    for frame in frames[1:]:
        [dx,dy,dxerr,dyerr] = chi2_shift(frames[0],frame)
        #error is nonzero only if you include per-pixel error of each image as an input. Should eventually do that, but no need for now.
        shifted = shift2d(frame,-1*dx,-1*dy)
        shifted_data.append(shifted)
        
    return shifted_data
    

if __name__ == "__main__":

    # user inputs
    moon = 'Despina' # must be lookup-able by JPL naif lookup
    load_result = True      
    obs_code = 568 # maunakea. JPL observatory code
    pixscale = 0.009942 #arcsec per pixel for NIRC2 narrow camera
    tstart = '2021-10-07 00:00' # these only need to be approximate, but tstart should be before first input frame and tend should be after last frame
    tend = '2021-10-07 23:59'
    filestem = '/Users/emolter/research/keck/observations/nirc2/reduced/2021oct07/'
    filenames = [filestem + 'frame%i_nophot_h.fits'%i for i in range(30)]
    outfile = 'data/shifted_stacked_%s.fits'%moon.lower()
    
    # get ephemeris from Horizons. quantity 6 is the satellite relative position to parent in arcsec
    code = get_ephem.naif_lookup(moon)
    frames = [Image(fname).data for fname in filenames]
    frames_centered = chisq_stack(frames)
    stepsize = '1 minute'
    ephem, _ = get_ephem.get_ephemerides(code, obs_code, tstart, tend, stepsize, quantities = 6) 
    
    # extract shifts from ephem
    ephem_times = ephem[:,0]
    ephem_times = np.asarray([s.strip(', \n') for s in ephem_times])
    x_shifts = ephem[:,3] #in arcsec. Satellite apparent differential coordinates in the plane-of-sky with respect to the primary body
    x_shifts = np.asarray([float(s.strip(', \n')) for s in x_shifts])
    y_shifts = ephem[:,4]
    y_shifts = np.asarray([float(s.strip(', \n')) for s in y_shifts])
    
    #plt.plot(x_shifts, y_shifts, linestyle = '', marker = '.')
    #plt.show()
    
    # loop through all the input images and perform shift and stack
    shifted_images = []
    shifted_x = []
    shifted_y = []
    for i in range(len(filenames)):
        
        print('Processing file %i out of %i'%(i+1, len(filenames)))
        filename = filenames[i]
        frame = frames_centered[i]
        hdr = Image(filename).header
        
        # rotate frame to posang 0, in case was rotated before
        angle_needed = -float(Image(filename).header['ROTPOSN'])
        if np.abs(angle_needed) > 0.0:
            frame = ndimage.rotate(frame, angle_needed)
        
        #plt.imshow(frame, origin = 'lower')
        #plt.show()
        
        # match ephemeris time with time in fits header
        obsdate = hdr['DATE-OBS'].strip(', \n')
        obsdate = datetime.strftime(datetime.strptime(obsdate, '%Y-%m-%d'), '%Y-%b-%d')
        start_time = obsdate + ' ' + hdr['EXPSTART'][:5]
        match_idx = int(np.argwhere(ephem_times == start_time))
        x_shift = x_shifts[match_idx]
        y_shift = y_shifts[match_idx]
        
        # translate from arcsec to number of pixels
        dx = x_shift / pixscale
        dy = y_shift / pixscale
        shifted_x.append(dx)
        shifted_y.append(dy)
        
        # do the shift
        shifted = shift2d(frame,dx,-dy)
        
        #plt.imshow(shifted, origin = 'lower')
        #plt.show()
        
        shifted_images.append(shifted)
        
    shifted_images = np.asarray(shifted_images)
    stacked_image = np.sum(shifted_images, axis = 0)
    
    # save the stacked image as .fits
    fits_out = Image(filenames[0]) # steal most of the header info from an input image
    fits_out.data = stacked_image
    fits_out.header['NAXIS1'] = stacked_image.shape[0]
    fits_out.header['NAXIS2'] = stacked_image.shape[1]
    fits_out.write(outfile)

    #plt.plot(shifted_x, shifted_y, linestyle = '', marker = '.')
    #plt.show()


