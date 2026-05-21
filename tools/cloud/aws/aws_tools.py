from langchain_core.tools import tool
import os
import sys

from lib.cloud.aws.storage.s3_service import S3Service
from lib.cloud.aws.OCR.ocr_service import OCRService

@tool
def upload_file_to_s3(file_path: str, object_name: str = None) -> str:
    """
    Sube un archivo local al bucket de almacenamiento S3 de AWS.
    
    Args:
        file_path (str): Ruta local del archivo a subir.
        object_name (str, opcional): El nombre que tendrá el archivo en el bucket S3. Si no se provee, se usará el nombre original del archivo.
        
    Returns:
        str: Un mensaje indicando si el archivo se subió con éxito o si ocurrió un error.
    """
    try:
        s3_service = S3Service()
        success = s3_service.upload_file(file_path, object_name)
        if success:
            dest_name = object_name if object_name else os.path.basename(file_path)
            return f"Archivo {file_path} subido con éxito a S3 con el nombre '{dest_name}'."
        else:
            return f"No se pudo subir el archivo {file_path} a S3."
    except Exception as e:
        return f"Error al subir archivo a S3: {str(e)}"

@tool
def download_file_from_s3(object_name: str, file_path: str) -> str:
    """
    Descarga un archivo desde el bucket de almacenamiento S3 de AWS a una ruta local.
    
    Args:
        object_name (str): El nombre del objeto/archivo dentro del bucket S3.
        file_path (str): La ruta local donde se guardará el archivo descargado.
        
    Returns:
        str: Un mensaje indicando si la descarga fue exitosa o si ocurrió un error.
    """
    try:
        s3_service = S3Service()
        success = s3_service.download_file(object_name, file_path)
        if success:
            return f"Archivo '{object_name}' descargado con éxito y guardado en {file_path}."
        else:
            return f"No se pudo descargar el archivo '{object_name}' de S3."
    except Exception as e:
        return f"Error al descargar archivo de S3: {str(e)}"

@tool
def extract_text_with_ocr(file_path: str) -> str:
    """
    Realiza OCR (Reconocimiento Óptico de Caracteres) utilizando AWS Textract para extraer el texto de un archivo de imagen o documento local.
    
    Args:
        file_path (str): Ruta local del archivo de imagen o PDF que se procesará para extraer texto.
        
    Returns:
        str: El texto extraído del documento o un mensaje de error si el proceso falló.
    """
    try:
        ocr_service = OCRService()
        text = ocr_service.extract_text_from_file(file_path)
        if text:
            return text
        else:
            return "No se pudo extraer texto del archivo o el documento no contiene texto legible."
    except Exception as e:
        return f"Error al realizar el OCR del archivo: {str(e)}"
