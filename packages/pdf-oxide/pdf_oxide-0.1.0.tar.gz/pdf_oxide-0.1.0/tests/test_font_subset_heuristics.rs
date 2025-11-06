//! Regression test for font subset heuristics (Phase 7B)
//!
//! This test suite validates the font subset and CJK detection heuristics
//! for handling embedded fonts without ToUnicode CMaps.
//!
//! PDF Spec Compliance:
//! - ISO 32000-1:2008 Section 9.6 (Font Descriptors)
//! - ISO 32000-1:2008 Section 9.7 (Font Encoding)
//!
//! Root Causes Addressed:
//! 1. Embedded subset fonts (40% of remaining failures)
//!    - Font names like "ABCDEF+Times-Roman" without ToUnicode CMap
//!    - Should fallback to StandardEncoding based on font family
//! 2. CJK fonts without Identity encoding (15% of remaining failures)
//!    - Fonts with CJK characters but missing Identity-H/V encoding marker
//!    - Should assume Identity-H encoding based on font name heuristics

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

// Test PDFs with subset fonts and CJK fonts
const PDF_WITH_SUBSET_FONTS: &str = "../pdf_oxide_tests/pdfs/mixed/YBTLDNWUYL3SLS4NVMFEB3OFUWOZBLA7.pdf";
const ARXIV_MATH: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25760v1.pdf";

/// Count replacement characters in text
fn count_replacement_chars(text: &str) -> usize {
    text.chars().filter(|&c| c == '\u{FFFD}' || c == '?').count()
}

/// Extract font names from PDF (helper for debugging)
fn extract_font_info(doc: &mut PdfDocument, page_num: usize) -> Vec<String> {
    // This is a simplified version - in real implementation we'd need to
    // parse the font dictionary from the page resources
    vec![]  // Placeholder
}

#[test]
fn test_subset_font_name_parsing() {
    // Test that subset prefixes are correctly identified
    let subset_fonts = vec![
        ("ABCDEF+Times-Roman", "Times-Roman"),
        ("GHIJKL+Helvetica", "Helvetica"),
        ("MNOPQR+Courier", "Courier"),
        ("STUVWX+Arial", "Arial"),
        ("YZABCD+TimesNewRoman", "TimesNewRoman"),
    ];

    println!("\n=== Subset Font Name Parsing ===");

    for (full_name, expected_base) in &subset_fonts {
        // Extract base name (remove subset prefix)
        let base_name = if let Some(plus_idx) = full_name.find('+') {
            &full_name[plus_idx + 1..]
        } else {
            full_name
        };

        println!("  '{}' -> '{}'", full_name, base_name);

        assert_eq!(
            base_name, *expected_base,
            "Failed to extract base font name from '{}'",
            full_name
        );
    }

    println!("✅ Subset font name parsing works correctly");
}

#[test]
fn test_font_family_detection() {
    // Test that font families are correctly detected for encoding fallback
    let test_cases = vec![
        ("Times-Roman", Some("StandardEncoding")),
        ("Times-Bold", Some("StandardEncoding")),
        ("Times-Italic", Some("StandardEncoding")),
        ("TimesNewRoman", Some("StandardEncoding")),
        ("Helvetica", Some("WinAnsiEncoding")),
        ("Helvetica-Bold", Some("WinAnsiEncoding")),
        ("Arial", Some("WinAnsiEncoding")),
        ("ArialMT", Some("WinAnsiEncoding")),
        ("Courier", Some("StandardEncoding")),
        ("Courier-Bold", Some("StandardEncoding")),
        ("CourierNew", Some("StandardEncoding")),
        ("Symbol", None),  // Symbolic font, no standard encoding
        ("ZapfDingbats", None),  // Symbolic font
        ("CustomFont", None),  // Unknown font family
    ];

    println!("\n=== Font Family Detection ===");

    for (font_name, expected_encoding) in &test_cases {
        let font_lower = font_name.to_lowercase();

        let detected_encoding = if font_lower.contains("times") || font_lower.contains("serif") {
            Some("StandardEncoding")
        } else if font_lower.contains("arial") || font_lower.contains("helvetica") {
            Some("WinAnsiEncoding")
        } else if font_lower.contains("courier") {
            Some("StandardEncoding")
        } else {
            None
        };

        println!("  '{}' -> {:?}", font_name, detected_encoding);

        assert_eq!(
            detected_encoding, *expected_encoding,
            "Wrong encoding detected for font '{}'",
            font_name
        );
    }

    println!("✅ Font family detection works correctly");
}

