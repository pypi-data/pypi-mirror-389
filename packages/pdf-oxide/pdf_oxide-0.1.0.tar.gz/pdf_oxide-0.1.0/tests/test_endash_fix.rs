//! Tests for En-Dash Replacement Character Fix
//!
//! This test suite verifies the fix for the issue where ToUnicode CMaps
//! incorrectly map en-dash character codes to U+FFFD (replacement character).
//!
//! Root cause: Government PDF authoring tools write U+FFFD in ToUnicode CMaps
//! when they can't determine the correct Unicode value for en-dash.
//!
//! Fix: Skip U+FFFD mappings in ToUnicode CMaps and fall back to predefined
//! encodings (MacRomanEncoding 0xD0 or WinAnsiEncoding 0x96 → U+2013).
//!
//! See ENDASH_ISSUE_ROOT_CAUSE.md for full analysis.

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;

// Test PDFs with known en-dash issues
const CFR_TITLE33: &str = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Vol1_Navigation_and_Navigable_Waters.pdf";
const CFR_TITLE45: &str = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title45_Public_Welfare.pdf";

/// Test that Page 0 of CFR Title 33 has no replacement characters
#[test]
fn test_cfr_title33_page0_no_replacement_chars() {
    let mut doc = PdfDocument::open(CFR_TITLE33).expect("Failed to open CFR Title 33");

    let markdown = doc
        .to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert page 0");

    let replacement_count = markdown.chars().filter(|&c| c == '\u{FFFD}').count();

    if replacement_count > 0 {
        println!("⚠️  Found {} replacement characters on page 0", replacement_count);
        let lines_with_repl: Vec<&str> = markdown
            .lines()
            .filter(|line| line.contains('\u{FFFD}'))
            .take(5)
            .collect();
        println!("   First few lines with replacement chars:");
        for line in &lines_with_repl {
            println!("   {}", line);
        }
    }

    assert_eq!(
        replacement_count, 0,
        "Page 0 should have no replacement characters after en-dash fix"
    );
}

/// Test that Page 1 of CFR Title 33 correctly extracts en-dash
#[test]
fn test_cfr_title33_page1_endash_correct() {
    let mut doc = PdfDocument::open(CFR_TITLE33).expect("Failed to open CFR Title 33");

    let markdown = doc
        .to_markdown(1, &ConversionOptions::default())
        .expect("Failed to convert page 1");

    // Check for replacement characters
    let replacement_count = markdown.chars().filter(|&c| c == '\u{FFFD}').count();

    if replacement_count > 0 {
        println!("⚠️  Found {} replacement characters on page 1", replacement_count);
        let lines_with_repl: Vec<&str> = markdown
            .lines()
            .filter(|line| line.contains('\u{FFFD}'))
            .take(5)
            .collect();
        println!("   Lines with replacement chars:");
        for line in &lines_with_repl {
            println!("   {}", line);
        }
    }

    assert_eq!(
        replacement_count, 0,
        "Page 1 should have no replacement characters after en-dash fix"
    );

    // Verify en-dash is actually present
    // Expected pattern: "Use of the 0–16" (with en-dash U+2013)
    let has_endash_isbn = markdown.contains("0–16") || markdown.contains("0\u{2013}16");
    let has_endash_zipcode = markdown.contains("20402–0001") || markdown.contains("20402\u{2013}0001");

    if !has_endash_isbn && !has_endash_zipcode {
        println!("⚠️  Expected en-dash patterns not found");
        println!("   Looking for: '0–16' or '20402–0001'");

        // Show lines with "0" and "16" to see what we got
        let lines_with_numbers: Vec<&str> = markdown
            .lines()
            .filter(|line| line.contains("0") && line.contains("16"))
            .take(3)
            .collect();

        if !lines_with_numbers.is_empty() {
            println!("   Lines with '0' and '16':");
            for line in &lines_with_numbers {
                println!("   {}", line);
            }
        }
    }

    assert!(
        has_endash_isbn || has_endash_zipcode,
        "Page 1 should contain en-dash in ISBN prefix (0–16) or zip code (20402–0001)"
    );
}

