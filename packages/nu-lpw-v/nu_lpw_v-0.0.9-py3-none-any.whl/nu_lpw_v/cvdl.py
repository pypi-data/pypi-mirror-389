def doc():
  print(r"""
| Function | Description |
|:--------:|-------------|
| p1() | Image resizing (÷2, ÷3), grayscale, translation, rotation |
| p2() | Log transform, gamma transform, piecewise transformation, bit-plane slicing, negative imaging |
| p3() | Spatial filtering: averaging, sharpening, min-max-median filters |
| p4() | Histogram equalization and histogram matching |
| p5() | Fourier transform: ideal, Gaussian, Butterworth |
| p6() | Feature extraction: 16-part descriptor, SIFT |
| p7() | MNIST digit classification (CNN) |
| p8() | Transfer learning (MobileNetV3-Large) |
| p9() | Image segmentation (U-Net) |
| p10() | Object detection (YOLO) |
""")
def p1():
    print(r"""
#ORIGINAL TO SMALL
# ===== CELL 1 =====
import cv2
import numpy as np
from google.colab.patches import cv2_imshow
original_image = cv2.imread('/content/lena.png')
small_image = np.zeros((256, 256, 3), dtype=np.uint8)

for i in range(0, original_image.shape[0], 2):
  for j in range(0, original_image.shape[1], 2):
    for k in range(0, 3):
      small_image[i//2][j//2][k] = np.mean(original_image[i:i+2, j:j+2, k])

print("Original Image:")
cv2_imshow(original_image)

print("Small Image:")
cv2_imshow(small_image)

#ORIGINAL TO LARGE
# ===== CELL 2 =====
import cv2
import numpy as np
from google.colab.patches import cv2_imshow

original_image = cv2.imread('/content/lena.png')

height, width = original_image.shape[:2]

large_image = np.zeros((height*2, width*2, 3), dtype=np.uint8)

for i in range(height):
    for j in range(width):
        for k in range(3):
            pixel = original_image[i, j, k]
            large_image[2*i, 2*j, k] = pixel
            large_image[2*i+1, 2*j, k] = pixel
            large_image[2*i, 2*j+1, k] = pixel
            large_image[2*i+1, 2*j+1, k] = pixel

print("Original Image:")
cv2_imshow(original_image)

print("Large Image:")
cv2_imshow(large_image)

#ORIGINAL TO GRAYSCALE
# ===== CELL 3 =====
import cv2
import numpy as np
from google.colab.patches import cv2_imshow
original_image = cv2.imread('/content/lena.png')
gray_image = np.zeros((512, 512), dtype=np.uint8)

for i in range(0, original_image.shape[0]):
  for j in range(0, original_image.shape[1]):
      gray_image[i][j] = np.mean(original_image[i, j, 0:3])
print("Original Image:")
cv2_imshow(original_image)

print("GrayScale Image:")
cv2_imshow(gray_image)

#ORIGINAL TO 1/3
# ===== CELL 4 =====
import cv2
import numpy as np
from google.colab.patches import cv2_imshow
original_image = cv2.imread('/content/lena.png')
small_image = np.zeros((171, 171, 3), dtype=np.uint8)

for i in range(0, original_image.shape[0], 3):
  for j in range(0, original_image.shape[1], 3):
    for k in range(0, 3):
      small_image[i//3][j//3][k] = np.mean(original_image[i:i+3, j:j+3, k])

print("Original Image:")
cv2_imshow(original_image)

print("Small Image:")
cv2_imshow(small_image)

#TRANSLATE
# ===== CELL 1 =====
import cv2
import numpy as np
import math
import cv2
from matplotlib import pyplot as plt

# Display image using matplotlib
def show_image(img, title='Image'):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.imshow(img_rgb)
    plt.title(title)
    plt.axis('off')
    plt.show()

# Load the original image
original_image = cv2.imread('lena.png')
height, width, channels = original_image.shape

# Translation amounts
tx, ty = 50, 30

# Create blank image with same size
translated_image = np.zeros_like(original_image)

# Manually copy pixels to new location
for y in range(height):
    for x in range(width):
        new_x = x + tx
        new_y = y + ty
        if 0 <= new_x < width and 0 <= new_y < height:
            translated_image[new_y, new_x] = original_image[y, x]

print("Original Image:")
show_image(original_image)

print("Translated Image:")
show_image(translated_image)


#ROTATE
# ===== CELL 2 =====
import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

# Load image
img = cv2.imread('lena.png')
h, w = img.shape[:2]
cx, cy = w // 2, h // 2  

angle = 45  
theta = math.radians(angle)
cos_theta = math.cos(theta)
sin_theta = math.sin(theta)

rotated = np.zeros_like(img)

for y in range(h):
    for x in range(w):
        x0 = x - cx
        y0 = y - cy

        orig_x = int(cx + x0 * cos_theta + y0 * sin_theta)
        orig_y = int(cy - x0 * sin_theta + y0 * cos_theta)

        if 0 <= orig_x < w and 0 <= orig_y < h:
            rotated[y, x] = img[orig_y, orig_x]

def show(img, title):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.imshow(img)
    plt.title(title)
    plt.axis('off')
    plt.show()

show(img, "Original")
show(rotated, "Rotated 45°")

""")
    
def p2():
    print(r"""
#LOG_TRANSFORM
# ===== CELL 1 =====
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

image_path = "images_woods\log_transform.jpg"
img = Image.open(image_path).convert("L")
# img = plt.imread("images_woods\log_transform.jpg").cmap('gray')
img_array = np.array(img)
print(img_array.shape)
print(img_array.min(), img_array.max())


c = 1

log_transformed_manual = np.zeros_like(img_array, dtype=np.float32)

rows, cols = img_array.shape
for i in range(rows):
    for j in range(cols):
        r = img_array[i, j]
        log_transformed_manual[i, j] = (c * np.log1p(r))

# Apply normalization to [0, 255] range
log_transformed_normalized = (log_transformed_manual - log_transformed_manual.min()) / (
    log_transformed_manual.max() - log_transformed_manual.min()
) * 255

plt.figure(figsize=(6, 6))
plt.imshow(log_transformed_normalized, cmap='gray', vmin=0, vmax=255)
plt.title(f"Log Transform using Loop (c = {c}) - Normalized")
plt.axis('off')
plt.show()

print("Original range:", log_transformed_manual.min(), log_transformed_manual.max())
print("Normalized range:", log_transformed_normalized.min(), log_transformed_normalized.max())

#GAMMA_TRANSFORM
# ===== CELL 4 =====
c = 1
gamma = 0.4
epsilon = 1e-1000000

gamma_transform_manual = np.zeros_like(img_array, dtype=np.float32)

rows, cols = img_array.shape
for i in range(rows):
    for j in range(cols):
        r = img_array[i, j]
        gamma_transform_manual[i, j] = c * ((r + epsilon) ** gamma)

# Apply normalization to [0, 255] range
gamma_transform_normalized = (gamma_transform_manual - gamma_transform_manual.min()) / (
    gamma_transform_manual.max() - gamma_transform_manual.min()
) * 255

plt.figure(figsize=(6, 6))
plt.imshow(gamma_transform_normalized, cmap='gray', vmin=0, vmax=255)
plt.title(f"Gamma Transform (c = {c}, gamma = {gamma}) - Normalized")
plt.axis('off')
plt.show()

print("Original range - Min:", gamma_transform_manual.min(), "Max:", gamma_transform_manual.max())
print("Normalized range - Min:", gamma_transform_normalized.min(), "Max:", gamma_transform_normalized.max())

image_path = "images_woods\\fig3.09(a).jpg"
img = Image.open(image_path).convert("L")
# img = plt.imread("images_woods\log_transform.jpg").cmap('gray')
img_array = np.array(img)
print(img_array.shape)
print(img_array.min(), img_array.max())


#GAMMA_TRANSFORM
# ===== CELL 6 =====
c = 1
gamma = 4
epsilon = 1e-1000000

gamma_transform_manual = np.zeros_like(img_array, dtype=np.float32)

rows, cols = img_array.shape
for i in range(rows):
    for j in range(cols):
        r = img_array[i, j]
        gamma_transform_manual[i, j] = c * ((r + epsilon) ** gamma)

# Apply normalization to [0, 255] range
gamma_transform_normalized = (gamma_transform_manual - gamma_transform_manual.min()) / (
    gamma_transform_manual.max() - gamma_transform_manual.min()
) * 255

plt.figure(figsize=(6, 6))
plt.imshow(gamma_transform_normalized, cmap='gray', vmin=0, vmax=255)
plt.title(f"Gamma Transform (c = {c}, gamma = {gamma}) - Normalized")
plt.axis('off')
plt.show()

print("Original range - Min:", gamma_transform_manual.min(), "Max:", gamma_transform_manual.max())
print("Normalized range - Min:", gamma_transform_normalized.min(), "Max:", gamma_transform_normalized.max())

#PIECEWISE_TRANSFORM
# ===== CELL 7 =====
import numpy as np
import matplotlib.pyplot as plt

# Parameters
r1, r2 = 128, 254
s1, s2 = 0, 128

# Slopes
# alpha = s1 / r1 if r1 != 0 else 0
# beta = (s2 - s1) / (r2 - r1)
# gamma = (255 - s2) / (255 - r2)

# Output array
piecewise_transform = np.zeros_like(img_array, dtype=np.float32)

rmin =img_array.min()
rmax = img_array.max()

rows, cols = img_array.shape
for i in range(rows):
    for j in range(cols):
        r = img_array[i, j]
        if r < r1:
            piecewise_transform[i, j] = int((s1 / r1) * r)
        elif r1 <= r <= r2:
            piecewise_transform[i, j] = int(((s2 - s1) / (r2 - r1)) * (r - r1) + s1)
        else:
            piecewise_transform[i, j] = int(((255 - s2) / (255 - r2)) * (r - r2) + s2)
        # r = img_array[i, j]
        # piecewise_transform[i,j] = ((255 *(r-rmin))/(rmax-rmin))

# Clip to valid range
# piecewise_transform = np.clip(piecewise_transform, 0, 255)

plt.figure(figsize=(6, 6))
plt.imshow(piecewise_transform, cmap='gray')
plt.title(f"Piecewise Contrast Stretching [{r1}-{r2}] → [{s1}-{s2}]")
plt.axis('off')
plt.show()

print("Range after stretching: Min:", piecewise_transform.min(), "Max:", piecewise_transform.max())


#BITPLANE_SLICING
# ===== CELL 8 =====
import numpy as np
import matplotlib.pyplot as plt
import cv2

# Read grayscale image
# img_array = cv2.imread('your_image.jpg', cv2.IMREAD_GRAYSCALE)

rows, cols = img_array.shape

# List to store bit planes
bit_planes = []

for bit in range(8):
    # Extract the bit plane using bitwise operations
    plane = (img_array >> bit) & 1
    # Multiply by 255 to make it visible (0 or 255)
    plane = (plane * 255).astype(np.uint8)
    bit_planes.append(plane)

# Plot all planes
plt.figure(figsize=(12, 6))
for i, plane in enumerate(bit_planes):
    plt.subplot(2, 4, i+1)
    plt.imshow(plane, cmap='gray')
    plt.title(f"Bit Plane {i}")
    plt.axis('off')

plt.tight_layout()
plt.show()


# ===== CELL 1 =====
#IMAGE_INVERSION
import numpy as np;
import cv2;
import matplotlib.pyplot as plt;

# ===== CELL 2 =====
original_image = cv2.imread('./images_woods/fig3.04(a).jpg', cv2.IMREAD_GRAYSCALE)


processed_image = 255 - original_image



plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(original_image, cmap='gray')
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(processed_image, cmap='gray')
plt.title('Negative Image')
plt.axis('off')

plt.tight_layout()
plt.show()
""")
    
