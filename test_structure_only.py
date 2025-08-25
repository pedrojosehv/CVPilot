#!/usr/bin/env python3
"""
Script de prueba simplificado para validar solo la estructura mejorada (sin LLM)
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from utils.intelligent_bullet_analyzer import EnhancedBulletAnalyzer
    from utils.logger import LoggerMixin
    print("✅ Imports exitosos")
except Exception as e:
    print(f"❌ Error en imports: {e}")
    sys.exit(1)

class StructureTestRunner(LoggerMixin):
    """Ejecutor de pruebas solo para estructura (sin LLM)"""
    
    def __init__(self):
        super().__init__()
        print("🔧 Inicializando StructureTestRunner...")
        try:
            self.analyzer = EnhancedBulletAnalyzer("templates/bullet_pool.docx")
            print("✅ EnhancedBulletAnalyzer inicializado correctamente")
        except Exception as e:
            self.log_error(f"Error inicializando analyzer: {e}")
            print(f"❌ Error inicializando analyzer: {e}")
            self.analyzer = None
    
    def test_enhanced_structure(self):
        """Probar la carga de estructura mejorada"""
        
        self.log_info("🧪 PROBANDO ESTRUCTURA MEJORADA")
        self.log_info("=" * 50)
        
        if not self.analyzer:
            self.log_error("❌ Analyzer no inicializado")
            return
        
        # Verificar que se cargó la estructura correctamente
        if self.analyzer.bullet_pool:
            self.log_info("✅ Bullet pool cargado correctamente")
            
            # Verificar perfiles
            if "advanced" in self.analyzer.bullet_pool:
                advanced = self.analyzer.bullet_pool["advanced"]
                self.log_info(f"✅ Perfil avanzado encontrado")
                self.log_info(f"   - Roles GCA: {len(advanced.get('gca_roles', []))}")
                self.log_info(f"   - Compañías con bullets: {len(advanced.get('bullets', {}))}")
                
                # Mostrar detalles de roles GCA
                gca_roles = advanced.get('gca_roles', [])
                if gca_roles:
                    self.log_info("   📋 Detalles de roles GCA:")
                    for i, role in enumerate(gca_roles, 1):
                        self.log_info(f"      {i}. {role.get('primary_role', 'Unknown')}")
                        self.log_info(f"         - Período: {role.get('period', 'Unknown')}")
                        self.log_info(f"         - Contexto: {role.get('application_context', 'Unknown')}")
                        self.log_info(f"         - Es actual: {'Sí' if role.get('is_current') else 'No'}")
            
            if "basic" in self.analyzer.bullet_pool:
                basic = self.analyzer.bullet_pool["basic"]
                self.log_info(f"✅ Perfil básico encontrado")
                self.log_info(f"   - Compañías: {len(basic.get('companies', []))}")
                self.log_info(f"   - Compañías con bullets: {len(basic.get('bullets', {}))}")
                
                # Mostrar compañías
                companies = basic.get('companies', [])
                if companies:
                    self.log_info("   🏢 Compañías detectadas:")
                    for company in companies:
                        self.log_info(f"      - {company.get('name', 'Unknown')}")
                        self.log_info(f"        Industria: {company.get('industry', 'Unknown')}")
                        self.log_info(f"        Ubicación: {company.get('location', 'Unknown')}")
        else:
            self.log_error("❌ No se pudo cargar el bullet pool")
    
    def test_company_contexts(self):
        """Probar los contextos de compañías"""
        
        self.log_info("\n🏢 PROBANDO CONTEXTOS DE COMPAÑÍAS")
        self.log_info("=" * 50)
        
        if not self.analyzer:
            self.log_error("❌ Analyzer no inicializado")
            return
        
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
    
    def test_profile_determination(self):
        """Probar determinación de perfiles sin LLM"""
        
        self.log_info("🎯 PROBANDO DETERMINACIÓN DE PERFILES")
        self.log_info("=" * 50)
        
        if not self.analyzer:
            self.log_error("❌ Analyzer no inicializado")
            return
        
        # Casos de prueba
        test_cases = [
            {
                'job_title_original': 'Senior Product Manager',
                'company': 'TechCorp',
                'skills': ['Product Management', 'Agile', 'Scrum', 'Data Analysis'],
                'software': ['Jira', 'Figma'],
                'seniority': 'senior'
            },
            {
                'job_title_original': 'Quality Assurance Analyst',
                'company': 'ManufacturingCorp',
                'skills': ['Quality Control', 'Testing', 'Process Improvement'],
                'software': ['Excel', 'SAP'],
                'seniority': 'mid'
            },
            {
                'job_title_original': 'Business Analyst',
                'company': 'FinTech Solutions',
                'skills': ['Business Analysis', 'Requirements Gathering', 'Process Mapping'],
                'software': ['Power BI', 'Visio'],
                'seniority': 'senior'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            self.log_info(f"   📋 Caso {i}: {test_case['job_title_original']}")
            
            try:
                profile_type, matching_role = self.analyzer._determine_optimal_profile(test_case)
                self.log_info(f"      - Perfil seleccionado: {profile_type}")
                if matching_role:
                    self.log_info(f"      - Rol coincidente: {matching_role.get('primary_role', 'Unknown')}")
                else:
                    self.log_info(f"      - Sin rol específico coincidente")
            except Exception as e:
                self.log_error(f"      ❌ Error: {e}")
            
            self.log_info("")
    
    def test_fallback_selection(self):
        """Probar selección de fallback sin LLM"""
        
        self.log_info("🔄 PROBANDO SELECCIÓN DE FALLBACK")
        self.log_info("=" * 50)
        
        if not self.analyzer:
            self.log_error("❌ Analyzer no inicializado")
            return
        
        test_job_data = {
            'job_title_original': 'Product Manager',
            'company': 'TechStartup',
            'skills': ['Product Management', 'Agile', 'User Research'],
            'software': ['Jira', 'Figma'],
            'seniority': 'senior'
        }
        
        try:
            # Probar fallback avanzado
            advanced_bullets = self.analyzer._enhanced_fallback_selection(test_job_data, "advanced")
            self.log_info(f"✅ Fallback avanzado: {len(advanced_bullets)} bullets")
            for i, bullet in enumerate(advanced_bullets[:3], 1):
                self.log_info(f"   {i}. {bullet[:80]}...")
            
            # Probar fallback básico
            basic_bullets = self.analyzer._enhanced_fallback_selection(test_job_data, "basic")
            self.log_info(f"✅ Fallback básico: {len(basic_bullets)} bullets")
            for i, bullet in enumerate(basic_bullets[:3], 1):
                self.log_info(f"   {i}. {bullet[:80]}...")
                
        except Exception as e:
            self.log_error(f"❌ Error en fallback: {e}")
    
    def run_structure_tests(self):
        """Ejecutar solo pruebas de estructura"""
        
        self.log_info("🚀 INICIANDO PRUEBAS DE ESTRUCTURA")
        self.log_info("=" * 60)
        
        try:
            self.test_enhanced_structure()
            self.test_company_contexts()
            self.test_profile_determination()
            self.test_fallback_selection()
            
            self.log_info("\n🎉 PRUEBAS DE ESTRUCTURA COMPLETADAS")
            self.log_info("=" * 60)
            
        except Exception as e:
            self.log_error(f"❌ Error durante las pruebas: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de estructura...")
    runner = StructureTestRunner()
    runner.run_structure_tests()
    print("✅ Pruebas completadas")
