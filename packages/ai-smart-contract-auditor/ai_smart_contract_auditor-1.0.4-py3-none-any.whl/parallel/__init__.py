"""
Parallel Processing Module for AI Smart Contract Auditor
Provides parallel execution capabilities for auditing tasks
"""

from .parallel_processor import (
    ParallelProcessor,
    ParallelTask,
    ParallelResult,
    ParallelAuditEngine,
    ParallelDatabaseQuery,
    ParallelPoCGenerator
)

from .parallel_audit import (
    ParallelSlitherAnalyzer,
    ParallelFoundryTester,
    ParallelVulnerabilityAnalyzer
)

from .parallel_database import (
    ParallelVulnerabilityDB,
    ParallelPoCDatabase
)

__all__ = [
    # Core
    "ParallelProcessor",
    "ParallelTask",
    "ParallelResult",
    "ParallelAuditEngine",
    "ParallelDatabaseQuery",
    "ParallelPoCGenerator",
    # Audit
    "ParallelSlitherAnalyzer",
    "ParallelFoundryTester",
    "ParallelVulnerabilityAnalyzer",
    # Database
    "ParallelVulnerabilityDB",
    "ParallelPoCDatabase",
]

__version__ = "1.0.0"
