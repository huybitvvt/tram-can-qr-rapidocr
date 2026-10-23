import cv2
import numpy as np

from tramcan_rapidocr.regions import red_display_regions


def row(frame, y):
    for index in range(3):
        cv2.rectangle(frame,(300+index*20,y),(313+index*20,y+28),(0,0,255),2)


def test_selects_gross_without_falling_through_to_lower_tare():
    frame = np.zeros((480,640,3),dtype=np.uint8)
    row(frame,110)
    row(frame,160)
    regions = red_display_regions(frame)
    assert len(regions)==1 and regions[0].y1 < 110 and regions[0].y2 < 160


def test_no_illuminated_display_has_no_region():
    assert red_display_regions(np.zeros((480,640,3),dtype=np.uint8))==[]
