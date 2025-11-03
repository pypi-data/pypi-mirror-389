#![allow(dead_code)]

// src/config.rs

#[derive(Debug, Clone, PartialEq)]
pub enum GwaComponent {
    Server,
    Frontend,
}

impl std::fmt::Display for GwaComponent {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GwaComponent::Server => write!(f, "Backend Server (PostgreSQL + FastAPI)"),
            GwaComponent::Frontend => write!(f, "Frontend Application (SvelteKit + Deno + Tauri)"),
        }
    }
}

#[derive(Debug, Default)]
pub struct ProjectConfig {
    pub project_name: String,
    pub author_name: String,
    pub author_email: String,
    pub app_identifier: String,
    pub db_name: Option<String>,
    pub db_owner_admin: Option<String>,
    pub db_owner_pword: Option<String>,
    pub include_server: bool,
    pub include_frontend: bool,
    pub include_tauri_desktop: bool,
    pub deno_package_name: String,
}
