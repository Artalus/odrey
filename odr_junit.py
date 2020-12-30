#!/usr/bin/env python3

import argparse
import json
import os
from typing import *

from xml.etree import ElementTree as ET
from xml.dom import minidom

Json = Dict[str, Any]

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('input_dir')
    p.add_argument('output_file')
    p.add_argument('--json_extension', default='json')
    return p.parse_args()


def main() -> None:
    args = parse_args()
    jsons = collect_jsons(args.input_dir, args.json_extension)
    x = json_to_xml(jsons)
    write_xml(x, args.output_file)


def collect_jsons(input_dir: str, file_extension: str) -> List[Json]:
    jsons = []
    for dirpath, _, files in os.walk(input_dir):
        for f in files:
            if f.endswith(file_extension):
                with open(os.path.join(dirpath, f)) as fp:
                    jsons.append(json.load(fp))
    return jsons

def json_to_xml(jsons: List[Json]) -> ET.Element:
    '''
<testsuite tests="3">
    <testcase classname="foo1" name="ASuccessfulTest"/>
    <testcase classname="foo2" name="AnotherSuccessfulTest"/>
    <testcase classname="foo3" name="AFailingTest">
        <failure type="NotEnoughFoo"> details about failure </failure>
    </testcase>
</testsuite>
'''
    '''
<?xml version="1.0" encoding="UTF-8"?>
<testsuites disabled="" errors="" failures="" name="" tests="" time="">
    <testsuite disabled="" errors="" failures="" hostname="" id=""
               name="" package="" skipped="" tests="" time="" timestamp="">
        <properties>
            <property name="" value=""/>
        </properties>
        <testcase assertions="" classname="" name="" status="" time="">
            <skipped/>
            <error message="" type=""/>
            <failure message="" type=""/>
            <system-out/>
            <system-err/>
        </testcase>
        <system-out/>
        <system-err/>
    </testsuite>
</testsuites>
'''
    # create the file structure
    root = ET.Element('testsuites')
    known_functions = dict()
    # suite.set('tests', str(len(jsons)))
    for j in jsons:
        tname = j['target']
        for c in j['collisions']:
            fname = c['name']
            if fname not in known_functions:
                t = known_functions[fname] = ET.SubElement(root, 'testsuite')
                t.set('name', fname)
            suite = known_functions[fname]
            case = ET.SubElement(suite, 'testcase')
            case.set('name', tname)

            files = ['%s: %s' % (x['filename'], x['data']) for x in c['entries']]
            files_str = '\n'.join(files)

            failure = ET.SubElement(case, 'failure')
            failure.set('type', 'OdrViolation')
            failure.text = f'CMake target: {tname}\nSymbol `{fname}` definition differs in files:\n{files_str}'

            serr = ET.SubElement(case, 'system-err')
            jdump = json.dumps(c['entries'], indent=2)
            serr.text = jdump
    return root


def write_xml(xmldata: ET.Element, filename: str) -> None:
    xmlstr = prety_xml(xmldata)
    with open(filename, "w") as f:
        f.write(xmlstr)


# silly hack to get indented xml without LXML package
def prety_xml(elem: ET.Element) -> str:
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ") # type: ignore


if __name__ == "__main__":
    main()
