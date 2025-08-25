# CVPilot - Quick Start Guide

## 🚀 Setup Rápido

### 1. Instalar Dependencias
```bash
cd CVPilot
pip install -r requirements.txt
```

### 2. Configurar API Keys
```bash
# Copiar archivo de configuración
cp env.example .env

# Editar .env y añadir tus API keys
# OPENAI_API_KEY=tu_api_key_aqui
# ANTHROPIC_API_KEY=tu_api_key_aqui
```

### 3. Verificar Configuración
```bash
python test_simple.py
```

### 4. Ejecutar Demo
```bash
python demo.py
```

## 📋 Uso Básico

### Generar CV con Preview (Dry-Run)
```bash
python -m src.main --job-id 0 --profile-type product_management --dry-run
```

### Generar CV Final
```bash
python -m src.main --job-id 0 --profile-type product_management
```

### Opciones Disponibles
- `--job-id`: ID del trabajo desde DataPM CSV
- `--profile-type`: Tipo de perfil (default: product_management)
- `--dry-run`: Solo generar preview
- `--verbose`: Salida detallada
- `--output-dir`: Directorio de salida

## 📁 Estructura del Proyecto

```
CVPilot/
├── src/                    # Código fuente
│   ├── main.py            # Punto de entrada
│   ├── ingest/            # Carga de datos DataPM
│   ├── matching/          # Matching de perfiles
│   ├── generation/        # Generación con LLM
│   ├── validation/        # Validación de contenido
│   ├── template/          # Procesamiento DOCX
│   └── utils/             # Utilidades
├── templates/             # Templates DOCX
│   └── PedroHerrera_PA_SaaS_B2B_Remote_2025.docx
├── profiles/              # Perfiles JSON
│   └── product_management.json
├── data/                  # Datos de entrada
├── logs/                  # Logs de ejecución
├── backups/               # Backups de templates
├── output/                # Archivos generados
└── requirements.txt       # Dependencias
```

## 🎯 Placeholders del Template

Tu template debe incluir estos placeholders Jinja:

- `{{ObjectiveTitle}}` - Título objetivo
- `{{ProfileSummary}}` - Resumen profesional
- `{{TopBullets}}` - Lista de logros (3-5 bullets)
- `{{SkillList}}` - Lista de habilidades
- `{{SoftwareList}}` - Lista de software
- `{{ATSRecommendations}}` - Recomendaciones ATS

## 🔧 Configuración

### Variables de Entorno (.env)
```
# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# API Keys
OPENAI_API_KEY=tu_api_key
ANTHROPIC_API_KEY=tu_api_key

# Validation Settings
MAX_SUMMARY_LENGTH=200
MAX_BULLET_LENGTH=150
MAX_SKILLS_COUNT=15
MAX_SOFTWARE_COUNT=10
```

## 📊 Datos de Entrada

El sistema lee automáticamente los archivos CSV de DataPM desde:
```
../../DataPM/csv/src/csv_processed/
```

Formato esperado:
- Job title (original)
- Job title (short)
- Company
- Country, State, City
- Schedule type, Experience years, Seniority
- Skills (separados por ;)
- Degrees (separados por ;)
- Software (separados por ;)

## 🐛 Solución de Problemas

### Error: "No module named 'docxtpl'"
```bash
pip install -r requirements.txt
```

### Error: "API key not found"
- Verifica que el archivo `.env` existe
- Asegúrate de que las API keys son correctas

### Error: "Template not found"
- Verifica que el template existe en `templates/`
- Asegúrate de que tiene los placeholders correctos

### Error: "Job ID not found"
- Verifica que el job_id existe en los CSV de DataPM
- Ejecuta `python test_simple.py` para verificar datos

## 📝 Logs

Los logs se guardan en `logs/` con timestamp:
```
logs/cvpilot_20250121_143022.log
```

## 🔄 Flujo de Trabajo

1. **Preparación**: Configura API keys y verifica template
2. **Prueba**: Ejecuta con `--dry-run` para verificar
3. **Generación**: Ejecuta sin `--dry-run` para generar CV
4. **Revisión**: Revisa el CV generado en `output/`
5. **Ajustes**: Modifica perfil o template si es necesario

## 📞 Soporte

Para problemas:
1. Revisa los logs en `logs/`
2. Ejecuta `python test_simple.py`
3. Verifica la configuración en `.env`
4. Consulta `INSTRUCTIONS.md` para detalles completos
