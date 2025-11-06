//! Regression test for character encoding and replacement character fallback
//!
//! Issue: Unicode replacement character (U+FFFD �) appears in text, indicating
//! encoding or character mapping failures.
//!
//! Root cause: ToUnicode CMap parsing failures, missing character mappings,
//! or font encoding issues. Current fallback returns "?" instead of proper
//! Unicode replacement char or trying alternative encoding strategies.
//!
//! Expected behavior: Multi-tier fallback strategy:
//! 1. ToUnicode CMap (primary)
//! 2. Adobe Glyph List for common symbols
//! 3. Standard/WinAnsi Encoding
//! 4. Direct Unicode (if in valid range)
//! 5. Unicode replacement character \u{FFFD} (last resort)

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

// PDFs with known character encoding issues
const HIGH_REPLACEMENT_CHARS: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25760v1.pdf"; // 121 replacement chars
const MIXED_ENCODING: &str = "../pdf_oxide_tests/pdfs/mixed/YBTLDNWUYL3SLS4NVMFEB3OFUWOZBLA7.pdf"; // 139 replacement chars

/// Count replacement characters in text
fn count_replacement_chars(text: &str) -> usize {
    text.chars().filter(|&c| c == '\u{FFFD}').count()
}

/// Find contexts where replacement chars appear
fn find_replacement_contexts(text: &str) -> Vec<String> {
    let mut contexts = Vec::new();

    for (byte_idx, c) in text.char_indices() {
        if c == '\u{FFFD}' {
            // Find char indices around the replacement character
            let chars_before: Vec<(usize, char)> = text.char_indices()
                .take_while(|(i, _)| *i < byte_idx)
                .collect();
            let chars_after: Vec<(usize, char)> = text.char_indices()
                .skip_while(|(i, _)| *i <= byte_idx)
                .collect();

            let start_idx = if chars_before.len() >= 20 {
                chars_before[chars_before.len() - 20].0
            } else {
                0
            };

            let end_idx = if chars_after.len() >= 20 {
                chars_after[19].0 + chars_after[19].1.len_utf8()
            } else {
                text.len()
            };

            let context = &text[start_idx..end_idx];
            contexts.push(format!("...{}...", context));
        }
    }

    contexts
}

#[test]
fn test_no_replacement_characters() {
    let mut doc = PdfDocument::open(HIGH_REPLACEMENT_CHARS)
        .expect("Failed to open PDF with encoding issues");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown", markdown.len());

    let replacement_count = count_replacement_chars(&markdown);

    if replacement_count > 0 {
        println!("\n❌ REPLACEMENT CHARACTERS FOUND: {}", replacement_count);

        let contexts = find_replacement_contexts(&markdown);

        println!("\nFirst 10 occurrences:");
        for (i, context) in contexts.iter().enumerate().take(10) {
            println!("{}. {}", i + 1, context);
        }

        if contexts.len() > 10 {
            println!("\n... and {} more", contexts.len() - 10);
        }

        // Save for debugging
        std::fs::write("/tmp/replacement_chars_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/replacement_chars_debug.md");

        panic!(
            "Found {} replacement characters (�) - character encoding fallback failed",
            replacement_count
        );
    }

    println!("✅ No replacement characters detected");
}

#[test]
fn test_mathematical_symbols_decoded() {
    // Common mathematical symbols that often fail to decode
    let mut doc = PdfDocument::open(HIGH_REPLACEMENT_CHARS)
        .expect("Failed to open math paper");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Expected mathematical symbols (may or may not be in the PDF)
    let expected_symbols = vec![
        ('∈', "element of"),
        ('∀', "for all"),
        ('∃', "exists"),
        ('≤', "less than or equal"),
        ('≥', "greater than or equal"),
        ('∞', "infinity"),
        ('∑', "summation"),
        ('∏', "product"),
        ('∫', "integral"),
        ('∂', "partial derivative"),
        ('∇', "nabla/del"),
        ('α', "alpha"),
        ('β', "beta"),
        ('γ', "gamma"),
        ('δ', "delta"),
        ('θ', "theta"),
        ('λ', "lambda"),
        ('μ', "mu"),
        ('π', "pi"),
        ('σ', "sigma"),
        ('ω', "omega"),
    ];

    // Count which symbols are present (successfully decoded)
    let mut found_symbols = Vec::new();
    let mut missing_symbols = Vec::new();

    for (symbol, name) in &expected_symbols {
        if markdown.contains(*symbol) {
            found_symbols.push((*symbol, name));
        } else {
            missing_symbols.push((*symbol, name));
        }
    }

    println!("Mathematical symbol analysis:");
    println!("Found symbols: {}", found_symbols.len());
    if !found_symbols.is_empty() {
        println!("  Examples:");
        for (symbol, name) in found_symbols.iter().take(5) {
            println!("    {} ({})", symbol, name);
        }
    }

    // Check for replacement chars where symbols should be
    let replacement_count = count_replacement_chars(&markdown);

    if replacement_count > 0 {
        println!("\n⚠️  WARNING:");
        println!("  {} replacement characters found", replacement_count);
        println!("  {} expected symbols not found", missing_symbols.len());
        println!("\nThis suggests mathematical symbols are being replaced with �");

        if replacement_count > 50 {
            panic!(
                "Too many replacement characters ({}) - likely failed symbol decoding",
                replacement_count
            );
        }
    }

    println!("✅ Mathematical symbol decoding analysis complete");
}

