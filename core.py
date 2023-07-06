import matplotlib.pyplot as plt
import numpy as np
from image_registration.chi2_shifts import chi2_shift
from image_registration.fft_tools.shift import shift2d
from astropy.io import fits
from scipy import ndimage, interpolate
import pandas as pd
import warnings
from skimage import feature
import importlib
import importlib.resources
import yaml
import shift_stack_moons.data as header_info


def chisq_stack(frames, showplot=False, edge_detect=True, **kwargs):
    """
    Cross-correlate input images applying sub-pixel shift.
    Shift found using DFT upsampling method
    as written by `image_registration <https://github.com/keflavich/image_registration>`_ package.
    Then stack them on top of each other to increase SNR.

    Parameters
    ----------
    :frames: list, required.
        list of 2-D image arrays.
    :showplot: bool, optional. default False.
        if True, shows diagnostic plot for Canny edge detector
    :edge_detect: bool, optional. default True
        if True, applies the cross-correlation on image edges.
        This can be advantageous for images of e.g. Neptune,
        which has bright cloud features that may move
        across the frame, so it's better to cross-correlate
        on the edge of the planet's disk
        if False, applies a simple cross-correlation to the image itself
    :kwargs:
        see kwargs of `skimage.feature.canny <https://scikit-image.org/docs/stable/api/skimage.feature.html#skimage.feature.canny>`_

    Returns
    -------
    np.array, the shifted data
    """
    defaultKwargs = {'sigma': 5,
                     'low_thresh': 1e-1,
                     'high_thresh': 1e1}
    kwargs = {**defaultKwargs, **kwargs}

    shifted_data = [frames[0]]
    if edge_detect:
        edges0 = feature.canny(
            frames[0],
            sigma=kwargs['sigma'],
            low_threshold=kwargs['low_thresh'],
            high_threshold=kwargs['high_thresh'])
    for i, frame in enumerate(frames[1:]):
        if not edge_detect:
            # simple max of convolution shift
            [dx, dy, dxerr, dyerr] = chi2_shift(frames[0], frame)
            # error is nonzero only if you include per-pixel error of each
            # image as an input. Should eventually do that, but no need for
            # now.
        else:
            # apply Canny algorithm to find edges. useful for aligning with
            # Uranus rings
            edges1 = feature.canny(
                frame,
                sigma=kwargs['sigma'],
                low_threshold=kwargs['low_thresh'],
                high_threshold=kwargs['high_thresh'])
            if i == 0:
                if showplot:
                    plt.imshow(edges1, origin='lower')
                    plt.show()
            [dx, dy, dxerr, dyerr] = chi2_shift(edges0, edges1)

        shifted = shift2d(frame, -1 * dx, -1 * dy)
        shifted_data.append(shifted)

    return shifted_data


def _load_header_kw_dict(instrument):
    '''
    Load dictionary that translates header keywords for a given telescope
    see kw_nirc2.yaml for an example

    Parameters
    ----------
    :instrument: str, required.
        telescope/instrument used. code will assume there exists a .yaml file
        named kw_instrument.yaml in the data/ subdirectory
    '''
    fname = f'kw_{instrument}.yaml'
    with importlib.resources.open_binary(header_info, fname) as file:
        yaml_bytes = file.read()
        header_kw_dict = yaml.safe_load(yaml_bytes)

    return header_kw_dict


