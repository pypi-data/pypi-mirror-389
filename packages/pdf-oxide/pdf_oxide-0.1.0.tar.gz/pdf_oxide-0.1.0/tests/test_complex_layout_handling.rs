//! Regression test for complex multi-column layout handling
//!
//! Issue: Dense multi-column layouts with 5+ authors cause column detection failure
//! Examples:
//!   - StreamingCoT: "Henan Institute of AdvancedInstitute of Automation, CAS"
//!   - Affiliations run together across columns
//!
//! Root cause: XY-Cut with fixed Gaussian smoothing (σ=2.0) over-smooths dense
//! title blocks, failing to detect column boundaries.
//!
//! Test PDFs:
//! - arxiv_2510.25332v1.pdf (StreamingCoT) - worst case, 6 authors in tight grid
//! - arxiv_2510.26480v1.pdf (Extract Method) - 5 authors, moderate complexity
//! - arxiv_2510.21165v1.pdf (Financial Networks) - 1 author, baseline (should be perfect)

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

const STREAMING_COT_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";
const EXTRACT_METHOD_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.26480v1.pdf";
const FINANCIAL_NETWORKS_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Affiliation fragments that should NOT be concatenated
const FORBIDDEN_AFFILIATION_CONCAT: &[&str] = &[
    // StreamingCoT affiliations run together
    "AdvancedInstitute",
    "TechnologyUCAS",
    "UniversityInstitute",
    "CASBeijing",
    "BeijingChina",

    // Extract Method affiliations
    "MunichGermany",
    "GroningenThe",

    // General patterns
    "UniversityUniversity",
    "InstituteInstitute",
];

/// Expected complete affiliation strings (should be preserved)
const EXPECTED_AFFILIATIONS: &[(&str, &[&str])] = &[
    (
        STREAMING_COT_PDF,
        &[
            "Henan Institute of Advanced Technology",
            "Zhengzhou University",
            "Institute of Automation",
            "CAS",
            "UCAS",
            "Beijing, China",
            "Kuaishou Technology",
        ]
    ),
    (
        EXTRACT_METHOD_PDF,
        &[
            "Technical University of Munich",
            "Munich, Germany",
            "University of Groningen",
            "Groningen, The Netherlands",
        ]
    ),
    (
        FINANCIAL_NETWORKS_PDF,
        &[
            "School of Information",
            "Xi'an University of Finance and Economics",
        ]
    ),
];

#[test]
fn test_no_affiliation_concatenation_streaming_cot() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("StreamingCoT markdown length: {} chars", markdown.len());
    println!("First 1500 chars:\n{}\n", &markdown[..1500.min(markdown.len())]);

    // Check for forbidden concatenations
    let mut found_issues = Vec::new();
    for forbidden in FORBIDDEN_AFFILIATION_CONCAT {
        if markdown.contains(forbidden) {
            found_issues.push(forbidden.to_string());
        }
    }

    if !found_issues.is_empty() {
        println!("\n❌ AFFILIATION CONCATENATION ISSUES FOUND:");
        for issue in &found_issues {
            println!("  - Found: \"{}\"", issue);
        }

        // Save for debugging
        std::fs::write("/tmp/streaming_cot_layout_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/streaming_cot_layout_debug.md");

        panic!("Affiliations are concatenated - column detection failed");
    }

    println!("✅ No affiliation concatenation in StreamingCoT");
}

#[test]
fn test_expected_affiliations_present() {
    for (pdf_path, expected_affiliations) in EXPECTED_AFFILIATIONS {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", pdf_path));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert to markdown");

        println!("\nChecking: {}", pdf_path);

        let mut missing_affiliations = Vec::new();
        for affiliation in *expected_affiliations {
            if !markdown.contains(affiliation) {
                missing_affiliations.push(*affiliation);
            } else {
                println!("  ✓ Found: \"{}\"", affiliation);
            }
        }

        if !missing_affiliations.is_empty() {
            println!("\n❌ EXPECTED AFFILIATIONS NOT FOUND:");
            for affiliation in &missing_affiliations {
                println!("  - Missing: \"{}\"", affiliation);
            }
            println!("\nThis likely means affiliations are concatenated or fragmented.");
            panic!("Expected affiliations not found in {}", pdf_path);
        }
    }

    println!("\n✅ All expected affiliations present in all test PDFs");
}

