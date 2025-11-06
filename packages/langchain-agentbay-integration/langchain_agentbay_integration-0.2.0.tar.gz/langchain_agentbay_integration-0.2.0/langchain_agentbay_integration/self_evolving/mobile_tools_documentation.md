# Mobile Tools Documentation

This document provides detailed information about the mobile tools available for use in the self-evolving agent system. Each tool's parameters and expected outputs are described to help the AI generate precise tool calls.

## 1. mobile_tap

Taps on the mobile screen at specific coordinates.

### Parameters:
- `x` (integer, required): X coordinate of the tap position
- `y` (integer, required): Y coordinate of the tap position

### Output Format:
```json
{
  "success": true/false,
  "message": "Description of the operation result",
  "x": x_coordinate,
  "y": y_coordinate
}
```

### Example Usage:
```json
{
  "name": "mobile_tap",
  "arguments": {
    "x": 150,
    "y": 320
  }
}
```

## 2. mobile_swipe

Swipes on the mobile screen from one point to another.

### Parameters:
- `start_x` (integer, required): Starting X coordinate
- `start_y` (integer, required): Starting Y coordinate
- `end_x` (integer, required): Ending X coordinate
- `end_y` (integer, required): Ending Y coordinate
- `duration_ms` (integer, optional, default=300): Duration of the swipe in milliseconds

### Output Format:
```json
{
  "success": true/false,
  "message": "Description of the operation result",
  "start_x": start_x_coordinate,
  "start_y": start_y_coordinate,
  "end_x": end_x_coordinate,
  "end_y": end_y_coordinate,
  "duration_ms": duration_in_milliseconds
}
```

### Example Usage:
```json
{
  "name": "mobile_swipe",
  "arguments": {
    "start_x": 100,
    "start_y": 500,
    "end_x": 100,
    "end_y": 200,
    "duration_ms": 500
  }
}
```

## 3. mobile_input_text

Inputs text into the active field on mobile.

### Parameters:
- `text` (string, required): Text to input

### Output Format:
```json
{
  "success": true/false,
  "message": "Description of the operation result",
  "text": "input_text"
}
```

### Example Usage:
```json
{
  "name": "mobile_input_text",
  "arguments": {
    "text": "Hello, world!"
  }
}
```

## 4. mobile_send_key

Sends a key event to the mobile device.

### Parameters:
- `key_code` (integer, required): Key code to send. Common codes:
  - HOME: 3
  - BACK: 4
  - VOLUME_UP: 24
  - VOLUME_DOWN: 25
  - POWER: 26
  - MENU: 82

### Output Format:
```json
{
  "success": true/false,
  "message": "Description of the operation result",
  "key_code": key_code_number,
  "key_name": "key_name"
}
```

### Example Usage:
```json
{
  "name": "mobile_send_key",
  "arguments": {
    "key_code": 3
  }
}
```

## 5. mobile_get_ui_elements

Gets all UI elements on the current mobile screen.

### Parameters:
- `timeout_ms` (integer, optional, default=2000): Timeout in milliseconds to wait for UI elements

### Output Format:
```json
{
  "success": true/false,
  "message": "Description of the operation result",
  "elements": [
    {
      // UI element information
    }
  ],
  "timeout_ms": timeout_in_milliseconds
}
```

### Example Usage:
```json
{
  "name": "mobile_get_ui_elements",
  "arguments": {
    "timeout_ms": 3000
  }
}
```

## 6. mobile_screenshot

Takes a screenshot of the current mobile screen.

### Parameters:
- `file_path` (string, required): File path to save the screenshot

### Output Format:
```json
{
  "success": true/false,
  "message": "Description of the operation result",
  "screenshot_url": "url_to_screenshot",
  "file_path": "path_to_saved_file"
}
```

### Example Usage:
```json
{
  "name": "mobile_screenshot",
  "arguments": {
    "file_path": "./screenshots/screen.png"
  }
}
```

## 7. mobile_wait

Waits for a specified amount of time in milliseconds.

### Parameters:
- `milliseconds` (integer, required): Time to wait in milliseconds

### Output Format:
```json
{
  "success": true/false,
  "message": "Description of the operation result"
}
```

### Example Usage:
```json
{
  "name": "mobile_wait",
  "arguments": {
    "milliseconds": 2000
  }
}
```