mod queue_operation;
mod task_mounter;

use pyo3::prelude::*;
use queue_operation::{QueueOperation, ShardedQueueOperation};
use task_mounter::TaskMounter; // 导入结构体 // 导入结构体

#[pymodule]
// #[pymodule(gil_used = false)]
fn queue_sqlite_core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<TaskMounter>()?;
    m.add_class::<QueueOperation>()?;
    m.add_class::<ShardedQueueOperation>()?;
    Ok(())
}
