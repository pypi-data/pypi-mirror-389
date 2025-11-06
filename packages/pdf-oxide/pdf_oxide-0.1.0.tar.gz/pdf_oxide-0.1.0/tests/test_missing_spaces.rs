//! Regression tests for missing spaces between words issue
//!
//! CRITICAL ISSUE: Academic and technical papers have words concatenated
//! without spaces, making text completely unreadable.
//!
//! Examples:
//! - "Overthepastdecades" should be "Over the past decades"
//! - "complexfinancialnetworks" should be "complex financial networks"
//! - "Suchnetworksarecrucial" should be "Such networks are crucial"
//!
//! Root cause: Character clustering algorithm not properly detecting
//! word boundaries based on inter-character spacing.
//!
//! PDF Spec Reference: ISO 32000-1:2008 Section 9.3.3 (Word Spacing)
//! and Section 9.4.3 (Text positioning operators)

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;

/// Test PDFs known to have missing space issues
const ACADEMIC_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";
const TECHNICAL_PDF: &str = "../pdf_oxide_tests/pdfs/technical/arxiv_2312.00001.pdf";
const NASA_PDF: &str = "../pdf_oxide_tests/pdfs/diverse/NASA_Apollo_11_Preliminary_Science_Report.pdf";

/// Words that should be properly separated (not concatenated)
const EXPECTED_SEPARATE_WORDS: &[&[&str]] = &[
    // From arxiv_2510.21165v1.pdf
    &["Over", "the", "past", "decades"],
    &["complex", "financial", "networks"],
    &["Such", "networks", "are", "crucial"],
    &["various", "complex", "financial"],
    &["intensive", "study", "have", "been"],
    &["Pearson", "correlation", "coefficients"],

    // From technical papers
    &["inspired", "by", "selected", "constructions"],
    &["inconsistency", "reduction", "of", "pairwise"],
    &["The", "wide", "popularity", "of", "the"],

    // From NASA document
    &["is", "chowing", "down", "on", "its"],
    &["seed", "corn", "to", "feed", "its"],
];

/// Concatenated patterns that should NOT appear
const FORBIDDEN_CONCATENATIONS: &[&str] = &[
    "Overthepastdecades",
    "complexfinancialnetworks",
    "Suchnetworksarecrucial",
    "variouscomplex",
    "intensivelystudied",
    "Pearsoncorrelation",
    "inspiredbyselected",
    "inconsistencyreduction",
    "Thewidepopularity",
    "ischowingdown",
    "seedcorntofeed",
];

/// Helper: Check if text has proper word spacing
fn check_word_spacing(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Check for forbidden concatenations
    for concat in FORBIDDEN_CONCATENATIONS {
        if text.contains(concat) {
            issues.push(format!(
                "Found concatenated words: '{}'",
                concat
            ));
        }
    }

    // Check average word length (heuristic for concatenation)
    let words: Vec<&str> = text.split_whitespace().collect();
    if !words.is_empty() {
        let avg_length: f64 = words.iter().map(|w| w.len()).sum::<usize>() as f64 / words.len() as f64;

        // Normal English: 4-6 chars average, concatenated text: 15-20+
        if avg_length > 12.0 {
            issues.push(format!(
                "Abnormally high average word length: {:.1} chars (indicates missing spaces)",
                avg_length
            ));
        }
    }

    issues
}

/// Helper: Check if words appear separated properly
fn check_words_separated(text: &str, word_groups: &[&[&str]]) -> Vec<String> {
    let mut issues = Vec::new();

    for group in word_groups {
        // Check if words appear in sequence with spaces
        let pattern = group.join(" ");
        let concatenated = group.join("");

        if text.contains(&concatenated) && !text.contains(&pattern) {
            issues.push(format!(
                "Words concatenated: '{}' (should be '{}')",
                concatenated, pattern
            ));
        }
    }

    issues
}

#[test]
fn test_academic_pdf_no_missing_spaces_spans() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    println!("Extracted {} chars from {} spans", text.len(), spans.len());
    println!("First 200 chars: {}", &text[..200.min(text.len())]);

    let spacing_issues = check_word_spacing(&text);
    let separation_issues = check_words_separated(&text, EXPECTED_SEPARATE_WORDS);

    if !spacing_issues.is_empty() || !separation_issues.is_empty() {
        println!("\n❌ MISSING SPACE ISSUES FOUND:");
        for issue in spacing_issues.iter().chain(separation_issues.iter()) {
            println!("  - {}", issue);
        }
        panic!("Missing spaces detected in extract_spans() output");
    }

    println!("✅ No missing space issues in extract_spans()");
}

