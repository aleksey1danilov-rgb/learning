import os

replacements = {
    '<i class="fas fa-home"></i>': '🏠',
    '<i class="fas fa-calendar-alt"></i>': '📅',
    '<i class="fas fa-book-open"></i>': '📚',
    '<i class="fas fa-user-tie"></i>': '👤',
    '<i class="fas fa-sign-out-alt"></i>': '🚪',
    '<i class="fas fa-users"></i>': '👥',
    '<i class="fas fa-chart-bar"></i>': '📊',
    '<i class="fas fa-plus-circle"></i>': '➕',
    '<i class="fas fa-lock"></i>': '🔒',
    '<i class="fas fa-tags"></i>': '🏷️',
    '<i class="fas fa-user-cog"></i>': '⚙️',
    '<i class="fas fa-sliders-h"></i>': '🎚️',
    '<i class="fas fa-book"></i>': '📖',
    '<i class="fas fa-graduation-cap"></i>': '🎓',
    '<i class="fas fa-search"></i>': '🔍',
    '<i class="fas fa-bell"></i>': '🔔',
    '<i class="fas fa-comment-dots"></i>': '💬',
    '<i class="fas fa-chevron-down"></i>': '▼',
    '<i class="fas fa-chevron-left"></i>': '◀',
    '<i class="fas fa-chevron-right"></i>': '▶',
    '<i class="fas fa-plus"></i>': '➕',
    '<i class="fas fa-edit"></i>': '✏️',
    '<i class="fas fa-trash"></i>': '🗑️',
    '<i class="fas fa-eye"></i>': '👁️',
    '<i class="fas fa-save"></i>': '💾',
    '<i class="fas fa-times"></i>': '✕',
    '<i class="fas fa-check"></i>': '✅',
    '<i class="fas fa-file-excel"></i>': '📊',
    '<i class="fas fa-sync"></i>': '🔄',
    '<i class="fas fa-shield-alt"></i>': '🛡️',
    '<i class="fas fa-chalkboard-teacher"></i>': '👨‍🏫',
    '<i class="fas fa-user-check"></i>': '✅',
    '<i class="fas fa-user-plus"></i>': '👤➕',
    '<i class="fas fa-arrow-left"></i>': '←',
    '<i class="fas fa-arrow-right"></i>': '→',
    '<i class="fas fa-spinner"></i>': '⏳',
    '<i class="fas fa-inbox"></i>': '📥',
    '<i class="fas fa-calendar-day"></i>': '📅',
    '<i class="fas fa-exclamation-triangle"></i>': '⚠️',
    '<i class="fas fa-exclamation-circle"></i>': '⚠️',
    '<i class="fas fa-check-circle"></i>': '✅',
    '<i class="fas fa-copy"></i>': '📋',
    '<i class="fas fa-arrows-alt"></i>': '↔️',
}

folder = 'app/templates'
for filename in os.listdir(folder):
    if not filename.endswith('.html'):
        continue
    path = os.path.join(folder, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Убираем Font Awesome CSS
    content = content.replace('<link rel="stylesheet" href="/static/css/font-awesome.min.css">', '')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated:', filename)

print('Done!')
