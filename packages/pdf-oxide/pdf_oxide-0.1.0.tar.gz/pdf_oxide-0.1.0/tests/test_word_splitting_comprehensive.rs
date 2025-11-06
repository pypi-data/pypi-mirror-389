//! Comprehensive regression tests for word splitting issues
//!
//! CRITICAL ISSUE: Words are incorrectly split with spaces or hyphens
//! inserted in the middle, creating non-existent words.
//!
//! Examples:
//! - "Darjeeling" → "Darjeelinri, g"
//! - "India-734011" → "Ind-734011ia"
//! - "January 2024" → "Jane 2024y"
//! - "THE ADVOCATE" → "THE ADVGCATE AL"
//! - "OTHER" → "OTHE ER"
//!
//! This extends the existing test_arxiv_word_splitting.rs to cover
//! all categories of PDFs and all types of splitting issues.

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;

// Test PDFs from different categories
const NEWSPAPER_PDF: &str = "../pdf_oxide_tests/pdfs/newspapers/IA_0-contant.pdf";
const MAGAZINE_PDF: &str = "../pdf_oxide_tests/pdfs/diverse/Magazine_Scientific_American_1845.pdf";
const ARXIV_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Words that should NOT be split - correct form and incorrectly split form
const SHOULD_NOT_SPLIT: &[(&str, &[&str])] = &[
    // From newspaper
    ("Darjeeling", &["Darjeelinri, g", "Darjeelin ri", "Darje eling"]),
    ("India", &["Ind-734011ia", "In dia", "Ind ia"]),
    ("January", &["Jane 2024y", "Janu ary", "Jan uary"]),
    ("Content", &["Con: tenlume", "Con tent", "Cont ent"]),
    ("volume", &["tenlume -iv", "vol ume", "volu me"]),
    ("issue", &["issu-i", "is sue", "iss ue"]),

    // From magazine (1845)
    ("ADVOCATE", &["ADVGCATE AL", "ADV OCATE", "ADVOC ATE"]),
    ("OTHER", &["OTHE ER", "OTH ER"]),
    ("IMPROVEMENTS", &["IMPROVE MENTS", "IMPROV EMENTS"]),
    ("Particularly", &["Hlarly", "Partic ularly", "Particu larly"]),
    ("calculated", &["lculated", "calcu lated", "calcul ated"]),
    ("volume", &["volum@s", "vol ume"]),

    // From arxiv (already covered in test_arxiv_word_splitting.rs, but included for completeness)
    ("various", &["var ious", "vari ous"]),
    ("correlation", &["cor relation", "corre lation"]),
    ("returns", &["retur ns", "ret urns"]),
    ("distributions", &["distr ibutions", "distri butions"]),
    ("crucial", &["cr ucial", "cru cial"]),
    ("constructed", &["constr ucted", "const ructed"]),
    ("prices", &["pr ices", "pri ces"]),
    ("critical", &["cr itical", "criti cal"]),
    ("shortcomings", &["shor tcomings", "short comings"]),
    ("summarized", &["summar ized", "summ arized"]),
];

/// Check text for word-splitting patterns
fn check_for_word_splitting(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    for (correct, split_variants) in SHOULD_NOT_SPLIT {
        for split in *split_variants {
            if text.contains(split) {
                issues.push(format!(
                    "Found split word: '{}' (should be '{}')",
                    split, correct
                ));
            }
        }

        // Also check if the correct form is missing
        if !text.to_lowercase().contains(&correct.to_lowercase()) {
            // Only report if we found a split variant
            let found_split = split_variants.iter().any(|s| text.contains(s));
            if found_split {
                issues.push(format!(
                    "Correct word '{}' not found, but split variant exists",
                    correct
                ));
            }
        }
    }

    issues
}

/// Check for suspicious hyphenation patterns
fn check_suspicious_hyphenation(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Pattern: letter-number in middle of words
    let re = regex::Regex::new(r"\b\w+-\d+\w+\b").unwrap();
    for mat in re.find_iter(text) {
        issues.push(format!(
            "Suspicious hyphenation with number: '{}'",
            mat.as_str()
        ));
    }

    // Pattern: excessive hyphens (more than 2 in a word)
    let re = regex::Regex::new(r"\b\w+(-\w+){3,}\b").unwrap();
    for mat in re.find_iter(text) {
        issues.push(format!(
            "Excessive hyphenation: '{}'",
            mat.as_str()
        ));
    }

    issues
}

