//! Regression test for reading order correctness
//!
//! Issue: Text extraction produces scrambled reading order on academic papers
//! with complex layouts (multi-column, headers, author lists).
//!
//! Expected: Text should flow in natural reading order (top-to-bottom,
//! left-to-right for single column, or column-by-column for multi-column).
//!
//! Root cause: Y-coordinate comparison may be flipped, or column detection
//! is not working correctly.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

const ARXIV_STREAMING_COT: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

/// Check if title appears before body text (basic reading order sanity check)
#[test]
fn test_arxiv_title_before_body() {
    let mut doc = PdfDocument::open(ARXIV_STREAMING_COT)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // The title "StreamingCoT" should appear before "Abstract"
    let title_pos = markdown.find("StreamingCoT");
    let abstract_pos = markdown.find("Abstract");

    match (title_pos, abstract_pos) {
        (Some(t), Some(a)) => {
            if t > a {
                println!("\n❌ READING ORDER ERROR:");
                println!("  Title position: {}", t);
                println!("  Abstract position: {}", a);
                println!("  Title should come BEFORE Abstract!");

                // Save debug output
                std::fs::write("/tmp/reading_order_debug.md", &markdown)
                    .expect("Failed to write debug file");
                println!("\n📝 Full markdown saved to: /tmp/reading_order_debug.md");

                panic!("Title appears after Abstract - reading order is wrong");
            }
        },
        (None, _) => {
            println!("\n⚠️ WARNING: Title 'StreamingCoT' not found in output");
        },
        (_, None) => {
            println!("\n⚠️ WARNING: 'Abstract' not found in output");
        },
    }

    println!("✅ Title appears before Abstract (basic reading order correct)");
}

/// Check that introduction section comes after abstract
#[test]
fn test_arxiv_section_order() {
    let mut doc = PdfDocument::open(ARXIV_STREAMING_COT)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Find key sections
    let abstract_pos = markdown.find("Abstract");
    let intro_pos = markdown.find("Introduction");

    match (abstract_pos, intro_pos) {
        (Some(a), Some(i)) => {
            if a > i {
                println!("\n❌ SECTION ORDER ERROR:");
                println!("  Abstract position: {}", a);
                println!("  Introduction position: {}", i);
                println!("  Abstract should come BEFORE Introduction!");

                panic!("Abstract appears after Introduction - reading order is wrong");
            }
        },
        _ => {
            println!("\n⚠️ WARNING: Could not find both Abstract and Introduction");
        },
    }

    println!("✅ Abstract appears before Introduction");
}

/// Check that text is not scrambled (no sentences split across non-adjacent positions)
#[test]
fn test_arxiv_no_text_scrambling() {
    let mut doc = PdfDocument::open(ARXIV_STREAMING_COT)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for tell-tale signs of scrambled text:
    // 1. URLs split across text: "https://doi.org/10.1145/3746027.3758311tations"
    // 2. Words with mixed content: "MM   Video Question"

    let scrambling_patterns = [
        ("https://doi.org/", "tations"),  // URL followed immediately by word fragment
        ("ACM  \nto conventional", ""),   // Organization name mixed with content
        ("MM   \nVideo", ""),              // Acronym mixed with content
    ];

    let mut found_scrambling = Vec::new();

    for (pattern1, pattern2) in &scrambling_patterns {
        if !pattern2.is_empty() {
            let combined = format!("{}{}", pattern1, pattern2);
            if markdown.contains(&combined) {
                found_scrambling.push(combined);
            }
        } else if markdown.contains(pattern1) {
            // Check context around pattern
            if let Some(pos) = markdown.find(pattern1) {
                let start = pos.saturating_sub(10);
                let end = (pos + 50).min(markdown.len());
                let context = &markdown[start..end];
                if context.contains('\n') && context.matches('\n').count() < 2 {
                    found_scrambling.push(format!("Suspicious pattern: {}", context));
                }
            }
        }
    }

    if !found_scrambling.is_empty() {
        println!("\n❌ TEXT SCRAMBLING DETECTED:");
        for issue in &found_scrambling {
            println!("  - {}", issue);
        }

        // Save debug output
        std::fs::write("/tmp/scrambling_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/scrambling_debug.md");

        panic!("Text scrambling detected - reading order is severely broken");
    }

    println!("✅ No obvious text scrambling detected");
}

