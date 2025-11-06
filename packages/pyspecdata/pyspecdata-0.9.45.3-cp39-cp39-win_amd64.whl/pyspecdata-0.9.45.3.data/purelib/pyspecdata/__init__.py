"""""" # start delvewheel patch
def _delvewheel_patch_1_11_2():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, '.'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-pyspecdata-0.9.45.3')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-pyspecdata-0.9.45.3')) as file:
                load_order = file.read().split()
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.LoadLibraryExW.restype = ctypes.wintypes.HMODULE
            kernel32.LoadLibraryExW.argtypes = ctypes.wintypes.LPCWSTR, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD
            for lib in load_order:
                lib_path = os.path.join(os.path.join(libs_dir, lib))
                if os.path.isfile(lib_path) and not kernel32.LoadLibraryExW(lib_path, None, 8):
                    raise OSError('Error loading {}; {}'.format(lib, ctypes.FormatError(ctypes.get_last_error())))


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from .general_functions import (
    CustomError,
    autostringconvert,
    balance_clims,
    box_muller,
    check_ascending_axis,
    complex_str,
    copy_maybe_none,
    det_unit_prefactor,
    dp,
    emptytest,
    fa,
    fname_makenice,
    init_logging,
    inside_sphinx,
    level_str_to_int,
    lsafe,
    lsafen,
    myfilter,
    ndgrid,
    pinvr,
    process_kwargs,
    redim_C_to_F,
    redim_F_to_C,
    reformat_exp,
    render_matrix,
    sech,
    strm,
    whereblocks,
)
from .plot_funcs.DCCT_function import DCCT
from .plot_funcs.image import image
from .core import *
from .load_files import *
from .figlist import *
from .nnls import *
from .lmfitdata import lmfitdata
from .lmfitdataGUI import lmfitdataGUI
from .generate_fake_data import fake_data
from .dict_utils import make_ndarray, unmake_ndarray
from .load_files.zenodo import zenodo_upload, create_deposition
from .datadir import getDATADIR, log_fname, proc_data_target_dir
from .mpl_utils import (
    plot_label_points,
    figlistret,
    figlistini_old,
)

# import numpy

# so essentially, __all__ is the namespace that is passed with an import *
# __all__ = ['prop',
#        'nddata',
#        'figlist_var',
#        'plot',
#        'OLDplot',
#        'nddata_hdf5']
# __all__.extend(numpy.__all__)
__all__ = [x for x in dir() if x[0] != "_"]
