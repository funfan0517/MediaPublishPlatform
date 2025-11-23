import sqlite3
import os

# 连接到数据库
db_path = os.path.join('db', 'database.db')
print(f'检查数据库: {db_path}')

if not os.path.exists(db_path):
    print('数据库文件不存在')
    exit()

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_info'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print('user_info表不存在')
    else:
        # 查询账号数据
        cursor.execute('SELECT * FROM user_info')
        rows = cursor.fetchall()
        print(f'已添加账号数量: {len(rows)}')
        
        if len(rows) > 0:
            print('账号列表:')
            for row in rows:
                print(row)
        else:
            print('当前系统中没有已添加的账号')
            
    conn.close()
except Exception as e:
    print(f'查询过程中出现错误: {e}')