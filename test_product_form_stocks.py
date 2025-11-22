#!/usr/bin/env python3
"""
Test suite for Seller Dashboard Product Form Stock Management

This file contains integration tests and examples for the stock management system.
Run with: python3 test_product_form_stocks.py
"""

import json
from typing import List, Dict, Tuple

class ProductStockValidator:
    """Validates and processes product stock data"""
    
    @staticmethod
    def parse_stock_data(stock_json: str) -> List[Dict]:
        """
        Parse stock data from JSON string (as received from form)
        
        Args:
            stock_json: JSON string from form hidden field
        
        Returns:
            List of dicts with keys: size, color, stock_qty
        """
        try:
            return json.loads(stock_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    @staticmethod
    def validate_stock_structure(stock_data: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate stock data structure
        
        Args:
            stock_data: Parsed stock data list
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        if not isinstance(stock_data, list):
            errors.append("Stock data must be an array")
            return False, errors
        
        if len(stock_data) == 0:
            errors.append("Stock data array cannot be empty")
            return False, errors
        
        for i, item in enumerate(stock_data):
            if not isinstance(item, dict):
                errors.append(f"Item {i} is not a dictionary")
                continue
            
            # Check required fields
            if 'size' not in item:
                errors.append(f"Item {i}: missing 'size' field")
            if 'color' not in item:
                errors.append(f"Item {i}: missing 'color' field")
            if 'stock_qty' not in item:
                errors.append(f"Item {i}: missing 'stock_qty' field")
            
            # Validate types
            if not isinstance(item.get('size'), str):
                errors.append(f"Item {i}: 'size' must be string")
            if not isinstance(item.get('color'), str):
                errors.append(f"Item {i}: 'color' must be string")
            if not isinstance(item.get('stock_qty'), int):
                errors.append(f"Item {i}: 'stock_qty' must be integer")
            
            # Validate values
            if isinstance(item.get('stock_qty'), int) and item['stock_qty'] <= 0:
                errors.append(f"Item {i}: 'stock_qty' must be > 0")
            
            if isinstance(item.get('stock_qty'), int) and item['stock_qty'] > 9999:
                errors.append(f"Item {i}: 'stock_qty' must be <= 9999")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def check_duplicates(stock_data: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Check for duplicate size-color combinations
        
        Args:
            stock_data: Parsed stock data list
        
        Returns:
            (no_duplicates, duplicate_entries)
        """
        seen = set()
        duplicates = []
        
        for item in stock_data:
            key = (item['size'], item['color'])
            if key in seen:
                duplicates.append(f"{item['size']} - {item['color']}")
            seen.add(key)
        
        return len(duplicates) == 0, duplicates
    
    @staticmethod
    def calculate_stats(stock_data: List[Dict]) -> Dict:
        """
        Calculate statistics about stock data
        
        Args:
            stock_data: Parsed stock data list
        
        Returns:
            Dict with stats
        """
        total_qty = sum(item['stock_qty'] for item in stock_data)
        avg_qty = total_qty / len(stock_data) if stock_data else 0
        
        sizes = set(item['size'] for item in stock_data)
        colors = set(item['color'] for item in stock_data)
        
        return {
            'total_combinations': len(stock_data),
            'unique_sizes': len(sizes),
            'unique_colors': len(colors),
            'total_stock': total_qty,
            'average_qty_per_combination': round(avg_qty, 2),
            'min_qty': min((item['stock_qty'] for item in stock_data), default=0),
            'max_qty': max((item['stock_qty'] for item in stock_data), default=0),
            'sizes': sorted(list(sizes)),
            'colors': sorted(list(colors))
        }


# ============ TEST CASES ============

def test_valid_stock_data():
    """Test with valid stock data"""
    print("\n" + "="*60)
    print("TEST 1: Valid Stock Data")
    print("="*60)
    
    stock_json = json.dumps([
        {"size": "M", "color": "Black", "stock_qty": 50},
        {"size": "M", "color": "White", "stock_qty": 30},
        {"size": "L", "color": "Black", "stock_qty": 45},
        {"size": "L", "color": "White", "stock_qty": 25},
    ])
    
    validator = ProductStockValidator()
    
    # Parse
    stock_data = validator.parse_stock_data(stock_json)
    print(f"✓ Parsed {len(stock_data)} items")
    
    # Validate structure
    valid, errors = validator.validate_stock_structure(stock_data)
    assert valid, f"Validation failed: {errors}"
    print(f"✓ Structure validation passed")
    
    # Check duplicates
    no_dups, dups = validator.check_duplicates(stock_data)
    assert no_dups, f"Duplicates found: {dups}"
    print(f"✓ No duplicates found")
    
    # Stats
    stats = validator.calculate_stats(stock_data)
    print(f"✓ Stats calculated:")
    for key, value in stats.items():
        print(f"    {key}: {value}")


def test_invalid_stock_qty():
    """Test with invalid stock quantities"""
    print("\n" + "="*60)
    print("TEST 2: Invalid Stock Quantities")
    print("="*60)
    
    stock_json = json.dumps([
        {"size": "M", "color": "Black", "stock_qty": 0},      # Invalid: qty = 0
        {"size": "M", "color": "White", "stock_qty": -5},     # Invalid: negative
        {"size": "L", "color": "Black", "stock_qty": 10000},  # Invalid: too high
    ])
    
    validator = ProductStockValidator()
    stock_data = validator.parse_stock_data(stock_json)
    
    valid, errors = validator.validate_stock_structure(stock_data)
    assert not valid, "Should have validation errors"
    print(f"✓ Caught {len(errors)} validation errors:")
    for error in errors:
        print(f"    - {error}")


def test_duplicate_combinations():
    """Test with duplicate size-color combinations"""
    print("\n" + "="*60)
    print("TEST 3: Duplicate Combinations")
    print("="*60)
    
    stock_json = json.dumps([
        {"size": "M", "color": "Black", "stock_qty": 50},
        {"size": "M", "color": "White", "stock_qty": 30},
        {"size": "M", "color": "Black", "stock_qty": 20},  # Duplicate
        {"size": "L", "color": "Black", "stock_qty": 45},
    ])
    
    validator = ProductStockValidator()
    stock_data = validator.parse_stock_data(stock_json)
    
    no_dups, dups = validator.check_duplicates(stock_data)
    assert not no_dups, "Should have detected duplicates"
    print(f"✓ Detected {len(dups)} duplicate combination(s):")
    for dup in dups:
        print(f"    - {dup}")


def test_large_dataset():
    """Test with large dataset (many size-color combinations)"""
    print("\n" + "="*60)
    print("TEST 4: Large Dataset (250 combinations)")
    print("="*60)
    
    sizes = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"]
    colors = ["Black", "White", "Gray", "Navy", "Blue", "Red", "Green", "Brown", "Beige", "Khaki"]
    
    stock_data = [
        {
            "size": size,
            "color": color,
            "stock_qty": (i * 7) % 100 + 1  # Distribute stock 1-100
        }
        for i, (size, color) in enumerate([(s, c) for s in sizes for c in colors])
    ]
    
    validator = ProductStockValidator()
    
    # Validate
    valid, errors = validator.validate_stock_structure(stock_data)
    assert valid, f"Validation failed: {errors}"
    print(f"✓ Validated {len(stock_data)} combinations")
    
    # Check duplicates
    no_dups, dups = validator.check_duplicates(stock_data)
    assert no_dups, f"Duplicates found: {dups}"
    print(f"✓ No duplicates in {len(stock_data)} combinations")
    
    # Stats
    stats = validator.calculate_stats(stock_data)
    print(f"✓ Stats:")
    print(f"    Total Combinations: {stats['total_combinations']}")
    print(f"    Unique Sizes: {stats['unique_sizes']}")
    print(f"    Unique Colors: {stats['unique_colors']}")
    print(f"    Total Stock: {stats['total_stock']} units")
    print(f"    Average per Combo: {stats['average_qty_per_combination']} units")
    print(f"    Stock Range: {stats['min_qty']} - {stats['max_qty']} units")


def test_mismatched_size_color_count():
    """Test with mismatched size and color counts"""
    print("\n" + "="*60)
    print("TEST 5: Mismatched Size-Color Count")
    print("="*60)
    
    # 3 sizes × 4 colors = 12 combinations expected
    sizes = ["S", "M", "L"]
    colors = ["Black", "White", "Gray", "Navy"]
    
    # But only provide 10
    stock_data = [
        {"size": size, "color": color, "stock_qty": 50}
        for size, color in [(s, c) for s in sizes for c in colors]
    ][:10]  # Only first 10
    
    validator = ProductStockValidator()
    stats = validator.calculate_stats(stock_data)
    
    print(f"⚠️  Expected combinations: 3 × 4 = 12")
    print(f"✓ Actually provided: {stats['total_combinations']}")
    print(f"   Missing: {3*4 - stats['total_combinations']}")
    print(f"   Sizes: {stats['sizes']}")
    print(f"   Colors: {stats['colors']}")


def test_custom_sizes_colors():
    """Test with custom sizes and colors"""
    print("\n" + "="*60)
    print("TEST 6: Custom Sizes & Colors")
    print("="*60)
    
    # Standard + custom
    sizes = ["S", "M", "L", "4XL", "5XL"]  # 4XL, 5XL are custom
    colors = ["Black", "White", "Burgundy", "Olive"]  # Burgundy, Olive are custom
    
    stock_data = [
        {"size": size, "color": color, "stock_qty": 40}
        for size, color in [(s, c) for s in sizes for c in colors]
    ]
    
    validator = ProductStockValidator()
    valid, errors = validator.validate_stock_structure(stock_data)
    assert valid, f"Validation failed: {errors}"
    
    stats = validator.calculate_stats(stock_data)
    print(f"✓ Custom sizes: {[s for s in stats['sizes'] if s in ['4XL', '5XL']]}")
    print(f"✓ Custom colors: {[c for c in stats['colors'] if c in ['Burgundy', 'Olive']]}")
    print(f"✓ Total combinations: {stats['total_combinations']}")
    print(f"✓ Total stock: {stats['total_stock']} units")


def test_single_combination():
    """Test with single size-color combination (edge case)"""
    print("\n" + "="*60)
    print("TEST 7: Single Combination (Edge Case)")
    print("="*60)
    
    stock_json = json.dumps([
        {"size": "OneSize", "color": "Universal", "stock_qty": 1000}
    ])
    
    validator = ProductStockValidator()
    stock_data = validator.parse_stock_data(stock_json)
    
    valid, errors = validator.validate_stock_structure(stock_data)
    assert valid, f"Validation failed: {errors}"
    print(f"✓ Single combination validated")
    
    stats = validator.calculate_stats(stock_data)
    print(f"✓ Stats:")
    print(f"    Total Stock: {stats['total_stock']}")
    print(f"    Unique Sizes: {stats['unique_sizes']}")
    print(f"    Unique Colors: {stats['unique_colors']}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# PRODUCT FORM STOCK MANAGEMENT - TEST SUITE")
    print("#"*60)
    
    tests = [
        test_valid_stock_data,
        test_invalid_stock_qty,
        test_duplicate_combinations,
        test_large_dataset,
        test_mismatched_size_color_count,
        test_custom_sizes_colors,
        test_single_combination,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "#"*60)
    print(f"# RESULTS: {passed} passed, {failed} failed")
    print("#"*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
