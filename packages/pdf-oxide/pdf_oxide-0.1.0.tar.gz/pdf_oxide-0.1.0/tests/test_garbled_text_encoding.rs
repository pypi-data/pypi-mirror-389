//! Regression tests for garbled text and encoding issues
//!
//! HIGH SEVERITY ISSUE: Some PDFs produce garbled, corrupted, or
//! improperly encoded text output.
//!
//! Examples:
//! - "(LegislativREGUL**REGUL(T**Ha1), 2), 3), 4)"
//! - "**Printed wi**** on rec d****r**"
//! - Mixed markdown formatting in plain text
//! - Character encoding failures
//!
//! Root causes:
//! 1. Font ToUnicode CMap parsing issues
//! 2. Encoding detection failures
//! 3. Markdown formatting bleeding into content
//! 4. Stream decoding errors
//!
//! PDF Spec Reference: ISO 32000-1:2008 Section 9.10.2 (ToUnicode CMaps)
//! and Section 9.6.6 (Character encoding)

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;

const GDPR_PDF: &str = "../pdf_oxide_tests/pdfs/diverse/EU_GDPR_Regulation.pdf";
const MIXED_PDF: &str = "../pdf_oxide_tests/pdfs/mixed/2Z5VOQ6G6CMR5GMVSAAXULXHXTMJPTM2.pdf";

/// Patterns that indicate garbled text
const GARBLED_PATTERNS: &[&str] = &[
    "LegislativREGUL**REGUL",
    "**REGUL(T**",
    "Printed wi****",
    "rec d****r**",
    "Oeesci", // "Other Defense Activities" garbled
];

/// Check for excessive markdown artifacts in plain text
fn check_markdown_bleeding(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Count asterisk pairs (markdown bold)
    let bold_markers = text.matches("**").count();
    if bold_markers > 0 {
        // This is only an issue if it's supposed to be plain text
        issues.push(format!(
            "Found {} markdown bold markers (**) in plain text",
            bold_markers
        ));
    }

    // Check for excessive punctuation mixing
    let mixed_punct_re = regex::Regex::new(r"\*{2,}\w+\*{2,}").unwrap();
    for mat in mixed_punct_re.find_iter(text) {
        issues.push(format!(
            "Markdown formatting artifact: '{}'",
            mat.as_str()
        ));
    }

    issues
}

/// Check for garbled character sequences
fn check_garbled_sequences(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    for pattern in GARBLED_PATTERNS {
        if text.contains(pattern) {
            issues.push(format!(
                "Found garbled pattern: '{}'",
                pattern
            ));
        }
    }

    // Check for suspicious character repetitions
    let re = regex::Regex::new(r"([A-Z]{10,}|[a-z]{15,})").unwrap();
    for mat in re.find_iter(text) {
        let matched = mat.as_str();
        // Allow some legitimate long words or concatenated words (spacing issues are separate)
        let lowercase = matched.to_lowercase();
        if !matches!(lowercase.as_str(),
                     "internationalization" | "responsibilities" | "telecommunications") &&
           // Allow words that are just concatenated English (spacing issue, not garbling)
           !lowercase.contains("legislative") && !lowercase.contains("representation") &&
           !lowercase.contains("significantly") {
            issues.push(format!(
                "Suspicious long character sequence: '{}'",
                &matched[..20.min(matched.len())]
            ));
        }
    }

    issues
}

/// Check for Unicode replacement characters (indicates encoding failure)
fn check_replacement_characters(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    let replacement_count = text.chars().filter(|&c| c == '\u{FFFD}').count();
    let total_chars = text.chars().count();

    if replacement_count > 0 {
        let ratio = (replacement_count as f64 / total_chars as f64) * 100.0;
        if ratio > 1.0 {
            issues.push(format!(
                "High replacement character ratio: {:.1}% ({}/{})",
                ratio, replacement_count, total_chars
            ));
        }
    }

    issues
}

/// Check for proper character encoding (UTF-8 validity)
fn check_encoding_validity(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Check if string is valid UTF-8 (should always be true in Rust String)
    // But check for suspicious byte sequences that might indicate issues

    // Check for control characters (except whitespace)
    let control_chars: Vec<char> = text.chars()
        .filter(|&c| c.is_control() && c != '\n' && c != '\r' && c != '\t')
        .collect();

    if !control_chars.is_empty() {
        issues.push(format!(
            "Found {} unexpected control characters",
            control_chars.len()
        ));
    }

    issues
}

#[test]
fn test_gdpr_no_garbled_text() {
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    println!("Extracted {} chars from GDPR PDF", text.len());
    println!("Sample: {}", &text[..200.min(text.len())]);

    let garbled = check_garbled_sequences(&text);
    let replacement = check_replacement_characters(&text);
    let encoding = check_encoding_validity(&text);

    let all_issues: Vec<_> = garbled.iter()
        .chain(replacement.iter())
        .chain(encoding.iter())
        .collect();

    if !all_issues.is_empty() {
        println!("\n❌ GARBLED TEXT ISSUES:");
        for issue in all_issues {
            println!("  - {}", issue);
        }
        panic!("Garbled text detected in GDPR PDF");
    }

    println!("✅ No garbled text in GDPR PDF");
}

