import numpy as np
from ..core.step_registry import BaseStep

class ExtractTopLocationsStep(BaseStep):
    """
    Extracts the top N pixel locations from a suitability raster.
    """
    def execute(self, context, inputs, parameters, outputs):
        raster_name = inputs.get("input_raster")
        raster = context.get(raster_name)
        
        if raster is None:
            raise ValueError(f"Raster {raster_name} not found in context")
            
        num_locations = parameters.get("num_locations", 10)
        
        # Flatten and get top indices
        flat = raster.flatten()
        indices = np.argsort(flat)[-num_locations:]
        rows, cols = np.unravel_index(indices, raster.shape)
        
        # We need the transform to get lat/lon
        transform = context.get("transform") # GISEngine should store this
        if transform is None:
            # Fallback for mock/test data if transform isn't passed
            locations = [{"latitude": float(r), "longitude": float(c), "score": float(raster[r,c])} for r,c in zip(rows, cols)]
        else:
            locations = []
            for r, c in zip(rows, cols):
                lon, lat = transform * (c, r)
                locations.append({
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "score": float(raster[r, c])
                })
        
        # Store in results
        context.set("final_locations", locations)
        return {"final_locations": locations}
