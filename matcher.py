import common.utils as utils
import cv2
import csv
import os
import torch
import time
import json 
import argparse
import gc
import tqdm

field_names = ['file_gopro']
list_providers = ['arcgis', 'google', 'geoportal']
for provider in list_providers:
    field_names += ['raw_'+provider, 'ransac_'+provider, 'time_'+provider, 'ransac_rot_'+provider, 'time_rot_'+provider]

class File():
    def __init__(self, file_name):
        self.file = open(file_name, 'w')
        self.writer = csv.DictWriter(self.file, fieldnames = field_names, delimiter=";")
        self.writer.writeheader()
        print("Created file: ", file_name)
        
    def write_row(self, row):
        self.writer.writerow(row)
        self.file.flush()
           
    def close(self):
        self.file.close()

def rotate_image(image, angle):
    height, width = image.shape[:2]
    center = (width // 2, height // 2)

    return cv2.warpAffine(image, cv2.getRotationMatrix2D(center, angle, scale=1.0), (width, height))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='dataset_folder matcher')
    parser.add_argument('dataset', type=str, help='Path to the folder containing the dataset.')
    parser.add_argument('matcher', type=str, help='name of matcher to use.')
    args = parser.parse_args()

    dataset_folder = args.dataset
    
    matcher_csv = File(dataset_folder + '/' + args.matcher + '.txt')
    
    match_threshold = 0.1
    extract_max_keypoints = 1000
    keypoint_threshold = 0.015
    DEFAULT_RANSAC = "USAC_MAGSAC"
    
    for filename in tqdm.tqdm([filename for filename in os.listdir(dataset_folder + "/gopro") if filename.endswith('.jpg')]):
        
        csv_row = {'file_gopro': filename}
        
        for provider in list_providers:
            
            image0 = cv2.imread(dataset_folder + "/gopro/" + filename)
            image1 = cv2.imread(dataset_folder + "/" + provider + "/" + filename)

            start_time = time.time()
            output = utils.run_matching(image0, image1, match_threshold, extract_max_keypoints, keypoint_threshold, args.matcher, None)
            csv_row.update({'raw_'+provider:output[3]['number raw matches']})         
            csv_row.update({'ransac_'+provider:output[3]['number ransac matches']})
            csv_row.update({'time_'+provider:round(time.time() - start_time, 2)})
            
            del output
            gc.collect()
            
            with open(dataset_folder + "/gopro/" + filename[:-4] + '.json', 'r') as file:
                yaw_angle = json.load(file)['yaw']

            image1 = rotate_image(image1, yaw_angle)
            
            start_time = time.time()
            output = utils.run_matching(image0, image1, match_threshold, extract_max_keypoints, keypoint_threshold, args.matcher, None)
            csv_row.update({'ransac_rot_'+provider:output[3]['number ransac matches']})
            csv_row.update({'time_rot_'+provider:round(time.time() - start_time, 2)})    

            del output
            gc.collect()   
        
        matcher_csv.write_row(csv_row)
                   
    matcher_csv.close()

