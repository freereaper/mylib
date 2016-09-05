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

    def run(self):
        cnt = 1
        while not self.thread_stop:
            #TODO
            self.realrun(cnt)
            cnt = cnt + 1
            time.sleep(self.interval)

    def stop(self):
        self.thread_stop = True
