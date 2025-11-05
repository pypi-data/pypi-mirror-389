"""Custom exceptions."""

from typing import Literal, Optional


class IncorrectSliceDimension(Exception):
    """
    Incorrect slice dimension.

    Raised when the number of slices does not match "slice_end" plus one.

    Parameters
    ----------
    slice_dim: :obj:`Literal["x", "y", "z"]`
        The specified slice dimension.

    n_slices: :obj:`int`
        The number of slices from the specified ``slice_dim``.

    slice_end: :obj:`int`
        The number of slices specified by "slice_end" in the NIfTI header.

    message: :obj:`str` or :obj:`None`:
        The error message. If None, a default error message is used.
    """

    def __init__(
        self,
        incorrect_slice_dim: Literal["x", "y", "z"],
        n_slices: int,
        slice_end: int,
        message: Optional[str] = None,
    ):
        if not message:
            self.message = (
                "Incorrect slice dimension. Number of slices for "
                f"{incorrect_slice_dim} dimension is {n_slices} but "
                f"'slice_end' in NIfTI header is {slice_end}."
            )
        else:
            self.message = message

        super().__init__(self.message)
