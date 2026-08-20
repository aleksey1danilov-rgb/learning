import os

folder = 'app/templates'
old_link = 'https://cdn.jsdelivr.net/npm/font-awesome@6.5.0/css/all.min.css'
new_link = '/static/css/font-awesome.min.css'

for filename in os.listdir(folder):
    if not filename.endswith('.html'):
        continue
    path = os.path.join(folder, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old_link in content:
        content = content.replace(old_link, new_link)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated:', filename)

print('Done!')
