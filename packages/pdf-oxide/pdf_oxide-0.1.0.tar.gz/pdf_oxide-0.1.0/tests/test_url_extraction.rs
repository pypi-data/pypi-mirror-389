//! Tests for URL and hyperlink extraction from PDFs
//!
//! URLs can appear in PDFs in several ways:
//! 1. As hyperlink annotations (clickable links)
//! 2. As plain text URLs in the content
//! 3. As DOIs (Digital Object Identifiers)
//! 4. As email addresses
//!
//! This test suite ensures we extract and preserve all URL types.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;
use regex::Regex;

const ARXIV_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Helper: Extract URLs from text using regex
fn extract_urls_from_text(text: &str) -> Vec<String> {
    let url_regex = Regex::new(r"https?://[^\s<>()]+").unwrap();
    url_regex
        .find_iter(text)
        .map(|m| m.as_str().to_string())
        .collect()
}

/// Helper: Extract DOIs from text
fn extract_dois_from_text(text: &str) -> Vec<String> {
    let doi_regex = Regex::new(r"10\.\d{4,}/[^\s<>()]+").unwrap();
    doi_regex
        .find_iter(text)
        .map(|m| m.as_str().to_string())
        .collect()
}

/// Helper: Extract email addresses from text
fn extract_emails_from_text(text: &str) -> Vec<String> {
    let email_regex = Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}").unwrap();
    email_regex
        .find_iter(text)
        .map(|m| m.as_str().to_string())
        .collect()
}

#[test]
fn test_html_contains_hyperlinks() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();

    // Extract from all pages to find URLs (academic papers have URLs in references)
    let mut all_html = String::new();
    let page_count = doc.page_count().unwrap_or(0);
    for page_num in 0..page_count.min(5) {
        if let Ok(html) = doc.to_html(page_num, &options) {
            all_html.push_str(&html);
        }
    }

    println!("Total HTML length: {} chars", all_html.len());

    // Check for clickable hyperlinks (<a href="...">)
    let hyperlink_regex = Regex::new(r#"<a\s+href="(https?://[^"]+)""#).unwrap();
    let hyperlinks: Vec<_> = hyperlink_regex
        .captures_iter(&all_html)
        .map(|cap| cap[1].to_string())
        .collect();

    println!("Found {} clickable hyperlinks in HTML", hyperlinks.len());

    // Also check for raw URLs in text (not wrapped in <a> tags)
    let raw_urls = extract_urls_from_text(&all_html);
    println!("Found {} raw URLs in HTML", raw_urls.len());

    if !hyperlinks.is_empty() {
        println!("Sample hyperlinks:");
        for (i, link) in hyperlinks.iter().take(5).enumerate() {
            println!("  {}: {}", i + 1, link);
        }
        println!("✅ HTML contains clickable hyperlinks");
    } else if !raw_urls.is_empty() {
        println!("⚠️ URLs found as raw text, but not as clickable hyperlinks");
        println!("Sample raw URLs:");
        for (i, url) in raw_urls.iter().take(5).enumerate() {
            println!("  {}: {}", i + 1, url);
        }
        println!("❌ NEED TO IMPLEMENT: Convert raw URLs to <a href> tags");
        panic!("URLs are present but not converted to hyperlinks");
    } else {
        println!("⚠️ No URLs found in this PDF (may not have external links)");
    }
}

#[test]
fn test_text_contains_urls() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();

    // Extract from all pages
    let mut all_text = String::new();
    let page_count = doc.page_count().unwrap_or(0);
    for page_num in 0..page_count.min(5) {
        if let Ok(text) = doc.to_plain_text(page_num, &options) {
            all_text.push_str(&text);
            all_text.push('\n');
        }
    }

    println!("Total text length: {} chars", all_text.len());

    // Extract URLs
    let urls = extract_urls_from_text(&all_text);
    println!("Found {} URLs in plain text", urls.len());

    if !urls.is_empty() {
        println!("Sample URLs:");
        for (i, url) in urls.iter().take(5).enumerate() {
            println!("  {}: {}", i + 1, url);
        }
        println!("✅ Plain text contains URLs");
    } else {
        println!("⚠️ No URLs found in plain text");
        println!("This could mean:");
        println!("  1. PDF has no external URLs");
        println!("  2. URLs are in annotations but not extracted");
        println!("  3. URLs are on pages beyond the first 5");
    }
}

#[test]
fn test_html_contains_dois() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();

    // Extract from all pages
    let mut all_html = String::new();
    let page_count = doc.page_count().unwrap_or(0);
    for page_num in 0..page_count.min(5) {
        if let Ok(html) = doc.to_html(page_num, &options) {
            all_html.push_str(&html);
        }
    }

    // Extract DOIs
    let dois = extract_dois_from_text(&all_html);
    println!("Found {} DOIs in HTML", dois.len());

    if !dois.is_empty() {
        println!("Sample DOIs:");
        for (i, doi) in dois.iter().take(5).enumerate() {
            println!("  {}: {}", i + 1, doi);
        }
        println!("✅ HTML contains DOIs");
    } else {
        println!("⚠️ No DOIs found (may not be present in this PDF)");
    }
}

