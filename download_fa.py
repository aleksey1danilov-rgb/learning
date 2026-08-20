import urllib.request

urls = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.1/css/all.min.css',
    'https://use.fontawesome.com/releases/v6.5.1/css/all.css'
]

for url in urls:
    try:
        urllib.request.urlretrieve(url, 'app/static/css/font-awesome.min.css')
        print('OK:', url)
        break
    except Exception as e:
        print('Error:', url, e)
