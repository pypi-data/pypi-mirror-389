

class BenchMarkParamsAggregator:

    def __init__(self, method_class: type, start_method_name: str,
                 method_kwargs: dict, param_name: str, params_values: list,
                 benchmarks: dict):
        self.param_name = param_name
        self.params_values = params_values
        self.benchmarks = benchmarks
        self.method_class = method_class
        self.start_method_name = start_method_name
        self.method_kwargs = method_kwargs

    def __call__(self) -> dict:
        results = {}
        for key in self.benchmarks:
            results[key] = []
            for param in self.params_values:
                benchmark = self.benchmarks[key]['class'](
                    method_class=self.method_class,
                    start_method_name=self.start_method_name,
                    method_kwargs={
                        self.param_name: param,
                        **self.method_kwargs
                    },
                    **self.benchmarks[key]['params'],
                )
                results[key].append(benchmark())
        return results