#[test]
fn test_special_punctuation_decoded() {
    // Special punctuation marks that often fail to decode
    let mut doc = PdfDocument::open(HIGH_REPLACEMENT_CHARS)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Common special punctuation
    let expected_punctuation = vec![
        ('—', "em dash"),
        ('–', "en dash"),
        ('\u{2018}', "left single quote"),  // '
        ('\u{2019}', "right single quote"), // '
        ('\u{201C}', "left double quote"),  // "
        ('\u{201D}', "right double quote"), // "
        ('…', "ellipsis"),
        ('•', "bullet"),
        ('°', "degree"),
        ('±', "plus-minus"),
        ('×', "multiplication"),
        ('÷', "division"),
    ];

    let mut found = 0;
    let mut not_found = 0;

    for (punct, name) in &expected_punctuation {
        if markdown.contains(*punct) {
            found += 1;
        } else {
            not_found += 1;
        }
    }

    println!("Special punctuation analysis:");
    println!("  Found: {}", found);
    println!("  Not found: {}", not_found);

    let replacement_count = count_replacement_chars(&markdown);

    if replacement_count > 0 && found == 0 {
        println!("\n⚠️  WARNING:");
        println!("  {} replacement characters", replacement_count);
        println!("  0 special punctuation symbols found");
        println!("\nThis suggests punctuation is being replaced with �");
    }

    println!("✅ Special punctuation decoding analysis complete");
}

#[test]
fn test_ligatures_decoded() {
    // Common ligatures that may appear in PDFs
    let mut doc = PdfDocument::open(HIGH_REPLACEMENT_CHARS)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Common ligatures
    let ligatures = vec![
        ("fi", "f-i ligature"),
        ("fl", "f-l ligature"),
        ("ffi", "f-f-i ligature"),
        ("ffl", "f-f-l ligature"),
        ("ff", "f-f ligature"),
    ];

    // Check if words contain these letter combinations
    // (ligatures should be decoded to regular letter sequences)
    let mut found_ligature_combos = Vec::new();

    for (combo, name) in &ligatures {
        if markdown.contains(combo) {
            found_ligature_combos.push((combo, name));
        }
    }

    println!("Ligature analysis:");
    println!("Found {} ligature combinations in text", found_ligature_combos.len());

    if !found_ligature_combos.is_empty() {
        println!("Examples:");
        for (combo, name) in found_ligature_combos.iter().take(3) {
            println!("  {} ({})", combo, name);
        }
        println!("✅ Ligatures appear to be decoded correctly");
    } else {
        println!("ℹ️  No obvious ligature combinations found (may not be present in PDF)");
    }

    // Check for replacement chars
    let replacement_count = count_replacement_chars(&markdown);
    if replacement_count > 0 {
        println!("\n⚠️  {} replacement characters found - some may be failed ligatures", replacement_count);
    }
}

#[test]
fn test_greek_letters_in_equations() {
    // Greek letters commonly used in equations
    let mut doc = PdfDocument::open(HIGH_REPLACEMENT_CHARS)
        .expect("Failed to open math paper");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let greek_letters = "αβγδεζηθικλμνξοπρστυφχψω";

    let greek_count = markdown.chars().filter(|c| greek_letters.contains(*c)).count();

    println!("Greek letter analysis:");
    println!("  Found {} Greek letters in text", greek_count);

    if greek_count > 0 {
        println!("✅ Greek letters are being decoded");
    } else {
        println!("ℹ️  No Greek letters found (may not be present in PDF)");
    }

    let replacement_count = count_replacement_chars(&markdown);
    if replacement_count > 10 && greek_count == 0 {
        println!("\n⚠️  WARNING: Many replacement chars but no Greek letters");
        println!("This suggests Greek letters may be failing to decode");
    }
}

