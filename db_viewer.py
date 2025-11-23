import sqlite3
import os
import json
from datetime import datetime

"""
简易数据库可视化查询工具
功能：查询和展示SQLite数据库中的所有表及数据
使用方法：python db_viewer.py
"""

def print_table_info(cursor, table_name):
    """打印表结构信息"""
    print(f"\n{'='*60}")
    print(f"表名: {table_name}")
    print(f"{'='*60}")
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print("表结构:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    print()
    
    # 获取表数据
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    print(f"数据行数: {len(rows)}")
    if len(rows) > 0:
        print("\n前5行数据预览:")
        # 打印列名
        col_names = [desc[0] for desc in cursor.description]
        print(" | ".join(col_names))
        print("-" * (len(" | ".join(col_names))))
        
        # 打印前5行数据
        for i, row in enumerate(rows[:5]):
            row_str = []
            for item in row:
                if isinstance(item, bytes):
                    row_str.append(f"<BLOB ({len(item)} bytes)>")
                elif isinstance(item, str) and len(item) > 30:
                    row_str.append(f"{item[:30]}...")
                else:
                    row_str.append(str(item))
            print(" | ".join(row_str))
        
        if len(rows) > 5:
            print(f"\n... 还有 {len(rows) - 5} 行数据未显示")
    print(f"{'='*60}\n")

def export_to_json(cursor, table_name, export_dir):
    """导出表数据到JSON文件"""
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # 获取列名
    col_names = [desc[0] for desc in cursor.description]
    
    # 转换数据为字典列表
    data = []
    for row in rows:
        row_dict = {}
        for i, value in enumerate(row):
            # 处理特殊类型
            if isinstance(value, bytes):
                row_dict[col_names[i]] = f"<BLOB ({len(value)} bytes)"  # Base64可能会很大，这里简化显示
            else:
                row_dict[col_names[i]] = value
        data.append(row_dict)
    
    # 确保导出目录存在
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # 导出到JSON文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = os.path.join(export_dir, f"{table_name}_{timestamp}.json")
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    return json_file

def main():
    # 数据库路径
    db_path = os.path.join('db', 'database.db')
    
    print(f"数据库可视化查询工具")
    print(f"目标数据库: {db_path}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print("错误: 数据库文件不存在!")
        print("请确认数据库路径正确或先运行 createTable.py 创建数据库")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        cursor = conn.cursor()
        
        print("\n数据库连接成功!")
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        if not tables:
            print("数据库中没有找到表!")
        else:
            print(f"\n发现 {len(tables)} 个表:")
            for i, table in enumerate(tables, 1):
                print(f"{i}. {table[0]}")
            
            print("\n详细信息:")
            for table in tables:
                print_table_info(cursor, table[0])
            
            # 询问是否导出数据
            export_choice = input("是否将数据导出为JSON文件? (y/n): ")
            if export_choice.lower() == 'y':
                export_dir = "db_exports"
                print(f"\n正在导出数据到 {export_dir} 目录...")
                for table in tables:
                    json_file = export_to_json(cursor, table[0], export_dir)
                    print(f"  - {table[0]} 表数据已导出到 {json_file}")
                print("\n数据导出完成!")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    main()