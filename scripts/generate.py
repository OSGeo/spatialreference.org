#!/usr/bin/env python3

import json
import os, shutil, sys
import re
from itertools import groupby
from pathlib import Path
from datetime import date
from string import Template

from pygments.lexer import RegexLexer
from pygments.token import *
from pygments import highlight
from pygments.formatters import HtmlFormatter

import jinja2

import pyproj
#from contextlib import redirect_stdout

class WKTLexer(RegexLexer):
    name = 'wkt'
    aliases = ['wkt']
    filenames = ['*.wkt']

    tokens = {
        'root': [
            (r'^This CRS cannot be written.*', Error),
            (r'\s+', Text),
            (r'[{}\[\]();,-.]+', Punctuation),
            (r'^(PROJCS|GEOGCS|GEOCCS|VERT_CS|COMPD_CS)\b', Generic.Heading),
            (r'^(PROJCRS|GEOGCRS|GEODCRS|VERTCRS|COMPOUNDCRS)\b', Generic.Heading),
            (r'(PROJCS|GEOGCS|GEOCCS|VERT_CS)\b', Keyword.Declaration),
            (r'(PROJCRS|GEOGCRS|GEODCRS|VERTCRS)\b', Keyword.Declaration),
            (r'(PARAMETER|PROJECTION|SPHEROID|DATUM|GEOGCS|AXIS|VERT_DATUM)\b', Keyword),
            (r'(ELLIPSOID)\b', Keyword),
            (r'(METHOD)\b', Keyword),
            (r'(PRIMEM|UNIT|TOWGS84)\b', Keyword.Constant),
            (r'([A-Z]+UNIT)\b', Name.Class),
            (r'(east|west|north|south|up|down|geocentric[XYZ])\b', Literal.String),
            (r'(EAST|WEST|NORTH|SOUTH|UP|DOWN)\b', Literal.String),
            (r'(ORDER|SCOPE|AREA|BBOX)\b', Keyword.Constant),
            (r'(BASEGEOGCRS|CONVERSION|CS|USAGE|VDATUM)\b', Keyword.Declaration),
            (r'([Cc]artesian|[Ee]llipsoidal|[Vv]ertical)\b', Literal.String),
            (r'(AUTHORITY)\b', Name.Builtin),
            (r'(ID)\b', Name.Builtin),
            (r'[$a-zA-Z_][a-zA-Z0-9_]*', Name.Other),
            (r'[0-9][0-9]*\.[0-9]+([eE][0-9]+)?[fd]?', Number.Float),
            (r'0x[0-9a-fA-F]+', Number.Hex),
            (r'[0-9]+', Number.Integer),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
        ]
    }

def dump_f(dst_folder, file, txt):
    dst_file = dst_folder + '/' + file
    with open(dst_file, 'w') as dst:
        dst.write(txt)

def dump(dst_folder, txt):
    Path(dst_folder).mkdir(parents=True, exist_ok=True)
    return dump_f(dst_folder, 'index.html', txt)

def add_frozen_crss(crss):
    return crss
    # Do not add it. It is too big in GitHub pages.
    parent = Path(__file__).parent.resolve()
    for domain in ['iau2000.json', 'sr-org.json']:
        with open(f'{parent}/{domain}', 'r') as fp:
            dom = json.load(fp)
            crss = [*crss, *dom]
    return crss

def make_crslist(dest_dir):
    dest_file = f'{dest_dir}/crslist.json'

    pyproj.show_versions()

    crs_list = pyproj.database.query_crs_info(allow_deprecated=True)

    def adapt_crs(crs):
        crs = crs._asdict()
        crs['type'] = str(crs['type']).replace('PJType.', '')
        return crs

    crss = sorted(
        [adapt_crs(crs) for crs in crs_list if crs.area_of_use],
        key=lambda d: d['auth_name'] + d['code'].zfill(7)
    )

    print('\nAnalysis of duplicated codes')
    codes = [d['auth_name'] + ':' + d['code'] for d in crss]
    unique = []
    for code in codes:
        if code in unique:
            print(code + ' is duplicated')
        else:
            unique.append(code)

    crss = add_frozen_crss(crss)

    with open(dest_file, 'w') as fp:
        json.dump(crss, fp, indent=2)

    return crss

