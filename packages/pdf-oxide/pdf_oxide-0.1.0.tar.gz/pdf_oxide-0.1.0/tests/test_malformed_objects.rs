/// Integration tests for PDFs with malformed object headers
///
/// These tests verify that the library can handle PDFs with:
/// - Missing whitespace in object headers
/// - Unusual object header formatting
/// - Garbage characters before object definitions
///
/// Tests follow TDD approach: written before implementation to capture expected behavior.
use pdf_oxide::PdfDocument;

/// Test HNBALTFDCV5YCQB772EJLOZGFV3JQLXS.pdf - 4 pages with malformed object headers
/// Expected: Extract >95% of text (target: ~2,500 chars vs PyMuPDF's 2,681 chars)
#[test]
fn test_malformed_headers_hnbaltfdcv5y() {
    let path = "../pdf_oxide_tests/pdfs/mixed/HNBALTFDCV5YCQB772EJLOZGFV3JQLXS.pdf";

    // Test 1: Document opens successfully
    let mut doc =
        PdfDocument::open(path).expect("Should open PDF despite malformed object headers");

    // Test 2: Correctly detects 4 pages
    let page_count = doc
        .page_count()
        .expect("Should get page count despite malformed headers");
    assert_eq!(page_count, 4, "Should detect all 4 pages even with malformed headers");

    // Test 3: Extract text from all pages
    let mut total_chars = 0;
    for page_num in 0..page_count {
        let text = doc
            .extract_text(page_num)
            .expect(&format!("Should extract text from page {}", page_num));
        total_chars += text.len();
        println!("Page {}: {} chars", page_num, text.len());
    }

    // Test 4: Character count should be >95% of PyMuPDF (2,681 chars)
    // Currently extracts only 757 chars (28%), target: >2,546 chars (95%)
    assert!(
        total_chars > 2_546,
        "Should extract >2,546 chars (95% of 2,681), got {} chars",
        total_chars
    );

    println!("✓ Total extracted: {} chars (target: 2,546+)", total_chars);
}

/// Test SEVNFYZBX7VQEWEG5SQQTFZK24PCUDFU.pdf - 4 pages with malformed object headers
/// Expected: Extract >95% of text (target: ~5,843 chars vs PyMuPDF's 6,151 chars)
#[test]
fn test_malformed_headers_sevnfyzb() {
    let path = "../pdf_oxide_tests/pdfs/mixed/SEVNFYZBX7VQEWEG5SQQTFZK24PCUDFU.pdf";

    // Test 1: Document opens successfully
    let mut doc =
        PdfDocument::open(path).expect("Should open PDF despite malformed object headers");

    // Test 2: Correctly detects 4 pages
    let page_count = doc
        .page_count()
        .expect("Should get page count despite malformed headers");
    assert_eq!(page_count, 4, "Should detect all 4 pages even with malformed headers");

    // Test 3: Extract text from all pages
    let mut total_chars = 0;
    for page_num in 0..page_count {
        let text = doc
            .extract_text(page_num)
            .expect(&format!("Should extract text from page {}", page_num));
        total_chars += text.len();
        println!("Page {}: {} chars", page_num, text.len());
    }

    // Test 4: Character count should be >95% of PyMuPDF (6,151 chars)
    // Currently extracts only 1,826 chars (30%), target: >5,843 chars (95%)
    assert!(
        total_chars > 5_843,
        "Should extract >5,843 chars (95% of 6,151), got {} chars",
        total_chars
    );

    println!("✓ Total extracted: {} chars (target: 5,843+)", total_chars);
}

/// Unit test for lenient object header parsing
/// Tests various malformed header formats that should be accepted
#[cfg(test)]
mod lenient_parsing_tests {
    use super::*;

    #[test]
    #[ignore] // Will implement after main tests fail
    fn test_parse_header_missing_whitespace() {
        // Format: "1 0obj" instead of "1 0 obj"
        // Should successfully parse as object 1, generation 0
        todo!("Implement lenient parsing for missing whitespace");
    }

    #[test]
    #[ignore]
    fn test_parse_header_with_leading_garbage() {
        // Format: "  \n  1 0 obj" with leading whitespace/newlines
        // Should skip garbage and parse successfully
        todo!("Implement lenient parsing with garbage skipping");
    }

    #[test]
    #[ignore]
    fn test_parse_header_unusual_spacing() {
        // Format: "1  0   obj" with multiple spaces
        // Should normalize spacing and parse successfully
        todo!("Implement lenient parsing for unusual spacing");
    }
}
