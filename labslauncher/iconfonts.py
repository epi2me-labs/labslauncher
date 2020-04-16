"""Allow use of icon fonts in widgets.

Copyright (c) 2010-2015 Kivy Team and other contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from collections import OrderedDict
import json
import re

from kivy.compat import PY2

_register = OrderedDict()

if not PY2:
    unichr = chr


def register(name, ttf_fname, fontd_fname):
    """Register an Iconfont.

    :param name: font name identifier.
    :param ttf_fname: ttf filename (path)
    :param fontd_fname: fontdic filename. (See create_fontdic)
    """
    with open(fontd_fname, 'r') as f:
        fontd = json.loads(f.read())
        _register[name] = ttf_fname, fontd_fname, fontd


def icon(code, size=None, color=None, font_name=None):
    """Get an icon from iconfont.

    :param code: Icon codename (ex: 'icon-name')
    :param size: Icon size
    :param color: Icon color
    :param font_name: Registered font name. If None first one is used.

    :returns: icon text (with markups)
    """
    font = list(_register.keys())[0] if font_name is None else font_name
    font_data = _register[font]
    s = "[font=%s]%s[/font]" % (font_data[0], unichr(font_data[2][code]))
    if size is not None:
        s = "[size=%s]%s[/size]" % (size, s)
    if color is not None:
        s = "[color=%s]%s[/color]" % (color, s)

    return s


def create_fontdict_file(css_fname, output_fname):
    """Create a font dictionary file.

    Basically creates a dictionary filled with icon_code: unicode_value
    entries obtained from a CSS file.

    :param css_fname: CSS filename where font's rules are declared.
    :param output_fname: Fontd file destination
    """
    with open(css_fname, 'r') as f:
        data = f.read()
        res = _parse(data)
        with open(output_fname, 'w') as o:
            o.write(json.dumps(res))
        return res


def _parse(data):
    # find start index where icons rules start
    pat_start = re.compile('}.+content:', re.DOTALL)
    rules_start = [x for x in re.finditer(pat_start, data)][0].start()
    data = data[rules_start:]  # crop data
    data = data.replace("\\", '0x')  # replace unicodes
    data = data.replace("'", '"')  # replace quotes
    # iterate rule indices and extract value
    pat_keys = re.compile('[a-zA-Z0-9_-]+:before')
    res = dict()
    for i in re.finditer(pat_keys, data):
        start = i.start()
        end = data.find('}', start)
        key = i.group().replace(':before', '')
        try:
            value = int(data[start:end].split('"')[1], 0)
        except (IndexError, ValueError):
            continue
        res[key] = value
    return res
