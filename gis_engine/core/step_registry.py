"""
Registry for tracking available GIS processing steps.
"""


class StepRegistry:
    """Manages registration and lookup of available processing steps."""

    def __init__(self):
        self.steps = {}

    # --------------------------------------------------
    # Registration
    # --------------------------------------------------

    def register(self, name, step_class, description=None):
        """
        Register a new processing step.

        Args:
            name: Unique step name (used in JSON workflow)
            step_class: Class implementing execute(context, **kwargs)
            description: Optional description
        """

        if name in self.steps:
            raise ValueError(f"Step '{name}' already registered.")

        self.steps[name] = {
            "class": step_class,
            "description": description
        }

    # --------------------------------------------------
    # Retrieval
    # --------------------------------------------------

    def get(self, name):
        """Retrieve registered step class."""
        step = self.steps.get(name)
        if step is None:
            raise KeyError(f"Step '{name}' not found in registry.")
        return step["class"]

    def get_metadata(self, name):
        """Get step metadata."""
        return self.steps.get(name)

    def list_steps(self):
        """List all available step names."""
        return list(self.steps.keys())

    # --------------------------------------------------
    # Execution Helper
    # --------------------------------------------------

    def execute(self, name, context, **kwargs):
        """
        Execute a registered step.

        Args:
            name: Step name
            context: ContextManager instance
            kwargs: Parameters from workflow
        """

        step_class = self.get(name)
        step_instance = step_class()

        if not hasattr(step_instance, "execute"):
            raise AttributeError(
                f"Step '{name}' must implement an 'execute(context, **kwargs)' method."
            )

        context.set_step(name)
        result = step_instance.execute(context=context, **kwargs)

        return result