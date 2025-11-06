"""
Universal Language Support Package
Comprehensive language detection and analysis for all programming languages
"""

from .detector import (
    UniversalLanguageDetector,
    LanguageInfo,
    LanguageCategory,
    language_detector,
    detect_file_language,
    get_security_tools_for_file,
    analyze_project_languages
)

__all__ = [
    'UniversalLanguageDetector',
    'LanguageInfo', 
    'LanguageCategory',
    'language_detector',
    'detect_file_language',
    'get_security_tools_for_file',
    'analyze_project_languages'
]