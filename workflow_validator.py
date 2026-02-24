def validate_semantics(workflow):

    if "error" in workflow:
        return False, "Invalid JSON"

    steps = workflow.get("steps", [])

    tools = [step.get("tool") for step in steps]

    workflow_type = workflow.get("workflow_type", "").lower()

    # Rule 1: If suitability workflow, enforce rules
    if "suitability" in workflow_type:

        if "WeightedOverlay" not in tools:
            return False, "Missing WeightedOverlay step"

        normalize_count = tools.count("NormalizeRaster")
        if normalize_count < 2:
            return False, "Need at least 2 NormalizeRaster steps"

        if tools[-1] != "ExtractTopLocations":
            return False, "ExtractTopLocations must be final step"

    # Rule 2: Prevent excessive gdalwarp
    if tools.count("gdalwarp") > 3:
        return False, "Too many gdalwarp steps"

    # Rule 3: Step IDs sequential
    for i, step in enumerate(steps):
        if step.get("step_id") != i + 1:
            return False, "Step IDs not sequential"

    return True, "Valid workflow"