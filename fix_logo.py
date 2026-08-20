import os

folder = 'app/templates'
old = '<i class="fas fa-graduation-cap"></i>'
new = '<span style="font-size:32px;line-height:1;">🎓</span>'

for filename in os.listdir(folder):
    if not filename.endswith('.html'):
        continue
    path = os.path.join(folder, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated:', filename)

print('Done!')
