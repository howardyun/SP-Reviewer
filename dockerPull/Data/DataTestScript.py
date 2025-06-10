import sqlite3

from fontTools.misc.cython import returns


def sqlit3_fetch_all(cursor,db_name = 'kv_data',key_name='repo_name',value_name= 'pypi_info_list'):
    cursor.execute(f"SELECT {key_name},{value_name} FROM {db_name}")
    return cursor.fetchall()
    # for row in cursor.fetchall():
    #     print(row[0], json.loads(row[1]))

def list_all_repo_to_pypi_data(db_name='repo/repo_pypi.db'):
    conn = sqlite3.connect(db_name)
    # 声明游标
    cur = conn.cursor()
    fetch_all = sqlit3_fetch_all(cur)
    print(len(fetch_all))


if __name__ == '__main__':
    list_all_repo_to_pypi_data()





# def fetch_repo_to_pypi(db_name= 'repo/DataTestScript.py'):
#     # 建立数据库的连接
#     conn = sqlite3.connect(db_name)
#     # 声明游标
#     cur = conn.cursor()
#     sql1 = '''select * from kv_data; '''
#     res = cur.execute(sql1)
#
#     for data in cur:
#         print(data)