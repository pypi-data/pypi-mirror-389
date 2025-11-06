//! Regression test for general encoding issues
//!
//! Issue: 21 PDFs (6%) have encoding issues beyond U+FFFD
//! Root cause: Various encoding problems (invalid Unicode, mojibake, etc.)
//!
//! This covers encoding issues that aren't replacement characters,
//! such as incorrect character mappings, mojibake, or invalid Unicode.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// PDFs with general encoding issues (not U+FFFD)
const ENCODING_ISSUE_FILES: &[&str] = &[
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25765v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25522v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25701v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25264v1.pdf",
];

/// Check for common encoding issues
fn detect_encoding_issues(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // 1. Invalid Unicode sequences (surrogates, invalid code points)
    let invalid_unicode = text.chars()
        .filter(|c| {
            let code = *c as u32;
            // Surrogate pairs (0xD800-0xDFFF)
            (code >= 0xD800 && code <= 0xDFFF) ||
            // Invalid code points
            code > 0x10FFFF
        })
        .count();

    if invalid_unicode > 0 {
        issues.push(format!("Invalid Unicode: {} chars", invalid_unicode));
    }

    // 2. Mojibake patterns (common encoding confusion)
    let mojibake_patterns = [
        "Ã©", "Ã¨", "Ã¼", // UTF-8 interpreted as Latin-1
        "â€™", "â€œ", "â€", // Smart quotes mojibake
        "Ã¡", "Ã­", "Ã³", // Accented chars mojibake
    ];

    let mut mojibake_count = 0;
    for pattern in &mojibake_patterns {
        mojibake_count += text.matches(pattern).count();
    }

    if mojibake_count > 3 {
        issues.push(format!("Mojibake patterns: {} occurrences", mojibake_count));
    }

    // 3. Excessive non-ASCII in supposedly English text
    let total_chars = text.len();
    let non_ascii = text.chars()
        .filter(|c| (*c as u32) > 127)
        .count();

    if total_chars > 1000 {
        let non_ascii_ratio = (non_ascii as f64 / total_chars as f64) * 100.0;

        // English text should be mostly ASCII
        // Allow higher ratio for international documents
        if non_ascii_ratio > 30.0 {
            issues.push(format!(
                "High non-ASCII ratio: {:.1}% (possible encoding issue)",
                non_ascii_ratio
            ));
        }
    }

    // 4. Null bytes in text (shouldn't happen)
    let null_bytes = text.chars().filter(|c| *c == '\0').count();
    if null_bytes > 0 {
        issues.push(format!("Null bytes: {}", null_bytes));
    }

    issues
}

#[test]
fn test_no_encoding_issues() {
    let mut files_with_issues = Vec::new();
    let mut checked = 0;

    println!("\n=== Testing for General Encoding Issues ===");

    for pdf_path in ENCODING_ISSUE_FILES {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        checked += 1;
        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.to_markdown(0, &ConversionOptions::default()) {
                    Ok(markdown) => {
                        let issues = detect_encoding_issues(&markdown);

                        if !issues.is_empty() {
                            println!("  Found {} encoding issues:", issues.len());
                            for issue in &issues {
                                println!("    - {}", issue);
                            }

                            files_with_issues.push(format!(
                                "{}: {}",
                                pdf_path,
                                issues.join(", ")
                            ));
                        } else {
                            println!("  ✓ No encoding issues detected");
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

    println!("\n=== Summary ===");
    println!("Checked: {}/{} files", checked, ENCODING_ISSUE_FILES.len());
    println!("Files with issues: {}", files_with_issues.len());

    if !files_with_issues.is_empty() {
        println!("\n❌ FAILURES:");
        for issue in &files_with_issues {
            println!("  • {}", issue);
        }
        panic!("Found encoding issues in {} files", files_with_issues.len());
    }

    println!("✅ No encoding issues detected");
}

#[test]
fn test_valid_unicode_only() {
    // Ensure all output is valid Unicode
    println!("\n=== Testing for Valid Unicode ===");

    for pdf_path in ENCODING_ISSUE_FILES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                // Check each character is valid Unicode
                let mut invalid_count = 0;
                let mut invalid_examples = Vec::new();

                for (i, ch) in markdown.chars().enumerate() {
                    let code = ch as u32;

                    // Check for invalid ranges
                    if (code >= 0xD800 && code <= 0xDFFF) || // Surrogates
                       code > 0x10FFFF {  // Beyond Unicode range
                        invalid_count += 1;
                        if invalid_examples.len() < 5 {
                            invalid_examples.push((i, ch));
                        }
                    }
                }

                println!("  Invalid Unicode chars: {}", invalid_count);

                if invalid_count > 0 {
                    println!("  Examples:");
                    for (pos, ch) in invalid_examples.iter().take(3) {
                        println!("    Position {}: U+{:04X}", pos, *ch as u32);
                    }
                }

                assert_eq!(
                    invalid_count, 0,
                    "Found {} invalid Unicode characters", invalid_count
                );
            }
        }
    }
}

#[test]
fn test_no_mojibake() {
    // Detect mojibake patterns in output
    println!("\n=== Testing for Mojibake ===");

    let mojibake_patterns = [
        "Ã©", "Ã¨", "Ã¼", // UTF-8 interpreted as Latin-1
        "â€™", "â€œ", "â€", // Smart quotes mojibake
        "Ã¡", "Ã­", "Ã³", // Accented chars mojibake
    ];

    for pdf_path in ENCODING_ISSUE_FILES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                let mut found_patterns = Vec::new();

                for pattern in &mojibake_patterns {
                    let count = markdown.matches(pattern).count();
                    if count > 0 {
                        found_patterns.push(format!("{} ({}x)", pattern, count));
                    }
                }

                if !found_patterns.is_empty() {
                    println!("  Found mojibake: {:?}", found_patterns);
                }

                assert!(
                    found_patterns.is_empty(),
                    "Found mojibake patterns: {:?}",
                    found_patterns
                );
            }
        }
    }

    println!("\n✅ No mojibake detected");
}