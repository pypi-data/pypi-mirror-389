"""
Ailoos Python SDK - Image Analysis Module
Análisis de imágenes usando modelos de IA de Ailoos
"""

import asyncio
import concurrent.futures
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
        max_concurrent: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Analizar múltiples imágenes concurrentemente

        Args:
            image_urls (List[str]): Lista de URLs de imágenes
            task (str): Tipo de análisis
            max_concurrent (int): Máximo número de análisis concurrentes
            **kwargs: Parámetros adicionales

        Returns:
            List[Dict[str, Any]]: Lista de resultados
        """
        async def analyze_single_image(url: str) -> Dict[str, Any]:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.analyze_image, url, task, kwargs
                )
                return result
            except Exception as e:
                return {
                    'error': str(e),
                    'image_url': url,
                    'task': task
                }

        async def analyze_batch() -> List[Dict[str, Any]]:
            semaphore = asyncio.Semaphore(max_concurrent)
            results = []

            async def analyze_with_semaphore(url: str) -> Dict[str, Any]:
                async with semaphore:
                    return await analyze_single_image(url)

            tasks = [analyze_with_semaphore(url) for url in image_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convertir excepciones a diccionarios de error
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'error': str(result),
                        'image_url': image_urls[i],
                        'task': task
                    })
                else:
                    processed_results.append(result)

            return processed_results

        # Ejecutar análisis concurrente
        try:
            return asyncio.run(analyze_batch())
        except RuntimeError:
            # Si ya estamos en un loop de eventos, usar approach síncrono
            return self._analyze_multiple_images_sync(image_urls, task, max_concurrent, **kwargs)

    def _analyze_multiple_images_sync(
        self,
        image_urls: List[str],
        task: str,
        max_concurrent: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Análisis síncrono de múltiples imágenes con concurrencia limitada"""
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Crear futures para cada análisis
            futures = [
                executor.submit(self.analyze_image, url, task, **kwargs)
                for url in image_urls
            ]

            # Recopilar resultados
            for future, url in zip(futures, image_urls):
                try:
                    result = future.result(timeout=30)  # 30 segundos timeout
                    results.append(result)
                except concurrent.futures.TimeoutError:
                    results.append({
                        'error': 'Analysis timeout',
                        'image_url': url,
                        'task': task
                    })
                except Exception as e:
                    results.append({
                        'error': str(e),
                        'image_url': url,
                        'task': task
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
        # Analizar ambas imágenes
        result1 = self.describe_image(image_url1, **kwargs)
        result2 = self.describe_image(image_url2, **kwargs)

        # Calcular similitud basada en descripciones
        similarity_score = self._calculate_description_similarity(
            result1.get('description', ''),
            result2.get('description', '')
        )

        # Identificar diferencias
        differences = self._identify_image_differences(result1, result2)

        return {
            'image1_analysis': result1,
            'image2_analysis': result2,
            'comparison': {
                'similarity_score': similarity_score,
                'similarity_percentage': round(similarity_score * 100, 2),
                'differences': differences,
                'are_similar': similarity_score > 0.7
            }
        }

    def _calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """Calcular similitud entre dos descripciones usando Jaccard similarity"""
        if not desc1 or not desc2:
            return 0.0

        # Convertir a sets de palabras
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())

        # Calcular similitud de Jaccard
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _identify_image_differences(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> List[str]:
        """Identificar diferencias entre análisis de imágenes"""
        differences = []

        desc1 = result1.get('description', '').lower()
        desc2 = result2.get('description', '').lower()

        # Palabras clave comunes
        common_keywords = {
            'person', 'people', 'man', 'woman', 'child', 'dog', 'cat', 'car', 'house',
            'tree', 'sky', 'water', 'mountain', 'building', 'street', 'room', 'food'
        }

        words1 = set(desc1.split())
        words2 = set(desc2.split())

        # Encontrar elementos únicos en cada imagen
        unique_to_1 = words1.intersection(common_keywords) - words2.intersection(common_keywords)
        unique_to_2 = words2.intersection(common_keywords) - words1.intersection(common_keywords)

        if unique_to_1:
            differences.append(f"Image 1 has: {', '.join(unique_to_1)}")
        if unique_to_2:
            differences.append(f"Image 2 has: {', '.join(unique_to_2)}")

        # Comparar colores si están disponibles
        colors1 = result1.get('colors', [])
        colors2 = result2.get('colors', [])

        if colors1 and colors2:
            color_diff = set(colors1) - set(colors2)
            if color_diff:
                differences.append(f"Different colors: {', '.join(color_diff)}")

        # Comparar objetos detectados si están disponibles
        objects1 = result1.get('objects', [])
        objects2 = result2.get('objects', [])

        if objects1 and objects2:
            obj_diff = set(objects1) - set(objects2)
            if obj_diff:
                differences.append(f"Different objects: {', '.join(obj_diff)}")

        return differences

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
        try:
            # Consultar modelos disponibles desde la API
            response = self.client._make_request('GET', '/models/vision')

            if response and 'models' in response:
                return response['models']
            else:
                # Fallback a lista conocida si la API no responde
                return [
                    "multimodal-vision",
                    "image-classifier-v2",
                    "object-detector-v3",
                    "segmentation-model",
                    "ocr-engine",
                    "face-detector-v1",
                    "emotion-analyzer",
                    "color-analyzer",
                    "caption-generator"
                ]
        except Exception as e:
            # En caso de error de conexión, devolver lista conocida
            return [
                "multimodal-vision",
                "image-classifier-v2",
                "object-detector-v3",
                "segmentation-model",
                "ocr-engine"
            ]