import pandas as pd
from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import sessionmaker

import authentic_file.config


class DatabaseUploader:
    def __init__(self, db_url):
        """
        初始化数据库上传器类。

        参数：
        - db_url: 数据库连接URL。
        """
        self.db_url = db_url
        self.engine = create_engine(db_url, pool_size=5, max_overflow=10)
        self.Session = sessionmaker(bind=self.engine)

    def upload_energy_data(self, df):
        """
        将DataFrame上传到数据库中的UploadEnergyData表中。

        参数：
        - df: 包含上传数据的DataFrame，需包含 'DOI', 'Formula', 'Uploader', 'AdsorbateName', 'Energy' 列。

        返回：
        - 成功插入的数据条数。
        """
        session = self.Session()
        try:
            df.to_sql('UploadEnergyData', con=self.engine, if_exists='append', index=False, method='multi')
            session.commit()
            print("数据上传成功。")
            return len(df)
        except exc.IntegrityError as e:
            session.rollback()
            print(f"数据插入失败，可能是重复键值或完整性错误：{e}")
        except exc.SQLAlchemyError as e:
            session.rollback()
            print(f"数据插入过程中发生错误：{e}")
        finally:
            session.close()
            self.engine.dispose()

    def upload_file_data(self, df):
        """
        将DataFrame上传到数据库中的UploadFile表中。

        参数：
        - df: 包含上传数据的DataFrame，需包含 'DOI', 'Formula', 'Uploader', 'AdsorbateName', 'FileType' 列。

        返回：
        - 成功插入的数据条数。
        """
        session = self.Session()
        try:
            df.to_sql('UploadFile', con=self.engine, if_exists='append', index=False, method='multi')
            session.commit()
            print("数据上传成功。")
            return len(df)
        except exc.IntegrityError as e:
            session.rollback()
            print(f"数据插入失败，可能是重复键值或完整性错误：{e}")
        except exc.SQLAlchemyError as e:
            session.rollback()
            print(f"数据插入过程中发生错误：{e}")
        finally:
            session.close()
            self.engine.dispose()

    def get_doi_uploader(self, sheet_name):
        """
        根据ReactionName获取DOI和Uploader信息。

        参数：
        - sheet_name: ReactionName，用于过滤数据。

        返回：
        - 包含DOI和Uploader的DataFrame。
        """
        query = text("""
        SELECT DOI, Uploader 
        FROM UploadEnergyData 
        WHERE ReactionName = :sheet_name
        """)
        with self.engine.connect() as connection:
            df = pd.read_sql(query, connection, params={'sheet_name': sheet_name})
        return df

    def get_valid_ads_ls(self, reaction_name):
        """
        获取与指定反应名称相关的有效 Adsorbate 列表。
        :param reaction_name: ReactionName
        :return: 有效的 Adsorbate 列表。
        """
        session = self.Session()
        try:
            # 使用正确的 SQL 查询并传递参数
            query = text("""
                    SELECT AdsorbateName
                    FROM ReactionAdsorbate
                    WHERE ReactionName = :reaction_name
                    """)
            # 使用命名参数来安全地传递参数
            result = session.execute(query, {"reaction_name": reaction_name}).fetchall()

            # 提取查询结果
            adsorbate_list = [row[0] for row in result]
            return adsorbate_list
        except exc.SQLAlchemyError as e:
            print(f"查询过程中发生错误：{e}")
            return []
        finally:
            session.close()


import threading
import time

# 示例函数，在线程中调用 get_valid_ads_ls
def query_adsorbate(your_class_instance, reaction_name):
    while True:
        ads_list = your_class_instance.get_valid_ads_ls(reaction_name)
        print(f"查询结果 for {reaction_name}: {ads_list}")
        time.sleep(0.1)  # 每隔一秒查询一次


if __name__ == "__main__":
    # 创建 YourClass 实例
    db_url = authentic_file.config.DB_URL  # 示例数据库 URL，请根据实际情况修改
    your_class_instance = DatabaseUploader(db_url)

    # 创建两个线程
    thread1 = threading.Thread(target=query_adsorbate, args=(your_class_instance, "Oxygen Reduction Reaction"))
    thread2 = threading.Thread(target=query_adsorbate, args=(your_class_instance, "Reaction2"))

    # 启动线程
    thread1.start()
    thread2.start()

    # 等待线程完成（在这个例子中，线程会无限运行，按 Ctrl+C 停止）
    thread1.join()
    thread2.join()
