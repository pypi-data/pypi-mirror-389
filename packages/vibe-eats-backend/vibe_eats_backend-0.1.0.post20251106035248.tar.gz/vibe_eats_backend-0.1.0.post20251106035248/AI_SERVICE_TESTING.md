# AI Service Testing Documentation

## Overview
Comprehensive test suite for the AI service module that handles restaurant recommendations based on user mood using OpenAI's GPT-4o-mini model.

## Test Coverage

```
Name            Stmts   Miss  Cover   Missing
---------------------------------------------
ai_service.py      33      0   100%
---------------------------------------------
TOTAL              33      0   100%

Test Suites: 6 test classes
Tests: 32 passed, 32 total
Time: ~1.8s
```

## Test Structure

### 1. TestFormatRestaurantsForAI (11 tests)
Tests for the `_format_restaurants_for_ai()` helper function.

**Covered Functionality:**
- ✅ Single restaurant formatting
- ✅ Multiple restaurants formatting
- ✅ All menu item fields included
- ✅ Empty restaurant list handling
- ✅ Restaurant without menu items
- ✅ Restaurant with empty menu items array
- ✅ Missing name field (defaults to "Unknown")
- ✅ Missing address field
- ✅ Missing menu item fields (defaults applied)
- ✅ Order preservation
- ✅ Special characters in data (accents, quotes, apostrophes)

**Example Test:**
```python
def test_format_single_restaurant(self, sample_restaurants):
    result = _format_restaurants_for_ai([sample_restaurants[0]])

    assert "Restaurant: Italian Bistro" in result
    assert "123 Main St, City" in result
    assert "Margherita Pizza" in result
    assert "$12.99" in result
```

### 2. TestGetAIRecommendations (13 tests)
Tests for the main `get_ai_recommendations()` function.

**Covered Functionality:**
- ✅ Successful recommendation generation
- ✅ Different mood inputs (happy, sad, stressed, excited, tired, adventurous)
- ✅ Prompt structure validation
- ✅ API parameters verification (model, temperature, max_tokens)
- ✅ Markdown code block removal (```json, ```)
- ✅ Plain markdown block removal
- ✅ Whitespace stripping
- ✅ Empty restaurant list handling
- ✅ Invalid JSON response error handling
- ✅ OpenAI API error handling
- ✅ Empty response error handling
- ✅ Long mood text handling
- ✅ Response structure validation

**Example Test:**
```python
@patch('ai_service.openai_client')
def test_successful_recommendation_generation(
    self, mock_client, sample_restaurants, sample_ai_response, mock_openai_completion
):
    mock_openai_completion.choices[0].message.content = sample_ai_response
    mock_client.chat.completions.create.return_value = mock_openai_completion

    result = get_ai_recommendations("feeling happy", sample_restaurants)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["title"] == "Margherita Pizza"
```

### 3. TestImageURLHandling (2 tests)
Tests for image URL transformation logic.

**Covered Functionality:**
- ✅ Relative image URL transformation to full Supabase URLs
- ✅ Absolute image URL preservation

**Example Test:**
```python
def test_relative_image_url_transformation(self, mock_client, sample_restaurants):
    result = get_ai_recommendations("happy", sample_restaurants)

    assert "supabase.co" in result[0]["image"]
    assert result[0]["image"].startswith("https://")
```

### 4. TestAIServiceIntegration (2 tests)
End-to-end integration tests.

**Covered Functionality:**
- ✅ Complete workflow from mood to recommendations
- ✅ Multiple sequential requests
- ✅ Data type validation for all response fields

**Example Test:**
```python
def test_end_to_end_recommendation_flow(self, mock_client, sample_restaurants):
    recommendations = get_ai_recommendations("stressed and need comfort food", sample_restaurants)

    for rec in recommendations:
        assert isinstance(rec["id"], (int, float))
        assert isinstance(rec["title"], str)
        assert isinstance(rec["price"], (int, float))
        # ... all fields validated
```

### 5. TestEdgeCases (4 tests)
Edge cases and boundary condition tests.

**Covered Functionality:**
- ✅ Special characters in mood text (quotes, ampersands, emojis)
- ✅ Unicode characters in restaurant data (accented characters)
- ✅ Large dataset performance (50 restaurants, 10 items each)
- ✅ None values handling

**Example Test:**
```python
def test_unicode_characters_in_restaurant_data(self, mock_client):
    restaurants_with_unicode = [{
        "name": "Café français",
        "menu_items": [{
            "name": "Crème brûlée",
            "description": "Délicieux dessert"
        }]
    }]

    result = get_ai_recommendations("happy", restaurants_with_unicode)
    assert result[0]["title"] == "Crème brûlée"
```

## Fixtures and Mock Data

