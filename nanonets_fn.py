import modal

app = modal.App("nanonets-server")

inference_image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "huggingface_hub[hf_transfer]==0.34.3",
    "transformers==4.54.1",
    "pillow==11.3.0",
    "torch==2.7.1",
    "torchvision==0.22.1",
    "accelerate==1.9.0",
)

MODEL_NAME = "nanonets/Nanonets-OCR-s"

def setup():
    import warnings

    from transformers import AutoTokenizer, AutoProcessor, AutoModelForImageTextToText

    with warnings.catch_warnings():  # filter noisy warnings from GOT modeling code
        warnings.simplefilter("ignore")
        
        model = AutoModelForImageTextToText.from_pretrained(
            MODEL_NAME, 
            torch_dtype="auto", 
            device_map="auto", 
            # attn_implementation="flash_attention_2"
        )
        model.eval()

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        processor = AutoProcessor.from_pretrained(MODEL_NAME)

    return model, processor

model_cache = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)

MODEL_CACHE_PATH = "/root/models"
inference_image = inference_image.env(
    {"HF_HUB_CACHE": MODEL_CACHE_PATH, "HF_HUB_ENABLE_HF_TRANSFER": "1"}
)

@app.function(
    gpu="l40s",
    retries=3,
    volumes={MODEL_CACHE_PATH: model_cache},
    image=inference_image,
)
def receipt_parser(image: bytes) -> str:
    from tempfile import NamedTemporaryFile
    from PIL import Image
    import io

    model, processor = setup()

    # Convert bytes to PIL Image
    image_pil = Image.open(io.BytesIO(image))

    print(f"Running OCR on image with size: {image_pil.size}")

    prompt = """Extract all the the items purchased as shown in the receipt above together with their price and quantity if have. Display output in tabular format"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
            {"type": "image", "image": image_pil},
            {"type": "text", "text": prompt},
        ]},
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    print(f"Prompt for OCR: {text}")
    inputs = processor(text=[text], images=[image_pil], padding=True, return_tensors="pt")
    inputs = inputs.to(model.device)
    
    output_ids = model.generate(**inputs, max_new_tokens=4096, do_sample=False)
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
    
    output_text = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
    print(f"Generated text: {output_text}")
    return output_text[0]
