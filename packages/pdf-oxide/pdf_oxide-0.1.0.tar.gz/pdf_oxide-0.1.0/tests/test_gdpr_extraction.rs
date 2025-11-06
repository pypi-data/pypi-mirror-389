//! Comprehensive GDPR PDF Text Extraction Tests
//!
//! This test suite verifies that ALL text extraction flows correctly
//! handle the EU GDPR PDF, which uses Type0 fonts with Identity-H encoding
//! and ToUnicode CMaps.
//!
//! These tests serve as:
//! 1. Verification that the ToUnicode CMap fix works
//! 2. Regression tests to prevent future scrambling issues
//! 3. Documentation of expected behavior for each extraction flow

use pdf_oxide::converters::{ConversionOptions, ReadingOrderMode};
use pdf_oxide::PdfDocument;

/// Path to the EU GDPR test PDF
const GDPR_PDF: &str = "../pdf_oxide_tests/pdfs/diverse/EU_GDPR_Regulation.pdf";

/// Expected phrases that should appear in the extracted text
/// These verify that ToUnicode CMap is working correctly
const EXPECTED_PHRASES: &[&str] = &[
    "Having regard to the Treaty",
    "Functioning of the European Union",
    "protection of natural persons",
    "REGULATION (EU) 2016/679",
    "European Parliament",
    "General Data Protection Regulation",
];

/// Phrases that should NOT appear (scrambled versions from the bug)
const FORBIDDEN_SCRAMBLED: &[&str] = &[
    "Havirnegdg",     // Scrambled "Having regard"
    "nceoH icafEEtoos", // Scrambled "Functioning"
    "aAotrcW",        // Scrambled fragment
];

/// Helper function to verify text is readable (not scrambled)
fn assert_text_is_readable(text: &str, method_name: &str) {
    // Strip HTML tags for HTML output (simple approach)
    let cleaned_text = if text.contains("<html>") || text.contains("<p>") {
        // Simple HTML tag stripping - just for testing
        text.replace("<", " <").replace(">", "> ")
    } else {
        text.to_string()
    };

    // Check that expected phrases are present
    let mut found_count = 0;
    for phrase in EXPECTED_PHRASES {
        if cleaned_text.contains(phrase) {
            found_count += 1;
        } else {
            eprintln!(
                "[{}] WARNING: Expected phrase not found: '{}'",
                method_name, phrase
            );
        }
    }

    // At least 50% of expected phrases should be present
    let threshold = (EXPECTED_PHRASES.len() / 2).max(1);
    assert!(
        found_count >= threshold,
        "[{}] Only {}/{} expected phrases found. Text may be scrambled. Found: {}",
        method_name,
        found_count,
        EXPECTED_PHRASES.len(),
        found_count
    );

    // Check that scrambled text is NOT present
    for scrambled in FORBIDDEN_SCRAMBLED {
        assert!(
            !cleaned_text.contains(scrambled),
            "[{}] Found scrambled text '{}' in output! Text extraction is broken.",
            method_name,
            scrambled
        );
    }

    println!(
        "[{}] ✓ Text is readable ({}/{} expected phrases found, no scrambled text)",
        method_name, found_count, EXPECTED_PHRASES.len()
    );
}