### Fixtures Used
```python
@pytest.fixture
def sample_restaurants():
    """Sample restaurant data with menu items."""

@pytest.fixture
def sample_ai_response():
    """Sample AI response JSON."""

@pytest.fixture
def mock_openai_completion():
    """Mock OpenAI completion response."""
```

### Mocking Strategy
- **OpenAI Client**: Mocked using `@patch('ai_service.openai_client')`
- **API Responses**: Controlled via mock completion objects
- **No External API Calls**: All tests are isolated and deterministic

## Running Tests

### Run All AI Service Tests
```bash
cd backend
python -m pytest tests/test_ai_service.py -v
```

### Run with Coverage
```bash
python -m pytest tests/test_ai_service.py --cov=ai_service --cov-report=term-missing
```

### Run with HTML Coverage Report
```bash
python -m pytest tests/test_ai_service.py --cov=ai_service --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Test Class
```bash
python -m pytest tests/test_ai_service.py::TestGetAIRecommendations -v
```

### Run Specific Test
```bash
python -m pytest tests/test_ai_service.py::TestGetAIRecommendations::test_successful_recommendation_generation -v
```

## Test Categories

### Unit Tests (24 tests)
- Restaurant formatting logic
- Data validation
- Error handling
- Input sanitization

### Integration Tests (2 tests)
- End-to-end workflow
- Multiple sequential requests

### Edge Case Tests (6 tests)
- Special characters
- Unicode handling
- Large datasets
- Boundary conditions

## Code Coverage Details

### Functions Tested
1. ✅ `get_ai_recommendations(mood_text, restaurants_data)` - 100% coverage
   - Mood processing
   - Restaurant data formatting
   - OpenAI API interaction
   - Response parsing
   - Error handling

2. ✅ `_format_restaurants_for_ai(restaurants)` - 100% coverage
   - Restaurant iteration
   - Menu item formatting
   - Default value handling
   - Special character handling

### Lines Covered
- All 33 statements covered
- All branches covered
- All error paths tested

## Error Handling Tests

### Tested Error Scenarios
1. ✅ Invalid JSON from OpenAI (raises `json.JSONDecodeError`)
2. ✅ OpenAI API errors (raises `Exception`)
3. ✅ Empty response from OpenAI (raises `json.JSONDecodeError`)
4. ✅ Missing required fields in data (uses defaults)
5. ✅ None values in data (handles gracefully)

## Best Practices Demonstrated

1. **Comprehensive Mocking**: All external dependencies (OpenAI API) are mocked
2. **Isolation**: Each test is independent and can run in any order
3. **Clear Naming**: Test names clearly describe what is being tested
4. **Fixtures**: Reusable test data via pytest fixtures
5. **Organization**: Tests grouped by functionality using classes
6. **Coverage**: 100% statement and branch coverage
7. **Edge Cases**: Special characters, unicode, large datasets tested
8. **Error Paths**: All error scenarios have dedicated tests
9. **Documentation**: Comprehensive docstrings for all tests

## Sample Test Output

```
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\Sande\CSC 510\CSC510-002-4\proj2\backend
plugins: anyio-4.11.0, cov-7.0.0, mock-3.15.1

tests/test_ai_service.py::TestFormatRestaurantsForAI::test_format_single_restaurant PASSED
tests/test_ai_service.py::TestFormatRestaurantsForAI::test_format_multiple_restaurants PASSED
tests/test_ai_service.py::TestGetAIRecommendations::test_successful_recommendation_generation PASSED
tests/test_ai_service.py::TestGetAIRecommendations::test_recommendation_with_different_moods PASSED
...
tests/test_ai_service.py::TestEdgeCases::test_large_restaurant_dataset PASSED

============================= 32 passed in 1.73s ==============================
```

## Maintenance

### Adding New Tests
When adding new functionality to `ai_service.py`:

1. Add corresponding test class or test method
2. Use appropriate fixtures for test data
3. Mock external dependencies (OpenAI client)
4. Test both success and error paths
5. Verify coverage remains at 100%

### Example Template
```python
@patch('ai_service.openai_client')
def test_new_feature(self, mock_client, sample_restaurants, mock_openai_completion):
    """Test description."""
    # Setup
    mock_openai_completion.choices[0].message.content = "test response"
    mock_client.chat.completions.create.return_value = mock_openai_completion

    # Execute
    result = get_ai_recommendations("test mood", sample_restaurants)

    # Assert
    assert expected_condition
```

## Dependencies

The tests require:
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- `pytest-cov` - Coverage reporting
- Python standard library (`json`, `unittest.mock`)

## CI/CD Integration

Add to your CI pipeline:
```yaml
- name: Run AI Service Tests
  run: |
    cd backend
    python -m pytest tests/test_ai_service.py --cov=ai_service --cov-fail-under=100 --cov-report=term
```

## Related Documentation
- [Main Testing Documentation](../frontend/TESTING.md)
- [Google Auth Testing](test_google_auth.py)
- [API Documentation](../README.md)
