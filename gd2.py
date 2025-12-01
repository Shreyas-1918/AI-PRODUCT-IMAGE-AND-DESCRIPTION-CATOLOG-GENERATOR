import google.generativeai as genai

genai.configure(api_key="AIzaSyDv4gr_JtJyWiGx2Di_e2y8CtYM1eehuEY")

def get_product_descriptions(product_name):
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt1 = (
        f"Describe {product_name} in extreme detail for a high-quality product photography generation. "
        "Focus on lighting, materials, textures, colors, and camera angle. "
        "Describe the neon/cyberpunk aesthetic if applicable, or a premium studio setting. "
        "The description should be a single, dense paragraph suitable for a text-to-image model like Flux. "
        "Do not include bullet points."
    )

    prompt2 = (
        f"List only the key features of {product_name} in a single concise paragraph. "
        "Do NOT include introductions, explanations, disclaimers, or assumptions. "
        "Do NOT say anything like 'here are the features' or 'it is impossible'. "
        "Only output the features text."
    )

    response1 = model.generate_content(prompt1)
    response2 = model.generate_content(prompt2)

    def extract_text(response):
        if response and response.candidates:
            parts = response.candidates[0].content.parts
            return "".join([p.text for p in parts if p.text]) if parts else ""
        return ""

    return extract_text(response1), extract_text(response2)
