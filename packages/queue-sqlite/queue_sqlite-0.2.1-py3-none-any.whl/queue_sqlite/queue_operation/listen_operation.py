#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   listen_operation.py
@Time    :   2025-09-27 17:02:18
@Author  :   chakcy
@Email   :   947105045@qq.com
@description   :   监听操作模块 - 改进版，优化数据库连接
"""


from ..mounter.listen_mounter import ListenMounter
import sqlite3
from typing import List, Tuple, Union
import logging


class ListenOperation:
    def __init__(self, db_dir):
        self.db_dir = db_dir
        self.listen_fields = ListenMounter.get_Listener_list()
        self.create_table()

    def _get_connection(self):
        """获取数据库连接 - 改进版"""
        conn = sqlite3.connect(
            self.db_dir, check_same_thread=False, timeout=30.0  # 增加超时时间
        )

        # 设置SQLite优化参数
        conn.execute("PRAGMA journal_mode=WAL;")  # 使用WAL模式提高并发
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-20000;")
        conn.execute("PRAGMA busy_timeout=5000;")  # 设置忙时超时
        conn.execute("PRAGMA mmap_size=268435456;")  # 256MB内存映射

        return conn

    def create_table(self):
        if len(self.listen_fields) == 0:
            return
        conn = self._get_connection()

        try:
            # 分别执行每个SQL语句而不是使用executescript
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS listen_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key Text,
                    value JSON
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT,
                    row_id INTEGER,
                    column_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    is_delete integer DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 检查触发器是否已存在，如果不存在则创建
            try:
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS track_value_change
                    AFTER UPDATE OF value ON listen_table
                    FOR EACH ROW
                    WHEN OLD.value <> NEW.value
                    BEGIN
                        INSERT INTO change_log (table_name, row_id, column_name, old_value, new_value)
                        VALUES ('listen_table', NEW.id, 'key', OLD.key, NEW.key);
                    END
                """
                )
            except sqlite3.Error:
                # 如果触发器创建失败，我们继续执行其他操作
                pass

            conn.commit()

            for listen_field in self.listen_fields:
                # 检查是否已存在该key
                cursor = conn.execute(
                    "SELECT id FROM listen_table WHERE key = ?", (listen_field,)
                )
                if cursor.fetchone() is None:
                    sql = """
                        INSERT INTO 
                            listen_table (key, value)
                        VALUES 
                            (?, ?)
                    """
                    conn.execute(sql, (listen_field, "null"))
                    conn.commit()

        except Exception as e:
            logging.error(f"创建监听表失败: {str(e)}")
        finally:
            conn.close()

    def listen_data(self) -> Tuple[bool, Union[List[Tuple], str]]:
        """获取监听数据 - 改进版"""
        conn = self._get_connection()
        try:
            sql = """
                SELECT * FROM change_log where is_delete = 0 ORDER BY id DESC LIMIT 100
            """
            result = conn.execute(sql).fetchall()
            if len(result) == 0:
                return False, "No data found"
            return True, result
        except Exception as e:
            logging.error(f"获取监听数据失败: {str(e)}")
            return False, str(e)
        finally:
            conn.close()

    def delete_change_log(self, delete_id):
        """删除变更日志 - 改进版"""
        conn = self._get_connection()
        try:
            sql = """
                DELETE FROM change_log WHERE id = ?
            """
            conn.execute(sql, (delete_id,))
            conn.commit()
        except Exception as e:
            logging.error(f"删除变更日志失败 {delete_id}: {str(e)}")
            raise e  # 重新抛出异常以便上层处理
        finally:
            conn.close()

    def update_listen_data(self, key, value):
        """更新监听数据 - 改进版"""
        conn = self._get_connection()
        try:
            sql = """
                UPDATE listen_table SET value = ? WHERE key = ?
            """
            conn.execute(sql, (value, key))
            conn.commit()
        except Exception as e:
            logging.error(f"更新监听数据失败 {key}: {str(e)}")
            raise e
        finally:
            conn.close()

    def get_value(self, key):
        """获取值 - 改进版"""
        conn = self._get_connection()
        try:
            sql = """
                SELECT value FROM listen_table WHERE key = ?
            """
            result = conn.execute(sql, (key,)).fetchone()
            if result is None:
                return None
            return result[0]
        except Exception as e:
            logging.error(f"获取值失败 {key}: {str(e)}")
            return None
        finally:
            conn.close()

    def get_values(self):
        """获取所有值 - 改进版"""
        conn = self._get_connection()
        try:
            sql = """
                SELECT key, value FROM listen_table
            """
            result = conn.execute(sql).fetchall()
            return result
        except Exception as e:
            logging.error(f"获取所有值失败: {str(e)}")
            return []
        finally:
            conn.close()
