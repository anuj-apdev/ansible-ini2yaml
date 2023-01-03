#! /usr/bin/env python
"""Test for ini2yaml script"""
import os
import subprocess
import yaml


def remove_keys(adict, keys):
    '''Remove irrelevant keys from dict '''
    for key in keys:
        adict.pop(key, None)


def normalize(hostvars_ini, hostvars_yaml):
    '''Normalize the dicts by deleting unnneccesary key=value pairs'''
    ignored_keys = ('inventory_dir', 'inventory_file', 'omit', 'groups', 'ansible_check_mode',
                    'ansible_diff_mode', 'ansible_inventory_sources', 'ansible_connection',
                    'ansible_forks', 'ansible_python_interpretor', 'ansible_verbosity')
    remove_keys(hostvars_ini, ignored_keys)
    remove_keys(hostvars_yaml, ignored_keys)

    for key, value in hostvars_yaml.items():
        if isinstance(value, bool) and isinstance(hostvars_ini[key], str):
            # Convert to boolean according to YAML if boolean in YAML inventory
            hostvars_ini[key] = yaml.load(
                "value: " + hostvars_ini[key], Loader=yaml.FullLoader)['value']
        elif isinstance(value, dict) and isinstance(hostvars_ini[key], str):
            # Unwrap nested dicts if unwrapped in YAML inventory
            hostvars_ini[key] = yaml.load(
                "value: " + hostvars_ini[key], Loader=yaml.FullLoader)['value']
        elif isinstance(value, list) and isinstance(hostvars_ini[key], str):
            # Unwrap nested lists if unwrapped in YAML inventory
            hostvars_ini[key] = yaml.load(
                "value: " + hostvars_ini[key], Loader=yaml.FullLoader)['value']


def test_hostvars(request, tmpdir, ansible_adhoc):
    '''tests output from ini and generated yaml file's variables by printing via ansible debug'''
    ini_inventory_filename = os.path.join(
        request.fspath.dirname, 'inventory.ini')
    yaml_inventory_filename = str(tmpdir.join('inventory.yaml'))

    with open(ini_inventory_filename, 'r', encoding="utf8") as ini_inventory_file, \
            open(yaml_inventory_filename, 'w', encoding="utf8") as yaml_inventory_file:
        with subprocess.Popen(os.path.join(request.fspath.dirname,
                                           "../ini2yaml"),
                              stdin=ini_inventory_file,
                              stdout=yaml_inventory_file) as process:
            process.communicate()
            assert process.returncode == 0
    # ['hostvars']['localhost']
    ini_hostvars = yaml.load(ansible_adhoc(inventory=ini_inventory_filename).localhost.debug(
        msg='{{ hostvars.localhost | to_yaml }}').values()[0]['msg'], Loader=yaml.FullLoader)
    # ['hostvars']['localhost']
    yaml_hostvars = yaml.load(ansible_adhoc(inventory=yaml_inventory_filename).localhost.debug(
        msg='{{ hostvars.localhost | to_yaml }}').values()[0]['msg'], Loader=yaml.FullLoader)
    # print('ini-hostname -> ', ini_hostvars)
    # print('yaml-hostname -> ', yaml_hostvars)

    normalize(ini_hostvars, yaml_hostvars)

    assert ini_hostvars == yaml_hostvars