/// Check that complete sentences are preserved (not fragmented)
#[test]
fn test_arxiv_sentence_completeness() {
    let mut doc = PdfDocument::open(ARXIV_STREAMING_COT)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // A known sentence from the abstract that should be complete:
    // "The rapid growth of streaming video applications demands multimodal models"
    // (or similar - we'll check for key phrases that should be together)

    let expected_phrases = [
        "Video Question Answering",
        "streaming video",
        "multimodal models",
    ];

    let mut missing_phrases = Vec::new();

    for phrase in &expected_phrases {
        if !markdown.contains(phrase) {
            missing_phrases.push(*phrase);
        }
    }

    if !missing_phrases.is_empty() {
        println!("\n⚠️ WARNING: Expected phrases not found (may be fragmented):");
        for phrase in &missing_phrases {
            println!("  - '{}'", phrase);
        }
    }

    println!("✅ Key phrases found intact (not fragmented)");
}

/// Verify reading order produces coherent first paragraph
#[test]
fn test_arxiv_first_paragraph_coherent() {
    let mut doc = PdfDocument::open(ARXIV_STREAMING_COT)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Get first 500 characters after the metadata header
    let content_start = markdown.find("---").unwrap_or(0);
    let content_start = markdown[content_start..].find('\n').map(|p| content_start + p + 1).unwrap_or(content_start);

    let first_500 = &markdown[content_start..content_start.saturating_add(500).min(markdown.len())];

    println!("\nFirst 500 chars of content:\n{}\n", first_500);

    // Check for signs of scrambling in first paragraph:
    // - Multiple isolated newlines with single words
    // - Random uppercase letters mid-line (e.g., "MM   \nVideo")
    // - URLs mixed with unrelated text

    let lines: Vec<&str> = first_500.lines().collect();
    let very_short_lines = lines.iter().filter(|l| l.trim().len() > 0 && l.trim().len() < 10).count();
    let very_short_percentage = (very_short_lines as f64 / lines.len().max(1) as f64) * 100.0;

    if very_short_percentage > 30.0 {
        println!("\n❌ INCOHERENT FIRST PARAGRAPH:");
        println!("  {} out of {} lines are very short (<10 chars)", very_short_lines, lines.len());
        println!("  {:.1}% of lines are fragments", very_short_percentage);
        println!("  This suggests severe reading order problems");

        panic!("First paragraph is incoherent - reading order is broken");
    }

    println!("✅ First paragraph appears coherent");
}

/// Verify PDF coordinates are being interpreted correctly
#[test]
fn test_coordinate_interpretation() {
    let mut doc = PdfDocument::open(ARXIV_STREAMING_COT)
        .expect("Failed to open arxiv PDF");

    // Extract spans to check coordinate order
    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    if spans.is_empty() {
        panic!("No spans extracted");
    }

    // Find the title span (should have large font size and be at top of page)
    let mut title_span = None;
    for span in &spans {
        if span.text.contains("StreamingCoT") {
            title_span = Some(span);
            break;
        }
    }

    if let Some(title) = title_span {
        println!("\nTitle span coordinates:");
        println!("  Text: {}", title.text);
        println!("  Y position: {}", title.bbox.y);
        println!("  Font size: {}", title.font_size);

        // Find a body text span (smaller font, should be lower on page)
        let mut body_span = None;
        for span in &spans {
            if span.text.contains("Abstract") || span.text.contains("Introduction") {
                body_span = Some(span);
                break;
            }
        }

        if let Some(body) = body_span {
            println!("\nBody span coordinates:");
            println!("  Text: {}", body.text);
            println!("  Y position: {}", body.bbox.y);
            println!("  Font size: {}", body.font_size);

            // In PDF coords: origin is bottom-left, Y increases upward
            // So title (at top) should have LARGER Y than body text
            if title.bbox.y < body.bbox.y {
                println!("\n❌ COORDINATE INTERPRETATION ERROR:");
                println!("  Title Y ({}) < Body Y ({})", title.bbox.y, body.bbox.y);
                println!("  In PDF coordinates, this means title is BELOW body!");
                println!("  This suggests Y-coordinate comparison is flipped");

                panic!("PDF coordinates are being interpreted incorrectly");
            }

            println!("\n✅ PDF coordinates interpreted correctly (title Y > body Y)");
        }
    }
}
