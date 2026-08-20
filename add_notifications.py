import os

css_add = '''
        .notif-dropdown { position: fixed; top: 50px; right: 20px; width: 320px; max-height: 400px; overflow-y: auto; background: #fff; border-radius: 12px; border: 1px solid #eaedf2; box-shadow: 0 8px 32px rgba(0,0,0,0.12); z-index: 9999; padding: 10px; display: none; }
        .notif-item { padding: 10px; border-radius: 8px; cursor: pointer; border-bottom: 1px solid #f0f2f5; transition: background 0.2s; }
        .notif-item:hover { background: #f0f5ff; }
        .notif-item.unread { background: #e6f0ff; }
        .notif-item .notif-title { font-size: 12px; font-weight: 600; }
        .notif-item .notif-message { font-size: 11px; color: #5a5e6a; margin-top: 2px; }
        .notif-item .notif-time { font-size: 10px; color: #8a8f99; margin-top: 2px; }
        .notif-badge { position: absolute; top: 2px; right: 2px; width: 16px; height: 16px; background: #FF0000; color: #fff; border-radius: 50%; font-size: 9px; display: none; align-items: center; justify-content: center; font-weight: 700; }
'''

html_bell = '''<div class="top-icon" style="position:relative;" onclick="toggleNotifDropdown()">
    <i class="fas fa-bell"></i>
    <span class="notif-badge" id="notifBadge">0</span>
</div>'''

html_dropdown = '''
<div class="notif-dropdown" id="notifDropdown">
    <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 8px 8px;border-bottom:1px solid #f0f2f5;margin-bottom:4px;">
        <strong style="font-size:14px;">🔔 Уведомления</strong>
        <button onclick="markAllRead()" style="background:none;border:none;color:#0066ff;font-size:11px;cursor:pointer;">Прочитать все</button>
    </div>
    <div id="notifList"></div>
</div>'''

js_add = '''
        // УВЕДОМЛЕНИЯ
        function toggleNotifDropdown() {
            var dd = document.getElementById('notifDropdown');
            dd.style.display = dd.style.display === 'none' || dd.style.display === '' ? 'block' : 'none';
            if (dd.style.display === 'block') loadNotifications();
        }

        function loadNotifications() {
            fetch('/api/v1/admin/my/notifications', {
                headers: { 'Authorization': 'Bearer ' + token }
            })
            .then(function(r) { return r.ok ? r.json() : []; })
            .then(function(notifications) {
                var unread = notifications.filter(function(n) { return !n.is_read; });
                var badge = document.getElementById('notifBadge');
                if (badge) {
                    badge.textContent = unread.length;
                    badge.style.display = unread.length > 0 ? 'flex' : 'none';
                }
                var list = document.getElementById('notifList');
                if (!notifications.length) {
                    list.innerHTML = '<div style="text-align:center;padding:16px;color:#8a8f99;font-size:12px;">Нет уведомлений</div>';
                    return;
                }
                list.innerHTML = notifications.map(function(n) {
                    var time = n.created_at ? new Date(n.created_at.replace(' ', 'T')).toLocaleString('ru', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}) : '';
                    return '<div class="notif-item ' + (n.is_read ? '' : 'unread') + '" onclick="markRead(' + n.id + ')">' +
                        '<div class="notif-title">' + n.title + '</div>' +
                        '<div class="notif-message">' + (n.message || '') + '</div>' +
                        '<div class="notif-time">' + time + '</div>' +
                        '</div>';
                }).join('');
            });
        }

        function markRead(id) {
            fetch('/api/v1/admin/my/notifications/' + id + '/read', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token }
            })
            .then(function() { loadNotifications(); });
        }

        function markAllRead() {
            fetch('/api/v1/admin/my/notifications/read-all', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token }
            })
            .then(function() { loadNotifications(); });
        }

        function checkUpcoming() {
            fetch('/api/v1/admin/my/upcoming-notifications', {
                headers: { 'Authorization': 'Bearer ' + token }
            })
            .then(function(r) { return r.ok ? r.json() : []; })
            .then(function(notifications) {
                if (notifications.length > 0) loadNotifications();
            });
        }

        loadNotifications();
        setInterval(loadNotifications, 30000);
        setInterval(checkUpcoming, 30000);
'''

folder = 'app/templates'
target_files = ['index.html', 'calendar.html']

for filename in target_files:
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        print('Skip:', filename)
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем CSS перед </style>
    content = content.replace('</style>', css_add + '</style>')
    
    # Добавляем колокольчик в top-bar (после user-info)
    content = content.replace('<div class="user-info">', html_bell + '\n    <div class="user-info">', 1)
    
    # Добавляем дропдаун перед </body>
    content = content.replace('</body>', html_dropdown + '\n</body>')
    
    # Добавляем JS перед </script>
    content = content.replace('</script>', js_add + '\n</script>')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('Updated:', filename)

print('Done!')
