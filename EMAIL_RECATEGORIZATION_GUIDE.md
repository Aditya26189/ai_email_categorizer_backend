# Email Re-categorization Guide

## Overview
This guide explains how to re-categorize emails in your AI Email Categorizer backend. I've added new endpoints that allow you to update email categories either manually or using AI re-classification.

## Available Categories
The system supports these predefined categories:
- `Important`
- `Work` 
- `Personal`
- `Finance`
- `Travel`
- `Shopping`
- `Entertainment`
- `Health`
- `Education`
- `Other`

## New Endpoints Added

### 1. Single Email Re-categorization
**Endpoint:** `PUT /routers/v1/emails/recategorize`

Re-categorize a single email by Gmail ID.

#### Request Body
```json
{
  "gmail_id": "1853d239248aee99",
  "new_category": "Work",  // Optional: if not provided, AI will re-classify
  "regenerate_summary": true  // Optional: whether to regenerate the summary
}
```

#### Response
```json
{
  "message": "Email recategorized successfully",
  "gmail_id": "1853d239248aee99",
  "old_category": "Personal",
  "new_category": "Work",
  "summary": ["Updated summary point 1", "Updated summary point 2"]
}
```

#### Example Usage
```bash
# Using curl (replace with your authentication token)
curl -X PUT "http://localhost:8000/routers/v1/emails/recategorize" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "gmail_id": "1853d239248aee99",
    "new_category": "Work",
    "regenerate_summary": true
  }'
```

### 2. Bulk Email Re-categorization
**Endpoint:** `PUT /routers/v1/emails/recategorize/bulk`

Re-categorize multiple emails at once using AI.

#### Query Parameters
- `category` (optional): Filter emails by current category to recategorize only those emails
- `regenerate_summary` (optional): Whether to regenerate summaries for all emails

#### Response
```json
{
  "message": "Bulk recategorization completed",
  "total_processed": 25,
  "successful": 23,
  "failed": 2
}
```

#### Example Usage
```bash
# Re-categorize all emails in "Personal" category
curl -X PUT "http://localhost:8000/routers/v1/emails/recategorize/bulk?category=Personal&regenerate_summary=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Re-categorize ALL emails (no category filter)
curl -X PUT "http://localhost:8000/routers/v1/emails/recategorize/bulk?regenerate_summary=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Use Cases

### 1. Fix Incorrect AI Classifications
When the AI incorrectly categorizes emails, you can manually correct them:
```json
{
  "gmail_id": "abc123",
  "new_category": "Finance",
  "regenerate_summary": false
}
```

### 2. Let AI Re-classify
If you want the AI to re-evaluate an email with updated models:
```json
{
  "gmail_id": "abc123",
  "regenerate_summary": true
}
```
*Note: Omitting `new_category` will trigger AI re-classification*

### 3. Bulk Re-categorization After Model Updates
When you update your classification model, re-process all emails:
```bash
curl -X PUT "http://localhost:8000/routers/v1/emails/recategorize/bulk"
```

### 4. Re-categorize Specific Category
If you notice all "Shopping" emails are miscategorized, fix just those:
```bash
curl -X PUT "http://localhost:8000/routers/v1/emails/recategorize/bulk?category=Shopping"
```

## Error Handling

### Common Errors
- **404**: Email not found or doesn't belong to user
- **500**: Database or AI service error
- **401**: Authentication required

### Example Error Response
```json
{
  "detail": {
    "message": "Email not found",
    "gmail_id": "invalid_id",
    "help": "Please verify the Gmail ID is correct and belongs to your account"
  }
}
```

## Integration with Frontend

### JavaScript Example
```javascript
// Re-categorize single email
async function recategorizeEmail(gmailId, newCategory, regenerateSummary = false) {
  const response = await fetch('/routers/v1/emails/recategorize', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userToken}`
    },
    body: JSON.stringify({
      gmail_id: gmailId,
      new_category: newCategory,
      regenerate_summary: regenerateSummary
    })
  });
  
  return response.json();
}

// Bulk re-categorization
async function bulkRecategorize(category = null, regenerateSummary = false) {
  const params = new URLSearchParams({
    regenerate_summary: regenerateSummary
  });
  
  if (category) {
    params.append('category', category);
  }
  
  const response = await fetch(`/routers/v1/emails/recategorize/bulk?${params}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${userToken}`
    }
  });
  
  return response.json();
}
```

## Performance Considerations

1. **Single Email**: Fast operation (~1-2 seconds per email)
2. **Bulk Operations**: Use for large batches, but consider rate limits
3. **Summary Regeneration**: Adds ~2-3 seconds per email due to AI processing
4. **Background Processing**: For very large datasets, consider implementing queue-based processing

## Monitoring and Logging

The system logs all re-categorization activities:
- Old and new categories
- Success/failure rates for bulk operations
- AI processing times
- User activities

Check logs in `logs/app.log` for detailed information.

## Future Enhancements

Potential improvements you could add:
1. **Category Rules**: Define rules for automatic re-categorization
2. **User Feedback**: Track user corrections to improve AI model
3. **Scheduled Re-categorization**: Auto re-categorize old emails periodically
4. **Category Analytics**: Show categorization accuracy metrics
5. **Undo Functionality**: Allow reverting re-categorization changes
