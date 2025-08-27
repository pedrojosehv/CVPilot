#!/usr/bin/env python3
"""
Script de prueba para el EnhancedBulletAnalyzer mejorado
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.intelligent_bullet_analyzer import EnhancedBulletAnalyzer
from utils.logger import LoggerMixin

class TestRunner(LoggerMixin):
    """Ejecutor de pruebas para el analizador mejorado"""
    
    def __init__(self):
        super().__init__()
        self.analyzer = EnhancedBulletAnalyzer("templates/bullet_pool.docx")
    
    def test_enhanced_structure(self):
        """Probar la carga de estructura mejorada"""
        
        self.log_info("🧪 PROBANDO ESTRUCTURA MEJORADA")
        self.log_info("=" * 50)
        
        # Verificar que se cargó la estructura correctamente
        if self.analyzer.bullet_pool:
            self.log_info("✅ Bullet pool cargado correctamente")
            
            # Verificar perfiles
            if "advanced" in self.analyzer.bullet_pool:
                advanced = self.analyzer.bullet_pool["advanced"]
                self.log_info(f"✅ Perfil avanzado encontrado")
                self.log_info(f"   - Roles GCA: {len(advanced.get('gca_roles', []))}")
                self.log_info(f"   - Compañías con bullets: {len(advanced.get('bullets', {}))}")
            
            if "basic" in self.analyzer.bullet_pool:
                basic = self.analyzer.bullet_pool["basic"]
                self.log_info(f"✅ Perfil básico encontrado")
                self.log_info(f"   - Compañías: {len(basic.get('companies', []))}")
                self.log_info(f"   - Compañías con bullets: {len(basic.get('bullets', {}))}")
        else:
            self.log_error("❌ No se pudo cargar el bullet pool")
    
    def test_role_progression(self):
        """Probar la detección de progresión de roles"""
        
        self.log_info("\n🎯 PROBANDO PROGRESIÓN DE ROLES")
        self.log_info("=" * 50)
        
        roles = self.analyzer.role_progression
        if roles:
            self.log_info(f"✅ {len(roles)} roles detectados en progresión:")
            for i, role in enumerate(roles, 1):
                self.log_info(f"   {i}. {role.get('primary_role', 'Unknown')}")
                self.log_info(f"      Período: {role.get('period', 'Unknown')}")
                self.log_info(f"      Contexto: {role.get('application_context', 'Unknown')}")
                self.log_info(f"      Es actual: {'Sí' if role.get('is_current') else 'No'}")
                self.log_info("")
        else:
            self.log_error("❌ No se detectó progresión de roles")
    
    def test_company_contexts(self):
        """Probar los contextos de compañías"""
        
        self.log_info("🏢 PROBANDO CONTEXTOS DE COMPAÑÍAS")
        self.log_info("=" * 50)
        
        contexts = self.analyzer.company_contexts
        if contexts:
            self.log_info(f"✅ {len(contexts)} contextos de compañías:")
            for company, context in contexts.items():
                self.log_info(f"   🏢 {company}:")
                self.log_info(f"      - Industria: {context.get('industry', 'Unknown')}")
                self.log_info(f"      - Tipo: {context.get('type', 'Unknown')}")
                self.log_info(f"      - Ubicación: {context.get('location', 'Unknown')}")
                self.log_info(f"      - Especialización: {context.get('specialization', 'Unknown')}")
                self.log_info("")
        else:
            self.log_error("❌ No se detectaron contextos de compañías")
    
    def test_job_analysis(self):
        """Probar análisis de trabajo específico"""
        
        self.log_info("🔍 PROBANDO ANÁLISIS DE TRABAJO")
        self.log_info("=" * 50)
        
        # Simular datos de trabajo para Product Manager
        test_job_data = {
            'job_title_original': 'Senior Product Manager',
            'company': 'TechCorp',
            'skills': ['Product Management', 'Agile', 'Scrum', 'Data Analysis', 'User Research'],
            'software': ['Jira', 'Figma', 'Google Analytics', 'SQL'],
            'seniority': 'senior'
        }
        
        # Determinar perfil óptimo
        profile_type, matching_role = self.analyzer._determine_optimal_profile(test_job_data)
        
        self.log_info(f"✅ Análisis de trabajo para '{test_job_data['job_title_original']}':")
        self.log_info(f"   - Perfil seleccionado: {profile_type}")
        if matching_role:
            self.log_info(f"   - Rol coincidente: {matching_role.get('primary_role', 'Unknown')}")
            self.log_info(f"   - Período: {matching_role.get('period', 'Unknown')}")
        else:
            self.log_info(f"   - Sin rol específico coincidente")
        
        # Probar selección de bullets
        try:
            selected_bullets = self.analyzer.analyze_job_and_select_bullets(test_job_data, "")
            self.log_info(f"✅ {len(selected_bullets)} bullets seleccionados:")
            for i, bullet in enumerate(selected_bullets, 1):
                self.log_info(f"   {i}. {bullet[:100]}...")
        except Exception as e:
            self.log_error(f"❌ Error en selección de bullets: {e}")
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        
        self.log_info("🚀 INICIANDO PRUEBAS DEL ENHANCED BULLET ANALYZER")
        self.log_info("=" * 60)
        
        try:
            self.test_enhanced_structure()
            self.test_role_progression()
            self.test_company_contexts()
            self.test_job_analysis()
            
            self.log_info("\n🎉 TODAS LAS PRUEBAS COMPLETADAS")
            self.log_info("=" * 60)
            
        except Exception as e:
            self.log_error(f"❌ Error durante las pruebas: {e}")

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
