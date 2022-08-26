import numpy as np
import os, sys
from pyproj import Proj
import cubic_spline_planner
import matplotlib.pyplot as plt

base_station_lat_long = [40.4410139324, -79.9468819254]
landmark_piksi = [42.37299524181758, -79.48704063745238]
landmark_google = [42.37299524181758, -79.48704063745238]

landm_lat_rover = [40.4401676323, 40.4399552004, 40.4397046473, 40.4394761884, 40.4412814679]
landm_long_rover = [-79.9457755896, -79.9458578792, -79.9465475879, -79.9463912996, -79.946761747]

landm_lat_gmaps = [40.4401616189461, 40.43995288691975, 40.439697712405575, 40.43947826155258, 40.44127493877423]
landm_long_gmaps = [ -79.945764319993, -79.94584948012805, -79.94653411397803, -79.9463698286776, -79.9467592084255]

landm_lat_earth = [40.44016388888888, 40.439952777777776, 40.439699999999995, 40.4394777777778, 40.4412722222222]
landm_long_earth = [-79.94576666666667, -79.94585000000001, -79.94654166666668, -79.9463722222222, -79.9467638888889]

my_path = os.path.abspath(os.path.dirname(__file__))

calibrate = False

def main(args):
    lst_finish_pos = []
    file_gps_name = "test_path.kml"
    file_gps_path = os.path.join(my_path, "../gps_waypoints/", file_gps_name)

    if len(args) < 2:
        print('Usage: python3 convert_gps_earth.py calibrate. Default is not calibrate')
        calibrate = False
    elif len(args) == 2:
        print("Calibrating the model")
        calibrate = True 
    else:
        print("Too many arguments")
        sys.exit(-1)

    #linear model fitting
    if calibrate:
        #latitude
        x_lat = landm_lat_earth
        y_lat = landm_lat_rover
        model_lat = np.polyfit(x_lat, y_lat, 1)
        #longitude
        x_lon = landm_long_earth
        y_lon = landm_long_rover
        model_lon = np.polyfit(x_lon, y_lon, 1) 
    else:
        model_lat = np.array([1, 0])
        model_lon = np.array([1, 0])
    predict_lat = np.poly1d(model_lat)
    predict_lon = np.poly1d(model_lon)

    #reading the gps path from google earth kml file
    with open(file_gps_path) as fileSample:
        A = fileSample.read().splitlines()

    gps_coods_all = A[38]
    end_location = gps_coods_all.index(' ')

    lst_finish_pos.append([pos for pos, char in enumerate(gps_coods_all) if char == ' '])
    lst_finish_pos = np.array(lst_finish_pos)

    lst_init_pos_ = lst_finish_pos+1
    lst_init_pos = np.append(1, lst_init_pos_[:,:-1])[np.newaxis]

    indices = np.hstack((lst_init_pos.T, lst_finish_pos.T))
    waypoints = np.empty((0,3), float)

    latitudes = []
    longitudes = []
    for row in indices:
        lat_lon_lat = []
        init = row[0]
        end = row[1]
        single_gps_str = gps_coods_all[init:end]
        lat_lon_lat.append([pos for pos, char in enumerate(single_gps_str) if char == ','])
        latitude = float(single_gps_str[lat_lon_lat[0][0]+1:lat_lon_lat[0][1]])
        longitude = float(single_gps_str[0:lat_lon_lat[0][0]])
        altitude = float(single_gps_str[lat_lon_lat[0][1]+1:])

        gps_coords = np.array([[latitude, longitude, altitude]])

        latitudes.append(latitude)
        longitudes.append(longitude)
        waypoints = np.append(waypoints, gps_coords, axis=0)

    myProj = Proj("+proj=utm +zone=17T, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

    UTMx_bs, UTMy_bs = myProj(base_station_lat_long[1],  base_station_lat_long[0])
    
    #correct the latitudes and longitudes using the model
    latitudes_corrected = predict_lat(latitudes)
    longitudes_corrected = predict_lon(longitudes)
    UTMx, UTMy = myProj(longitudes_corrected, latitudes_corrected)

    # UTM_landmark_receiver_x, UTM_landmark_receiver_y =  myProj(landmark_piksi[1],  landmark_piksi[0])
    # UTM_landmark_google_x, UTM_landmark_google_y =  myProj(landmark_google[1],  landmark_google[0])
    # error_google_x = UTM_landmark_google_x - UTM_landmark_receiver_x
    # error_google_y = UTM_landmark_google_y - UTM_landmark_receiver_y
    # waypoint_x = np.array(UTMx) - UTMx_bs - error_google_x #- error_google_x -> here I account for the discrepancy between the gps readings and the google earth coords
    # waypoint_y = np.array(UTMy) - UTMy_bs - error_google_y

    waypoint_x = np.array(UTMx) - UTMx_bs
    waypoint_y = np.array(UTMy) - UTMy_bs
    cx, cy, cyaw, ck, s = cubic_spline_planner.calc_spline_course(waypoint_x, waypoint_y, 1.0)

    plt.plot(waypoint_x, waypoint_y, "xb", label="input")
    plt.plot(cx, cy, "-r", label="spline")
    plt.grid(True)
    plt.axis("equal")
    plt.xlabel("x[m]")
    plt.ylabel("y[m]")
    plt.legend()
    plt.show()


    file_gps_name = file_gps_name[:-4] + "_waypoints" + ".kml"
    print(file_gps_name)
    file_out_path = os.path.join(my_path, "../gps_waypoints/", file_gps_name)
    with open(file_out_path, "w+") as fileOut:
        for i in range(0, len(waypoint_x)):
            fileOut.write("%f,%f\n" % (waypoint_x[i], waypoint_y[i]))

if __name__ == '__main__':
    main(sys.argv)