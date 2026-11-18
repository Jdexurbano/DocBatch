class PlanValidationError(Exception):
    def __init__(self, messages):
        self.messages = tuple(messages)
        super().__init__("; ".join(self.messages))


def normalize_batch_name(batch_name: str) -> str:
    return batch_name.strip().upper()
