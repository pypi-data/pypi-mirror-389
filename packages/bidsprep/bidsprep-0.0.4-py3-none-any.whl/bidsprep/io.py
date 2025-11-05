"""Module for input/output operations."""

import glob, json, os, shutil
from typing import Optional

import nibabel as nib


def load_nifti(
    nifti_file_or_img: str | nib.nifti1.Nifti1Image,
) -> nib.nifti1.Nifti1Image:
    """
    Loads a NIfTI image.

    Loads NIfTI image when not a ``Nifti1Image`` object or
    returns the image if already loaded in.

    Parameters
    ----------
    nifti_file_or_img: :obj:`str` or :obj:`Nifti1Image`
        Path to the NIfTI file or a NIfTI image.

    Returns
    -------
    nib.nifti1.Nifti1Image
        The loaded in NIfTI image.
    """
    nifti_img = (
        nifti_file_or_img
        if isinstance(nifti_file_or_img, nib.nifti1.Nifti1Image)
        else nib.load(nifti_file_or_img)
    )

    return nifti_img


def compress_image(nifti_file: str, remove_src_file: bool = False) -> None:
    """
    Compresses a ".nii" image to a ".nii.gz" image.

    Parameters
    ----------
    nifti_file: :obj:`str`
        Path to the NIfTI image.

    remove_src_file: :obj:`bool`
        Deletes the original source image file.

    Returns
    -------
    None
    """
    img = nib.load(nifti_file)
    nib.save(img, nifti_file.replace(".nii", ".nii.gz"))

    if remove_src_file:
        os.remove(nifti_file)


def glob_contents(src_dir: str, pattern: str) -> list[str]:
    """
    Use glob to get contents with specific patterns.

    Parameters
    ----------
    src_dir: :obj:`str`
        The source directory.

    ext: :obj:`str`
        The extension.

    Returns
    -------
    list[str]
        List of contents with the pattern specified by ``pattern``.
    """
    return glob.glob(os.path.join(src_dir, f"*{pattern}"))


def get_nifti_header(nifti_file_or_img):
    """
    Get header from a NIfTI image.

    Parameters
    ----------
    nifti_file_or_img: :obj:`str` or :obj:`Nifti1Image`
        Path to the NIfTI file or a NIfTI image.

    Returns
    -------
    nib.nifti1.Nifti1Image
        The header from a NIfTI image.
    """
    return load_nifti(nifti_file_or_img).header


def get_nifti_affine(nifti_file_or_img):
    """
    Get the affine matrix from a NIfTI image.

    Parameters
    ----------
    nifti_file_or_img: :obj:`str` or :obj:`Nifti1Image`
        Path to the NIfTI file or a NIfTI image.

    Returns
    -------
    nib.nifti1.Nifti1Image
        The header from a NIfTI image.
    """
    return load_nifti(nifti_file_or_img).affine


def _copy_file(src_file: str, dst_file: str, remove_src_file: bool) -> None:
    """
    Copy a file and optionally remove the source file.

    Parameters
    ----------
    src_file: :obj:`str`
        The source file to be copied

    dst_file: :obj:`str`
        The new destination file.

    remove_src_file: :obj:`bool`
        Delete the source file if True.

    Returns
    -------
    None
    """
    shutil.copy(src_file, dst_file)

    if remove_src_file:
        os.remove(src_file)


def create_bids_file(
    nifti_file: str,
    subj_id: str | int,
    desc: str,
    ses_id: Optional[str | int] = None,
    task_id: Optional[str] = None,
    run_id: Optional[str | int] = None,
    destination_dir: str = None,
    remove_src_file: bool = False,
    return_bids_filename: bool = False,
) -> str | None:
    """
    Create a BIDS compliant filename with required and optional entities.

    Parameters
    ----------
    nifti_file: :obj:`str`
        Path to NIfTI image.

    sub_id: :obj:`str` or :obj:`int`
        Subject ID (i.e. 01, 101, etc).

    desc: :obj:`str`
        Description of the file (i.e., T1w, bold, etc).

    ses_id: :obj:`str` or :obj:`int` or :obj:`None`, default=None
        Session ID (i.e. 001, 1, etc). Optional entity.

    ses_id: :obj:`str` or :obj:`int` or :obj:`None`, default=None
        Session ID (i.e. 001, 1, etc). Optional entity.

    task_id: :obj:`str` or :obj:`None`, default=None
        Task ID (i.e. flanker, n_back, etc). Optional entity.

    run_id: :obj:`str` or :obj:`int` or :obj:`None`, default=None
        Run ID (i.e. 001, 1, etc). Optional entity.

    destination_dir: :obj:`str`, default=None
        Directory name to copy the BIDS file to. If None, then the
        BIDS file is copied to the same directory as

    remove_src_file: :obj:`str`, default=False
        Delete the source file if True.

    return_bids_filename: :obj:`str`, default=False
        Returns the full BIDS filename if True.

    Returns
    -------
    None or str
        If ``return_bids_filename`` is True, then the BIDS filename is
        returned.

    Note
    ----
    There are additional entities that can be used that are
    not included in this function
    """
    bids_filename = (
        f"sub-{subj_id}_ses-{ses_id}_task-{task_id}_" f"run-{run_id}_desc-{desc}"
    )
    bids_filename = _strip_none_entities(bids_filename)

    ext = f"{nifti_file.partition('.')[-1]}"
    bids_filename += f"{ext}"
    bids_filename = (
        os.path.join(os.path.dirname(nifti_file), bids_filename)
        if destination_dir is None
        else os.path.join(destination_dir, bids_filename)
    )

    _copy_file(nifti_file, bids_filename, remove_src_file)

    return bids_filename if return_bids_filename else None


def _strip_none_entities(bids_filename: str) -> str:
    """
    Removes entities with None in a BIDS compliant filename.

    Parameters
    ----------
    bids_filename: :obj:`str`
        The BIDS filename.

    Returns
    -------
    str
        BIDS filename with entities ending in None removed.

    Example
    -------
    >>> bids_filename = "sub-101_ses-None_task-flanker_desc-bold.nii.gz"
    >>> _strip_none_entities(bids_filename)
        "sub-101_task-flanker_desc-bold.nii.gz"
    """
    basename, _, ext = bids_filename.partition(".")
    retained_entities = [
        entity for entity in basename.split("_") if not entity.endswith("-None")
    ]

    return f"{'_'.join(retained_entities)}.{ext}"


def create_dataset_description(dataset_name: str, bids_version: str = "1.0.0") -> dict:
    """
    Generate a dataset description dictionary.

    Creates a dictionary containing the name and BIDs version of a dataset.

    .. versionadded:: 0.34.1

    Parameters
    ----------
    dataset_name: :obj:`str`
        Name of the dataset.

    bids_version: :obj:`str`,
        Version of the BIDS dataset.

    derivative: :obj:`bool`, default=False
        Determines if "GeneratedBy" key is added to dictionary.

    Returns
    -------
    dict
        The dataset description dictionary
    """
    return {"Name": dataset_name, "BIDSVersion": bids_version}


def save_dataset_description(
    dataset_description: dict[str, str], output_dir: str
) -> None:
    """
    Save a dataset description dictionary.

    Saves the dataset description dictionary as a file named "dataset_description.json" to the
    directory specified by ``output_dir``.

    Parameters
    ----------
    dataset_description: :obj:`dict`
        The dataset description dictionary.

    output_dir: :obj:`str`
        Path to save the JSON file to.

    """
    with open(
        os.path.join(output_dir, "dataset_description.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(dataset_description, f)