/// Test multiple pages of CFR Title 33 for en-dash issues
#[test]
fn test_cfr_title33_multipage_no_replacement_chars() {
    let mut doc = PdfDocument::open(CFR_TITLE33).expect("Failed to open CFR Title 33");

    let page_count = doc.page_count().expect("Failed to get page count");
    let pages_to_check = 10.min(page_count);
    let mut total_replacements = 0;
    let mut pages_with_issues = Vec::new();

    println!("Checking first {} pages of CFR Title 33...", pages_to_check);

    for page_num in 0..pages_to_check {
        let markdown = doc
            .to_markdown(page_num, &ConversionOptions::default())
            .expect(&format!("Failed to convert page {}", page_num));

        let replacement_count = markdown.chars().filter(|&c| c == '\u{FFFD}').count();

        if replacement_count > 0 {
            println!("   Page {}: {} replacement characters", page_num, replacement_count);
            total_replacements += replacement_count;
            pages_with_issues.push(page_num);

            // Show first example
            if let Some(line) = markdown.lines().find(|l| l.contains('\u{FFFD}')) {
                println!("     Example: {}", line);
            }
        }
    }

    println!(
        "\n✓ Checked {} pages: {} total replacement characters across {} pages",
        pages_to_check,
        total_replacements,
        pages_with_issues.len()
    );

    if !pages_with_issues.is_empty() {
        println!("   Pages with issues: {:?}", pages_with_issues);
    }

    assert_eq!(
        total_replacements, 0,
        "No pages should have replacement characters after en-dash fix (found {} across pages {:?})",
        total_replacements, pages_with_issues
    );
}

/// Test CFR Title 45 (another CFR document with same issue)
#[test]
fn test_cfr_title45_no_replacement_chars() {
    let mut doc = PdfDocument::open(CFR_TITLE45).expect("Failed to open CFR Title 45");

    // Check first 5 pages
    let page_count = doc.page_count().expect("Failed to get page count");
    let pages_to_check = 5.min(page_count);
    let mut total_replacements = 0;

    for page_num in 0..pages_to_check {
        let markdown = doc
            .to_markdown(page_num, &ConversionOptions::default())
            .expect(&format!("Failed to convert page {}", page_num));

        let replacement_count = markdown.chars().filter(|&c| c == '\u{FFFD}').count();
        total_replacements += replacement_count;
    }

    assert_eq!(
        total_replacements, 0,
        "CFR Title 45 should have no replacement characters after en-dash fix (found {} in first {} pages)",
        total_replacements, pages_to_check
    );
}

/// Test that en-dash appears correctly in CFR documents
#[test]
fn test_cfr_endash_patterns() {
    let mut doc = PdfDocument::open(CFR_TITLE33).expect("Failed to open CFR Title 33");

    // Check pages 1-4 (where we know en-dash appears)
    let mut found_endash_patterns = Vec::new();

    // Look for common en-dash patterns in CFR documents
    let patterns = vec![
        ("ISBN prefix", "0–16"),
        ("ZIP code", "20402–0001"),
        ("Chapter marker", "I–Coast"),
        ("Section number", "01–1"),
        ("Public Law", "96–511"),
        ("Phone number", "202–741–6000"),
    ];

    for page_num in 1..5 {
        let markdown = doc
            .to_markdown(page_num, &ConversionOptions::default())
            .expect(&format!("Failed to convert page {}", page_num));

        for (pattern_name, pattern) in &patterns {
            if markdown.contains(pattern) {
                found_endash_patterns.push((page_num, *pattern_name));
                println!("   Page {}: Found {} pattern: {}", page_num, pattern_name, pattern);
            }
        }
    }

    assert!(
        !found_endash_patterns.is_empty(),
        "Should find at least one en-dash pattern in CFR document pages 1-4"
    );

    println!(
        "\n✓ Found {} en-dash patterns in CFR Title 33",
        found_endash_patterns.len()
    );
}

