# Developing guide


## Tests
test related files/modules should be on the tests directory

**To run tests:**
```
pytest
```

**To check codebase lines test coverage**
```
pytest --cov=src --cov-report=term
```

**To check codebase functions test coverage**
```
pytest --func_cov=src tests/
```
