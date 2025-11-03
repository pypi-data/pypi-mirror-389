//! Transformation plan module - defines what transformations need to be applied

use super::EngineError;
use crate::config::ProjectConfig;
use std::path::PathBuf;

// An action to be performed on the cloned template
#[derive(Debug, PartialEq, Clone)]
pub enum Action {
    Delete(PathBuf),
    Rename {
        from: PathBuf,
        to: PathBuf,
    },
    ApplyTemplate {
        path: PathBuf,
        context: TemplateContext,
    },
}

// Data to be injected into template files
#[derive(Debug, PartialEq, Clone)]
pub struct TemplateContext {
    pub project_name: String,
    pub author_name: String,
    pub author_email: String,
    pub app_identifier: String,
    pub db_name: Option<String>,
    pub db_owner_admin: Option<String>,
    pub include_server: bool,
    pub include_frontend: bool,
    pub include_tauri_desktop: bool,
    pub deno_package_name: String,
}

// The complete list of actions to transform the template
#[derive(Debug, Default, PartialEq)]
pub struct TransformationPlan {
    pub actions: Vec<Action>,
}

pub fn build_plan(config: &ProjectConfig) -> Result<TransformationPlan, EngineError> {
    let mut plan = TransformationPlan::default();

    // 1. Plan basic deletions (files/directories not needed in final project)
    plan.actions.push(Action::Delete(PathBuf::from(".git")));
    plan.actions.push(Action::Delete(PathBuf::from(".github")));
    plan.actions
        .push(Action::Delete(PathBuf::from("ROADMAP.md")));

    // 2. Plan conditional deletions based on configuration
    if !config.include_tauri_desktop {
        plan.actions
            .push(Action::Delete(PathBuf::from("client/src-tauri")));
    }

    if !config.include_server {
        plan.actions.push(Action::Delete(PathBuf::from("backend")));
    }

    if !config.include_frontend {
        plan.actions.push(Action::Delete(PathBuf::from("frontend")));
    }

    // 3. Plan file content transformations using template context
    let context = TemplateContext {
        project_name: config.project_name.clone(),
        author_name: config.author_name.clone(),
        author_email: config.author_email.clone(),
        app_identifier: config.app_identifier.clone(),
        db_name: config.db_name.clone(),
        db_owner_admin: config.db_owner_admin.clone(),
        include_server: config.include_server,
        include_frontend: config.include_frontend,
        include_tauri_desktop: config.include_tauri_desktop,
        deno_package_name: config.deno_package_name.clone(),
    };

    // Apply template to key files that contain placeholders
    plan.actions.push(Action::ApplyTemplate {
        path: PathBuf::from("README.md"),
        context: context.clone(),
    });

    plan.actions.push(Action::ApplyTemplate {
        path: PathBuf::from("docker-compose.yml"),
        context: context.clone(),
    });

    plan.actions.push(Action::ApplyTemplate {
        path: PathBuf::from("Cargo.toml"),
        context: context.clone(),
    });

    plan.actions.push(Action::ApplyTemplate {
        path: PathBuf::from("client/package.json"),
        context: context.clone(),
    });

    // 4. Plan renaming of the client directory to match the project name
    plan.actions.push(Action::Rename {
        from: PathBuf::from("client"),
        to: PathBuf::from(&config.project_name),
    });

    println!(
        "📝 Transformation plan built with {} actions",
        plan.actions.len()
    );

    Ok(plan)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::ProjectConfig;

    #[test]
    fn test_plan_generation_with_all_components() {
        // Arrange: Create a sample config with all components enabled
        let config = ProjectConfig {
            project_name: "my-app".to_string(),
            author_name: "Test User".to_string(),
            author_email: "test@example.com".to_string(),
            app_identifier: "com.example.myapp".to_string(),
            db_name: Some("my_app".to_string()),
            db_owner_admin: Some("my_app_owner".to_string()),
            db_owner_pword: Some("password".to_string()),
            include_server: true,
            include_frontend: true,
            include_tauri_desktop: true,
            deno_package_name: "@test/my-app".to_string(),
        };

        // Act: Build the plan
        let plan = build_plan(&config).unwrap();

        // Assert: Check for expected actions
        // 1. Check for basic deletions
        assert!(
            plan.actions
                .contains(&Action::Delete(PathBuf::from(".github")))
        );
        assert!(
            plan.actions
                .contains(&Action::Delete(PathBuf::from("ROADMAP.md")))
        );

        // 2. Check that Tauri directory is NOT deleted when include_tauri_desktop is true
        assert!(
            !plan
                .actions
                .contains(&Action::Delete(PathBuf::from("client/src-tauri")))
        );

        // 3. Check for template application
        let expected_context = TemplateContext {
            project_name: "my-app".to_string(),
            author_name: "Test User".to_string(),
            author_email: "test@example.com".to_string(),
            app_identifier: "com.example.myapp".to_string(),
            db_name: Some("my_app".to_string()),
            db_owner_admin: Some("my_app_owner".to_string()),
            include_server: true,
            include_frontend: true,
            include_tauri_desktop: true,
            deno_package_name: "@test/my-app".to_string(),
        };

        assert!(plan.actions.contains(&Action::ApplyTemplate {
            path: PathBuf::from("README.md"),
            context: expected_context.clone(),
        }));
    }

    #[test]
    fn test_plan_generation_without_tauri() {
        // Arrange: Create a config with Tauri disabled
        let config = ProjectConfig {
            project_name: "my-app".to_string(),
            include_tauri_desktop: false,
            db_owner_pword: Some("password".to_string()),
            ..Default::default()
        };

        // Act: Build the plan
        let plan = build_plan(&config).unwrap();

        // Assert: Tauri directory SHOULD be in the delete list
        assert!(
            plan.actions
                .contains(&Action::Delete(PathBuf::from("client/src-tauri")))
        );
    }

    #[test]
    fn test_plan_generation_without_server() {
        // Arrange: Create a config with server disabled
        let config = ProjectConfig {
            project_name: "my-app".to_string(),
            include_server: false,
            db_owner_pword: Some("password".to_string()),
            ..Default::default()
        };

        // Act: Build the plan
        let plan = build_plan(&config).unwrap();

        // Assert: Backend directory SHOULD be in the delete list
        assert!(
            plan.actions
                .contains(&Action::Delete(PathBuf::from("backend")))
        );
    }

    #[test]
    fn test_plan_generation_without_frontend() {
        // Arrange: Create a config with frontend disabled
        let config = ProjectConfig {
            project_name: "my-app".to_string(),
            include_frontend: false,
            db_owner_pword: Some("password".to_string()),
            ..Default::default()
        };

        // Act: Build the plan
        let plan = build_plan(&config).unwrap();

        // Assert: Frontend directory SHOULD be in the delete list
        assert!(
            plan.actions
                .contains(&Action::Delete(PathBuf::from("frontend")))
        );
    }

    #[test]
    fn test_plan_generation_with_rename_action() {
        // Arrange: Create a sample config
        let config = ProjectConfig {
            project_name: "my-shiny-new-app".to_string(),
            include_tauri_desktop: true,
            db_owner_pword: Some("password".to_string()),
            ..Default::default()
        };

        // Act: Build the plan
        let plan = build_plan(&config).unwrap();

        // Assert: Check for the rename action
        assert!(plan.actions.contains(&Action::Rename {
            from: PathBuf::from("client"),
            to: PathBuf::from("my-shiny-new-app"),
        }));
    }
}
