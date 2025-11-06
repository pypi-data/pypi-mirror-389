import os
import warnings
from pathlib import Path

import torch
from torch.utils.tensorboard import SummaryWriter
from utils.general import LOGGER, colorstr, cv2
from utils.loggers.mlflow.mlflow_utils import MLFlowLogger
from utils.plots import plot_images, plot_labels, plot_results
from utils.torch_utils import de_parallel

LOGGERS = ('csv', 'tb', 'mlflow')  # *.csv, TensorBoard, MLFlow
RANK = int(os.getenv('RANK', -1))

try:
    import mlflow
    
    assert hasattr(mlflow, '__version__')  # verify package import not local dir
except (ImportError, AssertionError):
    mlflow = None


class Loggers():
    # YOLO Loggers class
    def __init__(self, save_dir=None, weights=None, opt=None, hyp=None, logger=None, include=LOGGERS):
        self.save_dir = save_dir
        self.weights = weights
        self.opt = opt
        self.hyp = hyp
        self.plots = not opt.noplots  # plot results
        self.logger = logger  # for printing results to console
        self.include = include
        self.keys = [
            'train/box_loss',
            'train/cls_loss',
            'train/dfl_loss',  # train loss
            'metrics/precision',
            'metrics/recall',
            'metrics/mAP_0.5',
            'metrics/mAP_0.5:0.95',  # metrics
            'val/box_loss',
            'val/cls_loss',
            'val/dfl_loss',  # val loss
            'x/lr0',
            'x/lr1',
            'x/lr2'
        ]  # params
        self.best_keys = ['best/epoch', 'best/precision', 'best/recall', 'best/mAP_0.5', 'best/mAP_0.5:0.95']
        for k in LOGGERS:
            setattr(self, k, None)  # init empty logger dictionary
        self.csv = True  # always log to csv

        # Messages
        if not mlflow:
            prefix = colorstr('MLFlow: ')
            s = f"{prefix}run 'pip install mlflow boto3' to automatically track and visualize YOLO 🚀 runs in MLFlow"
            self.logger.info(s)
        
        # TensorBoard
        s = self.save_dir
        if 'tb' in self.include and not self.opt.evolve:
            prefix = colorstr('TensorBoard: ')
            self.logger.info(
                f"{prefix}Start with 'tensorboard --logdir {s.parent}', view at http://localhost:6006/")
            self.tb = SummaryWriter(str(s))

        # MLFlow
        if mlflow and 'mlflow' in self.include:
            mlflow_artifact_resume = isinstance(self.opt.resume, str) and self.opt.resume.startswith('mlflow://')
            run_id = None
            if self.opt.resume and mlflow_artifact_resume:
                # Extract run_id from mlflow://run_id format
                run_id = self.opt.resume.split('://')[-1]
            self.mlflow_logger = MLFlowLogger(self.opt, run_id)
        else:
            self.mlflow_logger = None

    @property
    def remote_dataset(self):
        # Get data_dict if custom dataset artifact link is provided
        data_dict = None
        if self.mlflow_logger:
            data_dict = self.mlflow_logger.data_dict
        return data_dict

    def on_train_start(self):
        if self.mlflow_logger:
            self.mlflow_logger.on_train_start()

    def on_pretrain_routine_start(self):
        if self.mlflow_logger:
            self.mlflow_logger.on_pretrain_routine_start()

    def on_pretrain_routine_end(self, labels, names):
        # Callback runs on pre-train routine end
        if self.plots:
            plot_labels(labels, names, self.save_dir)
            paths = self.save_dir.glob('*labels*.jpg')  # training labels
            if self.mlflow_logger:
                for path in paths:
                    self.mlflow_logger.log_image(path, artifact_path='labels')

    def on_train_batch_end(self, model, ni, imgs, targets, paths, vals):
        log_dict = dict(zip(self.keys[0:3], vals))
        # Callback runs on train batch end
        # ni: number integrated batches (since train start)
        if self.plots:
            if ni < 3:
                f = self.save_dir / f'train_batch{ni}.jpg'  # filename
                plot_images(imgs, targets, paths, f)
                if ni == 0 and self.tb and not self.opt.sync_bn:
                    log_tensorboard_graph(self.tb, model, imgsz=(self.opt.imgsz, self.opt.imgsz))

        if self.mlflow_logger:
            self.mlflow_logger.on_train_batch_end(log_dict, step=ni)

    def on_train_epoch_end(self, epoch):
        # Callback runs on train epoch end
        if self.mlflow_logger:
            self.mlflow_logger.on_train_epoch_end(epoch)

    def on_val_start(self):
        if self.mlflow_logger:
            self.mlflow_logger.on_val_start()

    def on_val_image_end(self, pred, predn, path, names, im):
        # Callback runs on val image end
        pass  # No image-level validation logging for now

    def on_val_batch_end(self, batch_i, im, targets, paths, shapes, out):
        # Callback runs on val batch end
        pass  # No batch-level validation logging for now

    def on_val_end(self, nt, tp, fp, p, r, f1, ap, ap50, ap_class, confusion_matrix):
        # Callback runs on val end
        if self.mlflow_logger:
            files = sorted(self.save_dir.glob('val*.jpg'))
            for f in files:
                self.mlflow_logger.log_image(f, artifact_path='validation')
            self.mlflow_logger.on_val_end()

    def on_fit_epoch_end(self, vals, epoch, best_fitness, fi):
        # Callback runs at the end of each fit (train+val) epoch
        x = dict(zip(self.keys, vals))
        
        # CSV logging
        if self.csv:
            file = self.save_dir / 'results.csv'
            n = len(x) + 1  # number of cols
            s = '' if file.exists() else (
                ('%20s,' * n % tuple(['epoch'] + self.keys)).rstrip(',') + '\n')  # add header
            with open(file, 'a') as f:
                f.write(s + ('%20.5g,' * n % tuple([epoch] + vals)).rstrip(',') + '\n')

        # TensorBoard logging
        if self.tb:
            for k, v in x.items():
                self.tb.add_scalar(k, v, epoch)

        # MLFlow logging
        if self.mlflow_logger:
            self.mlflow_logger.on_fit_epoch_end(x, epoch)

    def on_model_save(self, last, epoch, final_epoch, best_fitness, fi):
        # Callback runs on model save event
        if self.mlflow_logger:
            self.mlflow_logger.on_model_save(last, epoch, final_epoch, best_fitness, fi)

    def on_train_end(self, last, best, epoch, results):
        # Callback runs on training end, i.e. saving best model
        if self.plots:
            plot_results(file=self.save_dir / 'results.csv')  # save results.png
        files = ['results.png', 'confusion_matrix.png', *(f'{x}_curve.png' for x in ('F1', 'PR', 'P', 'R'))]
        files = [(self.save_dir / f) for f in files if (self.save_dir / f).exists()]  # filter
        self.logger.info(f"Results saved to {colorstr('bold', self.save_dir)}")

        # TensorBoard logging
        if self.tb:
            for f in files:
                self.tb.add_image(f.stem, cv2.imread(str(f))[..., ::-1], epoch, dataformats='HWC')

        # MLFlow logging
        if self.mlflow_logger:
            self.mlflow_logger.on_train_end(results, self.save_dir)
            self.mlflow_logger.finish_run()

    def on_params_update(self, params: dict):
        # Update hyperparams or configs of the experiment
        if self.mlflow_logger:
            self.mlflow_logger.on_params_update(params)