def make_mapping(home_dir):
    today = date.today().isoformat()
    mapping = {'home_dir': home_dir,
               'last_revised': os.getenv('LAST_REVISED', '-missing-'),
               'proj_version': os.getenv('PROJ_VERSION', '-missing-'),
               'built_date': today,}
    return mapping

def make_wkts(crs):
    try:
        output_axis_rule = True if crs.is_projected else None
        pretty = crs.to_wkt(version='WKT1_GDAL', pretty=True, output_axis_rule=output_axis_rule)
        ogcwkt = crs.to_wkt(version='WKT1_GDAL', pretty=False, output_axis_rule=output_axis_rule)
    except:
        pretty = 'This CRS cannot be written as WKT1_GDAL'
        ogcwkt = 'This CRS cannot be written as WKT1_GDAL'

    pretty2 = crs.to_wkt(version='WKT2_2019', pretty=True, output_axis_rule=output_axis_rule)

    #syntax_pretty = highlight(pretty, WKTLexer(), HtmlFormatter(cssclass='syntax', nobackground=True))
    #syntax_pretty2 = highlight(pretty2, WKTLexer(), HtmlFormatter(cssclass='syntax', nobackground=True))

    return (pretty, ogcwkt, pretty2)

class Generator:
    """ class to deal with Jinja2 templates rendering """
    def __init__(self):
        self.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates'),
            undefined=jinja2.StrictUndefined,
            trim_blocks=False,
            lstrip_blocks=True,)

    def render(self, tmpl, dest, mapping):
        if os.path.isdir(dest) or dest[-1] == '/':
            dest = os.path.join(dest, 'index.html')
        directory = os.path.dirname(dest)
        Path(directory).mkdir(parents=True, exist_ok=True)

        template = self.jinja2_env.get_template(tmpl)
        output_from_parsed_template = template.render(mapping)

        with open(dest, "w") as fh:
            fh.write(output_from_parsed_template)


