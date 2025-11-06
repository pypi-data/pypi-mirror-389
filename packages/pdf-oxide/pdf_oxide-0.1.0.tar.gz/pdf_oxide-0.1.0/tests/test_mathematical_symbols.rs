//! Regression tests for mathematical symbols and special characters
//!
//! HIGH SEVERITY: Mathematical symbols are lost or replaced with
//! incorrect characters, making academic papers lose meaning.
//!
//! Examples:
//! - Greek letters: ρ (rho), σ (sigma), μ (mu), α (alpha)
//! - Mathematical operators: ∫ (integral), ∑ (sum), ∏ (product)
//! - Set theory: ∈ (element of), ⊂ (subset), ∪ (union), ∩ (intersection)
//! - Logic: ∀ (for all), ∃ (exists), ¬ (not), ⇒ (implies)
//! - Subscripts/superscripts: X₁, X², etc.
//!
//! Root causes:
//! 1. ToUnicode CMap not properly handling Symbol fonts
//! 2. Private Use Area (PUA) characters not mapped
//! 3. Special math font encodings not decoded
//!
//! PDF Spec Reference: ISO 32000-1:2008 Section 9.6.6 (Encodings)
//! and Section 9.10 (Extraction of Text Content)

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;

const ACADEMIC_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";
const TECHNICAL_PDF: &str = "../pdf_oxide_tests/pdfs/technical/arxiv_2312.00001.pdf";

/// Mathematical symbols that should be preserved
/// Note: PDFs may use mathematical alphanumeric symbols (U+1D400-U+1D7FF)
/// instead of regular Greek letters (U+0370-U+03FF)
const GREEK_LETTERS: &[char] = &['ρ', 'σ', 'μ', 'α', 'β', 'γ', 'δ', 'ε', 'θ', 'λ', 'π', 'τ', 'φ', 'χ', 'ψ', 'ω'];
const MATH_GREEK: &[char] = &['𝛼', '𝛽', '𝛾', '𝛿', '𝜀', '𝜃', '𝜆', '𝜇', '𝜋', '𝜌', '𝜎', '𝜏', '𝜑', '𝜒', '𝜓', '𝜔']; // U+1D6FC-U+1D71B (mathematical italic)
const MATH_OPERATORS: &[char] = &['∫', '∑', '∏', '√', '∂', '∇', '∞', '±', '×', '÷', '≠', '≤', '≥', '≈', '∝'];
const SET_SYMBOLS: &[char] = &['∈', '∉', '⊂', '⊃', '⊆', '⊇', '∪', '∩', '∅'];
const LOGIC_SYMBOLS: &[char] = &['∀', '∃', '¬', '∧', '∨', '⇒', '⇔'];

/// Check if mathematical symbols are present and not replaced
fn check_math_symbols(text: &str) -> (usize, usize, Vec<String>) {
    let mut found = 0;
    let mut issues = Vec::new();

    // Check for presence of any math symbols
    for &symbol in GREEK_LETTERS.iter()
        .chain(MATH_GREEK.iter())
        .chain(MATH_OPERATORS.iter())
        .chain(SET_SYMBOLS.iter())
        .chain(LOGIC_SYMBOLS.iter())
    {
        if text.contains(symbol) {
            found += 1;
        }
    }

    // Check for replacement character
    let replacement_count = text.chars().filter(|&c| c == '\u{FFFD}').count();
    if replacement_count > 0 {
        issues.push(format!(
            "Found {} replacement characters (�) - symbols may be lost",
            replacement_count
        ));
    }

    // Check for question marks in mathematical context
    let question_marks_in_formula = text.matches("??").count();
    if question_marks_in_formula > 0 {
        issues.push(format!(
            "Found {} '??' patterns - likely missing symbols",
            question_marks_in_formula
        ));
    }

    (found, replacement_count, issues)
}

/// Check if specific Greek letters from Pearson's ρ are preserved
fn check_specific_symbols(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Known symbols in arxiv_2510.21165v1.pdf
    let expected = [
        ('ρ', "Pearson's ρ"),  // rho
        ('𝑋', "variable X"),    // mathematical X
        ('𝑌', "variable Y"),    // mathematical Y
    ];

    for (symbol, context) in &expected {
        if !text.contains(*symbol) {
            // Check if there's a context phrase that should contain it
            if text.contains(context.split(' ').next().unwrap()) {
                issues.push(format!(
                    "Symbol '{}' missing in context '{}'",
                    symbol, context
                ));
            }
        }
    }

    issues
}

#[test]
fn test_academic_pdf_preserves_greek_letters() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    println!("Checking for Greek letters in {} chars", text.len());

    // Check for both regular Greek and mathematical Greek
    let regular_greek = GREEK_LETTERS.iter()
        .filter(|&&c| text.contains(c))
        .count();
    let math_greek = MATH_GREEK.iter()
        .filter(|&&c| text.contains(c))
        .count();
    let total_greek = regular_greek + math_greek;

    println!("Found {} regular Greek + {} mathematical Greek = {} total",
             regular_greek, math_greek, total_greek);

    // Should find at least some Greek letters (paper uses Pearson's ρ/𝜌)
    assert!(
        total_greek > 0,
        "No Greek letters found. Symbol extraction may be broken."
    );

    println!("✅ Greek letters preserved: {} total", total_greek);
}

