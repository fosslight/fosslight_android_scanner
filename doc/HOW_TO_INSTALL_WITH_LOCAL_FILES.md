<!--
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
-->

# How to install as a local file without pypi connection

> How to install FOSSLight Android through local files in an environment where some network access is not available.

## Prerequisite (network access is available)
> Files to prepare in advance in an environment where network access is available.
1. fosslight_android.zip : A zip file that compressed the fosslight_android source.
2. Python-3.7.13.tgz : Python source file
3. virtualenv_pkg.tar.gz : Python packages for virtualenv 
4. fosslight_android_pkg.tar.gz : Python packages for fosslight_android 

### Set up python environment
How to set up python and virtualenv : https://fosslight.org/fosslight-guide-en/scanner/etc/guide_virtualenv.html

### Download python source
```
$ wget https://www.python.org/ftp/python/3.7.13/Python-3.7.13.tgz
```
### Download packages for virtualenv
```
$ mkdir virtualenv_pkg
$ cd virtualenv_pkg
$ pip download --only-binary :all: --dest . --no-cache virtualenv
$ tar cvfz virtualenv_pkg.tar.gz virtualenv_pkg/*
```
### Download packages for fosslight_android
```
$ unzip fosslight_android.zip
$ ls fosslight_android/requirements.txt
$ mkdir fosslight_android_pkg
$ cd fosslight_android_pkg
$ pip download -r ../fosslight_android/requirements.txt
$ tar cvfz fosslight_android_pkg.tar.gz fosslight_android_pkg/*
```
## Install fosslight_android with files (network access is not available)
> The file prepared in **prerequisite** is required.

### Install Python-3.7.13

```
$ mkdir ~/bin/python
$ tar zxfv Python-3.7.13.tgz
$ cd Python-3.7.13
$ ./configure --with-ssl --prefix=$HOME/bin/python
$ make
$ make install
```
### (Optional) Make .profile_python3.7 for PATH enviroment

For use only when necessary (if you do not have sudo privileges and want to separate from other build environments)

```
$ vi .profile_python3.7
if [ -z "$MY_PYTHONE3_PATH" ] ; then
        export MY_PYTHONE3_PATH=$HOME/.local/bin:$HOME/bin/python/bin
        PATH="$MY_PYTHONE3_PATH:$PATH"
fi

$ source .profile_python3.7
$ python3 --version
Python 3.7.13
```

### Install virtualenv

```
$ source .profile_python3.7
$ tar xvfz virtualenv_pkg.tar.gz 
$ cd virtualenv_pkg
$ ls | xargs pip install --no-index --find-links .
$ cd ~
$ virtualenv -p ~/bin/python/bin/python3.7 venv
```

### Install fosslight_android
```bash
$ source .profile_python3.7
$ source venv/bin/activate
(venv) $ tar xfvz fosslight_android_pkg.tar.gz
(venv) $ cd fosslight_android_pkg
(venv) $ ls | xargs pip install --no-index --find-links .
(venv) $ cd ../
(venv) $ pip install fosslight_android.zip
```
