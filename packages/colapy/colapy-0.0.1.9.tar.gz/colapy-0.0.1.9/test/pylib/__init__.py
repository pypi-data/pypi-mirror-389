from colapy import WriterBase, ConverterBase, GeneratorBase, EventData


class Generator(GeneratorBase):
    def __init__(self, **kwargs: dict[str, str]) -> None:
        print(f'init: {self}, {kwargs}')

    def __call__(self) -> EventData:
        return EventData()


class Converter(ConverterBase):
    def __init__(self, **kwargs: dict[str, str]) -> None:
        print(f'init: {self}, {kwargs}')

    def __call__(self, event_data: EventData) -> EventData:
        return event_data


class Writer(WriterBase):
    def __init__(self, **kwargs: dict[str, str]) -> None:
        print(f'init: {self}, {kwargs}')

    def __call__(self, event_data: EventData) -> None:
        print('call:', event_data)
