"""
SemBicho - Static Application Security Testing Tool
Paquete principal para análisis estático de seguridad
"""

__version__ = "1.0.0"
__author__ = "SemBicho Team"
__license__ = "MIT"

from .scanner import SemBichoScanner, Vulnerability, ScanResult

__all__ = ['SemBichoScanner', 'Vulnerability', 'ScanResult']