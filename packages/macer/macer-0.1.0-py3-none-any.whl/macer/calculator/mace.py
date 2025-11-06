from mace.calculators import MACECalculator
from pathlib import Path

def get_mace_calculator(model_paths, device="cpu"):
    """Construct MACE calculator (use float32 for MPS compatibility)."""
    if model_paths is None:
        # Use default model if none is provided
        # Assuming the default model is in the project root under mace-model/
        default_model_path = Path(__file__).parent.parent.parent / "mace-model" / "mace-omat-0-small-fp32.model"
        if not default_model_path.exists():
            raise FileNotFoundError(f"Default MACE model not found at {default_model_path}")
        model_paths = [str(default_model_path)]
    
    dtype = "float32" if device == "mps" else "float64"
    return MACECalculator(
        model_paths=model_paths,
        device=device,
        default_dtype=dtype,
    )