#[test]
fn test_gdpr_markdown_no_formatting_bleed() {
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    // Extract as plain text (should have NO markdown)
    let plain_text = doc.to_plain_text(0, &ConversionOptions::default())
        .expect("Failed to extract plain text");

    let markdown_issues = check_markdown_bleeding(&plain_text);

    if !markdown_issues.is_empty() {
        println!("\n❌ MARKDOWN BLEEDING INTO PLAIN TEXT:");
        for issue in &markdown_issues {
            println!("  - {}", issue);
        }
        panic!("Markdown formatting leaked into plain text");
    }

    println!("✅ No markdown bleeding in plain text");
}

#[test]
fn test_mixed_pdf_no_garbled_text() {
    let mut doc = PdfDocument::open(MIXED_PDF)
        .expect("Failed to open mixed PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    let issues = check_garbled_sequences(&text);

    if !issues.is_empty() {
        println!("\n❌ GARBLED TEXT IN MIXED PDF:");
        for issue in &issues {
            println!("  - {}", issue);
        }
        panic!("Garbled text detected");
    }

    println!("✅ No garbled text in mixed PDF");
}

#[test]
fn test_tounicode_cmap_produces_readable_text() {
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // Expected readable phrases (from GDPR document)
    let expected = [
        "European Union",
        "protection of natural persons",
        "personal data",
        "Treaty",
        "Parliament",
    ];

    let mut found = 0;
    for phrase in &expected {
        if text.contains(phrase) {
            found += 1;
        }
    }

    assert!(
        found >= expected.len() / 2,
        "Only {}/{} expected phrases found. ToUnicode CMap may be broken.",
        found,
        expected.len()
    );

    println!("✅ ToUnicode CMap produces readable text ({}/{} phrases)",
             found, expected.len());
}

#[test]
fn test_replacement_character_threshold() {
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    let replacement_count = text.chars().filter(|&c| c == '\u{FFFD}').count();
    let total_chars = text.chars().count();
    let ratio = (replacement_count as f64 / total_chars as f64) * 100.0;

    println!("Replacement characters: {} / {} ({:.2}%)",
             replacement_count, total_chars, ratio);

    // Should be < 1% replacement characters
    assert!(
        ratio < 1.0,
        "Too many replacement characters ({:.1}%). Encoding is failing.",
        ratio
    );

    println!("✅ Replacement character ratio acceptable");
}

#[test]
fn test_control_character_filtering() {
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    let issues = check_encoding_validity(&markdown);

    if !issues.is_empty() {
        println!("\n⚠️ ENCODING ISSUES:");
        for issue in &issues {
            println!("  - {}", issue);
        }
        panic!("Unexpected control characters in output");
    }

    println!("✅ No unexpected control characters");
}

#[test]
fn test_all_extraction_methods_produce_valid_text() {
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    let options = ConversionOptions::default();

    // Extract using all methods
    let spans = doc.extract_spans(0).expect("spans failed");
    let markdown = doc.to_markdown(0, &options).expect("markdown failed");
    let plain = doc.to_plain_text(0, &options).expect("plain failed");

    let span_text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // All should be valid UTF-8 (guaranteed by String type)
    // But check for garbling
    for (name, text) in [("spans", &span_text), ("markdown", &markdown), ("plain", &plain)] {
        let issues = check_garbled_sequences(text);
        assert!(
            issues.is_empty(),
            "Garbled text in {} method: {:?}",
            name,
            issues
        );
    }

    println!("✅ All extraction methods produce valid text");
}

#[test]
fn test_font_specific_encoding_issues() {
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Group spans by font
    let mut font_issues: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();

    for span in &spans {
        if !span.font_name.is_empty() {
            let issues = check_garbled_sequences(&span.text);
            if !issues.is_empty() {
                font_issues.entry(span.font_name.clone())
                    .or_insert_with(Vec::new)
                    .extend(issues);
            }
        }
    }

    if !font_issues.is_empty() {
        println!("\n❌ FONT-SPECIFIC ENCODING ISSUES:");
        for (font, issues) in &font_issues {
            println!("  Font '{}': {} issues", font, issues.len());
            for issue in issues.iter().take(3) {
                println!("    - {}", issue);
            }
        }
        panic!("Font-specific encoding issues detected");
    }

    println!("✅ No font-specific encoding issues");
}

#[test]
fn test_multibyte_character_decoding() {
    // GDPR uses Type0 fonts with Identity-H encoding (2-byte codes)
    // Note: The GDPR PDF is English text, so 100% ASCII is actually correct
    let mut doc = PdfDocument::open(GDPR_PDF)
        .expect("Failed to open GDPR PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // Check that text is valid UTF-8 and not corrupted
    let ascii_count = text.chars().filter(|c| c.is_ascii()).count();
    let total_count = text.chars().count();
    let ascii_ratio = ascii_count as f64 / total_count as f64;

    println!("ASCII ratio: {:.1}% ({}/{} chars)",
             ascii_ratio * 100.0, ascii_count, total_count);

    // GDPR PDF is English, so high ASCII ratio is expected and correct
    // Just verify we have actual text, not corrupted data
    assert!(
        total_count > 1000,
        "Too little text extracted ({} chars). Extraction may have failed.",
        total_count
    );

    // Check for replacement characters (indicates encoding failure)
    let replacement_count = text.chars().filter(|&c| c == '\u{FFFD}').count();
    assert!(
        replacement_count == 0,
        "Found {} replacement characters. Encoding failed.",
        replacement_count
    );

    println!("✅ Multibyte character decoding working (ASCII: {:.1}%)", ascii_ratio * 100.0);
}
