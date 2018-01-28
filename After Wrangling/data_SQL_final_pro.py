#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

#import cerberus

#import schema

OSM_PATH = "hong-kong_china.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"



LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

#SCHEMA = schema.py

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def is_zh (c):

        x = ord (c)
        # Punct & Radicals
        if x >= 0x2e80 and x <= 0x33ff:
                return True

        # Fullwidth Latin Characters
        elif x >= 0xff00 and x <= 0xffef:
                return True

        # CJK Unified Ideographs &
        # CJK Unified Ideographs Extension A
        elif x >= 0x4e00 and x <= 0x9fbb:
                return True
        # CJK Compatibility Ideographs
        elif x >= 0xf900 and x <= 0xfad9:
                return True

        # CJK Unified Ideographs Extension B
        elif x >= 0x20000 and x <= 0x2a6d6:
                return True

        # CJK Compatibility Supplement
        elif x >= 0x2f800 and x <= 0x2fa1d:
                return True

        else:
                return False
                
def split_zh_en (element, tag):
        zh_gather = ""
        en_gather = ""
        for c in shape_tag(element, tag)["value"]:
                if is_zh (c):
                        zh_gather += c
                elif not is_zh (c):
                        en_gather += c
                else:
                        pass

        if en_gather != "" and zh_gather != "":
          
          tag = [{
            'id'   : element.attrib['id'],
            'key'  : "en",
            'value': en_gather.lstrip(" "),
            'type' : tag.attrib['k']
    }, {
            'id'   : element.attrib['id'],
            'key'  : "zh",
            'value': zh_gather,
            'type' : tag.attrib['k']
    }]
          return tag


def shape_tag(element, tag): 
    tag = {
        'id'   : element.attrib['id'],
        'key'  : tag.attrib['k'],
        'value': tag.attrib['v'],
        'type' : 'regular'
    }
    
    if LOWER_COLON.match(tag['key']):
        tag['type'], _, tag['key'] = tag['key'].partition(':')
    elif PROBLEMCHARS.search(tag['key']):
        pass
    return tag

def shape_way_node(element, i ,nd):
    tag = {
        'id' : element.attrib['id'],
        'node_id': nd.attrib['ref'],
        'position': i
        }
    return tag
    
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""


    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements    
    tag_list1 = []
    tag_list2 = []
    if element.tag == 'node':
        if float(element.attrib["lat"]) > 22.1288990483 and float(element.attrib["lat"]) < 22.5940489229:
            if float(element.attrib["lon"]) > 113.7498330311 and float(element.attrib["lon"]) < 114.4761440615:
                for key in NODE_FIELDS:
                    node_attribs[key] = element.attrib[key]
                try:
                    for tag in element.iter('tag'):
                        tag_list1.append(shape_tag(element, tag))
                        if tag.attrib['k'] == 'operator':
                            tag_list1.extend(split_zh_en(element, tag))
                    return {'node': node_attribs, 'node_tags': tag_list1}
                except TypeError:
                    pass
            else:
                pass        
        else:
            pass        
    elif element.tag == 'way':
      for key in WAY_FIELDS:
          way_attribs[key] = element.attrib[key]
      for i, nd in enumerate(element.iter('nd')):
          way_nodes.append(shape_way_node(element, i ,nd))
      for tag in element.iter('tag'):
          tag_list2.append(shape_tag(element, tag))
      return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tag_list2}

# YOUR CODE HERE

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

 
#def validate_element(element, validator, schema=SCHEMA):
#    """Raise ValidationError if element does not match schema"""
#   if validator.validate(element, schema) is not True:
#        field, errors = next(validator.errors.iteritems())
#        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
#        error_string = pprint.pformat(errors)
        
#        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

#        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
    

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
