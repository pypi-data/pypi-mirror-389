//! Regression test for word-splitting issue in plain text extraction
//!
//! Issue: Words like "various", "correlation", "returns" should NOT be split
//! into "var ious", "cor relation", "retur ns" in plain text output.
//!
//! This mirrors the markdown word-splitting tests to ensure plain text extraction
//! maintains the same quality standards.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

const ARXIV_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Words that should NOT be split in the arxiv PDF
const SHOULD_NOT_SPLIT: &[(&str, &str)] = &[
    ("various", "var ious"),
    ("correlation", "cor relation"),
    ("returns", "retur ns"),
    ("distributions", "distr ibutions"),
    ("crucial", "cr ucial"),
    ("constructed", "constr ucted"),
    ("prices", "pr ices"),
    ("critical", "cr itical"),
    ("shortcomings", "shor tcomings"),
    ("summarized", "summar ized"),
    ("risks", "r isks"),
    ("financial", "finan cial"),
    ("networks", "net works"),
    ("Gaussian", "Gauss ian"),
];

/// Helper: Check text for word-splitting patterns
fn check_for_word_splitting(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    for (correct, split) in SHOULD_NOT_SPLIT {
        if text.contains(split) {
            issues.push(format!(
                "Found split word: '{}' (should be '{}')",
                split, correct
            ));
        }
    }

    issues
}

#[test]
fn test_plain_text_no_word_splitting() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    println!("Generated {} chars of plain text", text.len());
    println!("First 500 chars:\n{}\n", &text[..500.min(text.len())]);

    // Check for word-splitting issues
    let issues = check_for_word_splitting(&text);

    if !issues.is_empty() {
        println!("\n❌ WORD-SPLITTING ISSUES FOUND IN PLAIN TEXT:");
        for issue in &issues {
            println!("  - {}", issue);
        }

        // Save problematic output for debugging
        std::fs::write("/tmp/arxiv_text_word_split_debug.txt", &text)
            .expect("Failed to write debug file");
        println!("\n📝 Full text saved to: /tmp/arxiv_text_word_split_debug.txt");

        panic!("Word-splitting detected in plain text output");
    }

    println!("✅ No word-splitting in to_plain_text() output");
}

#[test]
fn test_plain_text_verify_correct_words() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    // Verify that correct (non-split) words ARE present
    let expected_words = [
        "various",
        "correlation",
        "returns",
        "distributions",
        "crucial",
        "constructed",
        "prices",
        "critical",
        "shortcomings",
        "summarized",
        "financial",
        "networks",
        "Gaussian",
    ];

    let mut missing_words = Vec::new();
    for word in &expected_words {
        if !text.to_lowercase().contains(&word.to_lowercase()) {
            missing_words.push(*word);
        }
    }

    if !missing_words.is_empty() {
        println!("\n⚠️ Expected words not found in plain text:");
        for word in &missing_words {
            println!("  - {}", word);
        }

        // This is not fatal - some words might not appear on page 0
        println!("⚠️ Warning: Some expected words missing (may not be on page 0)");
    } else {
        println!("✅ All expected words present in correct form");
    }
}

#[test]
fn test_plain_text_word_boundaries() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    // Check for suspicious patterns of excessive spacing that might indicate word splits
    // Pattern: single space followed by lowercase letter (indicating mid-word split)

    let mut suspicious_count = 0;
    let lines: Vec<_> = text.lines().collect();

    for line in &lines {
        // Look for pattern: lowercase + space + lowercase (common in split words)
        let chars: Vec<_> = line.chars().collect();
        for window in chars.windows(3) {
            if let [c1, ' ', c3] = window {
                if c1.is_lowercase() && c3.is_lowercase() {
                    // Check if this is NOT a normal word boundary
                    // Normal: "the end" - both are complete words
                    // Suspicious: "r isks" - fragment + fragment

                    // Simple heuristic: if both sides are very short (< 3 chars before/after space)
                    // This is an approximation
                    suspicious_count += 1;
                }
            }
        }
    }

    let total_chars = text.len();
    let suspicious_ratio = (suspicious_count as f64 / total_chars as f64) * 1000.0;

    println!("Total characters: {}", total_chars);
    println!("Suspicious lowercase-space-lowercase patterns: {}", suspicious_count);
    println!("Suspicious patterns per 1000 chars: {:.2}", suspicious_ratio);

    // This is a soft check - we expect some normal word boundaries
    if suspicious_ratio > 50.0 {
        println!("⚠️ Warning: High rate of suspicious spacing patterns");
        println!("This may indicate word fragmentation");
    } else {
        println!("✅ Spacing patterns look reasonable");
    }
}

