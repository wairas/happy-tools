import os
import requests

from spectral import open_image
from happy.data import HappyData
from happy.writers import HappyWriter


URL_92AV3C_lan = "https://github.com/wairas/happy-tools-testdata/raw/main/92AV3C/92AV3C.lan"
URL_92AV3C_Matlab = "https://github.com/wairas/happy-tools-testdata/raw/main/92AV3C.matlab/92AV3C.1.mat"


def download_file(url: str, local_file: str):
    """
    Downloads the file from the specified URL and stores in the local file.

    :param url: the URL to load the file from
    :type url: str
    :param local_file: the local file to store the data in
    :type local_file: str
    """
    print("Downloading test data: %s" % url)
    r = requests.get(url, stream=True)
    with open(local_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def init_92AV3C(base_dir: str):
    """
    Downloads and converts the 92AV3C.lan dataset if necessary.

    :param base_dir: the base dir to use
    :type base_dir: str
    """
    updated = False
    sample_id = "92AV3C"

    # lan
    local_file = os.path.join(base_dir, "92AV3C.lan")
    if not os.path.exists(os.path.join(base_dir, sample_id)):
        updated = True
        download_file(URL_92AV3C_lan, local_file)

        # convert
        print("Converting test data: %s" % local_file)
        img = open_image(local_file)
        img_data = img.load()
        wavenumbers = [x for x in range(img.nbands)]
        happy_data = HappyData(sample_id, "1", img_data, {}, {}, wavenumbers)

        # save as happy data
        print("Saving test data (HAPPy): %s/%s" % (base_dir, sample_id))
        writer = HappyWriter(base_dir=base_dir)
        writer.write_data(happy_data)

    # matlab
    local_file = os.path.join(base_dir, "92AV3C.1.mat")
    if not os.path.exists(local_file):
        updated = True
        download_file(URL_92AV3C_Matlab, local_file)

    if updated:
        print("Finished initializing test data!")
