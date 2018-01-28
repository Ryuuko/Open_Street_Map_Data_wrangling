import xml.etree.ElementTree as ET

xmlTree = ET.parse("hong-kong_sample3.osm")
id_list = []

for item in xmlTree.iter('node'):
    if float(item.attrib["lat"]) > 22.1288990483 and float(item.attrib["lat"]) < 22.5940489229:
        if float(item.attrib["lon"]) > 113.7498330311 and float(item.attrib["lon"]) < 114.4761440615 :
            pass
        else:
        	id_list.append(item.attrib['id'])

thefile = open('id00.text', 'w')

for item in id_list:
    thefile.write("%s\n" % item) 


