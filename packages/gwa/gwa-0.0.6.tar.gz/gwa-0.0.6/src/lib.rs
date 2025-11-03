use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::path::PathBuf;

use crate::config::ProjectConfig;

mod config;
mod engine;

// Macro to extract config values from PyDict with default values
macro_rules! extract_config {
    // Pattern for required values (no default)
    ($dict:expr, $key:literal, required) => {{
        if let Some(value) = $dict.get_item($key)? {
            value.extract()?
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(concat!(
                $key,
                " is required"
            )));
        }
    }};

    // Pattern for optional values with default (handles all types)
    ($dict:expr, $key:literal, $default:expr) => {{
        if let Some(value) = $dict.get_item($key)? {
            value.extract()?
        } else {
            $default
        }
    }};
}

#[pyfunction]
fn get_crate_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// The new engine-based function to generate a project
#[pyfunction]
fn run_engine(config_dict: &Bound<'_, PyDict>) -> PyResult<bool> {
    // Convert the Python dictionary to a Rust ProjectConfig struct
    let project_name: String = extract_config!(config_dict, "project_name", required);
    let destination: String = extract_config!(config_dict, "destination", ".".to_string());
    let destination_path = PathBuf::from(destination);

    // Extract other configuration options with defaults or Optionals
    let author_name: String = extract_config!(config_dict, "author_name", "Test User".to_string());
    let author_email: String =
        extract_config!(config_dict, "author_email", "test@example.com".to_string());

    let db_name: Option<String> = extract_config!(
        config_dict,
        "db_name",
        Some(project_name.to_lowercase().replace('-', "_"))
    );

    let db_owner_admin: Option<String> = extract_config!(
        config_dict,
        "db_owner_admin",
        Some(format!(
            "{}_owner",
            project_name.to_lowercase().replace('-', "_")
        ))
    );

    let db_owner_pword: Option<String> =
        extract_config!(config_dict, "db_owner_pword", Some("password".to_string()));

    let include_server: bool = extract_config!(config_dict, "include_server", true);
    let include_frontend: bool = extract_config!(config_dict, "include_frontend", true);
    let include_tauri_desktop: bool = extract_config!(config_dict, "include_tauri_desktop", true);

    let app_identifier: String = extract_config!(
        config_dict,
        "app_identifier",
        format!(
            "com.example.{}",
            project_name.to_lowercase().replace('-', "")
        )
    );

    let deno_package_name: String = extract_config!(
        config_dict,
        "deno_package_name",
        "@test/gwa-project".to_string()
    );

    // Create the ProjectConfig struct
    let project_config = ProjectConfig {
        project_name: project_name.clone(),
        author_name,
        author_email,
        app_identifier,
        db_name,
        db_owner_admin,
        db_owner_pword,
        include_server,
        include_frontend,
        include_tauri_desktop,
        deno_package_name,
    };

    // Generate the project using the new engine
    match engine::run(&project_config, &destination_path) {
        Ok(_) => Ok(true),
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to generate project with engine: {}",
            e
        ))),
    }
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<PyModule>) -> PyResult<()> {
    // m.add_function(wrap_pyfunction!(hello_from_bin, m)?)?;
    // m.add_function(wrap_pyfunction!(init, m)?)?;
    m.add_function(wrap_pyfunction!(get_crate_version, m)?)?;
    m.add_function(wrap_pyfunction!(run_engine, m)?)?;
    Ok(())
}
