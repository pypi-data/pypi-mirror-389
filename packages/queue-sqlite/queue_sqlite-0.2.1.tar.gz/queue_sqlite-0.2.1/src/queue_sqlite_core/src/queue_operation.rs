// src/lib.rs
use chrono::{DateTime, Duration, Utc};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;
use rand::seq::SliceRandom;
use rusqlite::{params, Connection, Row};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::path::Path;
use std::sync::{Arc, Mutex};

/// 单个分片的队列操作
#[pyclass]
pub struct QueueOperation {
    pool: Pool<SqliteConnectionManager>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Message {
    id: String,
    message_type: String,
    status: i32,
    content: String,
    createtime: String,
    updatetime: String,
    result: Option<String>,
    priority: i32,
    source: String,
    destination: String,
    retry_count: i32,
    expire_time: Option<String>,
    tags: Option<String>,
    metadata: Option<String>,
    is_deleted: i32,
}

impl TryFrom<&Row<'_>> for Message {
    type Error = rusqlite::Error;

    fn try_from(row: &Row) -> Result<Self, Self::Error> {
        Ok(Message {
            id: row.get("id")?,
            message_type: row.get("type")?,
            status: row.get("status")?,
            content: row.get("content")?,
            createtime: row.get("createtime")?,
            updatetime: row.get("updatetime")?,
            result: row.get("result")?,
            priority: row.get("priority")?,
            source: row.get("source")?,
            destination: row.get("destination")?,
            retry_count: row.get("retry_count")?,
            expire_time: row.get("expire_time")?,
            tags: row.get("tags")?,
            metadata: row.get("metadata")?,
            is_deleted: row.get("is_deleted")?,
        })
    }
}

#[pymethods]
impl QueueOperation {
    #[new]
    pub fn new(queue_path: String) -> PyResult<Self> {
        let manager = SqliteConnectionManager::file(queue_path);
        let pool = Pool::new(manager)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(QueueOperation { pool })
    }

    /// 初始化数据库和表
    /// Args:
    ///   - self: QueueOperation 实例
    /// Returns:
    ///   - None
    pub fn init_db(&self) -> PyResult<()> {
        let conn = self.get_connection()?;

        // 创建消息表
        conn.execute(
            "CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status INTEGER NOT NULL,
                content TEXT NOT NULL,
                createtime DATETIME NOT NULL,
                updatetime DATETIME NOT NULL,
                result TEXT,
                priority INTEGER NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                retry_count INTEGER NOT NULL,
                expire_time DATETIME,
                tags TEXT,
                metadata TEXT,
                is_deleted INTEGER NOT NULL DEFAULT 0
            )",
            [],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        // 创建索引
        let indexes = [
            "CREATE INDEX IF NOT EXISTS idx_status ON messages(status)",
            "CREATE INDEX IF NOT EXISTS idx_priority ON messages(priority)",
            "CREATE INDEX IF NOT EXISTS idx_dequeue ON messages(status, priority DESC, createtime ASC) WHERE is_deleted = 0 AND status = 0",
            "CREATE INDEX IF NOT EXISTS idx_expire_time ON messages(expire_time) WHERE expire_time IS NOT NULL",
        ];

        for index_sql in indexes.iter() {
            conn.execute(index_sql, [])
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        }

        // 设置 SQLite 优化参数
        let pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",
            "PRAGMA cache_size=-20000",
            "PRAGMA mmap_size=134217728",
            "PRAGMA temp_store=MEMORY",
            "PRAGMA busy_timeout=3000",
        ];

        for pragma in pragmas.iter() {
            conn.execute_batch(pragma)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        }

