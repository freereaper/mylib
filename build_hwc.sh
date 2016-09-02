#!/usr/bin/env bash

hwc_dir=$1

cd $hwc_dir
cd ../../../../
source build/envsetup.sh
lunch 13
cd $hwc_dir
mma


