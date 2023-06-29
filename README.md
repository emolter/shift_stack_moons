[![DOI](https://zenodo.org/badge/415108491.svg)](https://zenodo.org/badge/latestdoi/415108491)

# installation

1. Download `requirements.txt`
2. Ensure Python version in your environment is >3.6 (tested in 3.9)
3. `sh requirements.txt` should pip install all dependencies and the software itself

# usage

See `example-run.ipynb`

# description
Increase signal-to-noise ratio on small moons around planets in multi-frame observations according to the expected position of the moon from JPL Horizons.

At present, Keck NIRC2 fits header keywords are hard-coded in. If you would like to change that, submit a pull request!

![alt text](https://github.com/emolter/shift_stack_moons/blob/main/despina_pretty_picture.jpeg?raw=true)

This image shows the utility of the software. Thirty images of Neptune from Keck's NIRC2 instrument, each separated by 1-2 minutes, have been shifted according to the orbit of Despina to increase the signal-to-noise of that moon.  Despina appears as a point source, whereas all the other labeled moonlets appear as streaks. If you look closely, you can see the individual images that make up Proteus's streak. Neptune is a streak, too, but it's so overexposed you can't tell. The sidelobes of the PSF can be seen on Despina. I compared this stacked PSF to a calibration star PSF and the match is pretty close, so the shift-and-stack is quite accurate.


# caveats
shift_and_stack.py scrapes the FITS header of input images for the following keywords: ROTPOSN, DATE-OBS, EXPSTART, NAXIS1, NAXIS2, ITIME, COADDS
if you are using any instrument other than Keck NIRC2, you will likely need to replace these hard-coded keywords.
I plan to make this more generic eventually, but I'm paid to do science, not code. If you want to help out, make a pull request!

# dependencies
See requirements.txt.

Note that the most recent (officially unreleased) version of Astropy-affiliated package image\_registration is required, so it is installed directly from the GitHub page instead of from pypi.

The other dependencies should be included with a usual Python Anaconda install.

# how to cite
if you use this for research, please cite it using the DOI above. Please also cite Molter et al. 2023 (in review)

written by Ned Molter 2023-06-28
