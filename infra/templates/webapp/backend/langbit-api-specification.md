# API Specification for Language Exercise Generation

## Exercise Generation Endpoint

### Basic Information

- **URL**: `/api/v1/exercises/generate`
- **Method**: POST
- **Description**: Generates a language exercise based on the specified type and parameters.
- **Content-Type**: application/json

### Request Structure

```json
{
  "exerciseType": "string",
  "params": {
    // Dynamic set of parameters depending on the exercise type
  }
}
```

### Request Parameters

| Field | Type | Required | Description |
|------|-----|--------------|----------|
| exerciseType | string | Yes | Exercise type (see list of supported types) |
| params | object | Yes | Object with parameters for exercise generation |

### Supported Exercise Types and Their Parameters

#### 1. Multiple Choice

```json
{
  "exerciseType": "Multiple Choice",
  "params": {
    "difficultyLevel": "intermediate",
    "topic": "Present Perfect",
    "numberOfQuestions": 5,
    "optionsPerQuestion": 4,
    "includeExplanations": false
  }
}
```

| Parameter | Type | Required | Description | Valid Values |
|----------|-----|--------------|----------|--------------------|
| difficultyLevel | string | Yes | Difficulty level | "beginner", "intermediate", "advanced" |
| topic | string | No | Exercise topic | Any string |
| numberOfQuestions | number | Yes | Number of questions | 1-20 |
| optionsPerQuestion | number | Yes | Number of answer options per question | 3-5 |
| includeExplanations | boolean | No | Whether to include explanations for answers | true, false |

#### 2. Fill in the Gaps

```json
{
  "exerciseType": "Fill in the Gaps",
  "params": {
    "difficultyLevel": "intermediate",
    "topic": "Past Simple",
    "textType": "paragraph",
    "numberOfGaps": 8,
    "provideWordBank": true
  }
}
```

| Parameter | Type | Required | Description | Valid Values |
|----------|-----|--------------|----------|--------------------|
| difficultyLevel | string | Yes | Difficulty level | "beginner", "intermediate", "advanced" |
| topic | string | No | Exercise topic | Any string |
| textType | string | Yes | Text type | "paragraph", "sentences", "dialogue" |
| numberOfGaps | number | Yes | Number of gaps | 1-20 |
| provideWordBank | boolean | No | Whether to provide a word bank for filling in | true, false |

#### 3. Reading Comprehension

```json
{
  "exerciseType": "Reading Comprehension",
  "params": {
    "difficultyLevel": "intermediate",
    "topic": "Environment",
    "textLength": "medium",
    "questionTypes": ["multiple_choice", "true_false", "short_answer"],
    "numberOfQuestions": 5
  }
}
```

| Parameter | Type | Required | Description | Valid Values |
|----------|-----|--------------|----------|--------------------|
| difficultyLevel | string | Yes | Difficulty level | "beginner", "intermediate", "advanced" |
| topic | string | No | Exercise topic | Any string |
| textLength | string | Yes | Text length | "short", "medium", "long" |
| questionTypes | array | Yes | Question types | Array of: "multiple_choice", "true_false", "short_answer" |
| numberOfQuestions | number | Yes | Number of questions | 1-10 |

#### 4. Match the Pairs

```json
{
  "exerciseType": "Match the Pairs",
  "params": {
    "difficultyLevel": "intermediate",
    "matchType": "word_definition",
    "topic": "Phrasal Verbs",
    "numberOfPairs": 10
  }
}
```

| Parameter | Type | Required | Description | Valid Values |
|----------|-----|--------------|----------|--------------------|
| difficultyLevel | string | Yes | Difficulty level | "beginner", "intermediate", "advanced" |
| matchType | string | Yes | Match type | Various match types (e.g., "word_definition", "synonym_antonym") |
| topic | string | No | Exercise topic | Any string |
| numberOfPairs | number | Yes | Number of pairs to match | 1-20 |

#### 5. Sentence Completion

```json
{
  "exerciseType": "Sentence Completion",
  "params": {
    "difficultyLevel": "intermediate",
    "grammarFocus": "conditional_sentences",
    "numberOfSentences": 8,
    "optionsPerSentence": 3
  }
}
```

| Parameter | Type | Required | Description | Valid Values |
|----------|-----|--------------|----------|--------------------|
| difficultyLevel | string | Yes | Difficulty level | "beginner", "intermediate", "advanced" |
| grammarFocus | string | Yes | Grammar focus | Various grammar topics |
| numberOfSentences | number | Yes | Number of sentences | 1-20 |
| optionsPerSentence | number | Yes | Number of options for each sentence | 2-5 |

#### 6. True or False

```json
{
  "exerciseType": "True or False",
  "params": {
    "difficultyLevel": "intermediate",
    "topic": "Science",
    "statementType": "facts",
    "numberOfStatements": 10,
    "includeExplanations": true
  }
}
```

