# Accessory Management System

A Flask-based web application for managing accessories with SKU tracking, location management, and remark history.

## Features

### Core Functionality
- **Accessory Management**: Add, update, and delete accessories with SKU, location, and remarks
- **SKU Auto-handling**: Automatically appends `*1`, `*2`, etc. for duplicate SKUs at the same location
- **Remark History**: Track multiple remarks per accessory, sorted by time (newest first)
- **Location Management**: Predefined locations with usage count tracking
- **SKU Statistics**: Visual bar chart showing SKU distribution (variants grouped together)

### New Features
- **Location Dropdown**: Select locations from a predefined list, sorted by usage frequency
- **SKU Autocomplete**: Auto-suggest existing SKUs when typing
- **SKU Detail View**: Click any SKU in the statistics chart to see all locations and accessories for that SKU
- **Pagination**: Accessories list paginated with 7 items per page

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd remark_winsome
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python3 app.py
```

5. Access the application at `http://127.0.0.1:5001`

## Database Schema

### accessories
- `id`: Primary key
- `sku`: Stock Keeping Unit
- `location`: Storage location
- `updated_at`: Last update timestamp

### remarks
- `id`: Primary key
- `accessory_id`: Foreign key to accessories
- `content`: Remark text
- `created_at`: Creation timestamp

### locations
- `id`: Primary key
- `name`: Location name (unique)
- `usage_count`: Number of accessories at this location
- `created_at`: Creation timestamp

## Usage

### Adding an Accessory
1. Enter SKU in the input field (autocomplete will suggest existing SKUs)
2. Select location from the dropdown (sorted by usage frequency)
3. Add optional remarks
4. Click "Add"

### Managing Locations
- Click "Manage Locations" to add or remove storage locations
- Locations are automatically sorted by usage count

### Viewing SKU Details
- Scroll down to the "SKU Statistics" section
- Click any SKU bar to see all accessories and locations for that SKU

### Pagination
- Navigate through accessories using the pagination controls at the bottom of the list
- 7 items displayed per page

## API Endpoints

- `GET /api/skus`: Get all unique SKUs
- `GET /api/locations`: Get all locations with usage counts

## Technologies

- **Backend**: Flask, SQLite
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Python Version**: 3.8+

## License

MIT License
