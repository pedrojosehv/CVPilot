from docx import Document
import os

def verify_docx_content():
    """Verificar el contenido del DOCX generado para asegurar que los títulos están correctos"""

    # Ruta del archivo más reciente
    docx_path = "output/Project Manager - General - Excel (advanced), Amazon Seller Central, Helium 10/PedroHerrera_PJM_GEN_MP_2025.docx"

    if not os.path.exists(docx_path):
        print(f"❌ El archivo no existe: {docx_path}")
        return

    print(f"✅ Verificando archivo: {docx_path}")
    print("=" * 60)

    try:
        doc = Document(docx_path)
        print("📄 CONTENIDO DEL DOCUMENTO:")
        print("-" * 40)

        found_titles = []

        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()

            if text:
                print(f"[{i}] {text}")

                # Buscar títulos de experiencia
                if any(keyword in text.lower() for keyword in ['specialist', 'analyst', 'manager', 'owner']):
                    # Verificar si es un título de experiencia (tiene fechas)
                    if any(char in text for char in ['/', '-', 'present', '2020', '2021', '2022', '2023']):
                        found_titles.append(text)

        print("\n" + "=" * 60)
        print("🔍 ANÁLISIS DE TÍTULOS:")
        print("-" * 40)

        success_count = 0
        total_titles = 0

        for title in found_titles:
            total_titles += 1
            print(f"\n📋 Título encontrado: '{title}'")

            # Verificar si contiene "Project Manager"
            if "Project Manager" in title:
                print("   ✅ CORRECTO: Contiene 'Project Manager'")
                success_count += 1
            elif "Product Specialist" in title:
                print("   ❌ ERROR: Aún contiene 'Product Specialist'")
            else:
                print("   ❓ DESCONOCIDO: No es ninguno de los títulos esperados")

        print("\n" + "=" * 60)
        print("📊 RESUMEN:")
        print("-" * 40)
        print(f"✅ Títulos correctos: {success_count}")
        print(f"📈 Total títulos: {total_titles}")

        if success_count == 2:
            print("\n🎉 ¡VERIFICACIÓN EXITOSA! Los 2 títulos de experiencia se reemplazaron correctamente.")
        else:
            print(f"\n⚠️  VERIFICACIÓN INCOMPLETA: Se esperaban 2 títulos correctos, se encontraron {success_count}")

    except Exception as e:
        print(f"❌ Error al leer el documento: {e}")

if __name__ == "__main__":
    verify_docx_content()
