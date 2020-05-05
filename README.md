Cisco DevNet Финальное задание
=======================

Используемые компоненты:
-----------------------

Приложение состоит из серверной части (API) и front-end

Серверная часть (API) использует nornir для сбора информации с устройств и Flask для обмена информаций с front-end

Front-end использует библиотеки knockout для двухстороннего data bind и vis.js для отображения топологии, сравнение топологий реализовано в отдельном модальном окне используя deepdiff (вызывается метод `compare` на стороне сервера), результат сравнения - структура JSON с измененными данными (графическое представление сравнения топологий не реализовано, задача на будущее)

Сохраненные топологии можно просматривать по очереди, кликая на соответствующую, создание новой добавляет еще одну топологию в список и ее так же можно просмотреть



Установка и запуск:
-----------------------

1. Необходимо установить исползуемые библиотеки `pip install -r requirements.txt` (желательно создать venv)

```
deepdiff==4.3.2
Flask==1.1.2
Flask-Cors==3.0.8
nornir==2.4.0
```

2. В inventory внести оборудование, которое будет опрашиваться для составления топологии

3. Далее запустить `python flask_app.py`

4. Перейти в браузере по ссылке `http://127.0.0.1:5000/`

![Гравный экран приложения](/img/main_screen.PNG?raw=true)



Описание работы приложения:
-----------------------

При запуске приложения запрашивается список всех сохраненных топологий (метод `list`) и запрашивается последняя сохраненная топология для отображения схемы сети (метод `last`)

При выборе сохраненной топологии из списка, данная топология запросится со стороны сервера (метод `FILE_NAME`) и после получения данных отрисуется в окне топологии

При нажатии кнопки `Создать топологию` вызовется метод `create` (описание работы ниже), который на стороне сервера опросит все устройства и создаст новую топологию в списке. При выборе новой созданной топологии в списке, отобразится ее графическое представление

При нажатии кнопки `Сравнить топологии` на главном экране приложения вызывается модальное окно сравнения двух топологий

![Окно сравнения топологий](/img/compare_screen.PNG?raw=true)

Необходимо выбрать две топологии для сравнения, при нажатии кнопки `Сравнить топологии` в окне сравнения, на стороне сервера будет вызван метод `compare`, в качестве параметров которому будут переданы имена файлов топологий для сравнения, file1 и file2 соответственно

Результат сравнения, возвращенный сервером, будет отображаться в поле ввода ниже. Сравнение производится библиотекой DeepDiff, результат сравнения - структура в формате JSON. Графическая реализация сравнения двух топологий к сожалению не реализована.



Описание вызовов API:
-----------------------

Базовый URL API `http://127.0.0.1:5000/api/v1.0/topology/`

Все вызовы выполняются методом `GET`


Метод `list`:
---

Возвращает список сохраненных топологий в формате JSON

Вызов: `http://127.0.0.1:5000/api/v1.0/topology/list`

Пример ответа:
```
{
  "data": [
    {
      "topology_file": "topology-2020_05_04-20_20_48.json",
      "topology_name": "topology-2020_05_04-20_20_48"
    },
    {
      "topology_file": "topology-2020_05_04-21_18_06.json",
      "topology_name": "topology-2020_05_04-21_18_06"
    },
    {
      "topology_file": "topology-2020_05_04-23_03_45.json",
      "topology_name": "topology-2020_05_04-23_03_45"
    },
    {
      "topology_file": "topology-2020_05_05-08_11_13.json",
      "topology_name": "topology-2020_05_05-08_11_13"
    }
  ]
}
```


Метод `create`:
---

Создает новую топологию сети

1. В самом начале, используя библитоку nornir, собирает информацию по `hostname` устройств сети, формирует словарь вида `{ inventory.host.name : hostname.from.show_run_include_hostname }`, который используется для корректного отображения `hostname` на топологии сети

2. Собирает информацию о LLDP соседях с каждого устройства из `inventory` используя библитоку nornir для подключения к устройствам и выполнении заданий

3. Строит на основании полученной инфомации топологию в формате JSON `{ nodes: [список узлов], edges: [список соединений] }`

4. Сохраняет полученную топологию в каталог `topologies` с именем `topology-DATE-TIME`

