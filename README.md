<!--
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
-->

# FOSSLight Android

> List all the binaries loaded on the Android-based model to check which open source is used for each binary, and to check whether the notices are included in the OSS notice (ex-NOTICE.html: OSS Notice for Android-based model).

## License
FOSSLight Android is LGE proprietary license, as found in the LICENSE file.

## Install

To install fosslight_android, you need to have the following pieces of software on
your computer:

- Python 3.6+
- pip

It is recommended to install it in the [python 3.6 + virtualenv environment](https://fosslight.org/fosslight-guide-en/scanner/etc/guide_virtualenv.html).

### Installation via pip (For LGE use only)
You only need to run the following command:

```bash
pip3 install "http://mod.lge.com/hub/osc/fosslight_android/-/archive/master/fosslight_android-master.zip"
```

After this, make sure that `~/.local/bin` is in your `$PATH`.

### Installation from source

```bash
$ cd android_binary_analysis/
android_binary_analysis$ pip3 install .
```

## Prerequisite

When building android, save the build log as a text file.

```bash
$ source ./build/envsetup.sh
$ make clean
$ lunch aosp_hammerhead-user
$ make -j4 2>&1 | tee android.log
```

## Usage

This tool can do various more things, detailed in the documentation. Here a
short summary:

### Required Parameters
- `s` --- Android source path.
- `a` --- Android build log file name. (File in Android source path.)

### Optional Paremeters
- `m` --- Analyze the source code for the path where the license could not be found.
- `p` --- Check files that should not be included in the Packaging file.
- `f` --- Print result of Find Command for binary that can not find Source Code Path.
- `t` --- Collect NOTICE for binaries that are not added to NOTICE.html.
- `d` --- Divide needtoadd-notice.html by binary.
- `i` --- Disable the function to automatically convert OSS names based on AOSP.
- `r` --- result.txt file with a list of binaries to remove.

### Example
```bash
$ fosslight_android -s /home/test/android_source_path -a android.log -m
```
- android.log : Exists under the android source path. (/home/test/android_source_path/android.log)
- It is recommended to add the m option. 
    This is because, if the m option is used, the license is automatically detected based on the source code path for the binary for which the license could not be detected. However, if the m option is added, the script execution time becomes longer.

## Result files
- fosslight_binary_[datetime].txt : A file that outputs checksum and TLSH values for each binary.
- fosslight_report_[%y%m%d_%H%M].xlsx : Result file output in FOSSLight Report format (Source Path and OSS information are included for each binary)
- fosslight_log_[datetime].txt : FOSSLight Android execution log output file.
### In case of m option
- Files in source_analyzed_[%Y%m%d_%H%M%S] : Result of source code analysis for each path.