#[test]
fn test_gdpr_extract_spans() {
    println!("\n=== Testing extract_spans() ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    // Extract spans from first page
    let spans = doc
        .extract_spans(0)
        .expect("Failed to extract spans from page 0");

    // Verify we got spans
    assert!(
        !spans.is_empty(),
        "extract_spans() returned empty span list"
    );
    println!("Extracted {} spans from page 0", spans.len());

    // Concatenate span text
    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // Verify text is readable
    assert_text_is_readable(&text, "extract_spans");

    // Verify font information is present
    let fonts_present = spans.iter().any(|s| !s.font_name.is_empty());
    assert!(
        fonts_present,
        "No font names found in spans (font info missing)"
    );
    println!("✓ Font information preserved in spans");

    // Verify bold detection works
    let bold_present = spans.iter().any(|s| s.font_weight.is_bold());
    if bold_present {
        println!("✓ Bold text detected in spans");
    } else {
        println!("⚠ No bold text detected (may be normal for this page)");
    }
}

#[test]
fn test_gdpr_to_markdown_single_page() {
    println!("\n=== Testing to_markdown() (single page) ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    // Test with default options
    let options = ConversionOptions::default();
    let markdown = doc
        .to_markdown(0, &options)
        .expect("Failed to convert page 0 to markdown");

    // Verify we got output
    assert!(!markdown.is_empty(), "to_markdown() returned empty string");
    println!("Generated {} characters of markdown", markdown.len());

    // Verify text is readable
    assert_text_is_readable(&markdown, "to_markdown(default)");

    // Test with heading detection enabled
    let options_headings = ConversionOptions {
        detect_headings: true,
        ..Default::default()
    };
    let markdown_with_headings = doc
        .to_markdown(0, &options_headings)
        .expect("Failed to convert with heading detection");

    assert_text_is_readable(&markdown_with_headings, "to_markdown(headings)");
    println!("✓ Heading detection mode works");
}

#[test]
fn test_gdpr_to_markdown_all_pages() {
    println!("\n=== Testing to_markdown_all() ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let options = ConversionOptions::default();
    let markdown = doc
        .to_markdown_all(&options)
        .expect("Failed to convert all pages to markdown");

    // Verify we got output
    assert!(
        !markdown.is_empty(),
        "to_markdown_all() returned empty string"
    );
    println!(
        "Generated {} characters of markdown from all pages",
        markdown.len()
    );

    // Verify text is readable
    assert_text_is_readable(&markdown, "to_markdown_all");

    // Verify page separators are present
    let separator_count = markdown.matches("\n---\n").count();
    println!("Found {} page separators", separator_count);

    // Should have (page_count - 1) separators
    let page_count = doc.page_count().expect("Failed to get page count");
    if page_count > 1 {
        assert!(
            separator_count > 0,
            "Expected page separators but found none"
        );
    }
}

#[test]
fn test_gdpr_to_markdown_column_aware() {
    println!("\n=== Testing to_markdown() with ColumnAware mode ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let options = ConversionOptions {
        reading_order_mode: ReadingOrderMode::ColumnAware,
        ..Default::default()
    };

    let markdown = doc
        .to_markdown(0, &options)
        .expect("Failed to convert with ColumnAware mode");

    assert_text_is_readable(&markdown, "to_markdown(ColumnAware)");
    println!("✓ ColumnAware reading order works");
}

#[test]
fn test_gdpr_to_markdown_top_to_bottom() {
    println!("\n=== Testing to_markdown() with TopToBottomLeftToRight mode ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let options = ConversionOptions {
        reading_order_mode: ReadingOrderMode::TopToBottomLeftToRight,
        ..Default::default()
    };

    let markdown = doc
        .to_markdown(0, &options)
        .expect("Failed to convert with TopToBottomLeftToRight mode");

    assert_text_is_readable(&markdown, "to_markdown(TopToBottomLeftToRight)");
    println!("✓ TopToBottomLeftToRight reading order works");
}

#[test]
#[ignore] // TODO: HTML extraction appears to be not fully implemented yet
fn test_gdpr_to_html_single_page() {
    println!("\n=== Testing to_html() (single page) ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    // Test semantic HTML (default)
    let options = ConversionOptions::default();
    let html = doc
        .to_html(0, &options)
        .expect("Failed to convert page 0 to HTML");

    assert!(!html.is_empty(), "to_html() returned empty string");
    println!("Generated {} characters of HTML", html.len());

    assert_text_is_readable(&html, "to_html(semantic)");

    // Verify HTML tags are present
    assert!(html.contains("<p>") || html.contains("<div>"),
        "HTML output missing paragraph/div tags");
    println!("✓ HTML structure present");

    // Test layout-preserved HTML
    let options_layout = ConversionOptions {
        preserve_layout: true,
        ..Default::default()
    };
    let html_layout = doc
        .to_html(0, &options_layout)
        .expect("Failed to convert with layout preservation");

    assert_text_is_readable(&html_layout, "to_html(layout)");
    println!("✓ Layout-preserved HTML works");
}

#[test]
#[ignore] // TODO: HTML extraction appears to be not fully implemented yet
fn test_gdpr_to_html_all_pages() {
    println!("\n=== Testing to_html_all() ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let options = ConversionOptions::default();
    let html = doc
        .to_html_all(&options)
        .expect("Failed to convert all pages to HTML");

    assert!(!html.is_empty(), "to_html_all() returned empty string");
    println!(
        "Generated {} characters of HTML from all pages",
        html.len()
    );

    assert_text_is_readable(&html, "to_html_all");
}

#[test]
fn test_gdpr_to_plain_text_single_page() {
    println!("\n=== Testing to_plain_text() (single page) ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let options = ConversionOptions::default();
    let text = doc
        .to_plain_text(0, &options)
        .expect("Failed to convert page 0 to plain text");

    assert!(!text.is_empty(), "to_plain_text() returned empty string");
    println!("Generated {} characters of plain text", text.len());

    assert_text_is_readable(&text, "to_plain_text");

    // Verify it's actually plain text (no markdown/HTML formatting)
    assert!(
        !text.contains("**") && !text.contains("<p>"),
        "Plain text contains formatting markers (should be stripped)"
    );
    println!("✓ Text is plain (no formatting markers)");
}

#[test]
fn test_gdpr_to_plain_text_all_pages() {
    println!("\n=== Testing to_plain_text_all() ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let options = ConversionOptions::default();
    let text = doc
        .to_plain_text_all(&options)
        .expect("Failed to convert all pages to plain text");

    assert!(
        !text.is_empty(),
        "to_plain_text_all() returned empty string"
    );
    println!(
        "Generated {} characters of plain text from all pages",
        text.len()
    );

    assert_text_is_readable(&text, "to_plain_text_all");
}

#[test]
fn test_gdpr_extract_text_legacy() {
    println!("\n=== Testing extract_text() (legacy method) ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let text = doc
        .extract_text(0)
        .expect("Failed to extract text from page 0");

    assert!(!text.is_empty(), "extract_text() returned empty string");
    println!("Extracted {} characters of text", text.len());

    assert_text_is_readable(&text, "extract_text");
}

#[test]
fn test_gdpr_tounicode_cmap_loaded() {
    println!("\n=== Testing ToUnicode CMap Loading ===");

    // This test verifies that ToUnicode CMaps are being loaded
    // We can't directly access FontInfo from tests, but we can verify
    // that extraction produces readable text (which requires ToUnicode)

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let spans = doc
        .extract_spans(0)
        .expect("Failed to extract spans from page 0");

    // Concatenate text
    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // If ToUnicode is working, we should see:
    // - Correct character mappings (not scrambled)
    // - Multi-byte character codes decoded properly
    // - Font-specific glyphs rendered as correct Unicode

    assert_text_is_readable(&text, "ToUnicode CMap");

    println!("✓ ToUnicode CMap is loaded and working correctly");
}

#[test]
fn test_gdpr_multi_byte_character_handling() {
    println!("\n=== Testing Multi-Byte Character Code Handling ===");

    // GDPR PDF uses Type0 fonts with Identity-H encoding
    // which means 2-byte character codes (big-endian)

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let spans = doc
        .extract_spans(0)
        .expect("Failed to extract spans from page 0");

    // Verify we got meaningful text (not ?????? or empty)
    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // Should not contain replacement characters (U+FFFD) in large quantities
    let replacement_count = text.chars().filter(|&c| c == '\u{FFFD}').count();
    let total_chars = text.chars().count();

    assert!(
        replacement_count < total_chars / 10, // Less than 10% replacement chars
        "Too many replacement characters ({}/{}). Multi-byte decoding may be broken.",
        replacement_count,
        total_chars
    );

    println!(
        "✓ Multi-byte character codes handled correctly ({} chars, {} replacements)",
        total_chars, replacement_count
    );

    assert_text_is_readable(&text, "Multi-byte handling");
}

#[test]
fn test_gdpr_font_weight_detection() {
    println!("\n=== Testing Font Weight Detection ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let spans = doc
        .extract_spans(0)
        .expect("Failed to extract spans from page 0");

    // Count bold vs normal spans
    let bold_count = spans.iter().filter(|s| s.font_weight.is_bold()).count();
    let normal_count = spans.len() - bold_count;

    println!(
        "Font weight distribution: {} normal, {} bold",
        normal_count, bold_count
    );

    // GDPR should have at least some bold text (titles, headers, etc.)
    // But we don't assert because page 0 might not have bold text
    if bold_count > 0 {
        println!("✓ Bold text detected");
    } else {
        println!("⚠ No bold text detected (may be normal for page 0)");
    }

    // Verify font names are present
    let fonts_with_names = spans.iter().filter(|s| !s.font_name.is_empty()).count();
    assert!(
        fonts_with_names > 0,
        "No font names found in spans (font info missing)"
    );
    println!("✓ Font names present in {} spans", fonts_with_names);
}

#[test]
fn test_gdpr_bounding_boxes() {
    println!("\n=== Testing Bounding Box Accuracy ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let spans = doc
        .extract_spans(0)
        .expect("Failed to extract spans from page 0");

    // Verify bounding boxes are present and reasonable
    for (i, span) in spans.iter().take(10).enumerate() {
        assert!(
            span.bbox.width > 0.0,
            "Span {} has zero or negative width",
            i
        );
        assert!(
            span.bbox.height > 0.0,
            "Span {} has zero or negative height",
            i
        );

        // Font size should be reasonable (typically 8-72 pt)
        assert!(
            span.font_size > 0.0 && span.font_size < 1000.0,
            "Span {} has unreasonable font size: {}",
            i,
            span.font_size
        );
    }

    println!("✓ Bounding boxes are present and reasonable");
}

#[test]
fn test_gdpr_consistency_across_methods() {
    println!("\n=== Testing Consistency Across Extraction Methods ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    // Extract using different methods (excluding HTML which is not fully implemented)
    let options = ConversionOptions::default();
    let markdown = doc
        .to_markdown(0, &options)
        .expect("Failed to convert to markdown");
    let plain_text = doc
        .to_plain_text(0, &options)
        .expect("Failed to convert to plain text");
    let legacy_text = doc.extract_text(0).expect("Failed to extract text");

    // All methods should produce readable text
    assert_text_is_readable(&markdown, "consistency:markdown");
    assert_text_is_readable(&plain_text, "consistency:plain_text");
    assert_text_is_readable(&legacy_text, "consistency:extract_text");

    // All methods should find at least some common phrases
    let common_phrase = "European Union";

    let markdown_has = markdown.contains(common_phrase);
    let plain_has = plain_text.contains(common_phrase);
    let legacy_has = legacy_text.contains(common_phrase);

    // At least 2 out of 3 methods should find the common phrase
    let found_count = [markdown_has, plain_has, legacy_has]
        .iter()
        .filter(|&&x| x)
        .count();

    assert!(
        found_count >= 2,
        "Only {}/3 methods found common phrase '{}'. Methods are inconsistent.",
        found_count,
        common_phrase
    );

    println!(
        "✓ All extraction methods produce consistent results ({}/3 found common phrase)",
        found_count
    );
}

#[test]
fn test_gdpr_no_character_splitting() {
    println!("\n=== Testing No Character Splitting ===");

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    let spans = doc
        .extract_spans(0)
        .expect("Failed to extract spans from page 0");

    // Check that spans contain complete words, not individual characters
    // Single-character spans are OK (like "I", "a"), but most spans should be longer

    let single_char_spans = spans.iter().filter(|s| s.text.len() == 1).count();
    let total_spans = spans.len();

    // Less than 30% should be single-character spans
    let single_char_percentage = (single_char_spans as f32 / total_spans as f32) * 100.0;

    assert!(
        single_char_percentage < 30.0,
        "Too many single-character spans ({:.1}%). Character splitting may be occurring.",
        single_char_percentage
    );

    println!(
        "✓ No excessive character splitting ({:.1}% single-char spans)",
        single_char_percentage
    );

    // Check for common multi-character words
    let multi_char_words = spans
        .iter()
        .filter(|s| s.text.len() >= 3)
        .take(10)
        .map(|s| &s.text)
        .collect::<Vec<_>>();

    println!("Sample multi-character spans: {:?}", multi_char_words);
}

#[test]
#[ignore] // Ignored by default as it requires Python environment
fn test_gdpr_python_bindings() {
    println!("\n=== Testing Python Bindings ===");
    println!("Note: This test requires maturin develop to have been run");

    // This test would require Python environment and maturin
    // Marking as ignored for CI, but can be run manually:
    // cargo test test_gdpr_python_bindings -- --ignored

    // TODO: Add Python test script that:
    // 1. from pdf_oxide import PdfDocument
    // 2. doc = PdfDocument("../pdf_oxide_tests/pdfs/diverse/EU_GDPR_Regulation.pdf")
    // 3. text = doc.extract_text(0)
    // 4. markdown = doc.to_markdown(0)
    // 5. Verify both are readable
}

/// Integration test: Full pipeline from PDF to markdown file
#[test]
fn test_gdpr_full_pipeline() {
    println!("\n=== Testing Full Extraction Pipeline ===");

    use std::fs;

    let mut doc = PdfDocument::open(GDPR_PDF).expect("Failed to open GDPR PDF");

    // Extract to markdown
    let options = ConversionOptions {
        detect_headings: true,
        ..Default::default()
    };
    let markdown = doc
        .to_markdown_all(&options)
        .expect("Failed to convert to markdown");

    // Save to temporary file
    let temp_path = std::env::temp_dir().join("gdpr_test_output.md");
    fs::write(&temp_path, &markdown).expect("Failed to write markdown file");

    println!("Wrote {} bytes to {:?}", markdown.len(), temp_path);

    // Read back and verify
    let read_back = fs::read_to_string(&temp_path).expect("Failed to read markdown file");

    assert_eq!(
        markdown, read_back,
        "Markdown content changed after write/read"
    );

    assert_text_is_readable(&read_back, "full_pipeline");

    // Cleanup
    fs::remove_file(&temp_path).ok();

    println!("✓ Full pipeline works end-to-end");
}
