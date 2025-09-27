"""
Enhanced Data Quality Validation Pipeline

This module provides comprehensive data quality validation and scoring for enterprise
legislative data, including completeness, accuracy, consistency, and timeliness assessment.
"""

import re
import json
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from models.vector_document import VectorDocument, QualityReport, ProcessingStatus
from src.audit.audit_manager import get_audit_manager, AuditContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityDimension(str, Enum):
    """Data quality dimensions"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"

class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    dimension: QualityDimension
    field: str
    issue_type: str
    description: str
    severity: ValidationSeverity
    current_value: Any
    expected_value: Any
    remediation: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of validation for a specific dimension"""
    dimension: QualityDimension
    score: float = 0.0
    max_score: float = 100.0
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue"""
        self.issues.append(issue)
        # Recalculate score based on issues
        self._calculate_score()

    def _calculate_score(self) -> None:
        """Calculate score based on issues found"""
        if not self.issues:
            self.score = self.max_score
            return

        # Weight by severity
        severity_weights = {
            ValidationSeverity.CRITICAL: 0.0,
            ValidationSeverity.HIGH: 0.25,
            ValidationSeverity.MEDIUM: 0.5,
            ValidationSeverity.LOW: 0.75,
            ValidationSeverity.INFO: 1.0
        }

        total_weight = sum(severity_weights.get(issue.severity, 1.0) for issue in self.issues)
        max_weight = len(self.issues)

        if max_weight > 0:
            self.score = (total_weight / max_weight) * self.max_score

class DataQualityValidator:
    """Comprehensive data quality validator for legislative documents"""

    def __init__(self):
        # Validation rules for different document types
        self.validation_rules = {
            'bill': {
                'required_fields': ['title', 'content', 'collection', 'doc_id'],
                'optional_but_important': ['summary', 'sponsor', 'status', 'date'],
                'field_patterns': {
                    'doc_id': r'^[A-Z]+-\d+[A-Za-z]*\d*$',  # e.g., HR1234, S567
                    'title': r'.{10,500}',  # 10-500 characters
                    'content': r'.{100,}',  # At least 100 characters
                },
                'field_lengths': {
                    'title': {'min': 10, 'max': 500},
                    'content': {'min': 100, 'max': 50000},
                    'summary': {'min': 20, 'max': 2000}
                }
            },
            'member': {
                'required_fields': ['name', 'state', 'party', 'bioguide_id'],
                'optional_but_important': ['committee_assignments', 'office_address', 'phone'],
                'field_patterns': {
                    'bioguide_id': r'^[A-Z]\d{6}$',  # e.g., A000001
                    'state': r'^[A-Z]{2}$',  # Two letter state code
                    'party': r'^(D|R|I|ID)$',  # Democratic, Republican, Independent
                }
            },
            'law': {
                'required_fields': ['title', 'content', 'law_number', 'congress'],
                'optional_but_important': ['summary', 'effective_date', 'chapter'],
                'field_patterns': {
                    'law_number': r'^Public Law \d+-\d+$',  # e.g., Public Law 117-123
                    'congress': r'^\d{3}$',  # e.g., 117
                }
            }
        }

        # Cross-field validation rules
        self.cross_field_rules = {
            'bill_consistency': [
                ('status', 'date', 'Status should have corresponding date'),
                ('sponsor', 'committee', 'Sponsored bills should have committee assignment'),
            ],
            'member_consistency': [
                ('state', 'district', 'District should correspond to state'),
                ('party', 'committee_role', 'Committee role should align with party'),
            ]
        }

    def validate_document(self, document: VectorDocument) -> QualityReport:
        """
        Perform comprehensive quality validation on a document

        Args:
            document: Document to validate

        Returns:
            QualityReport with detailed assessment
        """
        start_time = datetime.utcnow()

        # Determine document type for validation rules
        doc_type = self._determine_document_type(document)

        # Initialize dimension results
        dimension_results = {}

        # Validate each quality dimension
        dimension_results[QualityDimension.COMPLETENESS] = self._validate_completeness(document, doc_type)
        dimension_results[QualityDimension.ACCURACY] = self._validate_accuracy(document, doc_type)
        dimension_results[QualityDimension.CONSISTENCY] = self._validate_consistency(document, doc_type)
        dimension_results[QualityDimension.TIMELINESS] = self._validate_timeliness(document)
        dimension_results[QualityDimension.VALIDITY] = self._validate_validity(document, doc_type)
        dimension_results[QualityDimension.UNIQUENESS] = self._validate_uniqueness(document)

        # Calculate overall score
        overall_score = self._calculate_overall_score(dimension_results)

        # Collect all issues
        all_issues = []
        all_warnings = []
        all_suggestions = []

        for dimension_result in dimension_results.values():
            for issue in dimension_result.issues:
                if issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
                    all_issues.append(f"{issue.dimension.value}: {issue.description}")
                elif issue.severity == ValidationSeverity.MEDIUM:
                    all_warnings.append(f"{issue.dimension.value}: {issue.description}")
                else:
                    all_suggestions.append(f"{issue.dimension.value}: {issue.description}")

        # Create quality report
        report = QualityReport(
            overall_score=overall_score,
            completeness_score=dimension_results[QualityDimension.COMPLETENESS].score,
            accuracy_score=dimension_results[QualityDimension.ACCURACY].score,
            consistency_score=dimension_results[QualityDimension.CONSISTENCY].score,
            timeliness_score=dimension_results[QualityDimension.TIMELINESS].score,
            issues=all_issues,
            warnings=all_warnings,
            suggestions=all_suggestions,
            assessed_at=datetime.utcnow(),
            assessor="enterprise_validator"
        )

        # Log validation results
        self._log_validation_results(document, report)

        return report

    def _determine_document_type(self, document: VectorDocument) -> str:
        """Determine document type based on collection"""
        collection = document.collection.lower()
        if 'bill' in collection:
            return 'bill'
        elif 'member' in collection:
            return 'member'
        elif 'law' in collection or 'plaw' in collection:
            return 'law'
        else:
            return 'generic'

    def _validate_completeness(self, document: VectorDocument, doc_type: str) -> ValidationResult:
        """Validate data completeness"""
        result = ValidationResult(dimension=QualityDimension.COMPLETENESS, max_score=100.0)

        rules = self.validation_rules.get(doc_type, {})
        required_fields = rules.get('required_fields', [])
        important_fields = rules.get('optional_but_important', [])

        # Check required fields
        for field in required_fields:
            value = getattr(document, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                result.add_issue(ValidationIssue(
                    dimension=QualityDimension.COMPLETENESS,
                    field=field,
                    issue_type="missing_required",
                    description=f"Required field '{field}' is missing or empty",
                    severity=ValidationSeverity.CRITICAL,
                    current_value=value,
                    expected_value="non-empty value"
                ))

        # Check important fields
        missing_important = 0
        for field in important_fields:
            value = getattr(document, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_important += 1

        if missing_important > 0:
            result.add_issue(ValidationIssue(
                dimension=QualityDimension.COMPLETENESS,
                field="important_fields",
                issue_type="missing_important",
                description=f"{missing_important} important fields are missing",
                severity=ValidationSeverity.MEDIUM,
                current_value=f"{missing_important} missing",
                expected_value="0 missing"
            ))

        # Calculate completeness score
        total_fields = len(required_fields) + len(important_fields)
        present_fields = total_fields - missing_important
        result.score = (present_fields / total_fields) * 100 if total_fields > 0 else 100

        return result

    def _validate_accuracy(self, document: VectorDocument, doc_type: str) -> ValidationResult:
        """Validate data accuracy"""
        result = ValidationResult(dimension=QualityDimension.ACCURACY, max_score=100.0)

        rules = self.validation_rules.get(doc_type, {})
        field_patterns = rules.get('field_patterns', {})

        # Check field patterns
        for field, pattern in field_patterns.items():
            value = getattr(document, field, None)
            if value and isinstance(value, str):
                if not re.match(pattern, value):
                    result.add_issue(ValidationIssue(
                        dimension=QualityDimension.ACCURACY,
                        field=field,
                        issue_type="invalid_format",
                        description=f"Field '{field}' does not match expected pattern",
                        severity=ValidationSeverity.HIGH,
                        current_value=value,
                        expected_value=f"matches pattern: {pattern}"
                    ))

        # Check field lengths
        field_lengths = rules.get('field_lengths', {})
        for field, length_rules in field_lengths.items():
            value = getattr(document, field, None)
            if value and isinstance(value, str):
                if 'min' in length_rules and len(value) < length_rules['min']:
                    result.add_issue(ValidationIssue(
                        dimension=QualityDimension.ACCURACY,
                        field=field,
                        issue_type="too_short",
                        description=f"Field '{field}' is too short",
                        severity=ValidationSeverity.MEDIUM,
                        current_value=len(value),
                        expected_value=f"at least {length_rules['min']} characters"
                    ))

                if 'max' in length_rules and len(value) > length_rules['max']:
                    result.add_issue(ValidationIssue(
                        dimension=QualityDimension.ACCURACY,
                        field=field,
                        issue_type="too_long",
                        description=f"Field '{field}' is too long",
                        severity=ValidationSeverity.LOW,
                        current_value=len(value),
                        expected_value=f"at most {length_rules['max']} characters"
                    ))

        # Check content quality
        if document.content:
            content_issues = self._analyze_content_quality(document.content)
            for issue in content_issues:
                result.add_issue(ValidationIssue(
                    dimension=QualityDimension.ACCURACY,
                    field="content",
                    issue_type=issue['type'],
                    description=issue['description'],
                    severity=issue['severity'],
                    current_value=issue['evidence']
                ))

        # Calculate accuracy score
        if not result.issues:
            result.score = 100.0
        else:
            # Weight by severity
            severity_weights = {
                ValidationSeverity.CRITICAL: 0.0,
                ValidationSeverity.HIGH: 0.3,
                ValidationSeverity.MEDIUM: 0.6,
                ValidationSeverity.LOW: 0.8,
                ValidationSeverity.INFO: 1.0
            }

            total_weight = sum(severity_weights.get(issue.severity, 1.0) for issue in result.issues)
            result.score = (total_weight / len(result.issues)) * 100

        return result

    def _analyze_content_quality(self, content: str) -> List[Dict[str, Any]]:
        """Analyze content quality for common issues"""
        issues = []

        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', content)) / len(content)
        if special_char_ratio > 0.1:
            issues.append({
                'type': 'excessive_special_chars',
                'description': 'Content has excessive special characters',
                'severity': ValidationSeverity.MEDIUM,
                'evidence': f"{special_char_ratio".1%"} special characters"
            })

        # Check for repetitive content
        words = content.split()
        if len(words) > 100:
            unique_words = set(words)
            uniqueness_ratio = len(unique_words) / len(words)
            if uniqueness_ratio < 0.3:
                issues.append({
                    'type': 'repetitive_content',
                    'description': 'Content appears to be repetitive',
                    'severity': ValidationSeverity.LOW,
                    'evidence': f"{uniqueness_ratio".1%"} unique words"
                })

        # Check for potential encoding issues
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            issues.append({
                'type': 'encoding_issues',
                'description': 'Content has encoding issues',
                'severity': ValidationSeverity.HIGH,
                'evidence': 'Unicode encoding errors detected'
            })

        # Check for extremely short or long content
        if len(content) < 50:
            issues.append({
                'type': 'content_too_short',
                'description': 'Content is extremely short',
                'severity': ValidationSeverity.HIGH,
                'evidence': f"{len(content)} characters"
            })

        return issues

    def _validate_consistency(self, document: VectorDocument, doc_type: str) -> ValidationResult:
        """Validate data consistency"""
        result = ValidationResult(dimension=QualityDimension.CONSISTENCY, max_score=100.0)

        # Check cross-field consistency rules
        cross_field_rules = self.cross_field_rules.get(f'{doc_type}_consistency', [])
        for field1, field2, rule_description in cross_field_rules:
            value1 = getattr(document, field1, None)
            value2 = getattr(document, field2, None)

            if value1 and not value2:
                result.add_issue(ValidationIssue(
                    dimension=QualityDimension.CONSISTENCY,
                    field=f"{field1}_{field2}",
                    issue_type="missing_related_field",
                    description=rule_description,
                    severity=ValidationSeverity.MEDIUM,
                    current_value=f"{field1}={value1}, {field2}=None",
                    expected_value=f"Both {field1} and {field2} should be present"
                ))

        # Check data type consistency
        if document.collection and doc_type != self._determine_document_type(document):
            result.add_issue(ValidationIssue(
                dimension=QualityDimension.CONSISTENCY,
                field="collection_type_mismatch",
                issue_type="inconsistent_collection",
                description="Collection type doesn't match document content",
                severity=ValidationSeverity.HIGH,
                current_value=f"collection={document.collection}, inferred_type={doc_type}",
                expected_value="Collection should match document type"
            ))

        # Check date consistency
        if hasattr(document, 'created_at') and hasattr(document, 'modified_at'):
            if document.modified_at < document.created_at:
                result.add_issue(ValidationIssue(
                    dimension=QualityDimension.CONSISTENCY,
                    field="date_order",
                    issue_type="invalid_date_order",
                    description="Modified date is before created date",
                    severity=ValidationSeverity.HIGH,
                    current_value=f"modified={document.modified_at}, created={document.created_at}",
                    expected_value="Modified date should be after or equal to created date"
                ))

        # Calculate consistency score
        if not result.issues:
            result.score = 100.0
        else:
            severity_weights = {
                ValidationSeverity.CRITICAL: 0.0,
                ValidationSeverity.HIGH: 0.3,
                ValidationSeverity.MEDIUM: 0.7,
                ValidationSeverity.LOW: 0.9,
                ValidationSeverity.INFO: 1.0
            }

            total_weight = sum(severity_weights.get(issue.severity, 1.0) for issue in result.issues)
            result.score = (total_weight / len(result.issues)) * 100

        return result

    def _validate_timeliness(self, document: VectorDocument) -> ValidationResult:
        """Validate data timeliness"""
        result = ValidationResult(dimension=QualityDimension.TIMELINESS, max_score=100.0)

        now = datetime.utcnow()

        # Check if document is too old (might indicate stale data)
        if document.created_at:
            age_days = (now - document.created_at).days

            # Different age thresholds for different document types
            max_age_days = {
                'bill': 365 * 2,  # 2 years for bills
                'member': 365 * 10,  # 10 years for members
                'law': 365 * 50,  # 50 years for laws
                'generic': 365 * 5  # 5 years default
            }

            doc_type = self._determine_document_type(document)
            threshold = max_age_days.get(doc_type, 365 * 5)

            if age_days > threshold:
                result.add_issue(ValidationIssue(
                    dimension=QualityDimension.TIMELINESS,
                    field="document_age",
                    issue_type="stale_data",
                    description=f"Document is {age_days} days old, exceeding threshold of {threshold} days",
                    severity=ValidationSeverity.LOW,
                    current_value=f"{age_days} days old",
                    expected_value=f"less than {threshold} days old"
                ))

        # Check if modification date is in the future
        if document.modified_at and document.modified_at > now + timedelta(minutes=5):
            result.add_issue(ValidationIssue(
                dimension=QualityDimension.TIMELINESS,
                field="modified_date",
                issue_type="future_date",
                description="Modified date is in the future",
                severity=ValidationSeverity.HIGH,
                current_value=document.modified_at.isoformat(),
                expected_value="date not in future"
            ))

        # Calculate timeliness score
        if not result.issues:
            result.score = 100.0
        else:
            severity_weights = {
                ValidationSeverity.CRITICAL: 0.0,
                ValidationSeverity.HIGH: 0.4,
                ValidationSeverity.MEDIUM: 0.7,
                ValidationSeverity.LOW: 0.9,
                ValidationSeverity.INFO: 1.0
            }

            total_weight = sum(severity_weights.get(issue.severity, 1.0) for issue in result.issues)
            result.score = (total_weight / len(result.issues)) * 100

        return result

    def _validate_validity(self, document: VectorDocument, doc_type: str) -> ValidationResult:
        """Validate data validity and format"""
        result = ValidationResult(dimension=QualityDimension.VALIDITY, max_score=100.0)

        # Check for common data quality issues
        issues = []

        # Check for null bytes or control characters
        if document.content:
            if '\x00' in document.content:
                issues.append(ValidationIssue(
                    dimension=QualityDimension.VALIDITY,
                    field="content",
                    issue_type="null_bytes",
                    description="Content contains null bytes",
                    severity=ValidationSeverity.HIGH,
                    current_value="Contains null bytes",
                    expected_value="No null bytes"
                ))

            # Check for excessive control characters
            control_chars = len(re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', document.content))
            if control_chars > len(document.content) * 0.01:  # More than 1% control chars
                issues.append(ValidationIssue(
                    dimension=QualityDimension.VALIDITY,
                    field="content",
                    issue_type="excessive_control_chars",
                    description="Content has excessive control characters",
                    severity=ValidationSeverity.MEDIUM,
                    current_value=f"{control_chars} control characters",
                    expected_value="Less than 1% control characters"
                ))

        # Check for reasonable character distribution
        if document.content and len(document.content) > 1000:
            char_counts = {}
            for char in document.content:
                char_counts[char] = char_counts.get(char, 0) + 1

            # Check for characters that appear too frequently
            total_chars = len(document.content)
            for char, count in char_counts.items():
                if count > total_chars * 0.3 and char not in ' \n\t\r':  # More than 30% of content
                    issues.append(ValidationIssue(
                        dimension=QualityDimension.VALIDITY,
                        field="content",
                        issue_type="character_overuse",
                        description=f"Character '{char}' appears too frequently",
                        severity=ValidationSeverity.LOW,
                        current_value=f"{count} times ({count/total_chars".1%"})",
                        expected_value="No character should exceed 30% of content"
                    ))

        for issue in issues:
            result.add_issue(issue)

        # Calculate validity score
        if not result.issues:
            result.score = 100.0
        else:
            severity_weights = {
                ValidationSeverity.CRITICAL: 0.0,
                ValidationSeverity.HIGH: 0.3,
                ValidationSeverity.MEDIUM: 0.6,
                ValidationSeverity.LOW: 0.8,
                ValidationSeverity.INFO: 1.0
            }

            total_weight = sum(severity_weights.get(issue.severity, 1.0) for issue in result.issues)
            result.score = (total_weight / len(result.issues)) * 100

        return result

    def _validate_uniqueness(self, document: VectorDocument) -> ValidationResult:
        """Validate data uniqueness"""
        result = ValidationResult(dimension=QualityDimension.UNIQUENESS, max_score=100.0)

        # For now, this is a placeholder
        # In a full implementation, this would check against existing documents
        # to detect potential duplicates

        # Check for obviously duplicate content within the document itself
        if document.content and len(document.content) > 1000:
            # Simple check for repeated sections
            lines = document.content.split('\n')
            if len(lines) > 10:
                # Check for repeated lines
                line_counts = {}
                for line in lines:
                    if len(line.strip()) > 20:  # Only consider substantial lines
                        line_counts[line.strip()] = line_counts.get(line.strip(), 0) + 1

                repeated_lines = {line: count for line, count in line_counts.items() if count > 3}
                if repeated_lines:
                    result.add_issue(ValidationIssue(
                        dimension=QualityDimension.UNIQUENESS,
                        field="content",
                        issue_type="repeated_content",
                        description=f"Found {len(repeated_lines)} lines repeated more than 3 times",
                        severity=ValidationSeverity.LOW,
                        current_value=f"{len(repeated_lines)} repeated lines",
                        expected_value="No repeated content"
                    ))

        # Calculate uniqueness score
        if not result.issues:
            result.score = 100.0
        else:
            result.score = 80.0  # Some penalty for repeated content

        return result

    def _calculate_overall_score(self, dimension_results: Dict[QualityDimension, ValidationResult]) -> float:
        """Calculate overall quality score from dimension results"""
        if not dimension_results:
            return 0.0

        # Weight dimensions equally for now
        total_score = sum(result.score for result in dimension_results.values())
        return total_score / len(dimension_results)

    def _log_validation_results(self, document: VectorDocument, report: QualityReport) -> None:
        """Log validation results for monitoring"""
        try:
            # Log to audit system
            audit_manager = get_audit_manager()
            audit_manager.log_event(
                operation="QUALITY_VALIDATION",
                table_name="vector_documents",
                record_id=document.doc_id,
                category=audit_manager.AuditCategory.DATA_MODIFICATION,
                additional_metadata={
                    'overall_score': report.overall_score,
                    'completeness_score': report.completeness_score,
                    'accuracy_score': report.accuracy_score,
                    'consistency_score': report.consistency_score,
                    'timeliness_score': report.timeliness_score,
                    'issues_count': len(report.issues),
                    'warnings_count': len(report.warnings),
                    'suggestions_count': len(report.suggestions)
                }
            )

            # Log significant quality issues
            if report.overall_score < 0.7:
                logger.warning(f"Low quality document {document.doc_id}: score={report.overall_score".2f"}")

        except Exception as e:
            logger.error(f"Failed to log validation results: {e}")

    def validate_batch(self, documents: List[VectorDocument]) -> Dict[str, QualityReport]:
        """
        Validate a batch of documents

        Args:
            documents: List of documents to validate

        Returns:
            Dictionary mapping document IDs to quality reports
        """
        results = {}

        for document in documents:
            try:
                report = self.validate_document(document)
                results[document.doc_id] = report

                # Update document with quality report
                document.update_quality_score(report)

            except Exception as e:
                logger.error(f"Failed to validate document {document.doc_id}: {e}")
                # Create error report
                error_report = QualityReport(
                    overall_score=0.0,
                    completeness_score=0.0,
                    accuracy_score=0.0,
                    consistency_score=0.0,
                    timeliness_score=0.0,
                    issues=[f"Validation failed: {str(e)}"],
                    assessed_at=datetime.utcnow(),
                    assessor="error"
                )
                results[document.doc_id] = error_report

        return results

    def get_quality_statistics(self, reports: List[QualityReport]) -> Dict[str, Any]:
        """Calculate quality statistics from multiple reports"""
        if not reports:
            return {}

        scores = {
            'overall': [r.overall_score for r in reports],
            'completeness': [r.completeness_score for r in reports],
            'accuracy': [r.accuracy_score for r in reports],
            'consistency': [r.consistency_score for r in reports],
            'timeliness': [r.timeliness_score for r in reports]
        }

        stats = {}
        for metric, values in scores.items():
            if values:
                stats[metric] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }

        # Count issues by type
        total_issues = sum(len(r.issues) for r in reports)
        total_warnings = sum(len(r.warnings) for r in reports)
        total_suggestions = sum(len(r.suggestions) for r in reports)

        stats['issue_summary'] = {
            'total_issues': total_issues,
            'total_warnings': total_warnings,
            'total_suggestions': total_suggestions,
            'average_issues_per_document': total_issues / len(reports)
        }

        return stats

# Global validator instance
_data_quality_validator: Optional[DataQualityValidator] = None

def get_quality_validator() -> DataQualityValidator:
    """Get or create global quality validator instance"""
    global _data_quality_validator
    if _data_quality_validator is None:
        _data_quality_validator = DataQualityValidator()
    return _data_quality_validator

def validate_document_quality(document: VectorDocument) -> QualityReport:
    """Convenience function for document quality validation"""
    validator = get_quality_validator()
    return validator.validate_document(document)

def validate_batch_quality(documents: List[VectorDocument]) -> Dict[str, QualityReport]:
    """Convenience function for batch quality validation"""
    validator = get_quality_validator()
    return validator.validate_batch(documents)
