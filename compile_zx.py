#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import hashlib
from functools import partial
from functools import wraps
from os import sys
import pexpect
import platform
import time
import shutil
import fileinput
from optparse import OptionParser
#from zhaoxin import repo_set as repo
from private import mypasswd
from mythread import mythread

result = {}
en_log = False
repo = {}

def process(module):
    def with_log(func):
        @wraps(func)
        def wrapper(*args, **kw):
            print("\n-------------------------------------start compiling %s------------------------------------------\n" % module)
            ret = func(*args, **kw)
            print("\n-------------------------------------compiling %s over-------------------------------------------\n" % module)
            return ret
        return wrapper
    return with_log

def process_bar(progress, over):
    bar = '█'
    sys.stdout.write('\rbulding: %s %s' % (bar * progress, over))
    sys.stdout.flush()

def md5sum(filename):
    with open(filename, 'rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 4096), b''):
            d.update(buf)
    return d.hexdigest()

def spawn_exec(cmd):
    osname = platform.system()
    if osname == 'Linux':
        prombt = r'\[sudo\] password for %s:' % os.environ['USER']
    elif osname == 'Darwin':
        prompt = 'Password:'
    else:
        assert False, osname

    child = pexpect.spawnu(cmd, timeout=600)
    idx = child.expect([prombt, pexpect.EOF, pexpect.TIMEOUT])
    if idx == 0:
        child.sendline(mypasswd)
        child.expect(pexpect.EOF)
    elif idx == 2:
        raise Exception("exec %s timeout" % cmd)
    child.close()
    return (child.exitstatus, child.before)

@process("kernel")
def compile_kernel(branch, bsp, force):
    bsp_changed = False
    ret = 1
    pattern = r"(^BSP_VERSION \?=) (\d{2}\.\d{2}\.\d{2}[a-zA-Z]?$)"
    result["kernel"] = bsp
    os.chdir(repo[branch]["KERNEL"])

    #modify the bsp version
    for line in fileinput.input("Makefile"):
        what = re.match(pattern, line.rstrip())
        if what is not None and what.group(2) != bsp:
            bsp_changed = True

    if bsp_changed or force:
        for line in fileinput.input("Makefile", inplace = True):
            print(re.sub(r"(^BSP_VERSION \?=) (\d{2}\.\d{2}\.\d{2}[a-zA-Z]?$)", r'\1 ' + bsp, line.rstrip()))

        try:
            thread = mythread(2, process_bar)
            thread.start()
            (ret,log) = spawn_exec("sudo ./build_zx2000.sh")
        finally:
            thread.stop(ret)
            thread.join()
            if en_log == True:
                print(log)

    else:
        ret = 0
        print("NOTICE: BSP Version unchanged, no need to compile kernel again\n")
        time.sleep(2)

    if ret != 0:
        result["kernel"] = "compile failed"
        print("\nERROR>> compile error : %d" % ret)
        raise Exception("compile kernel error")

@process("uboot")
def compile_uboot(branch):
    ret = 1

    os.chdir(repo[branch]["UBOOT"])

    try:
        thread = mythread(0.5, process_bar)
        thread.start()
        (ret, log) = spawn_exec("./build_zx2000.sh")
    finally:
        thread.stop(ret)
        thread.join()
        if en_log == True:
            print(log)



    if ret != 0:
        result["u-boot.toc"] = "compile failed"
        print("\nERROR>> compile uboot error : %d" % ret)
        raise Exception("compile uboot error")

    os.chdir("../secureboot-zx2000/utils/SigningTool")
    print("\n\nstart signing for the u-boot.bin")
    (ret, log) = spawn_exec("sudo ./secureboot.py -f ../../../uboot -k keys.lt_eng -B u-boot.toc")
    if ret != 0:
        result["u-boot.toc"] = "signing failed"
        print("\nERROR>> signing uboot error : %d" % ret)
        raise Exception("signing uboot error")

    print("Signing uboot over.\n")

    print('''md5info:
             * u-boot.toc: %s

             copy....
     ''' % (md5sum("output/u-boot.toc"), ))
    shutil.copy2("output/u-boot.toc", repo[branch]["OUT"])

    result["u-boot.toc"] = md5sum("output/u-boot.toc")

@process("hwc")
def compile_hwc(branch):
    ret = 1
    os.chdir(repo[branch]["HWC"])

    try:
        thread = mythread(1, process_bar)
        thread.start()
        (ret,log) = spawn_exec(r'sudo bash /home/reaper/mylib/build_hwc.sh %s' % repo[branch]["HWC"])
    finally:
        thread.stop(ret)
        thread.join()
        if en_log == True:
            print(log)


    if ret !=0:
        result["hwc_composer.zx2000.so"] = "compile failed"
        raise Exception("compile hwc failed")

    os.chdir("../../../../")
    print('''\n\nmd5info:
             * hwcomposer.zx2000.so: %s

             copy....
     ''' % (md5sum("out/target/product/zx2000/system/vendor/lib/hw/hwcomposer.zx2000.so"), ))
    shutil.copy2("out/target/product/zx2000/system/vendor/lib/hw/hwcomposer.zx2000.so", repo[branch]["OUT"])

    result["hwc_composer.zx2000.so"] = md5sum("out/target/product/zx2000/system/vendor/lib/hw/hwcomposer.zx2000.so")

@process("driver")
def compile_drv(branch):
    ret = 1
    os.chdir(repo[branch]["CBIOS"])

    for line in fileinput.input("build_arm.sh", inplace = True):
        print(re.sub(r"(^make) LINUXDIR=(\S+) (.*)", r'\1 LINUXDIR=' + repo[branch]["KERNEL"]  + r' \3', line.rstrip()))

    try:
        thread = mythread(0.1, process_bar)
        thread.start()
        (ret, log) = spawn_exec("bash ./build_arm.sh")
    finally:
        thread.stop(ret)
        thread.join()
        if en_log == True:
            print(log)

    if ret != 0:
        print("ERROR>> compile driver error : %d" % ret)
        result["s3g.ko"]="compile failed"
        result["s3g_core.ko"]="compile failed"
        raise Exception("compile driver failed")

    print('''\nmd5info:
             * s3g.ko: %s
             * s3g_core.ko: %s

             copy....
     ''' % (md5sum("s3g.ko"), md5sum("s3g_core.ko")))
    shutil.copy2("s3g.ko", repo[branch]["OUT"])
    shutil.copy2("s3g_core.ko", repo[branch]["OUT"])

    result["s3g.ko"]=md5sum("s3g.ko")
    result["s3g_core.ko"]=md5sum("s3g_core.ko")

def get_option():
    parser = OptionParser("usage: %prog [options] <branch> <bsp_version>", version="%prog 1.0")
    parser.add_option('-b',
                      '--branch',
                      type='string',
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
    parser.add_option('-f',
                      '--force',
                      action='store_true',
                      default=False,
                      dest='force',
                      help=('force compiling the kernel even the bsp version is not changed.'))
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
    parser.add_option('-r',
                      '--repo',
                      type='string',
                      dest='repo',
                      default="zhaoxin",
                      help=('from which module to load your repo setting'))
    parser.add_option('-l',
                      '--log',
                      action='store_true',
                      default=False,
                      dest='log',
                      help=('print the compile log or not'))


    (options, args) = parser.parse_args();
    return (options, parser.print_help)

def OnOff(switch):
    if switch:
        return "Yes"
    else:
        return "No"

if __name__ == "__main__" :
    options, help = get_option()

    try:
       repo_module = __import__(options.repo)
       repo_set = getattr(repo_module, "repo_set")

    except (ImportError, NameError):
        print(r"repo_set from %s.py can not be found" % options.repo)
        help()
        sys.exit()

    repo = repo_set

    en_log = options.log

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

    print("==================================================================================================")
    print("                             Compile settings:")
    print("                             branch      : %s" % options.branch)
    print("                             bsp version : %s" % options.bsp_version)
    print("                             dirver      : %s" % OnOff(options.driver))
    print("                             kernel      : %s" % OnOff(options.kernel))
    print("                             uboot       : %s" % OnOff(options.uboot))
    print("                             hwc         : %s" % OnOff(options.hwc))
    print("=================================================================================================")

    time.sleep(2)

    try:
        if options.kernel:
            result["kernel"] = ""
            compile_kernel(options.branch, bsp.group(), options.force)

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
        print("\n=========================================out============================================")
        for key, value in result.items():
            print("                        %s:    %s" %(key, value))
        print("=========================================out============================================\n")
