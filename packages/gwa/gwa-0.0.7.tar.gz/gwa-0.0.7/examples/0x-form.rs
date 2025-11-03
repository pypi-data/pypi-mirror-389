// src/main.rs (for your gwa-create binary)
#![allow(unused)]

use clap::Parser; // This IS used for #[derive(Parser)]
use inquire::{
    Confirm,
    // CustomType, // Not used in this version
    Password,
    PasswordDisplayMode,
    Select,
    Text,
    validator::{ErrorMessage, Validation},
};
// use std::collections::HashMap; // Not used yet if cargo-generate is commented out
use std::error::Error;
use std::path::PathBuf; // This IS used for CliArgs output_dir

// Define the structure for CLI arguments using clap
#[derive(Parser, Debug)]
#[clap(
    author,
    version,
    about = "CLI to generate a new General Web App (GWA) project"
)]
struct CliArgs {
    /// Name of the new GWA project (directory name)
    #[clap(index = 1)] // Positional argument
    project_name_arg: Option<String>,

    /// Output directory for the new project
    #[clap(short, long, default_value = ".")]
    output_dir: PathBuf,

    /// Skip interactive prompts and use defaults (or fail if not all provided)
    #[clap(short = 'y', long, default_value_t = false)]
    yes: bool,
}

// Structure to hold collected project configuration
#[derive(Debug)]
struct ProjectConfig {
    project_name: String,
    author_name: String,
    author_email: String,
    app_identifier: String,
    db_name: String,
    db_owner_admin: String,
    db_owner_pword: String,
    include_tauri: bool,
    // Add more fields as needed for your GWA template
}

fn main() -> Result<(), Box<dyn Error>> {
    let cli_args = CliArgs::parse(); // CliArgs is now defined above

    println!("🚀 Welcome to the General Web App (GWA) project generator!");
    println!("------------------------------------------------------");

    // --- 1. Get Project Name ---
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

    // --- 2. Author Information ---
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

    let author_email_validator = |input: &str| {
        if input.trim().is_empty() || !input.contains('@') || !input.contains('.') {
            Ok(Validation::Invalid(ErrorMessage::Custom(
                "Please enter a valid email address.".into(),
            )))
        } else {
            Ok(Validation::Valid)
        }
    };
    let author_email = Text::new("Author's email address (e.g., ada@example.com):")
        .with_validator(author_email_validator)
        .prompt()?;

    // --- 3. Application Specifics ---
    let default_app_id = format!(
        "com.example.{}",
        project_name.to_lowercase().replace('-', "")
    );
    let app_identifier = Text::new("Application Identifier (e.g., com.company.appname):")
        .with_initial_value(&default_app_id)
        .with_help_message("Used for Tauri bundle ID, Android package name, etc.")
        .with_validator(|input: &str| {
            let parts: Vec<&str> = input.split('.').collect();
            if parts.len() < 2 || parts.iter().any(|p| p.is_empty() || p.chars().any(|c| !c.is_alphanumeric() && c != '_')) {
                Ok(Validation::Invalid(ErrorMessage::Custom("Identifier should be in reverse domain name notation (e.g., com.example.app), using only alphanumerics and underscores within parts.".into())))
            } else {
                Ok(Validation::Valid)
            }
        })
        .prompt()?;

    // --- 4. Database Configuration (Example) ---
    println!("\n--- Database Configuration ---");
    let db_name = Text::new("Database name:")
        .with_initial_value(&project_name.to_lowercase().replace('-', "_"))
        .prompt()?;

    let db_owner_admin = Text::new("Database owner/admin username:")
        .with_initial_value(&format!(
            "{}_owner",
            project_name.to_lowercase().replace('-', "_")
        ))
        .prompt()?;

    let db_owner_pword = Password::new("Database owner/admin password:")
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
        .prompt()?;

    // --- 5. Optional Features ---
    let include_tauri = Confirm::new("Include Tauri desktop application setup?")
        .with_default(true)
        .prompt()?;

    let framework_options = vec!["SvelteKit (Default)", "Other (Placeholder)"];
    let _chosen_framework = Select::new(
        "Choose frontend framework (GWA currently uses SvelteKit):",
        framework_options,
    )
    .prompt()?;

    // --- Store collected configuration ---
    let config = ProjectConfig {
        // ProjectConfig is now defined above
        project_name: project_name.clone(),
        author_name,
        author_email,
        app_identifier,
        db_name,
        db_owner_admin,
        db_owner_pword,
        include_tauri,
    };

    println!("\n--- Configuration Summary ---");
    println!("{:#?}", config); // Pretty print the collected config
    println!("Output directory: {:?}", cli_args.output_dir);

    // --- Confirmation before proceeding ---
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

    // --- TODO: Here you would call cargo_generate::generate ---
    println!("\nSimulating project generation...");
    // The HashMap import is needed if you uncomment the simulation variables below
    // or when you actually prepare variables for cargo-generate.
    // use std::collections::HashMap; // <--- Add this if using HashMap
    let mut template_variables = std::collections::HashMap::new(); // Use full path if not `use`d
    template_variables.insert("project_name".to_string(), config.project_name.clone());
    template_variables.insert("author_name".to_string(), config.author_name.clone());
    template_variables.insert("author_email".to_string(), config.author_email.clone());
    // ... add other variables

    println!("Variables to pass to cargo-generate (simulated):");
    for (key, value) in &template_variables {
        if key == "db_owner_pword" {
            // This was for the ProjectConfig struct, not template_variables
            println!("  {}: [REDACTED]", key);
        } else {
            println!("  {}: {}", key, value);
        }
    }
    // Note: The db_owner_pword from the config struct should be added to template_variables
    // if your template needs it. The redaction logic above was slightly misplaced if
    // db_owner_pword wasn't yet in template_variables.

    // Actual call would look something like:
    /*
    use cargo_generate::{generate, GenerateArgs, TemplatePath, Variables as CgVariables};
    use std::collections::HashMap; // Ensure this is imported

    // ... (populate template_variables as above)
    // template_variables.insert("db_owner_pword".to_string(), config.db_owner_pword.clone()); // Add sensitive data carefully

    let mut cg_vars = CgVariables::new();
    for (key, value) in template_variables {
        cg_vars.insert(key, value.into());
    }

    let template_path = TemplatePath {
        git: Some("https://github.com/Yrrrrrf/gwa.git".to_string()),
        branch: Some("v0.1.0".to_string()),
        ..Default::default()
    };

    let gen_args = GenerateArgs {
        template_path,
        name: Some(config.project_name), // This is the directory name of the generated project
        output_path: Some(cli_args.output_dir), // Where to place the generated project
        define: cg_vars.into_iter().map(|(k, v)| format!("{}={}", k, v.as_str().unwrap_or_default())).collect(),
        verbose: true,
        ..Default::default()
    };

    match generate(gen_args) {
        Ok(path) => println!("Project generated successfully at: {:?}", path),
        Err(e) => eprintln!("Error generating project: {}", e),
    }
    */

    println!("\n✅ GWA project setup initiated (simulation complete).");
    println!("Please integrate with `cargo-generate` to perform actual file generation.");

    Ok(())
}
