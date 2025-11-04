#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import logging

# 配置日志器，输出到文件和控制台
logging.basicConfig(level=logging.INFO,
                    format='[daaskit.sdk] [%(levelname)s] %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
                    handlers=[
#                         logging.FileHandler("daaskit.sdk.log"), # 输出到文件
                        logging.StreamHandler(sys.stdout) # 同时输出到控制台
                    ])
logger = logging.getLogger(__name__)