// src/main.rs (for your gwa-create binary)

use clap::Parser;
use inquire::{
    Confirm,
    MultiSelect,
    Password,
    PasswordDisplayMode,
    // Select, // Commented out if not used for framework selection anymore
    Text,
    validator::{ErrorMessage, Validation},
};
use std::collections::HashMap;
use std::error::Error;
use std::path::PathBuf;

// Define the structure for CLI arguments using clap
#[derive(Parser, Debug)]
#[clap(
    author,
    version,
    about = "CLI to generate a new General Web App (GWA) project"
)]
struct CliArgs {
    #[clap(index = 1)]
    project_name_arg: Option<String>,
    #[clap(short, long, default_value = ".")]
    output_dir: PathBuf,
    #[clap(short = 'y', long, default_value_t = false)]
    yes: bool,
}

// Enum for component choices for better type safety
#[derive(Debug, Clone, PartialEq)]
enum GwaComponent {
    Server,
    Frontend,
}

impl std::fmt::Display for GwaComponent {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GwaComponent::Server => write!(f, "Backend Server (PostgreSQL + FastAPI)"),
            GwaComponent::Frontend => write!(f, "Frontend Application (SvelteKit + Deno)"),
        }
    }
}

#[derive(Debug)]
struct ProjectConfig {
    project_name: String,
    author_name: String,
    author_email: String,
    app_identifier: String,
    db_name: Option<String>,
    db_owner_admin: Option<String>,
    db_owner_pword: Option<String>,
    include_server: bool,
    include_frontend: bool,
    include_tauri_desktop: bool,
    include_tauri_android_poc: bool,
}

