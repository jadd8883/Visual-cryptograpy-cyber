
from PIL import Image
import numpy as np


def generate_shares(input_path, share1_path, share2_path):
    # Read and convert the secret image to grayscale
    image = Image.open(input_path).convert("L")

    # Limit image size to keep processing manageable
    image.thumbnail((500, 500))

    # 1 = black secret pixel, 0 = white secret pixel
    secret = np.array(image) < 128

    height, width = secret.shape

    # Random pattern: one black and one white subpixel
    pattern = np.random.randint(0, 2, (height, width)).astype(bool)

    # Each source pixel expands into two subpixels
    share1 = np.zeros((height, width * 2), dtype=bool)
    share2 = np.zeros((height, width * 2), dtype=bool)

    # Assign each pixel's pattern to the two shares
    share1[:, 0::2] = pattern
    share1[:, 1::2] = ~pattern

    # White secret pixels use the same pattern.
    # Black secret pixels use the complementary pattern.
    share2[:, 0::2] = np.where(secret, ~pattern, pattern)
    share2[:, 1::2] = np.where(secret, pattern, ~pattern)

    # Convert black masks to displayable grayscale images
    Image.fromarray(
        np.where(share1, 0, 255).astype(np.uint8)
    ).save(share1_path)

    Image.fromarray(
        np.where(share2, 0, 255).astype(np.uint8)
    ).save(share2_path)


def reconstruct_secret(share1_path, share2_path, output_path):
    first = np.array(Image.open(share1_path).convert("L"))
    second = np.array(Image.open(share2_path).convert("L"))

    if first.shape != second.shape:
        raise ValueError("Both shares must have the same dimensions.")

    # True means a black subpixel
    black1 = first < 128
    black2 = second < 128

    # Superposition: a subpixel is black if either share is black
    combined = black1 | black2

    result = np.where(combined, 0, 255).astype(np.uint8)
    Image.fromarray(result).save(output_path)