#[test]
fn test_title_block_column_detection() {
    // Test column detection specifically in title block region
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Find title block (top 20% of page)
    let page_height = spans.iter()
        .map(|s| s.bbox.y + s.bbox.height)
        .max_by(|a, b| a.partial_cmp(b).unwrap())
        .unwrap_or(0.0);

    let title_block_min_y = page_height * 0.8;
    let title_spans: Vec<_> = spans.iter()
        .filter(|s| s.bbox.y >= title_block_min_y)
        .collect();

    println!("Found {} spans in title block region", title_spans.len());

    // Analyze horizontal distribution to detect columns
    let x_positions: Vec<f32> = title_spans.iter()
        .map(|s| s.bbox.x)
        .collect();

    if x_positions.is_empty() {
        panic!("No spans found in title block region");
    }

    let min_x = x_positions.iter().cloned().fold(f32::INFINITY, f32::min);
    let max_x = x_positions.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
    let width = max_x - min_x;

    println!("Title block horizontal span: {:.1} to {:.1} (width: {:.1})",
             min_x, max_x, width);

    // Check for multi-column pattern (spans clustered at different X positions)
    let left_column = x_positions.iter().filter(|&&x| x < min_x + width * 0.4).count();
    let right_column = x_positions.iter().filter(|&&x| x > min_x + width * 0.6).count();

    println!("Left column spans: {}, Right column spans: {}", left_column, right_column);

    if left_column > 5 && right_column > 5 {
        println!("✓ Multi-column layout detected in title block");
    } else {
        println!("⚠️ Single column or unclear layout in title block");
    }

    println!("\n✅ Title block column detection analysis complete");
}

#[test]
fn test_institution_word_count_integrity() {
    // Test that institution names have correct word count (not fragmented)
    let test_cases = [
        (STREAMING_COT_PDF, "Institute of Automation", 3),
        (STREAMING_COT_PDF, "Kuaishou Technology", 2),
        (EXTRACT_METHOD_PDF, "Technical University of Munich", 4),
        (FINANCIAL_NETWORKS_PDF, "Xi'an University of Finance and Economics", 6),
    ];

    for (pdf_path, institution, expected_words) in &test_cases {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", pdf_path));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert to markdown");

        if markdown.contains(institution) {
            println!("  ✓ Found complete: \"{}\" ({} words)", institution, expected_words);
        } else {
            // Check if it's fragmented
            let words: Vec<&str> = institution.split_whitespace().collect();
            let fragments_found: Vec<&str> = words.iter()
                .filter(|w| markdown.contains(*w))
                .copied()
                .collect();

            if fragments_found.len() == words.len() && fragments_found.len() < *expected_words {
                println!("\n⚠️ INSTITUTION POSSIBLY FRAGMENTED:");
                println!("  Expected: \"{}\"", institution);
                println!("  Found fragments: {:?}", fragments_found);
                println!("  This suggests column detection split the institution name.");
            } else {
                panic!("Institution \"{}\" not found in {}", institution, pdf_path);
            }
        }
    }

    println!("\n✅ Institution name integrity check complete");
}

#[test]
fn test_vertical_alignment_in_title_block() {
    // Test that text on the same Y coordinate is kept together (not split by columns)
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Group spans by Y coordinate (within 2pt tolerance)
    use std::collections::HashMap;
    let mut y_groups: HashMap<i32, Vec<&str>> = HashMap::new();

    for span in &spans {
        let y_key = (span.bbox.y * 2.0) as i32;  // 0.5pt resolution
        y_groups.entry(y_key).or_insert_with(Vec::new).push(&span.text);
    }

    println!("Found {} distinct Y-coordinate groups", y_groups.len());

    // Check for groups that look like they should be on one line
    for (y, texts) in y_groups.iter() {
        if texts.len() > 5 {
            let combined: String = texts.join("");
            println!("  Y={:.1}: {} spans, text=\"{}...\"",
                     *y as f32 / 2.0, texts.len(), &combined[..50.min(combined.len())]);

            // Check if this line was incorrectly split by column detection
            // Pattern: "SomeInstitutionSomeOtherInstitution" suggests column split failure
            if combined.len() > 50 && !combined.contains(' ') {
                println!("    ⚠️ Long text without spaces - possible column split issue");
            }
        }
    }

    println!("\n✅ Vertical alignment analysis complete");
}

#[test]
fn test_line_length_consistency() {
    // Test that lines in title block have consistent length (not fragmented)
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Extract first 500 chars (title block region)
    let title_region = &markdown[..500.min(markdown.len())];
    let lines: Vec<&str> = title_region.lines().collect();

    println!("Analyzing first {} lines of title block", lines.len());

    let mut line_lengths: Vec<usize> = lines.iter()
        .map(|l| l.trim().len())
        .filter(|&len| len > 0)
        .collect();

    if line_lengths.is_empty() {
        panic!("No lines found in title block");
    }

    line_lengths.sort();
    let median_length = line_lengths[line_lengths.len() / 2];
    let avg_length = line_lengths.iter().sum::<usize>() / line_lengths.len();

    println!("Line length stats: avg={}, median={}", avg_length, median_length);

    // Count very short lines (< 30% of median)
    let very_short = line_lengths.iter()
        .filter(|&&len| len < median_length * 3 / 10)
        .count();

    let short_percentage = (very_short as f32 / line_lengths.len() as f32) * 100.0;

    println!("Very short lines: {} ({:.1}%)", very_short, short_percentage);

    // If > 40% of lines are very short, likely fragmentation
    if short_percentage > 40.0 {
        println!("\n❌ HIGH FRAGMENTATION DETECTED:");
        println!("  {:.1}% of lines are unusually short", short_percentage);
        println!("  This suggests column detection is fragmenting text.");
        panic!("Title block shows high fragmentation ({}%)", short_percentage as i32);
    }

    println!("✅ Line length consistency acceptable");
}

