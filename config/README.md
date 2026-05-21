## ¿Como usar este modulo?

Este modulo esta diseñado para ser una clase singleton que almacena todas las variables de entorno necesarias para la aplicacion. Para usarlo, simplemente importa la instancia global 'settings' y accede a sus atributos.

# Ejemplo de uso 

```python
from config.config import settings

# Acceder a una variable de entorno
api_key = settings.OPENAI_API_KEY
aws_region = settings.AWS_REGION

print(f"La región de AWS es: {aws_region}")
```
