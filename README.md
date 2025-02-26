# MeTTa Rift – Server

> **Note:** This repository contains the server for MeTTa Rift. If you're looking for the client, visit [MeTTa Rift – Client](https://github.com/fluidity-labs/metta-rift-client).

**MeTTa Rift** is a fun and educational text-based RPG that showcases the power of [OpenCog Hyperon](https://hyperon.opencog.org/) and the [MeTTa language](https://metta-lang.dev/). It features a procedurally generated world with advanced reasoning and memory management capabilities. Designed to foster community adoption and engagement, MeTTa Rift serves as an interactive way to explore and expand the utility of MeTTa while immersing players in a dynamic AI-driven experience.

The game includes a built-in console where players can observe all actions taken by MeTTa during gameplay, providing transparency into its decision-making and reasoning process. Additionally, an admin mode allows any query or action to be performed, offering deeper exploration and experimentation with MeTTa’s full capabilities.

## Features

- 🌍 **Procedural Generation** – The game world is dynamically created based on AI-driven rules.
- 🧠 **Advanced Reasoning** – Powered by OpenCog Hyperon for intelligent decision-making.
- 📜 **Memory Management** – NPCs and the environment retain and adapt to past interactions.
- 🎮 **Text-Based Adventure** – A rich, interactive experience where players navigate and shape the world through text commands.
- 🖥️ **Action Console** – Players can view all actions taken by MeTTa during gameplay, providing insight into its reasoning process.
- 🔧 **Admin Mode** – Any user can take control and execute any action, allowing for deeper experimentation with MeTTa's capabilities.

## Getting Started

### Prerequisites
- **Python 3.8+**  
- **pip** (Python package manager)
- **Linux/macOS** (Hyperon is currently not available on Windows)
- [**MeTTa Rift – Client**](https://github.com/fluidity-labs/metta-rift-client)

### Installation

```sh
# Clone the repository
git clone https://github.com/fluidity-labs/metta-rift-server.git
cd metta-rift-server

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## Tech Stack

[MeTTa](https://metta-lang.dev/) (Meta Type Talk) is a multi-paradigm language for declarative and functional computations over knowledge (meta)graphs.

[OpenCog Hyperon](https://hyperon.opencog.org/) is an ambitious open-source project aimed at creating an Artificial General Intelligence (AGI) framework, capable of human-level reasoning and beyond.

## License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.


