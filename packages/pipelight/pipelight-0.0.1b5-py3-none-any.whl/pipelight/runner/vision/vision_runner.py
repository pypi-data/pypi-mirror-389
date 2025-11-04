from typing import Callable, Optional, Tuple, Union, Sequence, Any, Dict, Sequence
from functools import partial
import torch
from torch import nn
from ..model_runner import ModelRunner
from ...utils.binder import binder


class VisionRunner(ModelRunner):
    def __init__(
        self,
        model: nn.Module,
        target_data_getter: Callable[[torch.Tensor], torch.Tensor],
        source_data_getter: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
        additional_data_getter: Optional[Callable[[torch.Tensor], Union[torch.Tensor, Tuple[torch.Tensor, ...]]]] = None,
        *args,
        metrics: Union[Callable[[torch.Tensor], torch.Tensor], Sequence[Callable[[torch.Tensor], torch.Tensor]], None] = None,
        global_metrics: Union[Callable[[torch.Tensor], torch.Tensor], Sequence[Callable[[torch.Tensor], torch.Tensor]], None] = None,
        features_extractor: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
        feature_metrics: Union[Callable[[torch.Tensor], torch.Tensor], Sequence[Callable[[torch.Tensor], torch.Tensor]], None] = None,
        **kwargs
    ):
        """
        Args:
            model (nn.Module): The model for the runner.
            target_data_getter (Callable[[torch.Tensor], torch.Tensor]):
                The target input data for the task.
            source_data_getter (Optional[Callable[[torch.Tensor], torch.Tensor]]):
                The source data that may be used to translate the source data into the target data.
                If ``None``, no translation task will be runned.
            additional_data_getter (Optional[Callable[[torch.Tensor], Union[torch.Tensor, Tuple[torch.Tensor, ...]]]]):
                The data that is not regarding to the direct main task, but may be for guidance. If ``None``,
                no other data will be used.
            *args
            metrics (Union[Callable[[torch.Tensor], torch.Tensor], Sequence[Callable[[torch.Tensor], torch.Tensor]], None]):
                The metrics list that contains all metrics calculation function, used after each validation and test step.
            global_metrics (Union[Callable[[torch.Tensor], torch.Tensor], Sequence[Callable[[torch.Tensor], torch.Tensor]], None]):
                The metrics list that contains all metrics calculation function, used in the total collected results and ground
                truth. When it is not ``None`` or empty, generation collection will be automatically available to obtain.
            features_extractor (Optional[Callable[[torch.Tensor], torch.Tensor]]): The extractor that extracts
                the features from the ground truth and the generated results.
            feature_metrics (Union[Callable[[torch.Tensor], torch.Tensor], Sequence[Callable[[torch.Tensor], torch.Tensor]], None]):
                The metrics that are calculated from the extracted features in the end of the validation and test epoch.
            **kwargs
        
        """
        super().__init__(model, *args, **kwargs)
        self.__test_collection = self.__validation_collection = None
        self.__generation = self.__target = None
        
        for collection_prefix in ('validation', 'test'):
            collection_prefix = f'_{__class__.__name__}__{collection_prefix}'
            generation_features_name = f'{collection_prefix}_generation_features'
            target_features_name = f'{collection_prefix}_target_features'
            super().__setattr__(generation_features_name, [])
            super().__setattr__(target_features_name, [])
        
        self.target_data_getter = target_data_getter
        self.source_data_getter = source_data_getter
        self.additional_data_getter = additional_data_getter
        
        self.metrics = _to_sequence(metrics)
        self.global_metrics = _to_sequence(global_metrics)
        self.features_extractor = features_extractor
        self.feature_metrics = _to_sequence(feature_metrics)
    
    @property
    def metrics(self):
        return self.__metrics
    
    @metrics.setter
    def metrics(self, value):
        self.__metrics = {_get_metric_name(metric) : metric for metric in value}
    
    def get_target_data(self, batch: torch.Tensor) -> torch.Tensor:
        return self.target_data_getter(batch)
    
    def get_source_data(self, batch: torch.Tensor) -> Optional[torch.Tensor]:
        if self.source_data_getter is not None:
            return self.source_data_getter(batch)
    
    def get_additional_data(self, batch: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        return _tuplize(self.additional_data_getter, batch)
    
    def extract_features(self, batch: torch.Tensor) -> Optional[torch.Tensor]:
        if self.features_extractor is not None:
            return self.features_extractor(batch)
    
    def process_training_step_mean_metrics(self, loss):
        self.log('Loss', loss, prog_bar=True, logger=True, on_step=True, on_epoch=True, sync_dist=True)
    
    def generate(self, batch: torch.Tensor, shape: Sequence[int], data: Tuple[torch.Tensor, ...], target: Optional[torch.Tensor] = None) -> Union[torch.Tensor, Tuple[torch.Tensor, ...]]:
        """Returns the generation.

        Args:
            batch (torch.Tensor): The output of your data iterable, normally a :class:`~torch.utils.data.DataLoader`.
            shape (Sequence[int]): The expected shape of the generation.
            data (Tuple[torch.Tensor, ...]): The data used for generating.
            target (Optional[torch.Tensor]): The main target data, sometimes it is necessary.
        
        Returns:
            out: The generation. It can be a batch of images, or a tuple of generated results, where the leading element should be the main
                generation used for the evaluation.
        
        """
        pass
    
    def make_comparison(self, batch: torch.Tensor) -> Tuple[torch.Tensor, Tuple[torch.Tensor, ...], Optional[torch.Tensor], Tuple[torch.Tensor, ...], torch.Tensor, Tuple[torch.Tensor, ...], Optional[Dict[str, Tuple[tuple, Dict[str, Any]]]]]:
        target_data: Union[torch.Tensor, Tuple[torch.Tensor, ...]] = self.get_target_data(batch)
        source_data: Optional[torch.Tensor] = self.get_source_data(batch)
        additional_data: Tuple[torch.Tensor, ...] = self.get_additional_data(batch)
        if isinstance(target_data, Tuple):
            other_target_data: Tuple[torch.Tensor, ...] = target_data[1:]
            target_data: torch.Tensor = target_data[0]
        else:
            other_target_data = tuple()
        if source_data is None:
            input_data = additional_data
        else:
            input_data = (source_data, *additional_data)
        generation_data = self.generate(batch, target_data.shape, input_data, target_data)
        if isinstance(generation_data, Tuple):
            other_generation_data: Tuple[torch.Tensor] = generation_data[1:]
            generation_data: torch.Tensor = generation_data[0]
        else:
            other_generation_data = tuple()
        return generation_data, other_generation_data, source_data, additional_data, target_data, other_target_data, None
    
    def calculate_metrics(self, generation: torch.Tensor, target: torch.Tensor, arguments: Optional[Dict[str, binder]] = None) -> Dict[str, torch.Tensor]:
        def generate_metrics():
            if arguments is None:
                for metric_name, metric in self.__metrics.items():
                    yield metric_name, metric(generation, target)
            else:
                for metric_name, metric in self.__metrics.items():
                    current_arguments = arguments.get(metric_name)
                    yield metric_name, current_arguments.invoke(partial(metric, generation, target))
        return dict(generate_metrics())
    
    @torch.inference_mode()
    def __evaluate_result(self, batch, batch_idx, log_prefix: Optional[str] = None, sync_to_logger: bool = True, return_images: bool = False):
        """Evaluates the batch step.

        Args:
            batch: The output of your data iterable, normally a :class:`~torch.utils.data.DataLoader`.
            batch_idx: The index of this batch.
            log_prefix (Optional[str]): The string that tells the evaluation type, for example, 'val' or 'test'.
            sync_to_logger (bool): The flag that controls whether sync the metrics to the logger.
            return_images (bool): The flag that controls whether adding the sampled and original images into
                the returned dictionary.
        
        """
        generation_data, other_generation_data, source_data, _, target_data, other_target_data, arguments = self.make_comparison(batch)
        metric_values = self.calculate_metrics(generation_data, target_data, arguments)
        features = self.extract_features(generation_data), self.extract_features(target_data)
        if log_prefix is None or log_prefix == '':
            collection_dict = metric_values
        else:
            collection_dict = {f'{log_prefix}-{key}' : value for key, value in metric_values.items()}
        if len(collection_dict) > 0:
            self.log_dict({key : value.mean() for key, value in collection_dict.items()}, logger=sync_to_logger, on_step=True, on_epoch=True, sync_dist=True)
        function_result = metric_values, features
        if return_images:
            function_result = *function_result, (generation_data.cpu(), *(obj.cpu() for obj in other_generation_data)), (target_data.cpu(), *(obj.cpu() for obj in other_target_data)), None if source_data is None else source_data.cpu()
            # else:
                # function_result = *function_result, generation_data.cpu(), target_data.cpu(), None if source_data is None else source_data.cpu()
        return function_result
    
    def __yield_each_collection(self, evaluation):
        for each in evaluation[2:]:
            if isinstance(each, Tuple):
                yield tuple([] for _ in range(len(each)))
            else:
                yield []
    
    @torch.inference_mode()
    def __evaluate_at_step(self, batch, batch_idx, collection_prefix, log_prefix, sync_to_logger) -> Union[torch.Tensor, Tuple[torch.Tensor, ...]]:
        collection_prefix = f'_{__class__.__name__}__{collection_prefix}'
        collection_name = f'{collection_prefix}_collection'
        need_images = getattr(self, collection_name) is not None or len(self.global_metrics) > 0
        evaluation = self.__evaluate_result(batch, batch_idx, log_prefix=log_prefix, sync_to_logger=sync_to_logger, return_images=need_images)
        if need_images:
            if getattr(self, collection_name) is None:
                self.need_validation_results()
            if getattr(self, collection_name) is _NeedsCollection:
                setattr(self, collection_name, tuple(self.__yield_each_collection(evaluation)))
            metric_values, features = evaluation[:2]
            for collection, each in zip(getattr(self, collection_name), evaluation[2:]):
                if isinstance(each, Tuple):
                    for inner_collection, inner_each in zip(collection, each):
                        inner_collection.append(inner_each)
                else:
                    collection.append(each)
        else:
            metric_values, features = evaluation
        generation_features, target_features = features
        generation_features_name = f'{collection_prefix}_generation_features'
        target_features_name = f'{collection_prefix}_target_features'
        if generation_features is not None:
            getattr(self, generation_features_name).append(generation_features)
        if target_features is not None:
            getattr(self, target_features_name).append(target_features)
        return metric_values
    
    def validate_at_step(self, batch, batch_idx) -> Union[torch.Tensor, Tuple[torch.Tensor, ...]]:
        return self.__evaluate_at_step(batch, batch_idx, 'validation', 'Val', True)
    
    @torch.inference_mode()
    def __end_for_evaluation_epoch(self, outputs: dict[str, torch.Tensor], collection_prefix, log_prefix):
        if log_prefix is None:
            log_prefix = ''
        elif log_prefix != '':
            log_prefix = f'{log_prefix}-'
        collection_prefix = f'_{__class__.__name__}__{collection_prefix}'
        collection_name = f'{collection_prefix}_collection'
        generation_features_name = f'{collection_prefix}_generation_features'
        target_features_name = f'{collection_prefix}_target_features'
        log = {f'{log_prefix}{key}' : value.mean() for key, value in outputs.items()}
        if len(getattr(self, generation_features_name)) > 0 and len(getattr(self, target_features_name)) > 0:
            generation_features = torch.concat(getattr(self, generation_features_name), dim=0)
            target_features = torch.concat(getattr(self, target_features_name), dim=0)
            getattr(self, generation_features_name).clear()
            getattr(self, target_features_name).clear()
            log.update({f'{log_prefix}{_get_metric_name(metric)}' : metric(generation_features.detach_(), target_features.detach_()).mean() for metric in self.feature_metrics})
        if len(self.global_metrics) > 0:
            generation, target, _ = self.__concat_collection(getattr(self, collection_name))
            log.update({f'{log_prefix}{_get_metric_name(metric)}' : metric(generation, target).mean() for metric in self.global_metrics})
        if len(log) > 0:
            self.log_dict(log, prog_bar=True, logger=True, on_step=False, on_epoch=True, sync_dist=True)
    
    def end_for_validation_epoch(self, outputs: dict[str, torch.Tensor]):
        self.__end_for_evaluation_epoch(outputs, 'validation', 'Val')
    
    def test_at_step(self, batch, batch_idx) -> Union[torch.Tensor, Tuple[torch.Tensor, ...]]:
        return self.__evaluate_at_step(batch, batch_idx, 'test', None, False)
    
    @torch.no_grad()
    def end_for_test_epoch(self, outputs: dict[str, torch.Tensor]):
        self.__end_for_evaluation_epoch(outputs, 'test', None)
    
    def __concat_collection(self, collection) -> Tuple[torch.Tensor, torch.Tensor, Optional[torch.Tensor]]:
        if self.__generation is None:
            generation, target, source = collection
            if isinstance(generation, Tuple):
                generation = tuple(torch.concat(each, dim=0) for each in generation)
            else:
                generation = torch.concat(generation, dim=0)
            if isinstance(target, Tuple):
                target = tuple(torch.concat(each, dim=0) for each in target)
            else:
                target = torch.concat(target, dim=0)
            if source[0] is None:
                source = None
            else:
                source = torch.concat(source, dim=0)
            self.__generation = generation
            self.__target = target
            self.__source = source
        return self.__generation, self.__target, self.__source
        
    def __evaluation_results(self, results, collection) -> Union[torch.Tensor, Tuple[torch.Tensor, ...], Dict[str, torch.Tensor]]:
        if collection is not None:
            generation, target, source = self.__concat_collection(collection)
            if isinstance(generation, Tuple):
                generations = generation[1:]
                generation = generation[0]
            else:
                generations = tuple()
            if isinstance(target, Tuple):
                targets = target[1:]
                target = target[0]
            else:
                targets = tuple()
            error_map = torch.abs(generation - target)
            generation, target, error_map = generation.cpu(), target.cpu(), error_map.cpu()
            if isinstance(results, tuple):
                results = results + (generation, target, error_map)
                if source is not None:
                    results = results + (source.cpu(),)
            elif isinstance(results, dict):
                results.update({
                    'generation' : generation,
                    'target' : target,
                    'error' : error_map
                })
                if len(generations) > 0:
                    results.update({
                        f'generation_{i + 1}' : each
                        for i, each in enumerate(generations)
                    })
                if len(targets) > 0:
                    results.update({
                        f'target_{i + 1}' : each
                        for i, each in enumerate(targets)
                    })
                if source is not None:
                    results.update({'source' : source.cpu()})
            else:
                results = results, generation, target, error_map
                if source is not None:
                    results = *results, source.cpu()
        return results
    
    def need_validation_results(self, need = True, need_images = True, *args, **kwargs):
        """Informs the runner to store the validation results, and collect them later by using
        :attr:`take_validation_results`.

        Args:
            need (bool): The flag that controls whether to use the validation results.
            need_images (bool) : The flag that controls whether to use the validation images.
        
        """
        super().need_validation_results(need, *args, **kwargs)
        if need_images:
            self.__generation = self.__target = self.__source = None
            self.__validation_collection = _NeedsCollection
        else:
            self.__validation_collection = None
    
    @property
    def __validation_results__(self) -> Union[torch.Tensor, Tuple[torch.Tensor, ...], Dict[str, torch.Tensor]]:
        return self.__evaluation_results(super().__validation_results__, self.__validation_collection)
    
    def take_validation_results(self) -> Union[Tuple[torch.Tensor, ...], Tuple[Dict[str, torch.Tensor], torch.Tensor, torch.Tensor]]:
        result = super().take_validation_results()
        self.__generation = self.__target = self.__source = self.__validation_collection = None
        return result
    
    def need_test_results(self, need = True, need_images = True, *args, **kwargs):
        """Informs the runner to store the test results, and collect them later by using
        :attr:`take_test_results`.

        Args:
            need (bool): The flag that controls whether to use the test results.
            need_images (bool) : The flag that controls whether to use the test images.
        
        """
        super().need_test_results(need, *args, **kwargs)
        if need_images:
            self.__generation = self.__target = self.__source = None
            self.__test_collection = _NeedsCollection
        else:
            self.__test_collection = None
    
    @property
    def __test_results__(self) -> Union[torch.Tensor, Tuple[torch.Tensor, ...], Dict[str, torch.Tensor]]:
        return self.__evaluation_results(super().__test_results__, self.__test_collection)
    
    def take_test_results(self) -> Union[Tuple[torch.Tensor, ...], Tuple[Dict[str, torch.Tensor], torch.Tensor, torch.Tensor]]:
        result = super().take_test_results()
        self.__generation = self.__target = self.__source = self.__test_collection = None
        return result


class _NeedsCollection: ...


def _tuplize(func, batch):
    if func is None:
        return tuple()
    else:
        data = func(batch)
        if not isinstance(data, tuple):
            data = (data,)
        return data


def _to_sequence(values):
    if values is None:
        return []
    elif isinstance(values, Sequence):
        return values
    else:
        return [values]


def _get_metric_name(metric):
    if hasattr(metric, '__name__'):
        return metric.__name__
    else:
        return type(metric).__name__