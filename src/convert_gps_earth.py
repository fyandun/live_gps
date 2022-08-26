import bagpy
import sys, os
import pandas as pd
from pyproj import Proj
import numpy as np
import math
import matplotlib.pyplot as plt


base_station_lat_long = [40.4410139324, -79.9468819254]

landm_lat_rover = [40.4401676323, 40.4399552004, 40.4397046473, 40.4394761884, 40.4412814679]
landm_long_rover = [-79.9457755896, -79.9458578792, -79.9465475879, -79.9463912996, -79.946761747]

landm_lat_gmaps = [40.4401616189461, 40.43995288691975, 40.439697712405575, 40.43947826155258, 40.44127493877423]
landm_long_gmaps = [ -79.945764319993, -79.94584948012805, -79.94653411397803, -79.9463698286776, -79.9467592084255]

landm_lat_earth = [40.44016388888888, 40.439952777777776, 40.439699999999995, 40.4394777777778, 40.4412722222222]
landm_long_earth = [-79.94576666666667, -79.94585000000001, -79.94654166666668, -79.9463722222222, -79.9467638888889]

def main(args):
    if len(args) < 2:
        print('Usage: python3 convert_gps_earth.py <path-to-bag-files>')
        sys.exit(-1)
    bagPath = args[1]
    b = bagpy.bagreader(bagPath)

    gps_csv_file = b.message_by_topic('/gps/fix')
    all_gps_data = pd.read_csv(gps_csv_file)
    all_latitudes = all_gps_data['latitude'].values
    all_longitudes = all_gps_data['longitude'].values    
    #convert this to UTM
    myProj = Proj("+proj=utm +zone=17T, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
    UTMx, UTMy = myProj(all_longitudes, all_latitudes)
    UTM_x_bs, UTM_y_bs = myProj(base_station_lat_long[1],  base_station_lat_long[0])
    gps_based_rtk_x = np.array(UTMx) - UTM_x_bs
    gps_based_rtk_y = np.array(UTMy) - UTM_y_bs    

    #for checking the errors between converting the rover gps coords and the rtk readings
    rtk_csv_file = b.message_by_topic('/gps/rtkfix')
    all_rtk_data = pd.read_csv(rtk_csv_file)
    all_x_rtk = all_rtk_data['pose.pose.position.x'].values
    all_y_rtk = all_rtk_data['pose.pose.position.y'].values

    error_x = gps_based_rtk_x - all_x_rtk
    error_y = gps_based_rtk_y - all_y_rtk
    # error_sq = math.sqrt(error_x**2 + error_y**2)

    #linear model fitting
    x_lat = landm_lat_earth
    y_lat = landm_lat_rover
    model_lat = np.polyfit(x_lat, y_lat, 1)
    predict_lat = np.poly1d(model_lat)

    x_lon = landm_long_earth
    y_lon = landm_long_rover
    model_lon = np.polyfit(x_lon, y_lon, 1)    
    predict_lon = np.poly1d(model_lon)    

    #visualization    
    x_line_lat = np.arange(min(x_lat), max(x_lat)+0.0001, 0.00005)
    y_line_lat = predict_lat(x_line_lat)
    x_line_lon = np.arange(min(x_lon), max(x_lon)+0.0001, 0.0001)
    y_line_lon = predict_lon(x_line_lon)


    plt.figure()
    plt.plot(error_x, ".b", label="error_x")
    plt.plot(error_y, ".c", label="error_y")
    plt.grid(True)
    plt.legend()

    plt.figure()
    plt.plot(landm_lat_earth, landm_lat_rover, "xb", label="sampled_landmarks")
    plt.plot(x_line_lat, y_line_lat, "r", label="linear_fit")
    plt.xlabel("google_earth_latitude")
    plt.ylabel("robot_latitude")
    plt.grid(True)
    plt.legend()

    plt.figure()
    plt.plot(landm_long_earth, landm_long_rover, "xb", label="sampled_landmarks")
    plt.plot(x_line_lon, y_line_lon, "r", label="linear_fit")
    plt.xlabel("google_earth_longitude")
    plt.ylabel("robot_longitude")
    plt.grid(True)
    plt.legend()

    plt.show()

if __name__ == '__main__':
    main(sys.argv)