"""
Ailoos Python SDK - Text Generation Module
Generación de texto usando modelos de IA de Ailoos
"""

from typing import Dict, List, Optional, Any, Union
from ..core.client import AiloosClient
from ..core.exceptions import ModelError, ValidationError


class TextGenerator:
    """
    Generador de texto usando modelos de Ailoos

    Args:
        client (AiloosClient): Cliente de Ailoos autenticado
        model (str): Modelo a usar (default: empiorio-lm-2b)
    """

    def __init__(self, client: AiloosClient, model: str = "empiorio-lm-2b"):
        self.client = client
        self.model = model

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generar texto a partir de un prompt

        Args:
            prompt (str): Texto de entrada
            max_tokens (int): Máximo número de tokens a generar
            temperature (float): Control de aleatoriedad (0.0-2.0)
            top_p (float): Nucleus sampling (0.0-1.0)
            frequency_penalty (float): Penalización por frecuencia
            presence_penalty (float): Penalización por presencia
            stop_sequences (List[str]): Secuencias para detener generación
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Respuesta con texto generado y metadatos

        Raises:
            ValidationError: Si los parámetros son inválidos
            ModelError: Si hay error en el modelo
        """
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("Prompt must be a non-empty string")

        if not (0 <= temperature <= 2):
            raise ValidationError("Temperature must be between 0 and 2")

        if not (0 <= top_p <= 1):
            raise ValidationError("top_p must be between 0 and 1")

        if max_tokens <= 0:
            raise ValidationError("max_tokens must be positive")

        data = {
            'prompt': prompt,
            'model': self.model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'frequency_penalty': frequency_penalty,
            'presence_penalty': presence_penalty,
            **kwargs
        }

        if stop_sequences:
            data['stop_sequences'] = stop_sequences

        try:
            return self.client.generate_text(**data)
        except Exception as e:
            raise ModelError(f"Text generation failed: {str(e)}")

    def generate_multiple(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generar texto para múltiples prompts

        Args:
            prompts (List[str]): Lista de prompts
            **kwargs: Parámetros de generación

        Returns:
            List[Dict[str, Any]]: Lista de respuestas
        """
        results = []
        for prompt in prompts:
            try:
                result = self.generate(prompt, **kwargs)
                results.append(result)
            except Exception as e:
                results.append({
                    'error': str(e),
                    'prompt': prompt
                })
        return results

    def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> Any:
        """
        Generar texto con streaming (si soportado por el modelo)

        Args:
            prompt (str): Texto de entrada
            **kwargs: Parámetros de generación

        Returns:
            Generator: Generador de tokens
        """
        # Implementar streaming si el backend lo soporta
        data = {
            'prompt': prompt,
            'model': self.model,
            'stream': True,
            **kwargs
        }

        try:
            response = self.client.generate_text(**data)
            # Aquí se implementaría el parsing del stream
            # Por ahora retornamos la respuesta completa
            return response
        except Exception as e:
            raise ModelError(f"Streaming generation failed: {str(e)}")

    def complete_text(
        self,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Completar texto dado

        Args:
            text (str): Texto a completar
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Texto completado
        """
        return self.generate(text, **kwargs)

    def summarize(
        self,
        text: str,
        max_length: int = 150,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Resumir texto

        Args:
            text (str): Texto a resumir
            max_length (int): Longitud máxima del resumen
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Resumen generado
        """
        prompt = f"Por favor resume el siguiente texto en máximo {max_length} palabras:\n\n{text}\n\nResumen:"
        return self.generate(prompt, max_tokens=max_length, **kwargs)

    def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Traducir texto

        Args:
            text (str): Texto a traducir
            target_language (str): Idioma destino
            source_language (str): Idioma origen (auto para detección automática)
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Texto traducido
        """
        if source_language == "auto":
            prompt = f"Traduce el siguiente texto al {target_language}:\n\n{text}\n\nTraducción:"
        else:
            prompt = f"Traduce el siguiente texto del {source_language} al {target_language}:\n\n{text}\n\nTraducción:"

        return self.generate(prompt, **kwargs)

    def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Responder pregunta

        Args:
            question (str): Pregunta a responder
            context (str): Contexto adicional
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Respuesta generada
        """
        if context:
            prompt = f"Contexto: {context}\n\nPregunta: {question}\n\nRespuesta:"
        else:
            prompt = f"Pregunta: {question}\n\nRespuesta:"

        return self.generate(prompt, **kwargs)

    def generate_code(
        self,
        description: str,
        language: str = "python",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generar código

        Args:
            description (str): Descripción de lo que debe hacer el código
            language (str): Lenguaje de programación
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Código generado
        """
        prompt = f"Genera código en {language} que {description}\n\nCódigo:"
        return self.generate(prompt, **kwargs)

    def analyze_sentiment(
        self,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analizar sentimiento de texto

        Args:
            text (str): Texto a analizar
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Análisis de sentimiento
        """
        prompt = f"Analiza el sentimiento del siguiente texto. Responde solo con: positivo, negativo, o neutral.\n\nTexto: {text}\n\nSentimiento:"
        return self.generate(prompt, max_tokens=10, **kwargs)

    def extract_keywords(
        self,
        text: str,
        num_keywords: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extraer palabras clave

        Args:
            text (str): Texto del que extraer keywords
            num_keywords (int): Número de keywords a extraer
            **kwargs: Parámetros adicionales

        Returns:
            Dict[str, Any]: Keywords extraídos
        """
        prompt = f"Extrae {num_keywords} palabras clave principales del siguiente texto:\n\n{text}\n\nPalabras clave:"
        return self.generate(prompt, max_tokens=50, **kwargs)

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
            List[str]: Lista de modelos
        """
        # En una implementación real, esto consultaría la API
        return [
            "empiorio-lm-2b",
            "empiorio-lm-7b",
            "empiorio-lm-13b",
            "empiorio-lm-30b"
        ]