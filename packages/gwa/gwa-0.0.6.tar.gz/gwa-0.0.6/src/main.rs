// src/main.rs
#![allow(unused)]
#![allow(dead_code)]

// Declare our modules
mod cli;
mod config;
mod engine;
mod interactive;
mod validators;

use crate::cli::{Cli, Commands, CreateArgs};
use crate::config::ProjectConfig;
use clap::Parser;
use std::error::Error;

fn main() -> Result<(), Box<dyn Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Create(args) => {
            handle_create_command(args)?;
        }
    }

    Ok(())
}

fn handle_create_command(args: CreateArgs) -> Result<(), Box<dyn Error>> {
    let config = if args.yes {
        // Non-Interactive "Fast-Track" Mode
        println!("✔️ Fast-track mode enabled (--yes). Using default values.");
        let project_name = args
            .name
            .ok_or("In --yes mode, project name is required. e.g., `gwa create my-app -y`")?;
        let author_name = "Test User".to_string(); // Let's be explicit
        let author_slug = author_name
            .to_lowercase()
            .replace(' ', "-")
            .chars()
            .filter(|c| c.is_alphanumeric() || *c == '-')
            .collect::<String>();
        let deno_package_name = format!("@{}/{}", author_slug, project_name);
        ProjectConfig {
            project_name: project_name.clone(),
            author_name: "Test User".into(),
            author_email: "test@example.com".into(),
            app_identifier: format!(
                "com.example.{}",
                project_name.to_lowercase().replace('-', "")
            ),
            db_name: Some(project_name.to_lowercase().replace('-', "_")),
            db_owner_admin: Some(format!(
                "{}_owner",
                project_name.to_lowercase().replace('-', "_")
            )),
            db_owner_pword: Some("password".into()),
            include_server: true,
            include_frontend: true,
            include_tauri_desktop: true,
            deno_package_name: "@test/gwa-project".to_string(),
        }
    } else {
        // Standard Interactive Mode
        interactive::run_interactive_flow(args.name)?
    };

    // Generate the project using the new engine
    engine::run(&config, &args.destination).map_err(|e| e.to_string())?;

    Ok(())
}
