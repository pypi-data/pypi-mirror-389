//! Regression test for column detection
//!
//! Issue: Multi-column academic papers have text from different columns
//! mixed together, destroying reading order.
//!
//! Expected: Column detection should identify text columns and extract
//! them in proper order (left column top-to-bottom, then right column
//! top-to-bottom).
//!
//! Root cause: XY-Cut algorithm may have Gaussian smoothing disabled,
//! causing false column splits or missing real column boundaries.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

const ARXIV_TWO_COLUMN: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

/// Test that two-column text doesn't get mixed together
#[test]
fn test_two_column_not_mixed() {
    let mut doc = PdfDocument::open(ARXIV_TWO_COLUMN)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // In a properly extracted two-column paper:
    // 1. Left column should be complete before right column starts
    // 2. No interleaving of left/right content on same lines
    // 3. Column text should flow naturally

    // Check for tell-tale sign of column mixing: very short lines
    // (indicates text from one column cut off to switch to other column)
    let lines: Vec<&str> = markdown.lines().collect();
    let content_lines: Vec<&str> = lines.iter()
        .filter(|l| !l.trim().is_empty() && !l.starts_with('#') && !l.starts_with('*'))
        .copied()
        .collect();

    let very_short_lines = content_lines.iter()
        .filter(|l| l.trim().len() > 0 && l.trim().len() < 15)
        .count();

    let very_short_percentage = (very_short_lines as f64 / content_lines.len().max(1) as f64) * 100.0;

    println!("\nColumn detection analysis:");
    println!("  Content lines: {}", content_lines.len());
    println!("  Very short lines (<15 chars): {}", very_short_lines);
    println!("  Short line percentage: {:.1}%", very_short_percentage);

    // Heuristic: If > 30% of content lines are very short, columns are likely mixed
    if very_short_percentage > 30.0 {
        println!("\n❌ COLUMN MIXING DETECTED:");
        println!("  {:.1}% of lines are very short", very_short_percentage);
        println!("  This suggests text from different columns is interleaved");

        // Show examples
        println!("\nExamples of short lines (first 10):");
        for (i, line) in content_lines.iter().take(10).enumerate() {
            if line.trim().len() < 15 {
                println!("  {}: '{}'", i, line.trim());
            }
        }

        // Save debug output
        std::fs::write("/tmp/column_mixing_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/column_mixing_debug.md");

        panic!("Column mixing detected - columns are not properly separated");
    }

    println!("✅ Column separation appears correct");
}

/// Test that multi-column paper has reasonable line lengths
#[test]
fn test_line_length_consistency() {
    let mut doc = PdfDocument::open(ARXIV_TWO_COLUMN)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let lines: Vec<&str> = markdown.lines().collect();
    let content_lines: Vec<&str> = lines.iter()
        .filter(|l| !l.trim().is_empty() && !l.starts_with('#') && !l.starts_with('-'))
        .copied()
        .collect();

    // Calculate average line length
    let total_chars: usize = content_lines.iter().map(|l| l.len()).sum();
    let avg_length = if content_lines.is_empty() { 0.0 } else {
        total_chars as f64 / content_lines.len() as f64
    };

    println!("\nLine length analysis:");
    println!("  Average line length: {:.1} chars", avg_length);

    // For a two-column academic paper, lines should average 40-80 chars per column
    // If average is < 30, columns are likely being split incorrectly
    if avg_length < 30.0 {
        println!("\n❌ LINE LENGTH TOO SHORT:");
        println!("  Average {:.1} chars is suspiciously short", avg_length);
        println!("  This suggests over-aggressive column splitting");

        panic!("Line lengths too short - possible column detection issue");
    }

    println!("✅ Line lengths appear reasonable");
}

