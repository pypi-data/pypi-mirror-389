// src/cli.rs

use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[clap(
    author,
    version,
    about = "A lightning-fast scaffolder for General Web App (GWA) projects."
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Create a new GWA project from the template.
    Create(CreateArgs),
}

#[derive(Parser, Debug)]
pub struct CreateArgs {
    /// Name for the new project directory.
    pub name: Option<String>,

    /// The directory where the new project folder will be placed.
    #[clap(short, long, default_value = ".")]
    pub destination: PathBuf,

    /// Skip all interactive prompts and use default values for rapid testing.
    #[clap(short = 'y', long, default_value_t = false)]
    pub yes: bool,
}
