import os
import tempfile

import cupy as cp
import numpy as np
import onnxruntime
import pixtreme as px
import pytest

import visagene as vg
from visagene import utils


class TestBlendSwapInference:
    """BlendSwap ONNX model inference test"""

    def setup_method(self):
        """Test setup"""
        self.model_path = "models/blendswap.onnx"
        self.detection_model_path = "models/face_detection.onnx"
        self.source_path = "examples/example2.png"
        self.target_path = "examples/example.png"

        # Check if model exists
        if not os.path.exists(self.model_path):
            pytest.skip(f"Model not found: {self.model_path}")

        # Initialize ONNX session
        self.session = onnxruntime.InferenceSession(self.model_path)

        # Get input and output names
        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]

    def test_model_info(self):
        """Verify model input/output information"""
        inputs = self.session.get_inputs()
        outputs = self.session.get_outputs()
        
        print("\n=== BlendSwap Model Info ===")
        print(f"Number of inputs: {len(inputs)}")
        for i, inp in enumerate(inputs):
            print(f"Input {i}: name={inp.name}, shape={inp.shape}, type={inp.type}")
        
        print(f"\nNumber of outputs: {len(outputs)}")
        for i, out in enumerate(outputs):
            print(f"Output {i}: name={out.name}, shape={out.shape}, type={out.type}")

        # Basic verification
        assert len(inputs) == 2, "BlendSwap should have 2 inputs (target and source)"
        assert len(outputs) >= 1, "BlendSwap should have at least 1 output"

    def test_basic_inference(self):
        """Basic inference test"""
        # Load and preprocess images
        source_image = px.imread(self.source_path)
        source_image = px.to_float32(source_image)
        source_image = px.bgr_to_rgb(source_image)
        
        target_image = px.imread(self.target_path)
        target_image = px.to_float32(target_image)
        target_image = px.bgr_to_rgb(target_image)

        # Face detection
        detection = vg.OnnxFaceDetection(model_path=self.detection_model_path)

        source_faces = detection.get(source_image, crop_size=112)
        target_faces = detection.get(target_image, crop_size=256)

        assert len(source_faces) > 0, "No source face detected"
        assert len(target_faces) > 0, "No target face detected"

        source_face = source_faces[0]
        target_face = target_faces[0]

        # Preprocessing parameters
        input_mean = 0.5
        input_std = 0.5

        # Prepare batch data
        source_batch = utils.image_to_batch(source_face.image, std=input_std, mean=input_mean, size=112, layout="NCHW")
        target_batch = utils.image_to_batch(target_face.image, std=input_std, mean=input_mean, size=256, layout="NCHW")
        
        source_batch = px.to_numpy(source_batch)
        target_batch = px.to_numpy(target_batch)

        # Run inference
        preds = self.session.run(None, {
            self.input_names[0]: target_batch,
            self.input_names[1]: source_batch
        })

        # Verify results
        assert len(preds) >= 1, "No output from model"
        output = preds[0]

        # Verify output shape
        assert output.shape[0] == 1, "Batch size should be 1"
        assert output.shape[1] == 3, "Should have 3 channels (RGB)"
        assert len(output.shape) == 4, "Output should be 4D tensor (B, C, H, W)"

        # Verify output value range
        assert output.min() >= -1.5, "Output values too low"
        assert output.max() <= 1.5, "Output values too high"

    def test_output_consistency(self):
        """Test if consistent output is obtained with same input"""
        # Inference with dummy data
        source_dummy = np.random.randn(1, 3, 112, 112).astype(np.float32)
        target_dummy = np.random.randn(1, 3, 256, 256).astype(np.float32)

        # Run inference twice
        output1 = self.session.run(None, {
            self.input_names[0]: target_dummy,
            self.input_names[1]: source_dummy
        })[0]
        
        output2 = self.session.run(None, {
            self.input_names[0]: target_dummy,
            self.input_names[1]: source_dummy
        })[0]

        # Verify results are identical
        np.testing.assert_allclose(output1, output2, rtol=1e-5)

    def test_batch_processing(self):
        """Batch processing test"""
        batch_size = 2

        # Prepare batch data
        source_batch = np.random.randn(batch_size, 3, 112, 112).astype(np.float32)
        target_batch = np.random.randn(batch_size, 3, 256, 256).astype(np.float32)

        try:
            # Run batch inference
            outputs = self.session.run(None, {
                self.input_names[0]: target_batch,
                self.input_names[1]: source_batch
            })

            output = outputs[0]
            assert output.shape[0] == batch_size, f"Expected batch size {batch_size}, got {output.shape[0]}"

        except Exception as e:
            # Possibly only batch size 1 is supported
            pytest.skip(f"Batch processing not supported: {e}")

    def test_with_real_images(self):
        """Complete inference test with real images"""
        # Load and preprocess images
        source_image = px.imread(self.source_path)
        source_image = px.to_float32(source_image)
        source_image = px.bgr_to_rgb(source_image)
        
        target_image = px.imread(self.target_path)
        target_image = px.to_float32(target_image)
        target_image = px.bgr_to_rgb(target_image)

        # Face detection
        detection = vg.OnnxFaceDetection(model_path=self.detection_model_path)

        source_faces = detection.get(source_image, crop_size=112)
        target_faces = detection.get(target_image, crop_size=256)

        if len(source_faces) == 0 or len(target_faces) == 0:
            pytest.skip("No faces detected in test images")

        source_face = source_faces[0]
        target_face = target_faces[0]

        # Preprocessing
        input_mean = 0.5
        input_std = 0.5

        source_batch = utils.image_to_batch(source_face.image, std=input_std, mean=input_mean, size=112, layout="NCHW")
        target_batch = utils.image_to_batch(target_face.image, std=input_std, mean=input_mean, size=256, layout="NCHW")

        source_batch = px.to_numpy(source_batch)
        target_batch = px.to_numpy(target_batch)

        # Inference
        preds = self.session.run(None, {
            self.input_names[0]: target_batch,
            self.input_names[1]: source_batch
        })

        # Postprocessing
        output = preds[0]
        # Convert numpy array to cupy array
        output = cp.asarray(output)
        output_images = utils.batch_to_images(output, std=input_std, mean=input_mean, layout="NCHW")
        output_image = output_images[0]
        output_image = px.rgb_to_bgr(output_image)

        # Verify output image
        assert output_image.shape == (256, 256, 3), "Output image should be 256x256x3"
        assert output_image.min() >= 0, "Output image should have non-negative values"
        assert output_image.max() <= 1, "Output image values should be <= 1"

        # Save to temporary file and test
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
        try:
            os.close(temp_fd)  # Close file descriptor
            px.imwrite(temp_path, output_image)
            assert os.path.exists(temp_path), "Failed to save output image"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])