//! Custom error types for the transformation engine

use std::path::PathBuf;

#[derive(Debug, thiserror::Error)]
pub enum EngineError {
    #[error("Configuration is invalid: {0}")]
    InvalidConfig(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Git operation failed: {0}")]
    Git(#[from] git2::Error),

    #[error("Template processing error: {0}")]
    Template(String),

    #[error("File system operation failed: {0}")]
    FileSystem(String),

    #[error("Path operation failed: {path}, error: {error}")]
    PathError { path: PathBuf, error: String },

    #[error("Source fetch failed: {0}")]
    SourceFetchFailed(String),

    #[error("Final project copy failed: {0}")]
    FinalCopyFailed(String),
}
