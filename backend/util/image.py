from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

from util.embedding import get_embedding

# this is the entry point
def image_to_embedding(file_path: str):
    caption = generateImageCaption(file_path=file_path)
    embedding = get_embedding(caption)


def generateImageCaption(file_path: str) -> str:
    model_name = "Salesforce/blip-image-captioning-base" # around 1 GB download size
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    image = Image.open(file_path).convert("RGB")

    inputs = processor(images=image, return_tensors="pt").to(model.device, torch.float16)
    generated_ids = model.generate(**inputs, max_new_tokens=30) # more token, longer caption
    caption = processor.decode(generated_ids[0], skip_special_tokens=True)

    # print(caption)
    return caption

# generateImageCaption("test_files/image/jail_cell.jpg")


