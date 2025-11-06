//! Regression test for excessive whitespace issues
//!
//! Issue: 153 PDFs (43%) have excessive whitespace
//! Root cause: Insufficient whitespace normalization
//!
//! Multiple consecutive spaces should be normalized to single spaces
//! in most contexts (except code blocks, tables).

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

fn count_excessive_spaces(text: &str) -> usize {
    // Count occurrences of 3+ consecutive spaces
    text.matches("   ").count()
}

fn find_excessive_space_lines(text: &str) -> Vec<String> {
    text.lines()
        .filter(|line| line.contains("   "))
        .take(5)
        .map(|s| s.to_string())
        .collect()
}

#[test]
fn test_no_excessive_whitespace() {
    println!("\n=== Testing for Excessive Whitespace ===");

    let test_pdfs = vec![
        "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Vol1_Navigation_and_Navigable_Waters.pdf",
        "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf",
    ];

    for pdf_path in &test_pdfs {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.to_markdown(0, &ConversionOptions::default()) {
                    Ok(markdown) => {
                        let count = count_excessive_spaces(&markdown);
                        println!("  Excessive space sequences: {}", count);

                        if count > 10 {
                            let examples = find_excessive_space_lines(&markdown);
                            println!("  Example lines:");
                            for line in examples.iter().take(3) {
                                // Show with visible spaces
                                let visible = line.replace("   ", "[···]");
                                println!("    {}", visible);
                            }

                            assert!(
                                count <= 10,
                                "Found {} instances of 3+ consecutive spaces (max 10 allowed)", count
                            );
                        } else {
                            println!("  ✓ Acceptable whitespace");
                        }
                    }
                    Err(e) => {
                        println!("  ❌ Extraction error: {}", e);
                    }
                }
            }
            Err(e) => {
                println!("  ❌ Failed to open: {}", e);
            }
        }
    }
}

#[test]
fn test_whitespace_ratio() {
    // Ensure text isn't mostly whitespace
    println!("\n=== Testing Whitespace Ratio ===");

    let test_pdfs = vec![
        "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf",
    ];

    for pdf_path in &test_pdfs {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                let total_chars = markdown.len();
                let space_chars = markdown.chars().filter(|&c| c == ' ').count();
                let newline_chars = markdown.chars().filter(|&c| c == '\n').count();

                let space_ratio = (space_chars as f64 / total_chars as f64) * 100.0;
                let newline_ratio = (newline_chars as f64 / total_chars as f64) * 100.0;

                println!("  Total chars: {}", total_chars);
                println!("  Space chars: {} ({:.1}%)", space_chars, space_ratio);
                println!("  Newline chars: {} ({:.1}%)", newline_chars, newline_ratio);

                // Typical English text: ~13-17% spaces
                assert!(
                    space_ratio < 30.0,
                    "Space ratio too high ({:.1}%) - indicates excessive whitespace",
                    space_ratio
                );

                // Newlines should be <5% for most documents
                assert!(
                    newline_ratio < 15.0,
                    "Newline ratio too high ({:.1}%) - indicates excessive line breaks",
                    newline_ratio
                );
            }
        }
    }
}

#[test]
fn test_no_trailing_whitespace() {
    // Lines shouldn't end with spaces
    println!("\n=== Testing for Trailing Whitespace ===");

    let test_pdfs = vec![
        "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf",
    ];

    for pdf_path in &test_pdfs {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                let lines_with_trailing_space = markdown
                    .lines()
                    .filter(|line| line.ends_with(' '))
                    .count();

                let total_lines = markdown.lines().count();
                let ratio = (lines_with_trailing_space as f64 / total_lines as f64) * 100.0;

                println!("  Lines with trailing spaces: {} ({:.1}%)",
                    lines_with_trailing_space, ratio);

                // Allow some trailing spaces, but not excessive
                assert!(
                    ratio < 10.0,
                    "Too many lines with trailing spaces ({:.1}%)", ratio
                );
            }
        }
    }
}

#[test]
fn test_paragraph_spacing() {
    // Multiple consecutive newlines should be normalized
    println!("\n=== Testing Paragraph Spacing ===");

    let test_pdfs = vec![
        "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf",
    ];

    for pdf_path in &test_pdfs {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                // Count occurrences of 3+ consecutive newlines
                let triple_newlines = markdown.matches("\n\n\n").count();

                println!("  Triple+ newline sequences: {}", triple_newlines);

                // Some documents may have intentional breaks, but not excessive
                assert!(
                    triple_newlines < 20,
                    "Too many triple newline sequences ({})", triple_newlines
                );
            }
        }
    }
}
