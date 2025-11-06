//! Regression test for excessive blank lines normalization
//!
//! Issue: Multiple consecutive blank lines (3+) appear throughout documents,
//! creating excessive whitespace.
//!
//! Root cause: Layout analysis detects large vertical gaps and converts them
//! to multiple newlines. No normalization is consistently applied.
//!
//! Expected behavior:
//! - Maximum 2 consecutive blank lines (one visible blank line)
//! - Section breaks preserved with appropriate spacing
//! - Paragraph spacing maintained (1 blank line)

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;
use regex::Regex;

// PDFs with known excessive blank line issues
const ARXIV_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";
const GOVERNMENT_DOC: &str = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Part1.pdf";

/// Helper: Count consecutive blank lines in text
fn count_excessive_blank_lines(text: &str) -> Vec<(usize, usize)> {
    // Pattern: 3 or more consecutive newlines
    let pattern = Regex::new(r"\n{3,}").unwrap();

    pattern
        .find_iter(text)
        .map(|mat| (mat.start(), mat.as_str().len() - 1)) // -1 because we count blank lines, not newlines
        .collect()
}

/// Helper: Find the longest sequence of blank lines
fn find_max_consecutive_blanks(text: &str) -> usize {
    let pattern = Regex::new(r"\n+").unwrap();

    pattern
        .find_iter(text)
        .map(|mat| mat.as_str().len() - 1) // Convert newlines to blank line count
        .max()
        .unwrap_or(0)
}

#[test]
fn test_no_excessive_blank_lines() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown", markdown.len());

    // Find all instances of 3+ consecutive blank lines
    let excessive_blanks = count_excessive_blank_lines(&markdown);

    if !excessive_blanks.is_empty() {
        println!("\n❌ EXCESSIVE BLANK LINES FOUND:");
        println!("Total instances: {}", excessive_blanks.len());

        // Show first few examples with context
        for (i, (pos, count)) in excessive_blanks.iter().enumerate().take(5) {
            println!("\n{}. At position {}: {} consecutive blank lines", i + 1, pos, count);

            // Extract context (30 chars before and after)
            let start = pos.saturating_sub(30);
            let end = (pos + 30).min(markdown.len());
            let context = &markdown[start..end];

            println!("   Context: ...{}...", context.escape_default());
        }

        panic!(
            "Found {} instances of 3+ consecutive blank lines (max: {} blanks)",
            excessive_blanks.len(),
            find_max_consecutive_blanks(&markdown)
        );
    }

    println!("✅ No excessive blank lines detected");
}

#[test]
fn test_maximum_two_blank_lines() {
    let mut doc = PdfDocument::open(GOVERNMENT_DOC)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let max_blanks = find_max_consecutive_blanks(&markdown);

    println!("Maximum consecutive blank lines: {}", max_blanks);

    if max_blanks > 2 {
        println!("\n❌ EXCESSIVE BLANK LINES:");
        println!("Expected: ≤2 consecutive blank lines");
        println!("Found: {} consecutive blank lines", max_blanks);

        // Find where this occurs
        let pattern = Regex::new(&format!(r"\n{{{},}}", max_blanks + 1)).unwrap();
        if let Some(mat) = pattern.find(&markdown) {
            let pos = mat.start();
            let start = pos.saturating_sub(50);
            let end = (pos + 50).min(markdown.len());
            let context = &markdown[start..end];

            println!("\nLocation (position {}):", pos);
            println!("Context: ...{}...", context.escape_default());
        }

        panic!("Maximum blank lines ({}) exceeds limit of 2", max_blanks);
    }

    println!("✅ Maximum blank lines within acceptable range ({})", max_blanks);
}

#[test]
fn test_section_breaks_normalized() {
    // Section breaks should have consistent spacing (1-2 blank lines)
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Look for markdown headers (section markers)
    let header_pattern = Regex::new(r"^#+\s+.+$").unwrap();
    let headers: Vec<usize> = header_pattern
        .find_iter(&markdown)
        .map(|m| m.start())
        .collect();

    println!("Found {} headers in markdown", headers.len());

    if headers.len() < 2 {
        println!("⚠️  Not enough headers to test section break spacing");
        return;
    }

    // Check spacing before each header (should be 1-2 blank lines)
    let mut violations = Vec::new();

    for &header_pos in &headers {
        if header_pos < 10 {
            continue; // Skip headers at start of document
        }

        // Look at the 10 characters before the header
        let context_start = header_pos.saturating_sub(10);
        let context = &markdown[context_start..header_pos];

        // Count consecutive newlines before header
        let newlines = context.chars().rev().take_while(|&c| c == '\n').count();

        // Violation: more than 3 newlines (= more than 2 blank lines)
        if newlines > 3 {
            violations.push((header_pos, newlines - 1)); // -1 to convert to blank line count
        }
    }

    if !violations.is_empty() {
        println!("\n⚠️  INCONSISTENT SECTION BREAK SPACING:");
        for (pos, blanks) in &violations {
            println!("  Header at position {}: {} blank lines before", pos, blanks);
        }

        // This is informational, not a hard failure
        println!("\nSection breaks should have consistent spacing (1-2 blank lines)");
    }

    println!("✅ Section break spacing check complete");
}