/// Test that XY-Cut is detecting columns (not failing completely)
#[test]
fn test_column_detection_working() {
    let mut doc = PdfDocument::open(ARXIV_TWO_COLUMN)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // If column detection is working, we should see:
    // 1. Text flows in reading order
    // 2. No random fragments
    // 3. Coherent paragraphs

    // Check for coherent text by looking at sentence endings
    let sentences_with_period = markdown.matches(". ").count();
    let total_chars = markdown.len();
    let sentences_per_1k = (sentences_with_period as f64 / total_chars as f64) * 1000.0;

    println!("\nText coherence analysis:");
    println!("  Sentences (ending with '. '): {}", sentences_with_period);
    println!("  Sentences per 1000 chars: {:.1}", sentences_per_1k);

    // Academic papers typically have 2-4 sentences per 1000 chars
    // If we have < 1, text is likely fragmented
    if sentences_per_1k < 1.0 {
        println!("\n❌ TEXT APPEARS FRAGMENTED:");
        println!("  Only {:.1} sentences per 1000 chars", sentences_per_1k);
        println!("  This suggests column detection is producing fragments");

        panic!("Text is too fragmented - column detection may be broken");
    }

    println!("✅ Text appears coherent (not fragmented)");
}

/// Test that column boundaries are clean (no mid-word splits)
#[test]
fn test_column_boundaries_clean() {
    let mut doc = PdfDocument::open(ARXIV_TWO_COLUMN)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let lines: Vec<&str> = markdown.lines().collect();

    // Check for lines ending with lowercase letters followed by lines starting with lowercase
    // This suggests a word was split across a column boundary
    let mut suspicious_splits = Vec::new();

    for window in lines.windows(2) {
        let line1 = window[0].trim();
        let line2 = window[1].trim();

        if line1.is_empty() || line2.is_empty() {
            continue;
        }

        let last_char = line1.chars().last();
        let first_char = line2.chars().next();

        if let (Some(last), Some(first)) = (last_char, first_char) {
            // If line ends with lowercase and next starts with lowercase (no punctuation)
            // and they're both alphabetic, likely a word split
            if last.is_lowercase() && last.is_alphabetic() &&
               first.is_lowercase() && first.is_alphabetic() {
                suspicious_splits.push(format!("'{}' → '{}'",
                    &line1[line1.len().saturating_sub(20)..],
                    &line2[..20.min(line2.len())]
                ));
            }
        }
    }

    if !suspicious_splits.is_empty() {
        println!("\n⚠️ SUSPICIOUS COLUMN SPLITS:");
        for (i, split) in suspicious_splits.iter().take(5).enumerate() {
            println!("  {}: {}", i + 1, split);
        }
        println!("  Total: {} suspicious splits", suspicious_splits.len());

        // If we have many splits, it's a real problem
        if suspicious_splits.len() > 10 {
            panic!("Too many suspicious column splits - column boundaries are not clean");
        }
    }

    println!("✅ Column boundaries appear clean");
}

/// Test that abstract is extracted coherently (most common failure point)
#[test]
fn test_abstract_coherence() {
    let mut doc = PdfDocument::open(ARXIV_TWO_COLUMN)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Find the abstract section
    if let Some(abstract_start) = markdown.find("Abstract") {
        let abstract_end = markdown[abstract_start..]
            .find("\n\n")
            .map(|p| abstract_start + p)
            .unwrap_or(abstract_start + 500);

        let abstract_text = &markdown[abstract_start..abstract_end.min(markdown.len())];

        println!("\nAbstract extracted:");
        println!("{}\n", abstract_text);

        // Abstract should be 100+ chars and have complete sentences
        if abstract_text.len() < 100 {
            println!("\n❌ ABSTRACT TOO SHORT:");
            println!("  Only {} chars", abstract_text.len());
            panic!("Abstract is too short - likely extraction failure");
        }

        // Should have at least one complete sentence (ending with period)
        if !abstract_text.contains(". ") && !abstract_text.contains(".\n") {
            println!("\n❌ ABSTRACT HAS NO COMPLETE SENTENCES:");
            println!("  No sentence-ending periods found");
            panic!("Abstract has no complete sentences - extraction is broken");
        }

        println!("✅ Abstract appears coherent");
    } else {
        println!("\n⚠️ WARNING: No abstract found");
    }
}
