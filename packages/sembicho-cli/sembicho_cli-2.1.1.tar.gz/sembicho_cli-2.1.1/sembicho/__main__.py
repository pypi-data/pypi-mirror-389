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
from dataclasses import replace, asdict

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
    
    # Subcomando 'lint' - Análisis de linting
    lint_parser = subparsers.add_parser('lint', help='Ejecutar análisis de linting (estilo y formato)')
    lint_parser.add_argument('--path', '-p', 
                           default='.',
                           help='Ruta del archivo o directorio a analizar')
    lint_parser.add_argument('--language', '-l',
                           choices=['python', 'javascript', 'typescript', 'java', 'php', 'ruby', 'go', 'csharp'],
                           help='Lenguaje a analizar (auto-detectado si no se especifica)')
    lint_parser.add_argument('--output', '-o',
                           help='Archivo donde guardar el reporte')
    lint_parser.add_argument('--format', '-f',
                           choices=['json', 'console', 'summary'],
                           default='summary',
                           help='Formato de salida')
    lint_parser.add_argument('--config', '-c',
                           help='Archivo de configuración (sembicho-quality.yml)')
    
    # Subcomando 'complexity' - Análisis de complejidad
    complexity_parser = subparsers.add_parser('complexity', help='Análisis de complejidad ciclomática y cognitiva')
    complexity_parser.add_argument('--path', '-p',
                                 default='.',
                                 help='Ruta del archivo o directorio a analizar')
    complexity_parser.add_argument('--language', '-l',
                                 choices=['python', 'javascript', 'typescript', 'java', 'php', 'ruby', 'go', 'csharp'],
                                 help='Lenguaje a analizar (auto-detectado si no se especifica)')
    complexity_parser.add_argument('--output', '-o',
                                 help='Archivo donde guardar el reporte')
    complexity_parser.add_argument('--format', '-f',
                                 choices=['json', 'console', 'summary'],
                                 default='summary',
                                 help='Formato de salida')
    complexity_parser.add_argument('--threshold',
                                 type=int,
                                 default=10,
                                 help='Umbral de complejidad para reportar (default: 10)')
    
    # Subcomando 'quality' - Análisis de calidad completo
    quality_parser = subparsers.add_parser('quality', help='Análisis de calidad completo (linting + complexity + coverage + smells)')
    quality_parser.add_argument('--path', '-p',
                              default='.',
                              help='Ruta del archivo o directorio a analizar')
    quality_parser.add_argument('--output', '-o',
                              help='Archivo donde guardar el reporte')
    quality_parser.add_argument('--format', '-f',
                              choices=['json', 'html', 'console', 'summary'],
                              default='summary',
                              help='Formato de salida')
    quality_parser.add_argument('--config', '-c',
                              help='Archivo de configuración (sembicho-quality.yml)')
    quality_parser.add_argument('--fail-on-grade',
                              choices=['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F'],
                              help='Fallar si el grado de calidad es inferior al especificado')
    
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