def p3():
    print(r"""
# ===== CELL 1 =====
import numpy as np;
import cv2;
import matplotlib.pyplot as plt;

# ===== CELL 2 =====
#AVERAGING_FILTER
original_image = cv2.imread('images_woods/fig3.04(a).jpg', cv2.IMREAD_GRAYSCALE)

filter_size = 3  
avg_filter = np.ones((filter_size, filter_size), dtype=np.float32) / (filter_size**2)

height, width = original_image.shape

k = filter_size // 2

processed_image = np.zeros_like(original_image)

for i in range(k, height - k):
    for j in range(k, width - k):
        cutout = original_image[i - k:i + k + 1, j - k:j + k + 1]
        processed_image[i, j] = np.sum(cutout * avg_filter)

plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(original_image, cmap='gray')
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(processed_image, cmap='gray')
plt.title(f'{filter_size}x{filter_size}     Averaged Image')
plt.axis('off')

plt.tight_layout()
plt.show()


# ===== CELL 3 =====
#SHARPEN_IMAGE
original_image = cv2.imread('./images_woods/fig3.04(a).jpg', cv2.IMREAD_GRAYSCALE)

laplacian_kernel = np.array([[-1, -1, -1],
                             [-1, 8, -1],
                             [-1, -1, -1]])

height, width = original_image.shape
k = laplacian_kernel.shape[0] // 2

laplacian_image = np.zeros_like(original_image, dtype=np.int32)
laplacian_image_log = np.zeros_like(original_image, dtype=np.int32)
sharpened_image = np.zeros_like(original_image, dtype=np.uint8)

for i in range(k, height - k):
    for j in range(k, width - k):
        cutout = original_image[i - k:i + k + 1, j - k:j + k + 1]
        value = np.sum(cutout * laplacian_kernel)
        laplacian_image[i, j] = value
        # laplacian_image_log[i, j] = np.log1p(np.abs(value))

sharpened_image = np.clip(original_image + laplacian_image, 0, 255).astype(np.uint8)

laplacian_image_log = np.log1p(np.abs(laplacian_image)).astype(np.float32)

# Normalize to 0–255 for display
laplacian_image_log = (255 * (laplacian_image_log - laplacian_image_log.min()) /
                       (laplacian_image_log.max() - laplacian_image_log.min())).astype(np.uint8)

plt.figure(figsize=(20, 5))

plt.subplot(1, 4, 1)
plt.imshow(original_image, cmap='gray')
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 4, 2)
plt.imshow(laplacian_image, cmap='gray')
plt.title('Laplacian Edges')
plt.axis('off')

plt.subplot(1, 4, 3)
plt.imshow(laplacian_image_log, cmap='gray')
plt.title('Laplacian Edges (log-scaled)')
plt.axis('off')

plt.subplot(1, 4, 4)
plt.imshow(sharpened_image, cmap='gray')
plt.title('Sharpened Image')
plt.axis('off')

plt.tight_layout()
plt.show()


# ===== CELL 4 =====
#MIN_MAX_MEDIAN_FILTER
original_image = cv2.imread('./images_woods/eight.tif', cv2.IMREAD_GRAYSCALE)

filter_size = 3
k = filter_size // 2

height, width = original_image.shape

min_filtered = np.zeros_like(original_image)
median_filtered = np.zeros_like(original_image)
max_filtered = np.zeros_like(original_image)

for i in range(k, height - k):
    for j in range(k, width - k):
        window = original_image[i - k:i + k + 1, j - k:j + k + 1].flatten()

        min_filtered[i, j] = np.min(window)

        median_filtered[i, j] = np.median(window)

        max_filtered[i, j] = np.max(window)

plt.figure(figsize=(15, 8))

plt.subplot(2, 2, 1)
plt.imshow(original_image, cmap='gray')
plt.title('Original Image')
plt.axis('off')

plt.subplot(2, 2, 2)
plt.imshow(min_filtered, cmap='gray')
plt.title(f'Min Filter ({filter_size}x{filter_size})')
plt.axis('off')

plt.subplot(2, 2, 3)
plt.imshow(median_filtered, cmap='gray')
plt.title(f'Median Filter ({filter_size}x{filter_size})')
plt.axis('off')

plt.subplot(2, 2, 4)
plt.imshow(max_filtered, cmap='gray')
plt.title(f'Max Filter ({filter_size}x{filter_size})')
plt.axis('off')

plt.tight_layout()
plt.show()

""")
    