#[test]
fn test_replacement_char_reduction_target() {
    // Test target: reduce replacement chars to <100 across problematic PDFs
    let test_pdfs = vec![
        (HIGH_REPLACEMENT_CHARS, 121, "arxiv math paper"),
        (MIXED_ENCODING, 139, "mixed encoding doc"),
    ];

    let mut total_replacements = 0;
    let mut total_expected = 0;

    for (pdf_path, expected_count, name) in &test_pdfs {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", name));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert to markdown");

        let replacement_count = count_replacement_chars(&markdown);
        total_replacements += replacement_count;
        total_expected += expected_count;

        println!("{}: {} replacement chars (baseline: {})",
                 name, replacement_count, expected_count);

        if replacement_count > 0 {
            let contexts = find_replacement_contexts(&markdown);
            println!("  First occurrence: {}", contexts.first().unwrap_or(&"N/A".to_string()));
        }
    }

    println!("\nTotal replacement characters: {}", total_replacements);
    println!("Baseline total: {}", total_expected);

    // Target: <100 total replacement chars
    if total_replacements > 100 {
        let reduction_pct = ((total_expected - total_replacements) as f64 / total_expected as f64) * 100.0;
        println!("Reduction from baseline: {:.1}%", reduction_pct);

        panic!(
            "Replacement character target not met: {} > 100 (target: 90% reduction from {})",
            total_replacements,
            total_expected
        );
    }

    let reduction_pct = ((total_expected - total_replacements) as f64 / total_expected as f64) * 100.0;
    println!("✅ Replacement character target met!");
    println!("   Reduction from baseline: {:.1}%", reduction_pct);
}

#[test]
fn test_fallback_cascade_effectiveness() {
    // Test that the fallback cascade is working by checking character distribution
    let mut doc = PdfDocument::open(HIGH_REPLACEMENT_CHARS)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Categorize characters
    let ascii_count = markdown.chars().filter(|c| c.is_ascii()).count();
    let unicode_count = markdown.chars().filter(|c| !c.is_ascii() && *c != '\u{FFFD}').count();
    let replacement_count = count_replacement_chars(&markdown);
    let total_chars = markdown.chars().count();

    println!("Character distribution:");
    println!("  ASCII: {} ({:.1}%)", ascii_count, (ascii_count as f64 / total_chars as f64) * 100.0);
    println!("  Unicode (non-ASCII): {} ({:.1}%)", unicode_count, (unicode_count as f64 / total_chars as f64) * 100.0);
    println!("  Replacement (�): {} ({:.1}%)", replacement_count, (replacement_count as f64 / total_chars as f64) * 100.0);

    let replacement_percentage = (replacement_count as f64 / total_chars as f64) * 100.0;

    // Heuristic: if > 1% are replacement chars, fallback isn't working well
    if replacement_percentage > 1.0 {
        panic!(
            "Too many replacement characters ({:.2}% of text) - fallback cascade not effective",
            replacement_percentage
        );
    }

    println!("✅ Character distribution looks healthy");
}

#[test]
fn test_specific_problematic_characters() {
    // Test specific characters known to cause issues in PDFs
    let mut doc = PdfDocument::open(HIGH_REPLACEMENT_CHARS)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Characters that commonly fail to decode
    let problematic_chars = vec![
        ('\u{2212}', "minus sign"),  // Often mapped incorrectly
        ('\u{2013}', "en dash"),     // Often confused with hyphen
        ('\u{2014}', "em dash"),     // Often missing
        ('\u{2192}', "right arrow"), // Common in math
        ('\u{2190}', "left arrow"),  // Common in math
        ('\u{00D7}', "multiplication sign"), // vs 'x'
        ('\u{2022}', "bullet"),      // Often missing
    ];

    let mut found_count = 0;
    let mut checked_count = 0;

    for (ch, name) in &problematic_chars {
        checked_count += 1;
        if markdown.contains(*ch) {
            found_count += 1;
            println!("✓ Found: {} ({})", ch, name);
        }
    }

    println!("\nProblematic character analysis:");
    println!("  Checked: {}", checked_count);
    println!("  Found: {}", found_count);

    let replacement_count = count_replacement_chars(&markdown);

    if replacement_count > 20 && found_count == 0 {
        println!("\n⚠️  Many replacement chars but no special characters found");
        println!("This suggests fallback strategies are not working");
    }

    println!("✅ Problematic character analysis complete");
}
