import os
import requests
import json

def capture_variable_info(var_name, var_value):
    info = {"name": var_name, "type": None, "value": None, "shape": None, "min": None, "max": None}
    
    try:
        import numpy as np
        if isinstance(var_value, np.ndarray):
            info["type"] = "numpy.ndarray"
            info["shape"] = list(var_value.shape)
            info["min"] = float(var_value.min())
            info["max"] = float(var_value.max())
            return info
    except ImportError:
        pass

    try:
        import torch
        if isinstance(var_value, torch.Tensor):
            info["type"] = "torch.Tensor"
            info["shape"] = list(var_value.shape)
            info["min"] = float(var_value.min().item())
            info["max"] = float(var_value.max().item())
            return info
    except ImportError:
        pass

    if isinstance(var_value, (int, float)):
        info["type"] = "float" if isinstance(var_value, float) else "int"
        info["value"] = float(var_value)
        return info

    return info


def verify(api_key: str = None, project_id: str = None, step: int = None, api_base_url: str = "https://www.crekai.com/api"):
    """
    Universal CrekAI Verification function.
    Automatically captures all variables and submits verification to CrekAI.
    
    If api_key or project_id are not provided, it tries to read them from environment variables:
      - CREKAI_API_KEY
      - CREKAI_PROJECT_ID
    """
    # Read from environment if not passed
    api_key = api_key or os.getenv("CREKAI_API_KEY")
    project_id = project_id or os.getenv("CREKAI_PROJECT_ID")

    if not api_key or not project_id:
        raise ValueError("Missing API key or project ID. Provide them directly or set CREKAI_API_KEY and CREKAI_PROJECT_ID in environment.")

    print("🔍 CrekAI Verification\n")
    print("📊 Capturing variables...")

    variables = {}
    frame = globals()

    for var_name, var_value in list(frame.items()):
        if var_name.startswith('_'):
            continue
        if var_name in ['In', 'Out', 'get_ipython', 'exit', 'quit', 'requests', 'json', 'np', 'torch', 'verify', 'capture_variable_info', 'os']:
            continue
        if callable(var_value) and not hasattr(var_value, 'shape'):
            continue

        try:
            info = capture_variable_info(var_name, var_value)
            if info["type"]:
                variables[var_name] = info
                print(f"   ✓ {var_name}")
        except:
            pass

    print("\n🚀 Submitting...\n")

    try:
        response = requests.post(
            f"{api_base_url}/track-execution",
            json={
                "token": api_key,
                "project_id": project_id,
                "step": step,
                "code": "executed",
                "output": {"variables": variables},
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print("=" * 60)
            print("✅ SUCCESS! Assignment Verified!")
            print("=" * 60)
            print(f"\n{data.get('message', '')}")
            if data.get('next_step'):
                print(f"\n🚀 Step {data['next_step']} unlocked!")
            print("\n👉 Return to CrekAI")
            print("=" * 60)
        else:
            print("❌ Validation Failed")
            error_data = response.json()
            print(f"\n{error_data.get('message', 'Check your code')}")

    except Exception as e:
        print(f"❌ Error: {e}")