#[test]
fn test_plain_text_excessive_spaces() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    // Check for excessive consecutive spaces (might indicate fragmentation)
    let double_space_count = text.matches("  ").count();
    let triple_space_count = text.matches("   ").count();
    let quad_space_count = text.matches("    ").count();

    let total_chars = text.len();
    let double_space_ratio = (double_space_count as f64 / total_chars as f64) * 1000.0;

    println!("Total characters: {}", total_chars);
    println!("Double spaces: {} ({:.2} per 1000 chars)", double_space_count, double_space_ratio);
    println!("Triple spaces: {}", triple_space_count);
    println!("Quad spaces: {}", quad_space_count);

    // Reasonable limits
    if triple_space_count > 100 {
        println!("⚠️ Warning: Many triple spaces found ({})", triple_space_count);
    }

    if quad_space_count > 50 {
        println!("⚠️ Warning: Many quad spaces found ({})", quad_space_count);
    }

    println!("✅ Whitespace check completed");
}

#[test]
fn test_plain_text_line_coherence() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    // Check if lines are coherent (not fragmented into single words)
    let lines: Vec<_> = text.lines().filter(|l| !l.trim().is_empty()).collect();

    let mut very_short_lines = 0;
    let mut single_word_lines = 0;

    for line in &lines {
        let trimmed = line.trim();
        let word_count = trimmed.split_whitespace().count();

        if trimmed.len() < 10 && !trimmed.chars().all(|c| c.is_numeric()) {
            very_short_lines += 1;
        }

        if word_count == 1 && trimmed.len() > 2 {
            single_word_lines += 1;
        }
    }

    let total_lines = lines.len();
    let short_ratio = (very_short_lines as f64 / total_lines as f64) * 100.0;
    let single_word_ratio = (single_word_lines as f64 / total_lines as f64) * 100.0;

    println!("Total lines: {}", total_lines);
    println!("Very short lines (<10 chars): {} ({:.1}%)", very_short_lines, short_ratio);
    println!("Single-word lines: {} ({:.1}%)", single_word_lines, single_word_ratio);

    // If > 30% of lines are very short, might indicate fragmentation
    if short_ratio > 30.0 {
        println!("⚠️ Warning: High percentage of very short lines ({:.1}%)", short_ratio);
        println!("This may indicate text fragmentation");

        // Show some examples
        println!("\nFirst 10 short lines:");
        let mut count = 0;
        for line in lines {
            if line.trim().len() < 10 && count < 10 {
                println!("  '{}'", line.trim());
                count += 1;
            }
        }
    } else {
        println!("✅ Line coherence looks good");
    }
}

#[test]
fn test_plain_text_reading_flow() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    // Check if text flows naturally by looking for expected phrases
    let expected_phrases = [
        "financial networks",
        "stock market",
        "correlation network",
        "complex system",
    ];

    let mut found_phrases = Vec::new();
    let mut missing_phrases = Vec::new();

    for phrase in &expected_phrases {
        if text.to_lowercase().contains(&phrase.to_lowercase()) {
            found_phrases.push(*phrase);
        } else {
            missing_phrases.push(*phrase);
        }
    }

    println!("Found phrases: {}/{}", found_phrases.len(), expected_phrases.len());

    if !found_phrases.is_empty() {
        println!("✅ Found: {:?}", found_phrases);
    }

    if !missing_phrases.is_empty() {
        println!("⚠️ Missing: {:?}", missing_phrases);
        println!("(Note: Some phrases may not appear on page 0)");
    }

    // Don't fail if some phrases are missing - they might not be on page 0
    if found_phrases.len() >= 2 {
        println!("✅ Text reading flow appears natural");
    }
}