def p4():
  print(r"""
# ===== CELL 1 =====
#HISTOGRAM_EQUALIZATION
import cv2
import numpy as np
import matplotlib.pyplot as plt

img = cv2.imread('./image.jpg', cv2.IMREAD_GRAYSCALE)

hist = np.zeros(256, dtype=int)
for value in img.ravel():
    hist[value] += 1

num_pixels = img.size
pdf = hist / num_pixels

cdf = np.cumsum(pdf)  

equalized_values = np.round(cdf * 255).astype('uint8')

equalized_img = equalized_values[img]

plt.figure(figsize=(10,5))

plt.subplot(1,2,1)
plt.imshow(img, cmap='gray')
plt.title('Original Image')
plt.axis('off')

plt.subplot(1,2,2)
plt.imshow(equalized_img, cmap='gray')
plt.title('Equalized Image')
plt.axis('off')

plt.show()


# ===== CELL 2 =====
plt.figure(figsize=(10,5))

plt.subplot(1,2,1)
plt.hist(img.ravel(), bins=256, range=(0,255), color='gray')
plt.title("Original Histogram")

plt.subplot(1,2,2)
plt.hist(equalized_img.ravel(), bins=256, range=(0,255), color='gray')
plt.title("Equalized Histogram")

plt.show()


# ===== CELL 3 =====
#HISTOGRAM_MATCHING
import cv2
import numpy as np

ref_image = equalized_img
original_image = img

processed_image = np.zeros_like(img)

hist_ref = np.zeros(256, dtype=int)
for value in ref_image.ravel():
    hist_ref[value] += 1

pdf_ref = hist_ref / ref_image.size
cdf_ref = np.cumsum(pdf_ref)

hist_original = np.zeros(256, dtype=int)
for value in original_image.ravel():
    hist_original[value] += 1

pdf_original = hist_original / original_image.size
cdf_original = np.cumsum(pdf_original)

transfer_function = np.zeros(256, dtype=np.uint8)

for i in range(256):
    j = 0
    while j < 256 and cdf_original[i] > cdf_ref[j]:
        j += 1
    if j == 256:
        j = 255
    transfer_function[i] = j

for i in range(img.shape[0]):
    for j in range(img.shape[1]):
        processed_image[i, j] = transfer_function[original_image[i, j]]


plt.imshow(processed_image, cmap='gray')


# ===== CELL 4 =====
import matplotlib.pyplot as plt

# Plot PDFs
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(pdf_original, color='blue', label='Original PDF')
plt.plot(pdf_ref, color='red', linestyle='-', label='Reference PDF')
plt.title("PDF Comparison")
plt.xlabel("Pixel Intensity")
plt.ylabel("Probability")
plt.legend()

# Plot CDFs
plt.subplot(1, 2, 2)
plt.plot(cdf_original, color='blue', label='Original CDF')
plt.plot(cdf_ref, color='red', linestyle='-', label='Reference CDF')
plt.title("CDF Comparison")
plt.xlabel("Pixel Intensity")
plt.ylabel("Cumulative Probability")
plt.legend()

plt.tight_layout()
plt.show()
""")
  
def p5():
  print(r"""
# ===== CELL 1 =====
# 1) convert the image to signed form ---> signed_image = original_image
# 2) (-1)**(i+j)                      ---> signed_image = signed_image * (-1)**(i+j)
# 3) fourier_transform()              ---> fourier_image = fft2(signed_image)
# 4) form the mask                    ---> mask
# 5) mask * fourier_image             ---> fourier_transform = mask * fourier_image
# 6) inverse fourier transform        ---> np.fft.ifft2()

# ===== CELL 2 =====


#IDEAL_FILTER
# from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import cv2
from numpy.fft import fft2
# from google.colab.patches import cv2_imshow

import cv2
import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft2, ifft2, fftshift

# 1. Read image
original_image = cv2.imread('./lena.png', cv2.IMREAD_GRAYSCALE)

# 2. Signed image (convert dtype)
signed_image = np.array(original_image, dtype=np.int32)

# 3. Multiply by (-1)^(i+j)
signed_image_1 = np.zeros_like(original_image, dtype=np.int32)
for i in range(signed_image.shape[0]):
    for j in range(signed_image.shape[1]):
        signed_image_1[i][j] = signed_image[i][j] * ((-1)**(i+j))

# 4. Fourier transform
fourier_image = fft2(signed_image_1)

# 5. Mask creation (low-pass circular)
rows, cols = original_image.shape
radius = 30
mask = np.zeros((rows, cols), dtype=np.uint8)
center_x, center_y = rows // 2, cols // 2
for i in range(rows):
    for j in range(cols):
        distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
        if distance < radius:
            mask[i, j] = 1

# 6. Apply mask in Fourier domain
fourier_transformed = mask * fourier_image

# 7. Inverse Fourier Transform
filtered_image = ifft2(fourier_transformed)
filtered_image = np.abs(filtered_image)

plt.figure(figsize=(15,10))

plt.subplot(2,4,1)
plt.title("Original Image")
plt.imshow(original_image, cmap='gray')
plt.axis("off")

plt.subplot(2,4,2)
plt.title("Signed Image")
plt.imshow(signed_image, cmap='gray')
plt.axis("off")

plt.subplot(2,4,3)
plt.title("Signed Image (-1)^(i+j)")
plt.imshow(signed_image_1, cmap='gray')
plt.axis("off")

plt.subplot(2,4,4)
plt.title("Fourier Spectrum")
plt.imshow(np.log(1+np.abs(fftshift(fourier_image))), cmap='gray')
plt.axis("off")

plt.subplot(2,4,5)
plt.title("Mask")
plt.imshow(mask, cmap='gray')
plt.axis("off")

plt.subplot(2,4,6)
plt.title("Masked Fourier Spectrum")
plt.imshow(np.log(1+np.abs(fftshift(fourier_transformed))), cmap='gray')
plt.axis("off")

plt.subplot(2,4,7)
plt.title("Filtered Image")
plt.imshow(filtered_image, cmap='gray')
plt.axis("off")

plt.tight_layout()
plt.show()


# ===== CELL 4 =====
#GAUSSIAN_FILTER
import cv2
import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft2, ifft2, fftshift

# 1. Read image
original_image = cv2.imread('./lena.png', cv2.IMREAD_GRAYSCALE)

# 2. Signed image
signed_image = np.array(original_image, dtype=np.int32)

# 3. Multiply by (-1)^(i+j)
signed_image_1 = np.zeros_like(original_image, dtype=np.int32)
for i in range(signed_image.shape[0]):
    for j in range(signed_image.shape[1]):
        signed_image_1[i][j] = signed_image[i][j] * ((-1)**(i+j))

# 4. Fourier transform
fourier_image = fft2(signed_image_1)

# 5. Gaussian Low-pass Filter
rows, cols = original_image.shape
center_x, center_y = rows // 2, cols // 2
D0 = 30  # cutoff frequency
mask = np.zeros((rows, cols), dtype=np.float32)
for i in range(rows):
    for j in range(cols):
        distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
        mask[i, j] = np.exp(-(distance**2) / (2 * (D0**2)))

# 6. Apply mask
fourier_transformed = mask * fourier_image

# 7. Inverse Fourier Transform
filtered_image = ifft2(fourier_transformed)
filtered_image = np.abs(filtered_image)

plt.figure(figsize=(15,10))

plt.subplot(2,4,1)
plt.title("Original Image")
plt.imshow(original_image, cmap='gray')
plt.axis("off")

plt.subplot(2,4,2)
plt.title("Signed Image")
plt.imshow(signed_image, cmap='gray')
plt.axis("off")

plt.subplot(2,4,3)
plt.title("Signed Image (-1)^(i+j)")
plt.imshow(signed_image_1, cmap='gray')
plt.axis("off")

plt.subplot(2,4,4)
plt.title("Fourier Spectrum")
plt.imshow(np.log(1+np.abs(fftshift(fourier_image))), cmap='gray')
plt.axis("off")

plt.subplot(2,4,5)
plt.title("Gaussian Mask")
plt.imshow(mask, cmap='gray')
plt.axis("off")

plt.subplot(2,4,6)
plt.title("Masked Fourier Spectrum")
plt.imshow(np.log(1+np.abs(fftshift(fourier_transformed))), cmap='gray')
plt.axis("off")

plt.subplot(2,4,7)
plt.title("Filtered Image (Gaussian LPF)")
plt.imshow(filtered_image, cmap='gray')
plt.axis("off")

plt.tight_layout()
plt.show()


# ===== CELL 5 =====
#BUTTERWORTH_FILTER
import cv2
import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft2, ifft2, fftshift

# 1. Read image
original_image = cv2.imread('./lena.png', cv2.IMREAD_GRAYSCALE)

# 2. Signed image
signed_image = np.array(original_image, dtype=np.int32)

# 3. Multiply by (-1)^(i+j)
signed_image_1 = np.zeros_like(original_image, dtype=np.int32)
for i in range(signed_image.shape[0]):
    for j in range(signed_image.shape[1]):
        signed_image_1[i][j] = signed_image[i][j] * ((-1)**(i+j))

# 4. Fourier transform
fourier_image = fft2(signed_image_1)

# 5. Butterworth Low-pass Filter
rows, cols = original_image.shape
center_x, center_y = rows // 2, cols // 2
D0 = 30   # cutoff frequency
n = 2     # order of filter
mask = np.zeros((rows, cols), dtype=np.float32)
for i in range(rows):
    for j in range(cols):
        distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
        mask[i, j] = 1 / (1 + (distance / D0)**(2 * n))

# 6. Apply mask
fourier_transformed = mask * fourier_image

# 7. Inverse Fourier Transform
filtered_image = ifft2(fourier_transformed)
filtered_image = np.abs(filtered_image)

plt.figure(figsize=(15,10))

plt.subplot(2,4,1)
plt.title("Original Image")
plt.imshow(original_image, cmap='gray')
plt.axis("off")

plt.subplot(2,4,2)
plt.title("Signed Image")
plt.imshow(signed_image, cmap='gray')
plt.axis("off")

plt.subplot(2,4,3)
plt.title("Signed Image (-1)^(i+j)")
plt.imshow(signed_image_1, cmap='gray')
plt.axis("off")

plt.subplot(2,4,4)
plt.title("Fourier Spectrum")
plt.imshow(np.log(1+np.abs(fftshift(fourier_image))), cmap='gray')
plt.axis("off")

plt.subplot(2,4,5)
plt.title(f"Butterworth Mask (n={n})")
plt.imshow(mask, cmap='gray')
plt.axis("off")

plt.subplot(2,4,6)
plt.title("Masked Fourier Spectrum")
plt.imshow(np.log(1+np.abs(fftshift(fourier_transformed))), cmap='gray')
plt.axis("off")

plt.subplot(2,4,7)
plt.title("Filtered Image (Butterworth LPF)")
plt.imshow(filtered_image, cmap='gray')
plt.axis("off")

plt.tight_layout()
plt.show()
""")
  
