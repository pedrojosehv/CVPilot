# CVPilot - CV Automation Tool

CVPilot es una herramienta de automatización para personalizar CVs según ofertas de trabajo específicas, utilizando datos normalizados de DataPM y LLMs para generar contenido adaptado.

## Arquitectura

### Pipeline Principal

1. **Ingesta**: Recupera JD normalizada por DataPM (roles, skills, software, prioridades, empresa, KPIs)
2. **Matching**: Compara JD con perfil maestro para calcular fit_score y gap_list
3. **Selección de Perfil**: Elige tipo de perfil según reglas (Growth PM, Data PM, Mobile PM, etc.)
4. **Generación Dirigida**: LLM genera replacements en formato JSON estructurado
5. **Validación**: Comprueba longitud, tokens prohibidos, y confidence_score
6. **Inserción DOCX**: Usa docxtpl con placeholders Jinja preservando estilos
7. **Dry-run**: Genera versión de texto plano y diff con CV original
8. **Registro/QA**: Log del job, fit_score, replacements, y enlace al DOCX final

### Estructura de Datos

- **Job Description**: Datos normalizados de DataPM (skills, software, seniority, etc.)
- **Profile Types**: Perfiles predefinidos (Product Management, Growth PM, Data PM, etc.)
- **Replacements**: JSON estructurado con bloques de contenido
- **Template**: DOCX con placeholders Jinja ({{ProfileSummary}}, {{TopBullets}}, etc.)

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

1. Crear archivo `.env` con las API keys:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

2. Colocar CV template en `templates/` con placeholders Jinja
3. Configurar perfiles en `profiles/`
4. Configurar datos de DataPM en `data/`

## Uso

```bash
python src/main.py --job-id <job_id> --profile-type <profile_type>
```

## Estructura del Proyecto

```
CVPilot/
├── src/                    # Código fuente
│   ├── main.py            # Punto de entrada
│   ├── ingest/            # Módulo de ingesta de datos
│   ├── matching/          # Módulo de matching y scoring
│   ├── generation/        # Módulo de generación con LLM
│   ├── validation/        # Módulo de validación
│   ├── template/          # Módulo de procesamiento de templates
│   └── utils/             # Utilidades
├── templates/             # Templates DOCX
├── profiles/              # Perfiles predefinidos
├── data/                  # Datos de DataPM
├── logs/                  # Logs de ejecución
├── backups/               # Backups de templates
└── requirements.txt       # Dependencias
```

## Placeholders del Template

- `{{ProfileSummary}}`: Resumen profesional adaptado
- `{{TopBullets}}`: 3-5 bullets prioritarios
- `{{SkillList}}`: Lista de skills ordenada por relevancia
- `{{SoftwareList}}`: Lista de software relevante
- `{{ObjectiveTitle}}`: Título objetivo adaptado
- `{{ATSRecommendations}}`: Recomendaciones para ATS

## Validaciones

- Longitud de secciones
- Tokens prohibidos
- Confidence score del LLM
- Integridad del template
- Encoding y caracteres especiales
