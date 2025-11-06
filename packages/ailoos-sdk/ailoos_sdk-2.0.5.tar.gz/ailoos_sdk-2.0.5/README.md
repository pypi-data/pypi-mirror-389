# Ailoos Python SDK

Python SDK for the Ailoos distributed AI platform - Sovereign AI for the decentralized future.

## 🚀 Installation

### Basic Installation
```bash
pip install ailoos-sdk
```

### Installation with GPU Support
```bash
pip install 'ailoos-sdk[gpu]'
```

### Installation with Quantum Computing Support
```bash
pip install 'ailoos-sdk[quantum]'
```
⚠️ **Note**: On macOS ARM64, qiskit-aer may fail to compile. Use cloud simulators instead:
- IBM Quantum Experience
- Amazon Braket
- Azure Quantum

### Installation with Blockchain Support
```bash
pip install 'ailoos-sdk[blockchain]'
```

### Full Development Installation
```bash
pip install 'ailoos-sdk[dev]'
```

## 📖 Guides and Tutorials

### Basic Tutorials
- **Getting Started** - First steps with Ailoos SDK
- **Text Generation** - Generate text with EmpoorioLM
- **Image Analysis** - Analyze images with multimodal models
- **Multimodal Processing** - Handle text, images, and audio together

### Advanced Tutorials
- **Distributed Training** - Train models across multiple nodes
- **Custom Fine-tuning** - Adapt models to your specific needs
- **Blockchain Integration** - Connect with DracmaS blockchain
- **Quantum Optimization** - Use quantum algorithms for optimization

## 🔧 Quick Start

```python
from ailoos_sdk import AiloosClient

# Initialize client
client = AiloosClient(api_key="your-api-key")

# Generate text
response = client.generate_text("Hello, how are you?")
print(response)

# Start a federated learning session
session = client.create_session(model="empoorio-lm", rounds=5)
print(f"Session created: {session.id}")
```

## 🏗️ Architecture

Ailoos combines:
- **EmpoorioLM**: Advanced GPT-2 based language model
- **Federated Learning**: Privacy-preserving distributed training
- **Blockchain Integration**: DracmaS token rewards system
- **Multi-modal AI**: Text, image, and audio processing
- **Decentralized Infrastructure**: P2P networking and coordination

## 📚 Documentation

- [Full API Reference](https://docs.ailoos.ai/python-sdk/api/)
- [Federated Learning Guide](https://docs.ailoos.ai/python-sdk/federated/)
- [Blockchain Integration](https://docs.ailoos.ai/python-sdk/blockchain/)
- [Quantum Computing](https://docs.ailoos.ai/python-sdk/quantum/)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the Ailoos & Empoorio Ecosystem License Agreement. See the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: https://docs.ailoos.ai
- **Discord**: https://discord.gg/ailoos
- **GitHub Issues**: https://github.com/ailoos/ailoos-python-sdk/issues
- **Email**: support@ailoos.ai

---

**© 2025 Ailoos Technologies & Empoorio Ecosystem. All rights reserved.**