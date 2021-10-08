# description
find small moons around planets using shift-and-stack based on JPL Horizons ephemeris, save as fits

will also auto-rotate back to N-up E-left if the telescope rotator had nonzero angle.

# usage
1. Open shift_and_stack.py in a text editor
2. Change the user inputs starting on Line 34
3. From terminal, run ./shift_and_stack.py

# despina_pretty_picture.jpeg
This image shows the utility of the software. The input frames have been shifted to stack on top of Despina, so all the labeled moonlets except Despina appear as streaks. If you look closely you can see the individual images that make up Proteus's streak. Neptune is a streak, too, but it's so overexposed you can't tell. The sidelobes of the PSF can be seen on Despina. We compared this stacked PSF to a calibration star PSF and the match is pretty close, so the shift-and-stack is quite accurate.

# caveats
this has only been tested on a single Neptune dataset (30 images over about an hour) observed with the NIRC2 narrow camera. Your mileage may vary.

shift_and_stack.py scrapes the FITS header of input images for the following keywords: ROTPOSN, DATE-OBS, EXPSTART, NAXIS1, NAXIS2
if you are using any instrument other than Keck NIRC2, you may need to replace these hard-coded keywords 

# dependencies
requires the Astropy-affiliated package image_registration: https://pypi.org/project/image_registration/

all other dependencies should be included with a usual Python Anaconda release

# cite
if you use this for research, please cite it in some way.  I'm no expert on how to do this right, but there are plenty of resources, e.g.: https://journals.aas.org/news/software-citation-suggestions/

written by Ned Molter 2021-Oct-08. email me: emolter at berkeley.edu
