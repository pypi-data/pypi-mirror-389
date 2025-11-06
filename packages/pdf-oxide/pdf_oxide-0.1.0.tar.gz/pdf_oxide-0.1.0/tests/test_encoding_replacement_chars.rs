//! Regression test for encoding and replacement character issues
//!
//! Issue: 10.7% of extracted PDFs contain replacement characters (�)
//! indicating encoding problems with character mapping.
//!
//! Root causes:
//! 1. Missing or incomplete ToUnicode CMaps
//! 2. Incorrect character code to Unicode mapping
//! 3. Unsupported font encodings (CJK, legacy encodings)
//! 4. Malformed font dictionaries
//!
//! This test documents known problematic PDFs and tracks progress
//! in fixing encoding issues to achieve 100% clean extraction.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// Check if text contains replacement characters
fn has_replacement_chars(text: &str) -> bool {
    text.contains('�')
}

/// Count replacement characters in text
fn count_replacement_chars(text: &str) -> usize {
    text.matches('�').count()
}

/// Extract context around replacement characters for debugging
fn extract_replacement_context(text: &str, context_chars: usize) -> Vec<String> {
    let mut contexts = Vec::new();
    let chars: Vec<char> = text.chars().collect();

    for (i, &c) in chars.iter().enumerate() {
        if c == '�' {
            let start = i.saturating_sub(context_chars);
            let end = (i + context_chars + 1).min(chars.len());
            let context: String = chars[start..end].iter().collect();
            contexts.push(context);
        }
    }

    contexts
}

#[test]
fn test_arxiv_no_replacement_chars() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";
    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let count = count_replacement_chars(&markdown);

    if count > 0 {
        println!("❌ Found {} replacement characters", count);

        let contexts = extract_replacement_context(&markdown, 20);
        println!("\nContext around replacement characters:");
        for (i, ctx) in contexts.iter().take(5).enumerate() {
            println!("  {}. '{}'", i + 1, ctx);
        }

        panic!("Replacement characters found in ArXiv PDF (encoding issue)");
    }

    println!("✅ No replacement characters in ArXiv PDF");
}

