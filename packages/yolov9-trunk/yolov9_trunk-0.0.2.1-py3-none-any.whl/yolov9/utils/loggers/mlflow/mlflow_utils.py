"""
MLFlow Logger for YOLOv9 Training

This logger sends training metrics, hyperparameters, and model artifacts to MLFlow,
which can be integrated with AWS SageMaker.

For more information on MLFlow:
https://mlflow.org/docs/latest/index.html
"""

import os
import sys
from pathlib import Path
from contextlib import contextmanager

try:
    import mlflow
    from mlflow import log_metric, log_param, log_artifact, log_artifacts
    from mlflow.tracking import MlflowClient
    assert hasattr(mlflow, '__version__')
except (ImportError, AssertionError):
    mlflow = None

try:
    import torch
except ImportError:
    torch = None


def _get_logger():
    """Get the logger for this module."""
    from utils.general import LOGGER
    return LOGGER


class MLFlowLogger:
    """
    Log training runs, datasets, models, and predictions to MLFlow.
    
    This logger sends information to MLFlow tracking server. By default, this information 
    includes hyperparameters, system configuration and metrics, model metrics, and basic 
    data metrics and analyses.
    
    Environment Variables:
        MLFLOW_TRACKING_URI: URI of the MLFlow tracking server (e.g., AWS SageMaker endpoint)
        MLFLOW_EXPERIMENT_NAME: Name of the MLFlow experiment
        MLFLOW_RUN_NAME: Name for this specific run (optional)
        MLFLOW_TRACKING_USERNAME: Username for MLFlow authentication (optional)
        MLFLOW_TRACKING_PASSWORD: Password for MLFlow authentication (optional)
    """
    
    def __init__(self, opt, run_id=None, job_type='Training'):
        """
        Initialize MLFlowLogger instance
        
        Arguments:
            opt (namespace): Commandline arguments for this run
            run_id (str): Run ID of MLFlow run to be resumed (optional)
            job_type (str): Job type for this run (default: 'Training')
        """
        self.opt = opt
        self.job_type = job_type
        self.mlflow = mlflow
        self.run = None
        self.run_id = run_id
        self.client = None
        
        # Get logger
        self.logger = _get_logger()
        
        if not mlflow:
            self.logger.warning('MLFlow is not installed. Run: pip install mlflow')
            return
        
        # Configure MLFlow tracking URI
        tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
            self.logger.info(f'MLFlow tracking URI set to: {tracking_uri}')
        else:
            self.logger.info('No MLFLOW_TRACKING_URI set, using local mlruns directory')
        
        # Set experiment name
        experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'yolov9-training')
        try:
            mlflow.set_experiment(experiment_name)
            self.logger.info(f'MLFlow experiment: {experiment_name}')
        except Exception as e:
            self.logger.error(f'Failed to set MLFlow experiment: {e}')
            return
        
        # Get run name
        run_name = os.getenv('MLFLOW_RUN_NAME', getattr(opt, 'name', 'yolov9-run'))
        
        # Start or resume run
        try:
            if run_id:
                # Resume existing run
                self.run = mlflow.start_run(run_id=run_id)
                self.logger.info(f'Resumed MLFlow run: {run_id}')
            else:
                # Start new run
                self.run = mlflow.start_run(run_name=run_name)
                self.run_id = self.run.info.run_id
                self.logger.info(f'Started MLFlow run: {self.run_id} ({run_name})')
            
            self.client = MlflowClient()
            
            # Log hyperparameters
            if hasattr(opt, 'hyp') and opt.hyp:
                self._log_hyperparameters(opt.hyp)
            
            # Log configuration parameters
            self._log_config(opt)
            
        except Exception as e:
            self.logger.error(f'Failed to initialize MLFlow run: {e}')
            self.run = None
    
    def _log_hyperparameters(self, hyp):
        """Log hyperparameters to MLFlow."""
        if not self.run:
            return
        
        try:
            for key, value in hyp.items():
                if isinstance(value, (int, float, str, bool)):
                    mlflow.log_param(f'hyp_{key}', value)
        except Exception as e:
            self.logger.warning(f'Failed to log hyperparameters: {e}')
    
    def _log_config(self, opt):
        """Log configuration parameters to MLFlow."""
        if not self.run:
            return
        
        try:
            # Log important configuration parameters
            params_to_log = [
                'epochs', 'batch_size', 'imgsz', 'weights', 'cfg', 'data',
                'optimizer', 'device', 'workers', 'project', 'name',
                'single_cls', 'image_weights', 'multi_scale', 'resume',
                'cos_lr', 'flat_cos_lr', 'fixed_lr', 'label_smoothing',
                'patience', 'seed'
            ]
            
            for param in params_to_log:
                if hasattr(opt, param):
                    value = getattr(opt, param)
                    if isinstance(value, (int, float, str, bool)):
                        mlflow.log_param(param, value)
                    elif isinstance(value, Path):
                        mlflow.log_param(param, str(value))
        except Exception as e:
            self.logger.warning(f'Failed to log configuration: {e}')
    
    def log(self, metrics_dict, step=None):
        """
        Log metrics to MLFlow.
        
        Arguments:
            metrics_dict (dict): Dictionary of metrics to log
            step (int): Step number (epoch or batch number)
        """
        if not self.run:
            return
        
        try:
            for key, value in metrics_dict.items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(key, value, step=step)
        except Exception as e:
            self.logger.warning(f'Failed to log metrics: {e}')
    
    def log_metric(self, key, value, step=None):
        """Log a single metric to MLFlow."""
        if not self.run:
            return
        
        try:
            mlflow.log_metric(key, value, step=step)
        except Exception as e:
            self.logger.warning(f'Failed to log metric {key}: {e}')
    
    def log_param(self, key, value):
        """Log a single parameter to MLFlow."""
        if not self.run:
            return
        
        try:
            mlflow.log_param(key, value)
        except Exception as e:
            self.logger.warning(f'Failed to log parameter {key}: {e}')
    
    def log_artifact(self, file_path, artifact_path=None):
        """
        Log an artifact (file) to MLFlow.
        
        Arguments:
            file_path (str or Path): Path to the file to log
            artifact_path (str): Path within the artifact directory (optional)
        """
        if not self.run:
            return
        
        try:
            file_path = Path(file_path)
            if file_path.exists():
                mlflow.log_artifact(str(file_path), artifact_path=artifact_path)
        except Exception as e:
            self.logger.warning(f'Failed to log artifact {file_path}: {e}')
    
    def log_artifacts(self, dir_path, artifact_path=None):
        """
        Log all files in a directory as artifacts.
        
        Arguments:
            dir_path (str or Path): Path to the directory
            artifact_path (str): Path within the artifact directory (optional)
        """
        if not self.run:
            return
        
        try:
            dir_path = Path(dir_path)
            if dir_path.exists() and dir_path.is_dir():
                mlflow.log_artifacts(str(dir_path), artifact_path=artifact_path)
        except Exception as e:
            self.logger.warning(f'Failed to log artifacts from {dir_path}: {e}')
    
    def log_model(self, model_path, model_name='model', register=False):
        """
        Log a PyTorch model to MLFlow.
        
        Arguments:
            model_path (str or Path): Path to the model checkpoint
            model_name (str): Name for the model
            register (bool): Whether to register the model in MLFlow Model Registry
        """
        if not self.run or not torch:
            return
        
        try:
            model_path = Path(model_path)
            if model_path.exists():
                # Log as artifact
                self.log_artifact(model_path, artifact_path='models')
                
                # Optionally register in model registry
                if register:
                    try:
                        # Log model with MLFlow PyTorch flavor
                        mlflow.pytorch.log_model(
                            torch.load(model_path, map_location='cpu'),
                            artifact_path=model_name,
                            registered_model_name=model_name
                        )
                        self.logger.info(f'Registered model: {model_name}')
                    except Exception as e:
                        self.logger.warning(f'Failed to register model: {e}')
        except Exception as e:
            self.logger.warning(f'Failed to log model {model_path}: {e}')
    
    def log_image(self, image_path, artifact_path='images'):
        """
        Log an image to MLFlow.
        
        Arguments:
            image_path (str or Path): Path to the image
            artifact_path (str): Path within the artifact directory
        """
        self.log_artifact(image_path, artifact_path=artifact_path)
    
    def log_images(self, image_paths, artifact_path='images'):
        """
        Log multiple images to MLFlow.
        
        Arguments:
            image_paths (list): List of image paths
            artifact_path (str): Path within the artifact directory
        """
        if not self.run:
            return
        
        for img_path in image_paths:
            self.log_image(img_path, artifact_path=artifact_path)
    
    def set_tag(self, key, value):
        """Set a tag for the run."""
        if not self.run:
            return
        
        try:
            mlflow.set_tag(key, value)
        except Exception as e:
            self.logger.warning(f'Failed to set tag {key}: {e}')
    
    def end_run(self, status='FINISHED'):
        """
        End the MLFlow run.
        
        Arguments:
            status (str): Status of the run ('FINISHED', 'FAILED', 'KILLED')
        """
        if not self.run:
            return
        
        try:
            mlflow.end_run(status=status)
            self.logger.info(f'Ended MLFlow run: {self.run_id}')
            self.run = None
        except Exception as e:
            self.logger.error(f'Failed to end MLFlow run: {e}')
    
    def finish_run(self):
        """Finish the run (alias for end_run)."""
        self.end_run(status='FINISHED')
    
    # Callback methods to match the interface expected by Loggers class
    
    def on_pretrain_routine_start(self):
        """Called at the beginning of pre-train routine."""
        if self.run:
            self.set_tag('stage', 'pretrain')
    
    def on_pretrain_routine_end(self):
        """Called at the end of pre-train routine."""
        pass
    
    def on_train_start(self):
        """Called at the start of training."""
        if self.run:
            self.set_tag('stage', 'training')
    
    def on_train_epoch_start(self, epoch):
        """Called at the start of each training epoch."""
        pass
    
    def on_train_batch_end(self, metrics, step):
        """Called at the end of each training batch."""
        self.log(metrics, step=step)
    
    def on_train_epoch_end(self, epoch):
        """Called at the end of each training epoch."""
        pass
    
    def on_val_start(self):
        """Called at the start of validation."""
        pass
    
    def on_val_end(self):
        """Called at the end of validation."""
        pass
    
    def on_fit_epoch_end(self, metrics, epoch):
        """Called at the end of each fit epoch (train + validation)."""
        self.log(metrics, step=epoch)
    
    def on_model_save(self, model_path, epoch, final_epoch, best_fitness, current_fitness):
        """
        Called when a model checkpoint is saved.
        
        Arguments:
            model_path (Path): Path to the saved model
            epoch (int): Current epoch
            final_epoch (bool): Whether this is the final epoch
            best_fitness (float): Best fitness score so far
            current_fitness (float): Current fitness score
        """
        if not self.run:
            return
        
        try:
            # Log the model as artifact
            self.log_model(model_path)
            
            # Log fitness metrics
            self.log_metric('fitness/best', best_fitness, step=epoch)
            self.log_metric('fitness/current', current_fitness, step=epoch)
            
            # If this is the best model, tag it
            if best_fitness == current_fitness:
                self.set_tag('best_epoch', epoch)
                self.set_tag('best_fitness', best_fitness)
        except Exception as e:
            self.logger.warning(f'Failed in on_model_save: {e}')
    
    def on_train_end(self, results, save_dir):
        """
        Called at the end of training.
        
        Arguments:
            results (tuple): Final results (P, R, mAP@.5, mAP@.5-.95, val_loss)
            save_dir (Path): Directory where results are saved
        """
        if not self.run:
            return
        
        try:
            # Log final results
            if len(results) >= 7:
                metrics = {
                    'final/precision': results[0],
                    'final/recall': results[1],
                    'final/mAP_0.5': results[2],
                    'final/mAP_0.5:0.95': results[3],
                    'final/val_box_loss': results[4],
                    'final/val_obj_loss': results[5],
                    'final/val_cls_loss': results[6],
                }
                self.log(metrics)
            
            # Log result artifacts (plots, CSVs, etc.)
            if save_dir and Path(save_dir).exists():
                result_files = [
                    'results.csv', 'results.png', 'confusion_matrix.png',
                    'F1_curve.png', 'PR_curve.png', 'P_curve.png', 'R_curve.png',
                    'labels.jpg', 'labels_correlogram.jpg'
                ]
                
                for filename in result_files:
                    file_path = Path(save_dir) / filename
                    if file_path.exists():
                        self.log_artifact(file_path, artifact_path='results')
            
            # Set completion tag
            self.set_tag('status', 'completed')
        except Exception as e:
            self.logger.warning(f'Failed in on_train_end: {e}')
    
    def on_params_update(self, params):
        """
        Called when parameters are updated.
        
        Arguments:
            params (dict): Dictionary of parameters to update
        """
        if not self.run:
            return
        
        try:
            for key, value in params.items():
                if isinstance(value, (int, float, str, bool)):
                    self.log_param(f'updated_{key}', value)
        except Exception as e:
            self.logger.warning(f'Failed to update params: {e}')
    
    @property
    def data_dict(self):
        """Return data dictionary (for compatibility with other loggers)."""
        return None


@contextmanager
def mlflow_logging_disabled():
    """
    Context manager to temporarily disable MLFlow logging.
    Useful for preventing log spam during certain operations.
    """
    if mlflow:
        original_autolog = mlflow.autolog
        mlflow.autolog(disable=True)
        try:
            yield
        finally:
            mlflow.autolog(disable=False)
    else:
        yield


def is_mlflow_available():
    """Check if MLFlow is available and properly configured."""
    if not mlflow:
        return False
    
    try:
        # Try to get the current experiment
        mlflow.get_experiment_by_name('test')
        return True
    except Exception:
        return False

