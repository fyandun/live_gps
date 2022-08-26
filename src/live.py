#!/usr/bin/env python
# license removed for brevity
import rospy
import os
from std_msgs.msg import String
from sensor_msgs.msg import NavSatFix, NavSatStatus

count = 0
latitudeTotal = 0
longitudeTotal = 0

my_path = os.path.abspath(os.path.dirname(__file__))
template_name = "KML_Sample_empty_Live_path.txt"
template_path = os.path.join(my_path, "../kml_templates/", template_name)

file_out_name = "live_gps_path.kml"
template_out = os.path.join(my_path, "../kml_templates/", file_out_name)

class MyAccumulator:
    def __init__(self):
        self.sum = 0
    def add(self, number): 
        self.sum += number
        return self.sum

class myAppendText:
    def __init__(self):
        with open(template_path) as fileSample:
            A = fileSample.read().splitlines()

        A[47] = "\t\tTest" 
        B = A[0:68]
        self.B_ = B
        self.aux1 = ["\t\t</coordinates>", "\t</LineString>", "\t</Placemark>", "\t</Document>", "</kml>"]

    def rememeber(self, text):
        self.B_ = text
        #return self.B_

    def changeLine(self,line, replace):
        aux = self.B_
        aux[line] = replace
        self.B_ = aux
        #return aux



def callback(data):
    count = cuenta.add(1)
    #print(cuenta.sum)
    if count<10:
        latTotal.add(data.latitude)
        longTotal.add(data.longitude)


    if count == 10:
        latitudeProm =  latTotal.sum/9
        longitudeProm = longTotal.sum/9
        stringManage.changeLine(51, "\t\t" + str(longitudeProm))
        stringManage.changeLine(54, "\t\t" + str(latitudeProm))
        #print(latitudeProm)
        #B[51] = "\t\t" + str(longitudeProm)
        #B[54] = "\t\t" + str(latitudeProm)
        #print(stringManage.B_)

    if count > 10:

        B = stringManage.B_

        if count != 11:
            B[-5:] = []
	#34.85 is the Geoid height and has to be added to get the Orthometric heigh, which is thing the Gooogle earth plots
	#https://www.unavco.org/software/geodetic-utilities/geoid-height-calculator/geoid-height-calculator.html
	#https://eos-gnss.com/elevation-for-beginners
        auxB = "\t\t" + str(data.longitude) + "," + str(data.latitude) + "," + str(data.altitude + 62)   #62 portugal, -26ISU
        B[38] = auxB;

        B.append(auxB)
        B.extend(stringManage.aux1)

        stringManage.rememeber(B)

        with open(template_out, "w") as fileFinal:
        #fileFinal.writelines(B) 
            for element in B:
                fileFinal.write(element + "\n")

            rospy.loginfo("Elemet written")
    
    #print(count)
  
def listener():

    # In ROS, nodes are uniquely named. If two nodes with the same
    # node are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
    rospy.init_node('live', anonymous=True)

    rospy.Subscriber("/dji_sdk/gps_position", NavSatFix, callback) #   /piksi/navsatfix_rtk_fix  /fix /vectornav1/gps_navsat

    # spin() simply keeps python from exiting until this node is stopped
    #rospy.spin()
    rate = rospy.Rate(1) # 10hz
    while not rospy.is_shutdown():
        rate.sleep()

if __name__ == '__main__':
    cuenta = MyAccumulator()
    latTotal = MyAccumulator()
    longTotal = MyAccumulator()
    stringManage = myAppendText()
    listener()
