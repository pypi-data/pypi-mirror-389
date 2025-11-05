import nibabel as nib, pytest
import bidsprep.utils as bids_utils


@pytest.mark.parametrize("return_header", (False, True))
def test_get_hdr_metadata(nifti_img_and_path, return_header):
    """Test for ``get_hdr_metadata``."""
    img, _ = nifti_img_and_path
    img.header["slice_end"] = 100

    if return_header:
        slice_end, hdr = bids_utils.get_hdr_metadata(
            metadata_name="slice_end",
            nifti_file_or_img=img,
            return_header=return_header,
        )
        assert isinstance(hdr, nib.nifti1.Nifti1Header)
    else:
        slice_end = bids_utils.get_hdr_metadata(
            metadata_name="slice_end",
            nifti_file_or_img=img,
            return_header=return_header,
        )

    assert slice_end == 100


def test_determine_slice_dim(nifti_img_and_path):
    """Test for ``determine_slice_dim``."""
    img, _ = nifti_img_and_path

    with pytest.raises(ValueError):
        bids_utils.determine_slice_dim(img)

    # Subtract one to convert to index
    img.header["slice_end"] = img.get_fdata().shape[2] - 1
    assert bids_utils.determine_slice_dim(img) == 2


def test_get_n_slices(nifti_img_and_path):
    """Test for ``get_n_slices``."""
    from bidsprep._exceptions import IncorrectSliceDimension

    img, _ = nifti_img_and_path
    # Subtract one to convert to index
    img.header["slice_end"] = img.get_fdata().shape[2] - 1

    with pytest.raises(IncorrectSliceDimension):
        bids_utils.get_n_slices(img, slice_dim="x")

    assert bids_utils.get_n_slices(img, slice_dim="z") == img.header["slice_end"] + 1
    assert bids_utils.get_n_slices(img) == img.header["slice_end"] + 1


def test_get_tr(nifti_img_and_path):
    """Test for ``get_tr``."""
    img, _ = nifti_img_and_path
    img.header["pixdim"][4] = 2.3
    assert bids_utils.get_tr(img) == 2.3

    img.header["pixdim"][4] = 0
    with pytest.raises(ValueError):
        bids_utils.get_tr(img)


@pytest.mark.parametrize("slice_acquisition_method", ("sequential", "interleaved"))
def test_create_slice_timing(slice_acquisition_method):
    """Test for ``create_slice_timing``."""
    from bidsprep.simulate import simulate_nifti_image

    img = simulate_nifti_image((10, 10, 4, 10))
    img.header["pixdim"][4] = 2
    img.header["slice_end"] = 3

    if slice_acquisition_method == "sequential":
        slice_timing_dict = bids_utils.create_slice_timing(
            nifti_file_or_img=img,
            slice_acquisition_method=slice_acquisition_method,
            ascending=True,
        )
        assert slice_timing_dict == [0, 0.5, 1, 1.5]

        slice_timing_dict = bids_utils.create_slice_timing(
            nifti_file_or_img=img,
            slice_acquisition_method=slice_acquisition_method,
            ascending=False,
        )
        assert slice_timing_dict == [1.5, 1, 0.5, 0]
    else:
        slice_timing_dict = bids_utils.create_slice_timing(
            nifti_file_or_img=img,
            slice_acquisition_method=slice_acquisition_method,
            ascending=True,
            interleaved_order="odd_first",
        )
        assert slice_timing_dict == [0, 1, 0.5, 1.5]

        slice_timing_dict = bids_utils.create_slice_timing(
            nifti_file_or_img=img,
            slice_acquisition_method=slice_acquisition_method,
            ascending=False,
            interleaved_order="odd_first",
        )
        assert slice_timing_dict == [1.5, 0.5, 1, 0]

        slice_timing_dict = bids_utils.create_slice_timing(
            nifti_file_or_img=img,
            slice_acquisition_method=slice_acquisition_method,
            ascending=True,
            interleaved_order="even_first",
        )
        assert slice_timing_dict == [1, 0, 1.5, 0.5]

        slice_timing_dict = bids_utils.create_slice_timing(
            nifti_file_or_img=img,
            slice_acquisition_method=slice_acquisition_method,
            ascending=False,
            interleaved_order="even_first",
        )
        assert slice_timing_dict == [0.5, 1.5, 0, 1]


def test_is_3d_img(nifti_img_and_path):
    """Test for ``is_3d_img``."""
    from bidsprep.simulate import simulate_nifti_image

    img = simulate_nifti_image((10, 10, 10))
    assert bids_utils.is_3d_img(img)

    img, _ = nifti_img_and_path
    assert not bids_utils.is_3d_img(img)


def test_get_scanner_info(nifti_img_and_path):
    """Test for ``get_scanner_info``."""
    img, _ = nifti_img_and_path
    with pytest.raises(ValueError):
        bids_utils.get_scanner_info(img)

    img.header["descrip"] = "Philips Ingenia Elition X 5.7.1"
    manufacturer_name, model_name = bids_utils.get_scanner_info(img)
    assert manufacturer_name == "Philips"
    assert model_name == "Ingenia Elition X 5.7.1"


def test_get_date_from_filename():
    """Test for ``get_date_from_filename``."""
    date = bids_utils.get_date_from_filename("101_240820_mprage_32chan.nii", "%y%m%d")
    assert date == "240820"

    date = bids_utils.get_date_from_filename("101_mprage_32chan.nii", "%y%m%d")
    assert not date