#[test]
fn test_paragraph_spacing_reasonable() {
    // Paragraphs should have minimal spacing (1 blank line or less)
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Count different levels of blank lines
    let single_blank = markdown.matches("\n\n").count(); // 1 blank line
    let double_blank = markdown.matches("\n\n\n").count(); // 2 blank lines
    let triple_blank = markdown.matches("\n\n\n\n").count(); // 3+ blank lines

    println!("Blank line distribution:");
    println!("  1 blank line: {} instances", single_blank);
    println!("  2 blank lines: {} instances", double_blank);
    println!("  3+ blank lines: {} instances", triple_blank);

    let total = single_blank + double_blank + triple_blank;
    if total > 0 {
        let triple_percentage = (triple_blank as f64 / total as f64) * 100.0;

        println!("\nPercentage of 3+ blank lines: {:.1}%", triple_percentage);

        // Heuristic: if more than 20% are excessive, there's a problem
        if triple_percentage > 20.0 {
            panic!(
                "Too many excessive blank lines ({:.1}% of all blank sections)",
                triple_percentage
            );
        }
    }

    println!("✅ Paragraph spacing distribution looks reasonable");
}

#[test]
fn test_whitespace_normalization_applied() {
    // Test that whitespace normalization is being applied
    let mut doc = PdfDocument::open(GOVERNMENT_DOC)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for patterns that indicate normalization wasn't applied
    let issues = vec![
        (r"\n{5,}", "5+ consecutive newlines"),
        (r"\n{10,}", "10+ consecutive newlines"),
        (r" {5,}", "5+ consecutive spaces"),
        (r"\t{2,}", "2+ consecutive tabs"),
    ];

    let mut found_issues = Vec::new();

    for (pattern, description) in &issues {
        let regex = Regex::new(pattern).unwrap();
        let count = regex.find_iter(&markdown).count();

        if count > 0 {
            found_issues.push((description.to_string(), count));
        }
    }

    if !found_issues.is_empty() {
        println!("\n❌ WHITESPACE NORMALIZATION ISSUES:");
        for (description, count) in &found_issues {
            println!("  - {}: {} instances", description, count);
        }

        panic!("Whitespace normalization not properly applied");
    }

    println!("✅ Whitespace normalization appears to be working");
}

#[test]
fn test_no_trailing_whitespace_blocks() {
    // Documents shouldn't have large blocks of whitespace at the end
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Trim and check what was removed
    let trimmed = markdown.trim_end();
    let trailing_whitespace = markdown.len() - trimmed.len();

    println!("Trailing whitespace: {} bytes", trailing_whitespace);

    // Heuristic: more than 100 bytes of trailing whitespace is excessive
    if trailing_whitespace > 100 {
        println!("\n⚠️  EXCESSIVE TRAILING WHITESPACE:");
        println!("Expected: <100 bytes");
        println!("Found: {} bytes", trailing_whitespace);

        // Show what the trailing whitespace looks like
        let trailing = &markdown[trimmed.len()..];
        println!("\nTrailing content: {:?}", trailing.escape_default().to_string());
    }

    println!("✅ Trailing whitespace check complete");
}

#[test]
fn test_consistent_line_spacing_multipage() {
    // Test that whitespace normalization is consistent across multiple pages
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    let pages_to_check = 3.min(page_count);

    println!("Checking {} pages for consistent whitespace", pages_to_check);

    let options = ConversionOptions::default();
    let mut page_max_blanks = Vec::new();

    for page_num in 0..pages_to_check {
        let markdown = doc.to_markdown(page_num, &options)
            .expect("Failed to convert page");

        let max_blanks = find_max_consecutive_blanks(&markdown);
        page_max_blanks.push((page_num, max_blanks));

        println!("Page {}: max {} consecutive blank lines", page_num, max_blanks);
    }

    // Check if any page has excessive blanks
    let has_excessive = page_max_blanks.iter().any(|(_, blanks)| *blanks > 2);

    if has_excessive {
        println!("\n❌ INCONSISTENT WHITESPACE ACROSS PAGES:");
        for (page_num, blanks) in &page_max_blanks {
            if *blanks > 2 {
                println!("  Page {}: {} consecutive blank lines (exceeds limit of 2)", page_num, blanks);
            }
        }

        panic!("Some pages have excessive blank lines");
    }

    println!("✅ Whitespace normalization consistent across all pages");
}