/// Test that span extraction has no replacement characters
#[test]
fn test_cfr_spans_no_replacement_chars() {
    let mut doc = PdfDocument::open(CFR_TITLE33).expect("Failed to open CFR Title 33");

    // Check spans on page 1 (where we know en-dash appears)
    let spans = doc.extract_spans(1).expect("Failed to extract spans");

    let mut spans_with_repl = Vec::new();

    for (i, span) in spans.iter().enumerate() {
        if span.text.contains('\u{FFFD}') {
            spans_with_repl.push((i, span.text.clone()));
        }
    }

    if !spans_with_repl.is_empty() {
        println!("⚠️  Found {} spans with replacement characters:", spans_with_repl.len());
        for (i, text) in &spans_with_repl {
            println!("   Span {}: {:?}", i, text);
        }
    }

    assert!(
        spans_with_repl.is_empty(),
        "Span extraction should have no replacement characters (found in {} spans)",
        spans_with_repl.len()
    );
}

/// Test MacRomanEncoding en-dash support
#[test]
fn test_macroman_endash_encoding() {
    use pdf_oxide::fonts::{Encoding, FontInfo};
    use std::collections::HashMap;

    // Create a font with MacRomanEncoding but with buggy ToUnicode CMap
    let mut buggy_cmap = HashMap::new();
    buggy_cmap.insert(0xD0, "\u{FFFD}".to_string()); // Buggy mapping: 0xD0 → U+FFFD

    let font = FontInfo {
        base_font: "TestFont".to_string(),
        subtype: "Type1".to_string(),
        encoding: Encoding::Standard("MacRomanEncoding".to_string()),
        to_unicode: Some(buggy_cmap), // Has buggy ToUnicode CMap
        font_weight: None,
        flags: None,
        stem_v: None,
        embedded_font_data: None,
        widths: None,
        first_char: None,
        last_char: None,
        default_width: 1000.0,
    };

    // Test that we skip U+FFFD mapping and fall back to MacRomanEncoding
    let result = font.char_to_unicode(0xD0);

    assert_eq!(
        result,
        Some("–".to_string()),
        "MacRomanEncoding 0xD0 should map to en-dash U+2013, not U+FFFD"
    );
}

/// Test WinAnsiEncoding en-dash support
#[test]
fn test_winansi_endash_encoding() {
    use pdf_oxide::fonts::{Encoding, FontInfo};
    use std::collections::HashMap;

    // Create a font with WinAnsiEncoding but with buggy ToUnicode CMap
    let mut buggy_cmap = HashMap::new();
    buggy_cmap.insert(0x96, "\u{FFFD}".to_string()); // Buggy mapping: 0x96 → U+FFFD

    let font = FontInfo {
        base_font: "TestFont".to_string(),
        subtype: "Type1".to_string(),
        encoding: Encoding::Standard("WinAnsiEncoding".to_string()),
        to_unicode: Some(buggy_cmap), // Has buggy ToUnicode CMap
        font_weight: None,
        flags: None,
        stem_v: None,
        embedded_font_data: None,
        widths: None,
        first_char: None,
        last_char: None,
        default_width: 1000.0,
    };

    // Test that we skip U+FFFD mapping and fall back to WinAnsiEncoding
    let result = font.char_to_unicode(0x96);

    assert_eq!(
        result,
        Some("–".to_string()),
        "WinAnsiEncoding 0x96 should map to en-dash U+2013, not U+FFFD"
    );
}

/// Test that valid ToUnicode mappings are still used
#[test]
fn test_valid_tounicode_still_works() {
    use pdf_oxide::fonts::{Encoding, FontInfo};
    use std::collections::HashMap;

    // Create a font with good ToUnicode CMap
    let mut good_cmap = HashMap::new();
    good_cmap.insert(0x41, "X".to_string()); // Custom mapping: 0x41 → 'X'
    good_cmap.insert(0xD0, "–".to_string()); // Correct mapping: 0xD0 → en-dash

    let font = FontInfo {
        base_font: "TestFont".to_string(),
        subtype: "Type1".to_string(),
        encoding: Encoding::Standard("MacRomanEncoding".to_string()),
        to_unicode: Some(good_cmap),
        font_weight: None,
        flags: None,
        stem_v: None,
        embedded_font_data: None,
        widths: None,
        first_char: None,
        last_char: None,
        default_width: 1000.0,
    };

    // Valid mappings should still be used
    assert_eq!(font.char_to_unicode(0x41), Some("X".to_string()));
    assert_eq!(font.char_to_unicode(0xD0), Some("–".to_string()));
}
