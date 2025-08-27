#!/usr/bin/env python3
"""
Script para mostrar el análisis detallado de bullet points
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.intelligent_bullet_analyzer import EnhancedBulletAnalyzer
from ingest.manual_loader import ManualLoader
import pandas as pd

def show_bullet_analysis():
    """Mostrar análisis detallado de bullet points para job ID 160"""
    
    print("🔍 ANÁLISIS DETALLADO DE BULLET POINTS - JOB ID 160")
    print("=" * 60)
    
    # Cargar job data
    loader = ManualLoader()
    jobs = loader.load_jobs()
    
    # Encontrar job ID 160
    job_160 = None
    for job in jobs:
        if job.job_id == 160:
            job_160 = job
            break
    
    if not job_160:
        print("❌ No se encontró el job ID 160")
        return
    
    print(f"📋 JOB DATA:")
    print(f"   - ID: {job_160.job_id}")
    print(f"   - Título: {job_160.job_title}")
    print(f"   - Empresa: {job_160.company}")
    print(f"   - País: {job_160.country}")
    print(f"   - Experiencia: {job_160.experience_years}")
    print(f"   - Seniority: {job_160.seniority}")
    print(f"   - Skills: {job_160.skills}")
    print(f"   - Software: {job_160.software}")
    
    print(f"\n🔧 INICIALIZANDO ENHANCED BULLET ANALYZER...")
    
    try:
        # Inicializar el analyzer
        analyzer = EnhancedBulletAnalyzer()
        
        print(f"✅ EnhancedBulletAnalyzer inicializado correctamente")
        
        # Mostrar estructura del bullet pool
        print(f"\n📊 ESTRUCTURA DEL BULLET POOL:")
        print(f"   - Perfiles Avanzados: {len(analyzer.bullet_pool.get('advanced', {}))}")
        print(f"   - Perfiles Básicos: {len(analyzer.bullet_pool.get('basic', {}))}")
        print(f"   - Progresión de Roles GCA: {len(analyzer.role_progression)}")
        print(f"   - Contextos de Empresas: {len(analyzer.company_contexts)}")
        
        # Mostrar roles GCA disponibles
        print(f"\n🏢 ROLES GCA DISPONIBLES:")
        for i, role in enumerate(analyzer.role_progression[:5], 1):
            print(f"   {i}. {role.get('role', 'N/A')} - {role.get('period', 'N/A')}")
        if len(analyzer.role_progression) > 5:
            print(f"   ... y {len(analyzer.role_progression) - 5} más")
        
        # Convertir job a dict para el análisis
        job_dict = {
            'job_id': job_160.job_id,
            'job_title': job_160.job_title,
            'company': job_160.company,
            'country': job_160.country,
            'experience_years': job_160.experience_years,
            'seniority': job_160.seniority,
            'skills': job_160.skills.split('; ') if job_160.skills else [],
            'software': job_160.software.split('; ') if job_160.software else []
        }
        
        print(f"\n🎯 ANÁLISIS DE JOB Y SELECCIÓN DE BULLETS:")
        print(f"   - Job Title: {job_dict['job_title']}")
        print(f"   - Company: {job_dict['company']}")
        print(f"   - Skills detectadas: {len(job_dict['skills'])}")
        print(f"   - Software detectado: {len(job_dict['software'])}")
        
        # Determinar perfil óptimo
        profile_type, matching_role = analyzer._determine_optimal_profile(job_dict)
        print(f"\n📈 DETERMINACIÓN DE PERFIL:")
        print(f"   - Perfil seleccionado: {profile_type}")
        if matching_role:
            print(f"   - Rol GCA coincidente: {matching_role.get('role', 'N/A')}")
            print(f"   - Período: {matching_role.get('period', 'N/A')}")
        else:
            print(f"   - No se encontró rol GCA coincidente")
        
        # Mostrar bullets disponibles por perfil
        if profile_type == 'advanced':
            bullets = analyzer.bullet_pool.get('advanced', {}).get('GCA', [])
            print(f"\n💼 BULLETS DISPONIBLES (Perfil Avanzado - GCA):")
            print(f"   - Total bullets: {len(bullets)}")
            for i, bullet in enumerate(bullets[:3], 1):
                print(f"   {i}. {bullet[:100]}...")
            if len(bullets) > 3:
                print(f"   ... y {len(bullets) - 3} más")
        else:
            bullets = analyzer.bullet_pool.get('basic', {}).get('GCA', [])
            print(f"\n💼 BULLETS DISPONIBLES (Perfil Básico - GCA):")
            print(f"   - Total bullets: {len(bullets)}")
            for i, bullet in enumerate(bullets[:3], 1):
                print(f"   {i}. {bullet[:100]}...")
            if len(bullets) > 3:
                print(f"   ... y {len(bullets) - 3} más")
        
        # Mostrar otras empresas disponibles
        other_companies = [k for k in analyzer.bullet_pool.get('basic', {}).keys() if k != 'GCA']
        print(f"\n🏢 OTRAS EMPRESAS DISPONIBLES:")
        for company in other_companies[:5]:
            bullets_count = len(analyzer.bullet_pool.get('basic', {}).get(company, []))
            print(f"   - {company}: {bullets_count} bullets")
        if len(other_companies) > 5:
            print(f"   ... y {len(other_companies) - 5} más")
        
        print(f"\n✅ ANÁLISIS COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error en el análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_bullet_analysis()
