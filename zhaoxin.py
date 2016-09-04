#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

p4_base = "/home/reaper/ws/p4ws/reaper_code/sw/s3gdrv"
git_base = "/home/reaper/ws/gitws"
base = [p4_base, git_base]

drv_dir = "LinuxDST/new_kernel/linux"
kernel_dir = "vendor/zhaoxin/kernel"
uboot_dir = "vendor/zhaoxin/zx2000/uboot"
hwc_dir = "vendor/zhaoxin/zx2000/hwcomposer"
p4_project_prefix = "Source_New_"
git_project_prefix = "zx-android-5.1.1_r4_"
project_prefix = [p4_project_prefix, git_project_prefix]

p4_project_name = ["ZX2000_DVB", "ZX2K_Android5_1_IPTV"]
git_project_name = ["ZX2000_DVB", "ZX2K_IPTV"]
project_name = [p4_project_name, git_project_name]

repo_set = {
        "DVB" : {
            "CBIOS": os.path.join(base[0], project_prefix[0]+project_name[0][0], drv_dir),
            "KERNEL": os.path.join(base[1], project_prefix[1]+project_name[1][0], kernel_dir),
            "UBOOT":  os.path.join(base[1], project_prefix[1]+project_name[1][0], uboot_dir),
            "HWC"  :  os.path.join(base[1], project_prefix[1]+project_name[1][0], hwc_dir),
            "OUT"   : os.path.join("/home/reaper/.out", p4_project_name[0])
         },

        "IPTV" : {
            "CBIOS": os.path.join(base[0], project_prefix[0]+project_name[0][1], drv_dir),
            "KERNEL": os.path.join(base[1], project_prefix[1]+project_name[1][1], kernel_dir),
            "UBOOT":  os.path.join(base[1], project_prefix[1]+project_name[1][1], uboot_dir),
            "HWC"  :  os.path.join(base[1], project_prefix[1]+project_name[1][1], hwc_dir),
            "OUT"   : os.path.join("/home/reaper/.out", p4_project_name[1])
         },

        "BRANCH" : ["DVB", "IPTV"]
}



# create dirs to store our new target file
for key in repo_set:
    s = repo_set[key]
    if isinstance(s, dict):
        target = s["OUT"]
        if not os.path.exists(target):
            os.makedirs(target)

