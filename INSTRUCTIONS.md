# CVPilot - Instrucciones de Uso

## 🚀 Configuración Inicial

### 1. Instalación de Dependencias
```bash
cd CVPilot
python setup.py
```

### 2. Configuración de API Keys
1. Copia el archivo `env.example` a `.env`
2. Edita `.env` y añade tus API keys:
   ```
   OPENAI_API_KEY=tu_api_key_de_openai
   ANTHROPIC_API_KEY=tu_api_key_de_anthropic
   ```

### 3. Verificación de Configuración
```bash
python test_setup.py
```

## 📄 Preparación del Template CV

### Ubicación del Template
Coloca tu CV template en la carpeta `templates/` con el nombre `cv_template.docx`

### Placeholders Requeridos
Tu template debe incluir estos placeholders Jinja:

- `{{ObjectiveTitle}}` - Título objetivo adaptado
- `{{ProfileSummary}}` - Resumen profesional
- `{{TopBullets}}` - Lista de logros principales (3-5 bullets)
- `{{SkillList}}` - Lista de habilidades
- `{{SoftwareList}}` - Lista de software/herramientas
- `{{ATSRecommendations}}` - Recomendaciones para ATS

### Ejemplo de Template
```
CURRICULUM VITAE

{{ObjectiveTitle}}

PROFESSIONAL SUMMARY
{{ProfileSummary}}

KEY ACHIEVEMENTS
{% for bullet in TopBullets %}
• {{bullet.content}}
{% endfor %}

SKILLS
{{SkillList}}

SOFTWARE & TOOLS
{{SoftwareList}}

ATS OPTIMIZATION
{{ATSRecommendations}}
```

## 🎯 Uso del Programa

### Comando Básico
```bash
python src/main.py --job-id <job_id> --profile-type product_management
```

### Opciones Disponibles
- `--job-id`: ID del trabajo a procesar (requerido)
- `--profile-type`: Tipo de perfil (default: product_management)
- `--template-path`: Ruta al template (opcional)
- `--output-dir`: Directorio de salida (default: ./output)
- `--dry-run`: Modo de prueba sin generar archivo final
- `--verbose`: Salida detallada

### Ejemplos de Uso

#### Procesamiento Normal
```bash
python src/main.py --job-id 0 --profile-type product_management
```

#### Modo Dry-Run (Prueba)
```bash
python src/main.py --job-id 0 --profile-type product_management --dry-run
```

#### Con Template Personalizado
```bash
python src/main.py --job-id 0 --template-path templates/mi_template.docx
```

## 📊 Datos de Entrada

### Estructura de DataPM
El programa lee automáticamente los archivos CSV de DataPM desde:
```
../../DataPM/csv/src/csv_processed/
```

### Formato de Datos
Los archivos CSV deben contener estas columnas:
- Job title (original)
- Job title (short)
- Company
- Country
- State
- City
- Schedule type
- Experience years
- Seniority
- Skills (separados por ;)
- Degrees (separados por ;)
- Software (separados por ;)

## 👤 Perfiles Disponibles

### Perfil Actual
- `product_management`: Perfil general de Product Management

### Crear Nuevos Perfiles
1. Crea un archivo JSON en `profiles/`
2. Sigue el formato del ejemplo `product_management.json`
3. Incluye skills, software, y placeholders específicos

## 🔧 Personalización

### Configuración de LLM
Edita `.env` para cambiar:
- `LLM_PROVIDER`: openai o anthropic
- `LLM_MODEL`: modelo específico
- `LLM_TEMPERATURE`: creatividad (0.0-1.0)
- `LLM_MAX_TOKENS`: máximo de tokens

### Validaciones
Configura en `.env`:
- `MAX_SUMMARY_LENGTH`: longitud máxima del resumen
- `MAX_BULLET_LENGTH`: longitud máxima de bullets
- `MAX_SKILLS_COUNT`: máximo número de skills
- `MAX_SOFTWARE_COUNT`: máximo número de software

## 📁 Estructura de Archivos

```
CVPilot/
├── src/                    # Código fuente
├── templates/              # Templates DOCX
├── profiles/               # Perfiles JSON
├── data/                   # Datos de entrada
├── logs/                   # Logs de ejecución
├── backups/                # Backups de templates
├── output/                 # Archivos generados
├── requirements.txt        # Dependencias
├── setup.py               # Script de instalación
├── test_setup.py          # Script de prueba
└── README.md              # Documentación
```

## 🐛 Solución de Problemas

### Error: "Job ID not found"
- Verifica que el job_id existe en los archivos CSV de DataPM
- Ejecuta `python test_setup.py` para verificar la carga de datos

### Error: "Template not found"
- Asegúrate de que existe un archivo .docx en `templates/`
- Verifica que el archivo tiene los placeholders correctos

### Error: "API key not found"
- Verifica que el archivo `.env` existe y tiene las API keys correctas
- Asegúrate de que las API keys son válidas

### Error: "Validation failed"
- Revisa los logs para ver qué validación falló
- Ajusta las configuraciones de validación en `.env`

## 📝 Logs y Debugging

### Ver Logs
Los logs se guardan en `logs/` con timestamp:
```
logs/cvpilot_20250121_143022.log
```

### Modo Verbose
```bash
python src/main.py --job-id 0 --verbose
```

### Logs en Consola
El programa muestra progreso en tiempo real con Rich.

## 🔄 Flujo de Trabajo Recomendado

1. **Preparación**: Configura API keys y template
2. **Prueba**: Ejecuta con `--dry-run` para verificar
3. **Generación**: Ejecuta sin `--dry-run` para generar CV
4. **Revisión**: Revisa el CV generado en `output/`
5. **Ajustes**: Modifica perfil o template si es necesario
6. **Repetición**: Genera CVs para otros trabajos

## 📞 Soporte

Para problemas o preguntas:
1. Revisa los logs en `logs/`
2. Ejecuta `python test_setup.py`
3. Verifica la configuración en `.env`
4. Consulta la documentación en `README.md`
