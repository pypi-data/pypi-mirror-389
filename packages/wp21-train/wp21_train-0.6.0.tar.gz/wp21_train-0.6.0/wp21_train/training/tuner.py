from dataclasses import dataclass
from typing import Any, Dict, List
from wp21_train.training.searchers.grid_search import GridSearch
from wp21_train.training.searchers.random_search import RandomSearch 

@dataclass
class TrialRecord:
    params: Dict[str, Any]
    score: float
    history: Dict[str, List[float]]
    model: List[Any]

class Tuner: 
    def __init__(self, mode, trainer):
        self.trials: List[TrialRecord] = []

        if mode == "hat":
            self.data = self._ignore_quant(trainer.data)
        elif mode == "qat":
            self.data = trainer.data

        search = trainer.meta.get("search")
        if search == "grid":
            self.strategy = GridSearch(self.data)
        elif search == "random":
            trials = int(trainer.meta["trials"])
            self.strategy = RandomSearch(self.data, num_trials=trials, seed=42)

        self.trainer = trainer
        self.exhausted = False

    def prepare_model_parameters(self):
        if self.exhausted:
            return False
        params = self.strategy.next()
        if params is None:
            self.exhausted = True
            return False

        self.params = params
        return True

    def run(self):
        while self.prepare_model_parameters():
            
            self.trainer.compile(self.params)
            history = self.trainer.fit(self.params)

            hist = {"loss": history.history.get("loss"), "val_loss": history.history.get("val_loss")}

            rec = TrialRecord(
                params = self.params,
                score = hist["loss"][-1],
                history = hist,
                model = self.trainer.model,
            )
            self.trials.append(rec)

    @staticmethod
    def _ignore_quant(d):
        return {k: v for k, v in d.items() if "quantizer" not in k.lower()}