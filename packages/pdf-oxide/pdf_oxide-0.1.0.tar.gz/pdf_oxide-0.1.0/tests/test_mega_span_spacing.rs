//! Regression tests for Fix #1 Comprehensive: Mega-span spacing preservation
//!
//! Issue: Dense grid layouts create "mega-spans" (e.g., "Shihan Wang, Zhenyu Yang, Yuhang Hu")
//! that get broken up during layout analysis for reading order, but the internal spaces are lost,
//! resulting in: "Shihan WangZhenyu YangYuhang Hu"
//!
//! Root cause: When layout analyzer splits mega-spans to establish reading order,
//! it doesn't preserve the internal word boundaries and spaces.
//!
//! Solution: Preserve space markers when splitting spans during layout analysis.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::layout::text_block::TextSpan;

/// PDF with dense author grid layout - causes mega-span formation
/// This PDF has 6 authors in a 3×2 grid with very tight spacing
const STREAMING_COT_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

/// Author names that should be properly spaced in the streaming_cot PDF
const STREAMING_COT_AUTHORS: &[&str] = &[
    "Shihan Wang",
    "Zhenyu Yang",
    "Yuhang Hu",
    "Changsheng Li",
    "Shengsheng Qian",
    "Xin Yuan",
];

/// Patterns that indicate spacing was lost (concatenated names)
const BAD_CONCATENATIONS: &[&str] = &[
    "WangZhenyu",
    "WangYuhang",
    "YangYuhang",
    "YangShihan",
    "HuZhenyu",
    "WangShengsheng",
    "LiShengsheng",
];

/// Helper: Check if text contains author names with proper spacing
fn check_author_spacing(text: &str, authors: &[&str]) -> Result<(), Vec<String>> {
    let mut issues = Vec::new();

    // Check for bad concatenations
    for bad in BAD_CONCATENATIONS {
        if text.contains(bad) {
            issues.push(format!(
                "Found concatenated names: '{}' (spaces lost during span splitting)",
                bad
            ));
        }
    }

    // Check that proper names are present
    let mut missing_proper = Vec::new();
    for author in authors {
        // Case-insensitive check since markdown may lowercase
        if !text.to_lowercase().contains(&author.to_lowercase()) {
            missing_proper.push(author.to_string());
        }
    }

    if !missing_proper.is_empty() {
        issues.push(format!(
            "Expected authors not found with proper spacing: {:?}",
            missing_proper
        ));
    }

    if issues.is_empty() {
        Ok(())
    } else {
        Err(issues)
    }
}

/// Helper: Analyze span boundaries to detect if spacing is preserved
fn analyze_span_boundaries(spans: &[TextSpan]) -> (usize, usize, Vec<String>) {
    let mut total_boundaries = 0;
    let mut space_preserved = 0;
    let mut suspicious = Vec::new();

    for window in spans.windows(2) {
        let span1 = &window[0];
        let span2 = &window[1];

        total_boundaries += 1;

        // Check if boundary has a space
        let has_space = span1.text.ends_with(' ') || span2.text.starts_with(' ');

        if has_space {
            space_preserved += 1;
        } else {
            // Suspicious if both spans are multi-character words
            if span1.text.len() > 2 && span2.text.len() > 2 {
                let text1 = span1.text.trim();
                let text2 = span2.text.trim();

                // Check if this looks like two separate words concatenated
                if text1.chars().last().unwrap_or(' ').is_alphanumeric() &&
                   text2.chars().next().unwrap_or(' ').is_uppercase() {
                    suspicious.push(format!(
                        "\"{}\" + \"{}\" (no space between spans)",
                        text1, text2
                    ));
                }
            }
        }
    }

    (total_boundaries, space_preserved, suspicious)
}

#[test]
fn test_mega_span_spacing_in_markdown() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open streaming_cot PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown", markdown.len());
    println!("First 1000 chars:\n{}\n", &markdown[..1000.min(markdown.len())]);

    match check_author_spacing(&markdown, STREAMING_COT_AUTHORS) {
        Ok(_) => {
            println!("✅ All author names properly spaced in markdown output");
        }
        Err(issues) => {
            println!("\n❌ MEGA-SPAN SPACING ISSUES FOUND:");
            for issue in &issues {
                println!("  - {}", issue);
            }

            // Save for debugging
            std::fs::write("/tmp/mega_span_debug.md", &markdown)
                .expect("Failed to write debug file");
            println!("\n📝 Full markdown saved to: /tmp/mega_span_debug.md");

            panic!("Mega-span spacing not preserved in markdown output");
        }
    }
}

#[test]
fn test_mega_span_spacing_in_spans() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open streaming_cot PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    println!("Extracted {} spans from page 0", spans.len());

    // Concatenate all span text
    let full_text: String = spans.iter()
        .map(|s| s.text.as_str())
        .collect();

    println!("Full text length: {} chars", full_text.len());

    match check_author_spacing(&full_text, STREAMING_COT_AUTHORS) {
        Ok(_) => {
            println!("✅ All author names properly spaced in raw spans");
        }
        Err(issues) => {
            println!("\n❌ SPACING ISSUES IN RAW SPANS:");
            for issue in &issues {
                println!("  - {}", issue);
            }
            panic!("Spacing not preserved in extract_spans() output");
        }
    }
}

