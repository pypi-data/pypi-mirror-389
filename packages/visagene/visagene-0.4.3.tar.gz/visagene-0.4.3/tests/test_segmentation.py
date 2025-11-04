import os

import cupy as cp
import pixtreme as px

import visagene as vg


def test_segmentation():
    # Initialize the segmentation model
    model_path = "models/face_segmentation.onnx"

    # Test both ONNX and TRT versions
    print("=== Testing ONNX Segmentation ===")
    model = vg.OnnxFaceSegmentation(model_path=model_path)
    run_segmentation_test(model, "ONNX")

    print("\n=== Testing TRT Segmentation ===")
    model_trt = vg.TrtFaceSegmentation(model_path=model_path)
    run_segmentation_test(model_trt, "TRT")


def run_segmentation_test(model, model_type):
    # Load a test image
    image_path = "examples/example2.png"
    image = px.imread(image_path)
    image = px.to_float32(image)
    image = px.resize(image, (512, 512), interpolation=px.INTER_AUTO)

    px.imshow(f"Input Image ({model_type})", image)

    # First, verify model reproducibility
    print(f"\n=== {model_type} Model Reproducibility Test ===")
    mask_single1 = model.get(image)
    mask_single2 = model.get(image)

    is_deterministic = cp.allclose(mask_single1, mask_single2, rtol=1e-5, atol=1e-5)
    max_diff_single = cp.max(cp.abs(mask_single1 - mask_single2))
    diff_count_single = cp.sum(cp.abs(mask_single1 - mask_single2) > 1e-5)

    print(f"{model_type} Single vs Single (same image processed twice):")
    print(f"  - Equal: {is_deterministic}")
    print(f"  - Max absolute difference: {max_diff_single}")
    print(
        f"  - Different pixels: {diff_count_single}/{mask_single1.size} ({float(diff_count_single) / mask_single1.size * 100:.4f}%)"
    )

    # Process with single get method (using mask_single1 from now on)
    mask_single = mask_single1
    px.imshow(f"{model_type} Single Segmentation Mask", mask_single)

    # Process same image in batch
    masks_batch = model.batch_get([image, image, image])

    # Compare results
    print(f"\n=== {model_type} Comparing single get() vs batch_get() results ===")

    # Compare each batch result with single processing result
    for i, mask_batch in enumerate(masks_batch):
        # Compare CuPy arrays (using more tolerant threshold)
        is_equal = cp.allclose(mask_single, mask_batch, rtol=0.01, atol=0.01)
        max_diff = cp.max(cp.abs(mask_single - mask_batch))

        # Count pixels with differences
        diff_count = cp.sum(cp.abs(mask_single - mask_batch) > 1e-5)
        total_pixels = mask_single.size

        print(f"{model_type} Batch mask {i} vs Single mask:")
        print(f"  - Shape single: {mask_single.shape}, batch: {mask_batch.shape}")
        print(f"  - Equal (within tolerance): {is_equal}")
        print(f"  - Max absolute difference: {max_diff}")
        print(f"  - Different pixels: {diff_count}/{total_pixels} ({float(diff_count) / total_pixels * 100:.2f}%)")

        # Display difference image
        diff_image = cp.abs(mask_single - mask_batch)
        px.imshow(f"{model_type} Difference {i}", diff_image)

        px.imshow(f"{model_type} Batch Mask {i}", mask_batch)

    # Test with different images
    print(f"\n=== {model_type} Batch processing test with different images ===")

    # Load a different image
    image2_path = "examples/example1.png" if os.path.exists("examples/example1.png") else image_path
    image2 = px.imread(image2_path)
    image2 = px.to_float32(image2)
    image2 = px.resize(image2, (512, 512), interpolation=px.INTER_AUTO)

    # Mixed batch processing
    mixed_masks = model.batch_get([image, image2, image])
    print(f"{model_type} Mixed batch processed: {len(mixed_masks)} masks")

    # Test with large batch size (verify batch splitting)
    print(f"\n=== {model_type} Large batch size test ===")
    large_batch = [image] * 20  # Exceeds MAX_BATCH_SIZE=16
    large_masks = model.batch_get(large_batch)
    print(f"{model_type} Large batch (20 images) processed: {len(large_masks)} masks")

    # Verify first and last results match single processing
    is_first_equal = cp.allclose(mask_single, large_masks[0], rtol=1e-5, atol=1e-5)
    is_last_equal = cp.allclose(mask_single, large_masks[-1], rtol=1e-5, atol=1e-5)
    print(f"{model_type} First mask equal to single: {is_first_equal}")
    print(f"{model_type} Last mask equal to single: {is_last_equal}")


if __name__ == "__main__":
    test_segmentation()
    px.waitkey(1)
    px.destroy_all_windows()