def p6():
  print(r"""
# ===== CELL 1 =====
#DIVIDE_TO_16_FEATURE_EXTRACTION
import cv2
import numpy as np
import pandas as pd
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.utils import to_categorical

def extract_features(image_path):
    
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    h, w, _ = img.shape
    h_step, w_step = h // 4, w // 4
    
    features = []
    
    for i in range(4):
        for j in range(4):
            square = img[i*h_step:(i+1)*h_step, j*w_step:(j+1)*w_step, :]
            
            for ch in range(3):
                hist = cv2.calcHist([square], [ch], None, [256], [0,256])
                max_val = np.argmax(hist)
                features.append(int(max_val))
    
    return features


def build_dataset(image_folder, label):
    
    data = []
    for file in os.listdir(image_folder):
        if file.endswith((".jpg", ".png", ".jpeg", ".tif")):
            path = os.path.join(image_folder, file)
            features = extract_features(path)
            features.append(label)
            data.append(features)
    
    columns = [f"feat{i+1}" for i in range(48)] + ["target"]
    return pd.DataFrame(data, columns=columns)

agri_df = build_dataset("feature_images/agriculture", "agriculture")
plane_df = build_dataset("feature_images/airplane", "airplane")

final_df = pd.concat([agri_df, plane_df], ignore_index=True)
final_df.to_csv("image_features.csv", index=False)

print("CSV file created with shape:", final_df.shape)


df = pd.read_csv("image_features.csv")

X = df.drop(columns=["target"]).values   
y = df["target"].values                  

encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)     


scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)


model = Sequential([
    Dense(128),   
    # Dropout(0.3),
    Dense(64),                      
    # Dropout(0.2),
    Dense(1, activation="sigmoid")                     
])

model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])


history = model.fit(X_train, y_train, epochs=100, validation_data=(X_test, y_test), verbose=1)


loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Accuracy: {acc*100:.2f}%")


def predict_image(image_path):
    features = extract_features(image_path)   # returns 48 features
    features_scaled = scaler.transform([features])
    prob = model.predict(features_scaled)[0][0]
    pred = "airplane" if prob >= 0.5 else "agriculture"
    return pred, prob

print(predict_image("feature_images/agriculture/agricultural99.tif"))

# ===== CELL 1 =====
#SIFT_FEATURE_EXTRACTION
import cv2
import numpy as np
import os
from sklearn.model_selection import train_test_split
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.utils import to_categorical

image_folder = './sift_images'

sift = cv2.SIFT_create()

X = []  
y = []  

for filename in os.listdir(image_folder):
    if filename.endswith('.tif'):
        img_path = os.path.join(image_folder, filename)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        
        keypoints, descriptors = sift.detectAndCompute(img, None)
        # print(keypoints.shape())
        if descriptors is not None:
            if descriptors.shape[0] >= 5:
                selected_features = descriptors[:5].flatten()
            else:
                pad_size = 5 - descriptors.shape[0]
                padding = np.zeros((pad_size, descriptors.shape[1]))
                selected_features = np.vstack((descriptors, padding)).flatten()
        else:
            selected_features = np.zeros((5, 128)).flatten()

        X.append(selected_features)
        
        label = 0 if 'agricultural' in filename.lower() else 1
        y.append(label)

X = np.array(X)
y = np.array(y)


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

y_train = to_categorical(y_train, num_classes=2)
y_test = to_categorical(y_test, num_classes=2)


X_train

y_train

model = Sequential([
    Dense(512, activation='relu', input_shape=(640,)),
    Dense(256, activation='relu'),
    Dense(2, activation='softmax')
])


optimizer = keras.optimizers.Adam(learning_rate=0.01) 

# You can then compile your model with this optimizer
model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy']) 
# model.compile(optimizer='adam', loss='categorical_crossentropy')

history = model.fit(X_train, y_train, epochs=4, validation_split=0.1)


import matplotlib.pyplot as plt

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])

# ===== CELL 8 =====
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {accuracy * 100:.2f}%")

""")
  
def p7():
  print(r"""
#MNIST_CNN

# ===== CELL 1 =====
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd

# ===== CELL 2 =====
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ===== CELL 3 =====
device

# ===== CELL 4 =====
def load_csv_dataset(csv_path):
    df = pd.read_csv(csv_path)
    data = df.iloc[:, 1:].values.astype('float32')  # Skip the label column
    labels = df.iloc[:, 0].values.astype('int64')  # First column is the label
    data = data / 255.0  # Normalize pixel values to [0, 1]
    data = torch.tensor(data)
    labels = torch.tensor(labels)
    return TensorDataset(data, labels)

# ===== CELL 5 =====
data_frame_train = load_csv_dataset('./mnist_train.csv')

# ===== CELL 6 =====
data_frame_train

# ===== CELL 7 =====
data_shape_train = data_frame_train.tensors[0].shape

# ===== CELL 8 =====
data_shape_train

# ===== CELL 9 =====
data_frame_test = load_csv_dataset('./mnist_test.csv')

# ===== CELL 10 =====
data_frame_test

# ===== CELL 11 =====
data_shape_test = data_frame_test.tensors[0].shape

# ===== CELL 12 =====
data_shape_test

# ===== CELL 13 =====
def print_tensor_dataset_head(dataset, num_rows=5):
    data_tensor, label_tensor = dataset.tensors
    data_df = pd.DataFrame(data_tensor.numpy())
    data_df['label'] = label_tensor.numpy()
    print(data_df.head(num_rows))

# ===== CELL 14 =====
print_tensor_dataset_head(data_frame_train)

# ===== CELL 15 =====
print_tensor_dataset_head(data_frame_test)

# ===== CELL 16 =====
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 10, figsize=(15, 4))
found_digits = {}
for img, label in data_frame_train:
    digit = label.item()
    if digit not in found_digits:
        found_digits[digit] = img.reshape(28, 28).numpy()
        axes[digit].imshow(found_digits[digit], cmap='gray')
        axes[digit].set_title(f"Label: {digit}")
        axes[digit].axis('off')
    if len(found_digits) == 10:
        break
plt.show()

# ===== CELL 17 =====
batch_size = 64
lr = 0.001
epochs = 50

# ===== CELL 18 =====
from torch.utils.data import DataLoader, TensorDataset

# ===== CELL 19 =====
train_loader = DataLoader(
    data_frame_train,
    batch_size=batch_size,
    shuffle=True
    )
test_loader = DataLoader(
    data_frame_test,
    batch_size=batch_size,
    shuffle=False
    )

# ===== CELL 20 =====
class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.relu3 = nn.ReLU()
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = x.view(-1, 1, 28, 28)  # Reshape input
        x = self.conv1(x)
        x = self.relu1(x)
        x = self.pool1(x)
        x = self.conv2(x)
        x = self.relu2(x)
        x = self.pool2(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.fc1(x)
        x = self.relu3(x)
        x = self.fc2(x)
        return x

# ===== CELL 21 =====
model = CNN().to(device)

# ===== CELL 22 =====

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad) 

print(f"Total trainable parameters: {count_parameters(model)}")





# ===== CELL 23 =====
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=lr)

# ===== CELL 24 =====
epochs = 20
train_losses = []  
test_accuracies = []  

for epoch in range(epochs):
    model.train()
    train_loss = 0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()

    train_loss /= len(train_loader)
    train_losses.append(train_loss)  # Append the train loss for this epoch

    # Testing
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    test_accuracies.append(accuracy)  # Append the test accuracy for this epoch

    # Print epoch metrics
    print(f"Epoch {epoch + 1}/{epochs}, Loss: {train_loss:.4f}, Accuracy: {accuracy:.2f}%")

# ===== CELL 25 =====

plt.figure(figsize=(12, 5))

# Plot training loss
plt.subplot(1, 2, 1)
plt.plot(range(1, epochs + 1), train_losses, marker='o', label='Training Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training Loss')
plt.legend()

# Plot test accuracy
plt.subplot(1, 2, 2)
plt.plot(range(1, epochs + 1), test_accuracies, marker='o', label='Test Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy (%)')
plt.title('Test Accuracy')
plt.legend()

plt.tight_layout()
plt.show()


# ===== CELL 26 =====
model.eval()
all_preds = []  # List to store all predictions
all_labels = []  # List to store all true labels

with torch.no_grad():
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)

        all_preds.extend(predicted.cpu().numpy())  # Add predictions to the list
        all_labels.extend(labels.cpu().numpy())  # Add labels to the list

test_accuracy = 100 * sum(1 for x, y in zip(all_preds, all_labels) if x == y) / len(all_labels)
print(f"Test Accuracy: {test_accuracy:.2f}%")

# ===== CELL 27 =====
torch.save(model.state_dict(), 'mnist_cnn_model.pth')
print("Model saved as 'mnist_cnn_model.pth'")

""")
  
