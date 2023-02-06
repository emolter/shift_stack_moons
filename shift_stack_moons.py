#!/usr/bin/env python

"""
example call:
python shift_stack_moons.py sample_images_list.txt "Despina" "568" "2021-10-07 00:00" "2021-10-07 23:59" 0.009942

make filename list with, e.g., ls frame*.fits > images_list.txt
"""

import matplotlib.pyplot as plt
import numpy as np
from image_registration.chi2_shifts import chi2_shift
from image_registration.fft_tools.shift import shift2d
from image import Image
from astroquery.jplhorizons import Horizons
from scipy import ndimage, interpolate
import sys
from datetime import datetime
import argparse
import pandas as pd
import warnings
from skimage import feature


def parse_arguments(args):

    parser = argparse.ArgumentParser(
        description="""
        Shift and stack observation frames according to a moon ephemeris.
        example call:
            python shift_stack_moons.py sample_images_list.txt "Despina" "568" "2021-10-07 00:00" "2021-10-07 23:59" 0.009942
        """
    )
    parser.add_argument(
        "fname_list",
        type=argparse.FileType("r"),
        help="text file with one input fits filename per line. requires full path to each file. can be made with, e.g., ls frame*.fits > images_list.txt",
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
        "tstart",
        nargs="?",
        help='Observation start time in format "YYYY-MM-DD HH:MM"". Needs not be exact as long as it is before first image was taken',
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
        help="Pixel scale of the images in arcseconds. Default is 0.009942 for NIRC2 narrow camera",
    )
    parser.add_argument("--version", action="version", version="0.0.1")

    args = parser.parse_args(args)
    args.fname_list = list(args.fname_list.readlines())
    args.fname_list = [s.strip(", \n") for s in args.fname_list]

    args.pixscale = float(args.pixscale)

    return args


def chisq_stack(frames, showplot = False, edge_detect=True, **kwargs):
    """Cross-correlate the images applying sub-pixel shift.
    Shift found using DFT upsampling method as written by image_registration package
    Stack them on top of each other to increase SNR."""
    defaultKwargs={'sigma':5,
                    'low_thresh':1e-1,
                    'high_thresh':1e1}
    kwargs = { **defaultKwargs, **kwargs }
    
    shifted_data = [frames[0]]
    if edge_detect:
        edges0 = feature.canny(frames[0], sigma=kwargs['sigma'], low_threshold = kwargs['low_thresh'], high_threshold = kwargs['high_thresh'])
    for i,frame in enumerate(frames[1:]):
        if not edge_detect:
            # simple max of convolution shift
            [dx, dy, dxerr, dyerr] = chi2_shift(frames[0], frame)
            # error is nonzero only if you include per-pixel error of each image as an input. Should eventually do that, but no need for now.
        else:
            # apply Canny algorithm to find edges. useful for aligning with Uranus rings
            edges1 = feature.canny(frame, sigma=kwargs['sigma'], low_threshold = kwargs['low_thresh'], high_threshold = kwargs['high_thresh'])
            if i == 0:
                if showplot:
                    plt.imshow(edges1, origin='lower')
                    plt.show()
            [dx,dy,dxerr,dyerr] = chi2_shift(edges0, edges1)
            
        shifted = shift2d(frame, -1 * dx, -1 * dy)
        shifted_data.append(shifted)

    return shifted_data