        Ok(())
    }

    /// 入队
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - message: PyDict 实例，包含消息内容
    /// Returns:
    ///   - String: 消息ID
    pub fn enqueue(&self, message: &Bound<'_, PyDict>) -> PyResult<String> {
        let mut conn = self.get_connection()?;

        let required_fields = [
            "id",
            "type",
            "status",
            "content",
            "createtime",
            "updatetime",
            "priority",
            "source",
            "destination",
            "retry_count",
        ];

        for field in required_fields.iter() {
            if !message.contains(field)? {
                return Err(PyErr::new::<pyo3::exceptions::PyKeyError, _>(format!(
                    "Missing required field: {}",
                    field
                )));
            }
        }

        let tx = conn
            .transaction()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        // 从PyDict获取值
        let id: String = message.get_item("id")?.unwrap().extract()?;
        let message_type: String = message.get_item("type")?.unwrap().extract()?;
        let status: i32 = message.get_item("status")?.unwrap().extract()?;
        let content: String = message.get_item("content")?.unwrap().extract()?;
        let createtime: String = message.get_item("createtime")?.unwrap().extract()?;
        let updatetime: String = message.get_item("updatetime")?.unwrap().extract()?;
        let priority: i32 = message.get_item("priority")?.unwrap().extract()?;
        let source: String = message.get_item("source")?.unwrap().extract()?;
        let destination: String = message.get_item("destination")?.unwrap().extract()?;
        let retry_count: i32 = message.get_item("retry_count")?.unwrap().extract()?;

        // 可选字段
        let result: Option<String> = match message.get_item("result")? {
            Some(item) => {
                if item.is_none() {
                    None
                } else {
                    Some(item.extract()?)
                }
            }
            None => None,
        };

        let expire_time: Option<String> = match message.get_item("expire_time")? {
            Some(item) => {
                if item.is_none() {
                    None
                } else {
                    Some(item.extract()?)
                }
            }
            None => None,
        };

        let tags: Option<String> = match message.get_item("tags")? {
            Some(item) => {
                if item.is_none() {
                    None
                } else {
                    Some(item.extract()?)
                }
            }
            None => None,
        };

        let metadata: Option<String> = match message.get_item("metadata")? {
            Some(item) => {
                if item.is_none() {
                    None
                } else {
                    Some(item.extract()?)
                }
            }
            None => None,
        };

        tx.execute(
            "INSERT INTO messages (
                id, type, status, content, createtime, updatetime, result,
                priority, source, destination, retry_count, expire_time, tags, metadata
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)",
            params![
                id,
                message_type,
                status,
                content,
                createtime,
                updatetime,
                result,
                priority,
                source,
                destination,
                retry_count,
                expire_time,
                tags,
                metadata,
            ],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        tx.commit()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(id)
    }

    /// 出队
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - size: i32, 获取消息数量
    /// Returns:
    ///   - Vec<HashMap<String, String>>: 获取的消息列表
    pub fn dequeue(&self, size: i32) -> PyResult<Vec<HashMap<String, String>>> {
        let limited_size = std::cmp::min(size, 500);
        let conn = self.get_connection()?;
        let now = Utc::now().to_rfc3339();

        let mut stmt = conn
            .prepare(
                "UPDATE messages 
             SET status = 1, updatetime = ?1 
             WHERE id IN (
                 SELECT id FROM messages 
                 WHERE is_deleted = 0 
                 AND status = 0 
                 AND (expire_time IS NULL OR expire_time > ?1)
                 ORDER BY priority DESC, createtime ASC 
                 LIMIT ?2
             )
             RETURNING *",
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let rows = stmt
            .query_map(params![now, limited_size], |row| {
                let message: Message = row.try_into()?;
                let mut map = HashMap::new();
                map.insert("id".to_string(), message.id);
                map.insert("type".to_string(), message.message_type);
                map.insert("status".to_string(), message.status.to_string());
                map.insert("content".to_string(), message.content);
                map.insert("createtime".to_string(), message.createtime);
                map.insert("updatetime".to_string(), message.updatetime);
                map.insert("result".to_string(), message.result.unwrap_or_default());
                map.insert("priority".to_string(), message.priority.to_string());
                map.insert("source".to_string(), message.source);
                map.insert("destination".to_string(), message.destination);
                map.insert("retry_count".to_string(), message.retry_count.to_string());
                map.insert(
                    "expire_time".to_string(),
                    message.expire_time.unwrap_or_default(),
                );
                map.insert("tags".to_string(), message.tags.unwrap_or_default());
                map.insert("metadata".to_string(), message.metadata.unwrap_or_default());
                Ok(map)
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let mut result = Vec::new();
        for row in rows {
            result.push(
                row.map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?,
            );
            if result.len() > 1000 {
                break;
            }
        }

        Ok(result)
    }

    /// 获取队列长度
    /// Args:
    ///   - self: QueueOperation 实例
    /// Returns:
    ///   - i32: 队列长度
    pub fn get_queue_length(&self) -> PyResult<i32> {
        let conn = self.get_connection()?;
        let now = Utc::now().to_rfc3339();

        let count: i32 = conn
            .query_row(
                "SELECT COUNT(*) FROM messages 
             WHERE is_deleted = 0 
             AND status = 0 
             AND (expire_time IS NULL OR expire_time > ?1)",
                params![now],
                |row| row.get(0),
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(count)
    }

    /// 获取已完成的消息
    /// Args:
    ///   - self: QueueOperation 实例
    /// Returns:
    ///   - Vec<HashMap<String, String>>: 已完成的消息列表
    pub fn get_completed_messages(&self) -> PyResult<Vec<HashMap<String, String>>> {
        let conn = self.get_connection()?;

        let mut stmt = conn
            .prepare(
                "SELECT * FROM messages 
             WHERE is_deleted = 0 
             AND (status = 2 OR status = 3)
             LIMIT 10000",
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let rows = stmt
            .query_map([], |row| {
                let message: Message = row.try_into()?;
                let mut map = HashMap::new();
                map.insert("id".to_string(), message.id);
                map.insert("type".to_string(), message.message_type);
                map.insert("status".to_string(), message.status.to_string());
                map.insert("content".to_string(), message.content);
                map.insert("createtime".to_string(), message.createtime);
                map.insert("updatetime".to_string(), message.updatetime);
                map.insert("result".to_string(), message.result.unwrap_or_default());
                map.insert("priority".to_string(), message.priority.to_string());
                map.insert("source".to_string(), message.source);
                map.insert("destination".to_string(), message.destination);
                map.insert("retry_count".to_string(), message.retry_count.to_string());
                map.insert(
                    "expire_time".to_string(),
                    message.expire_time.unwrap_or_default(),
                );
                map.insert("tags".to_string(), message.tags.unwrap_or_default());
                map.insert("metadata".to_string(), message.metadata.unwrap_or_default());
                Ok(map)
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let mut result = Vec::new();
        for row in rows {
            result.push(
                row.map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?,
            );
            if result.len() > 1000 {
                break;
            }
        }

        Ok(result)
    }

    /// 获取消息详情
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - id: String, 消息ID
    /// Returns:
    ///  - HashMap<String, String>: 消息详情
    pub fn get_result(&self, id: String) -> PyResult<HashMap<String, String>> {
        let conn = self.get_connection()?;

        let mut stmt = conn
            .prepare(
                "SELECT * FROM messages 
             WHERE id = ?1 
             AND (status = 2 OR status = 3)",
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let message: Message = stmt
            .query_row(params![id], |row| row.try_into())
            .map_err(|e| {
                // 更好地处理查询不到结果的情况
                if e == rusqlite::Error::QueryReturnedNoRows {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        "Message not found or not completed",
                    )
                } else {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string())
                }
            })?;

        let mut result = HashMap::new();
        result.insert("id".to_string(), message.id);
        result.insert("type".to_string(), message.message_type);
        result.insert("status".to_string(), message.status.to_string());
        result.insert("content".to_string(), message.content);
        result.insert("createtime".to_string(), message.createtime);
        result.insert("updatetime".to_string(), message.updatetime);
        result.insert("result".to_string(), message.result.unwrap_or_default());
        result.insert("priority".to_string(), message.priority.to_string());
        result.insert("source".to_string(), message.source);
        result.insert("destination".to_string(), message.destination);
        result.insert("retry_count".to_string(), message.retry_count.to_string());
        result.insert(
            "expire_time".to_string(),
            message.expire_time.unwrap_or_default(),
        );
        result.insert("tags".to_string(), message.tags.unwrap_or_default());
        result.insert("metadata".to_string(), message.metadata.unwrap_or_default());

        Ok(result)
    }

    /// 更新消息状态
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - id: String, 消息ID
    ///  - status: i32, 新状态
    /// Returns:
    ///   - () : 无返回值
    pub fn update_status(&self, id: String, status: i32) -> PyResult<()> {
        let conn = self.get_connection()?;
        let now = Utc::now().to_rfc3339();

        conn.execute(
            "UPDATE messages SET status = ?1, updatetime = ?2 WHERE id = ?3",
            params![status, now, id],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(())
    }

    /// 更新消息结果
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - id: String, 消息ID
    ///  - result: String, 新结果
    /// Returns:
    ///   - () : 无返回值
    pub fn update_result(&self, id: String, result: String) -> PyResult<()> {
        let conn = self.get_connection()?;
        let now = Utc::now().to_rfc3339();

        conn.execute(
            "UPDATE messages SET result = ?1, updatetime = ?2 WHERE id = ?3",
            params![result, now, id],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(())
    }

    /// 删除消息
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - id: String, 删除的消息ID
    /// Returns:
    ///   - () : 无返回值
    pub fn delete_message(&self, id: String) -> PyResult<()> {
        let conn = self.get_connection()?;

        conn.execute(
            "UPDATE messages SET is_deleted = 1 WHERE id = ?1",
            params![id],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(())
    }

    /// 清理过期消息
    /// Args:
    ///   - self: QueueOperation 实例
    /// Returns:
    ///   - () : 无返回值
    pub fn clean_expired_messages(&self) -> PyResult<()> {
        let conn = self.get_connection()?;
        let now = Utc::now().to_rfc3339();

        conn.execute(
            "UPDATE messages SET is_deleted = 1 
             WHERE is_deleted = 0 
             AND expire_time IS NOT NULL 
             AND expire_time < ?1",
            params![now],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(())
    }

    /// 清理旧消息
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - days: i64, 清理旧消息的天数
    /// Returns:
    ///   - () : 无返回值
    pub fn clean_old_messages(&self, days: i64) -> PyResult<()> {
        let conn = self.get_connection()?;
        let cutoff_time = (Utc::now() - Duration::days(days)).to_rfc3339();

        conn.execute(
            "UPDATE messages SET is_deleted = 1 
             WHERE is_deleted = 0 
             AND status IN (2, 3) 
             AND updatetime < ?1",
            params![cutoff_time],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(())
    }

    /// 删除过期消息
    /// Args:
    ///   - self: QueueOperation 实例
    ///   - days: i64, 删除过期消息的天数
    /// Returns:
    ///   - () : 无返回值
    pub fn remove_expired_messages(&self, days: i64) -> PyResult<()> {
        let now: DateTime<Utc> = Utc::now();
        let expire_time = now - Duration::days(days);
        let iso_format = expire_time.to_rfc3339();

        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        conn.execute(
            "
            DELETE FROM messages
            WHERE is_deleted = 0
            AND expire_time IS NOT NULL
            AND expire_time < ?1
            ",
            params![iso_format],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(())
    }
}

/// 获取数据库连接
impl QueueOperation {
    fn get_connection(&self) -> PyResult<r2d2::PooledConnection<SqliteConnectionManager>> {
        self.pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }
}

/// 分片队列操作
#[pyclass]
pub struct ShardedQueueOperation {
    shards: Vec<QueueOperation>,
    #[pyo3(get)]
    shard_num: usize,
    #[pyo3(get)]
    db_dir: String,
}

#[pymethods]
impl ShardedQueueOperation {
    #[new]
    pub fn new(shard_num: usize, queue_name: String) -> PyResult<Self> {
        // 创建缓存目录
        let db_dir = format!("cache/{}", queue_name);
        std::fs::create_dir_all(&db_dir)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let mut shards = Vec::with_capacity(shard_num);

        for i in 0..shard_num {
            let db_path = format!("{}/queue_shard_{}.db", db_dir, i);
            let queue_op = QueueOperation::new(db_path)?;
            queue_op.init_db()?;
            shards.push(queue_op);
        }

        Ok(ShardedQueueOperation {
            shards,
            shard_num,
            db_dir,
        })
    }

    /// 获取分片索引
    /// Args:
    ///  - self: ShardedQueueOperation 实例
    ///  - message_id: &str, 消息ID
    /// Returns:
    ///  - usize: 分片索引
    fn _get_shard_index(&self, message_id: &str) -> usize {
        let mut hasher = Sha256::new();
        hasher.update(message_id.as_bytes());
        let result = hasher.finalize();

        // 将哈希值转换为 usize
        let hash_bytes: [u8; 8] = result[..8].try_into().unwrap();
        let hash_value = u64::from_be_bytes(hash_bytes) as usize;

        hash_value % self.shard_num
    }

    /// 添加消息
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    ///   - message: &Bound<'_, PyDict>, 待添加的消息
    /// Returns:
    ///   - String: 添加的消息ID
    pub fn enqueue(&self, message: &Bound<'_, PyDict>) -> PyResult<String> {
        let message_id_bound = message
            .get_item("id")?
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing id field"))?;
        let message_id: String = message_id_bound.extract()?;

        let shard_index = self._get_shard_index(&message_id);
        self.shards[shard_index].enqueue(message)
    }

    /// 获取消息
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    ///   - size: i32, 获取的消息数量
    /// Returns:
    ///   - Vec<HashMap<String, String>>: 获取的消息列表
    pub fn dequeue(&self, size: i32) -> PyResult<Vec<HashMap<String, String>>> {
        let mut all_messages = Vec::new();
        let mut collected = 0;

        // 限制单次获取的最大消息数量
        let max_size = std::cmp::min(size, 1000);

        // 随机轮询分片顺序
        let mut shard_order: Vec<usize> = (0..self.shard_num).collect();
        let mut rng = rand::thread_rng();
        shard_order.shuffle(&mut rng);

        for shard_index in shard_order {
            if collected >= max_size {
                break;
            }

            let remaining = size - collected;
            let shard_messages = self.shards[shard_index].dequeue(remaining)?;
            collected += shard_messages.len() as i32;
            all_messages.extend(shard_messages);

            if all_messages.len() > 1000 {
                break;
            }
        }

        Ok(all_messages)
    }

    /// 获取队列长度
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    /// Returns:
    ///   - i32: 队列长度
    pub fn get_queue_length(&self) -> PyResult<i32> {
        let mut total = 0;
        for shard in &self.shards {
            total += shard.get_queue_length()?;
        }
        Ok(total)
    }

    /// 获取已完成的消息
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    /// Returns:
    ///   - Vec<HashMap<String, String>>: 已完成的消息列表
    pub fn get_completed_messages(&self) -> PyResult<Vec<HashMap<String, String>>> {
        let mut all_messages = Vec::new();
        for shard in &self.shards {
            let shard_messages = shard.get_completed_messages()?;
            all_messages.extend(shard_messages);

            if all_messages.len() > 1000 {
                break;
            }
        }
        Ok(all_messages)
    }

    /// 获取消息详情
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    ///   - message_id: String, 消息ID
    /// Returns:
    ///   - HashMap<String, String>: 消息详情
    pub fn get_result(&self, message_id: String) -> PyResult<HashMap<String, String>> {
        let shard_index = self._get_shard_index(&message_id);
        self.shards[shard_index].get_result(message_id)
    }

    /// 更新消息状态
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    ///   - message_id: String, 消息ID
    ///  - status: i32, 新状态
    /// Returns:
    ///   - () : 无返回值
    pub fn update_status(&self, message_id: String, status: i32) -> PyResult<()> {
        let shard_index = self._get_shard_index(&message_id);
        self.shards[shard_index].update_status(message_id, status)
    }

    /// 更新消息结果
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    ///   - message_id: String, 消息ID
    ///  - result: String, 新结果
    /// Returns:
    ///   - () : 无返回值
    pub fn update_result(&self, message_id: String, result: String) -> PyResult<()> {
        let shard_index = self._get_shard_index(&message_id);
        self.shards[shard_index].update_result(message_id, result)
    }

    /// 删除消息
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    ///   - message_id: String, 待删除的消息ID
    /// Returns:
    ///   - () : 无返回值
    pub fn delete_message(&self, message_id: String) -> PyResult<()> {
        let shard_index = self._get_shard_index(&message_id);
        self.shards[shard_index].delete_message(message_id)
    }

    /// 清理过期消息
    /// Args:
    ///   - self: ShardedQueueOperation 实例
    /// Returns:
    ///   - () : 无返回值
    pub fn clean_expired_messages(&self) -> PyResult<()> {
        for shard in &self.shards {
            shard.clean_expired_messages()?;
        }
        Ok(())
    }

    /// 清理旧消息
    /// Args:
    ///  - self: ShardedQueueOperation 实例
    /// - days: i64, 清理旧消息的天数
    /// Returns:
    ///   - () : 无返回值
    pub fn remove_expired_messages(&self, days: i64) -> PyResult<()> {
        for shard in &self.shards {
            shard.remove_expired_messages(days)?;
        }
        Ok(())
    }

    /// 清理旧消息
    /// Args:
    ///  - self: ShardedQueueOperation 实例
    /// - days: i64, 清理旧消息的天数
    /// Returns:
    ///   - () : 无返回值
    pub fn clean_old_messages(&self, days: i64) -> PyResult<()> {
        for shard in &self.shards {
            shard.clean_old_messages(days)?;
        }
        Ok(())
    }
}
