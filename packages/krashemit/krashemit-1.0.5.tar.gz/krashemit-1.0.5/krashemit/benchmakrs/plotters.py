from datetime import datetime
import random
import matplotlib.pyplot as plt


class BenchMarkParamsPlotter:

    _y_dict = {
        'calls': 'Среднее число вызовов функции',
        'avg_iterations': 'Среднее количество итераций',
        'success_percent': 'Процент сходимости',
        'avg_time': 'Среднее время',
    }

    def __init__(self, results: dict, x_param: str, method_name: str, path: str = ''):
        self.results = results
        self.x_param = x_param
        self.method_name = method_name
        self.path = path

    def plot(self):
        paths = []
        for r_key in self.results:
            x = [r.input_args.get(self.x_param) for r in self.results[r_key]]
            for key in self._y_dict:
                y = [getattr(r, key) for r in self.results[r_key]]
                plt.cla()
                plt.plot(x, y, label=f'Тестирование для параметра {self.x_param}')
                plt.grid()
                plt.title(f"Тестовая функция: {r_key} / Метод: {self.method_name}", fontsize=14)
                plt.xlabel(self.x_param, fontsize=12)
                plt.ylabel(self._y_dict[key], fontsize=12)
                plt.legend()
                plt.tight_layout()
                img_path = f'{self.path}plot_{datetime.now().strftime("%H_%M_%S_%d_%m_%Y")}_{str(random.randint(0, 100000))}.png'
                plt.savefig(img_path)
                paths.append(img_path)
        return paths