5. Возвращает имя и файл новой сохраненных топологий в формате JSON

Вызов: `http://127.0.0.1:5000/api/v1.0/topology/create`

Пример ответа:
```
{
  "data": {
    "topology_file": "topology-2020_05_05-08_11_13.json",
    "topology_name": "topology-2020_05_05-08_11_13"
  }
}
```


Метод `FILE_NAME`:
---

Возвращает данные сохраненной топологии с именем файла `FILE_NAME` в формате JSON

Если топология с именем файла `FILE_NAME` не будет найдена, возвращает 404

Вызов: `http://127.0.0.1:5000/api/v1.0/topology/FILE_NAME`

Пример ответа:
```
{
    "nodes": [
        {
            "host": "SW-SEG-LAB-CORE",
            "group": "core_device",
            "dev_type": "l3switch"
        },
        {
            "host": "N5K-C5548UP-FA",
            "group": "edge_device",
            "dev_type": "l2switch"
        }
    ],
    "edges": [
        {
            "from": "SW-SEG-LAB-CORE",
            "from_interface": "Gi1/0/5",
            "to": "N5K-C5548UP-FA",
            "to_interface": "mgmt0"
        },
        {
            "from": "SW-SEG-LAB-CORE",
            "from_interface": "Gi1/0/8",
            "to": "N5K-C5548UP-FA",
            "to_interface": "Eth1/2"
        }
    ]
}
```


Метод `last`:
---

Возвращает данные последней сохраненной топологии в формате JSON

Вызов: `http://127.0.0.1:5000/api/v1.0/topology/last`

Пример ответа:
```
{
    "nodes": [
        {
            "host": "SW-SEG-LAB-CORE",
            "group": "core_device",
            "dev_type": "l3switch"
        },
        {
            "host": "N5K-C5548UP-FA",
            "group": "edge_device",
            "dev_type": "l2switch"
        }
    ],
    "edges": [
        {
            "from": "SW-SEG-LAB-CORE",
            "from_interface": "Gi1/0/5",
            "to": "N5K-C5548UP-FA",
            "to_interface": "mgmt0"
        },
        {
            "from": "SW-SEG-LAB-CORE",
            "from_interface": "Gi1/0/8",
            "to": "N5K-C5548UP-FA",
            "to_interface": "Eth1/2"
        }
    ]
}
```


Метод `compare`:
---

Возвращает результат сравнения двух топологий в структуре формата JSON

В переменные `file1` и `file2` указываются имена файлов топологий, которые необходимо сравнить

Вызов: `http://127.0.0.1:5000/api/v1.0/topology/compare?file1=FILE_NAME_1&file2=FILE_NAME_2`

Пример ответа:
```
{
  "data": {
    "compare": {
      "iterable_item_added": {
        "root['edges'][3]": {
          "from": "SW-SEG-LAB-CORE",
          "from_interface": "Gi1/0/48",
          "to": "Diapazon_Lab_Vchassi",
          "to_interface": "776"
        },
        "root['edges'][4]": {
          "from": "SW-SEG-LAB-CORE",
          "from_interface": "Gi1/0/47",
          "to": "Diapazon_Lab_Vchassi",
          "to_interface": "775"
        },
        "root['nodes'][3]": {
          "dev_type": "l3switch",
          "group": "edge_device",
          "host": "Diapazon_Lab_Vchassi"
        }
      }
    }
  }
}
```

Если две топологии идентичны, то возвращает пустой результат
```
{
  "data": {
    "compare": {}
  }
}
```



Консольное приложение для отладки:
-----------------------

Для запуска необходимо использовать ключи командной строки

При запуске без ключей отобразит на экране полученную топологию в формате JSON

Для сравнения топологий необхоимо указать два файла, сравнение использует библиотеку DeepDiff

```
python app_topology.py --help
usage: app_topology.py [-h] [--compare COMPARE COMPARE] [--save]

Построение топологии сети (LLDP)

optional arguments:
  -h, --help            show this help message and exit
  --compare COMPARE COMPARE
                        Сравнение двух топологий в формате JSON
  --save                Сохранение полученной топологии в формате JSON
```


