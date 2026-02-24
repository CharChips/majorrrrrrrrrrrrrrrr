"""
Workflow executor for orchestrating GIS operations.
"""

import traceback


class WorkflowExecutor:
    """Executes a sequence of GIS processing steps."""

    def __init__(self, registry):
        """
        Args:
            registry: StepRegistry instance
        """
        self.registry = registry
        self.steps = []
        self.results = {}
        self.execution_log = []

    # --------------------------------------------------
    # Add Step
    # --------------------------------------------------

    def add_step(self, step_dict):
        """
        Add a step definition.

        step_dict format example:
        {
            "step": "threshold",
            "input_key": "slope",
            "min": 0,
            "max": 5,
            "output_key": "low_slope"
        }
        """
        if "step" not in step_dict:
            raise ValueError("Step dictionary must contain 'step' key.")

        self.steps.append(step_dict)

    # --------------------------------------------------
    # Execute Workflow
    # --------------------------------------------------

    def execute(self, context):
        """
        Execute all workflow steps sequentially.

        Args:
            context: ContextManager instance

        Returns:
            Execution summary dictionary
        """

        for index, step in enumerate(self.steps):

            step_name = step["step"]

            try:
                context.add_log(f"Starting step {index + 1}: {step_name}")

                # Execute via registry
                result = self.registry.execute(
                    name=step_name,
                    context=context,
                    **{k: v for k, v in step.items() if k != "step"}
                )

                # Track results
                self.results[step_name] = result

                context.add_log(f"Completed step {index + 1}: {step_name}")

            except Exception as e:
                error_message = f"Error in step '{step_name}': {str(e)}"
                context.add_log(error_message)

                traceback.print_exc()

                return {
                    "status": "failed",
                    "failed_step": step_name,
                    "error": error_message,
                    "logs": context.get_logs()
                }

        return {
            "status": "success",
            "results": self.results,
            "logs": context.get_logs()
        }