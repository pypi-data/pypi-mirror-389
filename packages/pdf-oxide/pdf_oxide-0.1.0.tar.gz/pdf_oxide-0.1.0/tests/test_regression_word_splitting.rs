//! Regression test for word splitting issues
//!
//! Issue: 268 PDFs (75%) have word splitting problems
//! Root cause: Overly aggressive TJ array offset interpretation
//!
//! This is the BIGGEST quality issue affecting the library.
//! Words are being split mid-word due to tight kerning being
//! interpreted as word boundaries.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// Sample of PDFs with known word splitting issues
const WORD_SPLITTING_FILES: &[&str] = &[
    "../pdf_oxide_tests/pdfs/diverse/SEVNFYZBX7VQEWEG5SQQTFZK24PCUDFU.pdf",
    "../pdf_oxide_tests/pdfs/diverse/ELS4P7L7AQO4WFSJVMCLQZ4HLOQIHFZU.pdf",
    "../pdf_oxide_tests/pdfs/diverse/LCFQJGJLCOJ56B3YM3XIPRJ7DFUQPTDG.pdf",
    "../pdf_oxide_tests/pdfs/diverse/RLGNJP7L3BZWPR6KCTTN5I4DIPFSCP3L.pdf",
    "../pdf_oxide_tests/pdfs/diverse/MMSNF4WV7XLHQFKEQYKHHH7GJPPQJQ7U.pdf",
];

/// Common English words that should NOT be split
const COMMON_WORDS: &[&str] = &[
    "the", "and", "for", "that", "with", "from", "this", "have",
    "will", "your", "more", "when", "they", "about", "which", "their",
    "would", "there", "other", "these", "should", "through", "between",
    "information", "government", "development", "management", "department",
    "national", "international", "different", "important", "available",
];

/// Patterns that indicate word splitting (2-letter fragments)
fn check_for_split_patterns(text: &str) -> Vec<String> {
    let mut issues = Vec::new();

    // Pattern: short fragment + space + short fragment
    let words: Vec<&str> = text.split_whitespace().collect();

    for window in words.windows(2) {
        let word1 = window[0];
        let word2 = window[1];

        // If both are very short, might be a split word
        if word1.len() >= 2 && word1.len() <= 4 && word2.len() >= 2 && word2.len() <= 6 {
            let combined = format!("{}{}", word1, word2).to_lowercase();

            // Check if combined form is a common word
            for &common in COMMON_WORDS {
                if combined == common {
                    issues.push(format!(
                        "Split word: '{}' + '{}' = '{}' (should be '{}')",
                        word1, word2, combined, common
                    ));
                }
            }
        }
    }

    issues
}

#[test]
fn test_no_common_word_splitting() {
    let mut files_with_issues = Vec::new();
    let mut checked = 0;

    println!("\n=== Testing for Word Splitting Issues ===");

    for pdf_path in WORD_SPLITTING_FILES {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        checked += 1;
        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.to_markdown(0, &ConversionOptions::default()) {
                    Ok(markdown) => {
                        let issues = check_for_split_patterns(&markdown);

                        if !issues.is_empty() {
                            println!("  Found {} split patterns", issues.len());
                            for (i, issue) in issues.iter().take(5).enumerate() {
                                println!("    {}. {}", i + 1, issue);
                            }

                            files_with_issues.push(format!(
                                "{}: {} splits",
                                pdf_path, issues.len()
                            ));
                        } else {
                            println!("  ✓ No obvious splits detected");
                        }
                    }
                    Err(e) => {
                        println!("  ❌ Extraction error: {}", e);
                    }
                }
            }
            Err(e) => {
                println!("  ❌ Failed to open: {}", e);
            }
        }
    }

    println!("\n=== Summary ===");
    println!("Checked: {}/{} files", checked, WORD_SPLITTING_FILES.len());
    println!("Files with splits: {}", files_with_issues.len());

    if !files_with_issues.is_empty() {
        println!("\n❌ FAILURES:");
        for issue in &files_with_issues {
            println!("  • {}", issue);
        }
        panic!("Found word splitting in {} files", files_with_issues.len());
    }

    println!("✅ No word splitting detected");
}