#[test]
fn test_email_integrity() {
    // Test that email addresses are not split
    let test_cases = [
        (STREAMING_COT_PDF, "yangzhenyu2022@ia.ac.cn"),
        (STREAMING_COT_PDF, "shihanwang@gs.zzu.edu.cn"),
        (EXTRACT_METHOD_PDF, "sivajeet.chand"),  // May be part of longer email
        (FINANCIAL_NETWORKS_PDF, "pengliuhep@outlook.com"),
    ];

    for (pdf_path, email_fragment) in &test_cases {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", pdf_path));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert to markdown");

        if !markdown.contains(email_fragment) {
            println!("\n❌ EMAIL FRAGMENT NOT FOUND:");
            println!("  Expected fragment: \"{}\"", email_fragment);
            println!("  In file: {}", pdf_path);

            // Check if it's split with spaces
            let with_space = email_fragment.replace("@", " @ ");
            if markdown.contains(&with_space) {
                println!("  Found with spaces: \"{}\"", with_space);
                panic!("Email address split with spaces in {}", pdf_path);
            }

            panic!("Email fragment \"{}\" not found in {}", email_fragment, pdf_path);
        } else {
            println!("  ✓ Found email fragment: \"{}\"", email_fragment);
        }
    }

    println!("\n✅ Email integrity check passed");
}

#[test]
fn test_column_gap_detection() {
    // Test that column gaps are correctly identified in projection profiles
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Build horizontal projection profile
    let page_width = spans.iter()
        .map(|s| s.bbox.x + s.bbox.width)
        .max_by(|a, b| a.partial_cmp(b).unwrap())
        .unwrap_or(0.0);

    let num_bins = 100;
    let bin_width = page_width / num_bins as f32;
    let mut profile = vec![0.0; num_bins];

    for span in &spans {
        let start_bin = ((span.bbox.x / bin_width) as usize).min(num_bins - 1);
        let end_bin = (((span.bbox.x + span.bbox.width) / bin_width) as usize).min(num_bins - 1);

        for bin in start_bin..=end_bin {
            profile[bin] += span.bbox.height;
        }
    }

    println!("Built projection profile with {} bins", num_bins);

    // Find valleys (potential column boundaries)
    let avg_density = profile.iter().sum::<f32>() / profile.len() as f32;
    let valley_threshold = avg_density * 0.1;  // 10% of average

    let mut valleys = Vec::new();
    for i in 1..profile.len()-1 {
        if profile[i] < valley_threshold &&
           profile[i] < profile[i-1] &&
           profile[i] < profile[i+1] {
            valleys.push((i, profile[i]));
        }
    }

    println!("Found {} valleys (potential column boundaries)", valleys.len());

    for (i, density) in &valleys {
        let x_pos = *i as f32 * bin_width;
        println!("  Valley at x={:.1}, density={:.2}", x_pos, density);
    }

    // For multi-column layout, expect at least 1 valley
    if valleys.len() < 1 {
        println!("\n⚠️ NO COLUMN BOUNDARIES DETECTED:");
        println!("  Expected at least 1 valley in projection profile");
        println!("  This may indicate Gaussian over-smoothing");
    } else {
        println!("✓ Column boundaries detected");
    }

    println!("\n✅ Column gap detection analysis complete");
}

#[test]
fn test_dense_layout_vs_sparse_layout() {
    // Compare handling of dense (StreamingCoT) vs sparse (Financial) layouts
    let dense_pdf = STREAMING_COT_PDF;
    let sparse_pdf = FINANCIAL_NETWORKS_PDF;

    for (pdf_path, layout_type) in &[(dense_pdf, "DENSE"), (sparse_pdf, "SPARSE")] {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", pdf_path));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert to markdown");

        // Count concatenation issues
        let concat_count = FORBIDDEN_AFFILIATION_CONCAT.iter()
            .filter(|&&pattern| markdown.contains(pattern))
            .count();

        println!("\n{} LAYOUT ({}):", layout_type, pdf_path.split('/').last().unwrap());
        println!("  Concatenation issues found: {}", concat_count);

        if *layout_type == "DENSE" && concat_count == 0 {
            println!("  ✅ Dense layout handled correctly!");
        } else if *layout_type == "SPARSE" && concat_count > 0 {
            println!("  ❌ Even sparse layout has issues - basic problem!");
            panic!("Sparse layout should not have concatenation issues");
        }
    }

    println!("\n✅ Layout density comparison complete");
}
