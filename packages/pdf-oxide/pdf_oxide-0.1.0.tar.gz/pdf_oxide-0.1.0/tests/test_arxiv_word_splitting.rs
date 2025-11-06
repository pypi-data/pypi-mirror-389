//! Regression test for word-splitting issue in academic papers
//!
//! Issue: Words like "various", "correlation", "returns" were being split
//! into "var ious", "cor relation", "retur ns" due to overly aggressive
//! word boundary detection in TJ array processing.
//!
//! Root cause: TJ array offsets representing tight kerning were being
//! interpreted as word boundaries, causing space spans to be inserted
//! mid-word.

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
fn test_arxiv_extract_spans_no_word_splitting() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    // Extract raw spans from first page
    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    println!("Extracted {} spans from page 0", spans.len());

    // Concatenate all span text
    let full_text: String = spans.iter()
        .map(|s| s.text.as_str())
        .collect();

    println!("Full text length: {} chars", full_text.len());
    println!("First 500 chars:\n{}\n", &full_text[..500.min(full_text.len())]);

    // Check for word-splitting issues
    let issues = check_for_word_splitting(&full_text);

    if !issues.is_empty() {
        println!("\n❌ WORD-SPLITTING ISSUES FOUND:");
        for issue in &issues {
            println!("  - {}", issue);
        }
        panic!("Word-splitting detected in raw spans (extract_spans)");
    }

    println!("✅ No word-splitting in extract_spans() output");
}

#[test]
fn test_arxiv_markdown_no_word_splitting() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown", markdown.len());
    println!("First 500 chars:\n{}\n", &markdown[..500.min(markdown.len())]);

    // Check for word-splitting issues
    let issues = check_for_word_splitting(&markdown);

    if !issues.is_empty() {
        println!("\n❌ WORD-SPLITTING ISSUES FOUND:");
        for issue in &issues {
            println!("  - {}", issue);
        }

        // Save problematic output for debugging
        std::fs::write("/tmp/arxiv_markdown_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/arxiv_markdown_debug.md");

        panic!("Word-splitting detected in markdown output");
    }

    println!("✅ No word-splitting in to_markdown() output");
}

#[test]
fn test_arxiv_verify_correct_words() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

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
    ];

    let mut missing_words = Vec::new();
    for word in &expected_words {
        if !markdown.to_lowercase().contains(word) {
            missing_words.push(*word);
        }
    }

    if !missing_words.is_empty() {
        println!("\n⚠️ Expected words not found:");
        for word in &missing_words {
            println!("  - {}", word);
        }
        panic!("Expected words missing from markdown (may be split)");
    }

    println!("✅ All expected words present in correct form");
}

#[test]
fn test_arxiv_span_boundaries() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Check for suspicious patterns: single letter followed by space followed by fragment
    let mut suspicious_patterns = Vec::new();

    for window in spans.windows(3) {
        let text1 = &window[0].text;
        let text2 = &window[1].text;
        let text3 = &window[2].text;

        // Pattern: short word + space + short fragment = likely split
        if text2 == " " && text1.len() <= 5 && text3.len() <= 5 {
            let combined = format!("{}{}{}", text1, text2, text3);

            // Check if this forms a known word
            for (correct, _) in SHOULD_NOT_SPLIT {
                if combined.to_lowercase().contains(&correct.to_lowercase()) {
                    suspicious_patterns.push(format!(
                        "\"{}\" + \" \" + \"{}\" = \"{}\" (should be \"{}\")",
                        text1, text3, combined, correct
                    ));
                }
            }
        }
    }

    if !suspicious_patterns.is_empty() {
        println!("\n❌ SUSPICIOUS SPAN BOUNDARIES:");
        for pattern in &suspicious_patterns {
            println!("  - {}", pattern);
        }
        panic!("Found suspicious span boundaries indicating word splits");
    }

    println!("✅ No suspicious span boundaries detected");
}

#[test]
fn test_arxiv_space_span_percentage() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let total_spans = spans.len();
    let space_spans = spans.iter().filter(|s| s.text == " ").count();
    let single_char_spans = spans.iter().filter(|s| s.text.len() == 1 && s.text != " ").count();

    let space_percentage = (space_spans as f64 / total_spans as f64) * 100.0;
    let single_char_percentage = (single_char_spans as f64 / total_spans as f64) * 100.0;

    println!("Total spans: {}", total_spans);
    println!("Space spans: {} ({:.1}%)", space_spans, space_percentage);
    println!("Single-char spans (non-space): {} ({:.1}%)", single_char_spans, single_char_percentage);

    // Heuristic: If > 20% are space spans, we're over-splitting
    if space_percentage > 20.0 {
        panic!(
            "Too many space spans ({:.1}%) - likely over-splitting words",
            space_percentage
        );
    }

    // Heuristic: If > 15% are single chars (excluding spaces), possible fragmentation
    if single_char_percentage > 15.0 {
        panic!(
            "Too many single-character spans ({:.1}%) - possible fragmentation",
            single_char_percentage
        );
    }

    println!("✅ Span distribution looks healthy");
}
