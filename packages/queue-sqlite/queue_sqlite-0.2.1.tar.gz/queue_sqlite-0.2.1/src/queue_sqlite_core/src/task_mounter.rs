use pyo3::prelude::*;

#[pyclass]
pub struct TaskMounter {
    obj: Py<PyAny>,
}

#[pymethods]
impl TaskMounter {
    #[new]
    fn new(obj: Py<PyAny>) -> Self {
        TaskMounter { obj }
    }

    fn get_task_list(&self, py: Python<'_>) -> PyResult<()> {
        let obj = self.obj.bind(py);
        let result_obj = obj.call_method("get_task_list", (), None)?;
        println!("Method result: {:?}", result_obj);
        Ok(())
    }

    fn get_task_function(&self, py: Python<'_>, task_name: &str) -> PyResult<PyObject> {
        let obj = self.obj.bind(py);
        let result = obj.call_method1("get_task_function", (task_name,))?;
        Ok(result.into())
    }
}
