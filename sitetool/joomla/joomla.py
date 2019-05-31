import yaml
import requests_html
import webbrowser
import argparse
import json
import itertools
from collections import defaultdict


class JoomlaSite():
    '''
    '''

    url = None
    username = None
    password = None

    def connect_joomla(self):
        pass

    def joomla_info(self):

        #data = yaml.load(open('/home/jjmontes/.jpat', 'r'))

        session = requests_html.HTMLSession()

        # Request loging page
        url = '%s/administrator/index.php' % (self.url)
        r = session.get(url)

        # Extract form fields
        data = {}
        inputs = r.html.find('input')
        for input in inputs:
            key = input.attrs['name']
            value = input.attrs.get('value', None)
            data[key] = value
        data['username'] = self.username
        data['passwd'] = self.password
        data['option'] = 'com_login'
        data['task'] = 'login'
        #data['return']

        # Login
        url = '%s/administrator/index.php' % (self.url)
        r = session.post(url, data=data)

        # Get System Info in JSON format
        url = '%s/administrator/index.php?option=com_admin&view=sysinfo&format=json' % (self.url)
        r = session.get(url)

        result = r.json()

        return result

    def extensions_list(self):
        pass

    def extensions_install(self):
        pass

    def extensions_upgradeall(self):
        pass


class JoomlaInfoCommand():
    '''
    '''

    COMMAND_DESCRIPTION = 'Show information about Joomla installations'

    def __init__(self, sitetool):
        self.st = sitetool
        self.src = None

    def parse_args(self, args):

        parser = argparse.ArgumentParser(prog="sitetool sites", description=self.COMMAND_DESCRIPTION)
        parser.add_argument("source", default="*:*", nargs='?', help="site:env - site environment filter")
        parser.add_argument("-j", "--json", action="store_true", default=False, help="dump all information in json format")
        parser.add_argument("-v", "--verbose", action="store_true", default=False, help="show more information")
        parser.add_argument("-e", "--extensions", action="store_true", default=False, help="list extensions")

        args = parser.parse_args(args)

        self.src = args.source
        self.json = args.json
        self.verbose = args.verbose
        self.extensions = args.extensions

    def run(self):
        """
        """

        self.ctx = self.st.config

        sites = self.st.sites.list_sites(self.src)

        count = 0
        for site in sorted(sites, key=lambda x: (x['site']['name'], x['name'])):

            if 'joomla' not in site: continue

            count += 1

            key = (site['site']['name'], site['name'])
            label = site['url'] if 'url' in site else '-'

            info = site['joomla'].joomla_info()

            # If JSON, print the result
            if self.json:
                print(json.dumps(info, indent=4))
                continue

            if not self.verbose:
                print("%-20s %s (%d extensions) - PHP %s" % (
                    ("%s:%s" % (site['site']['name'], site['name'])),
                    info['info']['version'],
                    len(info['extensions']),
                    info['info']['phpversion'] ))

            else:
                print("%-20s" % (("%s:%s" % (site['site']['name'], site['name']))))

                print("  %s (%d extensions) - PHP %s" % (
                    info['info']['version'],
                    len(info['extensions']),
                    info['info']['phpversion'] ))

                extensions = info['extensions'].keys()
                ext_groups = defaultdict(lambda: 0)
                for e in info['extensions'].values():
                    ext_groups[e['type']] += 1
                ext_text = ", ".join(['%s: %d' % (k, c) for k, c in ext_groups.items()])

                print("  %d extensions (%s)" % (len(extensions), ext_text))

                directories = info['directories'].items()
                dir_non_writable = [d for d in directories if not d[1]['writable']]
                print("  %d directories (%d non writable)" % (
                    len(directories), len(dir_non_writable)))

                print("  %s" % (site['joomla'].url))

            if self.extensions:
                print("  Extensions (%d):" % len(info['extensions']))
                for key, e in sorted(info['extensions'].items(), key=lambda x: (x[1]['type'], x[0])):
                    print("    %-34s %8s %s %10s" % (
                        key, e['version'],
                        'D' if e['state'] != 'Enabled' else ' ',
                        e['type']))

        print("Listed Joomla sites: %d" % (count))
