import urllib.request
import os

os.makedirs('app/static/webfonts', exist_ok=True)

base_url = 'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.1/webfonts/'
fonts = [
    'fa-solid-900.woff2',
    'fa-solid-900.ttf',
    'fa-regular-400.woff2',
    'fa-regular-400.ttf',
    'fa-brands-400.woff2',
    'fa-brands-400.ttf',
]

for font in fonts:
    try:
        urllib.request.urlretrieve(base_url + font, 'app/static/webfonts/' + font)
        print('OK:', font)
    except Exception as e:
        print('Error:', font, e)

print('Done!')
