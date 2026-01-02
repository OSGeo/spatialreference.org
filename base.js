function init_map(area_of_use) {
    if (!area_of_use) return;
    let map = L.map('map').setView([0, 0], 1);
    let osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);
    let rect = makeRectangle(area_of_use, 'green').addTo(map);
    map.fitBounds(rect.getBounds());
}

function makeRectangle (area_of_use, color) {
    let bounds = null;

    let off0 = 0, off2 = 0;
    if (area_of_use[0] < area_of_use[2]) {
    } else if (Math.abs(area_of_use[0]) < Math.abs(area_of_use[2])) {
        off2 = 360
    } else {
        off0 = 360
    }
    bounds = [[area_of_use[1], area_of_use[0]-off0], [area_of_use[3], area_of_use[2]+off2]];

    return L.rectangle(bounds, {color: color});
}

function type_abbr(type) {
    if (type == 'PROJECTED_CRS') {
        return 'P';
    } else if (type == 'GEOGRAPHIC_2D_CRS') {
        return 'G2D';
    } else if (type == 'GEOGRAPHIC_3D_CRS') {
        return 'G3D';
    } else if (type == 'GEOGRAPHIC_CRS') {
        return 'G';
    } else if (type == 'GEODETIC_CRS') {
        return 'GD';
    } else if (type == 'GEOCENTRIC_CRS') {
        return 'GC';
    } else if (type == 'VERTICAL_CRS') {
        return 'V';
    } else if (type == 'COMPOUND_CRS') {
        return 'C';
    }
    return '';
}

function generate_entries(data, home_dir, from, number, container) {
    for (let i = from; i < from + number; i++) {
        if (i >= data.length)
            break;
        const crs = data[i]
        let li = document.createElement('li');
        let a = document.createElement('a');
        a.href = `${home_dir}/ref/${crs.auth_name.toLowerCase()}/${crs.code}/`;
        a.innerText = `${crs.auth_name}:${crs.code}`;
        li.appendChild(a);
        name_broken = crs.name.replaceAll('_', '<wbr>_')
        li.innerHTML += `: ${name_broken}`;
        const t = type_abbr(crs.type);
        if (t) {
            li.innerHTML += ` <small class="type_abbr" title="${crs.type}">[${t}]</small>`;
        }
        if (crs.deprecated) {
            li.innerHTML += ' <span class="deprecated_in_list">(deprecated)</span>';
        }
        container.appendChild(li);
    }
}

function update_pages_links(page, search, max_pages) {
    let s = search ? `&search=${search}` : '';
    function doit (page_number, class_name, show) {
        let prev = document.querySelectorAll(class_name);
        Array.from(prev).forEach(e => {
            if (!show) {
                e.classList.add('is-disabled');
            } else {
                e.classList.remove('is-disabled');
                e.href = `?page=${page_number}${s}`;
            }
        });
    }
    page = Number(page)
    doit(page - 1, '.prev_page', page > 1)
    doit(page + 1, '.next_page', page < max_pages)
    Array.from(document.querySelectorAll('.next_page')).forEach(e => e.href = `?page=${page + 1}${s}`);
}

function paramsToDic(location) {
    const url = new URL(location);
    let dic = {};
    for (let k of url.searchParams.keys()) {
        dic[k] = url.searchParams.get(k);
    }
    return dic;
}

function filter_data(data, search, authority) {
    if (!search || !search.trim()) {
        search = '';
    }
    let s = search.toUpperCase().split(' ');
    let no_s = s.filter(elem => elem[0] == '-').map(elem => elem.substring(1));
    s = s.filter(elem => elem[0] != '-');

    let auth_code = [null, s.length ? s[0] : null];
    if (s.length == 1 && s[0].split(':').length == 2) {
        auth_code = s[0].split(':');
    }

    let r = data.filter(d => {
        let name = d.name.toUpperCase();
        let outlier = s.find(elem => !name.includes(elem));
        if (outlier == "WGS84") {
            // many people searches WGS84, however the EPSG name has a space: "WGS 84"
            const s2 = s.map(elem => elem == "WGS84" ? "WGS 84" : elem);
            outlier = s2.find(elem => !name.includes(elem));
        }
        let valid = (outlier == undefined);
        if (no_s.find(elem => name.includes(elem)) != undefined) {
            valid = false
        }

        if (!isNaN(auth_code[1]) && d.code === auth_code[1] && (!auth_code[0] || d.auth_name === auth_code[0])) {
            // filter by code or auth:code
            valid = true;
        }
        if (authority && authority !== d.auth_name) {
            valid = false;
        }
        return valid;
    });
    return r;
}

