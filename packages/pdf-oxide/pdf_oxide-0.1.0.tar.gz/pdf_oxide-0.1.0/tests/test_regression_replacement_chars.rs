//! Regression test for remaining replacement character (U+FFFD) issues
//!
//! Issue: 42 PDFs (12%) still contain U+FFFD despite Font dereferencing fix
//! Root cause: Multiple encoding issues beyond Font dictionary
//!
//! Progress: Reduced from 57 to 42 files (26% improvement!)
//! Remaining cases likely have different root causes.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// PDFs with remaining U+FFFD issues after initial fix
const REPLACEMENT_CHAR_FILES: &[&str] = &[
    "../pdf_oxide_tests/pdfs/diverse/YBTLDNWUYL3SLS4NVMFEB3OFUWOZBLA7.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25758v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25732v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25726v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25694v1.pdf",
];

#[test]
fn test_no_replacement_characters() {
    let mut files_with_issues = Vec::new();
    let mut checked = 0;

    println!("\n=== Testing for U+FFFD Replacement Characters ===");

    for pdf_path in REPLACEMENT_CHAR_FILES {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        checked += 1;
        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                let page_count = doc.page_count().unwrap_or(1);
                let pages_to_check = 3.min(page_count);

                let mut total_replacement_chars = 0;
                let mut examples = Vec::new();

                for page_num in 0..pages_to_check {
                    if let Ok(markdown) = doc.to_markdown(page_num, &ConversionOptions::default()) {
                        let count = markdown.matches('\u{FFFD}').count();
                        total_replacement_chars += count;

                        if count > 0 && examples.len() < 3 {
                            // Get example lines
                            for line in markdown.lines().take(100) {
                                if line.contains('\u{FFFD}') {
                                    examples.push(line.to_string());
                                    if examples.len() >= 3 {
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }

                println!("  Total U+FFFD: {} across {} pages",
                    total_replacement_chars, pages_to_check);

                if total_replacement_chars > 0 {
                    println!("  Examples:");
                    for ex in &examples {
                        println!("    {}", ex);
                    }

                    files_with_issues.push(format!(
                        "{}: {} replacement characters",
                        pdf_path, total_replacement_chars
                    ));
                }
            }
            Err(e) => {
                println!("  ❌ Failed to open: {}", e);
            }
        }
    }

    println!("\n=== Summary ===");
    println!("Checked: {}/{} files", checked, REPLACEMENT_CHAR_FILES.len());
    println!("Files with U+FFFD: {}", files_with_issues.len());

    if !files_with_issues.is_empty() {
        println!("\n❌ FAILURES:");
        for issue in &files_with_issues {
            println!("  • {}", issue);
        }
        panic!("Found U+FFFD in {} files", files_with_issues.len());
    }

    println!("✅ No replacement characters detected");
}

#[test]
fn test_replacement_chars_span_level() {
    // Test at span level to see if issue is in extraction or conversion
    println!("\n=== Testing Spans for U+FFFD ===");

    for pdf_path in REPLACEMENT_CHAR_FILES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\nChecking spans: {}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(spans) = doc.extract_spans(0) {
                let fffd_spans: Vec<_> = spans.iter()
                    .enumerate()
                    .filter(|(_, s)| s.text.contains('\u{FFFD}'))
                    .take(5)
                    .collect();

                println!("  Spans with U+FFFD: {}/{}", fffd_spans.len(), spans.len());

                for (i, span) in &fffd_spans {
                    println!("  Span {}: font={}, text={:?}",
                        i, span.font_name, span.text);
                }

                assert_eq!(
                    fffd_spans.len(), 0,
                    "Found U+FFFD in {} spans", fffd_spans.len()
                );
            }
        }
    }
}

#[test]
fn test_specific_problematic_chars() {
    // Test specific character codes known to cause issues
    println!("\n=== Testing Specific Problematic Character Mappings ===");

    for pdf_path in REPLACEMENT_CHAR_FILES.iter().take(1) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(spans) = doc.extract_spans(0) {
                println!("\n{}: {} spans", pdf_path, spans.len());

                // Look for spans with problematic patterns
                for (i, span) in spans.iter().enumerate().take(100) {
                    if span.text.contains('\u{FFFD}') {
                        println!("  Span {}: font={}, len={}, text={:?}",
                            i, span.font_name, span.text.len(),
                            &span.text.chars().take(20).collect::<String>());

                        // Show surrounding spans for context
                        if i > 0 {
                            println!("    Before: {:?}", spans[i-1].text);
                        }
                        if i + 1 < spans.len() {
                            println!("    After: {:?}", spans[i+1].text);
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn test_font_encoding_used() {
    // Diagnose which fonts/encodings are being used in problematic PDFs
    println!("\n=== Analyzing Font Encodings ===");

    for pdf_path in REPLACEMENT_CHAR_FILES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(spans) = doc.extract_spans(0) {
                // Collect unique fonts
                let mut fonts: std::collections::HashSet<String> = std::collections::HashSet::new();
                let mut fffd_fonts: std::collections::HashSet<String> = std::collections::HashSet::new();

                for span in &spans {
                    fonts.insert(span.font_name.clone());
                    if span.text.contains('\u{FFFD}') {
                        fffd_fonts.insert(span.font_name.clone());
                    }
                }

                println!("  Total fonts: {}", fonts.len());
                println!("  Fonts with U+FFFD: {}", fffd_fonts.len());

                if !fffd_fonts.is_empty() {
                    println!("  Problematic fonts:");
                    for font in &fffd_fonts {
                        println!("    - {}", font);
                    }
                }
            }
        }
    }
}
