import os

folder = 'app/templates'
link = '<link rel="stylesheet" href="/static/css/fa-fonts.css">'
font_awesome = '/static/css/font-awesome.min.css'

for filename in os.listdir(folder):
    if not filename.endswith('.html'):
        continue
    path = os.path.join(folder, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Если уже есть fa-fonts.css — пропускаем
    if 'fa-fonts.css' in content:
        continue
    
    # Добавляем после font-awesome.min.css
    if font_awesome in content:
        content = content.replace(
            '<link rel="stylesheet" href="' + font_awesome + '">',
            '<link rel="stylesheet" href="' + font_awesome + '">\n    ' + link
        )
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated:', filename)

print('Done!')