#[test]
fn test_space_span_ratio() {
    // Check if we're generating too many space spans (indicates over-splitting)
    println!("\n=== Testing Space Span Ratio ===");

    for pdf_path in WORD_SPLITTING_FILES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(spans) = doc.extract_spans(0) {
                let total_spans = spans.len();
                let space_spans = spans.iter().filter(|s| s.text == " ").count();
                let single_char_spans = spans.iter()
                    .filter(|s| s.text.len() == 1 && s.text != " ")
                    .count();

                let space_ratio = (space_spans as f64 / total_spans as f64) * 100.0;
                let single_char_ratio = (single_char_spans as f64 / total_spans as f64) * 100.0;

                println!("  Total spans: {}", total_spans);
                println!("  Space spans: {} ({:.1}%)", space_spans, space_ratio);
                println!("  Single-char spans: {} ({:.1}%)", single_char_spans, single_char_ratio);

                // Heuristic: >20% space spans indicates over-splitting
                assert!(
                    space_ratio < 20.0,
                    "Too many space spans ({:.1}%) - likely over-splitting words",
                    space_ratio
                );

                // Heuristic: >15% single-char spans indicates fragmentation
                assert!(
                    single_char_ratio < 15.0,
                    "Too many single-character spans ({:.1}%) - possible fragmentation",
                    single_char_ratio
                );
            }
        }
    }
}

#[test]
fn test_consecutive_short_spans() {
    // Detect patterns like: "the" " " "re" (should be "there")
    println!("\n=== Testing for Suspicious Span Sequences ===");

    for pdf_path in WORD_SPLITTING_FILES.iter().take(1) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(spans) = doc.extract_spans(0) {
                let mut suspicious_sequences = 0;

                for window in spans.windows(3) {
                    let text1 = &window[0].text;
                    let text2 = &window[1].text;
                    let text3 = &window[2].text;

                    // Pattern: short + space + short
                    if text2 == " " && text1.len() <= 5 && text3.len() <= 5 {
                        let combined = format!("{}{}", text1, text3).to_lowercase();

                        // Check if it forms a common word
                        for &common in COMMON_WORDS {
                            if combined == common {
                                suspicious_sequences += 1;
                                if suspicious_sequences <= 5 {
                                    println!("  Suspicious: '{}' + ' ' + '{}' = '{}'",
                                        text1, text3, combined);
                                }
                                break;
                            }
                        }
                    }
                }

                println!("  Found {} suspicious sequences", suspicious_sequences);

                assert_eq!(
                    suspicious_sequences, 0,
                    "Found {} suspicious span sequences indicating word splits",
                    suspicious_sequences
                );
            }
        }
    }
}

#[test]
fn test_word_length_distribution() {
    // Healthy text has average word length of 4-5 chars
    // Over-split text will have lower average
    println!("\n=== Testing Word Length Distribution ===");

    for pdf_path in WORD_SPLITTING_FILES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                let words: Vec<&str> = markdown.split_whitespace().collect();
                let total_words = words.len();

                if total_words == 0 {
                    continue;
                }

                let total_chars: usize = words.iter().map(|w| w.len()).sum();
                let avg_word_length = total_chars as f64 / total_words as f64;

                let short_words = words.iter().filter(|w| w.len() <= 3).count();
                let short_ratio = (short_words as f64 / total_words as f64) * 100.0;

                println!("  Total words: {}", total_words);
                println!("  Average word length: {:.2} chars", avg_word_length);
                println!("  Short words (≤3 chars): {} ({:.1}%)", short_words, short_ratio);

                // Healthy English text: avg word length 4-5 chars
                assert!(
                    avg_word_length >= 3.5,
                    "Average word length too low ({:.2}) - indicates over-splitting",
                    avg_word_length
                );

                // Healthy English text: ~40% words are ≤3 chars (the, and, for, etc.)
                // >60% indicates excessive fragmentation
                assert!(
                    short_ratio < 60.0,
                    "Too many short words ({:.1}%) - indicates over-splitting",
                    short_ratio
                );
            }
        }
    }
}

#[test]
fn test_specific_word_patterns() {
    // Test for specific known problematic patterns
    let problem_patterns = vec![
        ("var ious", "various"),
        ("cor relation", "correlation"),
        ("retur ns", "returns"),
        ("distr ibutions", "distributions"),
        ("constr ucted", "constructed"),
        ("the re", "there"),
        ("whe re", "where"),
    ];

    println!("\n=== Testing for Specific Word Split Patterns ===");

    for pdf_path in WORD_SPLITTING_FILES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                let text_lower = markdown.to_lowercase();
                let mut found_patterns = Vec::new();

                for (split_form, correct_form) in &problem_patterns {
                    if text_lower.contains(split_form) {
                        found_patterns.push(format!("'{}' (should be '{}')", split_form, correct_form));
                    }
                }

                if !found_patterns.is_empty() {
                    println!("  Found problematic patterns:");
                    for pattern in &found_patterns {
                        println!("    - {}", pattern);
                    }

                    panic!("Found {} known word split patterns in {}",
                        found_patterns.len(), pdf_path);
                }

                println!("  ✓ No known split patterns found");
            }
        }
    }
}
