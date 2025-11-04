from pathlib import Path
from typing import Dict, List, Optional, Set
import tempfile
import os
import subprocess

from snakemake.api import (
    SnakemakeApi,
    OutputSettings,
    ResourceSettings,
    StorageSettings,
    WorkflowSettings,
    ConfigSettings,
    DAGSettings,
    ExecutionSettings,
    DeploymentSettings,
    SchedulingSettings,
    RemoteExecutionSettings,
    GroupSettings,
)
from snakemake.rules import Rule
from snakemake.ruleinfo import RuleInfo


class SnakemakeExecutor:
    """
    Handles execution of PDP tasks using the Snakemake API by creating rules programmatically.
    """
    
    def __init__(self, cores: int = 1, executor: str = "local", verbose: bool = False):
        self.cores = cores
        self.executor = executor
        self.verbose = verbose
        
    def execute_task_hierarchy(self, root_task, project_root: Path) -> int:
        """
        Execute a task hierarchy using Snakemake API by creating rules programmatically.
        
        Args:
            root_task: The root task to execute
            project_root: Path to the project root
            
        Returns:
            0 if successful, 1 if failed
        """
        try:
            # Check if any tasks use SLURM
            has_slurm_tasks = self._check_for_slurm_tasks(root_task)
            if has_slurm_tasks and self.executor == "local":
                print("Detected SLURM tasks. Consider using --executor slurm for proper SLURM execution.")
            
            with SnakemakeApi(
                OutputSettings(
                    verbose=self.verbose,
                    show_failed_logs=True,
                )
            ) as snakemake_api:
                # Create workflow API with an empty snakefile (we'll add rules programmatically)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.smk', delete=False) as temp_snakefile:
                    temp_snakefile.write("# Programmatically generated workflow\n")
                    temp_snakefile_path = temp_snakefile.name
                
                try:
                    workflow_api = snakemake_api.workflow(
                        snakefile=temp_snakefile_path,
                        resource_settings=ResourceSettings(cores=self.cores),
                        storage_settings=StorageSettings(),
                        workflow_settings=WorkflowSettings(),
                        config_settings=ConfigSettings(),
                        workdir=project_root,
                    )
                    
                    # Generate rules from task hierarchy
                    self._generate_workflow_rules(workflow_api, root_task, project_root)
                    
                    # Create DAG and execute
                    dag_api = workflow_api.dag(
                        dag_settings=DAGSettings()
                    )
                    
                    # Execute the workflow
                    dag_api.execute_workflow(
                        executor=self.executor,
                        execution_settings=ExecutionSettings(),
                        remote_execution_settings=RemoteExecutionSettings(),
                        scheduling_settings=SchedulingSettings(),
                        group_settings=GroupSettings(),
                    )
                finally:
                    # Clean up temp file
                    os.unlink(temp_snakefile_path)
                
                return 0
                
        except Exception as e:
            print(f"Snakemake execution failed: {e}")
            return 1
    
    def _generate_workflow_rules(self, workflow_api, task, project_root: Path, parent_outputs: List[str] = None):
        """
        Recursively generate Snakemake rules from the task hierarchy.
        
        Args:
            workflow_api: The Snakemake WorkflowApi instance
            task: Current task to process
            project_root: Path to project root
            parent_outputs: List of parent task output files (for dependencies)
        """
        # Get inputs and outputs for this task
        task_inputs = self._get_task_inputs(task, parent_outputs or [], project_root)
        task_outputs = self._get_task_outputs(task, project_root)
        
        # Generate rule for this task if it has an entrypoint
        current_outputs = task_outputs
        if task.entrypoint:
            rule_name = self._get_rule_name(task)
            self._create_task_rule(workflow_api, rule_name, task, task_inputs, task_outputs, project_root)
        else:
            # If no entrypoint, pass through parent outputs
            current_outputs = parent_outputs or []
        
        # Recursively process subtasks
        for subtask in task.subtasks:
            self._generate_workflow_rules(workflow_api, subtask, project_root, current_outputs)
    
    def _get_rule_name(self, task) -> str:
        """Generate a valid Snakemake rule name from task name."""
        # Replace invalid characters with underscores
        rule_name = task.task_name.replace('/', '_').replace('-', '_').replace(' ', '_')
        # Ensure it starts with a letter or underscore
        if rule_name and not (rule_name[0].isalpha() or rule_name[0] == '_'):
            rule_name = f"task_{rule_name}"
        return rule_name or "task"
    
    def _get_task_inputs(self, task, parent_outputs: List[str], project_root: Path) -> List[str]:
        """Get input files for a task."""
        inputs = []
        
        # Add parent task outputs as inputs (dependencies)
        inputs.extend(parent_outputs)
        
        # Add files from input directory if it exists
        if task.input_folder.exists():
            for file_path in task.input_folder.rglob("*"):
                if file_path.is_file():
                    # Make path relative to project root
                    try:
                        rel_path = file_path.relative_to(project_root)
                        inputs.append(str(rel_path))
                    except ValueError:
                        # If file is not under project root, use absolute path
                        inputs.append(str(file_path))
        
        return inputs
    
    def _get_task_outputs(self, task, project_root: Path) -> List[str]:
        """Get expected output files for a task."""
        outputs = []
        
        # Create a marker file to indicate task completion
        try:
            task_rel_path = task.task_directory.relative_to(project_root)
            output_marker = task_rel_path / "output" / ".task_complete"
            outputs.append(str(output_marker))
        except ValueError:
            # If task directory is not under project root, use absolute path
            output_marker = task.task_directory / "output" / ".task_complete"
            outputs.append(str(output_marker))
        
        return outputs
    
    def _check_for_slurm_tasks(self, task) -> bool:
        """Recursively check if any tasks in the hierarchy use SLURM."""
        if hasattr(task, 'task_config') and task.task_config.uses_slurm:
            return True
        
        for subtask in getattr(task, 'subtasks', []):
            if self._check_for_slurm_tasks(subtask):
                return True
        
        return False
    
    def _create_task_rule(self, workflow_api, rule_name: str, task, inputs: List[str], outputs: List[str], project_root: Path):
        """
        Create a Snakemake rule for a task using the workflow API's internal rule system.
        
        Args:
            workflow_api: The Snakemake WorkflowApi instance
            rule_name: Name of the rule
            task: The task object
            inputs: List of input files
            outputs: List of output files
            project_root: Path to project root
        """
        # Get the relative path to the task directory
        try:
            task_dir_rel = task.task_directory.relative_to(project_root)
        except ValueError:
            task_dir_rel = task.task_directory
        
        # Create a run function for the rule
        def run_func(wildcards, input, output, params, threads, resources, log, version, rule, conda_env, container_img, singularity_args, use_singularity, env_modules, bench_record, jobid, is_shell, bench_iteration, cleanup_scripts, shadow_dir, edit_notebook, conda_base_path, basedir, runtime_sourcecache_path):
            """Run function that will be executed by Snakemake for this rule."""
            # Change to task directory
            original_cwd = os.getcwd()
            os.chdir(str(task.task_directory))
            
            try:
                # Create output directory
                output_dir = task.task_directory / "output"
                output_dir.mkdir(exist_ok=True)
                
                # Execute the task's entrypoint
                if task.task_config.uses_slurm:
                    # For SLURM tasks, check if we should use the SLURM script or entrypoint
                    if task.task_config.slurm_script:
                        # Use the SLURM script if defined
                        script_path = task.task_directory / task.task_config.slurm_script
                        if script_path.exists():
                            # When using Snakemake with a SLURM executor, we run the entrypoint
                            # The SLURM executor will handle job submission automatically
                            result = subprocess.run(task.entrypoint, shell=True, cwd=task.task_directory)
                        else:
                            raise Exception(f"SLURM script not found: {script_path}")
                    else:
                        result = subprocess.run(task.entrypoint, shell=True, cwd=task.task_directory)
                else:
                    result = subprocess.run(task.entrypoint, shell=True, cwd=task.task_directory)
                
                if result.returncode == 0:
                    # Create completion marker
                    marker_file = output_dir / ".task_complete"
                    marker_file.touch()
                else:
                    raise Exception(f"Task {task.task_name} failed with return code {result.returncode}")
                    
            finally:
                os.chdir(original_cwd)
        
        # Create the rule using workflow's internal mechanism
        rule = Rule(rule_name, workflow_api._workflow)
        
        # Set inputs if any
        if inputs:
            rule.set_input(*inputs)
        
        # Set outputs
        rule.set_output(*outputs)
        
        # Set the run function
        rule.run_func = run_func
        
        # Set resources (cores = 1 by default)
        rule.resources = {"_cores": 1, "_nodes": 1}
        
        # Add the rule to the workflow
        workflow_api._workflow.add_rule(rule)
        
        print(f"Created rule: {rule_name} with inputs: {inputs} and outputs: {outputs}")
    
    def _get_relative_path(self, path: Path, base: Path) -> str:
        """Get relative path, falling back to absolute if not under base."""
        try:
            return str(path.relative_to(base))
        except ValueError:
            return str(path)