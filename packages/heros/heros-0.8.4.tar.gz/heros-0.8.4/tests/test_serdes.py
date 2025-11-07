from heros.serdes import serialize, deserialize
import numpy as np


def test_ndarray():
    """Test serdes of numpy arrays of different shapes and memory representations"""
    arr_c_cont = np.arange(100).reshape(2, 50)
    assert arr_c_cont.flags.c_contiguous
    assert np.array_equiv(arr_c_cont, deserialize(serialize(arr_c_cont)))

    arr_f_cont = arr_c_cont.T
    assert arr_f_cont.flags.f_contiguous
    assert np.array_equiv(arr_f_cont, deserialize(serialize(arr_f_cont)))

    arr_none_cont = np.meshgrid(arr_c_cont, arr_c_cont, copy=False)[0][0:2]
    assert not arr_none_cont.flags.f_contiguous
    assert not arr_none_cont.flags.c_contiguous
    assert np.array_equiv(arr_none_cont, deserialize(serialize(arr_none_cont)))
