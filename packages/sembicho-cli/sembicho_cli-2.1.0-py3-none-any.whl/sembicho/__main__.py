#!/usr/bin/env python3
"""
SemBicho CLI - Herramienta de línea de comandos para análisis estático de seguridad
Punto de entrada principal de la aplicación CLI
"""

import argparse
import sys
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import replace

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sembicho.scanner import SemBichoScanner

# Versión de la aplicación
VERSION = "1.0.0"

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sembicho-cli')


def create_parser():
    """
    Crea y configura el parser de argumentos de línea de comandos
    
    Returns:
        argparse.ArgumentParser: Parser configurado
    """
    parser = argparse.ArgumentParser(
        description='SemBicho - Análisis estático de seguridad para código fuente',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos de uso:
  %(prog)s scan --path ./mi-proyecto --output reporte.json
  %(prog)s scan --path ./mi-proyecto --api-url http://localhost:8000/api/results --token abc123
  %(prog)s scan --path . --ci-mode --fail-on critical,high
  %(prog)s scan --path . --output reporte.html --format html
        '''
    )
    
    # Comando principal
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Subcomando 'scan'
    scan_parser = subparsers.add_parser('scan', help='Ejecutar análisis de seguridad')
    
    # Argumentos básicos
    scan_parser.add_argument('--path', '-p', 
                           default='.',
                           help='Ruta del archivo o directorio a analizar (default: directorio actual)')
    
    # Opciones de salida
    scan_parser.add_argument('--output', '-o', 
                           help='Archivo donde guardar el reporte')
    scan_parser.add_argument('--format', '-f',
                           choices=['json', 'html', 'console', 'sarif', 'xml', 'summary'], 
                           default='summary',
                           help='Formato de salida del reporte (default: summary)')
    scan_parser.add_argument('--multiple-formats',
                           help='Generar múltiples formatos separados por coma (ej: json,html,sarif)')
    
    # Filtros de severidad
    scan_parser.add_argument('--severity', '-s',
                           choices=['low', 'medium', 'high', 'critical'],
                           help='Filtrar por nivel de severidad mínimo')
    scan_parser.add_argument('--fail-on',
                           help='Fallar si se encuentran vulnerabilidades de estas severidades (ej: critical,high)')
    
    # Configuración
    scan_parser.add_argument('--config', '-c',
                           help='Archivo de configuración personalizado')
    scan_parser.add_argument('--verbose', '-v',
                           action='store_true',
                           help='Modo verbose para más detalles')
    
    # Integración con backend API
    scan_parser.add_argument('--api-url',
                           help='URL del endpoint API para enviar resultados')
    scan_parser.add_argument('--token', '--api-token',
                           help='Token de autenticación para la API (requerido si se usa --api-url)')
    scan_parser.add_argument('--pipeline-id',
                           help='ID del pipeline para identificar el escaneo')
    scan_parser.add_argument('--environment',
                           choices=['development', 'staging', 'production'],
                           default='development',
                           help='Ambiente de ejecución (development, staging, production)')
    
    # Modo CI/CD
    scan_parser.add_argument('--ci-mode',
                           action='store_true',
                           help='Modo CI/CD con salida optimizada para pipelines')
    scan_parser.add_argument('--no-color',
                           action='store_true',
                           help='Deshabilitar colores en la salida')
    
    # Herramientas específicas
    scan_parser.add_argument('--tools',
                           help='Herramientas específicas a ejecutar (ej: bandit,eslint,semgrep)')
    scan_parser.add_argument('--exclude',
                           help='Patrones de archivos/directorios a excluir')
    
    # Subcomando 'version'
    version_parser = subparsers.add_parser('version', help='Mostrar versión del programa')
    
    # Subcomando 'config'
    config_parser = subparsers.add_parser('config', help='Configurar SemBicho')
    config_parser.add_argument('--init', action='store_true', help='Crear archivo de configuración inicial')
    config_parser.add_argument('--show', action='store_true', help='Mostrar configuración actual')
    
    return parser


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Carga configuración desde archivo
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Diccionario de configuración
    """
    config = {}
    
    # Archivos de configuración por defecto
    default_configs = [
        '.sembicho.json',
        'sembicho.json',
        os.path.expanduser('~/.sembicho/config.json')
    ]
    
    config_file = config_path
    if not config_file:
        for default_config in default_configs:
            if os.path.exists(default_config):
                config_file = default_config
                break
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Configuración cargada desde: {config_file}")
        except Exception as e:
            logger.warning(f"Error cargando configuración: {e}")
    
    return config


def filter_vulnerabilities_by_severity(vulnerabilities: list, min_severity: str) -> list:
    """
    Filtra vulnerabilidades por severidad mínima
    
    Args:
        vulnerabilities: Lista de vulnerabilidades
        min_severity: Severidad mínima
        
    Returns:
        Lista filtrada de vulnerabilidades
    """
    severity_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
    min_level = severity_order.get(min_severity, 0)
    
    return [
        vuln for vuln in vulnerabilities 
        if severity_order.get(vuln.get('severity', 'low'), 0) >= min_level
    ]


def check_fail_conditions(results: Dict, fail_on: str) -> bool:
    """
    Verifica si se deben fallar las condiciones especificadas
    
    Args:
        results: Resultados del escaneo
        fail_on: Severidades que deben causar fallo
        
    Returns:
        True si se debe fallar, False en caso contrario
    """
    if not fail_on:
        return False
    
    fail_severities = [s.strip().lower() for s in fail_on.split(',')]
    severity_counts = results.get('severity_counts', {})
    
    for severity in fail_severities:
        if severity_counts.get(severity, 0) > 0:
            return True
    
    return False


def handle_scan_command(args):
    """
    Maneja el comando 'scan' - Modo Enterprise Backend-Only
    
    Args:
        args: Argumentos parseados de línea de comandos
    """
    # Configurar logging según verbose mode
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Cargar configuración
    config = load_config(args.config)
    
    # Merge configuración con argumentos CLI
    if args.api_url:
        config['api_url'] = args.api_url
    if args.token:
        config['token'] = args.token
    if args.pipeline_id:
        config['pipeline_id'] = args.pipeline_id
    
    # Validar token obligatorio para modo empresarial
    if not config.get('token') and not args.token:
        logger.error("🔐 Token de autenticación requerido para modo empresarial")
        logger.info("💡 Uso: sembicho scan --path ./proyecto --token TU_TOKEN")
        logger.info("💡 O configura la variable de entorno SEMBICHO_TOKEN")
        logger.info("💡 O agrega 'token' en .sembicho.json")
        sys.exit(1)
    
    # Validar URL del backend
    if not config.get('api_url'):
        logger.error("🌐 URL del backend requerida para modo empresarial")
        logger.info("💡 Agrega 'api_url' en .sembicho.json o usa --api-url")
        sys.exit(1)
    
    # Validar ruta
    target_path = Path(args.path)
    if not target_path.exists():
        logger.error(f"📂 La ruta '{args.path}' no existe.")
        sys.exit(1)
    
    # Usar token del argumento o configuración
    token = args.token or config.get('token')
    
    # Mostrar info inicial modo enterprise
    if not args.ci_mode:
        logger.info("🚀 SemBicho Enterprise - Análisis de Seguridad Profesional")
        logger.info(f"📂 Proyecto: {target_path.name}")
        logger.info(f"🌐 Backend: {config.get('api_url')}")
        logger.info(f"🏗️  Pipeline: {args.pipeline_id or 'default'}")
        logger.info("━" * 60)
    
    # Crear instancia del scanner en modo enterprise
    scanner = SemBichoScanner(config)
    scanner.configure_enterprise_mode(
        backend_url=config.get('api_url'),
        token=token,
        environment=args.environment or 'development',
        pipeline_id=args.pipeline_id
    )
    
    try:
        # Ejecutar análisis empresarial
        if target_path.is_file():
            results = scanner.scan_file(str(target_path))
        else:
            results = scanner.scan_directory(str(target_path))
        
        # En modo enterprise, el scanner automáticamente envía al backend
        # Solo mostramos resumen ejecutivo
        
        if not args.ci_mode:
            logger.info("✅ Análisis completado exitosamente")
            logger.info("━" * 60)
            logger.info("📊 RESUMEN EJECUTIVO:")
            logger.info(f"   🛡️  Grado de Seguridad: {results.overall_security_grade}")
            logger.info(f"   ⚡ Grado de Calidad: {results.overall_quality_grade}")
            logger.info(f"   📋 Grado de Compliance: {results.overall_compliance_grade}")
            logger.info(f"    Nivel de Riesgo: {results.risk_level}")
            logger.info(f"   🔍 Vulnerabilidades: {results.total_vulnerabilities}")
            
            # Mostrar solo vulnerabilidades críticas/altas si existen
            if results.severity_counts.get('critical', 0) > 0 or results.severity_counts.get('high', 0) > 0:
                logger.info("━" * 60)
                logger.warning("⚠️  VULNERABILIDADES DE ALTA PRIORIDAD:")
                if results.severity_counts.get('critical', 0) > 0:
                    logger.error(f"   🔴 Críticas: {results.severity_counts['critical']}")
                if results.severity_counts.get('high', 0) > 0:
                    logger.warning(f"   🟠 Altas: {results.severity_counts['high']}")
                    
            logger.info("━" * 60)
            logger.info(f"📤 Resultados enviados al dashboard empresarial")
            logger.info(f"🔗 ID de Escaneo: {results.scan_id}")
            logger.info(f"📈 Ver detalles en: {config.get('api_url')}/dashboard")
        
        # Aplicar fail conditions si están configuradas
        if args.fail_on:
            severities_to_fail = [s.strip() for s in args.fail_on.split(',')]
            should_fail = False
            
            for severity in severities_to_fail:
                count = results.severity_counts.get(severity, 0)
                if count > 0:
                    logger.error(f"💥 Fallo por {count} vulnerabilidades de severidad '{severity}'")
                    should_fail = True
            
            if should_fail:
                logger.error("❌ Pipeline fallido por vulnerabilidades críticas")
                sys.exit(1)
        
        # Modo CI: respuesta optimizada para pipelines
        if args.ci_mode:
            total = results.total_vulnerabilities
            critical = results.severity_counts.get('critical', 0)
            high = results.severity_counts.get('high', 0)
            
            if total == 0:
                print("✅ PASS - Análisis de seguridad completado sin vulnerabilidades")
            else:
                print(f"⚠️  REVIEW - {total} vulnerabilidades encontradas")
                print(f"   Seguridad: {results.overall_security_grade} | Riesgo: {results.risk_level}")
                if critical > 0 or high > 0:
                    print(f"   🔴 Críticas: {critical} | 🟠 Altas: {high}")
                print(f"   📊 Dashboard: {config.get('api_url')}/scan/{results.scan_id}")
        
    except Exception as e:
        logger.error(f"❌ Error durante el análisis empresarial: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def handle_version_command():
    """
    Maneja el comando 'version'
    """
    print(f"SemBicho CLI v{VERSION}")
    print("Herramienta de análisis estático de seguridad")
    print("Desarrollado para detectar vulnerabilidades en código fuente")


def handle_config_command(args):
    """
    Maneja el comando 'config'
    
    Args:
        args: Argumentos parseados
    """
    if args.init:
        # Crear archivo de configuración inicial
        config_template = {
            "api_url": "https://sembichobackend.onrender.com/reports",
            "token": "",
            "pipeline_id": "",
            "default_format": "console",
            "fail_on": ["critical", "high"],
            "tools": ["bandit", "eslint", "semgrep", "secrets"],
            "exclude_patterns": [
                "*.min.js",
                "node_modules/*",
                ".git/*",
                "__pycache__/*",
                "*.pyc"
            ],
            "compliance": {
                "owasp_top_10": True,
                "cwe_mapping": True,
                "nist_framework": True
            }
        }
        
        config_file = ".sembicho.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_template, f, indent=2, ensure_ascii=False)
            print(f"[OK] Archivo de configuración creado: {config_file}")
            print("Edita el archivo para personalizar la configuración.")
        except Exception as e:
            logger.error(f"Error creando configuración: {e}")
            sys.exit(1)
    
    elif args.show:
        # Mostrar configuración actual
        config = load_config()
        if config:
            print("[CONFIG] Configuración actual:")
            # Ocultar token por seguridad
            config_display = config.copy()
            if 'token' in config_display and config_display['token']:
                config_display['token'] = '***HIDDEN***'
            print(json.dumps(config_display, indent=2, ensure_ascii=False))
        else:
            print("[WARNING] No se encontró archivo de configuración.")
            print("Usa 'sembicho config --init' para crear uno.")
    
    else:
        print("Usa --init para crear configuración o --show para ver la actual")


def main():
    """
    Función principal del CLI
    """
    parser = create_parser()
    
    # Si no se proporcionan argumentos, mostrar ayuda
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Ejecutar comando correspondiente
    if args.command == 'scan':
        handle_scan_command(args)
    elif args.command == 'version':
        handle_version_command()
    elif args.command == 'config':
        handle_config_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()