from pydantic import BaseModel, computed_field


class SumMetrics(BaseModel):
    true_positives: float
    positive_predictions: float
    ground_truth_predictions: float

    @computed_field(return_type=float)  # type: ignore[prop-decorator]
    def precision(self) -> float:
        return self.true_positives / self.positive_predictions if self.positive_predictions else 1.0

    @computed_field(return_type=float)  # type: ignore[prop-decorator]
    def recall(self) -> float:
        return self.true_positives / self.ground_truth_predictions if self.ground_truth_predictions else 1.0

    @computed_field(return_type=float)  # type: ignore[prop-decorator]
    def f1_score(self) -> float:
        return self.f_score(beta=1)

    def f_score(self, beta: float = 1) -> float:
        denom = (beta**2 * self.precision) + self.recall
        return (1 + beta**2) * self.precision * self.recall / denom if denom else 0.0

    @staticmethod
    def merge(metrics: list["SumMetrics"]) -> "SumMetrics":
        return SumMetrics(
            true_positives=sum(metric.true_positives for metric in metrics),
            positive_predictions=sum(metric.positive_predictions for metric in metrics),
            ground_truth_predictions=sum(metric.ground_truth_predictions for metric in metrics),
        )
