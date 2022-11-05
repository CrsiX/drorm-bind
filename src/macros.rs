/**
Macro to expand database queries in a match statement to handle query errors properly
 */
macro_rules! handle_db_err {
    ( $py:ident, $query:expr ) => {{
        match $query {
            Ok(value) => value.into_py($py),
            Err(e) => return Err(BindingError::new_err(e.to_string())),
        }
    }};
}

/**
Macro to convert a row of a database query result to a hashmap of column name -> Python object
 */
macro_rules! convert_row {
    ( $py:ident, $row:ident, $columns:ident ) => {{
        let mut m = HashMap::new();
        for (col, col_t) in &$columns {
            let e = match col_t {
                DatabaseValueType::Null => $py.None(),
                DatabaseValueType::String => handle_db_err!($py, $row.get::<&str, &str>(col)),
                DatabaseValueType::I64 => handle_db_err!($py, $row.get::<i64, &str>(col)),
                DatabaseValueType::I32 => handle_db_err!($py, $row.get::<i32, &str>(col)),
                DatabaseValueType::I16 => handle_db_err!($py, $row.get::<i16, &str>(col)),
                DatabaseValueType::Bool => handle_db_err!($py, $row.get::<bool, &str>(col)),
                DatabaseValueType::F64 => handle_db_err!($py, $row.get::<f64, &str>(col)),
                DatabaseValueType::F32 => handle_db_err!($py, $row.get::<f32, &str>(col)),
                DatabaseValueType::Binary => $py.None(), // TODO
                DatabaseValueType::NaiveTime => $py.None(), // TODO
                DatabaseValueType::NaiveDate => $py.None(), // TODO
                DatabaseValueType::NaiveDateTime => $py.None(), // TODO
            };
            m.insert(*col, e);
        }
        m
    }};
}
