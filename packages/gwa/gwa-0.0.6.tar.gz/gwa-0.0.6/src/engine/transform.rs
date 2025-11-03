//! Transformation executor module - applies the transformation plan to files

use super::{
    EngineError,
    plan::{Action, TemplateContext, TransformationPlan},
};
use std::fs;
use std::path::Path;

pub fn execute(plan: &TransformationPlan, temp_dir: &Path) -> Result<(), EngineError> {
    for action in &plan.actions {
        match action {
            Action::Delete(path) => {
                let full_path = temp_dir.join(path);
                if full_path.exists() {
                    if full_path.is_dir() {
                        fs::remove_dir_all(&full_path).map_err(|e| {
                            EngineError::FileSystem(format!(
                                "Failed to delete directory {:?}: {}",
                                path, e
                            ))
                        })?;
                        println!("🗑️  Deleted directory: {}", path.display());
                    } else {
                        fs::remove_file(&full_path).map_err(|e| {
                            EngineError::FileSystem(format!(
                                "Failed to delete file {:?}: {}",
                                path, e
                            ))
                        })?;
                        println!("🗑️  Deleted file: {}", path.display());
                    }
                }
            }
            Action::Rename { from, to } => {
                let from_path = temp_dir.join(from);
                let to_path = temp_dir.join(to);
                if from_path.exists() {
                    fs::rename(&from_path, &to_path).map_err(|e| {
                        EngineError::FileSystem(format!(
                            "Failed to rename {:?} to {:?}: {}",
                            from, to, e
                        ))
                    })?;
                    println!("🔄 Renamed: {} -> {}", from.display(), to.display());
                }
            }
            Action::ApplyTemplate { path, context } => {
                let full_path = temp_dir.join(path);
                if full_path.exists() && full_path.is_file() {
                    let mut content = fs::read_to_string(&full_path).map_err(|e| {
                        EngineError::FileSystem(format!(
                            "Failed to read file {:?} for templating: {}",
                            path, e
                        ))
                    })?;

                    // Apply template replacements using the context
                    content = apply_template_replacements(&content, context);

                    fs::write(&full_path, content).map_err(|e| {
                        EngineError::FileSystem(format!(
                            "Failed to write templated content to {:?}: {}",
                            path, e
                        ))
                    })?;
                    println!("📝 Applied template: {}", path.display());
                }
            }
        }
    }
    Ok(())
}

fn apply_template_replacements(content: &str, context: &TemplateContext) -> String {
    let mut result = content.to_string();

    // Replace project-specific placeholders
    result = result.replace("{{project_name}}", &context.project_name);
    result = result.replace("General Web App", &context.project_name);
    result = result.replace("gwa", &context.project_name);

    // Replace author information
    result = result.replace("{{author_name}}", &context.author_name);
    result = result.replace("{{author_email}}", &context.author_email);

    // Replace app identifier
    result = result.replace("{{app_identifier}}", &context.app_identifier);

    // Replace database information if available
    if let Some(ref db_name) = context.db_name {
        result = result.replace("{{db_name}}", db_name);
    }

    if let Some(ref db_owner_admin) = context.db_owner_admin {
        result = result.replace("{{db_owner_admin}}", db_owner_admin);
    }

    // Replace package name
    result = result.replace("{{deno_package_name}}", &context.deno_package_name);

    // Conditional replacements based on included components
    if !context.include_server {
        // Remove server-specific sections (using comment markers)
        result = remove_conditional_section(&result, "SERVER_BEGIN", "SERVER_END");
    }

    if !context.include_frontend {
        result = remove_conditional_section(&result, "FRONTEND_BEGIN", "FRONTEND_END");
    }

    if !context.include_tauri_desktop {
        result = remove_conditional_section(&result, "TAURI_BEGIN", "TAURI_END");
    }

    result
}

fn remove_conditional_section(content: &str, start_marker: &str, end_marker: &str) -> String {
    let start_tag = format!("<!-- {} -->", start_marker);
    let end_tag = format!("<!-- {} -->", end_marker);

    let mut result = content.to_string();

    while let Some(start_pos) = result.find(&start_tag) {
        if let Some(end_pos) = result.find(&end_tag) {
            if end_pos > start_pos {
                let end_marker_end = end_pos + end_tag.len();
                result = format!("{}{}", &result[..start_pos], &result[end_marker_end..]);
                continue; // Check for more sections after removing one
            }
        }
        break; // No matching end tag found, stop processing
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_transformation_execution() {
        // Arrange: Create a temporary directory with mock files
        let dir = tempdir().unwrap();
        fs::write(
            dir.path().join("README.md"),
            "Project: General Web App\nAuthor: {{author_name}}",
        )
        .unwrap();
        fs::create_dir(dir.path().join(".github")).unwrap();
        fs::write(dir.path().join(".github/issue.md"), "bug report").unwrap();

        // Arrange: Create a plan
        let mut plan = TransformationPlan::default();
        plan.actions
            .push(Action::Delete(std::path::PathBuf::from(".github")));
        plan.actions.push(Action::ApplyTemplate {
            path: std::path::PathBuf::from("README.md"),
            context: TemplateContext {
                project_name: "My New Cool App".to_string(),
                author_name: "Test User".to_string(),
                author_email: "test@example.com".to_string(),
                app_identifier: "com.example.myapp".to_string(),
                db_name: Some("my_app".to_string()),
                db_owner_admin: Some("my_app_owner".to_string()),
                include_server: true,
                include_frontend: true,
                include_tauri_desktop: true,
                deno_package_name: "@test/myapp".to_string(),
            },
        });

        // Act: Execute the transformation
        execute(&plan, dir.path()).unwrap();

        // Assert: Check the results
        // 1. Directory should be deleted
        assert!(!dir.path().join(".github").exists());

        // 2. File content should be updated
        let readme_content = fs::read_to_string(dir.path().join("README.md")).unwrap();
        assert!(readme_content.contains("My New Cool App"));
        assert!(!readme_content.contains("General Web App"));
        assert!(readme_content.contains("Test User"));
    }

    #[test]
    fn test_conditional_removal() {
        // Test that conditional sections are properly removed
        let content =
            "Line 1\n<!-- SERVER_BEGIN -->\nServer code\n<!-- SERVER_END -->\nLine 2".to_string();
        let result = remove_conditional_section(&content, "SERVER_BEGIN", "SERVER_END");
        assert_eq!(result, "Line 1\n\nLine 2");
    }
}