| Parameter | Type | Required | Description | Valid Values |
|----------|-----|--------------|----------|--------------------|
| difficultyLevel | string | Yes | Difficulty level | "beginner", "intermediate", "advanced" |
| topic | string | No | Exercise topic | Any string |
| statementType | string | Yes | Statement type | "facts", "rules", "text_based" |
| numberOfStatements | number | Yes | Number of statements | 1-20 |
| includeExplanations | boolean | No | Whether to include explanations | true, false |

### Response Structure

#### Successful Response

- **Code**: 200 OK
- **Content-Type**: application/json

```json
{
  "success": true,
  "data": {
    "exerciseText": "# Multiple Choice Exercise\nDifficulty: Intermediate\nTopic: Present Perfect\n\nQuestion 1: Choose the correct option.\n1. He has went\n2. He has gone ✓\n3. He has goed\n4. He has goed\n\n...",
    "exerciseType": "Multiple Choice",
    "exerciseId": "5f9b5b5b5b5b5b5b5b5b5b5b"
  }
}
```

| Field | Type | Description |
|------|-----|----------|
| success | boolean | Flag indicating successful operation |
| data.exerciseText | string | Text of the generated exercise in Markdown format |
| data.exerciseType | string | Exercise type |
| data.exerciseId | string | Unique identifier of the generated exercise (optional, if storage is required) |

#### Error

- **Code**: 400 Bad Request, 404 Not Found, 500 Internal Server Error
- **Content-Type**: application/json

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Parameter 'numberOfQuestions' must be a number from 1 to 20",
    "details": {
      "parameter": "numberOfQuestions",
      "allowed": [1, 20]
    }
  }
}
```

| Field | Type | Description |
|------|-----|----------|
| success | boolean | Flag indicating successful operation (false in case of error) |
| error.code | string | Error code |
| error.message | string | Error message |
| error.details | object | Additional error details (optional) |

### Possible Error Codes

| Code | HTTP Status | Description |
|-----|------------|----------|
| INVALID_EXERCISE_TYPE | 400 | Unknown exercise type |
| MISSING_REQUIRED_PARAMETER | 400 | Missing required parameter |
| INVALID_PARAMETER | 400 | Invalid parameter value |
| GENERATION_FAILED | 500 | Error during exercise generation |

## Request and Response Examples

### Example 1: Generating a "Multiple Choice" Exercise

**Request**:

```http
POST /api/v1/exercises/generate HTTP/1.1
Host: api.langbit.com
Content-Type: application/json

{
  "exerciseType": "Multiple Choice",
  "params": {
    "difficultyLevel": "intermediate",
    "topic": "Present Perfect",
    "numberOfQuestions": 5,
    "optionsPerQuestion": 4,
    "includeExplanations": true
  }
}
```

**Response**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "exerciseText": "# Multiple Choice Exercise\nDifficulty: Intermediate\nTopic: Present Perfect\n\nQuestion 1: Choose the correct form of the Present Perfect.\n1. She have been to Paris\n2. She has been to Paris ✓\n3. She been to Paris\n4. She is been to Paris\n\nExplanation: The Present Perfect is formed with have/has + past participle (been).\n\nQuestion 2: Choose the correct sentence.\n1. I've known him since two years\n2. I've known him for two years ✓\n3. I know him since two years\n4. I know him for two years\n\nExplanation: We use 'for' with periods of time and 'since' with specific points in time.\n\n...",
    "exerciseType": "Multiple Choice",
    "exerciseId": "60f1a5c7e6b2f3b7d8a0c4e2"
  }
}
```

### Example 2: Error Due to Invalid Parameter Value

**Request**:

```http
POST /api/v1/exercises/generate HTTP/1.1
Host: api.langbit.com
Content-Type: application/json

{
  "exerciseType": "Fill in the Gaps",
  "params": {
    "difficultyLevel": "intermediate",
    "topic": "Past Simple",
    "textType": "invalid_text_type",
    "numberOfGaps": 8,
    "provideWordBank": true
  }
}
```

**Response**:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Parameter 'textType' has an invalid value. Valid values: 'paragraph', 'sentences', 'dialogue'",
    "details": {
      "parameter": "textType",
      "allowedValues": ["paragraph", "sentences", "dialogue"]
    }
  }
}
```

## Implementation Recommendations

1. **Parameter Validation**: Implement strict validation of all incoming parameters before starting exercise generation.

2. **Caching**: Consider caching frequently requested exercises to improve performance.

3. **Logging**: Maintain detailed logging of requests and responses for debugging and usage analysis.

4. **Authentication**: Add authentication and authorization mechanisms to protect the API.

5. **Error Handling**: Provide detailed error messages to facilitate debugging and integration.

6. **Versioning**: Use API versioning (/v1/) to ensure backward compatibility when changes are made.

7. **Documentation**: Create interactive API documentation using tools such as Swagger or Redoc.

8. **Rate Limiting**: Implement request rate limiting to prevent abuse.

9. **Monitoring**: Set up monitoring to track API performance and availability. 