def p8():
  print(r"""
#TRANSFER_LEARNING
# ===== CELL 1 =====
import torch
if torch.cuda.is_available():
    device=torch.device(type="cuda", index=0)
else:
    device=torch.device(type="cpu", index=0)

# ===== CELL 2 =====
import os
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms import Compose, Resize, Normalize, ToTensor
from PIL import Image

class CustomDataset(Dataset):
    def __init__(self, img_dir, transform=None):
        self.img_dir = img_dir
        self.img_files = sorted(os.listdir(img_dir))
        self.transform = transform if transform else Compose([
            Resize((224, 224)),
            ToTensor(),   
            Normalize(mean=[0.485, 0.456, 0.406],
                      std=[0.229, 0.224, 0.225])
        ])

    def __len__(self):
        return len(self.img_files)

    def __getitem__(self, idx):
        img_name = self.img_files[idx]
        img_path = os.path.join(self.img_dir, img_name)
        img = Image.open(img_path).convert("RGB")

        if self.transform:
            img = self.transform(img)
        label = 0 if idx < 100 else 1

        return img, label

dataset = CustomDataset("DataSet-2classes/")
traindataloader = DataLoader(dataset, batch_size=32, shuffle=True)


# ===== CELL 3 =====
import torch.nn as nn
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
class Cifar10Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.pretrainednet=mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.DEFAULT)
        self.pretrainednet.classifier=nn.Sequential(
            nn.Linear(in_features=960, out_features=1280,
                   bias=True),nn.Hardswish(),
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(in_features=1280, out_features=10,
                      bias=True)
        )

    def forward(self,x):
        x=self.pretrainednet(x)
        return x

# ===== CELL 4 =====
def train_one_epoch(dataloader, model,loss_fn, optimizer):
    model.train()
    track_loss=0
    num_correct=0
    num_param=0

    for i, (imgs, labels) in enumerate(dataloader):
        imgs=imgs.to(device)
        labels=labels.to(device)
        pred=model(imgs)

        loss=loss_fn(pred,labels)
        track_loss+=loss.item()
        num_correct+=(torch.argmax(prd,dim=1)==labels).type(torch.float).sum().item()

        running_loss=round(track_loss/(i+(imgs.shape[0]/batch_size)),2)
        running_acc=round((num_correct/((i*batch_size+imgs.shape[0])))*100,2)

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        if i%100==0:
            print("Batch:", i+1, "/",len(dataloader), "Running Loss:",running_loss, "Running Accuracy:",running_acc)

    epoch_loss=running_loss
    epoch_acc=running_acc
    return epoch_loss, epoch_acc

# ===== CELL 5 =====
model=Cifar10Net()
model=model.to(device)
batch_size=32
for param in model.pretrainednet.features.parameters():
    param.requires_grad=False

loss_fn=nn.CrossEntropyLoss()
lr=0.001
#optimizer=torch.optim.SGD(params=model.parameters(), lr=lr)
optimizer=torch.optim.Adam(params=model.parameters(), lr=lr)
n_epochs=3

for i in range(n_epochs):
    print("Epoch No:",i+1)
    train_epoch_loss, train_epoch_acc=train_one_epoch(traindataloader,model,loss_fn,optimizer)
    print("Training:", "Epoch Loss:", train_epoch_loss, "Epoch Accuracy:", train_epoch_acc)
    print("--------------------------------------------------")

for param in model.pretrainednet.features.parameters():
    param.requires_grad=True

for i in range(n_epochs):
    print("Epoch No:",i+1)
    train_epoch_loss, train_epoch_acc=train_one_epoch(traindataloader,model,loss_fn,optimizer)
    print("Training:", "Epoch Loss:", train_epoch_loss, "Epoch Accuracy:", train_epoch_acc)
    print("--------------------------------------------------")

# ===== CELL 6 =====
model.pretrainednet

""")
  
