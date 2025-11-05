from krashemit.algorithms import GeneticAlgorithm
from krashemit.algorithms import CountriesAlgorithm
from krashemit.algorithms import CountriesAlgorithm_v2
from krashemit.algorithms import CountriesAlgorithm_v3
from krashemit.benchmakrs.benchmark import SphereBenchMark
from krashemit.benchmakrs.aggregators import BenchMarkParamsAggregator
from krashemit.benchmakrs.plotters import BenchMarkParamsPlotter
from krashemit.benchmakrs.tg import TgSender


# benchmark = StBenchMark(
#     method_class=GeneticAlgorithm,
#     start_method_name='testing',
#     method_kwargs={
#         'n': 200,
#         'child_percent': 20,
#         'mutation_chance': 25,
#         'max_mutation': 8,
#         # 'x_min': 10 * [-5.12],
#         # 'x_max': 10 * [5.12],
#         'genes': 5 * [16],
#         't_max': 100
#     },
#     n=5,
#     iterations=10,
#     x_min=[-5.12, -5.12, -5.12, -5.12, -5.12],
#     x_max=[5.12, 5.12, 5.12, 5.12, 5.12]
# )
# res = benchmark()
# 	M=10,
# 	N=25,
# 	n=[1, 10],
# 	p=[0.00001, 2],
# 	m=[1, 8],
# 	k=8,
# 	l=3,
# 	ep=[0.2, 0.4],
aggr = BenchMarkParamsAggregator(
    method_class=CountriesAlgorithm_v3,
    start_method_name='testing',
    method_kwargs={
        'M': 5,
        'n': [2, 5],
        'genes': 5 * [16],
        'max_mutation': 8,
        'm': [1, 3],
        'k': 3,
        'l': 1,
        'ep': [0.2, 0.4],
        'tmax': 100
    },
    param_name='N',
    params_values=[10, 15, 20, 25],
    benchmarks={
        'sphere':
            {
                'class': SphereBenchMark,
                'params': {
                    'n': 5,
                    'iterations': 50,
                    'x_min': 5 * [-5],
                    'x_max': 5 * [5],
                    'x_min_argument': 'Xmin',
                    'x_max_argument': 'Xmax',
                }
            },
    }
)
res = aggr()
plotter = BenchMarkParamsPlotter(res, 'N', 'АВС3', path='C:/Users/Roman/PycharmProjects/KrasheMit/docs/')
plot_names = plotter.plot()
print(plot_names)
sender = TgSender(
    bot_token='5642427180:AAGU0AR0ONiaym-8edcFmZja9dwdOzGZ458',
    chat_id='247194445',
    results=res,
    x_param='N',
    method_name='АВС3',
    plot_names=plot_names,
    path='C:/Users/Roman/PycharmProjects/KrasheMit/docs/'
)
sender.send()
print(res)
