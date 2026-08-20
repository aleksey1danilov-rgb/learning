import os

folder = 'app/templates'
fa_css = '<link rel="stylesheet" href="/static/css/font-awesome.min.css">'
fa_fonts = '<link rel="stylesheet" href="/static/css/fa-fonts.css">'

for filename in os.listdir(folder):
    if not filename.endswith('.html'):
        continue
    path = os.path.join(folder, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Если нет font-awesome — добавляем оба
    if 'font-awesome.min.css' not in content:
        # Вставляем перед </head>
        content = content.replace('</head>', '    ' + fa_css + '\n    ' + fa_fonts + '\n</head>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Added CSS:', filename)
    elif 'fa-fonts.css' not in content:
        # Если есть font-awesome, но нет fa-fonts
        content = content.replace(fa_css, fa_css + '\n    ' + fa_fonts)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Added fa-fonts:', filename)

print('Done!')
