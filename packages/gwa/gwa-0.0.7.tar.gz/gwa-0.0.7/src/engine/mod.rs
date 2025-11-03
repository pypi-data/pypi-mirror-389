//! The core "Transformation Engine" module.
//!
//! This module orchestrates the entire project generation process by:
//! 1. Fetching the source template
//! 2. Building a transformation plan based on user configuration
//! 3. Executing the plan on the fetched files
//! 4. Deploying the result to the destination
// in src/engine/mod.rs

pub mod error;
pub mod plan;
pub mod source;
pub mod transform;

use crate::config::ProjectConfig;
use fs_extra::dir::{copy, CopyOptions};
// Add the 'fs' module for directory creation and checking
use std::{fs, path::Path};

pub use error::EngineError;

pub fn run(config: &ProjectConfig, destination: &Path) -> Result<(), EngineError> {
    println!("🚀 Engine starting...");

    // --- CRITICAL CHANGE #1: New, more robust destination handling ---
    let final_project_path = destination.join(&config.project_name);

    if final_project_path.exists() {
        if !final_project_path.is_dir() {
            return Err(EngineError::FileSystem(format!(
                "Destination '{}' exists but it is not a directory.",
                final_project_path.display()
            )));
        }
        
        let is_empty = final_project_path.read_dir()?.next().is_none();
        if !is_empty {
            return Err(EngineError::FileSystem(format!(
                "Destination directory '{}' already exists and is not empty. Aborting.",
                final_project_path.display()
            )));
        }
        println!("✔️ Destination directory exists and is empty. Using it.");
    } else {
        println!("✔️ Creating destination directory: {}", final_project_path.display());
        fs::create_dir_all(&final_project_path)?; // This will convert std::io::Error to EngineError::Io
    }

    // 1. Fetch source
    let temp_dir = source::fetch()?;

    // 2. Build transformation plan
    println!("📝 Building transformation plan...");
    let plan = plan::build_plan(config)?;

    // 3. Execute the plan
    println!("⚙️  Applying transformations...");
    transform::execute(&plan, temp_dir.path())?;

    // 4. Copy to final destination
    println!(
        "🚚 Copying project files to {}...",
        final_project_path.display()
    );
    let mut options = CopyOptions::new();
    
    // --- CRITICAL CHANGE #2: Tell fs_extra to copy the CONTENTS of the temp dir ---
    options.content_only = true; 
    
    copy(temp_dir.path(), &final_project_path, &options)
        .map_err(|e| EngineError::FinalCopyFailed(format!("Failed to copy project: {}", e)))?;

    println!(
        "\n✅ Project '{}' created successfully!",
        config.project_name
    );
    Ok(())
}