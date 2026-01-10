from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
from pathlib import Path

def generateImageSummarization(file_path):

    # Make sure file is actually an image
    extension = Path(file_path).suffix
    if extension not in [".png", ".jpg", ".jpeg"]:
        return ""
    
    model = AutoModelForCausalLM.from_pretrained(
        "vikhyatk/moondream2",
        revision="2025-06-21",
        trust_remote_code=True,
        device_map={"": "mps"}  # mps on Apple Silicon
    )

    image = Image.open(file_path)
    image_encoding = model.encode_image(image)
    return model.query(image_encoding, "Summarize what's in this image")