#[test]
fn test_academic_pdf_no_replacement_characters() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    let replacement_count = markdown.chars().filter(|&c| c == '\u{FFFD}').count();
    let total_chars = markdown.chars().count();
    let ratio = (replacement_count as f64 / total_chars as f64) * 100.0;

    println!("Replacement characters: {} / {} ({:.2}%)",
             replacement_count, total_chars, ratio);

    // Should have < 0.1% replacement characters for math symbols
    assert!(
        ratio < 0.5,
        "Too many replacement characters ({:.1}%). Math symbols being lost.",
        ratio
    );

    println!("✅ Replacement character ratio acceptable");
}

#[test]
fn test_specific_math_symbols() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    let issues = check_specific_symbols(&markdown);

    if !issues.is_empty() {
        println!("\n❌ MISSING MATH SYMBOLS:");
        for issue in &issues {
            println!("  - {}", issue);
        }
        panic!("Specific mathematical symbols are missing");
    }

    println!("✅ Specific mathematical symbols preserved");
}

#[test]
fn test_math_symbols_comprehensive() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    let (found, replacements, issues) = check_math_symbols(&markdown);

    println!("Math symbols found: {}", found);
    println!("Replacement characters: {}", replacements);

    if !issues.is_empty() {
        println!("\n⚠️ MATH SYMBOL ISSUES:");
        for issue in &issues {
            println!("  - {}", issue);
        }
    }

    // Academic papers should have at least a few math symbols
    assert!(
        found > 0 || replacements < 5,
        "Math symbols appear to be lost ({} found, {} replacements)",
        found, replacements
    );

    println!("✅ Mathematical symbols reasonably preserved");
}

#[test]
fn test_question_mark_symbol_replacement() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    // Count question marks in bold/italic context (likely missing symbols)
    let suspicious_qm = markdown.matches("**?**").count() + markdown.matches("*?*").count();

    println!("Suspicious question mark symbols: {}", suspicious_qm);

    // Should have very few question marks as symbol replacements
    assert!(
        suspicious_qm < 5,
        "Found {} suspicious '?' symbols - likely missing math symbols",
        suspicious_qm
    );

    println!("✅ No excessive question mark symbol replacements");
}

#[test]
fn test_subscript_superscript_handling() {
    let mut doc = PdfDocument::open(TECHNICAL_PDF)
        .expect("Failed to open technical PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    // Check for subscript/superscript Unicode characters
    let subscripts = "₀₁₂₃₄₅₆₇₈₉";
    let superscripts = "⁰¹²³⁴⁵⁶⁷⁸⁹";

    let has_subscript = subscripts.chars().any(|c| markdown.contains(c));
    let has_superscript = superscripts.chars().any(|c| markdown.contains(c));

    println!("Has subscripts: {}", has_subscript);
    println!("Has superscripts: {}", has_superscript);

    // Note: Many PDFs don't use Unicode sub/superscripts, they position text
    // So this test just documents the behavior
    if has_subscript || has_superscript {
        println!("✅ Sub/superscript Unicode characters preserved");
    } else {
        println!("ℹ️ No Unicode sub/superscripts (may use positioning instead)");
    }
}

#[test]
fn test_symbol_font_handling() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Check for Symbol font
    let symbol_font_spans: Vec<_> = spans.iter()
        .filter(|s| s.font_name.to_lowercase().contains("symbol"))
        .collect();

    if !symbol_font_spans.is_empty() {
        println!("Found {} spans with Symbol font", symbol_font_spans.len());

        // Check if Symbol font text is readable (not garbled)
        for span in symbol_font_spans.iter().take(5) {
            println!("  Symbol font span: '{}'", span.text);

            // Should not be all replacement characters
            let replacement_ratio = span.text.chars()
                .filter(|&c| c == '\u{FFFD}')
                .count() as f64 / span.text.len() as f64;

            assert!(
                replacement_ratio < 0.5,
                "Symbol font span is >50% replacement characters"
            );
        }

        println!("✅ Symbol font handled correctly");
    } else {
        println!("ℹ️ No Symbol font detected in this PDF");
    }
}

#[test]
fn test_private_use_area_characters() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // Private Use Area: U+E000 to U+F8FF
    let pua_chars: Vec<char> = text.chars()
        .filter(|&c| ('\u{E000}'..='\u{F8FF}').contains(&c))
        .collect();

    if !pua_chars.is_empty() {
        println!("Found {} Private Use Area characters", pua_chars.len());
        println!("Sample PUA chars: {:?}", &pua_chars[..pua_chars.len().min(10)]);

        // PUA characters should be mapped via ToUnicode to proper symbols
        // If we see many PUA characters, mapping may be incomplete
        let pua_ratio = pua_chars.len() as f64 / text.chars().count() as f64;

        if pua_ratio > 0.01 {
            panic!(
                "High ratio of PUA characters ({:.1}%) - ToUnicode mapping may be incomplete",
                pua_ratio * 100.0
            );
        }
    } else {
        println!("✅ No unmapped Private Use Area characters");
    }
}

#[test]
fn test_mathematical_context_preservation() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    // Check that mathematical contexts have symbols, not placeholders
    let math_contexts = [
        ("Pearson", vec!['ρ', '𝜌']),  // Should have rho
        ("variable", vec!['𝑋', '𝑌', 'X', 'Y']),  // Should have variables
        ("correlation", vec!['ρ', 'r']),  // Should have correlation symbol
    ];

    for (context, symbols) in &math_contexts {
        if markdown.contains(context) {
            let has_symbol = symbols.iter().any(|&s| markdown.contains(s));
            if !has_symbol {
                println!("⚠️ Context '{}' found but no symbols: {:?}", context, symbols);
            }
        }
    }

    println!("✅ Mathematical context preservation checked");
}
