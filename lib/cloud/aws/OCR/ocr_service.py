import boto3
import os

from config.config import settings

class OCRService:
    def __init__(self):
        self.textract_client = boto3.client(
            'textract',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

    def extract_text_from_file(self, file_path):
        """
        Extrae el texto de un archivo (imagen) utilizando AWS Textract.
        """
        with open(file_path, "rb") as document:
            image_bytes = document.read()

        try:
            response = self.textract_client.detect_document_text(Document={'Bytes': image_bytes})
            
            extracted_text = ""
            for item in response.get("Blocks", []):
                if item["BlockType"] == "LINE":
                    extracted_text += item["Text"] + "\n"
                    
            return extracted_text.strip()
        except Exception as e:
            print(f"Error al realizar OCR: {e}")
            return ""
