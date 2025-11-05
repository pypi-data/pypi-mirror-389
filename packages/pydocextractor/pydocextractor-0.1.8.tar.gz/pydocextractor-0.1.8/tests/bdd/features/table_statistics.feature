# ============================================
# Feature 4 — Table Statistics Extraction
# ============================================
Feature: Extract comprehensive statistics from tables in any document type
  As a data analyst
  I want statistical summaries computed for all tables
  So that I can quickly understand the data without manual analysis

  Background:
    Given the table profiler is enabled

  @numerical_stats
  Scenario: Calculate comprehensive numerical statistics
    Given a table with numerical column "Age" containing values [25, 30, 35, 40, 45]
    When statistics are calculated
    Then the output includes:
      | statistic | value |
      | min       | 25.00 |
      | max       | 45.00 |
      | mean      | 35.00 |
      | std       | 7.91  |
      | count     | 5     |

  @categorical_stats
  Scenario: Calculate categorical frequency distribution
    Given a table with categorical column "Occupation" containing ["Engineer", "Engineer", "Chef", "Chef", "Doctor"]
    When statistics are calculated
    Then the output includes frequency distribution with counts
    And the output includes frequency distribution with percentages
    And the mode is reported as "Engineer" or "Chef"

  @sample_output
  Scenario: Output shows maximum 5 rows sample
    Given a table with 20 rows of data
    When I convert the document to Markdown
    Then the table sample section shows exactly 5 rows
    And the statistics are calculated on all 20 rows
    And the metadata indicates total_rows: 20

  @mixed_types
  Scenario: Handle tables with both numerical and categorical columns
    Given a table with columns: Name (categorical), Age (numerical), Country (categorical), Salary (numerical)
    When statistics are calculated
    Then numerical columns (Age, Salary) show min, max, mean, std
    And categorical columns (Name, Country) show mode and frequency distribution
    And all columns are correctly classified by type

  @edge_cases
  Scenario Outline: Handle edge cases in table data
    Given a table with "<condition>"
    When statistics are calculated
    Then the output includes "<expected_behavior>"

    Examples:
      | condition                    | expected_behavior                        |
      | all unique categorical values| each value appears once in frequency    |
      | duplicate rows               | duplicate_count > 0 in metadata          |
      | missing values (NaN)         | count reflects non-null values only      |
      | single column table          | statistics calculated for that column    |
      | empty table                  | graceful handling with zero rows         |

  @data_quality
  Scenario: Report data quality metrics
    Given a table with 100 rows including 5 duplicate rows
    When I convert it to Markdown
    Then the statistics section includes "Duplicate rows: 5"
    And the metadata includes duplicate_count: 5
    And the total_rows is reported as 100

  @pdf_table_stats
  Scenario: PDF table detection and statistics integration
    Given I have "sample_document_airplane.pdf" with a 14-row table
    When I convert it to Markdown
    Then the table is detected and extracted
    And statistics are automatically calculated
    And the output shows sample of 5 rows from 14 total
    And Age statistics show min=25.00, max=45.00, mean≈32.57, std≈5.81
    And Occupation frequencies show Engineer and Chef as most common

  @docx_table_stats
  Scenario: Word document table statistics
    Given I have "Employee_List.docx" with employee data table
    When I convert it to Markdown
    Then tables are detected
    And statistics are computed for each detected table
    And the markdown output includes statistics blocks

  @all_tables_analyzed
  Scenario: All tables in document are analyzed regardless of size
    Given a PDF with tables of sizes: 2x2, 10x5, 100x3
    When I convert it to Markdown
    Then all 3 tables have statistics calculated
    And even the 2x2 table includes full statistical analysis
    And each table shows appropriate sample (up to 5 rows)

  @csv_enhanced_stats
  Scenario: CSV files include enhanced statistics
    Given I have a CSV file "data.csv" with numerical and categorical columns
    When I convert it to Markdown
    Then numerical columns include standard deviation
    And categorical columns include complete frequency distribution
    And the output shows only first 5 rows as sample
    And all statistics are computed on complete dataset

  @excel_enhanced_stats
  Scenario: Excel files include per-sheet enhanced statistics
    Given I have an Excel file "workbook.xlsx" with 2 sheets
    When I convert it to Markdown
    Then each sheet includes std deviation for numerical columns
    And each sheet includes frequency distribution for categorical columns
    And each sheet shows maximum 5 sample rows
    And metadata contains statistics for all sheets

  @frequency_distribution
  Scenario: Frequency distribution shows top 10 values
    Given a categorical column with 50 unique values
    When statistics are calculated
    Then the frequency distribution shows top 10 most frequent values
    And each value shows count and percentage
    And values are sorted by frequency (descending)

  @integration
  Scenario: End-to-end PDF with table to markdown with statistics
    Given I have "sample_document_airplane.pdf"
    When I convert it to Markdown using the default template
    Then the markdown contains the original table content
    And the markdown contains a "Table 1 Statistics" section
    And the statistics section shows sample data (5 rows)
    And the statistics section shows numerical column stats (Age)
    And the statistics section shows categorical column stats (Name, Country, Occupation, Email)
    And the statistics section shows data quality metrics
    And the document metadata includes table_statistics
