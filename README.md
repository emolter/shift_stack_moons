[![DOI](https://zenodo.org/badge/415108491.svg)](https://zenodo.org/badge/latestdoi/415108491)
[![codecov.io Code Coverage](https://codecov.io/gh/emolter/shift_stack_moons/branch/main/graph/badge.svg)](https://codecov.io/gh/emolter/shift_stack_moons)

# Installation

1. Ensure Python version in your environment is >=3.7
2. pip install -r requirements.txt
3. pip install shift-stack-moons

# Usage

See `example-run.ipynb`

# Description
Increase signal-to-noise ratio on small moons around planets in multi-frame observations according to the expected position of the moon from JPL Horizons.

![alt text](https://github.com/emolter/shift_stack_moons/blob/main/despina_pretty_picture.jpeg?raw=true)

This image shows the utility of the software. Thirty images of Neptune from Keck's NIRC2 instrument, each separated by 1-2 minutes, have been shifted according to the orbit of Despina to increase the signal-to-noise of that moon.  Despina appears as a point source, whereas all the other labeled moonlets appear as streaks. If you look closely, you can see the individual images that make up Proteus's streak. Neptune is a streak, too, but it's so overexposed you can't tell. The sidelobes of the PSF can be seen on Despina. I compared this stacked PSF to a calibration star PSF and the match is pretty close, so the shift-and-stack is quite accurate.

# Caveats
shift_and_stack.py scrapes the FITS header of input images for relevant information like the rotator angle, instrument angle, observation date and time, integration time, etc. The keywords are included in a .yaml file (data/kw\_instrument.yaml) to (in theory) support ease-of-use for different fits header conventions.  

However, this has only been tested for Keck's NIRC2 instrument. If you are using any instrument other than Keck NIRC2, you will need to make a .yaml file for your instrument.

# Dependencies
See requirements.txt.

Note that the most recent (officially unreleased) version of Astropy-affiliated package image\_registration is required, so it is installed directly from the GitHub page instead of from pypi.

The other dependencies should be included with a usual Python Anaconda install.

# Contributing

I welcome contributions! Please submit an issue first, explaining what you'd like to change/add.  I'll comment on that, and then you can submit a PR when your improvement/addition is ready!

# Cite
If you use this for research, please cite it using the DOI above. Please also cite Molter et al. 2023 (in review)
