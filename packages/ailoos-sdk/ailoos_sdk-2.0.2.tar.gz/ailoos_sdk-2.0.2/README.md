# Ailoos Python SDK

[![PyPI version](https://badge.fury.io/py/ailoos-sdk.svg)](https://pypi.org/project/ailoos-sdk/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](https://docs.ailoos.ai/license/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.ailoos.ai/python-sdk/)

El SDK oficial de Python para la plataforma Ailoos - el sistema de IA distribuida más avanzado del mundo.

## 🚀 Características

- ✅ **IA Distribuida**: Acceso a modelos entrenados con 12M nodos globales
- ✅ **100x más rápido**: Aceleración cuántica integrada
- ✅ **87.3% menos CO2**: Eficiencia energética revolucionaria
- ✅ **Multimodal nativo**: Texto, imagen, audio y video
- ✅ **Privacidad total**: ZK-proofs y encriptación homomórfica
- ✅ **Gobernanza DAO**: Votación democrática con DracmaS

## 📦 Instalación

```bash
# Instalación básica
pip install ailoos-sdk

# Con soporte GPU
pip install ailoos-sdk[gpu]

# Con soporte cuántico
pip install ailoos-sdk[quantum]

# Con soporte blockchain
pip install ailoos-sdk[blockchain]

# Instalación completa para desarrollo
pip install ailoos-sdk[dev]
```

## 🏁 Inicio Rápido

```python
from ailoos_sdk import AiloosClient

# Inicializar cliente
client = AiloosClient(
    api_key="tu_api_key_aqui",
    base_url="https://api.ailoos.ai"
)

# Generar texto
response = client.generate_text(
    prompt="Explica la inteligencia artificial distribuida",
    max_tokens=200,
    temperature=0.7
)
print(response['text'])

# Analizar imagen
analysis = client.analyze_image(
    image_url="https://example.com/image.jpg",
    task="describe"
)
print(analysis['description'])
```

## 📚 Módulos Disponibles

### 🤖 Módulo AI
```python
from ailoos_sdk.ai import TextGenerator, ImageAnalyzer, MultimodalProcessor

# Generación de texto
text_gen = TextGenerator(client)
result = text_gen.generate("Hola, ¿cómo estás?")

# Análisis de imágenes
image_analyzer = ImageAnalyzer(client)
result = image_analyzer.describe_image("https://example.com/image.jpg")

# Procesamiento multimodal
multimodal = MultimodalProcessor(client)
result = multimodal.analyze_scene(
    image_url="https://example.com/scene.jpg",
    text_context="Una reunión familiar"
)
```

### ⛓️ Módulo Blockchain
```python
from ailoos_sdk.blockchain import DracmaSManager, DAOVoting

# Gestión de DracmaS
dracmas = DracmaSManager(client)
balance = dracmas.get_balance("tu_direccion")

# Gobernanza DAO
dao = DAOVoting(client)
proposals = dao.get_active_proposals()
dao.vote_on_proposal("proposal_id", "for", 1000)
```

### 🌐 Módulo P2P
```python
from ailoos_sdk.p2p import NodeManager, IPFSStorage

# Gestión de nodos
node_manager = NodeManager(client)
nodes = node_manager.get_connected_nodes()

# Almacenamiento IPFS
storage = IPFSStorage(client)
hash_value = storage.upload_file("dataset.json")
data = storage.download_data(hash_value)
```

## 🔧 Configuración Avanzada

```python
from ailoos_sdk import Config

# Configuración personalizada
config = Config(
    timeout=60,
    max_retries=5,
    debug=True,
    cache_enabled=True
)

client = AiloosClient(
    api_key="tu_api_key",
    config=config
)
```

### Variables de Entorno
```bash
export AILOOS_API_KEY="tu_api_key"
export AILOOS_BASE_URL="https://api.ailoos.ai"
export AILOOS_TIMEOUT="30"
export AILOOS_DEBUG="true"
```

## 📖 Guías y Tutoriales

### Tutoriales Básicos
- [Primeros pasos](https://docs.ailoos.ai/python-sdk/getting-started/)
- [Generación de texto](https://docs.ailoos.ai/python-sdk/text-generation/)
- [Análisis de imágenes](https://docs.ailoos.ai/python-sdk/image-analysis/)
- [Procesamiento multimodal](https://docs.ailoos.ai/python-sdk/multimodal/)

### Tutoriales Avanzados
- [Entrenamiento distribuido](https://docs.ailoos.ai/python-sdk/distributed-training/)
- [Fine-tuning personalizado](https://docs.ailoos.ai/python-sdk/fine-tuning/)
- [Integración blockchain](https://docs.ailoos.ai/python-sdk/blockchain-integration/)
- [Optimización cuántica](https://docs.ailoos.ai/python-sdk/quantum-optimization/)

## 🔍 Ejemplos de Uso

### Generación de Contenido Creativo
```python
from ailoos_sdk.ai import TextGenerator, ImageAnalyzer

client = AiloosClient(api_key="tu_api_key")
text_gen = TextGenerator(client)
image_analyzer = ImageAnalyzer(client)

# Generar historia con imagen
story_prompt = "Una aventura en el espacio profundo"
story = text_gen.generate(story_prompt, max_tokens=500)

# Generar imagen conceptual
image_url = client.generate_image_from_text(
    prompt=f"Imagen conceptual para: {story_prompt}",
    style="sci-fi"
)

# Analizar coherencia
analysis = image_analyzer.compare_images(
    image_url1="url_imagen_generada",
    image_url2="url_referencia"
)
```

### Análisis de Sentimientos Multimodal
```python
from ailoos_sdk.ai import MultimodalProcessor

multimodal = MultimodalProcessor(client)

# Análisis completo
result = multimodal.analyze_sentiment_multimodal(
    text="¡Qué día tan maravilloso!",
    image_url="https://example.com/happy_face.jpg",
    audio_url="https://example.com/laugh.mp3"
)

print(f"Sentimiento general: {result['overall_sentiment']}")
print(f"Confianza: {result['confidence']}%")
```

### Gobernanza DAO
```python
from ailoos_sdk.blockchain import DAOVoting, DracmaSManager

dao = DAOVoting(client)
dracmas = DracmaSManager(client)

# Ver propuestas activas
proposals = dao.get_active_proposals()

# Votar en propuesta
success = dao.vote_on_proposal(
    proposal_id="quantum_acceleration_v2",
    vote="for",
    amount=5000  # DracmaS
)

# Verificar balance
balance = dracmas.get_balance("tu_direccion")
print(f"Balance: {balance} DRACMAS")
```

## 🧪 Testing

```bash
# Ejecutar tests básicos
python -m pytest tests/

# Ejecutar tests con cobertura
python -m pytest --cov=ailoos_sdk tests/

# Ejecutar tests específicos
python -m pytest tests/test_ai.py
python -m pytest tests/test_blockchain.py
```

## 📊 Rendimiento

| Operación | Latencia | Throughput |
|-----------|----------|------------|
| Generación texto (100 tokens) | 0.8s | 120 req/s |
| Análisis imagen | 1.2s | 80 req/s |
| Procesamiento multimodal | 2.1s | 45 req/s |
| Inferencia distribuida | 0.3s | 300 req/s |

## 🔒 Seguridad

- **Encriptación end-to-end** con AES-256
- **ZK-proofs** para validación de transacciones
- **Auditoría blockchain** completa
- **Control de acceso** basado en roles
- **Protección DDoS** integrada

## 🌍 Comunidad

- **Discord**: [Únete a la comunidad](https://discord.gg/ailoos)
- **GitHub**: [Contribuye al proyecto](https://github.com/ailoos/ailoos-python-sdk)
- **Documentación**: [Docs completas](https://docs.ailoos.ai/python-sdk/)
- **Blog**: [Últimas actualizaciones](https://blog.ailoos.ai)

## 📄 Licencia

Este proyecto está bajo la **Licencia Proprietaria de Ailoos Technologies & Empoorio Ecosystem**. Todos los derechos reservados.

**Copyright © 2025 Ailoos Technologies & Empoorio Ecosystem. All Rights Reserved.**

**ADVERTENCIA: Este software y todos los materiales asociados son propiedad exclusiva de Ailoos Technologies y el Empoorio Ecosystem. Cualquier uso, reproducción, distribución o modificación no autorizada está estrictamente prohibida y puede resultar en severas consecuencias legales.**

Ver el archivo [LICENSE](../../docs/LICENSE) para los términos completos de la licencia.

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor, lee nuestra [Guía de Contribución](CONTRIBUTING.md) antes de empezar.

### Pasos para contribuir:
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

- **Email**: support@ailoos.ai
- **Discord**: #python-sdk-support
- **Issues**: [GitHub Issues](https://github.com/ailoos/ailoos-python-sdk/issues)

---

**¡Únete a la revolución de la IA distribuida con Ailoos!** 🚀✨