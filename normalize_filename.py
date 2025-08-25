#!/usr/bin/env python3
"""
Script para normalizar nombres de archivos y carpetas de CV según parámetros estándar de CVPilot
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def normalize_cv_filename():
    """Normalizar el nombre del archivo CV según parámetros estándar de CVPilot"""
    
    # Ruta original
    original_path = Path("D:/Work Work/Upwork/CVPilot/output/Asistente - Analista/CV PH.docx")
    
    if not original_path.exists():
        print(f"❌ Archivo no encontrado: {original_path}")
        return
    
    # Parámetros de normalización según estándares de CVPilot
    job_title = "Asistente - Analista"
    role_initials = "AA"  # Asistente - Analista
    software_category = "GEN"  # General tools
    business_model = "GEN"  # General business model
    year = "2025"
    
    # Generar nombre normalizado
    normalized_filename = f"PedroHerrera_{role_initials}_{software_category}_{business_model}_{year}.docx"
    
    # Determinar carpeta normalizada
    # Basado en el patrón: "Job Title - Specialization - Software"
    specialization = "General"  # Para Asistente - Analista
    software_list = "Microsoft Office, General Tools"
    
    normalized_folder = f"{job_title} - {specialization} - {software_list}"
    
    # Crear nueva ruta
    new_folder_path = Path("D:/Work Work/Upwork/CVPilot/output") / normalized_folder
    new_file_path = new_folder_path / normalized_filename
    
    # Crear carpeta si no existe
    new_folder_path.mkdir(exist_ok=True)
    
    # Mover archivo
    try:
        shutil.move(str(original_path), str(new_file_path))
        print(f"✅ Archivo normalizado exitosamente:")
        print(f"   📁 Carpeta: {normalized_folder}")
        print(f"   📄 Archivo: {normalized_filename}")
        print(f"   📍 Nueva ubicación: {new_file_path}")
        
        # Eliminar carpeta original si está vacía
        original_folder = original_path.parent
        if original_folder.exists() and not any(original_folder.iterdir()):
            original_folder.rmdir()
            print(f"   🗑️ Carpeta original vacía eliminada: {original_folder}")
            
    except Exception as e:
        print(f"❌ Error al mover archivo: {e}")

if __name__ == "__main__":
    print("🔄 Normalizando nombre de archivo CV...")
    normalize_cv_filename()

