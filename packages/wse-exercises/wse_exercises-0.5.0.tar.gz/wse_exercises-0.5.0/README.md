## WSE Exercise Series

```python
from wse_exercises.core.math import (
    AddingExercise,
    RandomOperandGenerator,
)

random_operand_generator = RandomOperandGenerator()
config = {
    'min_value': 2,
    'max_value': 9,
}
exercise = AddingExercise(
    operand_generator=random_operand_generator,
    config=config,
)

task = exercise.create_task()
print(f'{task.question.text = }')
print(f'{task.answer.text = }')
```

### Install development mode

```
curl -SL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

## Dependencies

python = "^3.10"
pydantic = ">=2.12.3,<3.0.0"