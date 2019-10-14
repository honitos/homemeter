#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --
# -- set up the logging feature

import logging
import sys

class logger(object):
    
    def __init__(self, filename):
      self.logformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
      
      self.termhandler = logging.StreamHandler()      
      self.termhandler.setFormatter(self.logformatter)

      if filename:
        self.filehandler = self.logging.FileHandler("homeserver.log")
        self.filehandler.setFormatter(self.vlogformatter)
       
        self.getLogger()
      

if __name__ == "__main__":
    try:
        print('sfsdf');
        vlog = logger('');
        vlog.info("Program started...")
        
    except:
        e = sys.exc_info()
        print(e)
        raise
                        
    finally:
        vlog.debug("Program terminated...")
        exit()



