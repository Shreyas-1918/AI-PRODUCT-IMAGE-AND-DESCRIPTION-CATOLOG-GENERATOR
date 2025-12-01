# AI Product Image & Description Catalog Generator

**NEO-GENESIS** is an AI-powered application designed to generate high-quality product images and detailed descriptions. It features a modern, cyberpunk-inspired interface and leverages state-of-the-art AI models (Flux for images, Gemini for text) to create a premium cataloging experience.

## Features

*   **Dual Interface:**
    *   **Desktop App:** A sleek, fullscreen `customtkinter` application with a "glassmorphism" design.
    *   **Web App:** A Flask-based web interface for remote access and ease of use.
*   **AI Image Generation:** Uses **Flux (via Replicate)** to generate photorealistic product images based on text prompts.
*   **AI Description Generation:** Uses **Google Gemini** to create detailed product descriptions and feature lists.
*   **AI Verification:** Includes a local verification module (CLIP-based) to ensure generated images match the text description.
*   **Gallery & Archive:** Automatically saves generated images and metadata to a local gallery.
*   **Premium UI:** Dark mode, neon accents, and smooth animations.

## Prerequisites

Before running the application, ensure you have the following:

1.  **Python 3.8+** installed.
2.  **API Keys:**
    *   **Replicate API Token:** For Flux image generation.
    *   **Google Gemini API Key:** For text description generation.

## Installation

1.  **Clone the repository** (or download the source code).
2.  **Install dependencies:**
    Open a terminal/command prompt in the project folder and run:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The application currently uses hardcoded API keys in the scripts. For security and functionality, you should update these with your own keys or set them as environment variables.

*   **Google Gemini Key:**
    *   Open `gd2.py`.
    *   Update line 3: `genai.configure(api_key="YOUR_GEMINI_KEY")`
*   **Replicate API Token:**
    *   Open `flux_image_gen.py`.
    *   Update line 5: `os.environ["REPLICATE_API_TOKEN"] = "YOUR_REPLICATE_TOKEN"`

> **Note:** It is recommended to use environment variables for API keys in a production environment.

## Usage

### Option 1: Desktop Application

The desktop app provides the most immersive experience.

1.  Run the application:
    ```bash
    python app.py
    ```
2.  **Interface Controls:**
    *   **Input:** Enter your product vision (e.g., "Cyberpunk Sneakers, Neon Drone").
    *   **AI Verification:** Toggle the switch to enable/disable image verification (requires local models).
    *   **Initialize Generation:** Click to start the process.
    *   **Access Archives:** Opens the generated gallery in your browser.
    *   **Fullscreen:** Press `Esc` or `F11` to toggle fullscreen.

### Option 2: Web Application

The web app allows you to use the tool via a browser.

1.  Run the server:
    ```bash
    python web_app_v2.py
    ```
2.  Open your browser and navigate to:
    ```
    http://127.0.0.1:5000
    ```
3.  Use the web interface to generate and view products.

## Project Structure

*   `app.py`: Main desktop application entry point.
*   `web_app_v2.py`: Flask web application entry point.
*   `gd2.py`: Handles Google Gemini API calls for text descriptions.
*   `flux_image_gen.py`: Handles Replicate API calls for image generation.
*   `verify_image.py`: Logic for verifying image-text alignment.
*   `generated_images/`: Directory where outputs are saved.
*   `assets/`: Contains UI assets (backgrounds, etc.).

## Troubleshooting

*   **Verification Module Failed:** If you see this message, ensure you have `torch` and `transformers` installed and that your machine supports the required models. The app will still work but without verification.
*   **API Errors:** Check your API keys in `gd2.py` and `flux_image_gen.py`. Ensure you have sufficient credits/quota.