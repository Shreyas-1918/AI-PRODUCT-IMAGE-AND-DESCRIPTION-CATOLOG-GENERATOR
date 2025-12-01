import os
import replicate

# Configure Replicate API
os.environ["REPLICATE_API_TOKEN"] = "r8_RJmZNsOpNc06QEa2oM5TUX3VHvFZpFC1qweQZ"
client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

def generate_product_image(prompt: str):
    """
    Generates product images from a text prompt using Flux / Replicate API.
    Returns: list of image URLs (strings)
    """

    # Call Flux model on Replicate
    output = client.run(
        "black-forest-labs/flux-schnell",  # change if using different model
        input={"prompt": prompt}
    )

    # 🔑 FIX: Convert all outputs into plain strings
    # If Replicate returns FileOutput objects, convert them
    image_urls = [str(out) for out in output]

    return image_urls
