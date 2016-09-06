#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import time

class mythread(threading.Thread):
    def __init__(self, interval, realrun):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False
        self.realrun = realrun
        self.cnt = 0
        self.normal_exit = 0

    def run(self):
        while not self.thread_stop:
            self.cnt = self.cnt + 1
            self.realrun(self.cnt, '')
            time.sleep(self.interval)

        if self.normal_exit == 1:
            self.realrun(self.cnt, r'[100%]')
        print("\n")

    def stop(self, flag):
        self.thread_stop = True
        if flag == 0:
            self.normal_exit = 1
