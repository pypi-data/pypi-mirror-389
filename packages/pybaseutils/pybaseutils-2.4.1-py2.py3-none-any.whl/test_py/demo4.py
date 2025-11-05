# -*- coding: utf-8 -*-
"""
# --------------------------------------------------------
# @Author : Pan
# @E-mail :
# @Date   : 2025-07-08 14:10:15
# @Brief  : 转换labelme标注数据为voc格式
# --------------------------------------------------------
"""
import os
import numpy as np
import cv2
from pybaseutils.converter import convert_labelme2voc
from pybaseutils import time_utils, image_utils,file_utils

if __name__ == "__main__":
    image_dir = "/home/PKing/Downloads/image"
    image_list = file_utils.get_images_list(image_dir)
    for image_file in image_list:
        src = image_utils.read_image(image_file, use_rgb=True)
        image_utils.show_image("src", src, delay=10)
        src = cv2.cvtColor(src, cv2.COLOR_BGR2RGB)  # 将BGR转为RGB
        bs6 = image_utils.image2base64(src, use_rgb=True)
        out = image_utils.base642image(bs6, use_rgb=True)
        image_utils.show_image("out", out)
