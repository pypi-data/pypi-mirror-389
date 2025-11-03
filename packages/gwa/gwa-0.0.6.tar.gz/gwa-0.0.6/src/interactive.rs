// src/interactive.rs

use crate::config::{GwaComponent, ProjectConfig};
use crate::validators::*;
use inquire::{Confirm, MultiSelect, Password, PasswordDisplayMode, Text};
use std::error::Error;

pub fn run_interactive_flow(
    project_name_arg: Option<String>,
) -> Result<ProjectConfig, Box<dyn Error>> {
    let mut config = ProjectConfig::default();

    // --- 1. Collect Project Name (Essential) ---
    config.project_name = match project_name_arg {
        Some(name) => {
            println!("✔️ Project name provided: {}", name);
            name
        }
        None => Text::new("Enter the name for your new project (e.g., my-awesome-app):")
            .with_validator(validate_project_name)
            .prompt()?,
    };

    // --- (Optional but useful) Author Information ---
    // For faster testing, we use defaults. Uncomment to make it fully interactive.
    config.author_name = "Test User".into();
    config.author_email = "test@example.com".into();
    println!(
        "✔️ Using default author: Test User <test@example.com> (can be changed in generated files)"
    );

    // --- 2. Modular Component Selection (Essential) ---
    println!("\n--- Component Selection ---");
    let component_options = vec![GwaComponent::Server, GwaComponent::Frontend];
    let selected_components =
        MultiSelect::new("Select the core components to include:", component_options)
            .with_help_message("Use [space] to toggle, [enter] to confirm. Both are recommended.")
            .prompt()?;
    config.include_server = selected_components.contains(&GwaComponent::Server);
    config.include_frontend = selected_components.contains(&GwaComponent::Frontend);

    // --- 3. Conditional Prompts ---
    if config.include_frontend {
        println!("\n--- Frontend & Desktop Configuration ---");
        let default_app_id = format!(
            "com.example.{}",
            config.project_name.to_lowercase().replace('-', "")
        );
        config.app_identifier = Text::new("Application Identifier:")
            .with_initial_value(&default_app_id)
            .with_help_message("e.g., com.company.appname")
            .with_validator(validate_app_id)
            .prompt()?;
        config.include_tauri_desktop = Confirm::new("Include Tauri for desktop app support?")
            .with_default(true)
            .prompt()?;
    }

    if config.include_server {
        println!("\n--- Database Configuration ---");
        config.db_name = Some(
            Text::new("Database name:")
                .with_initial_value(&config.project_name.to_lowercase().replace('-', "_"))
                .prompt()?,
        );
        config.db_owner_admin = Some(
            Text::new("Database owner username:")
                .with_initial_value(&format!(
                    "{}_owner",
                    config.project_name.to_lowercase().replace('-', "_")
                ))
                .prompt()?,
        );
        config.db_owner_pword = Some(
            Password::new("Database owner password:")
                .with_display_mode(PasswordDisplayMode::Masked)
                .with_validator(validate_password)
                .prompt()?,
        );
    }

    // --- Final Confirmation ---
    println!("\n--- Configuration Summary ---");
    println!("{:#?}", config);

    let proceed = Confirm::new(&format!(
        "Generate project '{}' with this configuration?",
        config.project_name
    ))
    .with_default(true)
    .prompt()?;
    if !proceed {
        // A clean way to signal cancellation.
        return Err("Project generation cancelled by user.".into());
    }

    Ok(config)
}
