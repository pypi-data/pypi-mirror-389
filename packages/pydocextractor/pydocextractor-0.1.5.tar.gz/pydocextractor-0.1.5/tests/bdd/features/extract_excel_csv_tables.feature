# ============================================
# Feature 2 — Extract Excel and CSV tables
# ============================================
Feature: Extract tabular files (Excel and CSV) to Markdown
  As a data consumer
  I want spreadsheets and CSVs converted to Markdown tables
  So that I can diff, render, and embed them in documentation

  @happy_path @xlsx
  Scenario: Convert a multi-sheet Excel workbook to Markdown
    Given I have an Excel file "Sales_2025.xlsx"
    When I convert it to Markdown
    Then the converter produces one Markdown section per sheet
    And each sheet is rendered as a Markdown table
    And the output includes metadata about sheets and columns

  @happy_path @csv
  Scenario: Convert a CSV file to a Markdown table
    Given I have a CSV file "customers.csv"
    When I convert it to Markdown
    Then the converter outputs a Markdown table with proper formatting
    And metadata includes row count and column count

  @dialect_detection
  Scenario: Handle CSV with different delimiter
    Given I have a CSV file "semicolons.csv"
    When I convert it to Markdown
    Then the converter auto-detects the delimiter
    And produces a correct Markdown table

  @statistics @enhanced
  Scenario: CSV conversion includes enhanced statistics
    Given I have a CSV file "customers.csv" with age (numerical) and country (categorical) columns
    When I convert it to Markdown
    Then the output includes standard deviation for numerical columns
    And the output includes frequency distribution for all categorical values
    And the frequency distribution shows count and percentage for each value
    And only the first 5 rows of data are shown as a sample

  @statistics @excel
  Scenario: Excel conversion includes per-sheet statistics
    Given I have an Excel file "Sales_2025.xlsx" with 3 sheets
    When I convert it to Markdown
    Then each sheet includes its own statistical summary
    And numerical columns show min, max, mean, std for each sheet
    And categorical columns show complete frequency distribution
    And each sheet shows maximum 5 sample rows
