// src/validators.rs

use inquire::{error::CustomUserError, validator::Validation};

pub type ValidatorResult = Result<Validation, CustomUserError>;

pub fn required(value: &str) -> ValidatorResult {
    if value.trim().is_empty() {
        Ok(Validation::Invalid("This field is required.".into()))
    } else {
        Ok(Validation::Valid)
    }
}

pub fn validate_project_name(input: &str) -> ValidatorResult {
    if input.trim().is_empty() {
        Ok(Validation::Invalid("Project name cannot be empty.".into()))
    } else if input.contains(['/', '\\', ' ']) {
        Ok(Validation::Invalid(
            "Must be a valid directory name (no spaces or slashes).".into(),
        ))
    } else {
        Ok(Validation::Valid)
    }
}

pub fn validate_email(input: &str) -> ValidatorResult {
    if input.trim().is_empty() || !input.contains('@') || !input.contains('.') {
        Ok(Validation::Invalid(
            "Please enter a valid email address.".into(),
        ))
    } else {
        Ok(Validation::Valid)
    }
}

pub fn validate_app_id(input: &str) -> ValidatorResult {
    let parts: Vec<&str> = input.split('.').collect();
    if parts.len() < 2
        || parts
            .iter()
            .any(|p| p.is_empty() || p.chars().any(|c| !c.is_alphanumeric() && c != '_'))
    {
        Ok(Validation::Invalid(
            "Must be reverse domain name notation (e.g., com.example.app).".into(),
        ))
    } else {
        Ok(Validation::Valid)
    }
}

pub fn validate_password(input: &str) -> ValidatorResult {
    if input.len() < 8 {
        Ok(Validation::Invalid(
            "Password must be at least 8 characters long.".into(),
        ))
    } else {
        Ok(Validation::Valid)
    }
}
