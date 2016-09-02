#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import hashlib
from functools import partial
from os import sys
import time
import shutil
import fileinput
from optparse import OptionParser
from zhaoxin import repo_set as repo

result = {}

def md5sum(filename):
    with open(filename, 'rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 4096), b''):
            d.update(buf)
    return d.hexdigest()

def compile_kernel(branch, bsp):
    bsp_changed = False
    ret = 0
    pattern = r"(^BSP_VERSION \?=) (\d{2}\.\d{2}\.\d{2}[a-zA-Z]?$)"
    result["kernel"] = bsp
    os.chdir(repo[branch]["KERNEL"])

    print("\n**************************start compiling kernel*********************\n")

    #modify the bsp version
    for line in fileinput.input("Makefile"):
        what = re.match(pattern, line.rstrip())
        if what is not None and what.group(2) != bsp:
            bsp_changed = True

    if bsp_changed:
        for line in fileinput.input("Makefile", inplace = True):
            print(re.sub(r"(^BSP_VERSION \?=) (\d{2}\.\d{2}\.\d{2}[a-zA-Z]?$)", r'\1 ' + bsp, line.rstrip()))

        time.sleep(2)
        ret = os.system("sudo ./build_zx2000.sh")

    else:
        print("NOTICE: BSP Version unchanged, no need to compile kernel again\n")
        time.sleep(2)

    if ret != 0:
        result["kernel"] = "compile failed"
        print("\nERROR>> compile error : %d" % ret)
        raise Exception("compile kernel error")

    print("\n**************************compiling kernel over*********************\n")

    print("---------------------------------------------------------------------------------\n")


def compile_uboot(branch):
    os.chdir(repo[branch]["UBOOT"])

    print("\n**************************start compiling uboot*********************\n")

    ret = os.system("./build_zx2000.sh")
    if ret != 0:
        print("\nERROR>> compile uboot error : %d" % ret)
        sys.exit()

    os.chdir("../secureboot-zx2000/utils/SigningTool")
    print("\nstart signing for the u-boot.bin\n")
    os.system("sudo ./secureboot.py -f ../../../uboot -k keys.lt_eng -B u-boot.toc")
    print("\n**************************Signing uboot over*********************\n")

    print('''md5info: 
             * u-boot.toc: %s

             copy....
     ''' % (md5sum("output/u-boot.toc"), ))
    shutil.copy2("output/u-boot.toc", repo[branch]["OUT"])

    result["u-boot.toc"]=md5sum("output/u-boot.toc")

    print("---------------------------------------------------------------------------------\n")


def compile_hwc(branch):
    os.chdir(repo[branch]["HWC"])
    print("\n**************************start compiling hwc*********************\n")
    ret = os.system(r'sudo bash /home/reaper/mylib/build_hwc.sh %s' % repo[branch]["HWC"])
    if ret !=0:
        sys.exit()
    print("\n**************************compiling hwc over*********************\n")

    os.chdir("../../../../")
    print('''md5info: 
             * hwcomposer.zx2000.so: %s

             copy....
     ''' % (md5sum("out/target/product/zx2000/system/vendor/lib/hw/hwcomposer.zx2000.so"), ))
    shutil.copy2("out/target/product/zx2000/system/vendor/lib/hw/hwcomposer.zx2000.so", repo[branch]["OUT"])

    result["hwc_composer.zx2000.so"] = md5sum("out/target/product/zx2000/system/vendor/lib/hw/hwcomposer.zx2000.so")

    print("---------------------------------------------------------------------------------\n")

def compile_drv(branch):
    os.chdir(repo[branch]["CBIOS"])

    print("\n**************************start compiling driver*********************\n")

    for line in fileinput.input("build_arm.sh", inplace = True):
        print(re.sub(r"(^make) LINUXDIR=(\S+) (.*)", r'\1 LINUXDIR=' + repo[branch]["KERNEL"]  + r' \3', line.rstrip()))

    time.sleep(3)
    ret = os.system("./build_arm.sh")
    if ret != 0:
        print("ERROR>> compile driver error : %d" % ret)
        result["s3g.ko"]="compile failed"
        result["s3g_core.ko"]="compile failed"
        raise Exception("compile driver failed")

    print("\n**************************compiling driver over*********************\n")
    print('''md5info: 
             * s3g.ko: %s
             * s3g_core.ko: %s

             copy....
     ''' % (md5sum("s3g.ko"), md5sum("s3g_core.ko")))
    shutil.copy2("s3g.ko", repo[branch]["OUT"])
    shutil.copy2("s3g_core.ko", repo[branch]["OUT"])

    result["s3g.ko"]=md5sum("s3g.ko")
    result["s3g_core.ko"]=md5sum("s3g_core.ko")

    print("---------------------------------------------------------------------------------\n")

def get_option():
    parser = OptionParser("usage: %prog [options] <branch> <bsp_version>", version="%prog 1.0")
    parser.add_option('-b', 
                      '--branch',
                      choices=repo["BRANCH"],
                      help=('Specify the branch'))
    parser.add_option('-d',
                      '--driver',
                      action='store_true',
                      default=False,
                      dest='driver',
                      help=('compile the s3g driver'))
    parser.add_option('-u',
                      '--uboot',
                      action='store_true',
                      default=False,
                      dest='uboot',
                      help=('compile the uboot'))
    parser.add_option('-k',
                      '--kernel',
                      action='store_true',
                      default=True,
                      dest='kernel',
                      help=('compile the kernel'))
    parser.add_option('-c',
                      '--hwc',
                      action='store_true',
                      default=False,
                      dest='hwc',
                      help=('compile the hwc'))
    parser.add_option('-v',
                      '--bsp',
                      type='string',
                      dest='bsp_version',
                      help=('the version of the bsp'))


    (options, args) = parser.parse_args();
    return (options, parser.print_help)

def OnOff(switch):
    if switch:
        return "Yes"
    else:
        return "No"

if __name__ == "__main__" :
    options, help = get_option()

    if options.bsp_version is None:
        help()
        sys.exit()

    bsp = re.match(r"^\d{2}\.\d{2}\.\d{2}[a-zA-Z]?$", options.bsp_version)

    if bsp is None:
        print("bsp version input error")
        sys.exit()

    if options.branch is None:
        help()
        sys.exit()

    print("==================================================")
    print("Compile settings:")
    print("     branch      : %s" % options.branch)
    print("     bsp version : %s" % options.bsp_version)
    print("     dirver      : %s" % OnOff(options.driver))
    print("     kernel      : %s" % OnOff(options.kernel))
    print("     uboot       : %s" % OnOff(options.uboot))
    print("     hwc         : %s" % OnOff(options.hwc))
    print("==================================================")

    time.sleep(5)

    try:
        if options.kernel:
            result["kernel"] = ""
            compile_kernel(options.branch, bsp.group())

        if options.driver:
            result["s3g_core.ko"] = ""
            result["s3g.ko"] = ""
            compile_drv(options.branch)

        if options.uboot:
            result["u-boot.toc"] = ""
            compile_uboot(options.branch)

        if options.hwc:
            result["hwc_composer.zx2000.so"] = ""
            compile_hwc(options.branch)
    except Exception as e:
        print(e)
    finally:
        print("\n\n\n==================out================================")
        for key, value in result.items():
            print("%s:    %s" %(key, value))