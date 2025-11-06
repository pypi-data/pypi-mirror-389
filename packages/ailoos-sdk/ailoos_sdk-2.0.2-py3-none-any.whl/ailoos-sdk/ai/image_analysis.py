"""
Ailoos Python SDK - Image Analysis Module
Análisis de imágenes usando modelos de IA de Ailoos
"""

from typing import Dict, List, Optional, Any, Union
from ..core.client import AiloosClient
from ..core.exceptions import ModelError, ValidationError


class ImageAnalyzer:
    """
    Analizador de imágenes usando modelos de Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        model (str): Modelo a usar (default: multimodal-vision)
    """

    def __init__(self, client: AiloosClient, model: str = "multimodal-vision"):
        self.client = client
        self.model = model

    def analyze_image(
        self,
        image_url: str,
        task: str = "describe",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analizar imagen

        Args:
            image_url (str): URL de la imagen a analizar
            task (str): Tipo de análisis ('describe', 'classify', 'detect', 'segment')
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Resultado del análisis

        Raises:
            ValidationError: Si los parámetros son inválidos
            ModelError: Si hay error en el modelo
        """
        if not image_url or not isinstance(image_url, str):
            raise ValidationError("Image URL must be a non-empty string")

        valid_tasks = ['describe', 'classify', 'detect', 'segment', 'caption', 'ocr']
        if task not in valid_tasks:
            raise ValidationError(f"Task must be one of: {', '.join(valid_tasks)}")

        data = {
            'image_url': image_url,
            'task': task,
            'model': self.model,
            **kwargs
        }

        try:
            return self.client.analyze_image(**data)
        except Exception as e:
            raise ModelError(f"Image analysis failed: {str(e)}")

    def describe_image(
        self,
        image_url: str,
        max_length: int = 100,
        language: str = "es",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Describir imagen en lenguaje natural

        Args:
            image_url (str): URL de la imagen
            max_length (int): Longitud máxima de la descripción
            language (str): Idioma de la descripción
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Descripción de la imagen
        """
        return self.analyze_image(
            image_url,
            task="describe",
            max_length=max_length,
            language=language,
            **kwargs
        )

    def classify_image(
        self,
        image_url: str,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Clasificar imagen en categorías

        Args:
            image_url (str): URL de la imagen
            categories (List[str]): Categorías específicas (opcional)
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Clasificación de la imagen
        """
        data = {'task': 'classify'}
        if categories:
            data['categories'] = categories

        return self.analyze_image(image_url, **data, **kwargs)

    def detect_objects(
        self,
        image_url: str,
        confidence_threshold: float = 0.5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Detectar objetos en imagen

        Args:
            image_url (str): URL de la imagen
            confidence_threshold (float): Umbral de confianza (0.0-1.0)
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Objetos detectados con coordenadas
        """
        if not (0 <= confidence_threshold <= 1):
            raise ValidationError("Confidence threshold must be between 0 and 1")

        return self.analyze_image(
            image_url,
            task="detect",
            confidence_threshold=confidence_threshold,
            **kwargs
        )

    def segment_image(
        self,
        image_url: str,
        mode: str = "semantic",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Segmentar imagen

        Args:
            image_url (str): URL de la imagen
            mode (str): Modo de segmentación ('semantic', 'instance', 'panoptic')
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Máscara de segmentación
        """
        valid_modes = ['semantic', 'instance', 'panoptic']
        if mode not in valid_modes:
            raise ValidationError(f"Mode must be one of: {', '.join(valid_modes)}")

        return self.analyze_image(
            image_url,
            task="segment",
            mode=mode,
            **kwargs
        )

    def extract_text(
        self,
        image_url: str,
        languages: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extraer texto de imagen (OCR)

        Args:
            image_url (str): URL de la imagen
            languages (List[str]): Idiomas a detectar (opcional)
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Texto extraído con posiciones
        """
        data = {'task': 'ocr'}
        if languages:
            data['languages'] = languages

        return self.analyze_image(image_url, **data, **kwargs)

    def generate_caption(
        self,
        image_url: str,
        style: str = "natural",
        max_length: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generar caption para imagen

        Args:
            image_url (str): URL de la imagen
            style (str): Estilo del caption ('natural', 'formal', 'creative')
            max_length (int): Longitud máxima del caption
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Caption generado
        """
        valid_styles = ['natural', 'formal', 'creative', 'technical']
        if style not in valid_styles:
            raise ValidationError(f"Style must be one of: {', '.join(valid_styles)}")

        return self.analyze_image(
            image_url,
            task="caption",
            style=style,
            max_length=max_length,
            **kwargs
        )

    def analyze_multiple_images(
        self,
        image_urls: List[str],
        task: str = "describe",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Analizar múltiples imágenes

        Args:
            image_urls (List[str]): Lista de URLs de imágenes
            task (str): Tipo de análisis
            **kwargs: Parámetros adicionales

        Returns:
            List[Dict[str, Any]]: Lista de resultados
        """
        results = []
        for url in image_urls:
            try:
                result = self.analyze_image(url, task=task, **kwargs)
                results.append(result)
            except Exception as e:
                results.append({
                    'error': str(e),
                    'image_url': url
                })
        return results

    def compare_images(
        self,
        image_url1: str,
        image_url2: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Comparar dos imágenes

        Args:
            image_url1 (str): URL de la primera imagen
            image_url2 (str): URL de la segunda imagen
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Análisis de similitud y diferencias
        """
        # En una implementación real, esto podría requerir un endpoint específico
        # Por ahora, analizamos ambas imágenes por separado
        result1 = self.describe_image(image_url1, **kwargs)
        result2 = self.describe_image(image_url2, **kwargs)

        return {
            'image1_analysis': result1,
            'image2_analysis': result2,
            'comparison': {
                'similarity_score': 0.0,  # Placeholder
                'differences': []  # Placeholder
            }
        }

    def detect_faces(
        self,
        image_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Detectar rostros en imagen

        Args:
            image_url (str): URL de la imagen
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Rostros detectados con coordenadas y atributos
        """
        return self.analyze_image(
            image_url,
            task="detect",
            object_type="face",
            **kwargs
        )

    def analyze_colors(
        self,
        image_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analizar paleta de colores de imagen

        Args:
            image_url (str): URL de la imagen
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Análisis de colores dominante
        """
        return self.analyze_image(
            image_url,
            task="analyze",
            analysis_type="colors",
            **kwargs
        )

    def detect_emotions(
        self,
        image_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Detectar emociones en rostros

        Args:
            image_url (str): URL de la imagen
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Emociones detectadas
        """
        return self.analyze_image(
            image_url,
            task="detect",
            object_type="emotion",
            **kwargs
        )

    def set_model(self, model: str) -> None:
        """
        Cambiar modelo activo

        Args:
            model (str): Nombre del nuevo modelo
        """
        self.model = model

    def get_available_models(self) -> List[str]:
        """
        Obtener lista de modelos disponibles

        Returns:
            List[str]: Lista de modelos de visión
        """
        # En una implementación real, esto consultaría la API
        return [
            "multimodal-vision",
            "image-classifier-v2",
            "object-detector-v3",
            "segmentation-model",
            "ocr-engine"
        ]