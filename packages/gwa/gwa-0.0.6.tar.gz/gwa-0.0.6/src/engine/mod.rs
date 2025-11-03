//! The core "Transformation Engine" module.
//!
//! This module orchestrates the entire project generation process by:
//! 1. Fetching the source template
//! 2. Building a transformation plan based on user configuration
//! 3. Executing the plan on the fetched files
//! 4. Deploying the result to the destination

pub mod error;
pub mod plan;
pub mod source;
pub mod transform;

use crate::config::ProjectConfig;
use fs_extra::dir::{CopyOptions, copy};
use std::path::Path;

pub use error::EngineError; // Re-export for convenience

/// Main entry point for the transformation engine
pub fn run(config: &ProjectConfig, destination: &Path) -> Result<(), EngineError> {
    println!("🚀 Engine starting...");

    // 1. Fetch source
    let temp_dir = source::fetch()?;

    // 2. Build transformation plan
    println!("📝 Building transformation plan...");
    let plan = plan::build_plan(config)?;

    // 3. Execute the plan
    println!("⚙️  Applying transformations...");
    transform::execute(&plan, temp_dir.path())?;

    // 4. Copy to final destination
    println!("🚚 Copying project to {}...", destination.display());
    let mut options = CopyOptions::new();
    options.overwrite = true;
    copy(temp_dir.path(), destination, &options)
        .map_err(|e| EngineError::FinalCopyFailed(format!("Failed to copy project: {}", e)))?;

    println!(
        "\n✅ Project '{}' created successfully!",
        config.project_name
    );
    Ok(()) // The temp_dir will be automatically cleaned up when it goes out of scope
}
