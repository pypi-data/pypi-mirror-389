"""Mathematical operations for the MRFM simulation."""

import numpy as np


def slice_matrix(matrix, shape):
    """Slice numpy matrix.

    The function only slices the matrix in the middle based on the shape.
    The resulting array should be a view of the original array,
    which provides memory and speed improvement.

    :param ndarray matrix: a numpy array.
    :param tuple shape: sliced shape, has the same dimension as the matrix.
        The shape along the sliced axis should be the same oddity as the matrix.
    """

    oshape = np.array(matrix.shape)
    shape = np.array(shape)

    index_i = ((oshape - shape) / 2).astype(int)
    index_f = index_i + shape

    slice_index = []
    for i in range(shape.size):
        slice_index.append(slice(index_i[i], index_f[i]))

    return matrix[tuple(slice_index)]


def as_strided_x(dataset, window):
    """Function for adjusting the stride size in the x direction.

    The operation is very fast and does not require extra memory because it
    only defines the stride size rather than creating a new array
    For a dataset with a shape of (6, 5, 4) with a window of 3 in the x direction,
    the resulting array shape is (4, 5, 4). The two new parameters are
    (4, 6, 5, 4), stride is (160, 160, 32, 8) if each element is 2 bytes
    For example, to determine the max value of a 3-dimensional array for every
    3 elements in x direction::

        dataset_strided = strided_axis0(dataset, 3)
        dataset_strided.max(axis = 1)

    For more information, see `as_strided <https://docs.scipy.org/doc/numpy/
    reference/generated/numpy.lib.stride_tricks.as_strided.html
    #numpy.lib.stride_tricks.as_strided>`_ and `numpy arrays memory and strides
    <https://www.jessicayung.com/numpy-arrays-memory-and-strides/>`_.

    :param array dataset: the dataset target to determine max and min
                        (or other running operations)
    :param int window: the size of a sliding window for the dataset
    :return: strided dataset
    :rtype: ndarray
    """

    new = (dataset.shape[0] - window + 1, window) + dataset.shape[1:]
    strides = (dataset.strides[0],) + dataset.strides

    return np.lib.stride_tricks.as_strided(
        dataset, shape=new, strides=strides, writeable=False
    )
