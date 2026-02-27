# 🧩 NeuroPi (Autism Learning Hub)

✨ **An interactive, accessible desktop and embedded application designed to support autistic individuals and those with learning differences through specialized games, communication tools, and daily planners.**

---

## 🌟 Key Features

*   **📱 Interactive Dashboard**
    A central hub displaying the current time, daily progress, and upcoming scheduled tasks/events in a visually appealing and easy-to-understand format.
*   **🗣️ AAC Communication Board**
    An Augmentative and Alternative Communication (AAC) system equipped with Text-to-Speech (TTS) capabilities. It empowers non-verbal users to construct sentences by combining category-based icon buttons, letting the device speak for them.
*   **📅 Visual Scheduler & Admin Panel**
    Users or caretakers can easily create, manage, and track daily routines, events, and tasks visually to provide structure throughout the day.
*   **🎮 Therapeutic Games Hub**
    A suite of specialized mini-games designed for cognitive and emotional development:
    *   **Emotion Practice**: Uses computer vision to help users practice recognizing and mimicking different facial expressions.
    *   **Memory Match**: A cognitive game to improve memory retention and focus.
    *   **Routine Game**: Uses visual sequencing to teach daily activities (like brushing teeth or getting dressed).
    *   **Smart Bubbles**: A calming, sensory-friendly interactive game.

---

## 🛠️ Technology Stack

*   **GUI Framework:** [Kivy](https://kivy.org/) (Cross-platform Python UI framework)
*   **Database:** SQLite managed via **SQLAlchemy** ORM
*   **Computer Vision & AI:** **OpenCV**, **MediaPipe**, **TensorFlow** (For interactive vision-based games)
*   **Text-to-Speech:** `pyttsx3` / Windows SAPI
*   **Deployment:** Docker & Docker Compose configured for standard Linux and Raspberry Pi

---

## 🚀 Getting Started

### Prerequisites

Ensure you have **Python 3.8+** installed on your system.

### Option 1: Native Local Installation (Windows/Mac/Linux)

1.  **Open a terminal/command prompt** in the project directory.
2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You may want to use a virtual environment like `venv` or `conda`)*
3.  **Run the application:**
    ```bash
    python main.py
    ```
    *💡 On the very first run, the app will automatically generate the local database (`neuropi.db`) and seed it with basic AAC categories and sample events!*

### Option 2: Docker Setup (Ideal for Raspberry Pi / Kiosk Mode)

NeuroPi comes with complete Docker support for easy, isolated deployment. 

To build and start the container:
```bash
docker compose up -d --build
```

**⚠️ Important Docker GUI Note:**
Because NeuroPi is a visual Kivy application, running it via Docker requires passing display server permissions (like X11) and hardware access to the container. 
👉 **Please read the [Kivy Docker Guide](KIVY_DOCKER_GUIDE.md) and [Docker Readme](DOCKER_README.md) for detailed instructions on getting the interface to show up from a Docker container.**

---

## 📁 Project Structure

```text
📂 NeuroPi/
 ├── 📄 main.py               # Main Kivy application entry point & core screens
 ├── 📄 layout.kv             # Kivy interface design and styling rules
 ├── 📄 models.py             # Database architecture and schemas
 ├── 📄 requirements.txt      # Python dependencies list
 ├── 📂 assets/               # Images, UI icons, and visual resources
 ├── 📂 games/                # Implementations of the mini-games (emotions, memory, etc.)
 ├── 📂 models/               # Pre-trained AI/ML models for Mediapipe/TensorFlow
 ├── 📂 instance/             # Persistent storage volume used by Docker
 └── 📄 neuropi.db            # Auto-generated SQLite Database (Created on first run)
```

## 📷 Hardware Acceleration & Camera Access
If you are using the computer vision modules (Emotions / Smart Bubbles), ensure that your webcam is connected and accessible. 

*If running in Docker*, the default `docker-compose.yml` maps `/dev/video0`. If your camera uses a different port, update the `devices` mapping in the compose file accordingly.

---
*Built to make learning more accessible, structured, and engaging.* 💙