#[test]
fn test_government_cfr_no_replacement_chars() {
    // Government PDFs are known to have encoding issues (en-dash, em-dash)
    let pdf_path = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Vol1_Navigation.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("⚠️ Skipping test: {} not found", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open CFR PDF");

    let options = ConversionOptions::default();

    // Check first few pages
    for page in 0..3 {
        let markdown = doc.to_markdown(page, &options)
            .expect(&format!("Failed to convert page {}", page));

        let count = count_replacement_chars(&markdown);

        if count > 0 {
            println!("❌ Page {}: Found {} replacement characters", page, count);

            let contexts = extract_replacement_context(&markdown, 20);
            println!("\nContext around replacement characters:");
            for (i, ctx) in contexts.iter().take(3).enumerate() {
                println!("  {}. '{}'", i + 1, ctx);
            }

            panic!("Replacement characters found in CFR PDF page {} (encoding issue)", page);
        }
    }

    println!("✅ No replacement characters in CFR PDF (first 3 pages)");
}

#[test]
fn test_special_characters_en_dash() {
    // Test for proper en-dash (–) encoding, not replacement char
    let pdf_path = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Vol1_Navigation.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("⚠️ Skipping test: {} not found", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open CFR PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert page 0");

    // CFR documents often use en-dash (U+2013) for ranges
    // We should see proper en-dashes, not replacement chars
    let has_en_dash = markdown.contains('–');
    let has_replacement = markdown.contains('�');

    println!("En-dash (–) found: {}", has_en_dash);
    println!("Replacement char (�) found: {}", has_replacement);

    if has_replacement {
        println!("❌ Found replacement characters instead of proper en-dash encoding");

        let contexts = extract_replacement_context(&markdown, 30);
        println!("\nContext (first 3):");
        for (i, ctx) in contexts.iter().take(3).enumerate() {
            println!("  {}. '{}'", i + 1, ctx);
        }

        panic!("En-dash not properly encoded (showing as replacement char)");
    }

    println!("✅ Special characters properly encoded (no replacement chars)");
}

#[test]
fn test_unicode_characters_preserved() {
    // Test that common Unicode characters are preserved correctly
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";
    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Common Unicode characters in academic papers
    let unicode_chars = [
        ('α', "Greek alpha"),
        ('β', "Greek beta"),
        ('γ', "Greek gamma"),
        ('σ', "Greek sigma"),
        ('μ', "Greek mu"),
        ('π', "Greek pi"),
        ('∈', "Element of"),
        ('∑', "Summation"),
        ('∫', "Integral"),
        ('≤', "Less than or equal"),
        ('≥', "Greater than or equal"),
        ('≠', "Not equal"),
        ('×', "Multiplication"),
        ('÷', "Division"),
        ('°', "Degree"),
        ('±', "Plus-minus"),
    ];

    let mut found_chars = Vec::new();
    for (ch, name) in &unicode_chars {
        if markdown.contains(*ch) {
            found_chars.push((ch, name));
        }
    }

    println!("✅ Found {} Unicode characters preserved:", found_chars.len());
    for (ch, name) in &found_chars {
        println!("  - {} ({})", ch, name);
    }

    // If we have replacement chars, Unicode preservation failed
    if has_replacement_chars(&markdown) {
        let count = count_replacement_chars(&markdown);
        println!("❌ Unicode preservation failed: {} replacement chars", count);
        panic!("Unicode characters not properly preserved");
    }
}

#[test]
fn test_font_encoding_coverage() {
    // Test a diverse set of PDFs to ensure broad encoding support
    let test_pdfs = [
        ("../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf", "Academic (ArXiv)"),
        ("../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Vol1_Navigation.pdf", "Government (CFR)"),
    ];

    let mut total_pdfs = 0;
    let mut clean_pdfs = 0;

    for (path, category) in &test_pdfs {
        if !std::path::Path::new(path).exists() {
            println!("⚠️ Skipping: {} not found", path);
            continue;
        }

        total_pdfs += 1;

        let mut doc = PdfDocument::open(path)
            .expect(&format!("Failed to open {}", path));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert page 0");

        let has_issues = has_replacement_chars(&markdown);

        if has_issues {
            let count = count_replacement_chars(&markdown);
            println!("❌ {}: {} replacement chars", category, count);
        } else {
            clean_pdfs += 1;
            println!("✅ {}: Clean extraction", category);
        }
    }

    let success_rate = (clean_pdfs as f64 / total_pdfs as f64) * 100.0;
    println!("\nEncoding success rate: {}/{} ({:.1}%)", clean_pdfs, total_pdfs, success_rate);

    // Target: 100% clean extraction (no replacement chars)
    if success_rate < 100.0 {
        panic!(
            "Encoding coverage insufficient: {:.1}% (target: 100%)",
            success_rate
        );
    }
}

#[test]
fn test_replacement_char_diagnosis() {
    // This test is for diagnosis only - it doesn't fail, just reports
    // Run with --nocapture to see detailed output

    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";
    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let count = count_replacement_chars(&markdown);

    if count > 0 {
        println!("\n📊 REPLACEMENT CHARACTER ANALYSIS");
        println!("Total replacement chars: {}", count);
        println!("\nContexts (up to 10):");

        let contexts = extract_replacement_context(&markdown, 30);
        for (i, ctx) in contexts.iter().take(10).enumerate() {
            println!("\n{}. Context ({} chars):", i + 1, ctx.len());
            println!("   '{}'", ctx);

            // Try to identify the pattern
            if ctx.contains("–") || ctx.contains("-") {
                println!("   → Likely: en-dash/em-dash encoding issue");
            } else if ctx.chars().any(|c| c.is_ascii_punctuation()) {
                println!("   → Likely: punctuation encoding issue");
            } else if ctx.chars().any(|c| !c.is_ascii()) {
                println!("   → Likely: Unicode character mapping issue");
            } else {
                println!("   → Unknown encoding issue");
            }
        }
    } else {
        println!("✅ No replacement characters found - encoding is clean!");
    }
}
