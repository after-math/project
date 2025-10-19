import pymysql

# ====== 数据库连接配置 ======
host = "rm-wz97z0ykk16h460i9to.mysql.rds.aliyuncs.com"
user = "streamlit"
password = "Cjm20040224"
database = "word"  # 你自己的数据库名（如果你有单独建一个，比如 english_app，就改成那个）
port = 3306

try:
    # 建立连接
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        charset="utf8mb4"
    )
    print("✅ 成功连接到阿里云 RDS MySQL 数据库！")

    # 执行一个简单查询
    with connection.cursor() as cursor:
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("🕒 当前数据库时间:", result)

except pymysql.MySQLError as e:
    print("❌ 连接失败：", e)

finally:
    if 'connection' in locals() and connection.open:
        connection.close()
        print("🔒 数据库连接已关闭。")