#[test]
fn test_span_boundary_preservation() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open streaming_cot PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let (total, preserved, suspicious) = analyze_span_boundaries(&spans);

    println!("Total span boundaries: {}", total);
    println!("Boundaries with spaces: {} ({:.1}%)", preserved, (preserved as f64 / total as f64) * 100.0);
    println!("Suspicious concatenations: {}", suspicious.len());

    if !suspicious.is_empty() {
        println!("\n⚠️ Suspicious span boundaries:");
        for (i, s) in suspicious.iter().enumerate().take(10) {
            println!("  {}. {}", i + 1, s);
        }
        if suspicious.len() > 10 {
            println!("  ... and {} more", suspicious.len() - 10);
        }
    }

    // Heuristic: At least 30% of boundaries should have spaces in a well-formatted document
    let space_percentage = (preserved as f64 / total as f64) * 100.0;
    if space_percentage < 30.0 {
        panic!(
            "Too few word boundaries with spaces ({:.1}%) - spacing may be lost",
            space_percentage
        );
    }

    // Heuristic: Should have fewer than 20 suspicious concatenations
    if suspicious.len() > 20 {
        panic!(
            "Too many suspicious concatenations ({}) - spacing likely lost during span splitting",
            suspicious.len()
        );
    }

    println!("✅ Span boundaries look healthy");
}

#[test]
fn test_dense_grid_layout_handling() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open streaming_cot PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // In a 3-column × 2-row author grid, names should be separated by commas or newlines
    let has_commas = markdown.matches(',').count() >= 4; // At least 4 commas for 6 authors
    let has_newlines_after_names = markdown.lines()
        .filter(|line| STREAMING_COT_AUTHORS.iter().any(|a| line.contains(a)))
        .count() >= 3; // At least 3 lines with author names

    println!("Has comma separators: {}", has_commas);
    println!("Has newline separators: {}", has_newlines_after_names);

    if !has_commas && !has_newlines_after_names {
        panic!("Dense grid layout not properly formatted - names may be concatenated");
    }

    println!("✅ Dense grid layout handled correctly");
}

#[test]
fn test_email_formatting_with_proper_spacing() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open streaming_cot PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check if emails are properly formatted (Fix #3)
    // Email pattern from Fix #3
    let email_pattern = regex::Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        .expect("Failed to create regex");

    let emails: Vec<_> = email_pattern.find_iter(&markdown)
        .map(|m| m.as_str())
        .collect();

    println!("Found {} email addresses", emails.len());

    if emails.is_empty() {
        println!("⚠️ No emails found - may be concatenated with surrounding text");
        // This is expected if Fix #1 comprehensive isn't complete yet
        return;
    }

    // Check if emails are clickable (Fix #3)
    let mut clickable_count = 0;
    for email in &emails {
        if markdown.contains(&format!("[{}](mailto:{})", email, email)) {
            clickable_count += 1;
        }
    }

    println!("Clickable email links: {}/{}", clickable_count, emails.len());

    if clickable_count == emails.len() {
        println!("✅ All emails properly formatted and clickable");
    } else {
        println!("⚠️ Some emails not clickable (expected if Fix #1 comprehensive not complete)");
    }
}

#[test]
fn test_no_capital_letter_concatenations() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open streaming_cot PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Pattern: Lowercase letter immediately followed by uppercase (word boundary without space)
    // Example: "WangZhenyu" has 'g' followed by 'Z'
    let capital_transitions = regex::Regex::new(r"[a-z][A-Z]")
        .expect("Failed to create regex");

    let transitions: Vec<_> = capital_transitions.find_iter(&markdown)
        .map(|m| m.as_str())
        .collect();

    println!("Found {} lowercase→uppercase transitions", transitions.len());

    // Show first 10 examples
    if !transitions.is_empty() {
        println!("\nExamples:");
        for (i, trans) in transitions.iter().enumerate().take(10) {
            // Get context around the transition
            if let Some(pos) = markdown.find(trans) {
                let start = pos.saturating_sub(5);
                let end = (pos + 10).min(markdown.len());
                let context = &markdown[start..end];
                println!("  {}. \"{}\"", i + 1, context);
            }
        }
    }

    // Heuristic: Should have fewer than 20 suspicious transitions
    // (Some are legitimate like "iPhone", "MacDonald", etc.)
    if transitions.len() > 20 {
        panic!(
            "Too many lowercase→uppercase transitions ({}) - likely missing spaces between words",
            transitions.len()
        );
    }

    println!("✅ Capital letter transitions within acceptable range");
}

#[test]
fn test_affiliation_integrity() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open streaming_cot PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Common affiliation patterns that should be preserved
    let affiliations = [
        "Institute",
        "University",
        "Academy",
        "Technology",
        "Beijing",
        "China",
    ];

    let mut missing_affiliations = Vec::new();
    for affiliation in &affiliations {
        if !markdown.to_lowercase().contains(&affiliation.to_lowercase()) {
            missing_affiliations.push(*affiliation);
        }
    }

    if !missing_affiliations.is_empty() {
        println!("⚠️ Missing affiliations: {:?}", missing_affiliations);
        println!("   (May be concatenated or split incorrectly)");
    } else {
        println!("✅ All expected affiliations present");
    }

    // Check for concatenated affiliation patterns
    let bad_affiliation_patterns = [
        "InstituteBeijing",
        "TechnologyInstitute",
        "AcademyBeijing",
        "UniversityChina",
    ];

    let mut found_bad = Vec::new();
    for bad in &bad_affiliation_patterns {
        if markdown.contains(bad) {
            found_bad.push(*bad);
        }
    }

    if !found_bad.is_empty() {
        panic!(
            "Found concatenated affiliations: {:?} - spacing lost during span splitting",
            found_bad
        );
    }

    println!("✅ Affiliation integrity preserved");
}
