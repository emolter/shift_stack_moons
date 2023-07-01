from pytest import fixture
from .. import shift_and_stack, load_header_kw_dict
import os
from astropy.io import fits, ascii
import numpy as np


@fixture
def datadir(request, tmpdir):
    rootdir = request.config.rootdir
    path = os.path.join(rootdir, 'tests', 'data')
    return path


def test_datafiles_working(datadir):

    assert os.path.isfile(os.path.join(datadir, 'ephem.txt'))
    assert os.path.isfile(os.path.join(datadir, 'urh120.fits'))


def test_load_header():

    header_kw_dict = load_header_kw_dict('nirc2')
    for key in ['pixscale', 'rotation_correction', 'obsdate', 'start_time']:
        assert key in header_kw_dict.keys()


def test_shift_and_stack(datadir):

    # filename 5 does not exist; corrupted in original obs
    instems = [0, 1, 2, 3, 4, 6, 7, 8, 9]
    fname_list = [
        os.path.join(
            datadir,
            f'urh12{str(stem)}.fits') for stem in instems]
    fname_list = np.sort(fname_list)
    ephem = ascii.read(os.path.join(datadir, 'ephem.txt'))
    
    # test simple cross-correlation
    fits_out = shift_and_stack(
        fname_list,
        ephem,
        difference=True,
        edge_detect=False,
        diagnostic_plots=False)

    truth = fits.open(os.path.join(datadir, 'urh12_Puck_2019-11-04.fits'))

    for key in ['NAXIS1', 'NAXIS2', 'ITIME', 'COADDS', 'EXPSTOP']:
        assert fits_out[0].header[key] == truth[0].header[key]

    assert np.allclose(fits_out[0].data, truth[0].data, rtol=1e-3)
    
    # test edge detect
    fits_out_ed = shift_and_stack(
        fname_list,
        ephem,
        difference=False,
        edge_detect=True,
        diagnostic_plots=False)
        
    truth_ed = fits.open(os.path.join(datadir, 'urh12_Puck_2019-11-04_ed.fits'))
    assert np.allclose(fits_out_ed[0].data, truth_ed[0].data, rtol=1e-3)