fn main() -> Result<(), Box<dyn Error>> {
    let cli_args = CliArgs::parse();

    println!("🚀 Welcome to the General Web App (GWA) project generator!");
    println!("------------------------------------------------------");

    let project_name = match cli_args.project_name_arg {
        Some(name) => {
            println!("Using project name from argument: {}", name);
            name
        }
        None => Text::new("Enter the name for your new project (e.g., my-awesome-app):")
            .with_validator(|input: &str| {
                if input.trim().is_empty() {
                    Ok(Validation::Invalid(ErrorMessage::Custom(
                        "Project name cannot be empty.".into(),
                    )))
                } else if input.contains('/') || input.contains('\\') || input.contains(' ') {
                    Ok(Validation::Invalid(ErrorMessage::Custom(
                        "Project name should be a valid directory name (no spaces or slashes)."
                            .into(),
                    )))
                } else {
                    Ok(Validation::Valid)
                }
            })
            .prompt()?,
    };

    let author_name = Text::new("Author's full name (e.g., Ada Lovelace):")
        .with_validator(|input: &str| {
            if input.trim().is_empty() {
                Ok(Validation::Invalid(ErrorMessage::Custom(
                    "Author name cannot be empty.".into(),
                )))
            } else {
                Ok(Validation::Valid)
            }
        })
        .prompt()?;
    let author_email = Text::new("Author's email address (e.g., ada@example.com):")
        .with_validator(|input: &str| {
            if input.trim().is_empty() || !input.contains('@') || !input.contains('.') {
                Ok(Validation::Invalid(ErrorMessage::Custom(
                    "Please enter a valid email address.".into(),
                )))
            } else {
                Ok(Validation::Valid)
            }
        })
        .prompt()?;

    println!("\n--- Component Selection ---");
    let component_options = vec![GwaComponent::Server, GwaComponent::Frontend];
    let selected_components =
        MultiSelect::new("Select the core components to include:", component_options)
            .with_help_message(
                "Use space to toggle, enter to confirm. At least one component is recommended.",
            )
            .prompt()?;

    let include_server = selected_components.contains(&GwaComponent::Server);
    let include_frontend = selected_components.contains(&GwaComponent::Frontend);

    if !include_server && !include_frontend {
        println!(
            "⚠️ Warning: No core components selected. This might result in a very minimal project."
        );
    }

    let mut include_tauri_desktop = false;
    let mut include_tauri_android_poc = false;
    let mut app_identifier = String::new();

    if include_frontend {
        println!("\n--- Frontend & Desktop Configuration ---");
        let default_app_id = format!(
            "com.example.{}",
            project_name.to_lowercase().replace('-', "")
        );
        app_identifier = Text::new("Application Identifier (e.g., com.company.appname):")
            .with_initial_value(&default_app_id)
            .with_help_message("Required if Frontend is selected, used for Tauri bundle ID, PWA manifest, etc.")
            .with_validator(|input: &str| {
                let parts: Vec<&str> = input.split('.').collect();
                if parts.len() < 2 || parts.iter().any(|p| p.is_empty() || p.chars().any(|c| !c.is_alphanumeric() && c != '_')) {
                    Ok(Validation::Invalid(ErrorMessage::Custom("Identifier should be in reverse domain name notation (e.g., com.example.app).".into())))
                } else { Ok(Validation::Valid) }
            })
            .prompt()?;

        include_tauri_desktop = Confirm::new("Include Tauri for Desktop application support?")
            .with_default(true)
            .prompt()?;

        if include_tauri_desktop {
            include_tauri_android_poc =
                Confirm::new("Include experimental Tauri for Android (Proof-of-Concept)?")
                    .with_default(false)
                    .with_help_message("GWA has basic PoC for Android, full support is ongoing.")
                    .prompt()?;
        }
    }

    let mut db_name_opt: Option<String> = None;
    let mut db_owner_admin_opt: Option<String> = None;
    let mut db_owner_pword_opt: Option<String> = None;

    if include_server {
        println!("\n--- Database Configuration (Required for Server) ---");
        db_name_opt = Some(
            Text::new("Database name:")
                .with_initial_value(&project_name.to_lowercase().replace('-', "_"))
                .prompt()?,
        );
        db_owner_admin_opt = Some(
            Text::new("Database owner/admin username:")
                .with_initial_value(&format!(
                    "{}_owner",
                    project_name.to_lowercase().replace('-', "_")
                ))
                .prompt()?,
        );
        db_owner_pword_opt = Some(
            Password::new("Database owner/admin password:")
                .with_display_mode(PasswordDisplayMode::Masked)
                .with_help_message("Enter the password. You will be asked to confirm it.")
                .with_validator(|input: &str| {
                    if input.len() < 8 {
                        Ok(Validation::Invalid(ErrorMessage::Custom(
                            "Password must be at least 8 characters long.".into(),
                        )))
                    } else {
                        Ok(Validation::Valid)
                    }
                })
                .prompt()?,
        );
    }

    let config = ProjectConfig {
        project_name: project_name.clone(),
        author_name,
        author_email,
        app_identifier,
        db_name: db_name_opt,
        db_owner_admin: db_owner_admin_opt,
        db_owner_pword: db_owner_pword_opt,
        include_server,
        include_frontend,
        include_tauri_desktop,
        include_tauri_android_poc,
    };

    println!("\n--- Configuration Summary ---");
    println!("{:#?}", config);
    println!("Output directory: {:?}", cli_args.output_dir);

    if !cli_args.yes {
        let proceed = Confirm::new(&format!(
            "Generate project '{}' with the above configuration?",
            config.project_name
        ))
        .with_default(true)
        .prompt()?;
        if !proceed {
            println!("Project generation cancelled by user.");
            return Ok(());
        }
    }

    println!("\nSimulating project generation...");
    let mut template_variables = HashMap::new();
    template_variables.insert("project_name".to_string(), config.project_name.clone());
    template_variables.insert("author_name".to_string(), config.author_name.clone());
    template_variables.insert("author_email".to_string(), config.author_email.clone());
    if !config.app_identifier.is_empty() {
        template_variables.insert("app_identifier".to_string(), config.app_identifier.clone());
    }
    template_variables.insert(
        "include_server".to_string(),
        config.include_server.to_string(),
    );
    template_variables.insert(
        "include_frontend".to_string(),
        config.include_frontend.to_string(),
    );
    template_variables.insert(
        "include_tauri_desktop".to_string(),
        config.include_tauri_desktop.to_string(),
    );
    template_variables.insert(
        "include_tauri_android_poc".to_string(),
        config.include_tauri_android_poc.to_string(),
    );
    if let Some(db_name) = &config.db_name {
        template_variables.insert("db_name".to_string(), db_name.clone());
    }
    if let Some(db_admin) = &config.db_owner_admin {
        template_variables.insert("db_owner_admin".to_string(), db_admin.clone());
    }
    if config.db_owner_pword.is_some() {
        template_variables.insert("db_owner_pword_provided".to_string(), "true".to_string());
    }

    println!("Variables to pass to cargo-generate (simulated):");
    for (key, value) in &template_variables {
        println!("  {}: {}", key, value);
    }

    println!("\n✅ GWA project setup initiated (simulation complete).");
    println!("Please integrate with `cargo-generate` to perform actual file generation.");
    println!("Your GWA template will need Liquid `{{% if include_server %}}` etc. tags."); // CORRECTED LINE

    Ok(())
}
