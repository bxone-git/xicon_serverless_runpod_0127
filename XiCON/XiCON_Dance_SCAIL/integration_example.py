"""
Integration Example: Using request_transformer with RunPod Handler

This example shows how to integrate the request_transformer module
into the RunPod serverless handler.
"""

import json
from request_transformer import (
    transform_request_to_workflow,
    load_workflow_template,
    validate_user_input
)

# ============================================================
# Example 1: Basic Handler Integration
# ============================================================

def handler(job):
    """
    RunPod handler function with request transformation.

    Args:
        job: RunPod job object with 'input' field

    Returns:
        dict: Result with status and data
    """
    try:
        # Extract user input from job
        user_input = job["input"]

        # Validate input (raises ValueError if invalid)
        validate_user_input(user_input)

        # Load workflow template (cached at module level in production)
        template = load_workflow_template("workflow_template.json")

        # Transform user request to ComfyUI workflow
        workflow = transform_request_to_workflow(user_input, template)

        # Submit workflow to ComfyUI (placeholder)
        # result = submit_to_comfyui(workflow)

        return {
            "status": "success",
            "workflow": workflow,
            "message": "Request transformed successfully"
        }

    except ValueError as e:
        # Validation error
        return {
            "status": "error",
            "error_type": "validation_error",
            "message": str(e)
        }

    except Exception as e:
        # Other errors
        return {
            "status": "error",
            "error_type": "unknown_error",
            "message": str(e)
        }


# ============================================================
# Example 2: Optimized Handler with Template Caching
# ============================================================

# Load template once at module level (not per request)
WORKFLOW_TEMPLATE = load_workflow_template("workflow_template.json")

def optimized_handler(job):
    """
    Optimized handler with cached template.
    """
    try:
        user_input = job["input"]
        validate_user_input(user_input)

        # Use cached template
        workflow = transform_request_to_workflow(user_input, WORKFLOW_TEMPLATE)

        return {"status": "success", "workflow": workflow}

    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# Example 3: Sample User Requests
# ============================================================

# Minimal request (uses defaults)
minimal_request = {
    "images": {
        "reference_image": "https://example.com/person.jpg"
    },
    "videos": {
        "dance_video": "https://example.com/dance.mp4"
    }
}

# Full request (all parameters specified)
full_request = {
    "images": {
        "reference_image": "https://example.com/person.jpg"
    },
    "videos": {
        "dance_video": "https://example.com/dance.mp4"
    },
    "prompt": "a person dancing gracefully in the studio",
    "width": 512,
    "height": 768,
    "steps": 10,
    "cfg": 2.0,
    "seed": 42
}

# High-resolution request
hires_request = {
    "images": {
        "reference_image": "https://example.com/person_hd.jpg"
    },
    "videos": {
        "dance_video": "https://example.com/dance_hd.mp4"
    },
    "prompt": "professional dancer performing contemporary dance",
    "width": 832,
    "height": 1344,
    "steps": 15,
    "cfg": 1.5,
    "seed": 123
}


# ============================================================
# Example 4: Error Handling Scenarios
# ============================================================

def test_error_handling():
    """Test various error scenarios."""

    # Test 1: Missing reference image
    try:
        invalid_request = {
            "images": {},
            "videos": {"dance_video": "https://example.com/dance.mp4"}
        }
        validate_user_input(invalid_request)
        print("Test 1 FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"Test 1 PASSED: {e}")

    # Test 2: Invalid width
    try:
        invalid_request = {
            "images": {"reference_image": "https://example.com/ref.jpg"},
            "videos": {"dance_video": "https://example.com/dance.mp4"},
            "width": -100
        }
        validate_user_input(invalid_request)
        print("Test 2 FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"Test 2 PASSED: {e}")

    # Test 3: Invalid steps
    try:
        invalid_request = {
            "images": {"reference_image": "https://example.com/ref.jpg"},
            "videos": {"dance_video": "https://example.com/dance.mp4"},
            "steps": 0
        }
        validate_user_input(invalid_request)
        print("Test 3 FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"Test 3 PASSED: {e}")


# ============================================================
# Example 5: Testing Locally
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Request Transformer Integration Examples")
    print("=" * 60)

    # Test error handling
    print("\n[Error Handling Tests]")
    test_error_handling()

    # Test minimal request
    print("\n[Minimal Request Test]")
    try:
        validate_user_input(minimal_request)
        print("✅ Minimal request validation passed")
    except Exception as e:
        print(f"❌ Minimal request validation failed: {e}")

    # Test full request
    print("\n[Full Request Test]")
    try:
        validate_user_input(full_request)
        print("✅ Full request validation passed")
    except Exception as e:
        print(f"❌ Full request validation failed: {e}")

    # Test high-res request
    print("\n[High-Resolution Request Test]")
    try:
        validate_user_input(hires_request)
        print("✅ High-resolution request validation passed")
    except Exception as e:
        print(f"❌ High-resolution request validation failed: {e}")

    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)