def handle_lint_command(args):
    """
    Maneja el comando 'lint' para análisis de linting
    
    Args:
        args: Argumentos parseados
    """
    from sembicho.quality_integrator import QualityScannerIntegrator
    
    # Cargar configuración
    config = load_config(args.config)
    
    # Crear integrador de calidad
    quality_scanner = QualityScannerIntegrator(config)
    
    # Validar ruta
    if not os.path.exists(args.path):
        logger.error(f"Ruta no encontrada: {args.path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🔍 SemBicho - Análisis de Linting")
    print(f"{'='*60}")
    print(f"Ruta: {args.path}")
    print(f"Lenguaje: {args.language or 'auto-detectado'}")
    print(f"{'='*60}\n")
    
    # Ejecutar análisis de linting
    try:
        result = quality_scanner.analyze_quality(args.path, args.language)
        
        # Formatear salida
        if args.format == 'json':
            output = {
                'linting_issues': [asdict(v) for v in result.linting_issues],
                'linting_metrics': result.linting_metrics,
                'total_issues': len(result.linting_issues),
                'quality_score': result.quality_score,
                'grade': result.quality_grade,
                'execution_time': result.execution_time
            }
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"✅ Reporte guardado en: {args.output}")
            else:
                print(json.dumps(output, indent=2, ensure_ascii=False))
        
        else:  # summary/console
            print(f"📊 Resultados del Análisis:\n")
            print(f"   Total de issues: {len(result.linting_issues)}")
            
            if result.linting_metrics:
                metrics = result.linting_metrics.get('metrics', {})
                print(f"   Score de linting: {metrics.get('quality_score', 0):.1f}/100")
                print(f"   Grado: {metrics.get('quality_grade', 'N/A')}")
                
                # Breakdown por categoría
                print(f"\n   Issues por categoría:")
                for category, count in metrics.get('issues_by_category', {}).items():
                    if count > 0:
                        print(f"      - {category}: {count}")
                
                # Tools ejecutados
                tools = metrics.get('tools_executed', [])
                if tools:
                    print(f"\n   Herramientas ejecutadas: {', '.join(tools)}")
            
            print(f"\n   Tiempo de ejecución: {result.execution_time:.2f}s")
            
            if args.output:
                # Guardar también en archivo
                output = {
                    'linting_issues': [asdict(v) for v in result.linting_issues],
                    'linting_metrics': result.linting_metrics
                }
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"\n✅ Reporte completo guardado en: {args.output}")
        
        # Exit code basado en resultados
        sys.exit(0 if len(result.linting_issues) == 0 else 1)
        
    except Exception as e:
        logger.error(f"Error en análisis de linting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_complexity_command(args):
    """
    Maneja el comando 'complexity' para análisis de complejidad
    
    Args:
        args: Argumentos parseados
    """
    from sembicho.complexity_engine import ComplexityEngine
    from dataclasses import asdict
    
    # Validar ruta
    if not os.path.exists(args.path):
        logger.error(f"Ruta no encontrada: {args.path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🔢 SemBicho - Análisis de Complejidad")
    print(f"{'='*60}")
    print(f"Ruta: {args.path}")
    print(f"Lenguaje: {args.language or 'auto-detectado'}")
    print(f"Umbral: {args.threshold}")
    print(f"{'='*60}\n")
    
    # Detectar lenguaje si no se especifica
    language = args.language
    if not language:
        from sembicho.quality_integrator import QualityScannerIntegrator
        integrator = QualityScannerIntegrator()
        language = integrator._detect_language(args.path)
    
    # Crear engine de complejidad
    complexity_engine = ComplexityEngine()
    
    try:
        result = complexity_engine.analyze_complexity(args.path, language)
        
        # Formatear salida
        if args.format == 'json':
            output = {
                'total_functions': result.total_functions,
                'average_complexity': result.average_complexity,
                'max_complexity': result.max_complexity,
                'high_complexity_count': result.high_complexity_count,
                'critical_complexity_count': result.critical_complexity_count,
                'complexity_score': result.complexity_score,
                'complexity_grade': result.complexity_grade,
                'tools_executed': result.tools_executed,
                'complex_functions': [
                    {
                        'name': m.name,
                        'file': m.file_path,
                        'line': m.line_number,
                        'complexity': m.cyclomatic_complexity,
                        'level': m.complexity_level.value,
                        'description': m.description
                    }
                    for m in result.complexity_metrics
                    if m.cyclomatic_complexity >= args.threshold
                ]
            }
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"✅ Reporte guardado en: {args.output}")
            else:
                print(json.dumps(output, indent=2, ensure_ascii=False))
        
        else:  # summary/console
            print(f"📊 Resultados del Análisis de Complejidad:\n")
            print(f"   Total de funciones: {result.total_functions}")
            print(f"   Complejidad promedio: {result.average_complexity:.2f}")
            print(f"   Complejidad máxima: {result.max_complexity}")
            print(f"   Funciones complejas (>10): {result.high_complexity_count}")
            print(f"   Funciones críticas (>20): {result.critical_complexity_count}")
            print(f"\n   Score: {result.complexity_score:.1f}/100")
            print(f"   Grado: {result.complexity_grade}")
            
            # Mostrar funciones más complejas
            complex_funcs = [m for m in result.complexity_metrics if m.cyclomatic_complexity >= args.threshold]
            if complex_funcs:
                print(f"\n   🔴 Funciones que superan el umbral ({args.threshold}):\n")
                # Ordenar por complejidad descendente
                complex_funcs.sort(key=lambda x: x.cyclomatic_complexity, reverse=True)
                for func in complex_funcs[:10]:  # Mostrar top 10
                    print(f"      • {func.name} (complejidad: {func.cyclomatic_complexity})")
                    print(f"        Archivo: {func.file_path}:{func.line_number}")
                    print(f"        {func.description}\n")
            
            if result.tools_executed:
                print(f"   Herramientas: {', '.join(result.tools_executed)}")
            
            if args.output:
                output = {
                    'total_functions': result.total_functions,
                    'average_complexity': result.average_complexity,
                    'max_complexity': result.max_complexity,
                    'complexity_score': result.complexity_score,
                    'complex_functions': [asdict(m) for m in complex_funcs]
                }
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False, default=str)
                print(f"\n✅ Reporte completo guardado en: {args.output}")
        
        # Exit code
        sys.exit(0 if result.high_complexity_count == 0 else 1)
        
    except Exception as e:
        logger.error(f"Error en análisis de complejidad: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def handle_quality_command(args):
    """
    Maneja el comando 'quality' para análisis completo de calidad
    
    Args:
        args: Argumentos parseados
    """
    from sembicho.quality_integrator import QualityScannerIntegrator
    from dataclasses import asdict
    
    # Cargar configuración
    config = load_config(args.config)
    
    # Crear integrador de calidad
    quality_scanner = QualityScannerIntegrator(config)
    
    # Validar ruta
    if not os.path.exists(args.path):
        logger.error(f"Ruta no encontrada: {args.path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"🔍 SemBicho - Análisis de Calidad Completo")
    print(f"{'='*60}")
    print(f"Ruta: {args.path}")
    print(f"{'='*60}\n")
    
    # Ejecutar análisis completo
    try:
        result = quality_scanner.analyze_quality(args.path)
        
        # Formatear salida
        if args.format == 'json':
            output = {
                'linting_issues': [asdict(v) for v in result.linting_issues],
                'linting_metrics': result.linting_metrics,
                'complexity_issues': [asdict(v) for v in result.complexity_issues],
                'complexity_metrics': result.complexity_metrics,
                'coverage_metrics': result.coverage_metrics,
                'code_smells': [asdict(v) for v in result.code_smells],
                'total_quality_issues': result.total_quality_issues,
                'quality_score': result.quality_score,
                'quality_grade': result.quality_grade,
                'execution_time': result.execution_time
            }
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"✅ Reporte guardado en: {args.output}")
            else:
                print(json.dumps(output, indent=2, ensure_ascii=False))
        
        else:  # summary/console
            print(f"📊 Resultados del Análisis de Calidad:\n")
            print(f"   {'='*50}")
            print(f"   Score General: {result.quality_score:.1f}/100")
            print(f"   Grado de Calidad: {result.quality_grade}")
            print(f"   {'='*50}\n")
            
            print(f"   📝 Linting: {len(result.linting_issues)} issues")
            print(f"   🔢 Complejidad: {len(result.complexity_issues)} issues")
            print(f"   👃 Code Smells: {len(result.code_smells)} detected")
            print(f"   📊 Total Issues: {result.total_quality_issues}")
            
            if result.coverage_metrics:
                coverage = result.coverage_metrics.get('total_coverage', 0)
                print(f"   ✅ Cobertura: {coverage:.1f}%")
            
            print(f"\n   ⏱️ Tiempo de ejecución: {result.execution_time:.2f}s")
            
            if args.output:
                # Guardar también en archivo
                output = {
                    'linting_issues': [asdict(v) for v in result.linting_issues],
                    'linting_metrics': result.linting_metrics,
                    'complexity_issues': [asdict(v) for v in result.complexity_issues],
                    'complexity_metrics': result.complexity_metrics,
                    'coverage_metrics': result.coverage_metrics,
                    'code_smells': [asdict(v) for v in result.code_smells],
                    'total_quality_issues': result.total_quality_issues,
                    'quality_score': result.quality_score,
                    'quality_grade': result.quality_grade
                }
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"\n✅ Reporte completo guardado en: {args.output}")
        
        # Check fail condition por grado
        if args.fail_on_grade:
            grade_order = ['F', 'D', 'D+', 'C', 'C+', 'B', 'B+', 'A', 'A+']
            min_grade_idx = grade_order.index(args.fail_on_grade)
            actual_grade_idx = grade_order.index(result.quality_grade)
            
            if actual_grade_idx < min_grade_idx:
                print(f"\n❌ FALLO: Grado {result.quality_grade} es inferior a {args.fail_on_grade}")
                sys.exit(1)
        
        # Exit code basado en issues
        sys.exit(0 if result.total_quality_issues == 0 else 1)
        
    except Exception as e:
        logger.error(f"Error en análisis de calidad: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


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
    elif args.command == 'lint':
        handle_lint_command(args)
    elif args.command == 'complexity':
        handle_complexity_command(args)
    elif args.command == 'quality':
        handle_quality_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()