function init_ref(home_dir, authority) {
    fetch(home_dir + '/crslist.json', {
        method: "GET",
    })
    .then(response => response.json())
    .then(data => {
        let entries_per_page = 50;
        let params = paramsToDic(window.location);
        let page = params.page || 1;
        data = filter_data(data, params.search, authority);
        document.querySelector('#found').innerText = data.length;
        if(params.search && params.search.trim()) {
            document.querySelector('#searched_text_span').classList.remove("hidden")
            document.querySelector('#searched_text').textContent = params.search;

            const forms = document.querySelectorAll('form')
            Array.from(forms).forEach(form => form.elements['search'].value = params.search);

            only_searching = document.querySelector('.only_searching')
            if (only_searching) {
                only_searching.href += params.search.trim();
            }
        }
        let container = document.querySelector('#list1 ul');
        generate_entries(data, home_dir, (page - 1) * entries_per_page, entries_per_page/2, container);
        container = document.querySelector('#list2 ul');
        generate_entries(data, home_dir, (page - 0.5) * entries_per_page, entries_per_page/2, container);
        update_pages_links(page, params.search, Math.ceil(data.length / entries_per_page))
    });
}

function not_found(home_dir) {
    // This function is called in case of a 404, trying to redirect old links.
    // something like https://spatialreference.org/ref/epsg/anguilla-1957-british-west-indies-grid/
    const loc = window.location;
    const match = loc.pathname.match(/.*?\/ref\/(.*?)\/(.*)/);
    if (!match || match.length != 3) {
        return;
    }
    const auth_in_url = match[1];
    const name_in_url = match[2].endsWith('/') ? match[2].slice(0, -1) : match[2];

    // Not supported anymore. Give the user at least the JSON file with the data.
    if (auth_in_url == "sr-org" || auth_in_url == "iau2000") {
        const url = `https://github.com/OSGeo/spatialreference.org/blob/master/scripts/${auth_in_url}.json`;
        const text = `Sorry, ${auth_in_url} is not supported anymore. You can get old data from file<br>` +
                     `<a href="${url}" target="_blank">${url}</a>`;
        document.querySelector('#not_found_cont').innerHTML = text;
        return;
    }

    // It could be an old link. Let's analyze it
    fetch(home_dir + '/crslist.json', {
        method: "GET",
    })
    .then(response => response.json())
    .then(data => {
        let r = data.filter(d => {
            if (d.auth_name.toLowerCase() != auth_in_url)
                return false;
            const scaped_name = d.name.replace(/[^0-9a-zA-Z]+/g, '-').toLowerCase();
            return scaped_name == name_in_url;
        });
        if (r.length == 1) {
            const d = r[0];
            const url = `${loc.origin}/ref/${auth_in_url}/${d.code}`;
            const text = `However, apparently you want to visit<br><br>` +
                         `${d.auth_name}:${d.code}<br>${d.name}<br><br>` +
                         `Redirecting to <a href="${url}">${url}</a>`;
            document.querySelector('#not_found_cont').innerHTML = text;
            setTimeout(() => location.assign(url), 5000);
        }
    });
}

function download_prj(name, file) {
    if (name && name !=='') {
      var link = document.createElement('a');
      link.download = name;
      link.href = file;
      link.click();
    }
}