def main():
    dest_dir = os.getenv('DEST_DIR', '.')
    g = Generator()

    crss = make_crslist(dest_dir)

    # copy some literal files, not modified
    for literal in ['base.js', 'base.css', 'sr_logo.jpg', 'favicon.ico']:
        shutil.copy(f'./templates/{literal}', dest_dir)

    authorities = {
        key: len(list(group))
        for key, group in groupby(crss, lambda x: x['auth_name'])
    }
    count_authorities = {
        f'count_{key.lower().replace("-","_")}' : str(value)
        for key, value in authorities.items()
    }


    mapping = make_mapping('.') | count_authorities
    g.render('index.tmpl', f'{dest_dir}', mapping)
    g.render('about.tmpl', f'{dest_dir}/about.html', mapping)
    mapping = make_mapping('..')
    g.render('ref.tmpl', f'{dest_dir}/ref/', mapping)

    mapping = make_mapping('../..')
    for authority in authorities.keys():
        mapping['authority'] = authority
        g.render('authority.tmpl', f'{dest_dir}/ref/{authority.lower()}/', mapping)

    mapping_ref = make_mapping('../../..')
    mapping_wkt = make_mapping('../../..')

    count = 0
    total = len(crss)
    sys.stdout.write(f'Processing {total} CRSs:\n')

    for id, c in enumerate(crss):
        count += 1
        if count > 100:
            pass #break
        if count % int(total/100) == 0 or total == count:
            sys.stdout.write('\r')
            sys.stdout.write("[%-20s] %d%%" % ('='*int(count/total*20), int(count/total*100)))
            sys.stdout.flush()

        code = c["code"]
        auth_name = c["auth_name"]
        name = c["name"]
        auth_lowercase = auth_name.lower()
        error = ''
        show_list = True
        crs = None
        if "ogcwkt" in c:
            show_list = False
            try:
                crs = pyproj.CRS.from_user_input(c["ogcwkt"])
            except Exception as e:
                print('error with', auth_name, code, name)
                error = str(e)
        else:
            crs = pyproj.CRS.from_authority(auth_name=auth_name, code=code)

        epsg_scaped_name = re.sub(r'[^0-9a-zA-Z]+', '-', name) if auth_name == "EPSG" else ''

        aou = c.get("area_of_use")
        bounds = ', '.join([str(x) for x in aou[:4]]) if aou else 'Unknown'
        full_name = lambda c: f'{c["auth_name"]}:{c["code"]} : {c["name"]}'
        url = lambda c: f'../../../ref/{c["auth_name"].lower()}/{c["code"]}'

        axes = {}
        if crs:
            projjson = crs.to_json(pretty=False)
            try:
                js = json.loads(projjson)
                if 'components' in js:
                    components = js['components'] # to support compound CRSs
                else:
                    components = [js]
                axes_arr = []
                for comp in components:
                    axes_arr += [x for x in comp['coordinate_system']['axis']]
                if len(axes_arr) > 0:
                    axes['directions'] = ', '.join([x['direction'] for x in axes_arr])
                    axes['names'] = ', '.join([x['name'] for x in axes_arr])
                    axes['abbr'] = ','.join([x['abbreviation'] for x in axes_arr])
                    units = [x['unit']['name'] if 'name' in x['unit'] else x['unit'] for x in axes_arr]
                    axes['units'] = units[0] if all(e == units[0] for e in units) else ', '.join(units)
            except:
                pass

        mapping = mapping_ref | {
               'authority': auth_name,
               'code': code,
               'name': name,
               'area_name': aou[4] if aou else 'Unknown',
               'epsg_scaped_name': epsg_scaped_name,
               'deprecated': c.get("deprecated", False),
               'crs_type': c.get("type", '--'),
               'bounds': bounds,
               'bounds_map': bounds if aou and auth_lowercase[0:3] != 'iau' else None,
               'scope': crs.scope if crs else '--',
               'prev_full_name': full_name(crss[id-1]),
               'prev_url': url(crss[id-1]),
               'next_full_name': full_name(crss[(id+1)%len(crss)]),
               'next_url': url(crss[(id+1)%len(crss)]),
               'error': error,
               'show_list': show_list,
               'projection_method_name': c.get("projection_method_name", ''),
               'axes': axes,
        }
        dir = f'{dest_dir}/ref/{auth_lowercase}/{code}'
        g.render('crs.tmpl', f'{dir}/', mapping)

        if not crs:
            ogcwkt = c.get("ogcwkt")
            dump_f(f'{dir}', 'ogcwkt.txt', ogcwkt)
            dump(f'{dir}/ogcwkt', ogcwkt) # backwards compatible
        else:
            pretty, ogcwkt, pretty2 = make_wkts(crs)

            mapping = mapping_wkt | {
                'authority': auth_name,
                'code': code,
                'wkt_type': '',
                'syntax_html': '', #syntax_pretty,
                'wkt_filename': './prettywkt.txt',
            }

            g.render('htmlwkt.tmpl', f'{dir}/wkt.html', mapping)
            dump_f(f'{dir}', 'prettywkt.txt', pretty)
            dump(f'{dir}/prettywkt', pretty) # backwards compatible
            dump(f'{dir}/ogcwkt', ogcwkt) # backwards compatible

            mapping = mapping | {
                'wkt_type': ' - WKT2',
                'wkt_filename': './prettywkt2.txt',
            }
            g.render('htmlwkt.tmpl', f'{dir}/wkt2.html', mapping)
            dump_f(f'{dir}', 'prettywkt2.txt', pretty2)

            try:
                esri = crs.to_wkt(version='WKT1_ESRI')
            except:
                esri = 'This CRS cannot be written as WKT1_ESRI'
            dump_f(f'{dir}', 'esriwkt.txt', esri)

            # projjson generated above for the axes
            dump_f(f'{dir}', 'projjson.json', projjson)

            try:
                proj4 = crs.to_proj4()
            except:
                proj4 = ''
            dump_f(f'{dir}', 'proj4.txt', proj4)

    return 0


if __name__ == '__main__':
    exit(main())