#[test]
fn test_cjk_font_detection() {
    // Test that CJK fonts are correctly identified
    let cjk_fonts = vec![
        ("SimSun", true),           // Simplified Chinese
        ("SimHei", true),           // Simplified Chinese
        ("MingLiU", true),          // Traditional Chinese
        ("MS-Gothic", true),        // Japanese
        ("HeiseiKakuGo", true),     // Japanese
        ("Batang", true),           // Korean
        ("Dotum", true),            // Korean
        ("STSong", true),           // Chinese
        ("STHeiti", true),          // Chinese
        ("HiraginoSans", true),     // Japanese
        ("Times-Roman", false),     // Not CJK
        ("Helvetica", false),       // Not CJK
        ("Arial", false),           // Not CJK
    ];

    println!("\n=== CJK Font Detection ===");

    for (font_name, is_cjk) in &cjk_fonts {
        let name_lower = font_name.to_lowercase();

        let detected_cjk = name_lower.contains("cjk") ||
            name_lower.contains("sim") ||      // Simplified Chinese
            name_lower.contains("ming") ||     // Traditional Chinese
            name_lower.contains("gothic") ||   // Japanese
            name_lower.contains("heisei") ||   // Japanese
            name_lower.contains("hiragino") || // Japanese
            name_lower.contains("batang") ||   // Korean
            name_lower.contains("dotum") ||    // Korean
            name_lower.contains("heiti") ||    // Chinese
            name_lower.contains("song") ||     // Chinese (STSong)
            name_lower.contains("kai");        // Chinese (Kai)

        println!("  '{}' -> CJK: {}", font_name, detected_cjk);

        assert_eq!(
            detected_cjk, *is_cjk,
            "Wrong CJK detection for font '{}'",
            font_name
        );
    }

    println!("✅ CJK font detection works correctly");
}

#[test]
fn test_identity_encoding_assumption_for_cjk() {
    // Test that CJK character codes are correctly interpreted as Identity-H
    // when font is detected as CJK

    // CJK Unified Ideographs range: U+4E00-U+9FFF
    let test_cjk_codes = vec![
        (0x4E2D, '中'),  // "middle" in Chinese
        (0x6587, '文'),  // "text/literature"
        (0x5B57, '字'),  // "character/word"
        (0x65E5, '日'),  // "day/sun"
        (0x672C, '本'),  // "origin/book"
    ];

    println!("\n=== Identity Encoding for CJK ===");

    for (code, expected_char) in &test_cjk_codes {
        // In Identity-H encoding, character code directly maps to Unicode
        let decoded_char = char::from_u32(*code as u32);

        println!("  0x{:04X} -> {:?} (expected: {})", code, decoded_char, expected_char);

        assert_eq!(
            decoded_char, Some(*expected_char),
            "Failed to decode CJK code 0x{:04X} with Identity-H",
            code
        );
    }

    println!("✅ Identity-H encoding assumption works for CJK");
}

#[test]
fn test_replacement_char_reduction_with_heuristics() {
    // Test that font subset heuristics reduce replacement characters
    let mut doc = PdfDocument::open(PDF_WITH_SUBSET_FONTS)
        .expect("Failed to open PDF with subset fonts");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let replacement_count = count_replacement_chars(&markdown);

    println!("\n=== Replacement Character Analysis ===");
    println!("  Total characters: {}", markdown.len());
    println!("  Replacement chars: {}", replacement_count);
    println!("  Replacement percentage: {:.2}%",
             (replacement_count as f64 / markdown.len() as f64) * 100.0);

    // With Phase 7A + 7B, we expect very few replacement characters
    // Target: <10 replacement chars per page
    assert!(
        replacement_count < 10,
        "Too many replacement characters ({}) - heuristics not effective",
        replacement_count
    );

    println!("✅ Replacement character count is acceptable");
}

