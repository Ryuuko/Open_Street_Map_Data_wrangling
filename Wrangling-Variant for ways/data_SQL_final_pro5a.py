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
WAYS_PATH = "ways_var.csv"
WAY_NODES_PATH = "ways_nodes_var.csv"
WAY_TAGS_PATH = "ways_tags_var.csv"

id = []
thefile = open('id00.text', 'r')
for item in thefile:
    id.append(item.strip())


LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

#SCHEMA = schema.py

# Make sure the fields order in the csvs matches the column order in the sql table schema

WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

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

    
def shape_element(element, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""


    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements    
    tag_list1 = []
    tag_list2 = []
    if element.tag == 'way':
        for i, nd in enumerate(element.iter('nd')):
            if nd.attrib['ref'] not in id:
                for key in WAY_FIELDS:
                    way_attribs[key] = element.attrib[key]
                for i, nd in enumerate(element.iter('nd')):
                    way_nodes.append(shape_way_node(element, i ,nd))
                for tag in element.iter('tag'):
                    tag_list2.append(shape_tag(element, tag))
                return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tag_list2}
            else:
                pass
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
def process_map(file_in):
    """Iteratively process each XML element and write to csv(s)"""

    

    with codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

#        validator = cerberus.Validator()
        
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
    

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH)
