# description
find small moons around planets using shift-and-stack based on JPL Horizons ephemeris, save as fits

will also auto-rotate back to N-up E-left if the telescope rotator had nonzero angle.

![alt text](https://github.com/emolter/shift_stack_moons/blob/main/despina_pretty_picture.jpeg?raw=true)

This image shows the utility of the software. Thirty images of Neptune from Keck's NIRC2 instrument, each separated by 1-2 minutes, have been shifted according to the orbit of Despina to increase the signal-to-noise of that moon.  Despina appears as a point source, whereas all the other labeled moonlets appear as streaks. If you look closely you can see the individual images that make up Proteus's streak. Neptune is a streak, too, but it's so overexposed you can't tell. The sidelobes of the PSF can be seen on Despina. I compared this stacked PSF to a calibration star PSF and the match is pretty close, so the shift-and-stack is quite accurate.

# usage
1. Open shift_and_stack.py in a text editor
2. Change the user inputs starting on Line 34
3. From terminal, run ./shift_and_stack.py

# caveats
this has only been tested on a single Neptune dataset observed with the NIRC2 narrow camera. Your mileage may vary.

shift_and_stack.py scrapes the FITS header of input images for the following keywords: ROTPOSN, DATE-OBS, EXPSTART, NAXIS1, NAXIS2, ITIME, COADDS
if you are using any instrument other than Keck NIRC2, you may need to replace these hard-coded keywords 

# dependencies
requires the Astropy-affiliated package image_registration: https://pypi.org/project/image_registration/

all other dependencies should be included with a usual Python Anaconda release

# cite
if you use this for research, please cite it in some way.  I'm no expert on how to do this right, but there are plenty of resources, e.g.: https://journals.aas.org/news/software-citation-suggestions/

written by Ned Molter 2021-Oct-08.
