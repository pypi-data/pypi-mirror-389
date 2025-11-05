# ============================================
# Feature 1 — Extract PDF and Word to Markdown
# ============================================
Feature: Extract textual documents (PDF and Word) to Markdown
  As a user of the pyDocExtractor library
  I want PDF and Word documents converted to clean Markdown
  So that I can index, render, and query the content consistently

  @happy_path @pdf
  Scenario: Convert a text-based PDF to Markdown
    Given I have a PDF file "Company_Handbook.pdf" with MIME "application/pdf"
    And the PDF is text-based (not scanned) and not password-protected
    When I convert the file to Markdown
    Then the converter produces a Markdown document with preserved headings, paragraphs, lists, and links

  @happy_path @docx
  Scenario: Convert a Word document (DOCX) to Markdown
    Given I have a Word file "Q4_Strategy.docx" with MIME "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    And the document contains headings, paragraphs, bullet lists, numbered lists, and hyperlinks
    When I convert the file to Markdown
    Then the converter produces semantically-correct Markdown preserving heading levels (H1..H4)
    And lists are converted to proper Markdown bullets or numbers
    And inline links are preserved as [text](url)

  @formatting
  Scenario: Normalize whitespace and special characters
    Given a DOCX file contains smart quotes, em-dashes, non-breaking spaces, and mixed newlines
    When I convert it to Markdown
    Then the converter normalizes smart quotes to straight quotes
    And em-dashes are preserved or converted to standard dashes
    And non-breaking spaces are converted to regular spaces
    And line breaks are normalized to LF

  @error_handling
  Scenario Outline: Reject unreadable or unsupported documents
    Given I have a file "<file>" with MIME "<mime>"
    When I attempt to convert it to Markdown
    Then the converter responds with error "<error_code>"
    And the error message indicates "<reason>"

    Examples:
      | file                | mime            | error_code        | reason                       |
      | Locked.pdf          | application/pdf | PDF_LOCKED        | password-protected           |
      | Scan_ImageOnly.pdf  | application/pdf | OCR_REQUIRED      | image-only, OCR not enabled  |
      | Legacy.doc          | application/msword | UNSUPPORTED_MIME | legacy .doc not supported    |
      | BigFile.pdf         | application/pdf | SIZE_LIMIT        | exceeds max size             |
