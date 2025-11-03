//! Source fetcher module - responsible for cloning the template repository

use super::EngineError;
use git2;
use tempfile::TempDir;

const TEMPLATE_URL: &str = "https://github.com/Yrrrrrf/gwa.git";
const TEMPLATE_BRANCH: &str = "main";

pub fn fetch() -> Result<TempDir, EngineError> {
    let temp_dir = TempDir::new().map_err(|e| EngineError::SourceFetchFailed(e.to_string()))?;

    let mut fo = git2::FetchOptions::new();
    fo.depth(1); // Shallow clone for speed

    let mut builder = git2::build::RepoBuilder::new();
    builder.fetch_options(fo);
    builder.branch(TEMPLATE_BRANCH);

    builder
        .clone(TEMPLATE_URL, temp_dir.path())
        .map_err(|e| EngineError::SourceFetchFailed(e.to_string()))?;

    println!(
        "✅ Source template cloned into: {}",
        temp_dir.path().display()
    );
    Ok(temp_dir)
}
