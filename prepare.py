#!/usr/bin/env python
import os
import tarfile
from os import path
from pathlib import Path
import urllib.request
import sys
import requests
import util
import clone
import shutil
import gzip

def unzip_file(gz_file, final_file):
    util.ensure_dirs_exist(gz_file)
    util.ensure_dirs_exist(final_file)
    unzip_dir = Path(final_file)
    if not unzip_dir.exists():
        with gzip.open(gz_file, 'rb') as f_in:
            with open(final_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

def untar_file(tar_file, final_file):
    util.ensure_dirs_exist(tar_file)
    util.ensure_dirs_exist(final_file)
    unzip_dir = Path(final_file)

    # Check if untarred file already exists
    if not unzip_dir.exists():
        if tar_file.endswith("tar.gz"):
            tar = tarfile.open(tar_file, "r:gz")
            tar.extractall(str(unzip_dir))
            tar.close()
        elif tar_file.endswith("tar"):
            tar = tarfile.open(tar_file, "r:")
            tar.extractall(str(unzip_dir))
            tar.close()

def download_with_progress(url, filename):
    util.ensure_dirs_exist(filename)

    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(
                    chunk_size=max(int(total / 1000), 1024 * 1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total)
                sys.stdout.write('\r[{}{}]'.format('█' * done,
                                                   '.' * (50 - done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


def download_and_untar(url, tar_name, final_name):
    if os.path.exists(tar_name):
        print("{} already exists - skipping download".format(tar_name))
    else:
        print("Downloading {} to {}...".format(url, tar_name))
        download_with_progress(url, tar_name)

    if os.path.exists(final_name):
        print("{} already exists - skipping extracting".format(final_name))
    else:
        print("Extracting {} to {}...".format(tar_name, final_name))
        untar_file(tar_name, final_name)


def run(cache_dir):
    download_and_untar("http://hunch.net/~vw/rcv1.tar.gz", os.path.join(cache_dir, "tmp/rcv1.tar.gz"), os.path.join(cache_dir, "tmp/rcv1_temp"))
    unzip_file(os.path.join(cache_dir, "tmp/rcv1_temp/rcv1/rcv1.test.vw.gz"), os.path.join(cache_dir, "data/rcv1/rcv1.test.vw"))
    unzip_file(os.path.join(cache_dir, "tmp/rcv1_temp/rcv1/rcv1.train.vw.gz"), os.path.join(cache_dir, "data/rcv1/rcv1.train.vw"))
    download_and_untar("https://cpsdevtesting.blob.core.windows.net/perf-data/cb_data.json.tar.gz?sp=r&st=2019-08-08T17:07:58Z&se=2050-08-09T01:07:58Z&spr=https&sv=2018-03-28&sig=Y9xgnrzemDmLdLfqa9xIPdIBWMESCvMswTNTry%2Bgwj8%3D&sr=b",
        os.path.join(cache_dir, "tmp/cb_data.tar.gz"), os.path.join(cache_dir, "data/cb_data"))
    clone.update_info_repo(cache_dir)