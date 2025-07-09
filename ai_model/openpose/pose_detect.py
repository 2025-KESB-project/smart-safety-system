# ai_model/openpose/pose_detect.py
import cv2
import pyopenpose as op

params = dict()
params["model_folder"] = "models/"
opWrapper = op.WrapperPython()
opWrapper.configure(params)
opWrapper.start()

def detect_pose(image_path):
    image = cv2.imread(image_path)
    datum = op.Datum()
    datum.cvInputData = image
    opWrapper.emplaceAndPop([datum])
    return datum.poseKeypoints