import urllib.request

URL = 'https://raw.githubusercontent.com/notAidven/community-solar-map/master/community_solar_map.html'

print(f'Fetching {URL} ...')
html = urllib.request.urlopen(URL).read().decode('utf-8')
print(f'Fetched {len(html):,} characters')

MARKER = 'const STATES_DATA = '
start = html.index(MARKER) + len(MARKER)

depth = 0
end = start
for i in range(start, len(html)):
    c = html[i]
    if c == '{':
        depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end == start:
    raise ValueError('STATES_DATA not found or unterminated in source HTML')

states_json = html[start:end]
print(f'Extracted {len(states_json):,} characters of STATES_DATA')

with open('states_data_output.js', 'w', encoding='utf-8') as f:
    f.write('const STATES_DATA = ')
    f.write(states_json)
    f.write(';')

print('Written to states_data_output.js')

# Quick sanity check: count features
import json
data = json.loads(states_json)
print(f'Features in GeoJSON: {len(data.get("features", []))}')
