"""(Re)installs pyxb compiling the opengis bundle in order to access OGC
binding classes.

"""

import argparse
import os
import shlex
import shutil
import subprocess
import tarfile
import tempfile

import pathlib2


def main(download_dir):
    download_command = "pip download {} --dest {}".format(
        _get_declared_pyxb_version(),
        str(download_dir)
    )
    subprocess.check_call(shlex.split(download_command))
    for sub_path in download_dir.iterdir():
        if sub_path.is_file() and "PYXB" in sub_path.name.upper():
            downloaded = sub_path
            break
    else:
        raise RuntimeError("Could not download pyxb to the "
                           "temporary directory")
    _untar_file(downloaded, download_dir)
    pyxb_dir = str(download_dir / downloaded.name.replace(".tar.gz", ""))
    env = os.environ.copy()
    env["PYXB_ROOT"] = pyxb_dir
    genbundles_command = ("/bin/bash {}/maintainer/genbundles common wssplat "
                          "saml20 dc opengis".format(pyxb_dir))
    subprocess.check_call(shlex.split(genbundles_command),
                          cwd=pyxb_dir, env=env)
    subprocess.check_call(["python", "setup.py", "install"],
                          cwd=pyxb_dir, env=env)


def _get_declared_pyxb_version():
    return "pyxb"


def _untar_file(path, destination_dir):
    if path.is_file() and path.name.endswith(".tar.gz"):
        tar_object = tarfile.open(str(path))
        tar_object.extractall(path=str(destination_dir))
        tar_object.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    temporary_dir = pathlib2.Path(tempfile.mkdtemp())
    try:
        main(temporary_dir)
    except Exception as err:
        print(err)
    else:
        print("Successfully installed PyXB with the opengis bundle!")
    finally:
        shutil.rmtree(str(temporary_dir))