def shift_and_stack(fname_list, ephem, pixscale=0.009971, rotation_correction = 0.262, difference=False, edge_detect=False, perturbation_mode=False, diagnostic_plots = False):
    """
    Description
    -----------
    See Molter et al. (2023), doi:whatever Appendix whatever
    
    Parameters
    ----------
    fname_list: list of Keck fits image filenames. if not time-sorted this will
        still work, but some header info might be incorrect
        header info is taken from the zeroth fname in the list
    ephem: pd dataframe, required. astroquery Horizons ephemeris. must contain at least quantity 6, 
        the x,y position of the satellite relative to the planet
    pixscale: float, optional. pixel scale of the detector, default 0.009971 (Keck post-2015)
    rotation_correction: float, optional. 
        number of degrees to rotate clockwise to get North up, default 0.262 (Keck post-2015)
    difference: bool, optional. default False. Do you want to compute a median average, 
        then difference each frame according to that median average?
    edge_detect: bool, optional. default False. If True, align the frames using a Canny
        edge detection technique. If False, use a chi-square minimization of cross correlation
    perturbation_mode: bool, optional. If True, add random x,y shifts on top of 
        the true x,y shifts to show that this does NOT lead to a detection, i.e.,
        that the shift-and-stack technique does not introduce spurious detections
    diagnostic_plots: bool, optional. If True, shows median frame after image registration
        but before applying moon shift, and if edge_detect is also True, shows the edge detection solution
    
    To do
    -----
    presently, this only works on Keck NIRC2 images. make header keyword dictionary possible
    """

    frames = [Image(fname).data for fname in fname_list]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        frames_centered = chisq_stack(frames, edge_detect=edge_detect, showplot = diagnostic_plots)
    if difference:
        # find the median frame after shifting, from which we can difference the others
        frames_centered = np.array(frames_centered)
        median_frame = np.median(frames_centered, axis=0)
        if diagnostic_plots:
            plt.imshow(median_frame, origin='lower', vmax=100)
            plt.show()

    # plt.plot(x_shifts, y_shifts, linestyle = '', marker = '.')
    # plt.show()
    
    # make an interpolation function for x,y position as f(time) from ephem
    x_shifts = ephem["sat_X"].to_numpy()
    y_shifts = ephem["sat_Y"].to_numpy()
    datetimes = pd.DatetimeIndex(ephem["datetime_str"])
    ephem_start_time = datetimes[0]
    dt = (datetimes - ephem_start_time).total_seconds().to_numpy()
    x_interp = interpolate.interp1d(dt, x_shifts)
    y_interp = interpolate.interp1d(dt, y_shifts)
    #test_time = (pd.to_datetime('2019-10-28 01:00:04', format="%Y-%m-%d %H:%M:%S") - ephem_start_time).total_seconds()
    #print(x_interp(test_time))

    # loop through all the input images and perform shift and stack
    shifted_images = []
    shifted_x = []
    shifted_y = []
    total_itime_seconds = 0
    for i in range(len(frames_centered)):

        print("Processing file %i out of %i" % (i + 1, len(frames_centered)))
        filename = fname_list[i]
        frame = frames_centered[i]
        hdr = Image(filename).header
        
        # do the differencing if difference=True
        if difference==True:
            scaling = False #remove this option later.
            if scaling:
                flux_scaling = np.mean(median_frame) / np.mean(frame)
                frame = (flux_scaling*frame) - median_frame
            else:
                frame = frame - median_frame

        # rotate frame to posang 0, in case was rotated before
        # rotation correction is defined clockwise, but ndimage.rotate rotates ccw
        angle_needed = -rotation_correction-(float(Image(filename).header["ROTPOSN"]) - float(Image(filename).header["INSTANGL"]))
        frame = ndimage.rotate(frame, angle_needed)

        # match ephemeris time with midpoint time in fits header
        obsdate = hdr["DATE-OBS"].strip(", \n")
        start_time = obsdate + " " + hdr["EXPSTART"][:8] #accuracy seconds
        start_nseconds = (pd.to_datetime(start_time, format="%Y-%m-%d %H:%M:%S") - ephem_start_time).total_seconds()
        middle_nseconds = start_nseconds + 0.5*float(hdr["ITIME"])*float(hdr["COADDS"])
        x_shift = x_interp(middle_nseconds)
        y_shift = y_interp(middle_nseconds)

        # translate from arcsec to number of pixels
        dx = x_shift / pixscale
        dy = y_shift / pixscale
        
        # make it so image 0 has no shift applied
        if i == 0:
            dx0 = dx
            dy0 = dy
            dx = 0
            dy = 0
        else:
            dx = dx - dx0
            dy = dy - dy0
        
        if perturbation_mode:
            perturbation = 20
            dx += np.random.normal(loc=0, scale=perturbation)
            dy += np.random.normal(loc=0, scale=perturbation)
        
        shifted_x.append(dx)
        shifted_y.append(dy)

        # do the shift
        shifted = shift2d(frame, dx, -dy)
        shifted_images.append(shifted)

        # add to total exposure time
        itime = hdr["ITIME"] * hdr["COADDS"]
        total_itime_seconds += itime

    shifted_images = np.asarray(shifted_images)
    stacked_image = np.sum(shifted_images, axis=0)

    # save the stacked image as .fits
    fits_out = Image(fname_list[0])  # steal most of the header info from the first input image
    fits_out.data = stacked_image
    fits_out.header["NAXIS1"] = stacked_image.shape[0]
    fits_out.header["NAXIS2"] = stacked_image.shape[1]
    fits_out.header["ITIME"] = total_itime_seconds
    fits_out.header["COADDS"] = 1
    fits_out.header["EXPSTOP"] = hdr["EXPSTOP"] #this comes from the last input image

    return fits_out


if __name__ == "__main__":

    args = parse_arguments(sys.argv[1:])

    ## get ephemeris from Horizons. quantity 6 is the satellite relative position to parent in arcsec
    horizons_obj = Horizons(
        id=args.code,
        location=args.obscode,
        epochs={"start": args.tstart, "stop": args.tend, "step": "1m"},
    )
    ephem = horizons_obj.ephemerides(quantities=6).to_pandas()
    ephem = ephem.set_index(pd.DatetimeIndex(ephem["datetime_str"]))

    # do shift-and-stack and write
    fits_out = shift_and_stack(args.fname_list, ephem, pixscale=args.pixscale)
    outfname = "shifted_stacked_%s.fits" % (args.code)
    fits_out.write(outfname)
