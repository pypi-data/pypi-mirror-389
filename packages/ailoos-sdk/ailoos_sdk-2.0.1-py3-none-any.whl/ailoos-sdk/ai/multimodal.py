"""
Ailoos Python SDK - Multimodal Module
Procesamiento multimodal (texto + imagen + audio)
"""

from typing import Dict, List, Optional, Any, Union
from ..core.client import AiloosClient
from ..core.exceptions import ModelError, ValidationError


class MultimodalProcessor:
    """
    Procesador multimodal para combinar texto, imagen y audio

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        model (str): Modelo multimodal a usar
    """

    def __init__(self, client: AiloosClient, model: str = "multimodal-unified"):
        self.client = client
        self.model = model

    def process_multimodal(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        task: str = "analyze",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Procesar entrada multimodal

        Args:
            text (str): Texto de entrada
            image_url (str): URL de imagen
            audio_url (str): URL de audio
            task (str): Tipo de tarea ('analyze', 'generate', 'translate', 'summarize')
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Resultado del procesamiento multimodal

        Raises:
            ValidationError: Si no se proporciona al menos una entrada
            ModelError: Si hay error en el procesamiento
        """
        if not any([text, image_url, audio_url]):
            raise ValidationError("At least one input (text, image, or audio) must be provided")

        valid_tasks = ['analyze', 'generate', 'translate', 'summarize', 'describe', 'question_answer']
        if task not in valid_tasks:
            raise ValidationError(f"Task must be one of: {', '.join(valid_tasks)}")

        data = {
            'task': task,
            'model': self.model,
            **kwargs
        }

        if text:
            data['text'] = text
        if image_url:
            data['image_url'] = image_url
        if audio_url:
            data['audio_url'] = audio_url

        try:
            return self.client.process_multimodal(**data)
        except Exception as e:
            raise ModelError(f"Multimodal processing failed: {str(e)}")

    def analyze_scene(
        self,
        image_url: str,
        text_context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analizar escena combinando imagen y texto

        Args:
            image_url (str): URL de la imagen
            text_context (str): Contexto textual adicional
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Análisis de la escena
        """
        return self.process_multimodal(
            text=text_context,
            image_url=image_url,
            task="analyze",
            analysis_type="scene",
            **kwargs
        )

    def generate_image_from_text(
        self,
        prompt: str,
        style: str = "realistic",
        size: str = "512x512",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generar imagen desde texto

        Args:
            prompt (str): Descripción de la imagen
            style (str): Estilo de la imagen
            size (str): Tamaño de la imagen
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: URL de la imagen generada
        """
        return self.process_multimodal(
            text=prompt,
            task="generate",
            modality="image",
            style=style,
            size=size,
            **kwargs
        )

    def transcribe_audio(
        self,
        audio_url: str,
        language: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribir audio a texto

        Args:
            audio_url (str): URL del audio
            language (str): Idioma del audio
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Texto transcrito
        """
        return self.process_multimodal(
            audio_url=audio_url,
            task="transcribe",
            language=language,
            **kwargs
        )

    def generate_audio_from_text(
        self,
        text: str,
        voice: str = "neutral",
        language: str = "es",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generar audio desde texto (TTS)

        Args:
            text (str): Texto a convertir
            voice (str): Tipo de voz
            language (str): Idioma
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: URL del audio generado
        """
        return self.process_multimodal(
            text=text,
            task="generate",
            modality="audio",
            voice=voice,
            language=language,
            **kwargs
        )

    def translate_multimodal(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        target_language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Traducir contenido multimodal

        Args:
            text (str): Texto a traducir
            image_url (str): URL de imagen con texto
            target_language (str): Idioma destino
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Contenido traducido
        """
        return self.process_multimodal(
            text=text,
            image_url=image_url,
            task="translate",
            target_language=target_language,
            **kwargs
        )

    def describe_image_audio(
        self,
        image_url: str,
        audio_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Describir imagen con contexto de audio

        Args:
            image_url (str): URL de la imagen
            audio_url (str): URL de audio contextual
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Descripción combinada
        """
        return self.process_multimodal(
            image_url=image_url,
            audio_url=audio_url,
            task="describe",
            modality="combined",
            **kwargs
        )

    def question_answer_multimodal(
        self,
        question: str,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Responder preguntas usando múltiples modalidades

        Args:
            question (str): Pregunta a responder
            image_url (str): URL de imagen relevante
            audio_url (str): URL de audio relevante
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Respuesta generada
        """
        return self.process_multimodal(
            text=question,
            image_url=image_url,
            audio_url=audio_url,
            task="question_answer",
            **kwargs
        )

    def summarize_multimodal(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        max_length: int = 200,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Resumir contenido multimodal

        Args:
            text (str): Texto a resumir
            image_url (str): URL de imagen a incluir
            audio_url (str): URL de audio a incluir
            max_length (int): Longitud máxima del resumen
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Resumen multimodal
        """
        return self.process_multimodal(
            text=text,
            image_url=image_url,
            audio_url=audio_url,
            task="summarize",
            max_length=max_length,
            **kwargs
        )

    def detect_emotions_multimodal(
        self,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        text: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Detectar emociones usando múltiples modalidades

        Args:
            image_url (str): URL de imagen facial
            audio_url (str): URL de audio con voz
            text (str): Texto a analizar
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Análisis de emociones
        """
        return self.process_multimodal(
            text=text,
            image_url=image_url,
            audio_url=audio_url,
            task="analyze",
            analysis_type="emotions",
            **kwargs
        )

    def generate_story_from_image(
        self,
        image_url: str,
        story_length: str = "short",
        genre: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generar historia basada en imagen

        Args:
            image_url (str): URL de la imagen
            story_length (str): Longitud de la historia
            genre (str): Género de la historia
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Historia generada
        """
        return self.process_multimodal(
            image_url=image_url,
            task="generate",
            content_type="story",
            story_length=story_length,
            genre=genre,
            **kwargs
        )

    def analyze_sentiment_multimodal(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analizar sentimiento usando múltiples modalidades

        Args:
            text (str): Texto a analizar
            image_url (str): URL de imagen
            audio_url (str): URL de audio
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Análisis de sentimiento multimodal
        """
        return self.process_multimodal(
            text=text,
            image_url=image_url,
            audio_url=audio_url,
            task="analyze",
            analysis_type="sentiment",
            **kwargs
        )

    def create_presentation(
        self,
        topic: str,
        image_urls: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Crear presentación multimodal

        Args:
            topic (str): Tema de la presentación
            image_urls (List[str]): URLs de imágenes para incluir
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Estructura de presentación
        """
        data = {
            'text': topic,
            'task': 'generate',
            'content_type': 'presentation',
            **kwargs
        }

        if image_urls:
            data['image_urls'] = image_urls

        try:
            return self.client._make_request('POST', '/api/ai/multimodal/generate', json=data)
        except Exception as e:
            raise ModelError(f"Presentation generation failed: {str(e)}")

    def set_model(self, model: str) -> None:
        """
        Cambiar modelo multimodal activo

        Args:
            model (str): Nombre del nuevo modelo
        """
        self.model = model

    def get_available_models(self) -> List[str]:
        """
        Obtener lista de modelos multimodales disponibles

        Returns:
            List[str]: Lista de modelos
        """
        # En una implementación real, esto consultaría la API
        return [
            "multimodal-unified",
            "vision-language-v2",
            "audio-visual-fusion",
            "cross-modal-large"
        ]