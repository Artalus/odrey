#!/usr/bin/env python3

import argparse
import json
import os
import lxml.etree as ET


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('input_dir')
    p.add_argument('output_file')
    return p.parse_args()


def main():
    args = parse_args()
    jsons = collect_jsons(args.input_dir)
    x = json_to_xml(jsons)
    write_xml(x, args.output_file)


def collect_jsons(input_dir):
    jsons = []
    for dirpath, _, files in os.walk(input_dir):
        for f in files:
            if f.endswith('.odr.json'):
                with open(f'{dirpath}/{f}') as fp:
                    jsons.append(json.load(fp))
    return jsons

def json_to_xml(jsons):
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

            files = ['%s size=%s' % (x['file'], x['size']) for x in c['entries']]
            files_str = '\n'.join(files)

            failure = ET.SubElement(case, 'failure')
            failure.set('type', 'OdrViolation')
            failure.text = f'CMake target: {tname}\nFunction {fname} definition differs in files:\n{files_str}'

            serr = ET.SubElement(case, 'system-err')
            jdump = json.dumps(c['entries'], indent=2)
            serr.text = jdump
    return root


def write_xml(xmldata, filename):
    xmlstr = ET.tostring(xmldata, pretty_print=True)
    with open(filename, "wb") as f:
        f.write(xmlstr)


if __name__ == "__main__":
    main()
