import glob, os
import nibabel as nib, pytest
import bidsprep.io as bids_io


def test_compress_image(nifti_img_and_path):
    """Test for ``compress_image``."""
    _, img_path = nifti_img_and_path

    files = glob.glob(os.path.join(os.path.dirname(img_path), "*"))
    assert len(files) == 1

    file = files[0]
    assert file.endswith(".nii")

    bids_io.compress_image(img_path, remove_src_file=True)

    files = glob.glob(os.path.join(os.path.dirname(img_path), "*"))
    assert len(files) == 1

    file = files[0]
    assert file.endswith(".nii.gz")


def test_load_nifti(nifti_img_and_path):
    """Test for ``load_nifti``."""
    img, img_path = nifti_img_and_path
    assert isinstance(bids_io.load_nifti(img), nib.nifti1.Nifti1Image)
    assert isinstance(bids_io.load_nifti(img_path), nib.nifti1.Nifti1Image)


def test_glob_contents(nifti_img_and_path):
    """Test for ``glob_contents``"""
    _, img_path = nifti_img_and_path
    files = bids_io.glob_contents(os.path.dirname(img_path), pattern=".nii")
    assert len(files) == 1


def test_get_nifti_header(nifti_img_and_path):
    """Test for ``get_nifti_header``."""
    img, _ = nifti_img_and_path
    assert isinstance(bids_io.get_nifti_header(img), nib.nifti1.Nifti1Header)


def test_get_nifti_affine(nifti_img_and_path):
    """Test for ``get_nifti_affine``."""
    img, _ = nifti_img_and_path
    assert bids_io.get_nifti_affine(img).shape == (4, 4)


@pytest.mark.parametrize(
    "destination_dir, remove_src_file", ([None, True], [True, False])
)
def test_create_bids_file(
    nifti_img_and_path, tmp_dir, destination_dir, remove_src_file
):
    """Test for ``create_bids_file``."""
    _, img_path = nifti_img_and_path
    destination_dir = (
        None if not destination_dir else os.path.join(tmp_dir.name, "test")
    )
    if destination_dir:
        os.makedirs(destination_dir)

    bids_filename = bids_io.create_bids_file(
        img_path,
        subj_id="01",
        desc="bold",
        remove_src_file=remove_src_file,
        destination_dir=destination_dir,
        return_bids_filename=True,
    )
    assert bids_filename
    assert os.path.basename(bids_filename) == "sub-01_desc-bold.nii"

    if destination_dir:
        dst_file = glob.glob(os.path.join(destination_dir, "*nii"))[0]
        assert os.path.basename(dst_file) == "sub-01_desc-bold.nii"

        src_file = glob.glob(os.path.join(os.path.dirname(img_path), "*.nii"))[0]
        assert os.path.basename(src_file) == "img.nii"
    else:
        files = glob.glob(os.path.join(os.path.dirname(img_path), "*.nii"))
        assert len(files) == 1
        assert os.path.basename(files[0]) == "sub-01_desc-bold.nii"


def test_create_dataset_description():
    """Test for ``create_dataset_description``."""
    dataset_desc = bids_io.create_dataset_description(
        dataset_name="test", bids_version="1.2.0"
    )
    assert dataset_desc.get("Name") == "test"
    assert dataset_desc.get("BIDSVersion") == "1.2.0"


def test_save_dataset_description(tmp_dir):
    """Test for ``save_dataset_description``."""
    dataset_desc = bids_io.create_dataset_description(
        dataset_name="test", bids_version="1.2.0"
    )
    bids_io.save_dataset_description(dataset_desc, tmp_dir.name)
    files = glob.glob(os.path.join(tmp_dir.name, "*.json"))
    assert len(files) == 1
    assert os.path.basename(files[0]) == "dataset_description.json"