class GenericLogger:
    """
    YOLO General purpose logger for non-task specific logging
    Usage: from utils.loggers import GenericLogger; logger = GenericLogger(...)
    Arguments
        opt:             Run arguments
        console_logger:  Console logger
        include:         loggers to include
    """

    def __init__(self, opt, console_logger, include=('tb', 'mlflow')):
        # init default loggers
        self.save_dir = Path(opt.save_dir)
        self.include = include
        self.console_logger = console_logger
        self.csv = self.save_dir / 'results.csv'  # CSV logger
        
        if 'tb' in self.include:
            prefix = colorstr('TensorBoard: ')
            self.console_logger.info(
                f"{prefix}Start with 'tensorboard --logdir {self.save_dir.parent}', view at http://localhost:6006/"
            )
            self.tb = SummaryWriter(str(self.save_dir))
        else:
            self.tb = None

        if mlflow and 'mlflow' in self.include:
            self.mlflow_logger = MLFlowLogger(opt, run_id=None)
        else:
            self.mlflow_logger = None

    def log_metrics(self, metrics, epoch):
        # Log metrics dictionary to all loggers
        if self.csv:
            keys, vals = list(metrics.keys()), list(metrics.values())
            n = len(metrics) + 1  # number of cols
            s = '' if self.csv.exists() else (
                ('%23s,' * n % tuple(['epoch'] + keys)).rstrip(',') + '\n')  # header
            with open(self.csv, 'a') as f:
                f.write(s + ('%23.5g,' * n % tuple([epoch] + vals)).rstrip(',') + '\n')

        if self.tb:
            for k, v in metrics.items():
                self.tb.add_scalar(k, v, epoch)

        if self.mlflow_logger:
            self.mlflow_logger.log(metrics, step=epoch)

    def log_images(self, files, name='Images', epoch=0):
        # Log images to all loggers
        files = [Path(f) for f in (files if isinstance(files, (tuple, list)) else [files])]  # to Path
        files = [f for f in files if f.exists()]  # filter by exists

        if self.tb:
            for f in files:
                self.tb.add_image(f.stem, cv2.imread(str(f))[..., ::-1], epoch, dataformats='HWC')

        if self.mlflow_logger:
            for f in files:
                self.mlflow_logger.log_image(f, artifact_path=name)

    def log_graph(self, model, imgsz=(640, 640)):
        # Log model graph to all loggers
        if self.tb:
            log_tensorboard_graph(self.tb, model, imgsz)

    def log_model(self, model_path, epoch=0, metadata={}):
        # Log model to all loggers
        if self.mlflow_logger:
            self.mlflow_logger.log_model(model_path)

    def update_params(self, params):
        # Update the parameters logged
        if self.mlflow_logger:
            self.mlflow_logger.on_params_update(params)


def log_tensorboard_graph(tb, model, imgsz=(640, 640)):
    # Log model graph to TensorBoard
    try:
        p = next(model.parameters())  # for device, type
        imgsz = (imgsz, imgsz) if isinstance(imgsz, int) else imgsz  # expand
        im = torch.zeros(
            (1, 3, *imgsz)).to(p.device).type_as(p)  # input image (WARNING: must be zeros, not empty)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')  # suppress jit trace warning
            tb.add_graph(torch.jit.trace(de_parallel(model), im, strict=False), [])
    except Exception as e:
        LOGGER.warning(f'WARNING ⚠️ TensorBoard graph visualization failure {e}')


def web_project_name(project):
    # Convert local project name to web project name
    if not project.startswith('runs/train'):
        return project
    suffix = '-Classify' if project.endswith('-cls') else '-Segment' if project.endswith('-seg') else ''
    return f'YOLO{suffix}'
