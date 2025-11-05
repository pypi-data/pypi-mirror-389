import telebot
import matplotlib.pyplot as plt
import datetime
import random


class TgSender:

    _y_dict = {
        'calls': 'Среднее число вызовов функции',
        'avg_iterations': 'Среднее количество итераций',
        'success_percent': 'Процент сходимости',
        'avg_time': 'Среднее время',
    }

    def __init__(self, bot_token: str, chat_id: str, results: dict,
                 x_param: str, method_name: str, plot_names: list, path: str = ''):
        self.tag = f'#{method_name.replace(" ", "_")}_{datetime.datetime.now().strftime("%H_%M_%S_%d_%m_%Y")}'
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.results = results
        self.plot_names = plot_names
        self.x_param = x_param
        self.method_name = method_name
        self.body = ''
        self.path = path
        for key, value in self.results[list(self.results.keys())[0]][0].input_args.items():
            if key != self.x_param:
                self.body += f'{key}: {value}\n'

    def create_tables(self):
        paths = []
        for r_key in self.results:
            title = f"Тестовая функция: {r_key} / Метод: {self.method_name}"
            res = []
            x = [str(r.input_args.get(self.x_param)) for r in self.results[r_key]]
            res.append(x)
            head = [self.x_param]
            for key in self._y_dict:
                head.append(key)
                y = [str(getattr(r, key)) for r in self.results[r_key]]
                res.append(y)
            res = [list(row) for row in zip(*res)]
            fig, ax = plt.subplots()
            ax.axis('off')
            table_data = [
                head,
                *res
            ]
            table = ax.table(
                cellText=table_data,
                cellLoc='center',
                loc='center'
            )
            table.auto_set_font_size(True)
            fig.tight_layout()
            img_path = f'{self.path}table_{datetime.datetime.now().strftime("%H_%M_%S_%d_%m_%Y")}_{str(random.randint(0, 100000))}.png'
            plt.savefig(img_path)
            paths.append((img_path, title))
        return paths

    def create_log_documents(self):
        result_text = ""
        for r_key in self.results:
            title = f"Тестовая функция: {r_key} / Метод: {self.method_name}"
            res = []
            x = [str(r.input_args.get(self.x_param)) for r in self.results[r_key]]
            res.append(x)
            head = [self.x_param]
            for key in self._y_dict:
                head.append(key)
                y = [str(getattr(r, key)) for r in self.results[r_key]]
                res.append(y)
            res = [list(row) for row in zip(*res)]
            table_data = [
                head,
                *res
            ]
            result_text += f"{title}\n\n"
            for row in table_data:
                for i in row:
                    result_text += f"{i:<25} "
                result_text += '\n'
        file_path = f'{self.path}log_{datetime.datetime.now().strftime("%H_%M_%S_%d_%m_%Y")}_{str(random.randint(0, 100000))}.txt'
        with open(file_path, 'w') as f:
            f.write(result_text)
        return file_path

    def send(self):
        table_paths = self.create_tables()
        log_path = self.create_log_documents()
        for table_path, title in table_paths:
            with open(table_path, 'rb') as img:
                self.send_image(img, f"{self.tag}\n{title}\n{self.body}")
        with open(log_path, 'rb') as f:
            self.send_file(f, self.body)
        for plot_path in self.plot_names:
            with open(plot_path, 'rb') as img:
                self.send_image(img, f"{self.tag}\n{self.body}")

    def send_image(self, image, caption):
        bot = telebot.TeleBot(self.bot_token)
        bot.send_photo(
            int(self.chat_id),
            image,
            caption=caption
        )

    def send_file(self, file, caption):
        bot = telebot.TeleBot(self.bot_token)
        bot.send_document(
            int(self.chat_id),
            file,
            caption=caption
        )