#[test]
fn test_newspaper_no_word_splitting() {
    let mut doc = PdfDocument::open(NEWSPAPER_PDF)
        .expect("Failed to open newspaper PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    println!("Extracted {} chars from {} spans", text.len(), spans.len());
    println!("Sample text: {}", &text[..300.min(text.len())]);

    let issues = check_for_word_splitting(&text);

    if !issues.is_empty() {
        println!("\n❌ WORD-SPLITTING ISSUES FOUND:");
        for issue in &issues {
            println!("  - {}", issue);
        }
        panic!("Word-splitting detected in newspaper PDF");
    }

    println!("✅ No word-splitting in newspaper PDF");
}

#[test]
fn test_magazine_no_word_splitting() {
    let mut doc = PdfDocument::open(MAGAZINE_PDF)
        .expect("Failed to open magazine PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    println!("Extracted {} chars from {} spans", text.len(), spans.len());

    let issues = check_for_word_splitting(&text);

    if !issues.is_empty() {
        println!("\n❌ WORD-SPLITTING ISSUES FOUND:");
        for issue in &issues {
            println!("  - {}", issue);
        }
        panic!("Word-splitting detected in magazine PDF");
    }

    println!("✅ No word-splitting in magazine PDF");
}

#[test]
fn test_all_categories_word_integrity() {
    // Test a sampling of PDFs from each category
    let test_pdfs = [
        ("academic", ARXIV_PDF),
        ("newspaper", NEWSPAPER_PDF),
        ("magazine", MAGAZINE_PDF),
    ];

    for (category, pdf_path) in &test_pdfs {
        println!("\nTesting {} category: {}", category, pdf_path);

        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {} PDF", category));

        let markdown = doc.to_markdown(0, &ConversionOptions::default())
            .expect(&format!("Failed to convert {} PDF", category));

        let issues = check_for_word_splitting(&markdown);

        assert!(
            issues.is_empty(),
            "Word-splitting in {} PDF: {:?}",
            category,
            issues
        );

        println!("✅ {} PDF passed", category);
    }
}

#[test]
fn test_suspicious_hyphenation_patterns() {
    let mut doc = PdfDocument::open(NEWSPAPER_PDF)
        .expect("Failed to open newspaper PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    let issues = check_suspicious_hyphenation(&markdown);

    if !issues.is_empty() {
        println!("\n⚠️ SUSPICIOUS HYPHENATION PATTERNS:");
        for issue in &issues {
            println!("  - {}", issue);
        }
        // Not a hard failure, but worth investigating
        println!("Note: These may be legitimate hyphenated compounds");
    } else {
        println!("✅ No suspicious hyphenation patterns");
    }
}

#[test]
fn test_word_split_at_span_boundaries() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Look for patterns where a word might be split across span boundaries
    let mut suspicious = Vec::new();

    for window in spans.windows(3) {
        let text1 = &window[0].text;
        let text2 = &window[1].text;
        let text3 = &window[2].text;

        // Pattern: short fragment + space + short fragment = might be split word
        if text2 == " " && text1.len() <= 4 && text3.len() <= 6 {
            let combined = format!("{}{}{}", text1, text2, text3);

            // Check if this matches any known split pattern
            for (correct, splits) in SHOULD_NOT_SPLIT {
                for split in *splits {
                    if combined.to_lowercase() == split.to_lowercase() {
                        suspicious.push(format!(
                            "Potential split: '{}' + ' ' + '{}' = '{}' (should be '{}')",
                            text1, text3, combined, correct
                        ));
                    }
                }
            }
        }
    }

    if !suspicious.is_empty() {
        println!("\n❌ SUSPICIOUS SPAN BOUNDARIES:");
        for item in &suspicious {
            println!("  - {}", item);
        }
        panic!("Found word splits at span boundaries");
    }

    println!("✅ No word splits at span boundaries");
}

#[test]
fn test_mid_word_space_spans() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Count space spans and analyze their context
    let mut mid_word_spaces = 0;

    for window in spans.windows(3) {
        let prev = &window[0].text;
        let curr = &window[1].text;
        let next = &window[2].text;

        if curr == " " {
            // Check if this looks like a mid-word space
            // Heuristic: lowercase before and after, short fragments
            let prev_lowercase = prev.chars().all(|c| c.is_lowercase() || !c.is_alphabetic());
            let next_lowercase = next.chars().next().map_or(false, |c| c.is_lowercase());

            if prev_lowercase && next_lowercase && prev.len() <= 5 && next.len() <= 6 {
                mid_word_spaces += 1;
            }
        }
    }

    let total_spaces = spans.iter().filter(|s| s.text == " ").count();
    let mid_word_ratio = mid_word_spaces as f64 / total_spaces as f64;

    println!("Mid-word spaces: {}/{} ({:.1}%)",
             mid_word_spaces, total_spaces, mid_word_ratio * 100.0);

    // Should be very few mid-word spaces
    assert!(
        mid_word_ratio < 0.10,
        "Too many mid-word spaces ({:.1}%) - indicates word splitting",
        mid_word_ratio * 100.0
    );

    println!("✅ Low mid-word space ratio");
}

#[test]
fn test_verify_complete_words_present() {
    let mut doc = PdfDocument::open(NEWSPAPER_PDF)
        .expect("Failed to open newspaper PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to convert to markdown");

    // These complete words should be present (not split)
    let expected_complete = [
        "Darjeeling",
        "India",
        "January",
        "Content",
        "volume",
        "issue",
    ];

    let mut missing = Vec::new();
    for word in &expected_complete {
        // Case-insensitive check
        if !markdown.to_lowercase().contains(&word.to_lowercase()) {
            missing.push(*word);
        }
    }

    if !missing.is_empty() {
        panic!(
            "Expected complete words not found (may be split): {:?}",
            missing
        );
    }

    println!("✅ All expected complete words present");
}

#[test]
fn test_ocr_artifacts_vs_splitting() {
    let mut doc = PdfDocument::open(MAGAZINE_PDF)
        .expect("Failed to open magazine PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    let text: String = spans.iter().map(|s| s.text.as_str()).collect();

    // Check for OCR artifacts (character substitutions) vs true splitting
    // OCR artifacts: single characters wrong (l→1, O→0, etc.)
    // Word splitting: spaces or hyphens inserted

    let ocr_artifact_count = text.matches(char::is_numeric).count();
    let split_space_count = check_for_word_splitting(&text).len();

    println!("OCR artifacts (numbers in text): {}", ocr_artifact_count);
    println!("Word splitting issues: {}", split_space_count);

    // This is an old 1845 magazine, so some OCR artifacts are expected
    // But word splitting should be minimal
    assert!(
        split_space_count < 10,
        "Too many word splitting issues ({}). Expected < 10 for OCR document.",
        split_space_count
    );

    println!("✅ Word splitting issues within acceptable range for OCR");
}