def p9():
  print(r"""
#IMAGE_SEGMENTATION_USING_UNET
# ===== CELL 1 =====
import torch
import torch.nn as nn
from torchvision.models import vgg16_bn,VGG16_BN_Weights
import torch.nn.functional as F
import numpy as np
from torch.utils.data import Dataset, DataLoader, random_split
import os
import PIL
from PIL import Image
from torchvision.transforms import Normalize, ToTensor, Compose
from matplotlib import pyplot as plt
import math
import pandas as pd

# ===== CELL 2 =====
if torch.cuda.is_available():
    device=torch.device(type="cuda", index=0)
else:
    device=torch.device(type="cpu", index=0)

# ===== CELL 3 =====
img=Image.open('./sai-vessel-segmentation2/all/train/21_training.tif')
mask=Image.open('./sai-vessel-segmentation2/all/train/21_manual1.gif')
print("Image Type:", type(img))
print("Mask Type:", type(mask))
print("Image Size:",img.size)
print("Image Shape:", np.array(img).shape, "Mask Shape:", np.array(mask).shape)
print("Unique in Mask:",np.unique(mask))
print("Image Data Type:", np.array(img).dtype)
print("Mask Data Type:", np.array(mask).dtype)

plt.figure(figsize=(10,5))
plt.subplot(1,2,1)
plt.title("Original Image")
plt.imshow(img)
plt.subplot(1,2,2)
plt.title("Mask")
plt.imshow(mask)
plt.show()

# ===== CELL 4 =====
def reshape_to_512(imgpath):
    ori_image = Image.open(imgpath)
    reshaped_image=ori_image.resize((512,512),PIL.Image.NEAREST)

    return reshaped_image

# ===== CELL 5 =====
img=reshape_to_512("./sai-vessel-segmentation2/all/train/21_training.tif")
mask=reshape_to_512("./sai-vessel-segmentation2/all/train/21_manual1.gif")

print("After Reshape:")

print("Image Type:", type(img))
print("Mask Type:", type(mask))
print("Image Shape:",np.array(img).shape,"Mask Shape:",np.array(mask).shape,"Image dtype:",np.array(img).dtype,"Mask dtype:", np.array(mask).dtype)
print("Unique in Mask:",np.unique(mask))
print("Number of Ones in Mask:",np.sum(np.sum(np.array(mask)/255)))

plt.figure(figsize=(10,5))
plt.subplot(1,2,1)
plt.title("Original Image 512 x 512")
plt.imshow(img)
plt.subplot(1,2,2)
plt.title("Mask 512 x 512")
plt.imshow(mask)
plt.show()

# ===== CELL 6 =====
class TrainDataset(Dataset):
    def __init__(self,path,transform=None):
        super().__init__()
        self.path=path
        _,_,self.filepaths=next(os.walk(path))
        self.length=int(len(self.filepaths)/2)-4
        self.transform=Compose([ToTensor(), Normalize(mean=[0.485, 0.456, 0.406],std=[0.229, 0.224, 0.225])])

    def __len__(self):
        return self.length

    def __getitem__(self,idx):
        idx=idx+21
        path=self.path + str(idx) + "_training.tif"
        img=reshape_to_512(path)
        img=self.transform(img)

        path=self.path + str(idx) + "_manual1.gif"
        mask=reshape_to_512(path)
        mask=np.array(mask)
        mask=torch.from_numpy(mask).type(torch.long)
        mask[mask==255]=1

        return img, mask

class ValDataset(Dataset):
    def __init__(self,path,transform=None):
        super().__init__()
        self.path=path
        _,_,self.filepaths=next(os.walk(path))
        self.length=int(len(self.filepaths)/2)-16
        self.transform=Compose([ToTensor(), Normalize(mean=[0.485, 0.456, 0.406],std=[0.229, 0.224, 0.225])])


    def __len__(self):
        return self.length

    def __getitem__(self,idx):
        idx=idx+37
        path=self.path + str(idx) + "_training.tif"
        img=reshape_to_512(path)
        img=self.transform(img)

        path=self.path + str(idx) + "_manual1.gif"
        mask=reshape_to_512(path)
        mask=np.array(mask)
        mask=torch.from_numpy(mask).type(torch.long)
        mask[mask==255]=1

        return img, mask

# ===== CELL 7 =====
train_dataset=TrainDataset("./sai-vessel-segmentation2/all/train/")
#train_dataset,val_dataset=torch.utils.data.random_split(train_dataset,[16,4])
val_dataset=ValDataset("./sai-vessel-segmentation2/all/train/")

batch_size=4

train_dataloader=DataLoader(dataset=train_dataset,batch_size=batch_size,shuffle=True)
val_dataloader=DataLoader(dataset=val_dataset,batch_size=batch_size)

# ===== CELL 8 =====
img,mask=train_dataset[0]

print("Image Shape:",img.shape,"Mask Shape:",mask.shape,"Image dtype:",img.dtype, "Mask dtype:", mask.dtype)
print("Unique in Mask:",np.unique(mask))

plt.figure(figsize=(10,5))
plt.subplot(1,2,1)
plt.title("Original Image 512 x 512 from Train_Dataset")
plt.imshow(torch.permute(img,(1,2,0)))

plt.subplot(1,2,2)
plt.title("Mask 512 x 512 from Train_Dataset")
plt.imshow(mask)
plt.show()

# ===== CELL 9 =====
class Unet(nn.Module):
    def __init__(self, encoder, center, decoder):
        super().__init__()
        self.encoder=encoder
        self.center=center
        self.decoder=decoder
        #self.dropout=nn.Dropout(p=0.2, inplace=True)

    def forward(self,x):
        encoder_features_outputs=self.encoder(x)
        #self.dropout(encoder_features_outputs[-1])
        center_output=self.center(encoder_features_outputs[-1])
        logits=self.decoder(center_output, encoder_features_outputs)
        return logits

# ===== CELL 10 =====
class Encoder(nn.Module):
    def __init__(self,pretrained_network):
        super().__init__()
        self.encoder=pretrained_network

    def forward(self,x):
        encoder_features_outputs=[]
        for layer in self.encoder.features:
                x=layer(x)
                encoder_features_outputs.append(x)

        return encoder_features_outputs

# ===== CELL 11 =====
class Center(nn.Sequential):
  def __init__(self):
        conv1=nn.Conv2d(in_channels=512,out_channels=1024, kernel_size=3,padding=1)
        bn1=nn.BatchNorm2d(num_features=1024)
        rl1=nn.ReLU()

        conv2=nn.Conv2d(in_channels=1024,out_channels=1024, kernel_size=3,padding=1)
        bn2=nn.BatchNorm2d(num_features=1024)
        rl2=nn.ReLU()

        super().__init__(conv1,bn1,rl1,conv2,bn2,rl2)

# ===== CELL 12 =====
class Decoder(nn.Module):
    def __init__(self):
        super().__init__()

        self.rl=nn.ReLU()

        self.conv5_up=nn.Conv2d(in_channels=1024,out_channels=512, kernel_size=3,padding=1)
        self.conv5_1=nn.Conv2d(in_channels=1024,out_channels=512, kernel_size=3,padding=1)
        self.bn5_1=nn.BatchNorm2d(num_features=512)
        self.conv5_2=nn.Conv2d(in_channels=512,out_channels=512, kernel_size=3,padding=1)
        self.bn5_2=nn.BatchNorm2d(num_features=512)
        self.conv5_3=nn.Conv2d(in_channels=512,out_channels=512, kernel_size=3,padding=1)
        self.bn5_3=nn.BatchNorm2d(num_features=512)

        self.conv4_up=nn.Conv2d(in_channels=512,out_channels=512, kernel_size=3,padding=1)
        self.conv4_1=nn.Conv2d(in_channels=1024,out_channels=512, kernel_size=3,padding=1)
        self.bn4_1=nn.BatchNorm2d(num_features=512)
        self.conv4_2=nn.Conv2d(in_channels=512,out_channels=512, kernel_size=3,padding=1)
        self.bn4_2=nn.BatchNorm2d(num_features=512)
        self.conv4_3=nn.Conv2d(in_channels=512,out_channels=512, kernel_size=3,padding=1)
        self.bn4_3=nn.BatchNorm2d(num_features=512)

        self.conv3_up=nn.Conv2d(in_channels=512,out_channels=256, kernel_size=3,padding=1)
        self.conv3_1=nn.Conv2d(in_channels=512,out_channels=256, kernel_size=3,padding=1)
        self.bn3_1=nn.BatchNorm2d(num_features=256)
        self.conv3_2=nn.Conv2d(in_channels=256,out_channels=256, kernel_size=3,padding=1)
        self.bn3_2=nn.BatchNorm2d(num_features=256)
        self.conv3_3=nn.Conv2d(in_channels=256,out_channels=256, kernel_size=3,padding=1)
        self.bn3_3=nn.BatchNorm2d(num_features=256)

        self.conv2_up=nn.Conv2d(in_channels=256,out_channels=128, kernel_size=3,padding=1)
        self.conv2_1=nn.Conv2d(in_channels=256,out_channels=128, kernel_size=3,padding=1)
        self.bn2_1=nn.BatchNorm2d(num_features=128)
        self.conv2_2=nn.Conv2d(in_channels=128,out_channels=128, kernel_size=3,padding=1)
        self.bn2_2=nn.BatchNorm2d(num_features=128)

        self.conv1_up=nn.Conv2d(in_channels=128,out_channels=64, kernel_size=3,padding=1)
        self.conv1_1=nn.Conv2d(in_channels=128,out_channels=64, kernel_size=3,padding=1)
        self.bn1_1=nn.BatchNorm2d(num_features=64)
        self.conv1_2=nn.Conv2d(in_channels=64,out_channels=64, kernel_size=3,padding=1)
        self.bn1_2=nn.BatchNorm2d(num_features=64)

        self.convfinal=nn.Conv2d(in_channels=64,out_channels=2,kernel_size=1)

    def forward(self,x, encoder_features_output):
        x=F.interpolate(x,scale_factor=2, mode="nearest")
        x=self.conv5_up(x)
        x=self.rl(x)
        x=torch.cat((x,encoder_features_output[42]),dim=1)
        x=self.conv5_1(x)
        x=self.bn5_1(x)
        x=self.rl(x)
        x=self.conv5_2(x)
        x=self.bn5_2(x)
        x=self.rl(x)
        x=self.conv5_3(x)
        x=self.bn5_3(x)
        x=self.rl(x)

        x=F.interpolate(x,scale_factor=2, mode="nearest")
        x=self.conv4_up(x)
        x=self.rl(x)
        x=torch.cat((x,encoder_features_output[32]),dim=1)
        x=self.conv4_1(x)
        x=self.bn4_1(x)
        x=self.rl(x)
        x=self.conv4_2(x)
        x=self.bn4_2(x)
        x=self.rl(x)
        x=self.conv4_3(x)
        x=self.bn4_3(x)
        x=self.rl(x)

        x=F.interpolate(x,scale_factor=2, mode="nearest")
        x=self.conv3_up(x)
        x=self.rl(x)
        x=torch.cat((x,encoder_features_output[22]),dim=1)
        x=self.conv3_1(x)
        x=self.bn3_1(x)
        x=self.rl(x)
        x=self.conv3_2(x)
        x=self.bn3_2(x)
        x=self.rl(x)
        x=self.conv3_3(x)
        x=self.bn3_3(x)
        x=self.rl(x)

        x=F.interpolate(x,scale_factor=2, mode="nearest")
        x=self.conv2_up(x)
        x=self.rl(x)
        x=torch.cat((x,encoder_features_output[12]),dim=1)
        x=self.conv2_1(x)
        x=self.bn2_1(x)
        x=self.rl(x)
        x=self.conv2_2(x)
        x=self.bn2_2(x)
        x=self.rl(x)

        x=F.interpolate(x,scale_factor=2, mode="nearest")
        x=self.conv1_up(x)
        x=self.rl(x)
        x=torch.cat((x,encoder_features_output[5]),dim=1)
        x=self.conv1_1(x)
        x=self.bn1_1(x)
        x=self.rl(x)
        x=self.conv1_2(x)
        x=self.bn1_2(x)
        x=self.rl(x)

        logits=self.convfinal(x)

        return logits

# ===== CELL 13 =====
def train_one_epoch(dataloader, model,loss_fn, optimizer):
    model.train()
    track_loss=0
    XintY=0
    X=0
    Y=0
    for i, (imgs, masks) in enumerate(dataloader):
        imgs=imgs.to(device)
        masks=masks.to(device)

        preds=model(imgs)

        loss=loss_fn(preds,masks)

        track_loss+=loss.item()

        predclass=torch.argmax(preds,dim=1)

        Y+=predclass.sum().item()
        X+=masks.sum().item()


        predclass[predclass==0]=2

        XintY+=(predclass==masks).type(torch.float).sum().item()

        print("Trainig Batch",i+1,":","2*XintY:",2*XintY,"X:",X,"Y:",Y, "X+Y:",X+Y)

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        running_loss=round(track_loss/(i+1),2)
        running_dice_coef=round(((2*XintY)/(X+Y)),2)

        print("Training Batch", i+1,":","/",len(dataloader), "Running Loss:",running_loss, "Running Dice_Coef:",running_dice_coef)

    epoch_loss=running_loss
    epoch_dice_coef=running_dice_coef
    return epoch_loss, epoch_dice_coef


def val_one_epoch(dataloader, model,loss_fn):
    model.eval()
    track_loss=0
    XintY=0
    X=0
    Y=0
    with torch.no_grad():
        for i, (imgs, masks) in enumerate(dataloader):
            imgs=imgs.to(device)
            masks=masks.to(device)

            preds=model(imgs)

            loss=loss_fn(preds,masks)

            track_loss+=loss.item()

            predclass=torch.argmax(preds,dim=1)

            Y+=predclass.sum().item()
            X+=masks.sum().item()

            predclass[predclass==0]=2

            XintY+=(predclass==masks).type(torch.float).sum().item()

            print("Validation Batch",i+1,":","2*XintY:",2*XintY,"X:",X,"Y:",Y, "X+Y:",X+Y)


            running_loss=round(track_loss/(i+1),2)
            running_dice_coef=round(((2*XintY)/(X+Y)),2)

            print("Validation Batch", i+1,":","/",len(dataloader), "Running Loss:",running_loss, "Running Dice_Coef:",running_dice_coef)

    epoch_loss=running_loss
    epoch_dice_coef=running_dice_coef
    return epoch_loss, epoch_dice_coef

# ===== CELL 14 =====
pretrained_network=vgg16_bn(weights=VGG16_BN_Weights.DEFAULT)
print(pretrained_network)

for param in pretrained_network.features.parameters():
    param.requires_grad=False

encoder=Encoder(pretrained_network).to(device)
center=Center().to(device)
decoder=Decoder().to(device)

model=Unet(encoder,center, decoder).to(device)

loss_fn=nn.CrossEntropyLoss()
lr=0.001
optimizer=torch.optim.Adam(params=model.parameters(), lr=lr)
n_epochs=2

for i in range(n_epochs):
    print("Epoch No:",i+1)
    train_epoch_loss, train_epoch_dice_coef=train_one_epoch(train_dataloader,model,loss_fn,optimizer)
    print("Training Epoch Loss:", train_epoch_loss, "Training Epoch Dice_Coef:", train_epoch_dice_coef)
    val_epoch_loss, val_epoch_dice_coef=val_one_epoch(val_dataloader,model,loss_fn)
    print("Validation Epoch Loss:", val_epoch_loss, "Validation Epoch Dice_Coef:", val_epoch_dice_coef)
    print("--------------------------------------------------")


for param in pretrained_network.features.parameters():
    param.requires_grad=True

n_epochs=2
for i in range(n_epochs):
    print("Epoch No:",i+1)
    train_epoch_loss, train_epoch_dice_coef=train_one_epoch(train_dataloader,model,loss_fn,optimizer)
    print("Training Epoch Loss:", train_epoch_loss, "Training Epoch Dice_Coef:", train_epoch_dice_coef)
    val_epoch_loss, val_epoch_dice_coef=val_one_epoch(val_dataloader,model,loss_fn)
    print("Validation Epoch Loss:", val_epoch_loss, "Validation Epoch Dice_Coef:", val_epoch_dice_coef)
    print("--------------------------------------------------")

# ===== CELL 15 =====
def plotres(img,pred,mask=None):
    img[0,:,:]=img[0,:,:]*0.229 + 0.485
    img[1,:,:]=img[1,:,:]*0.224 + 0.456
    img[2,:,:]=img[2,:,:]*0.225 + 0.406
    if mask!=None:
        print("Image Shape:",img.shape,"Mask Shape:", mask.shape, "Pred Shape:",pred.shape, "Image dtype", img.dtype, "Mask dtype",mask.dtype, "Pred dtype",pred.dtype)
        print("Mask Unique:",mask.unique())
    else:
        print("Image Shape:",img.shape, "Pred Shape:", pred.shape, "Image dtype:",img.dtype, "Pred dtype:",pred.dtype)

    print("Pred Unique:",pred.unique())

    plt.figure(figsize=(10,5))

    plt.subplot(1,3,1)
    plt.title("Original Image 512 x 512")
    plt.imshow(torch.permute(img.cpu(),(1,2,0)))

    if mask!=None:
        plt.subplot(1,3,2)
        plt.title("Mask Image  512 x 512")
        plt.imshow(mask.cpu())

    plt.subplot(1,3,3)
    plt.title("Predicted Image  512 x 512")
    plt.imshow(pred.cpu())
    plt.show()

# ===== CELL 16 =====
imgs,masks=next(iter(val_dataloader))
model.eval()

imgs=imgs.to(device)
masks=masks.to(device)

with torch.no_grad():
    preds=model(imgs)

    predclass=torch.argmax(preds,dim=1)

    Y=predclass.sum().item()
    X=masks.sum().item()

    predclass[predclass==0]=2

    XintY=(predclass==masks).type(torch.float).sum().item()

    print("On Validation Set:","2*XintY:",2*XintY,"X:",X,"Y:",Y, "X+Y:",X+Y)

    dice_coef=round((2*XintY)/(X+Y),2)


print("Validation Dice Coef:",dice_coef)

predclass[predclass==2]=0
plotres(imgs[0],predclass[0],masks[0])
plotres(imgs[1],predclass[1],masks[1])
plotres(imgs[2],predclass[2],masks[2])
plotres(imgs[3],predclass[3],masks[3])

# ===== CELL 17 =====
train_dataset=TrainDataset("./sai-vessel-segmentation2/all/train/", "yes")

batch_size=4

n_epochs=2

train_dataloader=DataLoader(dataset=train_dataset,batch_size=batch_size,shuffle=True)

for i in range(n_epochs):
    print("Epoch No:",i+1)
    train_epoch_loss, train_epoch_dice_coef=train_one_epoch(train_dataloader,model,loss_fn,optimizer)
    print("Training Epoch Loss:", train_epoch_loss, "Training Epoch Dice_Coef:", train_epoch_dice_coef)
    print("--------------------------------------------------")

# ===== CELL 18 =====
class TestDataset(Dataset):
    def __init__(self,path):
        super().__init__()
        self.path=path
        _,_,self.filepaths=next(os.walk(path))
        self.length=len(self.filepaths)
        self.transform=Compose([ToTensor(), Normalize(mean=[0.485, 0.456, 0.406],std=[0.229, 0.224, 0.225])])

    def __len__(self):
        return self.length

    def __getitem__(self,idx):
        idx=idx+1
        if idx <= 9:
            path=self.path + "0" + str(idx) + "_test.tif"
        else:
            path=self.path + str(idx) + "_test.tif"

        img=reshape_to_512(path)
        img=self.transform(img)

        return img

# ===== CELL 19 =====
torch.cuda.empty_cache()

# ===== CELL 20 =====
test_dataset=TestDataset("./sai-vessel-segmentation2/all/test/")

batch_size=2
test_dataloader=DataLoader(dataset=test_dataset,batch_size=batch_size)

# ===== CELL 21 =====
def eval_one_epoch(dataloader, model):
    model.eval()
    outputs=[]
    for i, imgs in enumerate(dataloader):
        imgs=imgs.to(device)
        preds=model(imgs)

        with torch.no_grad():
            for i in range(preds.shape[0]):
                pred=preds[i,:,:,:]
                pred=torch.argmax(pred,dim=0).cpu()

                plotres(imgs[i],pred)

                predf=pred.flatten()

                pixelidx=np.where(predf==1)[0]+1

                run_lengths=[]

                for pxid in pixelidx:
                    if len(run_lengths)==0:
                        run_lengths.extend((pxid,1))
                    elif pxid>prev+1:
                        run_lengths.extend((pxid,1))
                    else:
                        run_lengths[-1]+=1
                    prev=pxid

                output = ' '.join([str(r) for r in run_lengths])

                outputs.append(output)
    return outputs

outputs=eval_one_epoch(test_dataloader,model)
df=pd.DataFrame(columns=['Id','Predicted'])
df['Id']=[str(i) for i in range(20)]
df['Predicted']=outputs
df.to_csv("submission.csv", index=None)
df
""")
  