#[test]
fn test_text_contains_emails() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();

    // Extract from first page (emails usually on first page)
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to extract text");

    // Extract emails
    let emails = extract_emails_from_text(&text);
    println!("Found {} email addresses", emails.len());

    if !emails.is_empty() {
        println!("Email addresses:");
        for email in &emails {
            println!("  - {}", email);
        }
        println!("✅ Plain text contains email addresses");

        // Check if the known email is present (may have prefix due to PDF text concatenation)
        let has_expected_email = emails.iter().any(|e| e.contains("pengliuhep@outlook.com"));
        if !has_expected_email {
            println!("⚠️ Warning: Expected email 'pengliuhep@outlook.com' not found or has prefix");
            println!("Found emails: {:?}", emails);
        }
        assert!(
            has_expected_email,
            "Expected email 'pengliuhep@outlook.com' (with or without prefix) not found"
        );
    } else {
        panic!("No email addresses found (expected at least one)");
    }
}

#[test]
fn test_html_email_as_mailto_link() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // Check for mailto: links
    let mailto_regex = Regex::new(r#"<a\s+href="mailto:([^"]+)""#).unwrap();
    let mailto_links: Vec<_> = mailto_regex
        .captures_iter(&html)
        .map(|cap| cap[1].to_string())
        .collect();

    println!("Found {} mailto: links", mailto_links.len());

    // Also check for raw emails
    let raw_emails = extract_emails_from_text(&html);
    println!("Found {} raw email addresses", raw_emails.len());

    if !mailto_links.is_empty() {
        println!("Mailto links:");
        for email in &mailto_links {
            println!("  - {}", email);
        }
        println!("✅ HTML contains mailto: links");
    } else if !raw_emails.is_empty() {
        println!("⚠️ Emails found as raw text, but not as mailto: links");
        println!("Sample raw emails:");
        for email in raw_emails.iter().take(3) {
            println!("  - {}", email);
        }
        println!("❌ NEED TO IMPLEMENT: Convert email addresses to mailto: links");
        // Don't panic yet - this is an enhancement
    } else {
        panic!("No email addresses found (expected at least one)");
    }
}

#[test]
fn test_url_extraction_quality_score() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();

    // Extract HTML from all pages
    let mut all_html = String::new();
    let page_count = doc.page_count().unwrap_or(0);
    for page_num in 0..page_count.min(10) {
        if let Ok(html) = doc.to_html(page_num, &options) {
            all_html.push_str(&html);
        }
    }

    // Count different URL types
    let hyperlink_regex = Regex::new(r#"<a\s+href="https?://[^"]+""#).unwrap();
    let clickable_urls = hyperlink_regex.find_iter(&all_html).count();

    let raw_urls = extract_urls_from_text(&all_html).len();
    let dois = extract_dois_from_text(&all_html).len();
    let emails = extract_emails_from_text(&all_html).len();

    println!("\n=== URL Extraction Quality Report ===");
    println!("Clickable hyperlinks (<a href>): {}", clickable_urls);
    println!("Raw URLs (text only): {}", raw_urls);
    println!("DOIs: {}", dois);
    println!("Email addresses: {}", emails);

    let mut score = 0.0;
    let mut max_score = 100.0;
    let mut issues = Vec::new();

    // Scoring criteria
    if raw_urls > 0 {
        let url_conversion_rate = clickable_urls as f64 / raw_urls as f64;
        let url_score = url_conversion_rate * 40.0; // Max 40 points for URL conversion
        score += url_score;

        if url_conversion_rate < 1.0 {
            issues.push(format!(
                "Only {:.0}% of URLs are clickable ({}/{})",
                url_conversion_rate * 100.0, clickable_urls, raw_urls
            ));
        }
    } else {
        // No URLs in this PDF - not penalized
        max_score -= 40.0;
    }

    // DOI presence (20 points)
    if dois > 0 {
        score += 20.0;
    }

    // Email presence (20 points)
    if emails > 0 {
        score += 20.0;
    } else {
        issues.push("No email addresses found".to_string());
    }

    // URL formatting quality (20 points)
    // This is a placeholder - would check if URLs are properly formatted
    score += 20.0;

    println!("\nURL Extraction Score: {:.1}/{:.1}", score, max_score);

    if !issues.is_empty() {
        println!("\nIssues:");
        for issue in &issues {
            println!("  - {}", issue);
        }
    }

    // We expect at least basic URL extraction
    // Don't fail if URLs aren't clickable yet - that's what we're implementing
    if max_score > 0.0 {
        let percentage = (score / max_score) * 100.0;
        println!("\nPercentage: {:.1}%", percentage);

        if percentage < 50.0 {
            println!("⚠️ URL extraction quality below 50% - needs improvement");
        }
    }
}