#[test]
fn test_academic_pdf_no_missing_spaces_markdown() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown", markdown.len());

    let spacing_issues = check_word_spacing(&markdown);
    let separation_issues = check_words_separated(&markdown, EXPECTED_SEPARATE_WORDS);

    if !spacing_issues.is_empty() || !separation_issues.is_empty() {
        println!("\n❌ MISSING SPACE ISSUES FOUND:");
        for issue in spacing_issues.iter().chain(separation_issues.iter()) {
            println!("  - {}", issue);
        }

        std::fs::write("/tmp/missing_spaces_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/missing_spaces_debug.md");

        panic!("Missing spaces detected in to_markdown() output");
    }

    println!("✅ No missing space issues in to_markdown()");
}

#[test]
fn test_technical_pdf_no_missing_spaces() {
    let mut doc = PdfDocument::open(TECHNICAL_PDF)
        .expect("Failed to open technical PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    let issues = check_word_spacing(&text);

    assert!(
        issues.is_empty(),
        "Missing spaces in technical PDF: {:?}",
        issues
    );

    println!("✅ Technical PDF has proper word spacing");
}

#[test]
#[ignore = "NASA PDF has no spaces in content stream - different root cause, tracked separately"]
fn test_nasa_pdf_no_missing_spaces() {
    let mut doc = PdfDocument::open(NASA_PDF)
        .expect("Failed to open NASA PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    let issues = check_word_spacing(&text);

    assert!(
        issues.is_empty(),
        "Missing spaces in NASA PDF: {:?}",
        issues
    );

    println!("✅ NASA PDF has proper word spacing");
}

#[test]
fn test_space_to_character_ratio() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    let total_chars = text.len();
    let space_count = text.chars().filter(|&c| c == ' ').count();
    let space_ratio = (space_count as f64 / total_chars as f64) * 100.0;

    println!("Space-to-character ratio: {:.1}% ({}/{} chars)",
             space_ratio, space_count, total_chars);

    // English text typically has 15-20% spaces
    assert!(
        space_ratio >= 10.0,
        "Space ratio too low ({:.1}%) - indicates missing spaces. Expected 15-20%.",
        space_ratio
    );

    println!("✅ Space-to-character ratio is healthy");
}

#[test]
fn test_average_word_length() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    let words: Vec<&str> = text.split_whitespace().collect();
    let avg_length = words.iter().map(|w| w.len()).sum::<usize>() as f64 / words.len() as f64;

    println!("Average word length: {:.1} chars ({} words)",
             avg_length, words.len());

    // Normal English: 4-6 chars, concatenated text: 15-20+
    assert!(
        avg_length <= 10.0,
        "Average word length too high ({:.1} chars) - indicates concatenation. Expected 4-6 chars.",
        avg_length
    );

    println!("✅ Average word length is normal");
}

#[test]
fn test_specific_phrase_separation() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    // These phrases should appear with spaces
    // Note: Use phrases that actually appear in the PDF
    let required_phrases = [
        "network science",
        "financial networks",
        "stock market",
        "correlation coefficient",  // Note: PDF uses singular, not plural
        "statistical dependence",
    ];

    let mut missing = Vec::new();
    for phrase in &required_phrases {
        if !markdown.to_lowercase().contains(phrase) {
            missing.push(*phrase);
        }
    }

    if !missing.is_empty() {
        // Debug: print lines with "correlation" to see what's actually there
        println!("\n=== Lines containing 'correlation' ===");
        for line in markdown.lines() {
            if line.to_lowercase().contains("correlation") {
                println!("{}", line);
            }
        }
        println!("=== End debug output ===\n");

        panic!(
            "Required phrases not found (may be concatenated): {:?}",
            missing
        );
    }

    println!("✅ All required phrases properly separated");
}

#[test]
fn test_inter_character_spacing_detection() {
    let mut doc = PdfDocument::open(ACADEMIC_PDF)
        .expect("Failed to open academic PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Analyze spacing between consecutive character spans
    let mut tight_spacings = 0;
    let mut normal_spacings = 0;

    for window in spans.windows(2) {
        let span1 = &window[0];
        let span2 = &window[1];

        // Calculate horizontal gap
        let gap = span2.bbox.x - (span1.bbox.x + span1.bbox.width);

        // Typical word spacing: 0.2-0.4 × font size
        // Typical char spacing (kerning): 0-0.15 × font size
        let font_size = span1.font_size;
        let normalized_gap = gap / font_size;

        if normalized_gap > 0.15 {
            normal_spacings += 1;
        } else if normalized_gap >= 0.0 {
            tight_spacings += 1;
        }
    }

    println!("Spacing analysis: {} tight, {} normal",
             tight_spacings, normal_spacings);

    // Should have significant number of normal spacings (between words)
    let normal_ratio = normal_spacings as f64 / (tight_spacings + normal_spacings) as f64;

    assert!(
        normal_ratio >= 0.10,
        "Too few normal spacings ({:.1}%) - word boundaries not detected",
        normal_ratio * 100.0
    );

    println!("✅ Inter-character spacing detection working");
}
