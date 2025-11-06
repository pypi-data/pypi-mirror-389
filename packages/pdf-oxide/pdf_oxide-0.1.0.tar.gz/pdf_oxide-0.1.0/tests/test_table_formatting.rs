//! Regression tests for table formatting quality
//!
//! MEDIUM SEVERITY: Tables should be properly formatted in markdown
//! with clear structure, aligned columns, and readable data.
//!
//! Observations:
//! - Forms produce excellent tables (8/10 quality)
//! - Academic papers have semi-readable tables but poor alignment
//! - Some tables lose structure entirely
//!
//! Goal: Apply the successful form extraction logic to all table types

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;

const FORM_PDF: &str = "../pdf_oxide_tests/pdfs/forms/irs_f1040.pdf";
const ACADEMIC_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Check if markdown contains properly formatted tables
fn check_table_formatting(markdown: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Count table rows
    let table_rows = markdown.lines()
        .filter(|line| line.contains('|') && line.matches('|').count() >= 2)
        .count();

    if table_rows == 0 {
        return issues; // No tables to check
    }

    println!("Found {} table rows", table_rows);

    // Check for table headers (should have separator row)
    let has_separator = markdown.lines()
        .any(|line| line.contains("|---") || line.contains("|--"));

    if !has_separator && table_rows > 0 {
        issues.push("Table found but missing header separator row".to_string());
    }

    // Check for consistent column counts
    let column_counts: Vec<usize> = markdown.lines()
        .filter(|line| line.contains('|') && line.matches('|').count() >= 2)
        .map(|line| line.matches('|').count())
        .collect();

    if !column_counts.is_empty() {
        let first_count = column_counts[0];
        let inconsistent = column_counts.iter().any(|&c| c != first_count);

        if inconsistent {
            issues.push(format!(
                "Inconsistent column counts in table: {:?}",
                &column_counts[..5.min(column_counts.len())]
            ));
        }
    }

    issues
}

#[test]
fn test_form_table_quality() {
    let mut doc = PdfDocument::open(FORM_PDF)
        .expect("Failed to open form PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    let issues = check_table_formatting(&markdown);

    assert!(
        issues.is_empty(),
        "Form table formatting issues: {:?}",
        issues
    );

    // Forms may or may not have markdown tables (depends on structure detection)
    if markdown.contains('|') {
        println!("✅ Form table formatting is good");
    } else {
        println!("ℹ️  Form extracted as structured text (table detection not triggered)");
    }
}

#[test]
fn test_academic_table_structure() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    if markdown.contains('|') {
        let issues = check_table_formatting(&markdown);

        if !issues.is_empty() {
            println!("⚠️ Academic table issues:");
            for issue in &issues {
                println!("  - {}", issue);
            }
        }

        println!("✅ Academic table structure checked");
    } else {
        println!("ℹ️ No tables detected in academic PDF");
    }
}

#[test]
fn test_table_cell_content_preservation() {
    let mut doc = PdfDocument::open(FORM_PDF)
        .expect("Failed to open form PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    // Check that table cells aren't empty (if tables exist)
    let table_lines: Vec<&str> = markdown.lines()
        .filter(|line| line.contains('|'))
        .collect();

    if table_lines.is_empty() {
        println!("ℹ️  No tables detected in form (extracted as structured text)");
        return; // Skip test if no tables
    }

    let empty_cells = table_lines.iter()
        .filter(|line| line.contains("||") || line.contains("| |"))
        .count();

    let total_cells = table_lines.len();
    let empty_ratio = empty_cells as f64 / total_cells as f64;

    println!("Empty cells: {}/{} ({:.1}%)", empty_cells, total_cells, empty_ratio * 100.0);

    // Some empty cells are OK (empty form fields), but not > 50%
    assert!(
        empty_ratio < 0.50,
        "Too many empty table cells ({:.1}%)",
        empty_ratio * 100.0
    );

    println!("✅ Table cell content preserved");
}

#[test]
fn test_table_alignment() {
    let mut doc = PdfDocument::open(FORM_PDF)
        .expect("Failed to open form PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    // Check for alignment specifiers in header row
    let has_alignment = markdown.lines()
        .any(|line| line.contains(":---") || line.contains("---:") || line.contains(":---:"));

    if has_alignment {
        println!("✅ Table has alignment specifiers");
    } else {
        println!("ℹ️ No alignment specifiers (using default left alignment)");
    }
}