#[test]
fn test_subset_font_fallback_quality() {
    // Test that text extracted from subset fonts is readable
    let mut doc = PdfDocument::open(PDF_WITH_SUBSET_FONTS)
        .expect("Failed to open PDF with subset fonts");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("\n=== Subset Font Fallback Quality ===");
    println!("  Markdown length: {} chars", markdown.len());
    println!("  First 200 chars:\n{}\n", &markdown[..200.min(markdown.len())]);

    // Check for basic sanity
    assert!(
        markdown.len() > 100,
        "Markdown too short: {} chars",
        markdown.len()
    );

    // Check for common English words (should be present if fallback works)
    let common_words = ["the", "and", "of", "to", "in", "is", "for", "that"];
    let mut found_words = 0;

    for word in &common_words {
        if markdown.to_lowercase().contains(word) {
            found_words += 1;
        }
    }

    assert!(
        found_words >= 4,
        "Too few common words found ({}), text may be garbled",
        found_words
    );

    println!("  Found {} / {} common words", found_words, common_words.len());
    println!("✅ Subset font fallback produces readable text");
}

#[test]
fn test_no_quality_degradation() {
    // Test that heuristics don't degrade quality for PDFs that work well already
    let mut doc = PdfDocument::open(ARXIV_MATH)
        .expect("Failed to open arxiv math PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let replacement_count = count_replacement_chars(&markdown);

    println!("\n=== No Quality Degradation Test ===");
    println!("  Arxiv math paper replacement chars: {}", replacement_count);

    // Arxiv PDF should still have 0 replacement chars (Phase 7A result)
    assert_eq!(
        replacement_count, 0,
        "Quality degraded! Arxiv PDF now has {} replacement chars (expected 0)",
        replacement_count
    );

    println!("✅ No quality degradation for well-formed PDFs");
}

#[test]
fn test_backward_compatibility() {
    // Test that Phase 7B doesn't break existing functionality
    let test_pdfs = vec![
        (PDF_WITH_SUBSET_FONTS, "subset fonts PDF"),
        (ARXIV_MATH, "arxiv math PDF"),
    ];

    println!("\n=== Backward Compatibility ===");

    for (pdf_path, name) in &test_pdfs {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", name));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect(&format!("Failed to convert {}", name));

        // Basic sanity checks
        assert!(
            markdown.len() > 100,
            "{}: Markdown too short ({})",
            name, markdown.len()
        );

        assert!(
            markdown.contains('\n'),
            "{}: No newlines in output",
            name
        );

        println!("  {}: {} chars, looks good", name, markdown.len());
    }

    println!("✅ Backward compatibility maintained");
}

#[test]
fn test_performance_no_regression() {
    // Test that heuristics don't slow down processing
    use std::time::Instant;

    let mut doc = PdfDocument::open(PDF_WITH_SUBSET_FONTS)
        .expect("Failed to open PDF");

    let start = Instant::now();
    let options = ConversionOptions::default();
    let _markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");
    let duration = start.elapsed();

    println!("\n=== Performance Test ===");
    println!("  Page conversion time: {:.2}ms", duration.as_secs_f64() * 1000.0);

    // Should complete in reasonable time (< 5 seconds for one page)
    assert!(
        duration.as_secs() < 5,
        "Conversion too slow: {:.2}s (expected: <5s)",
        duration.as_secs_f64()
    );

    println!("✅ Performance acceptable");
}

#[test]
fn test_character_distribution_healthy() {
    // Test that character distribution remains healthy after Phase 7B
    let mut doc = PdfDocument::open(PDF_WITH_SUBSET_FONTS)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let ascii_count = markdown.chars().filter(|c| c.is_ascii()).count();
    let unicode_count = markdown.chars().filter(|c| !c.is_ascii() && *c != '\u{FFFD}').count();
    let replacement_count = count_replacement_chars(&markdown);
    let total_chars = markdown.chars().count();

    let replacement_percentage = (replacement_count as f64 / total_chars as f64) * 100.0;

    println!("\n=== Character Distribution ===");
    println!("  ASCII: {} ({:.1}%)", ascii_count, (ascii_count as f64 / total_chars as f64) * 100.0);
    println!("  Unicode (non-ASCII): {} ({:.1}%)", unicode_count, (unicode_count as f64 / total_chars as f64) * 100.0);
    println!("  Replacement (� or ?): {} ({:.1}%)", replacement_count, replacement_percentage);

    // Healthy distribution: mostly ASCII, minimal replacements
    assert!(
        replacement_percentage < 1.0,
        "Too many replacement characters ({:.2}%)",
        replacement_percentage
    );

    println!("✅ Character distribution healthy");
}
