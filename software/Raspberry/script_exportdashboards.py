#!/usr/bin/env python
# coding=utf-8
# Created by JTProgru / JTProg
# Date: 11.03.2020
# https://jtprog.ru/

__author__ = 'jtprog'
__version__ = '0.2'
__author_email__ = 'mail@jtprog.ru'

import requests
import time
import os
import argparse
import json
import glob
import urllib3
import uuid


class Bgcolors:
    def __init__(self):
        self.get = {
            'HEADER': '\033[95m',
            'OKBLUE': '\033[94m',
            'OKGREEN': '\033[92m',
            'WARNING': '\033[93m',
            'FAIL': '\033[91m',
            'ENDC': '\033[0m',
            'BOLD': '\033[1m',
            'UNDERLINE': '\033[4m'
        }


def get_grafana_dashboards(g_url, g_token):
    dashboards_array = []
    headers = {'Authorization': str('Bearer ' + g_token), 'Content-type': 'application/json'}
    get_data_req = requests.get(g_url + '/api/search?query=&', headers=headers)

    pars_json = json.loads(get_data_req.text)
    for dash in pars_json:
        # print(dash['uri'][3::])
        dashboards_array.append(dash['uri'][3::])

    return dashboards_array


def export_grafana_dashboards(g_token, g_url, dir_path, e_dash):
    headers = {'Authorization': str('Bearer ' + g_token),
               'Content-type': 'application/json'
               }
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(dir_path, 'has been created')

    dashboard_names = get_grafana_dashboards(g_url, g_token)
    dash_count = 1

    if e_dash == 'all':
        print('I will export ALL DASHes!')
        for d in dashboard_names:
            pn = f'-{str(uuid.uuid4())}'
            dashboard_name_out = dir_path + '/' + d + pn + '.json'
            get_dashboard = requests.get(g_url + '/api/dashboards/db/' + d, headers=headers)
            try:
                f = open(dashboard_name_out, 'w')
                f.write(json.dumps(get_dashboard.json(), indent=4))
                f.close()
                print('[', dash_count, ']', d)
                dash_count += 1
            except EOFError:
                print('I cant write to file: ', EOFError)

    else:
        print('I will export {} dashbourd(s)!'.format(e_dash))
        for d in dashboard_names:
            for dd in e_dash:
                if d == dd:
                    dashboard_name_out = dir_path + '/' + d + '.json'
                    get_dashboard = requests.get(g_url + '/api/dashboards/db/' + d, headers=headers)
                    try:
                        f = open(dashboard_name_out, 'w+')
                        f.write(json.dumps(get_dashboard.json(), indent=4))
                        f.close()
                        print('[', dash_count, ']', d)
                        dash_count += 1
                    except ValueError:
                        print('I cant write to file: ', ValueError)
    #

    return export_grafana_dashboards


def import_grafana_dashboards(g_token, g_url, dir_path, i_dash):
    headers = {'Authorization': str('Bearer ' + g_token),
               'Content-type': 'application/json',
               'Accept': 'application/json'
               }
    dash_count = 1

    if i_dash == 'all':
        print('I will import ALL DASHes!')
        files = glob.glob(dir_path + "/" + "*.json")
    else:
        print('I will import %s dashbourd(s)!' % i_dash)
        for d in i_dash:
            files = glob.glob(str(dir_path) + "/" + str(d) + ".json")
    for f in files:
        d = f.split('.')[0].split('/')[1]

        with open(f, 'r') as file:
            dashboard = file.read()
            try:
                print('[{0}] Need to create an import to grafana [{1}]'.format(dash_count, f))
                datas = json.loads(dashboard)

                protocol = g_url.split(':')[0]
                if protocol == "http":
                    i__dash = requests.post(g_url + '/api/dashboards/db/', headers=headers, json=datas)
                elif protocol == "https":
                    verify = False
                    if not verify:
                        urllib3.disable_warnings()
                    i__dash = requests.post(g_url + '/api/dashboards/db/', headers=headers, json=datas, verify=verify)
                    if i__dash.status_code != 200:
                        print(i__dash.status_code)
                        exit(0)
                else:
                    print('Incorrect URL! Use url with http|https protocol')
                    exit(0)
                print(i__dash)
            except EOFError as e:
                print(e)
        dash_count += 1

    return import_grafana_dashboards


def main():
    start__time = time.time()
    parser = argparse.ArgumentParser(prog='python3 grafana-export.py -h',
                                     usage='python3 grafana-export.py {ARGS}',
                                     add_help=True,
                                     prefix_chars='--/',
                                     epilog='created by {}'.format(__author__))
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--dash', '--dashboard', nargs='+', dest='dashboard', help='Indicate a dashboard(s)',
                        default='all')
    parser.add_argument('--gurl', '--url', dest='gurl', help='URL from grafana', default=None)
    parser.add_argument('--dir', '--directory', dest='dashboards_dir', help='Indicate a folder for dashboard(s)',
                        default='CM-Shared_Grafana', metavar='folder')

    imp_group = parser.add_mutually_exclusive_group(required=False)
    imp_group.add_argument('--i', dest='imports', help='Import function', action='store_true')
    imp_group.add_argument('--import', dest='imports', help='Import function', action='store_true')

    exp_group = parser.add_mutually_exclusive_group(required=False)
    exp_group.add_argument('--e', dest='exports', help='Export function',
                           action='store_true', default=argparse.SUPPRESS)
    exp_group.add_argument('--export', dest='exports', help='Export function', action='store_true')

    results = parser.parse_args()
    dashboards_dir = results.dashboards_dir
    dashboard = results.dashboard
    #grafana_token = os.getenv("GRAFANA_TOKEN")
    grafana_token = 'eyJrIjoiVTBmTEtkazYwS3dSNDlsdEo2WkNyWFRGZzNLS0pBNUQiLCJuIjoiMjFkYXNoIiwiaWQiOjF9'
    grafana_url = 'https://grafometheus.21-school.ru/'

    #if (grafana_token is not None) and (grafana_url is not None):
    if results.exports:
         print('EXPORT function!')
         export_grafana_dashboards(grafana_token, grafana_url, dashboards_dir, dashboard)
    elif results.imports:
         print('IMPORT function')
         import_grafana_dashboards(grafana_token, grafana_url, dashboards_dir, dashboard)
    #else:
    #    print('Please add [--gurl] and/or [--gtoken] option(s).\n'
    #          'Use "--e" to export, "--i" to import dashboards as well')
    #    print('For help, use: grafana-export.py -h')
    #    exit(0)

    end__time = round(time.time() - start__time, 2)

    print("--- {} seconds ---".format(end__time))

    print(
        Bgcolors().get['OKGREEN'], "============================================================",
        Bgcolors().get['ENDC'])
    print(
        Bgcolors().get['OKGREEN'], "==========================FINISHED==========================",
        Bgcolors().get['ENDC'])
    print(
        Bgcolors().get['OKGREEN'], "============================================================",
        Bgcolors().get['ENDC'])


if __name__ == '__main__':
    main()