function lexer_from_python() {
    const Error = 'err';
    const Text = '';
    const Punctuation = 'p';
    const Generic = {Heading: 'gh'};
    const Keyword = {Declaration: 'kd', Constant: 'kc'}; // Keyword='k'
    const Name = {Class: 'nc', Builtin: 'nb', Other: 'no'};
    const Literal = {String: 's'};
    const Number = {Float: 'mf', Hex: 'mh', Integer: 'mi'};
    const String = {Double: 's2', Single: 's1'};

    function r(rx, type) {
        if (type == Keyword)
            type = 'k';
        let res = {cls:type};
        res.regex = rx instanceof RegExp ? rx : new RegExp(rx.replaceAll('\b', '\\b'), 'y');
        return res;
    }

    // just removed the initial "r" from every line, and add a few extra \ in Text and Punctuation
    const lexer = [
        r('^This CRS cannot be written.*', Error),
        r('\\s+', Text),
        r('[{}\\[\\]();,-.]+', Punctuation),
        r('^(PROJCS|GEOGCS|GEOCCS|VERT_CS|COMPD_CS)\b', Generic.Heading),
        r('^(PROJCRS|GEOGCRS|GEODCRS|VERTCRS|COMPOUNDCRS)\b', Generic.Heading),
        r('(PROJCS|GEOGCS|GEOCCS|VERT_CS)\b', Keyword.Declaration),
        r('(PROJCRS|GEOGCRS|GEODCRS|VERTCRS)\b', Keyword.Declaration),
        r('(PARAMETER|PROJECTION|SPHEROID|DATUM|GEOGCS|AXIS|VERT_DATUM)\b', Keyword),
        r('(ELLIPSOID)\b', Keyword),
        r('(METHOD)\b', Keyword),
        r('(PRIMEM|UNIT|TOWGS84)\b', Keyword.Constant),
        r('([A-Z]+UNIT)\b', Name.Class),
        r('(east|west|north|south|up|down|geocentric[XYZ])\b', Literal.String),
        r('(EAST|WEST|NORTH|SOUTH|UP|DOWN)\b', Literal.String),
        r('(ORDER|SCOPE|AREA|BBOX)\b', Keyword.Constant),
        r('(BASEGEOGCRS|CONVERSION|CS|USAGE|VDATUM)\b', Keyword.Declaration),
        r('([Cc]artesian|[Ee]llipsoidal|[Vv]ertical)\b', Literal.String),
        r('(AUTHORITY)\b', Name.Builtin),
        r('(ID)\b', Name.Builtin),
        r('[$a-zA-Z_][a-zA-Z0-9_]*', Name.Other),
        r('[0-9][0-9]*\.[0-9]+([eE][0-9]+)?[fd]?', Number.Float),
        r('0x[0-9a-fA-F]+', Number.Hex),
        r('[0-9]+', Number.Integer),
        r('"(\\\\|\\"|[^"])*"', String.Double),
        r("'(\\\\|\\'|[^'])*'", String.Single),
    ];
    return lexer
}
function format(txt) {
    let lexer = lexer_from_python();
    const lines = txt.split('\n');
    let res = ''
    lines.forEach(line => {
        let pos = 0;
        while (line.length > 0 && pos < line.length) {
            let found = false;
            for(let l = 0; l < lexer.length; l++) {
                let lx = lexer[l];
                lx.regex.lastIndex = pos;
                const match = lx.regex.exec(line);
                if (match && match.index == pos) {
                    found = true;
                    const matched = match[0];
                    if (lexer[l].cls == '') {
                        res += matched;
                    } else {
                        res += `<span class="${lx.cls}">${matched}</span>`;
                    }
                    pos += matched.length
                    break;
                }
            }
            if (!found) {
                res += line[pos];
                pos += 1
            }
        }
        res += '\n';
    });
    let syntax = document.createElement('div');
    syntax.classList.add('syntax');
    let pre = document.createElement('pre');
    pre.innerHTML = res;
    syntax.appendChild(pre);
    return syntax;
}

function fill_prettywkt(filename) {
    let wkt = document.getElementById('wkt');
    if (!wkt.innerText) {
        fetch(filename, {
            method: "GET",
        })
        .then(response => response.text())
        .then(data => {
                let syntax = format(data);
                wkt.appendChild(syntax);
        })
    }
}
