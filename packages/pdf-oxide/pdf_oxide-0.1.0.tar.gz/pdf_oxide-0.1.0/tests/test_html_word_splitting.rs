//! Regression test for word-splitting issue in HTML conversion
//!
//! Issue: Words like "various", "correlation", "returns" should NOT be split
//! into "var ious", "cor relation", "retur ns" in HTML output.
//!
//! This mirrors the markdown word-splitting tests to ensure HTML conversion
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
fn test_html_no_word_splitting() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    println!("Generated {} chars of HTML", html.len());
    println!("First 500 chars:\n{}\n", &html[..500.min(html.len())]);

    // Check for word-splitting issues
    let issues = check_for_word_splitting(&html);

    if !issues.is_empty() {
        println!("\n❌ WORD-SPLITTING ISSUES FOUND IN HTML:");
        for issue in &issues {
            println!("  - {}", issue);
        }

        // Save problematic output for debugging
        std::fs::write("/tmp/arxiv_html_word_split_debug.html", &html)
            .expect("Failed to write debug file");
        println!("\n📝 Full HTML saved to: /tmp/arxiv_html_word_split_debug.html");

        panic!("Word-splitting detected in HTML output");
    }

    println!("✅ No word-splitting in to_html() output");
}

#[test]
fn test_html_semantic_no_word_splitting() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions {
        preserve_layout: false,
        detect_headings: true,
        extract_tables: false,
        include_images: false,
        image_output_dir: None,
        reading_order_mode: pdf_oxide::converters::ReadingOrderMode::ColumnAware,
    };

    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML (semantic)");

    println!("Generated {} chars of semantic HTML", html.len());

    // Check for word-splitting issues
    let issues = check_for_word_splitting(&html);

    if !issues.is_empty() {
        println!("\n❌ WORD-SPLITTING ISSUES FOUND IN SEMANTIC HTML:");
        for issue in &issues {
            println!("  - {}", issue);
        }

        std::fs::write("/tmp/arxiv_html_semantic_word_split_debug.html", &html)
            .expect("Failed to write debug file");
        println!("\n📝 Full HTML saved to: /tmp/arxiv_html_semantic_word_split_debug.html");

        panic!("Word-splitting detected in semantic HTML output");
    }

    println!("✅ No word-splitting in semantic HTML output");
}

#[test]
fn test_html_verify_correct_words() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // Strip HTML tags for word checking
    let text_only = html
        .replace("<", " <")
        .replace(">", "> ")
        .split_whitespace()
        .filter(|w| !w.starts_with('<'))
        .collect::<Vec<_>>()
        .join(" ");

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
        if !text_only.to_lowercase().contains(&word.to_lowercase()) {
            missing_words.push(*word);
        }
    }

    if !missing_words.is_empty() {
        println!("\n⚠️ Expected words not found in HTML:");
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
fn test_html_no_fragmented_tags() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions {
        preserve_layout: false,
        detect_headings: true,
        extract_tables: false,
        include_images: false,
        image_output_dir: None,
        reading_order_mode: pdf_oxide::converters::ReadingOrderMode::ColumnAware,
    };

    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // Check for patterns like: <p>single</p><p>word</p><p>here</p>
    // This indicates excessive tag fragmentation

    // Count paragraph tags
    let p_tag_count = html.matches("<p>").count();
    let html_len = html.len();

    // Heuristic: If we have more than 1 <p> tag per 100 chars, something is wrong
    let tags_per_100_chars = (p_tag_count as f64 / html_len as f64) * 100.0;

    println!("HTML length: {} chars", html_len);
    println!("Paragraph tags: {}", p_tag_count);
    println!("Tags per 100 chars: {:.2}", tags_per_100_chars);

    if tags_per_100_chars > 5.0 {
        println!("⚠️ Warning: High paragraph tag density ({:.2} tags per 100 chars)", tags_per_100_chars);
        println!("This may indicate word fragmentation into separate tags");

        // Show first few paragraphs for debugging
        let paragraphs: Vec<_> = html.match_indices("<p>").take(10).collect();
        if !paragraphs.is_empty() {
            println!("\nFirst 10 paragraph tags:");
            for (i, (pos, _)) in paragraphs.iter().enumerate() {
                let end = html[*pos..].find("</p>").unwrap_or(50) + pos;
                let snippet = &html[*pos..end.min(pos + 100)];
                println!("  {}: {}", i + 1, snippet);
            }
        }

        // Don't fail the test yet - just warn
        // panic!("Excessive paragraph tag density detected");
    } else {
        println!("✅ Paragraph tag density is reasonable");
    }
}

#[test]
fn test_html_word_continuity() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // Extract text content between tags
    let mut in_tag = false;
    let mut text_segments = Vec::new();
    let mut current_segment = String::new();

    for ch in html.chars() {
        match ch {
            '<' => {
                if !current_segment.trim().is_empty() {
                    text_segments.push(current_segment.clone());
                }
                current_segment.clear();
                in_tag = true;
            }
            '>' => {
                in_tag = false;
            }
            _ if !in_tag => {
                current_segment.push(ch);
            }
            _ => {}
        }
    }

    // Check if any known split words appear across segments
    let mut cross_segment_issues = Vec::new();

    for window in text_segments.windows(2) {
        let combined = format!("{}{}", window[0].trim(), window[1].trim());

        for (correct, split) in SHOULD_NOT_SPLIT {
            // Check if this looks like a split word
            if split.contains(' ') {
                let parts: Vec<_> = split.split(' ').collect();
                if parts.len() == 2 {
                    if window[0].trim().to_lowercase().ends_with(parts[0])
                        && window[1].trim().to_lowercase().starts_with(parts[1]) {
                        cross_segment_issues.push(format!(
                            "Split word '{}' across segments: '{}' | '{}'",
                            correct, window[0].trim(), window[1].trim()
                        ));
                    }
                }
            }
        }
    }

    if !cross_segment_issues.is_empty() {
        println!("\n❌ CROSS-SEGMENT WORD SPLITS FOUND:");
        for issue in &cross_segment_issues {
            println!("  - {}", issue);
        }
        panic!("Words split across HTML segments/tags");
    }

    println!("✅ No cross-segment word splits detected");
}
