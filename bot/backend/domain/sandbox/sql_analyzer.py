"""
SQL Analyzer - Detects SQL injection and analyzes query patterns
"""
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class SQLInjectionPattern:
    """Represents a potential SQL injection pattern"""
    pattern: str
    regex: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    example_dangerous: str


class SQLAnalyzer:
    """Analyzes SQL queries for injection patterns and safety issues"""

    # SQL Injection patterns to detect
    INJECTION_PATTERNS = [
        SQLInjectionPattern(
            pattern="UNION SELECT",
            regex=r"\bUNION\s+SELECT\b",
            severity="CRITICAL",
            description="UNION-based SQL injection attempt",
            example_dangerous="' UNION SELECT * FROM users--"
        ),
        SQLInjectionPattern(
            pattern="UNION based injection",
            regex=r"\bUNION\s+(SELECT|UPDATE|DELETE|INSERT)\b",
            severity="CRITICAL",
            description="UNION with other SQL statements",
            example_dangerous="' UNION UPDATE users SET--"
        ),
        SQLInjectionPattern(
            pattern="Stacked queries",
            regex=r";\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)\b",
            severity="CRITICAL",
            description="Multiple SQL statements separated by semicolon",
            example_dangerous="'; DROP TABLE users;--"
        ),
        SQLInjectionPattern(
            pattern="Dynamic SQL execution",
            regex=r"\b(EXEC|EXECUTE)\s*\(",
            severity="CRITICAL",
            description="Dynamic SQL execution",
            example_dangerous="EXEC('SELECT * FROM' + @table)"
        ),
        SQLInjectionPattern(
            pattern="Dynamic query",
            regex=r"\bEXECUTE\s+(IMMEDIATE|STATEMENT)\b",
            severity="CRITICAL",
            description="Execute immediate statement",
            example_dangerous="EXECUTE IMMEDIATE 'DROP TABLE users'"
        ),
        SQLInjectionPattern(
            pattern="DROP statement",
            regex=r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW|INDEX)\b",
            severity="CRITICAL",
            description="DROP statement that could destroy data",
            example_dangerous="' OR '1'='1'; DROP TABLE users;--"
        ),
        SQLInjectionPattern(
            pattern="DELETE statement",
            regex=r"\bDELETE\s+FROM\b",
            severity="HIGH",
            description="DELETE statement without WHERE",
            example_dangerous="DELETE FROM users"
        ),
        SQLInjectionPattern(
            pattern="INSERT statement",
            regex=r"\bINSERT\s+INTO\b",
            severity="MEDIUM",
            description="INSERT statement",
            example_dangerous="INSERT INTO logs VALUES(...)"
        ),
        SQLInjectionPattern(
            pattern="Subquery injection",
            regex=r"\(\s*SELECT\s+.*FROM\s",
            severity="HIGH",
            description="Nested SELECT queries",
            example_dangerous="(SELECT * FROM (SELECT * FROM users))"
        ),
        SQLInjectionPattern(
            pattern="Comment injection",
            regex=r"(--|#|/\*)",
            severity="MEDIUM",
            description="SQL comments (could hide malicious code)",
            example_dangerous="' OR '1'='1'--"
        ),
        SQLInjectionPattern(
            pattern="String escaping bypass",
            regex=r"('')|(\\\\)|('')",
            severity="MEDIUM",
            description="Attempts to escape string delimiters",
            example_dangerous="' OR 1=1 --"
        ),
    ]

    # Sensitive columns that shouldn't be exposed
    SENSITIVE_COLUMNS = [
        "password",
        "passwd",
        "pwd",
        "pass",
        "secret",
        "private_key",
        "api_key",
        "token",
        "ssn",
        "social_security",
        "credit_card",
        "card_number",
        "cvv",
        "cc_number",
        "salary",
        "wage",
        "income",
        "email",
        "phone",
        "mobile",
        "cell_phone",
        "home_phone",
        "personal_email",
        "maiden_name",
        "security_question",
        "pin",
        "oauth_token",
        "jwt_token",
        "access_token",
        "refresh_token",
    ]

    # SQL keywords that indicate complex operations
    COMPLEX_KEYWORDS = [
        "RECURSIVE",
        "WITH",
        "CTE",
        "WINDOW",
        "PARTITION",
        "OVER",
    ]

    def __init__(self):
        """Initialize SQL analyzer"""
        self.compile_patterns()

    def compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        self.compiled_patterns = []
        for pattern in self.INJECTION_PATTERNS:
            try:
                compiled = re.compile(pattern.regex, re.IGNORECASE | re.MULTILINE)
                self.compiled_patterns.append((pattern, compiled))
            except re.error as e:
                # Skip invalid patterns
                pass

    def analyze(self, sql_query: str) -> Dict[str, Any]:
        """
        Analyze SQL query for safety issues
        
        Returns:
        {
            'syntax_valid': bool,
            'sql_injection_safe': bool,
            'injection_patterns_found': List[str],
            'sensitive_columns_found': List[str],
            'is_select_only': bool,
            'complexity_level': 'simple'|'moderate'|'complex',
            'table_count': int,
            'join_count': int,
            'warnings': List[str],
            'errors': List[str],
        }
        """
        if not sql_query or not sql_query.strip():
            return {
                'syntax_valid': False,
                'sql_injection_safe': False,
                'injection_patterns_found': [],
                'sensitive_columns_found': [],
                'is_select_only': False,
                'complexity_level': 'simple',
                'table_count': 0,
                'join_count': 0,
                'warnings': ['Empty query'],
                'errors': ['No SQL query provided'],
            }

        # Clean query
        query = sql_query.strip()

        # Check for injection patterns
        injection_patterns = self._detect_injection_patterns(query)
        is_injection_safe = len(injection_patterns) == 0

        # Check for sensitive columns
        sensitive_cols = self._detect_sensitive_columns(query)

        # Analyze query structure
        is_select_only = self._is_select_only(query)
        table_count = self._count_tables(query)
        join_count = self._count_joins(query)
        complexity = self._assess_complexity(query)

        # Generate warnings
        warnings = self._generate_warnings(query, is_select_only, sensitive_cols, join_count)

        return {
            'syntax_valid': True,  # TODO: Implement actual syntax validation
            'sql_injection_safe': is_injection_safe,
            'injection_patterns_found': injection_patterns,
            'sensitive_columns_found': sensitive_cols,
            'is_select_only': is_select_only,
            'complexity_level': complexity,
            'table_count': table_count,
            'join_count': join_count,
            'warnings': warnings,
            'errors': [],
        }

    def _detect_injection_patterns(self, query: str) -> List[str]:
        """Detect SQL injection patterns"""
        found_patterns = []

        for pattern, compiled_regex in self.compiled_patterns:
            if compiled_regex.search(query):
                found_patterns.append(pattern.pattern)

        return found_patterns

    def _detect_sensitive_columns(self, query: str) -> List[str]:
        """Detect if query exposes sensitive columns"""
        found_columns = []

        # Check for SELECT *
        if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
            # SELECT * is suspicious, could expose sensitive columns
            found_columns.append("SELECT * (could expose sensitive data)")
            return found_columns

        # Check for specific sensitive column names
        upper_query = query.upper()
        for col in self.SENSITIVE_COLUMNS:
            # Look for column name in SELECT clause
            pattern = rf"SELECT\s+.*\b{re.escape(col)}\b"
            if re.search(pattern, upper_query, re.IGNORECASE):
                found_columns.append(col)

        return found_columns

    def _is_select_only(self, query: str) -> bool:
        """Check if query is SELECT only (read-only)"""
        upper_query = query.strip().upper()
        
        # Check for write operations
        write_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
        
        for keyword in write_keywords:
            if re.search(rf"\b{keyword}\b", upper_query):
                return False

        # Check if it starts with SELECT or WITH (CTE)
        if upper_query.startswith("SELECT") or upper_query.startswith("WITH"):
            return True

        return False

    def _count_tables(self, query: str) -> int:
        """Estimate number of tables accessed"""
        # Look for FROM and JOIN clauses
        from_pattern = r"\bFROM\s+[\w\.\[\]`\"']+"
        join_pattern = r"\b(INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+|CROSS\s+)?JOIN\s+[\w\.\[\]`\"']+"

        from_count = len(re.findall(from_pattern, query, re.IGNORECASE))
        join_count = len(re.findall(join_pattern, query, re.IGNORECASE))

        return max(1, from_count + join_count)

    def _count_joins(self, query: str) -> int:
        """Count JOIN operations"""
        join_pattern = r"\bJOIN\b"
        return len(re.findall(join_pattern, query, re.IGNORECASE))

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity level"""
        upper_query = query.upper()
        
        # Check for complex patterns
        complex_count = 0
        
        for keyword in self.COMPLEX_KEYWORDS:
            if keyword in upper_query:
                complex_count += 1
        
        # Count subqueries
        subquery_count = upper_query.count("SELECT") - 1
        if subquery_count > 0:
            complex_count += min(subquery_count, 2)
        
        # Count JOINs
        join_count = len(re.findall(r"\bJOIN\b", upper_query, re.IGNORECASE))
        if join_count > 2:
            complex_count += 1
        
        if complex_count >= 3:
            return "complex"
        elif complex_count >= 1:
            return "moderate"
        else:
            return "simple"

    def _generate_warnings(
        self, query: str, is_select_only: bool, 
        sensitive_cols: List[str], join_count: int
    ) -> List[str]:
        """Generate warnings about the query"""
        warnings = []

        # Warning: SELECT *
        if "SELECT *" in query.upper():
            warnings.append("Using SELECT * - consider specifying columns explicitly")

        # Warning: No WHERE clause
        if is_select_only and "WHERE" not in query.upper():
            warnings.append("No WHERE clause - query might scan entire table")

        # Warning: Sensitive columns
        if sensitive_cols:
            for col in sensitive_cols:
                if col != "SELECT * (could expose sensitive data)":
                    warnings.append(f"Sensitive column '{col}' may be exposed")

        # Warning: Many JOINs
        if join_count > 3:
            warnings.append(f"Query has {join_count} JOINs - performance may be impacted")

        # Warning: Comments
        if "--" in query or "/*" in query or "#" in query:
            warnings.append("Query contains comments - verify query logic")

        return warnings

    def get_injection_risk_summary(self, injection_patterns: List[str]) -> Tuple[str, str]:
        """
        Get risk level and summary for detected injection patterns
        
        Returns: (risk_level, summary)
        """
        if not injection_patterns:
            return "LOW", "No SQL injection patterns detected"

        # Check for critical patterns
        critical_patterns = [
            "UNION SELECT",
            "Stacked queries",
            "Dynamic SQL execution",
            "DROP statement",
        ]

        found_critical = any(p in injection_patterns for p in critical_patterns)

        if found_critical:
            return "CRITICAL", f"Dangerous SQL injection patterns found: {', '.join(injection_patterns[:2])}"
        else:
            return "MEDIUM", f"Potential SQL patterns found: {', '.join(injection_patterns[:2])}"