def shift_and_stack(
        fname_list,
        ephem,
        instrument='nirc2',
        difference=False,
        edge_detect=False,
        perturbation_mode=False,
        diagnostic_plots=False,
        **kwargs):
    """
    apply the shift-and-stack routine on a list of images
    based on an input ephemeris
            
    Parameters
    ----------
    :fname_list: list, required.
        list of fits image filenames. image assumed to be in hdulist[0].data
        if not time-sorted, some header info might be incorrect
    :ephem: Astropy Table, required.
        astroquery Horizons ephemeris. must contain at least quantity 6,
        the x,y position of the satellite relative to the planet
    :instrument: str, optional. default "nirc2"
        header keyword .yaml file to load.
        assumes filename kw_instrument.yaml
        see kw_nirc2.yaml for an example
    :difference: bool, optional. default False.
        Do you want to compute a median average,
        then difference each frame according to that median average?
    :edge_detect: bool, optional. default False.
        If True, align the frames using a Canny
        edge detection technique.
        If False, use a chi-square minimization of cross correlation
    :perturbation_mode: bool, optional. Default False.
        If True, add random x,y shifts on top of the
        true x,y shifts to show that this does NOT lead to a detection, i.e.,
        that the shift-and-stack technique doesnt introduce spurious detections
    :diagnostic_plots: bool, optional. Default False.
        If True, shows median frame after image registration
        but before applying moon shift, and if edge_detect is also True,
        shows the edge detection solution

    Returns
    -------
    astropy.fits object, output fits file.
    header copied from first input image, with the exception of
    *ITIME* = total integration time, computed as the sum of itime*coadds

    Notes
    -----
    Rotation Angle
    ~~~~~~~~~~~~~~
    The image is rotated counterclockwise according to
    angle_needed = -rotation_correction - (rotator_angle - instrument_angle)
    This definition follows the convention for Keck NIRC2.
    see https://github.com/jluastro/nirc2_distortion/wiki
        
    References
    ----------
    See Molter et al. (2023), doi:whatever
    """

    # load the header keyword dictionary
    kw_inst = _load_header_kw_dict(instrument)
    pixscale = kw_inst['pixscale']
    rotation_correction = kw_inst['rotation_correction']

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        frames = [fits.open(fname, ignore_missing_end=True)[
            0].data for fname in fname_list]
        frames_centered = chisq_stack(
            frames,
            edge_detect=edge_detect,
            showplot=diagnostic_plots,
            **kwargs)

    median_frame = np.median(frames_centered, axis=0)
    if diagnostic_plots:
        plt.imshow(median_frame, origin='lower')
        plt.show()

    # plt.plot(x_shifts, y_shifts, linestyle = '', marker = '.')
    # plt.show()

    # ensure ephem is a pandas object with proper index
    ephem = ephem.to_pandas()
    ephem = ephem.set_index(pd.DatetimeIndex(ephem["datetime_str"]))

    # make an interpolation function for x,y position as f(time) from ephem
    x_shifts = ephem["sat_X"].to_numpy()
    y_shifts = ephem["sat_Y"].to_numpy()
    datetimes = pd.DatetimeIndex(ephem["datetime_str"])
    ephem_start_time = min(datetimes)
    dt = (datetimes - ephem_start_time).total_seconds().to_numpy()
    x_interp = interpolate.interp1d(dt, x_shifts)
    y_interp = interpolate.interp1d(dt, y_shifts)

    if diagnostic_plots:
        plt.plot(x_shifts, y_shifts)
        plt.xlabel('X position')
        plt.ylabel('Y position')
        plt.title('Object track, sky N up')
        plt.show()

    # loop through all the input images and perform shift and stack
    shifted_images = []
    shifted_x = []
    shifted_y = []
    total_itime_seconds = 0
    for i in range(len(frames_centered)):

        print("Processing file %i out of %i" % (i + 1, len(frames_centered)))
        filename = fname_list[i]
        frame = frames_centered[i]
        hdr = fits.open(filename, ignore_missing_end=True)[0].header

        # do the differencing if difference=True
        if difference:
            frame = frame - median_frame

        # rotate frame to posang 0, in case was rotated before
        # rotation correction is defined clockwise, but ndimage.rotate rotates
        # ccw
        angle_needed = -rotation_correction - \
            (float(hdr[kw_inst["rotator_angle"]]) -
                float(hdr[kw_inst["instrument_angle"]]))
        frame = ndimage.rotate(frame, angle_needed)

        # match ephemeris time with midpoint time in fits header
        obsdate = hdr[kw_inst["obsdate"]].strip(", \n")
        start_time = obsdate + " " + \
            hdr[kw_inst["start_time"]][:8]  # accuracy seconds
        start_nseconds = (
            pd.to_datetime(
                start_time,
                format="%Y-%m-%d %H:%M:%S") -
            ephem_start_time).total_seconds()
        middle_nseconds = start_nseconds + 0.5 * \
            float(hdr[kw_inst["itime"]]) * float(hdr[kw_inst["coadds"]])
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
        itime = hdr[kw_inst["itime"]] * hdr[kw_inst["coadds"]]
        total_itime_seconds += itime

    shifted_images = np.asarray(shifted_images)
    stacked_image = np.sum(shifted_images, axis=0)

    # save the stacked image as .fits
    # steal most of the header info from the first input image
    fits_out = fits.open(fname_list[0], ignore_missing_end=True)
    fits_out[0].data = stacked_image
    fits_out[0].header["NAXIS1"] = stacked_image.shape[0]
    fits_out[0].header["NAXIS2"] = stacked_image.shape[1]
    fits_out[0].header["ITIME"] = total_itime_seconds
    fits_out[0].header["COADDS"] = 1
    # this comes from the last input image
    fits_out[0].header["EXPSTOP"] = hdr[kw_inst["end_time"]]

    return fits_out