def p10():
  print(r"""
#YOLO_MODEL
# ===== CELL 1 =====
!pip install torch torchvision matplotlib --quiet
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision
from PIL import Image
import os, numpy as np, matplotlib.pyplot as plt

# ===== CELL 2 =====
!wget -q https://www.cis.upenn.edu/~jshi/ped_html/PennFudanPed.zip
!unzip -q PennFudanPed.zip -d ./data

# ===== CELL 3 =====
class PennFudanDataset(Dataset):
    def __init__(self, root, transform=None, S=7, B=2, C=1):
        self.root = root
        self.transform = transform
        self.imgs = list(sorted(os.listdir(os.path.join(root, "PNGImages"))))
        self.masks = list(sorted(os.listdir(os.path.join(root, "PedMasks"))))
        self.S, self.B, self.C = S, B, C

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img_path = os.path.join(self.root, "PNGImages", self.imgs[idx])
        mask_path = os.path.join(self.root, "PedMasks", self.masks[idx])
        img = Image.open(img_path).convert("RGB")
        mask = Image.open(mask_path)

        # Extract bounding boxes from mask
        mask_np = np.array(mask)
        obj_ids = np.unique(mask_np)[1:]  # skip background 0
        boxes = []
        for obj_id in obj_ids:
            pos = np.where(mask_np == obj_id)
            xmin, xmax = np.min(pos[1]), np.max(pos[1])
            ymin, ymax = np.min(pos[0]), np.max(pos[0])
            boxes.append([xmin, ymin, xmax, ymax])

        # Convert to YOLO grid target
        label = torch.zeros((self.S, self.S, self.B*5 + self.C))
        w, h = img.size
        for box in boxes:
            x_c = (box[0] + box[2]) / (2 * w)
            y_c = (box[1] + box[3]) / (2 * h)
            bw = (box[2] - box[0]) / w
            bh = (box[3] - box[1]) / h
            cell_x, cell_y = int(x_c * self.S), int(y_c * self.S)
            label[cell_y, cell_x, 0:5] = torch.tensor([x_c, y_c, bw, bh, 1.0])
            label[cell_y, cell_x, 10:] = torch.tensor([1.0])  # pedestrian class

        if self.transform:
            img = self.transform(img)
        return img, label


# ===== CELL 4 =====
root = "data/PennFudanPed"

# Select sample image and mask
img_path = os.path.join(root, "PNGImages", "PennPed00016.png")
mask_path = os.path.join(root, "PedMasks", "PennPed00016_mask.png")

# Load image and mask
img = np.array(Image.open(img_path).convert("RGB"))
mask = np.array(Image.open(mask_path))

# Extract unique object IDs (each pedestrian = different gray value)
obj_ids = np.unique(mask)[1:]  # skip background 0

# Plot image
fig, ax = plt.subplots(1, figsize=(6,6))
ax.imshow(img)

# Draw bounding boxes for each object
for obj_id in obj_ids:
    pos = np.where(mask == obj_id)
    xmin, xmax = np.min(pos[1]), np.max(pos[1])
    ymin, ymax = np.min(pos[0]), np.max(pos[0])

    rect = patches.Rectangle(
        (xmin, ymin), xmax - xmin, ymax - ymin,
        linewidth=2, edgecolor='r', facecolor='none'
    )
    ax.add_patch(rect)
    ax.text(xmin, ymin - 5, f"Ped {obj_id}", color='yellow', fontsize=10, weight='bold')

ax.set_title("Annotated Bounding Boxes (PennFudanPed)")
plt.axis("off")
plt.show()

# ===== CELL 5 =====
class TinyYOLO(nn.Module):
    def __init__(self, S=7, B=2, C=1):
        super(TinyYOLO, self).__init__()
        self.S, self.B, self.C = S, B, C

        self.conv = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.BatchNorm2d(16),
            nn.LeakyReLU(0.1),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(16, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.1),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.1),
            nn.MaxPool2d(2, 2),
        )

        # 64 * 32 * 32 = 65536 (for 256x256 input)
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 32 * 32, 4096),
            nn.LeakyReLU(0.1),
            nn.Linear(4096, S * S * (B * 5 + C))
        )

    def forward(self, x):
        x = self.conv(x)
        x = self.fc(x)
        return x.view(-1, self.S, self.S, self.B * 5 + self.C)


# ===== CELL 6 =====
class YoloLoss(nn.Module):
    def __init__(self, S=7, B=2, C=1, λ_coord=5, λ_noobj=0.5):
        super(YoloLoss, self).__init__()
        self.S, self.B, self.C = S, B, C
        self.λ_coord, self.λ_noobj = λ_coord, λ_noobj

    def forward(self, preds, targets):
        coord_mask = targets[..., 4] > 0

        loc_loss = F.mse_loss(preds[..., 0:2][coord_mask], targets[..., 0:2][coord_mask])
        size_loss = F.mse_loss(torch.sqrt(torch.abs(preds[..., 2:4][coord_mask])),
                               torch.sqrt(torch.abs(targets[..., 2:4][coord_mask])))
        conf_loss_obj = F.mse_loss(preds[..., 4][coord_mask], targets[..., 4][coord_mask])
        conf_loss_noobj = F.mse_loss(preds[..., 4][~coord_mask], targets[..., 4][~coord_mask])
        class_loss = F.mse_loss(preds[..., 10:], targets[..., 10:])

        total_loss = (self.λ_coord * (loc_loss + size_loss)
                      + conf_loss_obj
                      + self.λ_noobj * conf_loss_noobj
                      + class_loss)
        return total_loss


# ===== CELL 7 =====
S, B, C = 7, 2, 1
transform = transforms.Compose([transforms.Resize((256,256)), transforms.ToTensor()])
dataset = PennFudanDataset(root='data/PennFudanPed', transform=transform, S=S, B=B, C=C)
loader = DataLoader(dataset, batch_size=4, shuffle=True)

model = TinyYOLO(S=S, B=B, C=C)
criterion = YoloLoss(S=S, B=B, C=C)
optimizer = optim.Adam(model.parameters(), lr=1e-4)

for epoch in range(2):
    total_loss = 0
    for imgs, labels in loader:
        preds = model(imgs)
        loss = criterion(preds, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch [{epoch+1}/2] | Loss: {total_loss/len(loader):.4f}")


# ===== CELL 8 =====
import matplotlib.patches as patches

def plot_prediction(img, pred, S=7, conf_thresh=0.3):
    fig, ax = plt.subplots(1)
    ax.imshow(np.transpose(img.numpy(), (1,2,0)))
    cell_size = 1/S
    for i in range(S):
        for j in range(S):
            if pred[0, i, j, 4] > conf_thresh:
                x, y, w, h = pred[0, i, j, 0:4]
                x, y, w, h = float(x), float(y), float(w), float(h)
                rect = patches.Rectangle(((x - w/2)*256, (y - h/2)*256),
                                         w*256, h*256, linewidth=2, edgecolor='r', facecolor='none')
                ax.add_patch(rect)
    plt.show()

test_img, _ = dataset[5]
with torch.no_grad():
    pred = model(test_img.unsqueeze(0))
plot_prediction(test_img, pred)
""")