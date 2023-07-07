# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Basic Usage

# %%
from shift_stack_moons import shift_and_stack
from astropy.io import fits, ascii
import numpy as np
import matplotlib.pyplot as plt
import os
from astroquery.jplhorizons import Horizons

# %% [markdown]
# First we need a list of time-sorted filenames. The shift-and-stack algorithm will run properly whether these are time-sorted or not, but if they are not, some header information in the output may be incorrect.

# %%
## find filenames
data_dir = '/Users/emolter/research/keck/observations/nirc2/reduced/2019nov04/'
data_files = os.listdir(data_dir)
stem = 'urh12' #some subset of all the frames over the course of the night
fnames = [data_dir+s for s in data_files if s.startswith(stem)]
fnames = np.sort(fnames)
#print(fnames)

# %% [markdown]
# Next, we need to get the satellite ephemeris from JPL Horizons. shift_stack_moons requires an Astropy table as input, which makes it easy to interface with astroquery.

# %%
## set up call to astroquery to retrieve satellite ephemeris
obscode = '568' #Keck observatory code
code = 'Puck'
date = '2019-11-04'
tstart = date+' 00:00'
tend = date+' 23:59'
outfname = f"{stem}_{code}_{date}.fits"

# %%
## get ephemeris from Horizons. quantity 6 is the satellite relative position to parent in arcsec
horizons_obj = Horizons(
    id=code,
    location=obscode,
    epochs={"start": tstart, "stop": tend, "step": "1m"},
)
ephem = horizons_obj.ephemerides(quantities=6) #.to_pandas()

# %% [markdown]
# Now we will choose the options that are passed into shift_stack_moons. None of these is required; the default instrument (and the only one we've tested so far) is NIRC2.

# %%
## other inputs and flags to shift_stack_moons
instrument = 'nirc2'
difference = False
edge_detect = True
diagnostic_plots = False
perturbation_mode = False

# %%
## run it
fits_out = shift_and_stack(fnames, 
                           ephem, 
                           instrument=instrument, 
                           difference=difference, 
                           edge_detect=edge_detect, 
                           diagnostic_plots=diagnostic_plots,
                           perturbation_mode=perturbation_mode)
print(type(fits_out))
#fits_out.writeto(outfname, overwrite=True)

# %% [markdown]
# We can see that the output is an Astropy FITS object. If the fits_out.writeto() line is uncommented, the file urh12_Puck_2019-11-04.fits will be created.
#
# Finally, let's check out the results. Note that useful metadata has been pre-computed and put into the header, including the total integration time.

# %%
# Visualize the output
stacked_data = fits_out[0].data
hdr = fits_out[0].header
print(f'Total integration time in stack: {hdr["ITIME"]} seconds, which equals ({len(fnames)} frames) * (120 seconds per frame)')

fig, ax = plt.subplots(1,1,figsize=(10,10))
ax.imshow(stacked_data, origin='lower', vmin=0, vmax = stacked_data.max()/50)
ax.text(200, 250, 'Puck', color='orange', fontsize=16)
plt.show()

# %%
