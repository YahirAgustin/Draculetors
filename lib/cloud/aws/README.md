# Módulo AWS (Amazon Web Services)

Este módulo proporciona una integración sencilla con servicios en la nube de AWS utilizando el SDK `boto3`. Está diseñado para facilitar el almacenamiento de archivos y la extracción de texto mediante inteligencia artificial.

---

## 1. ¿Qué es AWS?

**Amazon Web Services (AWS)** es la plataforma de computación en la nube más completa y adoptada del mundo. Ofrece más de 200 servicios integrales de infraestructura, base de datos, análisis, redes, móvil, herramientas para desarrolladores, IoT, seguridad y servicios empresariales a nivel global. En este proyecto, utilizamos AWS para delegar tareas pesadas como el almacenamiento seguro y el procesamiento inteligente de imágenes.

---

## 2. Servicios de AWS Implementados

Este módulo expone dos capacidades principales:

1. **Almacenamiento (Amazon S3):**
   * **Servicio:** Amazon Simple Storage Service (S3).
   * **Descripción:** Un servicio de almacenamiento de objetos que ofrece escalabilidad, disponibilidad de datos, seguridad y rendimiento líderes en el sector.
   * **Implementación:** Ubicada en [s3_service.py](storage/s3_service.py). Permite subir y descargar cualquier tipo de archivo directamente a un bucket configurado.

2. **OCR (Amazon Textract):**
   * **Servicio:** Amazon Textract.
   * **Descripción:** Un servicio de aprendizaje automático (Machine Learning) que extrae automáticamente texto impreso, manuscrito y datos de prácticamente cualquier documento o imagen sin necesidad de configurar flujos manuales de OCR.
   * **Implementación:** Ubicada en [ocr_service.py](OCR/ocr_service.py). Procesa imágenes de facturas, tickets, etc., abstrayendo la llamada a la API y devolviendo directamente el texto estructurado por líneas.

---

## 3. ¿Cómo configurar AWS para utilizar estos servicios?

Para utilizar este módulo, necesitas tener una cuenta de AWS y configurar tus credenciales en el archivo `.env` del proyecto.

### Paso 1: Configurar en AWS Console
1. **Crear un Bucket de S3:** 
   * Ve a la consola de S3 y crea un nuevo bucket. Guarda el nombre del bucket para tu archivo `.env`.
2. **Crear un Usuario IAM:**
   * Ve al servicio IAM (Identity and Access Management) y crea un nuevo usuario con acceso programático (Access Key y Secret Access Key).
3. **Asignar Políticas de Permisos:**
   * Para **S3**: Asigna una política que permita acciones de lectura y escritura en tu bucket (como `AmazonS3FullAccess` o una política personalizada restrictiva).
   * Para **Textract**: Asigna la política `AmazonTextractFullAccess` o crea una personalizada que permita la acción `textract:DetectDocumentText`.

### Paso 2: Configurar las Variables de Entorno
Asegúrate de tener un archivo `.env` en la raíz del proyecto con la siguiente estructura:

```env
AWS_ACCESS_KEY_ID=tu_access_key_id
AWS_SECRET_ACCESS_KEY=tu_secret_access_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=nombre_de_tu_bucket_s3
```

---

## 4. 🚀 ¡Importante para el Hackathon!

> [!TIP]
> **¡El uso de tecnologías en la nube suma puntos para el Hackathon!**
> Implementar soluciones escalables y robustas basadas en la nube como Amazon Web Services demuestra una visión técnica profesional y capacidad de integración de arquitectura moderna. Utilizar estos servicios de almacenamiento y procesamiento de datos le dará un empuje extra a tu proyecto frente a los jueces.
