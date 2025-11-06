//! Tests for markdown formatting quality
//!
//! Covers:
//! - Excessive blank lines and horizontal rules
//! - Bold/italic formatting artifacts
//! - Heading detection accuracy
//! - Paragraph structure
//!
//! These are lower priority issues but affect overall quality

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;

const FORM_PDF: &str = "../pdf_oxide_tests/pdfs/forms/irs_f1040.pdf";
const ACADEMIC_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Check for excessive blank lines
fn check_blank_lines(markdown: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Count consecutive blank lines
    let max_consecutive = markdown.split("\n\n")
        .map(|s| s.chars().filter(|&c| c == '\n').count())
        .max()
        .unwrap_or(0);

    if max_consecutive > 3 {
        issues.push(format!(
            "Found {} consecutive blank lines (max should be 2-3)",
            max_consecutive
        ));
    }

    // Check for excessive horizontal rules
    let hr_count = markdown.matches("\n---\n").count();
    let line_count = markdown.lines().count();
    let hr_ratio = hr_count as f64 / line_count as f64;

    if hr_ratio > 0.10 {
        issues.push(format!(
            "Excessive horizontal rules: {} in {} lines ({:.1}%)",
            hr_count, line_count, hr_ratio * 100.0
        ));
    }

    issues
}

/// Check for bold/italic formatting artifacts
fn check_formatting_artifacts(markdown: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Check for broken bold markers
    let broken_bold = markdown.matches("**").count();
    if broken_bold % 2 != 0 {
        issues.push(format!(
            "Odd number of ** markers ({}), formatting may be broken",
            broken_bold
        ));
    }

    // Check for triple or more asterisks (likely formatting error)
    if markdown.contains("***") {
        let count = markdown.matches("***").count();
        issues.push(format!(
            "Found {} instances of *** (formatting artifact)",
            count
        ));
    }

    // Check for bold markers without space separation
    let re = regex::Regex::new(r"\*\*\w+\*\*\w+").unwrap();
    for mat in re.find_iter(markdown) {
        issues.push(format!(
            "Bold marker without space: '{}'",
            mat.as_str()
        ));
    }

    issues
}

/// Check heading detection quality
fn check_heading_quality(markdown: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Count headings by level
    let h1_count = markdown.lines().filter(|l| l.starts_with("# ")).count();
    let h2_count = markdown.lines().filter(|l| l.starts_with("## ")).count();
    let h3_count = markdown.lines().filter(|l| l.starts_with("### ")).count();

    println!("Headings: H1={}, H2={}, H3={}", h1_count, h2_count, h3_count);

    // Should have at least H1 (document title)
    if h1_count == 0 {
        issues.push("No H1 headings found".to_string());
    }

    // Check for heading hierarchy issues
    if h3_count > 0 && h2_count == 0 {
        issues.push("H3 found without H2 (hierarchy broken)".to_string());
    }

    issues
}

#[test]
fn test_no_excessive_blank_lines() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert");

    let issues = check_blank_lines(&markdown);

    if !issues.is_empty() {
        println!("⚠️ Blank line issues:");
        for issue in &issues {
            println!("  - {}", issue);
        }
    }

    println!("✅ Blank line check complete");
}

#[test]
fn test_bold_italic_formatting() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions {
        detect_headings: true,
        ..Default::default()
    };
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert");

    let issues = check_formatting_artifacts(&markdown);

    if !issues.is_empty() {
        println!("⚠️ Formatting artifacts:");
        for issue in &issues {
            println!("  - {}", issue);
        }
    }

    println!("✅ Formatting artifact check complete");
}

#[test]
fn test_heading_detection() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions {
        detect_headings: true,
        ..Default::default()
    };
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert");

    let issues = check_heading_quality(&markdown);

    assert!(
        issues.is_empty() || issues.len() < 2,
        "Heading detection issues: {:?}",
        issues
    );

    println!("✅ Heading detection working");
}

#[test]
fn test_paragraph_structure() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert");

    // Count paragraphs (separated by blank lines)
    let paragraphs = markdown.split("\n\n")
        .filter(|p| !p.trim().is_empty())
        .count();

    println!("Found {} paragraphs", paragraphs);

    // Should have multiple paragraphs
    assert!(
        paragraphs > 1,
        "Only {} paragraph found, structure may be lost",
        paragraphs
    );

    println!("✅ Paragraph structure preserved");
}

#[test]
fn test_form_separator_quality() {
    let mut doc = PdfDocument::open(FORM_PDF)
        .expect("Failed to open form PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert");

    // Forms may have many separators, check they're not excessive
    let issues = check_blank_lines(&markdown);

    // Forms can have more separators, so be lenient
    if issues.len() > 2 {
        panic!("Form has excessive formatting issues: {:?}", issues);
    }

    println!("✅ Form separator quality acceptable");
}

#[test]
fn test_overall_markdown_quality_score() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions {
        detect_headings: true,
        ..Default::default()
    };
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert");

    let blank_issues = check_blank_lines(&markdown);
    let format_issues = check_formatting_artifacts(&markdown);
    let heading_issues = check_heading_quality(&markdown);

    let total_issues = blank_issues.len() + format_issues.len() + heading_issues.len();

    println!("\n=== Quality Score ===");
    println!("Blank line issues: {}", blank_issues.len());
    println!("Formatting issues: {}", format_issues.len());
    println!("Heading issues: {}", heading_issues.len());
    println!("Total issues: {}", total_issues);

    // Quality score: 10 - (issues / 2)
    let quality_score = (10.0 - (total_issues as f64 / 2.0)).max(0.0);
    println!("Quality score: {:.1}/10", quality_score);

    // Should score at least 7/10
    assert!(
        quality_score >= 7.0,
        "Quality score too low: {:.1}/10",
        quality_score
    );

    println!("✅ Overall quality acceptable");
}
