import torch
import coremltools as ct
from sports.tennis.ball_tracking.tracknet.model_pytorch import TrackNet

def export_to_coreml(checkpoint_path, output_path="sports/tennis/models/TrackNetFTV2.mlpackage"):
    model = TrackNet()
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    
    example_input = torch.rand(1, 9, 360, 640)
    
    traced_model = torch.jit.trace(model, example_input)
    
    coreml_model = ct.convert(
        traced_model,
        inputs=[ct.TensorType(name="video_frames", shape=example_input.shape)],
        compute_units=ct.ComputeUnit.CPU_AND_GPU
    )
    
    coreml_model.save(output_path)
    print(f"coreml model successfully compiled and saved to: {output_path}")

if __name__ == "__main__":
    export_to_coreml("sports/tennis/models/tracknet_ftV2.pt")
