import pymysql

if __name__ == '__main__':
    conn = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="hetingdemo",
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor)
# 获取游标
cursor = conn.cursor()

try:
    # 执行一条insert语句，返回受影响的行数
    # cursor.execute("INSERT INTO para5(name,age) VALUES(%s,%s);",('次牛','12'))
    # 执行多次insert并返回受影响的行数
    cursor.executemany("INSERT INTO para5(name,age) VALUES(%s,%s);", [('次牛444', '12'), ("次牛2", '11'), ('次牛3', '10')])
    # 提交执行
    conn.commit()
except Exception as e:
    # 如果执行sql语句出现问题，则执行回滚操作
    conn.rollback()
    print(e)
finally:
    # 不论try中的代码是否抛出异常，这里都会执行
    # 关闭游标和数据库连接
    cursor.close()
    conn.close()
